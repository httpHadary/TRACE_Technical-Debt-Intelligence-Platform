"""E.2 descriptor-only bounds, ownership and identity regression proof."""
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
from tools import prepare_tminus90 as e
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
    (folder/'owner.json').write_text(json.dumps(dict(phase='E.2',base=e.BASE,exclusive_root=str(folder))))
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
    assert a.seal()['prior_request_ledgers']==dict(D=2000,D1=400,D2=52,D3=112,E03=56,E05=12,E051=52,E1=32)

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
    assert e.COMMIT=='e1529b546d9696192f4de52152777403b4a01b39'
    assert e.TREE=='c1a67e730fc5729a5376c267ed559f4ae310df01'
    assert e.POM=='f4403aa060f16ca0f17d28fffb1bc6fcc42c31d480af8dc6a6436f25fddf8f15'
    assert e.MAX_REQUESTS==200 and e.MAX_BYTES==64*1024**2 and e.MAX_SECONDS==600
    assert e.previous.MAX_REQUESTS==120 and e.descriptor_tools.MAX_REQUESTS==160
    assert all(g[-1]=='5.11.0-M2' for g in e.TARGETS[:3]) and e.TARGETS[3][-1]=='3.2.5'


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
    plugin=e.parse_xml(b'<plugin><artifactId>maven-surefire-plugin</artifactId><version>3.2.5</version></plugin>')
    # parse_xml normalizes project POMs only; this is a namespaced POM fragment.
    import xml.etree.ElementTree as ET
    plugin=ET.fromstring('<plugin xmlns="http://maven.apache.org/POM/4.0.0"><artifactId>maven-surefire-plugin</artifactId><version>3.2.5</version></plugin>')
    rows,unknown=e.plugin_rows(dict(plugins={('org.apache.maven.plugins','maven-surefire-plugin'):plugin},managed_plugins={},properties={}))
    assert rows[0]['gav']==['org.apache.maven.plugins','maven-surefire-plugin','3.2.5']
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
    model['source']={'source_entries':[]}
    q=e.comparison(model,model,'t0')
    assert q['actual_tminus90_effective_pom_sha256'] is None and q['remaining_actual_maven_model']=='UNKNOWN'


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
    plan=dict(plugins=[dict(gav=['org.apache.maven.plugins','maven-resources-plugin','3.3.1'],missing_paths=[],configured_executions=[],default_bindings=[('process-resources','resources')])])
    q=e.differential_closure(None,plan,model)
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


def test_published_710_seed_manifest_identity_and_paths():
    base=Path(__file__).resolve().parents[1]
    p=base/'examples/phase5_2_2_e_1/dependency_manifest.json'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==e.MANIFEST
    q=json.loads(p.read_text());rows={r['path']:r for r in q['artifacts']}
    assert len(rows)==710 and q['requests']==32 and e.canonical(rows)==e.CACHE_ID
    assert relative_path('org.junit','junit-bom','5.11.0-M2') in rows
    assert all(relative_path(*gav,ext) not in rows for gav in e.TARGETS for ext in ('pom','jar'))


def test_exact_milestone_and_later_descriptor_roots():
    assert e.TARGETS==(('org.junit.jupiter','junit-jupiter-api','5.11.0-M2'),
        ('org.junit.jupiter','junit-jupiter-engine','5.11.0-M2'),
        ('org.junit.jupiter','junit-jupiter-params','5.11.0-M2'),
        ('org.apache.maven.plugins','maven-surefire-plugin','3.2.5'),
        ('org.cyclonedx','cyclonedx-maven-plugin','2.8.0'),
        ('org.spdx','spdx-maven-plugin','0.7.3'),
        ('org.moditect','moditect-maven-plugin','1.2.1.Final'))


def test_no_automatic_http_retry_and_failure_is_durable(tmp_path,seed):
    a=recovery(tmp_path,seed)
    class Opener:
        def open(self,*args,**kwargs):raise urllib.error.URLError('fixture offline')
    a.opener=Opener()
    with pytest.raises(urllib.error.URLError):a.fetch('g/new/1/new-1.pom',100)
    assert a.requests==1 and len(a.transport_failures)==1
    assert json.loads((a.root/'dependency_manifest.json').read_text())['requests']==1


def test_failed_previous_build_proof_prevents_publication(monkeypatch):
    import tools.verify_compile_e06 as t0
    import tools.verify_compile_e11 as t30
    monkeypatch.setattr(t0,'audit',lambda root:dict(status='PARTIAL'))
    monkeypatch.setattr(t30,'audit',lambda root:pytest.fail('Do not accept the next proof after failure'))
    with pytest.raises(ValueError,match='prior evidence'):e.verify_successful_builds()


def test_target_comparison_does_not_label_tminus30_as_target():
    source=dict(source_entries=[dict(path='src/main/Foo.java',sha256='a')])
    model=dict(parent_chain=[],imports=[],dependencies=[],dependency_management=[],profiles=[],plugins=[],build_sections=[],properties={},source=source)
    other=copy.deepcopy(model);other['source']['source_entries'][0]['sha256']='b'
    q=e.comparison(model,other,'t_minus30')
    assert q['source_changes']['changed_production_java']==['src/main/Foo.java']
    assert q['actual_tminus90_effective_pom_sha256'] is None


def test_static_blockers_and_cache_capacity_never_become_compile_pass():
    after=dict(target=dict(static_model_issues=[]),plan=dict(unknown=[],plugins=[]),test_closure=dict(unresolved=[],dependency_profile_uncertainties=[]),changed_compile_plugin_closure=dict(issues=[]),missing_paths=[])
    q=e.decision(None,after,None,dict(status='FITS_128_MIB'))
    assert q['status']=='PASS_STATIC_T_MINUS_90_READINESS' and not q['compile_success']
    assert q['actual_effective_model_sha256'] is None
    assert e.decision(None,after,None,dict(status='BLOCKED_RUNTIME_CACHE_CAPACITY'))['status']=='BLOCKED'
    after['missing_paths']=['g/a/1/a-1.pom']
    assert e.decision(None,after,None,dict(status='FITS_128_MIB'))['status']=='PARTIAL'


def test_changed_enforcer_version_is_audited_without_t0_substitution(monkeypatch):
    import xml.etree.ElementTree as ET
    plugin=ET.fromstring('<plugin xmlns="http://maven.apache.org/POM/4.0.0"><version>3.5.0</version></plugin>')
    baseline=dict(plugins={('org.apache.maven.plugins','maven-enforcer-plugin'):plugin},managed_plugins={},properties={})
    plan=dict(plugins=[dict(gav=['org.apache.maven.plugins','maven-enforcer-plugin','3.4.1'],missing_paths=[],configured_executions=[dict(phase='validate')],default_bindings=[])])
    class Model:
        issues=[]
        def __init__(self,a):pass
        def closure(self,roots,reason):return [dict(gav=roots[0]['gav'],reason=reason)]
    monkeypatch.setattr(e,'Models',Model)
    result=e.differential_closure(None,plan,baseline)
    assert result['roots']==[['org.apache.maven.plugins','maven-enforcer-plugin','3.4.1']]


def test_milestone_bom_resolves_exact_engine_api_parent_metadata(tmp_path):
    documents={('g','base','1'):b'<project><groupId>g</groupId><artifactId>base</artifactId><version>1</version><packaging>pom</packaging></project>',
      ('org.junit','junit-bom','5.11.0-M2'):b'<project><groupId>org.junit</groupId><artifactId>junit-bom</artifactId><version>5.11.0-M2</version><packaging>pom</packaging><dependencyManagement><dependencies><dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-api</artifactId><version>5.11.0-M2</version></dependency></dependencies></dependencyManagement></project>',
      ('org.junit.jupiter','junit-jupiter-engine','5.11.0-M2'):b'<project><parent><groupId>g</groupId><artifactId>base</artifactId><version>1</version></parent><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-engine</artifactId><version>5.11.0-M2</version><dependencyManagement><dependencies><dependency><groupId>org.junit</groupId><artifactId>junit-bom</artifactId><version>5.11.0-M2</version><scope>import</scope><type>pom</type></dependency></dependencies></dependencyManagement><dependencies><dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-api</artifactId></dependency></dependencies></project>',
      ('org.junit.jupiter','junit-jupiter-api','5.11.0-M2'):b'<project><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-api</artifactId><version>5.11.0-M2</version></project>'}
    class Cache:
        cache=tmp_path;used_paths=set();records={}
        def get(self,g,a,v,extension='pom',classifier=''):
            key=(g,a,v)
            assert key in documents
            path=relative_path(g,a,v,extension,classifier);self.used_paths.add(path);self.records[path]={}
            raw=documents[key] if extension=='pom' else b'fixture_not_executed'
            p=self.cache/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            return raw
    root=dict(gav=['org.junit.jupiter','junit-jupiter-engine','5.11.0-M2'],scope='test',type='jar',classifier='',optional=False,exclusions=[])
    q=e.seed.static_closure(Cache(),[root],{})
    assert {tuple(r['gav']) for r in q['edges']}=={('org.junit.jupiter','junit-jupiter-engine','5.11.0-M2'),('org.junit.jupiter','junit-jupiter-api','5.11.0-M2')}
    assert not q['missing'] and not q['unresolved']
    assert any(r['path']==relative_path('org.junit','junit-bom','5.11.0-M2') for r in q['pom_metadata'])
    assert not q['resolved_runtime_classpath']


@pytest.mark.parametrize('mutation',['none','extra_property','dependency','property_reference','activation_consumer','other_remote'])
def test_remote_compiler_profile_scope_keeps_activation_unknown(mutation):
    identity=['commons-codec','commons-codec','1.16.0']
    parent='<project><groupId>org.apache.commons</groupId><artifactId>commons-parent</artifactId><version>58</version><profiles><profile><id>jdk9-compiler</id><activation><jdk>[9</jdk></activation><properties><maven.compiler.release>${commons.compiler.release}</maven.compiler.release></properties></profile></profiles></project>'
    child='<project><parent><groupId>org.apache.commons</groupId><artifactId>commons-parent</artifactId><version>58</version></parent><groupId>commons-codec</groupId><artifactId>commons-codec</artifactId><version>1.16.0</version></project>'
    if mutation=='extra_property':parent=parent.replace('</properties>','<version.a>1</version.a></properties>')
    if mutation=='dependency':parent=parent.replace('</profile>','<dependencies/></profile>')
    if mutation=='property_reference':child=child.replace('</project>','<properties><x>${maven.compiler.release}</x></properties></project>')
    if mutation=='activation_consumer':child=child.replace('</project>','<profiles><profile><id>x</id><activation><property><name>maven.compiler.release</name></property></activation></profile></profiles></project>')
    if mutation=='other_remote':identity=['g','unknown','1']
    class Cache:
        def get(self,*gav):return (parent if gav[1]=='commons-parent' else child).encode()
    row=e.issue_relevance(Cache(),[dict(kind='PROFILE',identity=identity,reason='jdk9-compiler')])[0]
    assert row['activation']=='UNKNOWN_NOT_MAVEN_EVALUATED'
    assert row['blocking']==(mutation!='none')
    if mutation=='none':assert row['scope_evidence']['property_reference_consumers']==0


def test_project_compiler_profile_cannot_use_remote_scope_exception():
    class Cache:
        def get(self,*gav):pytest.fail('Project profile must remain blocking')
    row=e.issue_relevance(Cache(),[dict(kind='PROFILE',identity=['commons-cli','commons-cli',e.COMMIT],reason='jdk9-compiler')])[0]
    assert row['blocking'] and row['activation']=='UNKNOWN_NOT_MAVEN_EVALUATED'
