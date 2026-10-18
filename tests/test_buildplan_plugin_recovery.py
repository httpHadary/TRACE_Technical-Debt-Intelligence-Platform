"""Nonexecuting E.0.5 policy/integrity proof using synthetic XML/ZIP transports."""
import copy
import hashlib
import io
import json
from pathlib import Path
import inspect
import time
import urllib.error
import urllib.request
import zipfile
import pytest
from tools import recover_buildplan_plugin as e
from tools.maven_recovery.acquisition import Acquisition, CENTRAL, relative_path, BudgetExceeded


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(urllib.request.OpenerDirector,'open',lambda *a,**k:pytest.fail('Real network forbidden'))


def pom(artifact='seed'):
    return f'<project><groupId>g</groupId><artifactId>{artifact}</artifactId><version>1</version></project>'.encode()


@pytest.fixture
def seed(tmp_path):
    a=Acquisition(tmp_path/'old');raw=pom()
    a.fetch=lambda p,limit:hashlib.sha512(raw).hexdigest().encode() if p.endswith('.sha512') else raw
    a.get('g','seed','1');return a.root,list(a.records.values())


def recovery(tmp_path,seed,local=()):
    a=e.Recovery(tmp_path/'e05',*seed,local=local);a.network_enabled=True;return a


class Response:
    status=200
    def __init__(self,path,raw):self.path,self.raw=path,raw;self.headers={'Content-Length':str(len(raw))}
    def geturl(self):return CENTRAL+self.path
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n):raw,self.raw=self.raw[:n],self.raw[n:];return raw


def opener(a,raw,missing=()):
    class Opener:
        def open(self,req,timeout):
            p=req.full_url.removeprefix(CENTRAL);alg=p.rsplit('.',1)[-1]
            if alg in missing:raise urllib.error.HTTPError(req.full_url,404,'fixture',None,None)
            return Response(p,hashlib.new(alg,raw).hexdigest().encode() if alg in ('sha512','sha256','sha1') else raw)
    a.opener=Opener()


def test_seed_copy_separate_and_ledgers_immutable(tmp_path,seed):
    source,rows=seed;before=(source/'dependency_manifest.json').read_bytes();a=recovery(tmp_path,seed)
    name=rows[0]['path']
    assert (a.cache/name).stat().st_ino!=(source/'repository'/name).stat().st_ino
    assert a.get('g','seed','1')==pom() and a.requests==a.bytes==0
    assert a.seal()['prior_request_ledgers']==dict(D=2000,D1=400,D2=52,D3=112,E03=56)
    assert (source/'dependency_manifest.json').read_bytes()==before


@pytest.mark.parametrize('which',['bytes','checksum','source','coordinate'])
def test_seed_integrity_failures_rejected_before_new_cache(tmp_path,seed,which):
    source,rows=seed;rows=copy.deepcopy(rows)
    if which=='bytes':(source/'repository'/rows[0]['path']).write_bytes(b'wrong')
    elif which=='checksum':rows[0]['repository_checksum']['value']='0'*128
    elif which=='source':rows[0]['source_url']='https://wrong.invalid/a'
    else:rows[0]['coordinates'][0]='other'
    with pytest.raises((ValueError,FileNotFoundError)):recovery(tmp_path,(source,rows))
    assert not (tmp_path/'e05').exists()


def test_existing_cache_not_resumable(tmp_path,seed):
    a=recovery(tmp_path,seed)
    with pytest.raises(FileExistsError):e.Recovery(a.root,*seed,local=())


@pytest.mark.parametrize('old',['phase5_2_2_e_0_3','phase5_2_2_e_0_4'])
def test_previous_phase_paths_denied(tmp_path,seed,old):
    with pytest.raises(ValueError):e.Recovery(e.RESEARCH/old/'forbidden',*seed,local=())


def test_checksum_404_requests_and_last_request_cap(tmp_path,seed):
    a=recovery(tmp_path,seed);opener(a,pom('new'),('sha512','sha256'));a.get('g','new','1')
    assert a.requests==4 and len(a.http_events)==2
    a.requests=119;opener(a,pom('last'))
    with pytest.raises(BudgetExceeded):a.get('g','last','1')
    assert a.requests==120 and relative_path('g','last','1') not in a.records
    assert json.loads((a.root/'dependency_manifest.json').read_text())['requests']==120
    with pytest.raises(BudgetExceeded):a.fetch(relative_path('g','last','1'),100)


def test_local_candidates_require_fresh_checksum(tmp_path,seed):
    local=tmp_path/'approved';p=local/relative_path('g','local','1');p.parent.mkdir(parents=True);p.write_bytes(pom('local'))
    a=recovery(tmp_path,seed,(local,));opener(a,pom('local'));a.get('g','local','1')
    assert a.requests==1 and a.bytes==128
    assert a.records[str(p.relative_to(local))]['origin']=='APPROVED_LOCAL_BYTES_FRESH_CENTRAL_CHECKSUM'


def test_local_bad_checksum_never_admitted(tmp_path,seed):
    local=tmp_path/'approved';p=local/relative_path('g','local','1');p.parent.mkdir(parents=True);p.write_bytes(pom('wrong'))
    a=recovery(tmp_path,seed,(local,));opener(a,pom('local'))
    with pytest.raises(ValueError,match='checksum mismatch'):a.get('g','local','1')
    assert str(p.relative_to(local)) not in a.records


@pytest.mark.parametrize('cap',['bytes','time','requests','disk','artifact'])
def test_caps_stop_safely_before_payload_read(tmp_path,seed,cap):
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
            r.read=lambda n:pytest.fail('Cannot read oversized artifact');return r
    a.opener=Opener()
    with pytest.raises(BudgetExceeded):a.fetch('g/new/1/new-1.pom',e.MAX_ARTIFACT)


@pytest.mark.parametrize('path',['../escape','https://evil.invalid/a','g/new/1/a?query'])
def test_allowlist_paths(tmp_path,seed,path):
    a=recovery(tmp_path,seed)
    with pytest.raises(ValueError):a.fetch(path,100)
    assert a.requests==0


def test_redirect_response_rejected(tmp_path,seed):
    a=recovery(tmp_path,seed)
    class Opener:
        def open(self,*args,**kwargs):
            r=Response('g/new/1/new-1.pom',pom('new'));r.geturl=lambda:'https://wrong.invalid/a';return r
    a.opener=Opener()
    with pytest.raises(ValueError,match='identity'):a.get('g','new','1')


def plugin_jar(gav=e.FELIX,duplicate=False):
    out=io.BytesIO()
    xml=f'<plugin><groupId>{gav[0]}</groupId><artifactId>{gav[1]}</artifactId><version>{gav[2]}</version><mojos><mojo><goal>manifest</goal><phase>process-classes</phase></mojo></mojos><dependencies><dependency><groupId>later</groupId><artifactId>runtime</artifactId><version>9</version></dependency></dependencies></plugin>'.encode()
    with zipfile.ZipFile(out,'w') as z:
        z.writestr('META-INF/maven/plugin.xml',xml)
        if duplicate:z.writestr('META-INF/maven/plugin.xml',xml)
    return out.getvalue()


class DataCache:
    def __init__(self,raw):self.raw=raw;self.requests=[]
    def get(self,*args):self.requests.append(args);return self.raw


def test_descriptor_reads_only_jar_metadata_never_runtime_closure():
    a=DataCache(plugin_jar());q=e.descriptor(a,e.FELIX)
    assert q['mojos'][0]['phase']=='process-classes'
    assert len(q['declared_descriptor_runtime_dependencies'])==1
    assert a.requests==[(*e.FELIX,'jar')]
    assert not q['classes_executed'] and not q['plugin_realm_resolved']


def test_descriptor_coordinate_mismatch_rejected():
    with pytest.raises(ValueError,match='coordinate'):e.descriptor(DataCache(plugin_jar(('wrong','plugin','1'))),e.FELIX)


def test_descriptor_duplicate_entries_rejected():
    with pytest.warns(UserWarning):raw=plugin_jar(duplicate=True)
    with pytest.raises(ValueError,match='duplicate'):e.descriptor(DataCache(raw),e.FELIX)


def test_capacity_uses_fixed_limit_and_reserve():
    q=e.runtime_capacity([dict(path='g/a/1/a-1.jar',bytes=100)])
    assert q['limit_bytes']==128*1024**2 and q['metadata_reserve_bytes']==16*1024**2
    assert q['estimated_total_bytes']>q['payload_bytes']
    assert e.runtime_capacity([dict(path='g/a/1/a-1.jar',bytes=128*1024**2)])['status']=='BLOCKED_RUNTIME_CACHE_CAPACITY'


def test_no_artifact_execution_or_unbounded_runtime_traversal():
    source=inspect.getsource(e)
    assert 'subprocess' not in source and 'os.system' not in source
    assert '.closure(' not in source and 'execute_once' not in source
    assert e.MAX_REQUESTS==120 and e.MAX_BYTES==48*1024**2 and e.MAX_SECONDS==600
    assert e.seed.MAX_REQUESTS==200


def test_offline_plan_has_no_implicit_network_or_version_resolution(tmp_path,monkeypatch):
    from tools.maven_recovery.acquisition import parse_xml
    root=parse_xml(b'<project><build><plugins><plugin><groupId>org.apache.felix</groupId><artifactId>maven-bundle-plugin</artifactId><version>5.1.9</version><executions><execution><id>bundle-manifest</id><phase>process-classes</phase><goals><goal>manifest</goal></goals></execution></executions></plugin></plugins></build></project>')
    monkeypatch.setattr(e,'context',lambda base:root)
    class Cache:
        records={}
        def get(self,*args):pytest.fail('No network-capable get for missing descriptor')
    q=e.plan_audit(tmp_path,Cache())
    assert relative_path(*e.FELIX,'jar') in q['missing_paths']
    assert q['plugins'][0]['executions'][0]['phase']=='process-classes'
    assert not q['actual_plan_resolved'] and not q['full_offline_build_ready']
    assert q['unknown']  # default bindings absent rather than invented versions


def test_local_filename_does_not_bypass_exhausted_budget(tmp_path,seed):
    local=tmp_path/'approved';p=local/relative_path('g','local','1');p.parent.mkdir(parents=True);p.write_bytes(pom('local'))
    a=recovery(tmp_path,seed,(local,));a.requests=e.MAX_REQUESTS
    with pytest.raises(BudgetExceeded):a.get('g','local','1')
    assert relative_path('g','local','1') not in a.records


def test_invalid_jar_never_admitted(tmp_path,seed):
    a=recovery(tmp_path,seed);opener(a,b'not a zip')
    with pytest.raises(zipfile.BadZipFile):a.get('g','bad','1','jar')
    assert relative_path('g','bad','1','jar') not in a.records


def test_bounded_metadata_read_rejects_oversized_member():
    with pytest.raises(ValueError):e.jar_member(plugin_jar(),'META-INF/maven/plugin.xml',cap=10)
