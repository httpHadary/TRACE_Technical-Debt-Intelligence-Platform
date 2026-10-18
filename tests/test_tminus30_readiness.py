"""E.1 descriptor-only bounds, ownership and identity regression proof."""
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
from tools import prepare_tminus30 as e
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
    (folder/'owner.json').write_text(json.dumps(dict(phase='E.1',base=e.BASE,exclusive_root=str(folder))))
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
    assert a.seal()['prior_request_ledgers']==dict(D=2000,D1=400,D2=52,D3=112,E03=56,E05=12,E051=52)

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
    a.requests=199;transport(a,pom('last'))
    with pytest.raises(BudgetExceeded):a.get('g','last','1')
    assert a.requests==200 and relative_path('g','last','1') not in a.records
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


def test_revision_and_seed_identities_are_distinct_from_t0():
    assert e.COMMIT=='fb6293fcd6a9b55ac8ecb550af6572daaed18fa1'
    assert e.TREE=='598dec4901a9adcf8e55b241c9689a8db6219c29'
    assert e.POM=='2f322b0751115f2a5e93aabfb83372dc0511d57bbd8b4f178f08d5b449ff3fcf'
    assert e.MAX_REQUESTS==200 and e.MAX_BYTES==64*1024**2 and e.MAX_SECONDS==600
    assert e.previous.MAX_REQUESTS==120 and e.descriptor_tools.MAX_REQUESTS==160
    assert all(g[-1]=='5.11.0' for g in e.TARGETS[:3]) and e.TARGETS[3][-1]=='3.4.0'


def test_models_keep_static_profile_and_effective_model_unknowns():
    model=dict(chain=[['g','parent','74']],imports=[],properties={},dependencies=[],management={},profiles=[dict(id='conditional',active=None)],plugins={},managed_plugins={})
    class Models:issues=[]
    q=e.summary(model,Models(),dict(tracked_files=116))
    assert q['actual_effective_model_sha256'] is None and not q['actual_maven_executed']
    assert q['profiles'][0]['runtime_decision']=='UNKNOWN_NOT_MAVEN_EVALUATED'


def test_absent_default_versions_remain_unknown_not_t0_substituted():
    rows,unknown=e.plugin_rows(dict(plugins={},managed_plugins={},properties={}))
    assert not rows and len(unknown)==6
    assert all(x['status']=='UNKNOWN_EXACT_DEFAULT_PLUGIN_VERSION' for x in unknown)


def test_target_static_plan_reads_own_plugin_versions():
    plugin=e.parse_xml(b'<plugin><artifactId>maven-surefire-plugin</artifactId><version>3.4.0</version></plugin>')
    # parse_xml normalizes project POMs only; this is a namespaced POM fragment.
    import xml.etree.ElementTree as ET
    plugin=ET.fromstring('<plugin xmlns="http://maven.apache.org/POM/4.0.0"><artifactId>maven-surefire-plugin</artifactId><version>3.4.0</version></plugin>')
    rows,unknown=e.plugin_rows(dict(plugins={('org.apache.maven.plugins','maven-surefire-plugin'):plugin},managed_plugins={},properties={}))
    assert rows[0]['gav']==['org.apache.maven.plugins','maven-surefire-plugin','3.4.0']
    assert len(unknown)==5


def test_write_is_flushed_before_replace_and_ledger_is_immutable_on_fetch_failure(tmp_path,seed):
    source=inspect.getsource(e.write)
    assert source.index('os.fsync(stream.fileno())')<source.index('temporary.replace(path)')
    assert 'os.fsync(directory)' in source
    a=recovery(tmp_path,seed);transport(a,pom('new'),missing=('sha512',));a.get('g','new','1')
    assert a.requests==3 and json.loads((a.root/'dependency_manifest.json').read_text())['requests']==3


def test_no_maven_java_or_container_execution_entrypoint():
    code=inspect.getsource(e)
    assert '.execute_once(' not in code and '.docker(' not in code and 'run_smoke(' not in code
    assert 'subprocess' not in code and 'os.system' not in code
    assert '.context(' not in code  # no T0 effective model used to build target plan
    assert 'actual_effective_model_sha256=None' in code


def test_static_comparison_cannot_promote_to_compile_pass():
    model=dict(parent_chain=[],imports=[],dependencies=[],dependency_management=[],profiles=[],plugins=[],build_sections=[],properties={})
    q=e.compare(model,model)
    assert q['actual_tminus30_effective_pom_sha256'] is None and q['remaining_actual_maven_model']=='UNVERIFIED'


def test_closure_metadata_scope_excludes_unrelated_plugin_reads():
    class Parent:
        cache=Path('/unused');records={};used_paths={'unrelated/plugin.pom'}
        def get(self,*args):return b'fixture'
    scoped=e.ScopedCache(Parent())
    assert scoped.get('g','a','1')==b'fixture'
    assert scoped.used_paths=={'g/a/1/a-1.pom'}
    assert 'unrelated/plugin.pom' not in scoped.used_paths


def test_managed_default_resources_is_not_a_changed_version(monkeypatch):
    import xml.etree.ElementTree as ET
    resource=ET.fromstring('<plugin xmlns="http://maven.apache.org/POM/4.0.0"><version>3.3.1</version></plugin>')
    model=dict(plugins={},managed_plugins={('org.apache.maven.plugins','maven-resources-plugin'):resource},properties={})
    monkeypatch.setattr(e,'plan_inventory',lambda a,m:dict(plugins=[dict(gav=['org.apache.maven.plugins','maven-resources-plugin','3.3.1'],missing_paths=[],configured_executions=[],default_bindings=[('process-resources','resources')])]))
    q=e.differential_closure(None,model,model)
    assert q['roots']==[] and q['edges']==[]


@pytest.mark.parametrize('extra',['','<dependencies/>','<properties><x>y</x></properties>'])
def test_profile_activation_unknown_remains_but_only_build_config_is_nonblocking(extra):
    raw=('<project><profiles><profile><id>no-containers-for-windows</id><activation><os><family>windows</family></os></activation>'+extra+'<build><plugins><plugin><artifactId>maven-surefire-plugin</artifactId><version>1</version><configuration><excludedGroups>fixture</excludedGroups></configuration></plugin></plugins></build></profile></profiles></project>').encode()
    class Cache:
        def get(self,*args):return raw
    q=e.issue_relevance(Cache(),[dict(kind='PROFILE',identity=['org.apache.sshd','sshd-core','2.9.2'])])[0]
    assert q['activation']=='UNKNOWN_NOT_MAVEN_EVALUATED'
    assert q['blocking']==bool(extra)


def test_unknown_project_profiles_always_remain_blocking():
    class Cache:
        def get(self,*args):pytest.fail('No remote-profile exception for a project profile')
    q=e.issue_relevance(Cache(),[dict(kind='PROFILE',identity=['commons-cli',e.COMMIT])])
    assert q[0]['blocking'] and q[0]['activation']=='UNKNOWN_NOT_MAVEN_EVALUATED'
