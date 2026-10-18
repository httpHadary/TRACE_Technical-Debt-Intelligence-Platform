"""Adapter policy/structure tests; these never execute Docker or Maven."""
import io
import json
from pathlib import Path
import struct
import subprocess
import tarfile
import pytest
from tools import build_compile_e02 as e


def test_command_is_exact_registered_compile_only():
    assert e.maven_command()==['/usr/share/maven/bin/mvn','--offline','--batch-mode','--no-transfer-progress','--errors',
        '-s','/inspection/settings.xml','-gs','/inspection/settings.xml','-Dmaven.repo.local=/runtime-repository',
        '-Duser.home=/tmp','-Dmaven.test.skip=true','-Dmaven.compiler.release=8','compile']


def test_explicit_compile_adapter_does_not_change_smoke_script_or_sentinel():
    p=Path(e.b.__file__).with_name('build_sandbox_setup.sh');before=p.read_bytes();script=e.wrapper_script()
    assert '--e02-offline-compile' in script and '2147483648' in script
    assert '--no-maven-smoke' not in script and 'INJECTED_PRE_MAVEN_FAILURE' not in script
    assert p.read_bytes()==before and b'INJECTED_PRE_MAVEN_FAILURE' in before
    assert script.count('/usr/share/maven/bin/mvn')==1
    assert '240s /usr/share/maven/bin/mvn' in script and 'maven.stdout' in script and 'maven.stderr' in script
    assert 'enforcer.skip' not in script and 'git init' not in script and 'chmod -R' not in script
    assert subprocess.run(['/bin/sh','-n'],input=script.encode(),capture_output=True).returncode==0


def test_compile_exclusive_claim_cannot_be_reset_or_reused(tmp_path,monkeypatch):
    (tmp_path/'attempt_claim.json').write_text('{}')
    monkeypatch.setattr(e.b,'enforce_process_limits',lambda:None)
    monkeypatch.setattr(e,'admission',lambda:pytest.fail('No second attempt'))
    with pytest.raises(FileExistsError):e.execute_once(tmp_path)


def test_resource_gate_is_four_gib_not_smoke_three(monkeypatch):
    monkeypatch.setattr(e.b,'admission',lambda:dict(available_ram_bytes=4*1024**3-1))
    with pytest.raises(RuntimeError,match='4GiB'):e.admission()
    monkeypatch.setattr(e.b,'admission',lambda:dict(available_ram_bytes=4*1024**3))
    assert e.admission()['headroom_bytes']==2*1024**3


def test_failed_resource_gate_never_creates_a_container(tmp_path,monkeypatch):
    monkeypatch.setattr(e.b,'enforce_process_limits',lambda:None)
    def fail():raise RuntimeError('BLOCKED_RESOURCES')
    monkeypatch.setattr(e,'admission',fail)
    monkeypatch.setattr(e.b,'docker',lambda *a:pytest.fail('No create/start'))
    result=e.execute_once(tmp_path)
    assert result['substatus']=='BLOCKED_RESOURCES' and (tmp_path/'attempt_claim.json').exists()


def minimal_class(name='org/apache/commons/cli/Foo',source='Foo.java',major=52):
    # Hand-encoded structural fixture; never presented as a historical class.
    def utf(s):
        raw=s.encode();return b'\1'+struct.pack('>H',len(raw))+raw
    cp=utf(name)+b'\7\0\1'+utf('java/lang/Object')+b'\7\0\3'+utf('SourceFile')+utf(source)
    return b'\xca\xfe\xba\xbe'+struct.pack('>HHH',0,major,7)+cp+struct.pack('>HHHHHHH',0x21,2,4,0,0,0,1)+struct.pack('>HIH',5,2,6)


def test_class_parser_checks_real_structure_not_magic_only():
    parsed=e.parse_class(minimal_class())
    assert parsed['major']==52 and parsed['internal_name']=='org/apache/commons/cli/Foo'
    assert parsed['source_file']=='Foo.java'


@pytest.mark.parametrize('raw',[b'\xca\xfe\xba\xbe',minimal_class(major=61),minimal_class()[:-1],minimal_class()+b'garbage',b'not a class'])
def test_invalid_non_java8_and_truncated_classes_cannot_pass(raw):
    with pytest.raises((ValueError,IndexError)):e.parse_class(raw)


def class_fixture(tmp_path,internal='org/apache/commons/cli/Foo'):
    source=tmp_path/'inputs/source/src/main/java/org/apache/commons/cli';source.mkdir(parents=True)
    (source/'Foo.java').write_text('package org.apache.commons.cli; public class Foo {}')
    (source/'package-info.java').write_text('package org.apache.commons.cli;')
    cap=tmp_path/'capture';cap.mkdir()
    with tarfile.open(cap/'classes.tar','w') as tar:
        raw=minimal_class(internal);row=tarfile.TarInfo(internal+'.class');row.size=len(raw);tar.addfile(row,io.BytesIO(raw))


def test_class_completeness_matches_named_production_population(tmp_path):
    class_fixture(tmp_path)
    result=e.class_manifest(tmp_path)
    assert result['complete'] and result['expected_top_level_count']==1 and result['class_count']==1
    assert result['package_info_sources']==['org/apache/commons/cli/package-info']


def test_wrong_top_level_identity_cannot_satisfy_aggregate_count(tmp_path):
    class_fixture(tmp_path,'org/apache/commons/cli/Wrong')
    result=e.class_manifest(tmp_path)
    assert not result['complete'] and result['missing_top_level']==['org/apache/commons/cli/Foo']


def test_extended_archive_allowlist_does_not_enable_maven_files_in_smoke(tmp_path):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as tar:
        row=tarfile.TarInfo('maven.stdout');row.size=2;tar.addfile(row,io.BytesIO(b'ok'))
    raw=stream.getvalue()
    with pytest.raises(ValueError):e.b.extract_archive(raw,tmp_path)
    assert e.b.extract_archive(raw,tmp_path,allowed=e.ALLOWED)==['maven.stdout']


def test_explicit_archive_extension_cannot_allow_traversal(tmp_path):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as tar:
        row=tarfile.TarInfo('../outside');row.size=1;tar.addfile(row,io.BytesIO(b'x'))
    with pytest.raises(ValueError):e.b.extract_archive(stream.getvalue(),tmp_path,allowed={'../outside'})
    assert not list(tmp_path.iterdir())


def test_recorded_maven_failure_has_exact_roots_and_no_compiler_success():
    p=Path(__file__).resolve().parents[1]/'examples/phase5_2_2_e_0_2'
    m=json.loads((p/'failure_manifest.json').read_text());stage=json.loads((p/'stage_evidence.json').read_text())
    assert m['status']=='BLOCKED_DEPENDENCY' and m['maven_actually_launched']
    assert m['missing_jar_count']==5 and m['missing_pom_count']==5
    assert len(m['missing_artifacts'])==10 and all(not x['seed_bytes_present'] for x in m['missing_artifacts'])
    assert stage['actual_plugin_order']==[] and stage['compiler']=='NOT_REACHED'
    assert stage['maven_exit']==stage['docker_exit']==1 and stage['logs']['complete']
    assert all(x['goal_execution_observed'] is False for x in stage['original_lifecycle_bindings'])


@pytest.mark.parametrize('mutation',['mode','heap','memory','network','owner'])
def test_compile_policy_cannot_accept_smoke_limits_or_unsafe_settings(tmp_path,mutation):
    c=dict(Name='/owned',Image=e.b.IMAGE,Config=dict(User='1000:1000',Labels={e.LABEL:'owned'},
        Cmd=['/inspection/wrapper.sh','--e02-offline-compile'],Entrypoint=['/bin/sh'],WorkingDir='/source',Env=['MAVEN_OPTS='+e.OPTIONS]),
        HostConfig=dict(Memory=e.MEMORY,MemorySwap=e.MEMORY,NanoCpus=1000000000,PidsLimit=64,NetworkMode='none',
            ReadonlyRootfs=True,Privileged=False,CapAdd=None,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Tmpfs=e.b.tmpfs_options(),
            Ulimits=[dict(Name='fsize',Soft=8388608,Hard=8388608),dict(Name='nofile',Soft=1024,Hard=1024)]),
        Mounts=[dict(Type='bind',Destination='/'+p,Source=str(tmp_path/p),RW=False) for p in ('inputs','inspection')])
    e.validate_container(c,'owned',tmp_path)
    if mutation=='mode':c['Config']['Cmd'][-1]='--no-maven-smoke'
    if mutation=='heap':c['Config']['Env']=['MAVEN_OPTS=-Xmx2g']
    if mutation=='memory':c['HostConfig']['Memory']=1024**3
    if mutation=='network':c['HostConfig']['NetworkMode']='bridge'
    if mutation=='owner':c['Config']['Labels']={e.b.LABEL:'owned'}
    with pytest.raises(ValueError):e.validate_container(c,'owned',tmp_path)
