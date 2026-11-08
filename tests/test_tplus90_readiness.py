"""E.5 descriptor-only bounds, ownership and identity regression proof."""
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
from tools import prepare_tplus90 as e
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
    (folder/'owner.json').write_text(json.dumps(dict(phase='E.5',base=e.BASE,exclusive_root=str(folder))))
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
    assert a.seal()['prior_request_ledgers']==dict(D=2000,D1=400,D2=52,D3=112,E03=56,E05=12,E051=52,E1=32,E2=67,E3=46,E4=8)

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
    a.requests=79;transport(a,pom('last'))
    with pytest.raises(BudgetExceeded):a.get('g','last','1')
    assert a.requests==80 and relative_path('g','last','1') not in a.records
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
    assert e.COMMIT=='af2b3e72a552cfb2a902556469868763ddea3638'
    assert e.TREE=='0d773516c1c7bb0a371b2af6e084b62ef2d36546'
    assert e.POM=='87c8ed93cb21deedb52b826d520931bc175e24e5ee48643c6a21ed154c62324b'
    assert e.MAX_REQUESTS==80 and e.MAX_BYTES==24*1024**2 and e.MAX_SECONDS==600
    assert e.previous.MAX_REQUESTS==120 and e.descriptor_tools.MAX_REQUESTS==160
    assert e.TARGETS==(('org.apache.commons','commons-text','1.13.0'),)


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
    assert q['actual_tplus90_effective_pom_sha256'] is None and q['remaining_actual_maven_model']=='UNKNOWN'


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
    p=base/'examples/phase5_2_2_e_4/dependency_manifest.json'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==e.MANIFEST
    q=json.loads(p.read_text());rows={r['path']:r for r in q['artifacts']}
    assert len(rows)==753 and q['requests']==8 and e.canonical(rows)==e.CACHE_ID
    assert relative_path('org.junit','junit-bom','5.11.2') in rows
    assert all(relative_path(*gav,ext) not in rows for gav in e.TARGETS for ext in ('pom','jar'))


def test_exact_text_root_and_reused_dependencies():
    assert e.TARGETS==(('org.apache.commons','commons-text','1.13.0'),)
    assert e.TRACKED_FILES==138 and e.JAVA_FILES==36
    manifest=json.loads((Path(__file__).resolve().parents[1]/'examples/phase5_2_2_e_4/dependency_manifest.json').read_text())
    records={r['path'] for r in manifest['artifacts']}
    for gav in [('org.junit.jupiter','junit-jupiter-api','5.11.2'),('commons-io','commons-io','2.18.0')]:
        assert all(relative_path(*gav,ext) in records for ext in ('pom','jar'))


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
    assert q['actual_tplus90_effective_pom_sha256'] is None


def test_static_blockers_and_cache_capacity_never_become_compile_pass():
    after=dict(target=dict(static_model_issues=[]),plan=dict(unknown=[],plugins=[]),test_closure=dict(unresolved=[],dependency_profile_uncertainties=[]),changed_compile_plugin_closure=dict(issues=[]),missing_paths=[])
    q=e.decision(None,after,None,dict(status='FITS_128_MIB'))
    assert q['status']=='PASS_STATIC_T_PLUS_90_READINESS' and not q['compile_success']
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


def test_exact_junit_bom_resolves_exact_engine_api_parent_metadata(tmp_path):
    documents={('g','base','1'):b'<project><groupId>g</groupId><artifactId>base</artifactId><version>1</version><packaging>pom</packaging></project>',
      ('org.junit','junit-bom','5.11.2'):b'<project><groupId>org.junit</groupId><artifactId>junit-bom</artifactId><version>5.11.2</version><packaging>pom</packaging><dependencyManagement><dependencies><dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-api</artifactId><version>5.11.2</version></dependency></dependencies></dependencyManagement></project>',
      ('org.junit.jupiter','junit-jupiter-engine','5.11.2'):b'<project><parent><groupId>g</groupId><artifactId>base</artifactId><version>1</version></parent><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-engine</artifactId><version>5.11.2</version><dependencyManagement><dependencies><dependency><groupId>org.junit</groupId><artifactId>junit-bom</artifactId><version>5.11.2</version><scope>import</scope><type>pom</type></dependency></dependencies></dependencyManagement><dependencies><dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-api</artifactId></dependency></dependencies></project>',
      ('org.junit.jupiter','junit-jupiter-api','5.11.2'):b'<project><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-api</artifactId><version>5.11.2</version></project>'}
    class Cache:
        cache=tmp_path;used_paths=set();records={}
        def get(self,g,a,v,extension='pom',classifier=''):
            key=(g,a,v)
            assert key in documents
            path=relative_path(g,a,v,extension,classifier);self.used_paths.add(path);self.records[path]={}
            raw=documents[key] if extension=='pom' else b'fixture_not_executed'
            p=self.cache/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            return raw
    root=dict(gav=['org.junit.jupiter','junit-jupiter-engine','5.11.2'],scope='test',type='jar',classifier='',optional=False,exclusions=[])
    q=e.seed.static_closure(Cache(),[root],{})
    assert {tuple(r['gav']) for r in q['edges']}=={('org.junit.jupiter','junit-jupiter-engine','5.11.2'),('org.junit.jupiter','junit-jupiter-api','5.11.2')}
    assert not q['missing'] and not q['unresolved']
    assert any(r['path']==relative_path('org.junit','junit-bom','5.11.2') for r in q['pom_metadata'])
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


def test_frozen_138_tracked_and_36_java_population_matches_registered_identity():
    import gzip
    base=Path(__file__).resolve().parents[1]
    registry=json.loads(gzip.decompress((base/'examples/phase5_2_1/source_inventory.json.gz').read_bytes()))
    state=next(s for s in registry['source_states'] if s['commit_sha']==e.COMMIT)
    entries=state['inventory']['entries']
    assert state['tree_sha']==e.TREE and state['offset_days']==90
    assert len(entries)==len({r['path'] for r in entries})==138
    assert sum(r['path'].startswith('src/main/') and r['path'].endswith('.java') for r in entries)==36
    assert all(r['mode'] in ('100644','100755') for r in entries)
    q=json.loads((base/'examples/phase5_2_2_d/requirements.json').read_text())
    target=next(s for s in q['states'] if s['commit_sha']==e.COMMIT)
    assert target['pom_sha256']==e.POM and target['parent_version']=='78'
    assert ('org.apache.commons','commons-text','1.13.0') in {tuple(r['gav']) for r in target['declared_dependencies']}
    assert all(r['scope']=='test' for r in target['declared_dependencies'])


def test_all_five_read_only_build_auditors_are_required(monkeypatch):
    import tools.verify_compile_e06 as t0
    import tools.verify_compile_e11 as t30
    import tools.verify_compile_e21 as t90
    import tools.verify_compile_e31 as tplus30
    import tools.verify_compile_e41 as tplus60
    calls=[]
    def read_only(root):calls.append(str(root));return dict(status='COMPILE_PASS')
    for module in (t0,t30,t90,tplus30,tplus60):monkeypatch.setattr(module,'audit',read_only)
    monkeypatch.setattr(e,'sha',lambda p:'0'*64)
    q=e.verify_successful_builds()
    assert set(q)=={'t0','tminus30','tminus90','tplus30','tplus60'} and len(calls)==5
    assert all(row['status']=='COMPILE_PASS' and row['claim_sha256']=='0'*64 for row in q.values())


def test_unknown_legacy_compile_phase_resolved_from_target_descriptor(tmp_path):
    directory=tmp_path/'examples/phase5_2_2_d';directory.mkdir(parents=True)
    def plugin(artifact,phase):
        return dict(gav=['g',artifact,'1'],required_through_compile=None,dependencies=[dict(gav=['g',artifact+'-dep','1'],type='jar',classifier='',reason='fixture')])
    registration=dict(commit_sha=e.COMMIT,tree_sha=e.TREE,pom_sha256=e.POM,parent_version='78',plugins=[plugin('enforcer','validate'),plugin('jar','package')])
    (directory/'requirements.json').write_text(json.dumps(dict(states=[registration])))
    plan=dict(plugins=[dict(gav=['g',name,'1'],missing_paths=[],configured_executions=[dict(phase=phase)],default_bindings=[]) for name,phase in [('enforcer','validate'),('jar','package')]])
    class Cache:records={}
    rows=e.registered_candidates(tmp_path,Cache(),plan)
    assert len(rows)==2 and all(r['gav'][1]=='enforcer-dep' for r in rows)
    assert all(r['legacy_required_through_compile'] is None and r['target_descriptor_requires_compile'] for r in rows)


def test_only_target_and_tplus60_baseline_are_compared():
    assert not hasattr(e,'later_common_requirements')
    code=inspect.getsource(e.audit)
    assert 't0q' not in code and 'tplus60' in code and 'later_common' not in code
    assert 'phase5_2_2_e_4/2026-10-19/source' in code


def test_prior_753_artifacts_and_future_cache_cap_are_immutable():
    base=Path(__file__).resolve().parents[1]
    rows=json.loads((base/'examples/phase5_2_2_e_4/dependency_manifest.json').read_text())['artifacts']
    capacity=e.previous.runtime_capacity(rows)
    assert capacity['estimated_total_bytes']==102371328
    assert capacity['metadata_reserve_bytes']==16*1024**2
    assert capacity['limit_bytes']==128*1024**2
    assert capacity['status']=='FITS_128_MIB'


def test_plugin_parent_metadata_is_independent_of_prior_cache_reads(monkeypatch):
    rows=[dict(gav=['g',name,'1'],executions=[],default_bindings=[],configuration='fixture') for name in ('one','two')]
    monkeypatch.setattr(e,'plugin_rows',lambda model:(rows,[]))
    monkeypatch.setattr(e.previous,'descriptor',lambda a,gav:dict(mojos=[]))
    monkeypatch.setattr(e.reference,'buildplan_tasks',lambda a,model:dict(selected='deploy'))
    class Cache:
        cache=Path('/fixture');records={relative_path(*r['gav'],ext):{} for r in rows for ext in ('pom','jar')}
        used_paths={'g/shared-parent/1/shared-parent-1.pom'}
        def get(self,g,a,v,ext='pom',classifier=''):
            self.used_paths.add(relative_path(g,a,v,ext,classifier));return b'fixture'
    calls=[]
    def inspect_plugin(scoped,row):
        assert scoped.used_paths==set()
        scoped.get('g','shared-parent','1')
        calls.append(set(scoped.used_paths))
        return dict(gav=row['gav'],metadata_paths=sorted(scoped.used_paths))
    monkeypatch.setattr(e.descriptor_tools,'inspect_plugin',inspect_plugin)
    cache=Cache();first=e.plan_inventory(cache,{})
    cache.used_paths.add('another/prior/read.pom');second=e.plan_inventory(cache,{})
    assert first==second and len(calls)==4
    assert all(row['metadata_paths']==['g/shared-parent/1/shared-parent-1.pom'] for row in first['plugins'])


def test_exact_commons_text_transitive_version_and_test_scope_nonpropagation(tmp_path):
    docs={('org.apache.commons','commons-text','1.13.0'):b'<project><groupId>org.apache.commons</groupId><artifactId>commons-text</artifactId><version>1.13.0</version><dependencies><dependency><groupId>org.apache.commons</groupId><artifactId>commons-lang3</artifactId><version>3.17.0</version></dependency><dependency><groupId>g</groupId><artifactId>own-test</artifactId><version>1</version><scope>test</scope></dependency><dependency><groupId>g</groupId><artifactId>optional</artifactId><version>1</version><optional>true</optional></dependency></dependencies></project>',
          ('org.apache.commons','commons-lang3','3.17.0'):b'<project><groupId>org.apache.commons</groupId><artifactId>commons-lang3</artifactId><version>3.17.0</version></project>'}
    class Cache:
        cache=tmp_path;records={};used_paths=set()
        def get(self,g,a,v,extension='pom',classifier=''):
            assert (g,a,v) in docs,'Unjustified test/optional closure or wrong version'
            raw=docs[(g,a,v)] if extension=='pom' else b'unit_fixture_not_executed'
            path=relative_path(g,a,v,extension,classifier);self.records[path]={};self.used_paths.add(path)
            p=self.cache/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);return raw
    root=dict(gav=['org.apache.commons','commons-text','1.13.0'],scope='test',type='jar',classifier='',optional=False,exclusions=[])
    result=e.seed.static_closure(Cache(),[root],{})
    assert {tuple(r['gav']) for r in result['edges']}==set(docs)
    assert not result['missing'] and not result['unresolved'] and not result['resolved_runtime_classpath']


def test_comparison_records_mode_and_test_resource_changes_without_compiler_claims():
    left=dict(parent_chain=[],imports=[],dependencies=[],dependency_management=[],profiles=[],plugins=[],build_sections=[],properties={},source=dict(source_entries=[dict(path='src/test/Foo.txt',sha256='a',mode='100644')]))
    right=copy.deepcopy(left);right['source']['source_entries'][0].update(sha256='b',mode='100755')
    q=e.comparison(left,right,'t_plus60')
    assert q['source_changes']['mode_changes']['src/test/Foo.txt']==dict(t_plus60='100644',t_plus90='100755')
    assert q['source_changes']['changed_test_files']==['src/test/Foo.txt']
    assert q['actual_tplus90_effective_pom_sha256'] is None


@pytest.mark.parametrize('mutation',['none','runtime_edge','management','direct_property_consumer',
    'inherited_consumer','property_alias','activation_consumer','unknown_section','extra_profile','wrong_artifact'])
def test_remote_own_test_profile_scope_is_proven_without_guessing_activation(mutation):
    profiles=''.join('<profile><id>'+name+'</id><activation><jdk>[11,22)</jdk></activation>'
        '<properties><test.version>1</test.version></properties><dependencies><dependency>'
        '<groupId>g</groupId><artifactId>own-test</artifactId><version>${test.version}</version>'
        '<scope>test</scope></dependency></dependencies></profile>'
        for name in ('java-8-10','java-11-21','java-22-up'))
    parent='<project><groupId>g</groupId><artifactId>parent</artifactId><version>1</version></project>'
    dependency='<dependencies><dependency><groupId>g</groupId><artifactId>runtime</artifactId><version>${test.version}</version></dependency></dependencies>'
    extra=''
    if mutation=='runtime_edge':profiles=profiles.replace('<scope>test</scope>','<scope>runtime</scope>',1)
    if mutation=='management':profiles=profiles.replace('</profile>','<dependencyManagement/></profile>',1)
    if mutation=='direct_property_consumer':extra=dependency
    if mutation=='inherited_consumer':parent=parent.replace('</project>',dependency+'</project>')
    if mutation=='property_alias':extra='<properties><alias>${test.version}</alias></properties>'+dependency.replace('${test.version}','${alias}')
    if mutation=='activation_consumer':profiles=profiles.replace('<jdk>[11,22)</jdk>','<property><name>test.version</name></property>',1)
    if mutation=='unknown_section':profiles=profiles.replace('</profile>','<repositories/></profile>',1)
    if mutation=='extra_profile':profiles+='<profile><id>other</id>'+dependency+'</profile>'
    child=('<project><parent><groupId>g</groupId><artifactId>parent</artifactId><version>1</version></parent>'
        '<groupId>org.apache.commons</groupId><artifactId>commons-text</artifactId><version>1.13.0</version>'
        +extra+'<profiles>'+profiles+'</profiles></project>')
    class Cache:
        def get(self,*gav):return (parent if gav[1]=='parent' else child).encode()
    issue=dict(status='UNKNOWN_REMOTE_DESCRIPTOR_DEPENDENCY_PROFILE_ACTIVATION',
        path=relative_path('org.apache.commons','commons-text','1.13.0'),profiles=['java-8-10','java-11-21','java-22-up'])
    if mutation=='wrong_artifact':issue['path']=relative_path('g','other','1')
    row=e.issue_relevance(Cache(),[issue])[0]
    assert row['activation']=='UNKNOWN_NOT_MAVEN_EVALUATED'
    assert row['blocking']==(mutation!='none')
    if mutation=='none':
        assert row['scope_evidence']['non_test_coordinate_consumers']==0
        assert all(p['activation']=='UNKNOWN_NOT_MAVEN_EVALUATED' for p in row['scope_evidence']['profiles'])


def test_real_frozen_source_difference_and_original_antrun_declaration():
    folder=Path(__file__).resolve().parents[1]/'examples/phase5_2_2_e_5'
    comparison=json.loads((folder/'configuration_difference.json').read_text())['tplus60_vs_tplus90']
    changes=comparison['source_changes']
    assert not changes['added'] and not changes['removed'] and not changes['mode_changes']
    assert set(changes['changed_production_java'])=={
        'src/main/java/org/apache/commons/cli/CommandLine.java','src/main/java/org/apache/commons/cli/Option.java'}
    assert len(changes['changed'])==11 and len(changes['changed_test_files'])==4
    plugins=json.loads((folder/'buildplan_descriptor_verification.json').read_text())
    antrun=next(r for r in plugins['plugins'] if r['gav'][1]=='maven-antrun-plugin')
    assert antrun['gav'][2]=='3.1.0' and antrun['expected_goals_verified']
    assert plugins['selected_tasks']['selected']=='deploy' and not plugins['actual_maven_plan_calculated']


def test_real_recovered_cache_identity_and_honest_profile_qualification():
    folder=Path(__file__).resolve().parents[1]/'examples/phase5_2_2_e_5'
    manifest=json.loads((folder/'dependency_manifest.json').read_text())
    identity=json.loads((folder/'cache_identity.json').read_text())
    assert len(manifest['artifacts'])==758 and manifest['requests']==17
    assert hashlib.sha256((folder/'dependency_manifest.json').read_bytes()).hexdigest()==identity['manifest_sha256']
    assert identity['seed_count']==753 and identity['canonical_sha256']=='df9f176ceeea2f165cbf463dd3eb43675741b0932d1134c756386f0f7259462d'
    proof=json.loads((folder/'profile_scope_verification.json').read_text())
    assert proof['initial_status']=='PARTIAL' and proof['final_status']=='PASS_STATIC_T_PLUS_90_READINESS'
    assert proof['extra_requests']==0 and proof['raw_audit_and_acquisition_manifest_unchanged']
    assert all(not row['blocking'] and row['activation']=='UNKNOWN_NOT_MAVEN_EVALUATED' for row in proof['evidence'])
