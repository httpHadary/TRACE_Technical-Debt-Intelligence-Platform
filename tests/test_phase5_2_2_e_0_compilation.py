"""Compilation controller tests never start Docker/Maven or download artifacts."""
import io
from pathlib import Path
import tarfile
import pytest
from tools import compile_phase5_2_2_e_0 as e


def test_exact_command_preserves_enforcers_and_registered_context():
    c=e.command()
    assert c[-1]=='compile' and '--offline' in c and '--errors' in c
    assert '-Dmaven.compiler.release=8' in c and '-Dmaven.test.skip=true' in c
    assert '-Duser.home=/tmp' in c
    assert not any('enforcer.skip' in x or 'rat.skip' in x or 'buildNumber.skip' in x or x=='-P' for x in c)
    assert not set(c)&{'test','package','install','deploy','site','verify','validate'}


def test_persistent_attempt_claim_blocks_any_retry(tmp_path,monkeypatch):
    (tmp_path/'attempt_claim.json').write_text('{}')
    monkeypatch.setattr(e,'enforce_process_limits',lambda:None)
    monkeypatch.setattr(e,'resource_admission',lambda:pytest.fail('must not reach resource/startup'))
    with pytest.raises(FileExistsError):e.execute_once(tmp_path)


def test_failed_resource_admission_consumes_claim_without_container(tmp_path,monkeypatch):
    monkeypatch.setattr(e,'enforce_process_limits',lambda:None)
    def fail():raise RuntimeError('BLOCKED_RESOURCES')
    monkeypatch.setattr(e,'resource_admission',fail)
    monkeypatch.setattr(e,'docker',lambda *a:pytest.fail('No container allowed'))
    with pytest.raises(RuntimeError):e.execute_once(tmp_path)
    assert (tmp_path/'attempt_claim.json').exists()


def test_headroom_admission_precedes_docker(monkeypatch):
    monkeypatch.setattr(e,'host_available',lambda:4*1024**3-1)
    monkeypatch.setattr(e,'docker',lambda *a:pytest.fail('Do not start'))
    with pytest.raises(RuntimeError,match='RAM'):e.resource_admission()


@pytest.mark.parametrize('code,out,complete,compiler,expected',[
    (0,'BUILD SUCCESS',False,False,'PARTIAL'),
    (0,'BUILD SUCCESS',True,True,'COMPILE_PASS'),
    (1,'Could not find artifact g:a:jar:1',False,False,'BLOCKED_DEPENDENCY'),
    (1,'Cannot access central in offline mode',False,False,'BLOCKED_DEPENDENCY'),
    (1,'fatal: not a git repository',False,False,'BLOCKED_SCM_CONTEXT'),
    (1,'Rule requireMavenVersion failed',False,False,'BLOCKED_BUILD_OR_RESOURCE'),
    (124,'timeout',False,False,'BLOCKED_BUILD_OR_RESOURCE'),
    (137,'oom',False,False,'BLOCKED_BUILD_OR_RESOURCE'),
    (123,'',False,False,'BLOCKED_BUILD_OR_RESOURCE'),
])
def test_failure_categories_do_not_conflate_scm_with_dependencies(code,out,complete,compiler,expected):
    assert e.classify_result(code,out,'',complete,compiler)==expected


def archive(name,kind=tarfile.REGTYPE,data=b'0'):
    raw=io.BytesIO()
    with tarfile.open(fileobj=raw,mode='w') as z:
        m=tarfile.TarInfo(name);m.type=kind;m.size=len(data) if kind==tarfile.REGTYPE else 0
        z.addfile(m,io.BytesIO(data) if kind==tarfile.REGTYPE else None)
    return raw.getvalue()


@pytest.mark.parametrize('name,kind',[('../outside',tarfile.REGTYPE),('/absolute',tarfile.REGTYPE),
    ('classes/link',tarfile.SYMTYPE),('source/pom.xml',tarfile.REGTYPE)])
def test_build_archive_cannot_escape_or_admit_source_replacements(tmp_path,name,kind):
    with pytest.raises(ValueError):e.extract_evidence(archive(name,kind),tmp_path)


def test_incomplete_capture_is_not_success(tmp_path):
    with pytest.raises(ValueError,match='Incomplete'):e.extract_evidence(archive('maven.stdout'),tmp_path)


def test_wrapper_preserves_one_goal_timeout_and_no_metadata_invention():
    assert '240s "$@"' in e.WRAPPER
    assert 'git init' not in e.WRAPPER and 'mvn' not in e.WRAPPER
    assert '2147483648' in e.WRAPPER and 'memory.swap.max' in e.WRAPPER
    assert 'cache-before.sha256' in e.WRAPPER and 'source-after.sha256' in e.WRAPPER
    assert '/output/collected' in e.WRAPPER and '/output/ready' in e.WRAPPER


def test_real_setup_failure_cannot_be_promoted_to_dependency_or_compile_evidence():
    import json
    root=Path(__file__).resolve().parents[1]/'examples/phase5_2_2_e_0'
    evidence=json.loads((root/'failure_manifest.json').read_text())
    assert evidence['status']=='BLOCKED_BUILD_OR_RESOURCE'
    assert evidence['container_exit_code']==123 and evidence['container_start_count']==1
    assert evidence['maven_invocations']==0 and evidence['compiler_started'] is False
    assert evidence['missing_artifact_assessment']=='NOT_REACHED'
    assert evidence['full_stdout_stderr_available'] is False
    assert evidence['cgroup_peak_memory_available'] is False
    assert evidence['retry_performed'] is False
