"""No containers in regression tests: shell trap proof plus mocked Docker races."""
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
from types import SimpleNamespace
import pytest
from tools import build_sandbox as b


def script():return Path(b.__file__).with_name('build_sandbox_setup.sh').read_text()


def test_owned_tmpfs_preserves_security_and_disk_limits():
    opts=b.tmpfs_options()
    assert set(opts)=={'/source','/runtime-repository','/tmp','/output'}
    for value in opts.values():
        assert all(x in value.split(',') for x in ('uid=1000','gid=1000','nosuid','nodev','noexec','mode=1777'))
    assert 'size=134217728' in opts['/source']
    assert 'size=33554432' in opts['/output']


def test_script_registers_trap_before_setup_and_never_chmods_mount_roots():
    s=script()
    assert s.index("trap 'finish")<s.index('# BEGIN_SETUP')
    assert '-mindepth 1 -type f -exec chmod u+w' in s and 'chmod -R' not in s
    assert s.index('MOUNT_OWNERSHIP')<s.index('SOURCE_COPY')
    assert '/usr/share/maven/bin/mvn' not in s and 'javac' not in s
    assert 'reject_non_smoke' in s and 'exit 73' in s


@pytest.mark.parametrize('stage,category,code',[
    ('SOURCE_COPY','copy_frozen_source',23),('ARTIFACT_COPY','copy_verified_cache',24),
    ('SOURCE_PERMISSIONS','chmod_owned_files',25),('BOOTSTRAP','early_exit',26),
    ('INJECTED_PRE_MAVEN_FAILURE','deliberate_exit_73',73)])
def test_actual_shell_exit_trap_preserves_exact_stage_stderr_and_code(tmp_path,stage,category,code):
    out=tmp_path/'out';out.mkdir();cg=tmp_path/'cg';cg.mkdir()
    for name,value in [('memory.peak','12345\n'),('memory.events','oom 0\n'),('cpu.stat','usage_usec 12\n')]:
        (cg/name).write_text(value)
    core=script().split('# BEGIN_SETUP')[0].replace('OUT=/output','OUT='+shlex.quote(str(out))).replace('CG=/sys/fs/cgroup','CG='+shlex.quote(str(cg)))
    driver=core+f'''\nexec > "$OUT/setup.stdout" 2> "$OUT/setup.stderr"
run_stage {stage} {category} sh -c 'printf "exact stdout\\n"; printf "exact stderr\\n" >&2; exit {code}'
'''
    result=subprocess.run(['/bin/sh','-c',driver],env={'PATH':'/usr/bin:/bin','TD_CAPTURE_HOLD_SECONDS':'0'},capture_output=True,timeout=5)
    assert result.returncode==code
    assert (out/'exit.code').read_text()==str(code)+'\n'
    assert (out/'stage.txt').read_text()==stage+'\n'
    assert (out/'command-category.txt').read_text()==category+'\n'
    assert (out/'setup.stderr').read_text()==f'exact stderr\nSTAGE_FAILED {stage} {category} exit={code}\n'
    assert b'exact stderr\n' in result.stderr and b'exact stdout\n' in result.stdout
    assert (out/'memory.peak').read_text()=='12345\n'
    assert not (out/'maven.stdout').exists()


def test_missing_cgroup_measurement_is_explicitly_unavailable(tmp_path):
    core=script().split('# BEGIN_SETUP')[0].replace('OUT=/output','OUT='+shlex.quote(str(tmp_path))).replace('CG=/sys/fs/cgroup','CG='+shlex.quote(str(tmp_path/'missing')))
    result=subprocess.run(['/bin/sh','-c',core+'\nexit 17\n'],env={'PATH':'/usr/bin:/bin','TD_CAPTURE_HOLD_SECONDS':'0'},capture_output=True,timeout=5)
    assert result.returncode==17
    assert not (tmp_path/'memory.peak').exists()
    assert (tmp_path/'memory.peak.unavailable').read_text()=='not_readable\n'


def test_exclusive_attempt_claim_prevents_any_second_container(tmp_path,monkeypatch):
    (tmp_path/'attempt_claim.json').write_text('{}')
    monkeypatch.setattr(b,'enforce_process_limits',lambda:None)
    monkeypatch.setattr(b,'admission',lambda:pytest.fail('No second resource/startup attempt'))
    with pytest.raises(FileExistsError):b.run_smoke(tmp_path)


def test_exec_race_returns_unavailable_and_does_not_raise_or_claim_success(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'call',lambda *a:SimpleNamespace(returncode=1,stdout=b'',stderr=b'container is not running'))
    capture=b.collect_if_ready('owned',tmp_path)
    assert capture['race'] and capture['captured'] is False


def test_logs_do_not_require_exec_for_immediate_exit(tmp_path,monkeypatch):
    def fake(*args):
        assert args==('logs','owned')
        return SimpleNamespace(returncode=0,stdout=b'setup stage\n',stderr=b'exact stderr\n')
    monkeypatch.setattr(b,'call',fake)
    result=b.retain_logs('owned',tmp_path)
    assert result['exit_code']==0 and (tmp_path/'docker.stderr').read_bytes()==b'exact stderr\n'


@pytest.mark.parametrize('name,label',[('/other','owned'),('/owned','different')])
def test_cleanup_cannot_target_unowned_container(name,label):
    with pytest.raises(ValueError):b.assert_owned({'Name':name,'Config':{'Labels':{b.LABEL:label}}},'owned')


def archive(rows):
    data=io.BytesIO()
    with tarfile.open(fileobj=data,mode='w') as z:
        for name,kind,size in rows:
            m=tarfile.TarInfo(name);m.type=kind;m.size=size if kind==tarfile.REGTYPE else 0
            z.addfile(m,io.BytesIO(b'x'*size) if kind==tarfile.REGTYPE else None)
    return data.getvalue()


@pytest.mark.parametrize('name,kind',[
    ('../outside',tarfile.REGTYPE),('/absolute',tarfile.REGTYPE),('nested/setup.stderr',tarfile.REGTYPE),
    ('setup.stderr',tarfile.SYMTYPE),('setup.stderr',tarfile.LNKTYPE)])
def test_archive_rejects_traversal_links_and_unregistered_paths(tmp_path,name,kind):
    with pytest.raises(ValueError):b.extract_archive(archive([(name,kind,1)]),tmp_path)
    assert not list(tmp_path.iterdir())


def test_archive_checks_duplicates_before_any_write(tmp_path):
    raw=archive([('setup.stderr',tarfile.REGTYPE,1),('./setup.stderr',tarfile.REGTYPE,1)])
    with pytest.raises(ValueError):b.extract_archive(raw,tmp_path)
    assert not list(tmp_path.iterdir())


def test_archive_accepts_exact_bytes_and_rejects_overwrite(tmp_path):
    raw=archive([('setup.stderr',tarfile.REGTYPE,2)])
    assert b.extract_archive(raw,tmp_path)==['setup.stderr']
    assert (tmp_path/'setup.stderr').read_bytes()==b'xx'
    with pytest.raises(ValueError):b.extract_archive(raw,tmp_path)


def test_archive_rejects_oversized_members(tmp_path):
    with pytest.raises(ValueError):b.extract_archive(archive([('setup.stderr',tarfile.REGTYPE,8*1024**2+1)]),tmp_path)


def test_insufficient_host_ram_blocks_before_docker(monkeypatch):
    monkeypatch.setattr(b,'host_available',lambda:3*1024**3-1)
    monkeypatch.setattr(b,'docker',lambda *a:pytest.fail('Resource check must precede Docker'))
    with pytest.raises(RuntimeError,match='RAM'):b.admission()


def test_inspect_race_still_retains_logs_events_and_ownership_checked_cleanup(tmp_path,monkeypatch):
    calls=[];count=0
    def state(name):
        nonlocal count
        count+=1
        if count==1:raise RuntimeError('transient inspect race')
        return {'Name':'/owned','Config':{'Labels':{b.LABEL:'owned'}},'State':{'Running':False,'ExitCode':73}}
    monkeypatch.setattr(b,'inspect',state)
    monkeypatch.setattr(b,'retain_logs',lambda *a:dict(exit_code=0))
    monkeypatch.setattr(b,'daemon_events',lambda *a:[])
    monkeypatch.setattr(b,'docker',lambda *a:calls.append(a))
    result=dict(capture=dict(captured=False),errors=[],cleanup_complete=False)
    b.retain_terminal_evidence('owned','id',0,tmp_path,result)
    assert result['docker_logs']['exit_code']==0 and result['events']==[]
    assert result['cleanup_complete'] and calls==[('rm','-f','-v','owned')]
    assert result['errors'][0]['kind']=='HOST_STATE'


def test_immediate_exit_terminal_oom_state_retained_without_exec(tmp_path,monkeypatch):
    state={'Name':'/owned','Config':{'Labels':{b.LABEL:'owned'}},
           'State':{'Running':False,'ExitCode':137,'OOMKilled':True}}
    monkeypatch.setattr(b,'inspect',lambda *a:state)
    monkeypatch.setattr(b,'collect_if_ready',lambda *a:pytest.fail('Stopped container needs no exec'))
    monkeypatch.setattr(b,'retain_logs',lambda *a:dict(exit_code=0))
    monkeypatch.setattr(b,'daemon_events',lambda *a:[])
    monkeypatch.setattr(b,'docker',lambda *a:None)
    result=dict(capture=dict(captured=False),errors=[],cleanup_complete=False)
    b.retain_terminal_evidence('owned','id',0,tmp_path,result)
    assert result['terminal_state']['OOMKilled'] and not result['capture']['captured']
    assert result['docker_logs']['exit_code']==0 and result['cleanup_complete']


@pytest.mark.parametrize('paths,ok',[
    ('z\nA\n',True),('A\nz\n',True),('A\nA\n',False),('A\nwrong\n',False),(None,False)])
def test_file_identity_equality_is_locale_independent_but_exact(paths,ok):
    assert b.canonical_paths_match(paths,['a'*64+'  A','b'*64+'  z']) is ok


def valid_container(tmp_path):
    return dict(Name='/owned',Image=b.IMAGE,
        Config=dict(User='1000:1000',Labels={b.LABEL:'owned'},Cmd=['/inspection/wrapper.sh','--no-maven-smoke'],
                    Entrypoint=['/bin/sh'],WorkingDir='/source'),
        HostConfig=dict(Memory=b.MEMORY,MemorySwap=b.MEMORY,NanoCpus=1000000000,PidsLimit=64,
            NetworkMode='none',ReadonlyRootfs=True,Privileged=False,CapDrop=['ALL'],CapAdd=None,
            SecurityOpt=['no-new-privileges'],Tmpfs=b.tmpfs_options(),ShmSize=8388608,
            Ulimits=[dict(Name='fsize',Soft=8388608,Hard=8388608),dict(Name='nofile',Soft=1024,Hard=1024)]),
        Mounts=[dict(Type='bind',Destination='/'+n,Source=str(tmp_path/n),RW=False) for n in ('inputs','inspection')])


@pytest.mark.parametrize('mutation',['uid','network','ownership','caps','root','file_limit'])
def test_exact_mount_and_runtime_isolation_tampering_is_rejected(tmp_path,mutation):
    c=valid_container(tmp_path);b.verify_container(c,'owned',tmp_path)
    if mutation=='uid':c['Config']['User']='0:0'
    if mutation=='network':c['HostConfig']['NetworkMode']='bridge'
    if mutation=='ownership':c['HostConfig']['Tmpfs']['/source']=c['HostConfig']['Tmpfs']['/source'].replace('uid=1000','uid=0')
    if mutation=='caps':c['HostConfig']['CapAdd']=['SYS_ADMIN']
    if mutation=='root':c['HostConfig']['ReadonlyRootfs']=False
    if mutation=='file_limit':c['HostConfig']['Ulimits']=[]
    with pytest.raises(ValueError):b.verify_container(c,'owned',tmp_path)
