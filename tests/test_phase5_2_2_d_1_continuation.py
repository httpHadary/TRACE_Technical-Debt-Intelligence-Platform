"""No network/project execution: Task D.1 copy, accounting and offline gates."""
import hashlib
import json
import urllib.error
import urllib.request
import pytest
from tools.maven_recovery import acquisition as original
from tools.maven_recovery import continuation as c
from tools import recover_phase5_2_2_d_1 as driver


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Real network forbidden in tests')
    monkeypatch.setattr(urllib.request.OpenerDirector,'open',forbidden)


def pom(a='seed'):
    return f'<project><groupId>g</groupId><artifactId>{a}</artifactId><version>1</version></project>'.encode()


@pytest.fixture
def seeded(tmp_path):
    source=tmp_path/'task-d';a=original.Acquisition(source);raw=pom()
    a.fetch=lambda path,limit:hashlib.sha512(raw).hexdigest().encode() if path.endswith('.sha512') else raw
    a.get('g','seed','1');a.requests=2000;manifest=a.seal()
    return source,manifest


def test_independent_seed_copy_and_distinct_accounting(tmp_path,seeded):
    source,manifest=seeded;before=(source/'dependency_manifest.json').read_bytes()
    a=c.Continuation(tmp_path/'new',source,manifest)
    record=next(iter(a.records.values()));left=source/'repository'/record['path'];right=a.cache/record['path']
    assert left.read_bytes()==right.read_bytes() and left.stat().st_ino!=right.stat().st_ino
    assert a.requests==a.bytes==0 and len(a.seed_paths)==1
    assert a.get('g','seed','1')==pom() and a.requests==0
    assert (source/'dependency_manifest.json').read_bytes()==before
    assert a.seal()['parent_task_d']['requests']==2000
    assert original.MAX_REQUESTS==2000 and c.MAX_REQUESTS==400


def test_no_original_cache_overwrite_or_implicit_resume(tmp_path,seeded):
    source,manifest=seeded
    with pytest.raises(ValueError,match='separate'):c.Continuation(source,source,manifest)
    with pytest.raises(ValueError,match='separate'):c.Continuation(source/'nested',source,manifest)
    assert not (source/'nested').exists()
    a=c.Continuation(tmp_path/'new',source,manifest)
    with pytest.raises(FileExistsError):c.Continuation(a.root,source,manifest)


@pytest.mark.parametrize('target',['bytes','published_sha','old_accounting'])
def test_seed_tampering_and_wrong_parent_ledger_rejected(tmp_path,seeded,target):
    source,manifest=seeded
    if target=='bytes':
        (source/'repository/g/seed/1/seed-1.pom').write_bytes(b'changed')
    elif target=='published_sha':manifest['artifacts'][0]['sha256']='0'*64
    else:
        data=json.loads((source/'dependency_manifest.json').read_text());data['requests']=1999
        (source/'dependency_manifest.json').write_text(json.dumps(data))
    with pytest.raises(ValueError):c.Continuation(tmp_path/'new',source,manifest)


def test_offline_audit_and_budget_never_open_connection(tmp_path,seeded):
    a=c.Continuation(tmp_path/'new',*seeded)
    with pytest.raises(ValueError,match='OFFLINE_MISSING'):a.get('g','missing','1')
    assert a.requests==0
    a.network_enabled=True;a.requests=400
    with pytest.raises(c.BudgetExceeded):a.fetch('g/missing/1/missing-1.pom',100)
    assert a.requests==400 and a.bytes==0


class Response:
    status=200
    def __init__(self,path,raw):self.path=path;self.raw=raw;self.headers={'Content-Length':str(len(raw))}
    def geturl(self):return original.CENTRAL+self.path
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n):value=self.raw[:n];self.raw=self.raw[n:];return value


def test_all_checksum_probes_share_the400_limit(tmp_path,seeded):
    a=c.Continuation(tmp_path/'new',*seeded);raw=pom('new');urls=[]
    class Opener:
        def open(self,request,timeout):
            path=request.full_url.removeprefix(original.CENTRAL);urls.append(path)
            if path.endswith(('.sha512','.sha256')):raise urllib.error.HTTPError(request.full_url,404,'fixture',None,None)
            return Response(path,hashlib.sha1(raw).hexdigest().encode() if path.endswith('.sha1') else raw)
    a.opener=Opener();a.network_enabled=True
    a.get('g','new','1');assert a.requests==len(urls)==4
    a.get('g','new','1');assert a.requests==4
    assert a.seal()['new_count']==1 and a.seal()['seed_count']==1


def test_payload_cap_rejects_before_read_without_exceeding96mib(tmp_path,seeded):
    a=c.Continuation(tmp_path/'new',*seeded);a.network_enabled=True;a.bytes=c.MAX_BYTES-5
    class Opener:
        def open(self,request,timeout):return Response('g/a/1/a-1.pom',b'123456')
    a.opener=Opener()
    with pytest.raises(c.BudgetExceeded):a.fetch('g/a/1/a-1.pom',32*1024*1024)
    assert a.bytes==c.MAX_BYTES-5


def test32mib_artifact_limit_rejects_before_body(tmp_path,seeded):
    a=c.Continuation(tmp_path/'new',*seeded);a.network_enabled=True
    class Opener:
        def open(self,request,timeout):
            r=Response('g/a/1/a-1.pom',b'')
            r.headers={'Content-Length':str(32*1024*1024+1)}
            r.read=lambda n:pytest.fail('Oversized body must not be read')
            return r
    a.opener=Opener()
    with pytest.raises(c.BudgetExceeded):a.fetch('g/a/1/a-1.pom',32*1024*1024)
    assert a.bytes==0


def test_checksum_budget_exhaustion_does_not_admit_unverified_artifact(tmp_path,seeded):
    a=c.Continuation(tmp_path/'new',*seeded);a.network_enabled=True;a.requests=399
    class Opener:
        def open(self,request,timeout):return Response('g/new/1/new-1.pom',pom('new'))
    a.opener=Opener()
    with pytest.raises(c.BudgetExceeded):a.get('g','new','1')
    assert a.requests==400 and len(a.records)==1
    assert not (a.cache/'g/new/1/new-1.pom').exists()


def test_retry_attempts_are_bounded_and_counted(tmp_path,seeded,monkeypatch):
    a=c.Continuation(tmp_path/'new',*seeded);a.network_enabled=True
    class Opener:
        def open(self,*args,**kwargs):raise urllib.error.URLError('fixture timeout')
    a.opener=Opener();monkeypatch.setattr(c.time,'sleep',lambda _:None)
    with pytest.raises(urllib.error.URLError):a.fetch('g/a/1/a-1.pom',100)
    assert a.requests==3 and len(a.transport_failures)==3


def test_redirect_response_cannot_escape_allowlist(tmp_path,seeded):
    a=c.Continuation(tmp_path/'new',*seeded);a.network_enabled=True
    class Opener:
        def open(self,*args,**kwargs):
            r=Response('g/a/1/a-1.pom',b'123');r.geturl=lambda:'https://unapproved.example/data';return r
    a.opener=Opener()
    with pytest.raises(ValueError,match='response'):a.fetch('g/a/1/a-1.pom',100)


def test_frontier_identity_not_nearest_or_newer_version():
    value='org/apache/maven/plugins/maven-resources-plugin/3.3.1/maven-resources-plugin-3.3.1.pom'
    assert driver.frontier_coordinate(value)==('org.apache.maven.plugins','maven-resources-plugin','3.3.1','pom')
    with pytest.raises(ValueError):driver.frontier_coordinate(value.replace('3.3.1.pom','3.3.2.pom'))


def test_driver_requires_resource_limits_before_any_source_read(tmp_path,monkeypatch):
    monkeypatch.setattr(driver.os,'sched_getaffinity',lambda _: {0,1})
    with pytest.raises(ValueError,match='Require one CPU'):driver.execute(tmp_path,tmp_path/'out')


def test_disk_budget_is_fatal_without_writing_more_artifacts(tmp_path,seeded):
    a=c.Continuation(tmp_path/'new',*seeded)
    with pytest.raises(c.BudgetExceeded,match='disk cap'):a.check_disk(c.MAX_DISK)
    assert a.requests==0 and len(a.records)==1


def test_readonly_reverification_preserves_accounting_and_rejects_tampering(tmp_path,seeded):
    a=c.Continuation(tmp_path/'new',*seeded);a.seal();before=(a.root/'dependency_manifest.json').read_bytes()
    reader=c.ReadOnlyCache(a.root)
    assert reader.get('g','seed','1')==pom()
    with pytest.raises(ValueError,match='OFFLINE_MISSING'):reader.get('g','missing','1')
    assert (a.root/'dependency_manifest.json').read_bytes()==before
    (a.cache/'g/seed/1/seed-1.pom').write_bytes(b'changed')
    with pytest.raises(ValueError):c.ReadOnlyCache(a.root)


def test_conditional_profiles_remain_unknown_and_do_not_become_required(tmp_path):
    path='g/parent/1/parent-1.pom';p=tmp_path/'repository'/path;p.parent.mkdir(parents=True)
    raw=b'<project><groupId>g</groupId><artifactId>parent</artifactId><version>1</version><profiles><profile><id>conditional</id><activation><os><family>unix</family></os></activation><dependencies><dependency><groupId>x</groupId><artifactId>conditional-lib</artifactId><version>${unresolved}</version></dependency></dependencies></profile></profiles></project>'
    p.write_bytes(raw)
    profile=dict(model=['g','parent','1'],id='conditional',active=None,reason='UNSUPPORTED_ACTIVATION_os')
    state=dict(commit_sha='a'*40,tree_sha='b'*40,pom_sha256='c'*64,offset_days=0,parent_version='1',compile_dependency_readiness='UNKNOWN',offline_build_readiness='UNKNOWN',missing_paths=[],unknown_profiles=[profile],plugins=[])
    result=dict(states=[state],required_compile_candidates=[],later_phase_descriptor_paths=[],accessed_artifact_paths=[path],optional_or_nonruntime=[],missing_paths=[])
    manifest=dict(artifacts=[dict(path=path,sha256=hashlib.sha256(raw).hexdigest())],http_events=[])
    categories,matrix=driver.classify(result,manifest,tmp_path)
    assert matrix[0]['offline_build_readiness']=='UNKNOWN'
    assert categories['conditional_profile_declarations'][0]['status']=='UNKNOWN'
    assert categories['conditional_profile_declarations'][0]['declarations'][0]['gav'][2]=='${unresolved}'
    assert not categories['required_compile_static_candidates']


def test_published_batch_frontier_matrix_and_accounting_are_consistent():
    from pathlib import Path
    base=Path(__file__).resolve().parents[1];public=base/'examples/phase5_2_2_d_1'
    manifest=json.loads((public/'dependency_manifest.json').read_text())
    comparison=json.loads((public/'frontier_comparison.json').read_text())
    matrix=json.loads((public/'compile_readiness_matrix.json').read_text())
    old=json.loads((base/'examples/phase5_2_2_d/readiness_manifest.json').read_text())
    assert comparison['before']==old['missing_requested_paths'] and len(comparison['before'])==22
    assert manifest['parent_task_d']['requests']==2000 and manifest['requests']==400
    assert manifest['seed_count']==509 and manifest['new_count']==102
    assert manifest['transferred_bytes']<=96*1024*1024
    assert manifest['limits']['max_requests']==400 and len(manifest['cpu_affinity'])==1
    assert manifest['address_space_limit_bytes']==1073741824
    assert len(comparison['resolved_original'])==21 and len(comparison['after'])==2
    assert len(matrix)==6 and all(s['offline_build_readiness']=='BLOCKED' for s in matrix)
    prior=json.loads((base/'examples/phase5_2_2_d/requirements.json').read_text())
    identity=lambda s:(s['commit_sha'],s['tree_sha'],s['pom_sha256'],s['offset_days'])
    assert {identity(s) for s in matrix}=={identity(s) for s in prior['states']}
    for row in matrix:assert row['missing_paths']==comparison['after'] and row['unknown_profile_count']>0
    jar=next(d for d in comparison['descriptors'] if d['gav']==list(driver.JAR_PLUGIN))
    assert not jar['executed']
    assert all(g['phase']=='package' for g in jar['goals'] if g['goal'] in ('jar','test-jar'))
    priorities=json.loads((public/'priority_plugin_readiness.json').read_text())
    assert len(priorities)==3 and all(p['static_known_artifacts_verified'] for p in priorities)
    assert all(p['offline_build_readiness']=='UNKNOWN' for p in priorities)
    seal=json.loads((public/'manifest.json').read_text())
    for name,h in seal['artifacts'].items():assert c.digest(public/name)==h
    assert not list(public.rglob('*.pom')) and not list(public.rglob('*.jar'))


def test_missing_compile_dependency_is_not_misclassified_as_metadata(tmp_path):
    path='g/missing/1/missing-1.jar'
    result=dict(states=[],required_compile_candidates=[],later_phase_descriptor_paths=[],
        accessed_artifact_paths=[path],optional_or_nonruntime=[],missing_paths=[path],
        unresolved=[dict(kind='DEPENDENCY',identity=['g','missing','1'],reason='OFFLINE_MISSING: '+path)])
    categories,_=driver.classify(result,dict(artifacts=[],http_events=[]),tmp_path)
    assert path in categories['required_compile_static_candidates']
    assert not categories['model_or_configuration_metadata']
