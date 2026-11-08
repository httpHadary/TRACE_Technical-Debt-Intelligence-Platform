"""D.3 boundaries: no container, downloaded code or network in these tests."""
import io
import json
from pathlib import Path
import zipfile
import pytest
from tools import inspect_phase5_2_2_d_3 as d


@pytest.mark.parametrize('goal', d.GOALS)
def test_command_is_pinned_offline_model_only(goal):
    cmd=d.maven_command(goal)
    assert cmd[-1]=='org.apache.maven.plugins:maven-help-plugin:3.5.1:'+goal
    assert '--offline' in cmd and '-Dmaven.compiler.release=8' in cmd
    assert '-Dmaven.test.skip=true' in cmd and '-Duser.home=/tmp' in cmd
    assert not any(v in cmd for v in ('compile','validate','verify','package','install','-P'))


@pytest.mark.parametrize('goal', ['compile','validate','all-profiles','effective-settings','help:effective-pom',''])
def test_unapproved_goals_rejected(goal):
    with pytest.raises(ValueError):d.maven_command(goal)


def test_seed_rejects_wrong_manifest_before_copy(tmp_path):
    source=tmp_path/'source';source.mkdir()
    (source/'dependency_manifest.json').write_text('{}')
    with pytest.raises(ValueError):d.verified_seed(source,{},tmp_path/'destination')
    assert not (tmp_path/'destination').exists()


def test_seed_rejects_cache_nesting(tmp_path):
    with pytest.raises(ValueError):d.verified_seed(tmp_path,{},tmp_path/'nested')


def test_seed_rejects_git_destination(tmp_path):
    (tmp_path/'.git').mkdir()
    with pytest.raises(ValueError):d.verified_seed(tmp_path/'old',{},tmp_path/'new')


def helper_jar(fork=''):
    xml='<plugin><version>3.5.1</version><mojos>'+''.join(
        '<mojo><goal>'+g+'</goal>'+fork+'</mojo>' for g in d.GOALS)+'</mojos><dependencies/></plugin>'
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:z.writestr('META-INF/maven/plugin.xml',xml)
    return stream.getvalue()


@pytest.mark.parametrize('fork', ['<executePhase>compile</executePhase>',
    '<executeGoal>compile</executeGoal>','<requiresDependencyResolution>test</requiresDependencyResolution>'])
def test_helper_cannot_fork_or_resolve_project_dependencies(monkeypatch,tmp_path,fork):
    monkeypatch.setattr(d.Models,'remote',lambda *a: {})
    class Fake:
        root=tmp_path
        def get(self,*args):return helper_jar(fork)
    with pytest.raises(ValueError,match='fork lifecycle'):d.prepare_helper(Fake())


def test_helper_request_cap_counts_checksum_probes(tmp_path):
    a=d.HelperAcquisition(tmp_path/'helper',tmp_path/'seed',{})
    a.requests=150
    with pytest.raises(d.BudgetExceeded):a.fetch('g/a/1/a-1.pom.sha1',4096)
    assert a.requests==150


def test_helper_has_separate_ledger_and_caps(tmp_path):
    a=d.HelperAcquisition(tmp_path/'helper',tmp_path/'seed',{})
    m=a.seal()
    assert m['version']=='task-d3-helper-acquisition-v1'
    assert m['requests']==0 and m['limits']['requests']==150
    assert m['limits']['response_bytes']==64*1024*1024
    assert m['maven_executions_during_acquisition']==0


def test_wrapper_bounds_and_retains_noexec():
    assert '180s "$@"' in d.WRAPPER and 'memory.swap.max' in d.WRAPPER
    assert '1610612736' in d.WRAPPER and 'memory.peak' in d.WRAPPER
    assert 'compile' not in d.WRAPPER


def test_host_resource_evidence_is_not_assumed(monkeypatch):
    monkeypatch.setattr(Path,'read_text',lambda *a,**k:'MemAvailable: 3145728 kB\n')
    assert d.host_available()==3*1024*1024*1024
    monkeypatch.setattr(Path,'read_text',lambda *a,**k:'missing\n')
    with pytest.raises(ValueError):d.host_available()


def archive_bytes(names):
    import tarfile
    data=io.BytesIO()
    with tarfile.open(fileobj=data,mode='w') as archive:
        for name,value in names.items():
            record=tarfile.TarInfo(name);record.size=len(value)
            archive.addfile(record,io.BytesIO(value))
    return data.getvalue()


def test_tmpfs_evidence_requires_complete_bounded_namespace_export(tmp_path):
    records={n:b'0' for n in ('goal.exit','memory.peak','memory.events','maven.stdout','maven.stderr')}
    d.extract_output(archive_bytes(records),tmp_path)
    assert (tmp_path/'goal.exit').read_bytes()==b'0'
    with pytest.raises(ValueError,match='Incomplete'):d.extract_output(archive_bytes({}),tmp_path)


@pytest.mark.parametrize('name',['../outside','/absolute','nested/goal.exit','unexpected.jar'])
def test_output_archive_cannot_escape_or_admit_binaries(tmp_path,name):
    with pytest.raises(ValueError):d.extract_output(archive_bytes({name:b'bad'}),tmp_path)


def test_output_archive_size_cap(tmp_path):
    with pytest.raises(ValueError):d.extract_output(b'0'*(2*1024*1024+1),tmp_path)


def test_sandbox_refuses_network_before_execution(tmp_path):
    c=dict(Name='/test',Image=d.IMAGE,Config={'User':'1000:1000'},HostConfig={'NetworkMode':'bridge'})
    with pytest.raises(ValueError):d.verify_container(c,'test',tmp_path)


def test_collected_signal_prevents_tmpfs_teardown_before_evidence_copy():
    assert 'touch /output/ready' in d.WRAPPER and '/output/collected' in d.WRAPPER
    assert '"$count" -lt 30' in d.WRAPPER


class Response:
    status=200
    def __init__(self,url,body):self.url=url;self.body=io.BytesIO(body);self.headers={'Content-Length':str(len(body))}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def geturl(self):return self.url
    def read(self,n):return self.body.read(n)


@pytest.mark.parametrize('body,ok',[(b'1234',True),(b'12345',False)])
def test_helper_transfer_budget_exact_boundary(tmp_path,body,ok):
    a=d.HelperAcquisition(tmp_path/'helper',tmp_path/'seed',{})
    a.bytes=d.MAX_BYTES-4
    class Opener:
        def open(self,req,timeout):return Response(req.full_url,body)
    a.opener=Opener()
    if ok:assert a.fetch('g/a/1/a-1.pom',32*1024*1024)==body
    else:
        with pytest.raises(d.BudgetExceeded):a.fetch('g/a/1/a-1.pom',32*1024*1024)
    assert a.requests==1 and a.bytes<=d.MAX_BYTES


def test_helper_records_http_attempt_before_failure(tmp_path):
    import urllib.error
    a=d.HelperAcquisition(tmp_path/'helper',tmp_path/'seed',{})
    class Opener:
        def open(self,req,timeout):raise urllib.error.HTTPError(req.full_url,404,'not found',{},None)
    a.opener=Opener()
    with pytest.raises(urllib.error.HTTPError):a.fetch('g/a/1/a-1.pom.sha512',4096)
    assert json.loads((a.root/'dependency_manifest.json').read_text())['requests']==1
    assert a.events[0]['status']==404


def test_published_actual_model_does_not_imply_compilation_or_classpaths():
    root=Path(__file__).resolve().parents[1]/'examples/phase5_2_2_d_3'
    m=json.loads((root/'static_vs_maven.json').read_text())
    assert m['status']=='MODEL_VERIFIED' and m['active_profile_count']==8
    assert m['inactive_profile_count']==17 and m['all_project_profile_decisions_agree']
    assert len(m['unresolved_transitive_profile_sources'])==15
    assert m['project_runtime_classpath']=='NOT_RESOLVED'
    assert m['offline_java_build_readiness']=='UNKNOWN'
    assert m['historical_compilation']=='NOT_ATTEMPTED'
    assert m['literal_open_jdk_activation']['status']=='NOT_A_T0_PROJECT_PARENT_NOT_DIRECTLY_EVALUATED'
    deps=m['dependency_declarations']['maven']
    assert len(deps)==5 and all(r['scope']=='test' for r in deps)
    jar=next(p for p in m['effective_plugins'] if p['gav'][1]=='maven-jar-plugin')
    assert all(e['required_through_compile'] is False for e in jar['executions'])
    assert all(e['executed'] is False for p in m['effective_plugins'] for e in p['executions'])
