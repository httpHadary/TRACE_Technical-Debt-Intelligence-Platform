"""E.0.5.1 descriptor-only bounds, ownership and identity regression proof."""
import copy
import hashlib
import inspect
import io
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import zipfile
import pytest
from tools import recover_buildplan_frontier as e
from tools.maven_recovery.acquisition import Acquisition, BudgetExceeded, CENTRAL, relative_path

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(urllib.request.OpenerDirector,'open',lambda *a,**k:pytest.fail('Network forbidden in tests'))

def pom(artifact='seed'):
    return f'<project><groupId>g</groupId><artifactId>{artifact}</artifactId><version>1</version></project>'.encode()

@pytest.fixture
def seed(tmp_path):
    a=Acquisition(tmp_path/'old');raw=pom()
    a.fetch=lambda p,limit:hashlib.sha512(raw).hexdigest().encode() if p.endswith('.sha512') else raw
    a.get('g','seed','1');return a.root,list(a.records.values())

def task(tmp_path):
    folder=tmp_path/'owned';folder.mkdir()
    (folder/'owner.json').write_text(json.dumps(dict(phase='E.0.5.1',base=e.BASE,exclusive_root=str(folder))))
    return folder

def recovery(tmp_path,seed,local=()):
    folder=task(tmp_path);a=e.Recovery(folder/'recovery-1',*seed,local=local,task=folder)
    a.network_enabled=True;return a

class Response:
    status=200
    def __init__(self,path,raw):self.path,self.raw=path,raw;self.headers={'Content-Length':str(len(raw))}
    def geturl(self):return CENTRAL+self.path
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n):raw,self.raw=self.raw[:n],self.raw[n:];return raw

def transport(a,raw,missing=()):
    class Opener:
        def open(self,req,timeout):
            path=req.full_url.removeprefix(CENTRAL);alg=path.rsplit('.',1)[-1]
            # Every request, including checksum probes, must already be durable.
            assert json.loads((a.root/'dependency_manifest.json').read_text())['requests']==a.requests
            if alg in missing:raise urllib.error.HTTPError(req.full_url,404,'fixture',None,None)
            return Response(path,hashlib.new(alg,raw).hexdigest().encode() if alg in ('sha512','sha256','sha1') else raw)
    a.opener=Opener()

def test_independent_seed_and_old_ledger_preserved(tmp_path,seed):
    source,rows=seed;old=(source/'dependency_manifest.json').read_bytes();a=recovery(tmp_path,seed)
    assert (a.cache/rows[0]['path']).stat().st_ino!=(source/'repository'/rows[0]['path']).stat().st_ino
    assert a.get('g','seed','1')==pom() and a.requests==a.bytes==0
    assert (source/'dependency_manifest.json').read_bytes()==old
    assert a.seal()['prior_request_ledgers']==dict(D=2000,D1=400,D2=52,D3=112,E03=56,E05=12)

@pytest.mark.parametrize('what',['bytes','checksum','source','coordinates'])
def test_bad_seed_rejected_before_output(tmp_path,seed,what):
    source,rows=seed;rows=copy.deepcopy(rows);folder=task(tmp_path)
    if what=='bytes':(source/'repository'/rows[0]['path']).write_bytes(b'bad')
    elif what=='checksum':rows[0]['repository_checksum']['value']='0'*128
    elif what=='source':rows[0]['source_url']='https://evil.invalid/pom'
    else:rows[0]['coordinates'][0]='wrong'
    with pytest.raises((ValueError,FileNotFoundError)):e.Recovery(folder/'recovery-1',source,rows,local=(),task=folder)
    assert not (folder/'recovery-1').exists()

@pytest.mark.parametrize('path_kind',['old','parent','other','symlink','bad_owner'])
def test_ownership_guard_before_any_write(tmp_path,seed,path_kind):
    folder=task(tmp_path);root=folder/'recovery-1'
    if path_kind=='old':root=seed[0]
    elif path_kind=='parent':root=folder.parent/'recovery-1'
    elif path_kind=='other':root=folder/'other'
    elif path_kind=='symlink':root.symlink_to(seed[0],target_is_directory=True)
    else:(folder/'owner.json').write_text('{}')
    with pytest.raises(ValueError):e.Recovery(root,*seed,task=folder,local=())
    assert not (folder/'recovery-1').is_dir() or path_kind=='symlink'

def test_consumed_directory_cannot_be_reused(tmp_path,seed):
    a=recovery(tmp_path,seed)
    with pytest.raises(FileExistsError):e.Recovery(a.root,*seed,task=a.task,local=())

def test_request_budget_includes_checksum_probes(tmp_path,seed):
    a=recovery(tmp_path,seed);transport(a,pom('new'),missing=('sha512','sha256'));a.get('g','new','1')
    assert a.requests==4
    a.requests=159;transport(a,pom('last'))
    with pytest.raises(BudgetExceeded):a.get('g','last','1')
    assert a.requests==160 and relative_path('g','last','1') not in a.records
    with pytest.raises(BudgetExceeded):a.fetch(relative_path('g','last','1'),100)

@pytest.mark.parametrize('cap',['bytes','time','disk','requests','artifact'])
def test_budget_and_storage_caps(tmp_path,seed,cap):
    a=recovery(tmp_path,seed)
    if cap=='disk':
        with pytest.raises(BudgetExceeded):a.check_disk(e.MAX_DISK)
        return
    if cap=='bytes':a.bytes=e.MAX_BYTES
    elif cap=='time':a.started-=e.MAX_SECONDS+1
    elif cap=='requests':a.requests=e.MAX_REQUESTS
    if cap!='artifact':
        with pytest.raises(BudgetExceeded):a.fetch('g/new/1/new-1.pom',100)
        return
    class Opener:
        def open(self,*args,**kwargs):
            r=Response('g/new/1/new-1.pom',b'');r.headers['Content-Length']=str(e.MAX_ARTIFACT+1)
            r.read=lambda n:pytest.fail('Oversized body read');return r
    a.opener=Opener()
    with pytest.raises(BudgetExceeded):a.fetch('g/new/1/new-1.pom',e.MAX_ARTIFACT)

def test_local_bytes_need_authoritative_fresh_checksum(tmp_path,seed):
    folder=tmp_path/'local';p=folder/relative_path('g','local','1');p.parent.mkdir(parents=True);p.write_bytes(pom('local'))
    a=recovery(tmp_path,seed,(folder,));transport(a,pom('local'));a.get('g','local','1')
    assert a.requests==1 and a.records[str(p.relative_to(folder))]['origin']=='APPROVED_LOCAL_BYTES_FRESH_CENTRAL_CHECKSUM'

@pytest.mark.parametrize('path',['../bad','https://evil.invalid/a','g/a/1/a.pom?query'])
def test_allowlist_is_exact(tmp_path,seed,path):
    a=recovery(tmp_path,seed)
    with pytest.raises(ValueError):a.fetch(path,100)
    assert a.requests==0

def plugin_cache(gav,goals=('test',),props_gav=None):
    g,a,v=gav;props_gav=props_gav or gav
    pp=f'<project><groupId>{g}</groupId><artifactId>{a}</artifactId><version>{v}</version><packaging>maven-plugin</packaging></project>'.encode()
    xml=f'<plugin><groupId>{g}</groupId><artifactId>{a}</artifactId><version>{v}</version><mojos>'+''.join(f'<mojo><goal>{goal}</goal><phase>test</phase></mojo>' for goal in goals)+'</mojos><dependencies><dependency><groupId>future</groupId><artifactId>runtime</artifactId><version>1</version></dependency></dependencies></plugin>'
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        z.writestr('META-INF/maven/plugin.xml',xml)
        z.writestr(f'META-INF/maven/{g}/{a}/pom.properties','\n'.join(f'{k}={x}' for k,x in zip(('groupId','artifactId','version'),props_gav)))
    class Cache:
        used_paths=set();records={}
        def get(self,*args):
            path=relative_path(*args);self.used_paths.add(path)
            assert args[:3]==gav,'Runtime closure was requested'
            return out.getvalue() if len(args)>3 and args[3]=='jar' else pp
    return Cache()

def row(gav):return dict(gav=list(gav),executions=[],default_bindings=[('test','test')])

def test_descriptor_and_properties_verified_without_runtime_fetch():
    gav=e.TARGETS[0];q=e.inspect_plugin(plugin_cache(gav),row(gav))
    assert q['expected_goals_verified'] and q['embedded_properties_gav_verified']
    assert q['runtime_requirements'][0]['status']=='UNKNOWN_RUNTIME_RESOLUTION_NOT_EXECUTED'
    assert q['execution_status']=='NOT_EXECUTED' and not q['actual_maven_plan_verified']

@pytest.mark.parametrize('defect',['properties','goal','duplicate'])
def test_plugin_identity_and_goals_rejected(defect):
    gav=e.TARGETS[0];a=plugin_cache(gav,goals=('other',) if defect=='goal' else ('test','test') if defect=='duplicate' else ('test',),props_gav=('wrong','a','1') if defect=='properties' else None)
    with pytest.raises(ValueError):e.inspect_plugin(a,row(gav))

def test_status_keeps_unknown_model_conditions_visible():
    plan=dict(missing_paths=[],unknown=[]);capacity=dict(status='FITS_128_MIB')
    matrix=[dict(gav=['g','a','1'],execution_status='NOT_EXECUTED',static_model_issues=[dict(kind='PROFILE')])]
    assert e.summarize(plan,plan,matrix,None,capacity)['status']=='PARTIAL'
    matrix[0]['static_model_issues']=[]
    assert e.summarize(plan,plan,matrix,None,capacity)['status']=='PASS_STATIC_DESCRIPTOR_CLOSURE'
    capacity['status']='BLOCKED_RUNTIME_CACHE_CAPACITY'
    assert e.summarize(plan,plan,matrix,None,capacity)['status']=='BLOCKED'

def test_fixed_targets_limits_and_no_execution():
    assert len(e.TARGETS)==6 and e.MAX_REQUESTS==160 and e.MAX_SECONDS==600
    assert e.MAX_BYTES==48*1024**2 and e.previous.MAX_REQUESTS==120 and e.seed.MAX_REQUESTS==200
    code=inspect.getsource(e)
    assert 'subprocess' not in code and 'os.system' not in code and '.closure(' not in code
    assert code.index('for gav in TARGETS:')<code.index('a.completed.append(list(gav));a.seal()')
    q=e.previous.runtime_capacity([dict(path='g/a/1/a-1.jar',bytes=100)])
    assert q['limit_bytes']==128*1024**2 and q['metadata_reserve_bytes']==16*1024**2


def test_frozen_inventory_normalizes_json_tuple_representation(tmp_path,monkeypatch):
    folder=tmp_path/'examples/phase5_2_2_e_0_5';folder.mkdir(parents=True)
    plan=dict(missing_paths=sorted(relative_path(*g,ext) for g in e.TARGETS for ext in ('pom','jar')),
              unknown=[],plugins=[row(g) for g in e.TARGETS])
    (folder/'plan_after.json').write_text(json.dumps(plan))
    monkeypatch.setattr(e.previous,'plan_audit',lambda base,a:plan)
    assert len(e.frozen_inventory(tmp_path,None)[1])==6
