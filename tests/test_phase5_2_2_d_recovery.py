"""Task D proof with fake repository responses; never network/Maven/JAR execution."""
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
import pytest
from tools.maven_recovery import acquisition as acq
from tools.maven_recovery.model import Models, activation, expand, jdk_matches, merge_xml, text
from tools import recover_phase5_2_2_d as driver


@pytest.fixture(autouse=True)
def prohibit_real_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Unit tests must not perform network I/O')
    monkeypatch.setattr(urllib.request.OpenerDirector, 'open', forbidden)


@pytest.mark.parametrize('gav',[
    ('org.test','x','LATEST'),('org.test','x','RELEASE'),('org.test','x','1-SNAPSHOT'),
    ('org.test','x','[1,2)'),('org.test','x','${version}'),('org.test','../x','1'),
    ('org..test','x','1'),('https://evil','x','1'),('org.test','x',None)])
def test_exact_coordinates_only(gav):
    with pytest.raises(ValueError):acq.relative_path(*gav)


def test_fixed_https_coordinates_and_classifier():
    assert acq.CENTRAL=='https://repo.maven.apache.org/maven2/'
    assert acq.relative_path('org.apache.commons','commons-parent','71')=='org/apache/commons/commons-parent/71/commons-parent-71.pom'
    assert acq.relative_path('g','a','1','jar','tests')=='g/a/1/a-1-tests.jar'
    with pytest.raises(ValueError):acq.relative_path('g','a','1','exe')
    with pytest.raises(ValueError):acq.NoRedirect().redirect_request(None,None,None,None,None,None)


def test_xml_entities_never_expanded():
    with pytest.raises(ValueError):acq.parse_xml(b'<!DOCTYPE p [<!ENTITY x "boom">]><p>&x;</p>')


def test_old_namespace_free_poms_do_not_hide_transitive_dependencies():
    class Fake:
        def get(self,*args):raise AssertionError('Pure model inspection only')
    raw=b'<project><groupId>g</groupId><artifactId>a</artifactId><version>1</version><dependencies><dependency><groupId>g</groupId><artifactId>legacy-lib</artifactId><version>2</version></dependency></dependencies></project>'
    model=Models(Fake()).build(acq.parse_xml(raw),[],{},['fixture'])
    assert model['dependencies'][0]['gav']==['g','legacy-lib','2']
    assert acq.parse_xml(b'<plugin><mojos/></plugin>').tag=='plugin'


def pom(g='g',a='a',v='1',body=''):
    return (f'<project xmlns="http://maven.apache.org/POM/4.0.0"><groupId>{g}</groupId>'
            f'<artifactId>{a}</artifactId><version>{v}</version>{body}</project>').encode()


def fake_fetch(a,raw,*,checksum=None):
    def fetch(path,limit):
        if path.endswith('.sha512'):
            return (checksum or hashlib.sha512(raw).hexdigest()).encode()
        return raw
    a.fetch=fetch


def test_checksum_and_coordinate_validation_before_publication(tmp_path):
    a=acq.Acquisition(tmp_path/'cache');raw=pom();fake_fetch(a,raw,checksum='0'*128)
    with pytest.raises(ValueError,match='checksum mismatch'):a.get('g','a','1')
    assert not list(a.cache.rglob('*.pom'))
    fake_fetch(a,pom(a='other'))
    with pytest.raises(ValueError,match='coordinate mismatch'):a.get('g','a','1')
    assert not a.records


def test_verified_artifact_hash_and_resume_tamper_rejection(tmp_path):
    a=acq.Acquisition(tmp_path/'cache');raw=pom();fake_fetch(a,raw)
    assert a.get('g','a','1')==raw
    row=next(iter(a.records.values()))
    assert row['sha256']==hashlib.sha256(raw).hexdigest()
    assert row['source_url']==acq.CENTRAL+row['path']
    a.seal();b=acq.Acquisition(a.root,resume=True)
    assert b.get('g','a','1')==raw
    (a.cache/row['path']).write_bytes(b'changed')
    with pytest.raises(ValueError,match='integrity'):acq.Acquisition(a.root,resume=True)


def test_existing_or_symlink_cache_never_reused_implicitly(tmp_path):
    acq.Acquisition(tmp_path/'cache')
    with pytest.raises(FileExistsError):acq.Acquisition(tmp_path/'cache')
    (tmp_path/'link').symlink_to(tmp_path/'cache',target_is_directory=True)
    with pytest.raises(ValueError):acq.Acquisition(tmp_path/'link',resume=True)


def test_cache_outside_git_and_user_caches(tmp_path):
    (tmp_path/'.git').mkdir()
    with pytest.raises(ValueError,match='outside Git'):acq.Acquisition(tmp_path/'cache')
    with pytest.raises(ValueError,match='read-only'):acq.Acquisition('/home/hp/.m2/task-d-must-not-create')


def test_redirect_response_identity_and_size_caps(tmp_path):
    class Response:
        status=200
        headers={}
        def geturl(self):return 'https://unapproved.example/file'
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):raise AssertionError('Must reject before reading')
    class Opener:
        def open(self,*args,**kwargs):return Response()
    a=acq.Acquisition(tmp_path/'cache');a.opener=Opener()
    with pytest.raises(ValueError,match='response'):a.fetch('g/a/1/a-1.pom',100)
    Response.geturl=lambda _: acq.CENTRAL+'g/a/1/a-1.pom'
    Response.headers={'Content-Length':'101'}
    with pytest.raises(acq.BudgetExceeded):a.fetch('g/a/1/a-1.pom',100)


def test_jar_crc_and_xml_coordinate_failure_rejected(tmp_path):
    a=acq.Acquisition(tmp_path/'cache');fake_fetch(a,b'not a jar')
    with pytest.raises(__import__('zipfile').BadZipFile):a.get('g','a','1','jar')
    assert not a.records and not list(a.cache.rglob('*.jar'))


def test_request_cap_is_fatal_and_precedes_network(tmp_path,monkeypatch):
    a=acq.Acquisition(tmp_path/'cache');monkeypatch.setattr(acq,'MAX_REQUESTS',0)
    with pytest.raises(acq.BudgetExceeded):a.fetch('g/a/1/a-1.pom',100)
    assert a.requests==0


def test_transport_retries_bounded_and_no_repository_fallback(tmp_path,monkeypatch):
    class Opener:
        urls=[]
        def open(self,request,timeout):
            self.urls.append(request.full_url)
            raise urllib.error.URLError('fixture timeout')
    a=acq.Acquisition(tmp_path/'cache');a.opener=Opener();monkeypatch.setattr(acq.time,'sleep',lambda _:None)
    with pytest.raises(urllib.error.URLError):a.fetch('g/a/1/a-1.pom',100)
    assert len(a.opener.urls)==a.requests==3
    assert len(set(a.opener.urls))==1 and all(u.startswith(acq.CENTRAL) for u in a.opener.urls)
    assert len(a.transport_failures)==3


@pytest.mark.parametrize('path',['https://evil/file','../file','g/%2e%2e/a','g/a?token=x'])
def test_allowlist_cannot_be_bypassed(tmp_path,path):
    a=acq.Acquisition(tmp_path/'cache')
    with pytest.raises(ValueError):a.fetch(path,100)


@pytest.mark.parametrize('spec,expected',[('[9,)',True),('[17,)',True),('(,9)',False),('[1.8,1.9)',False),('11',False),('[1.8]',False),('!1.8',True)])
def test_jdk17_profile_selection(spec,expected):
    assert jdk_matches(spec)==expected


def test_profile_file_and_property_evidence():
    p=acq.parse_xml(b'<profile xmlns="http://maven.apache.org/POM/4.0.0"><activation><file><exists>src/profile</exists></file><jdk>[9,)</jdk></activation></profile>')
    assert activation(p,['src/profile'],{})[0] is True
    assert activation(p,[],{})[0] is False
    unknown=acq.parse_xml(b'<profile xmlns="http://maven.apache.org/POM/4.0.0"><activation><os><family>unix</family></os></activation></profile>')
    assert activation(unknown,[],{})[0] is None
    unsupported=acq.parse_xml(b'<profile xmlns="http://maven.apache.org/POM/4.0.0"><activation><jdk>[9</jdk></activation></profile>')
    assert activation(unsupported,[],{})==(None,"UNSUPPORTED_JDK_ACTIVATION_'[9'")


def test_child_properties_management_and_merged_execution():
    class Fake:
        def get(self,g,a,v):
            assert (g,a,v)==('g','parent','1')
            return pom(a='parent',body='<properties><lib.version>2</lib.version></properties><dependencyManagement><dependencies><dependency><groupId>g</groupId><artifactId>lib</artifactId><version>${lib.version}</version></dependency></dependencies></dependencyManagement>')
    raw=pom(a='child',body='<parent><groupId>g</groupId><artifactId>parent</artifactId><version>1</version></parent><properties><lib.version>3</lib.version></properties><dependencies><dependency><groupId>g</groupId><artifactId>lib</artifactId></dependency></dependencies>')
    model=Models(Fake()).build(acq.parse_xml(raw),[],{},['fixture'])
    assert model['dependencies'][0]['gav']==['g','lib','3']
    assert expand('${x}',{'x':'${y}','y':'1'})=='1'
    assert expand('${missing}',{})=='${missing}'
    parent=acq.parse_xml(b'<plugin xmlns="http://maven.apache.org/POM/4.0.0"><executions><execution><id>x</id><phase>validate</phase></execution></executions></plugin>')
    child=acq.parse_xml(b'<plugin xmlns="http://maven.apache.org/POM/4.0.0"><executions><execution><id>x</id><phase>verify</phase></execution></executions></plugin>')
    merged=merge_xml(parent,child)
    ns={'m':'http://maven.apache.org/POM/4.0.0'}
    assert merged.findtext('m:executions/m:execution/m:phase',namespaces=ns)=='verify'


def test_managed_test_scope_never_becomes_plugin_runtime():
    class Fake:
        def get(self,*args):raise AssertionError('No remote input required')
    raw=pom(body='<dependencyManagement><dependencies><dependency><groupId>g</groupId><artifactId>testlib</artifactId><version>2</version><scope>test</scope></dependency></dependencies></dependencyManagement><dependencies><dependency><groupId>g</groupId><artifactId>testlib</artifactId></dependency></dependencies>')
    model=Models(Fake()).build(acq.parse_xml(raw),[],{},['fixture'])
    assert model['dependencies'][0]['gav']==['g','testlib','2']
    assert model['dependencies'][0]['scope']=='test'


def test_transitive_scope_optional_and_exclusions_limit_downloads():
    dependency=lambda a,extra='':f'<dependency><groupId>g</groupId><artifactId>{a}</artifactId><version>1</version>{extra}</dependency>'
    class Fake:
        calls=[]
        def get(self,g,a,v,extension='pom',classifier=''):
            self.calls.append((a,extension))
            if extension=='jar':return b'fixture JAR not executed'
            assert a in ('root','kept')
            return pom(a=a,body=('<dependencies>'+dependency('kept')+dependency('excluded')
                +dependency('optional','<optional>true</optional>')+dependency('testlib','<scope>test</scope>')+'</dependencies>') if a=='root' else '')
    a=Fake();models=Models(a)
    root=dict(gav=['g','root','1'],type='jar',classifier='',exclusions=[['g','excluded']])
    result=models.closure([root],'fixture')
    assert {r['gav'][1] for r in result}=={'root','kept'}
    assert {r[0] for r in a.calls}=={'root','kept'}
    assert not models.issues


def test_budget_failure_not_downgraded_to_missing_dependency():
    class Fake:
        def get(self,*args):raise acq.BudgetExceeded('stop')
    row=dict(gav=['g','a','1'],type='jar',classifier='',exclusions=[])
    with pytest.raises(acq.BudgetExceeded):Models(Fake()).closure([row],'fixture')


def test_missing_compile_plugin_is_never_marked_unnecessary():
    class Fake:
        def get(self,*args):raise ValueError('OFFLINE_MISSING')
    models=Models(Fake())
    rows=models.compile_plugins(dict(plugins={},managed_plugins={},properties={}))
    assert {r['gav'][1] for r in rows}=={'maven-resources-plugin','maven-compiler-plugin'}
    assert all(r['disposition']=='UNRESOLVED' and r['required_through_compile'] is True for r in rows)


def test_offline_audit_cannot_contact_repository(tmp_path):
    a=acq.OfflineAcquisition(tmp_path/'cache')
    with pytest.raises(ValueError,match='OFFLINE_MISSING'):a.get('g','a','1')
    assert a.requests==a.bytes==0


def test_unresolved_range_never_selects_a_newer_version():
    class Fake:
        def get(self,*args):raise AssertionError('Range must not be fetched')
    models=Models(Fake());row=dict(gav=['g','a','[1,2)'],type='jar',classifier='',exclusions=[])
    assert models.closure([row],'fixture')==[]
    assert models.issues[0]['identity']==['g','a','[1,2)']


def test_parent_cycle_rejected_without_execution():
    class Fake:
        def get(self,*args):return pom(body='<parent><groupId>g</groupId><artifactId>a</artifactId><version>1</version></parent>')
    with pytest.raises(ValueError,match='cycle'):Models(Fake()).remote(['g','a','1'])


def test_driver_refuses_unbounded_process_before_reading_sources(tmp_path,monkeypatch):
    monkeypatch.setattr(driver.os,'sched_getaffinity',lambda _: {0,1})
    with pytest.raises(ValueError,match='taskset'):driver.recover(tmp_path,tmp_path/'out')


def test_staged_cache_excludes_earlier_unused_candidates_and_preserves_missing(tmp_path):
    a=acq.Acquisition(tmp_path/'cache')
    fake_fetch(a,pom());a.get('g','a','1')
    fake_fetch(a,pom(a='unused'));a.get('g','unused','1');a.seal()
    requested=['g/a/1/a-1.pom','g/missing/1/missing-1.pom']
    (a.root/'requirements.json').write_text(json.dumps({'accessed_artifact_paths':requested}))
    result=driver.stage_cache(a.root)
    assert (a.root/'admitted-repository/g/a/1/a-1.pom').exists()
    assert not (a.root/'admitted-repository/g/unused').exists()
    assert result['missing_requested_paths']==['g/missing/1/missing-1.pom']
    assert not result['staging_is_build_completeness_proof']
    assert result['artifacts'][1]['disposition']=='EARLIER_UNUSED_CANDIDATE_NOT_STAGED'
    with pytest.raises(ValueError,match='overwrite'):driver.stage_cache(a.root)


def test_published_evidence_matches_pins_and_does_not_claim_build_proof():
    base=Path(__file__).resolve().parents[1]
    public=base/'examples/phase5_2_2_d'
    if not public.exists():
        pytest.fail('Publish verified Task D evidence before final verification')
    requirements=json.loads((public/'requirements.json').read_text())
    reference=json.loads((base/'examples/phase5_2_1/dependency_inspection.json').read_text())
    identity=lambda r:(r['commit_sha'],r['tree_sha'],r['pom_sha256'],r['offset_days'],r['parent_version'])
    assert {identity(r) for r in requirements['states']}=={identity(r) for r in reference['states']}
    assert len(requirements['states'])==6
    assert requirements['project_goals_executed']==0
    assert requirements['status']=='PARTIAL_STATIC_NOT_OFFLINE_BUILD_PROOF'
    manifest=json.loads((public/'dependency_manifest.json').read_text())
    parents={tuple(r['coordinates']) for r in manifest['artifacts']}
    assert all(('org.apache.commons','commons-parent',v) in parents for v in ['71','74','76','78'])
    assert manifest['downloaded_artifacts_executed']==manifest['project_goals_executed']==0
    assert not manifest['user_caches_modified']
    assert len(manifest['cpu_affinity'])==1
    assert manifest['address_space_limit_bytes']==1073741824
    assert manifest['peak_rss_kib']<1048576
    assert len({r['path'] for r in manifest['artifacts']})==len(manifest['artifacts'])
    for row in manifest['artifacts']:
        assert row['path']==acq.relative_path(*row['coordinates'],row['extension'],row['classifier'])
        assert row['source_url']==acq.CENTRAL+row['path']
        assert len(row['sha256'])==64
    requested=set(requirements['accessed_artifact_paths'])
    assert manifest['missing_requested_paths']==sorted(requested-{r['path'] for r in manifest['artifacts']})
    for row in manifest['artifacts']:
        assert (row['disposition']=='STAGED_STATIC_CANDIDATE')==(row['path'] in requested)
    assert not list(public.rglob('*.jar')) and not list(public.rglob('*.pom'))
    seal=json.loads((public/'manifest.json').read_text())
    for name,digest in seal['artifacts'].items():
        assert hashlib.sha256((public/name).read_bytes()).hexdigest()==digest
