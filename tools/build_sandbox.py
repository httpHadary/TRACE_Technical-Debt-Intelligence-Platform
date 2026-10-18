"""Owned tmpfs setup and fail-closed capture, with one no-Maven smoke entry point."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import resource
import shutil
import subprocess
import tarfile
import time
import uuid
import http.client
import socket
import urllib.parse
from tools.inspect_phase5_2_2_d_3 import sha, write, docker, host_available, IMAGE, COMMIT, TREE, POM
from tools.recover_phase5_2_2_d_2 import verify_rows, enforce_process_limits

BASE='8e73a0a050fc3f411087666aae1057b66fa3282f'
E0=Path('/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0/2026-10-16')
MEMORY=1024**3
LABEL='techdebt360.phase522e01'
MAX_ARCHIVE=32*1024**2
ALLOWED={'setup.stdout','setup.stderr','exit.code','stage.txt','command-category.txt','passed-stages.txt',
    'maven.state.txt','mount-ownership.txt','mountinfo.txt','source.paths','cache.paths',
    'source.after.sha256','cache.after.sha256','working-directory.txt','setup.complete','processes.txt','ready','cgroup.limits.txt'}
ALLOWED |= {m+s for m in ('memory.peak','memory.events','cpu.stat') for s in ('','.unavailable')}


def tmpfs_options():
    return {('/'+name):f'rw,nosuid,nodev,noexec,size={size*1024**2},mode=1777,uid=1000,gid=1000'
            for name,size in [('source',128),('runtime-repository',128),('tmp',128),('output',32)]}


def prepare(base,root):
    base,root=Path(base),Path(root).absolute()
    if any(p.is_symlink() or (p/'.git').exists() for p in (root,*root.parents)) or root.is_relative_to(E0):
        raise ValueError('Fresh output outside Git and old attempt required')
    reference=json.loads((base/'examples/phase5_2_2_e_0/prerequisite_verification.json').read_text())
    if sha(E0/'prerequisites.json')!=reference['full_private_prerequisites_sha256']:
        raise ValueError('E.0 seed provenance changed')
    q=json.loads((E0/'prerequisites.json').read_text())
    if (q['commit_sha'],q['tree_sha'],q['pom_sha256'])!=(COMMIT,TREE,POM):
        raise ValueError('Frozen source identities changed')
    d3=E0.parent.parent/'phase5_2_2_d_3/2026-10-16'
    if sha(d3/'effective-pom/effective-pom.xml')!=q['effective_pom_sha256']:
        raise ValueError('D.3 effective model changed')
    records=verify_rows(E0/'inputs',dict(artifacts=q['artifact_records']))
    if len(records)!=653 or len(q['source_entries'])!=117:raise ValueError('Exact seed population required')
    inputs=root/'inputs';inputs.mkdir(exist_ok=False)
    inspection=root/'inspection';inspection.mkdir()
    for kind,rows in [('repository',list(records.values())),('source',q['source_entries'])]:
        for row in rows:
            name=row['path'];p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\n' in name or '\\' in name:
                raise ValueError('Unsafe manifest path')
            src=E0/'inputs'/kind/name
            if any(v.is_symlink() for v in (src,*src.parents)) or sha(src)!=row['sha256']:
                raise ValueError('Frozen seed bytes changed')
            if kind=='source':
                data=src.read_bytes()
                if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=row['git_blob']:
                    raise ValueError('Source Git blob mismatch')
            dst=inputs/kind/name;dst.parent.mkdir(parents=True,exist_ok=True)
            with src.open('rb') as left,dst.open('xb') as right:shutil.copyfileobj(left,right,65536)
            if sha(dst)!=row['sha256'] or dst.stat().st_ino==src.stat().st_ino:raise ValueError('Independent copy mismatch')
            dst.chmod(0o555 if row.get('mode')=='100755' else 0o444)
        name='source.sha256' if kind=='source' else 'cache.sha256'
        (inspection/name).write_text(''.join(row['sha256']+'  '+row['path']+'\n' for row in sorted(rows,key=lambda r:r['path'])))
    script=Path(__file__).with_name('build_sandbox_setup.sh')
    shutil.copyfile(script,inspection/'wrapper.sh')
    write(root/'seed_verification.json',dict(version='e01-seeds-v1',commit_sha=COMMIT,tree_sha=TREE,
        pom_sha256=POM,source_count=117,artifact_count=653,original_e0_manifest_sha256=sha(E0/'prerequisites.json'),
        source_manifest_sha256=sha(inspection/'source.sha256'),cache_manifest_sha256=sha(inspection/'cache.sha256'),
        wrapper_sha256=sha(script),all_copies_independent=True,downloads=0))


def admission():
    available=host_available()
    if available<MEMORY+2*1024**3:raise RuntimeError('Insufficient RAM for1GiB sandbox plus2GiB host headroom')
    if docker('ps','-q').strip():raise RuntimeError('Another container is running')
    conflicts=[]
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                comm=(p/'comm').read_text().strip()
                args=(p/'cmdline').read_bytes().split(b'\0')[:3]
                if comm in ('java','mvn','sonar-scanner') or any(b'chronos_worker' in a or b'granite_worker' in a for a in args):
                    conflicts.append(dict(pid=p.name,comm=comm))
            except (FileNotFoundError,PermissionError):continue
    if conflicts:raise RuntimeError('Concurrent prohibited workload: '+repr(conflicts))
    disk=shutil.disk_usage('/home/hp/tst').free
    if disk<512*1024**2:raise RuntimeError('Insufficient bounded task storage')
    return dict(available_ram_bytes=available,free_disk_bytes=disk,prohibited_processes=conflicts,running_containers=0)


def call(*args,timeout=20):
    def small_stack():resource.setrlimit(resource.RLIMIT_STACK,(1048576,1048576))
    env=dict(os.environ,GOMAXPROCS='1',GOMEMLIMIT='64MiB',MALLOC_ARENA_MAX='1')
    p=subprocess.run(['docker',*map(str,args)],capture_output=True,env=env,preexec_fn=small_stack,timeout=timeout)
    if len(p.stdout)+len(p.stderr)>MAX_ARCHIVE:raise ValueError('Docker output cap')
    return p


def inspect(name):
    return json.loads(docker('inspect',name))[0]


def assert_owned(c,name,label=None):
    label=LABEL if label is None else label
    if c['Name']!='/'+name or c['Config']['Labels'].get(label)!=name:
        raise ValueError('Cleanup ownership not established')


def verify_container(c,name,root):
    assert_owned(c,name);h=c['HostConfig'];cfg=c['Config']
    if (c['Image']!=IMAGE or cfg['User']!='1000:1000' or cfg['Cmd']!=['/inspection/wrapper.sh','--no-maven-smoke']
        or cfg['Entrypoint']!=['/bin/sh'] or cfg['WorkingDir']!='/source'
        or h['Memory']!=MEMORY or h['MemorySwap']!=MEMORY or h['NanoCpus']!=1000000000 or h['PidsLimit']!=64
        or h['NetworkMode']!='none' or not h['ReadonlyRootfs'] or h['Privileged']
        or h.get('CapAdd') or h['ShmSize']!=8388608
        or 'ALL' not in h['CapDrop'] or 'no-new-privileges' not in h['SecurityOpt'] or h['Tmpfs']!=tmpfs_options()):
        raise ValueError('Smoke sandbox isolation mismatch')
    limits={v['Name']:(v['Soft'],v['Hard']) for v in h['Ulimits']}
    if limits.get('fsize')!=(8388608,8388608) or limits.get('nofile')!=(1024,1024):
        raise ValueError('Missing file/process limits')
    binds={m['Destination']:m for m in c['Mounts'] if m['Type']=='bind'}
    expected={'/inputs':str(root/'inputs'),'/inspection':str(root/'inspection')}
    if set(binds)!=set(expected) or any(binds[k]['RW'] or binds[k]['Source']!=v for k,v in expected.items()):
        raise ValueError('Unapproved host mount')
    if any(m['Type'] not in ('bind','tmpfs') for m in c['Mounts']):raise ValueError('Unexpected volume')


def extract_archive(raw,destination,allowed=None):
    allowed=ALLOWED if allowed is None else allowed
    if len(raw)>MAX_ARCHIVE:raise ValueError('Archive size cap')
    destination=Path(destination)
    if destination.is_symlink():raise ValueError('Unsafe output directory')
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
        members=[];seen=set();total=0
        for entry in archive:
            if entry.isdir() and entry.name in ('.','./'):continue
            name=entry.name.removeprefix('./')
            if (PurePosixPath(name).name!=name or '\\' in name or name not in allowed
                or not entry.isfile() or name in seen or entry.size<0 or entry.size>8*1024**2
                or (destination/name).exists() or (destination/name).is_symlink()):
                raise ValueError('Unsafe/duplicate archive member')
            total+=entry.size
            if total>MAX_ARCHIVE or len(seen)>=128:raise ValueError('Archive expansion cap')
            seen.add(name);members.append((entry,name))
        for entry,name in members:
            with archive.extractfile(entry) as source,(destination/name).open('xb') as target:
                shutil.copyfileobj(source,target,65536)
    return sorted(seen)


def collect_if_ready(name,output,extractor=None):
    """An exec race is recorded, never treated as successful capture."""
    probe=call('exec',name,'/bin/sh','-c','if test -f /output/ready; then echo READY; fi')
    if probe.returncode:return dict(captured=False,race=True,error=probe.stderr.decode(errors='replace')[:1000])
    if probe.stdout.strip()!=b'READY':return dict(captured=False,race=False)
    archive=call('exec',name,'tar','--format=ustar','-C','/output','-cf','-','.')
    if archive.returncode:return dict(captured=False,race=True,error=archive.stderr.decode(errors='replace')[:1000])
    members=(extract_archive if extractor is None else extractor)(archive.stdout,output)
    ack=call('exec',name,'/bin/sh','-c','touch /output/collected')
    return dict(captured=True,members=members,acknowledged=ack.returncode==0,race=ack.returncode!=0)


def retain_logs(name,root):
    p=call('logs',name)
    (root/'docker.stdout').write_bytes(p.stdout);(root/'docker.stderr').write_bytes(p.stderr)
    return dict(exit_code=p.returncode,stdout_bytes=len(p.stdout),stderr_bytes=len(p.stderr))


def daemon_events(container_id,since):
    class Connection(http.client.HTTPConnection):
        def connect(self):
            self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.sock.settimeout(10)
            self.sock.connect('/var/run/docker.sock')
    query=urllib.parse.urlencode(dict(since=int(since)-2,until=int(time.time())+1,
        filters=json.dumps({'container':[container_id]})))
    conn=Connection('localhost');conn.request('GET','/events?'+query);response=conn.getresponse()
    raw=response.read(2*1024**2+1);conn.close()
    if response.status!=200 or len(raw)>2*1024**2:raise ValueError('Daemon event query failed/bounded')
    rows=[json.loads(line) for line in raw.splitlines() if line]
    if any(e['Actor']['ID']!=container_id for e in rows):raise ValueError('Unowned daemon event')
    return rows


def retain_terminal_evidence(name,container_id,since,root,result,owner_label=None,collector=None):
    """Independent capture paths: failed inspect/exec cannot suppress Docker logs."""
    try:
        c=inspect(name);assert_owned(c,name,owner_label)
        if c['State']['Running']:
            if not result['capture']['captured']:
                try:result['capture']=(collect_if_ready if collector is None else collector)(name,root/'capture')
                except Exception as exc:result['errors'].append(dict(kind='FINAL_CAPTURE',detail=str(exc)[:1000]))
            docker('kill',name);c=inspect(name)
        write(root/'inspect.final.private.json',c);result['terminal_state']=c['State']
    except Exception as exc:
        result['errors'].append(dict(kind='HOST_STATE',detail=str(exc)[:1000]))
    try:result['docker_logs']=retain_logs(name,root)
    except Exception as exc:result['errors'].append(dict(kind='HOST_LOGS',detail=str(exc)[:1000]))
    try:
        events=daemon_events(container_id,since);write(root/'events.private.json',events)
        result['events']=[dict(action=e['Action'],time_nano=e['timeNano'],exit_code=e['Actor']['Attributes'].get('exitCode')) for e in events]
    except Exception as exc:result['errors'].append(dict(kind='HOST_EVENTS',detail=str(exc)[:1000]))
    try:
        current=inspect(name);assert_owned(current,name,owner_label)
        docker('rm','-f','-v',name);result['cleanup_complete']=True
    except Exception as exc:result['errors'].append(dict(kind='CLEANUP',detail=str(exc)[:1000]))


def run_smoke(root):
    root=Path(root).absolute();enforce_process_limits()
    with (root/'attempt_claim.json').open('x') as f:json.dump(dict(mode='NO_MAVEN_SMOKE',max_containers=1),f)
    output=root/'capture';output.mkdir(exist_ok=False)
    result=dict(status='BLOCKED',mode='NO_MAVEN_SMOKE',maven_processes=0,compiler_processes=0,
        attempts=1,capture=dict(captured=False),cleanup_complete=False,errors=[])
    try:admitted=admission()
    except Exception as exc:
        result['errors'].append(dict(kind='RESOURCE_ADMISSION',detail=str(exc)[:1000]))
        write(root/'execution.json',result);return result
    write(root/'resource_admission.json',admitted)
    name='td522e01-'+uuid.uuid4().hex[:12];created_at=time.time();created=False
    result.update(container=name,image=IMAGE,minimum_host_available_bytes=admitted['available_ram_bytes'])
    cmd=['create','--name',name,'--label',LABEL+'='+name,'--pull','never','--network','none',
        '--memory',str(MEMORY),'--memory-swap',str(MEMORY),'--cpus','1','--pids-limit','64',
        '--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only',
        '--shm-size','8388608','--ulimit','fsize=8388608:8388608','--ulimit','nofile=1024:1024',
        '--log-driver','local','--log-opt','max-size=1m','--log-opt','max-file=1','--log-opt','compress=false',
        '--workdir','/source','--entrypoint','/bin/sh','--env','HOME=/tmp','--env','TD_CAPTURE_HOLD_SECONDS=15']
    for path,options in tmpfs_options().items():cmd+=['--tmpfs',path+':'+options]
    for path in ('inputs','inspection'):cmd+=['--mount',f'type=bind,src={root/path},dst=/{path},readonly']
    cmd += [IMAGE,'/inspection/wrapper.sh','--no-maven-smoke'];result['create_command']=cmd
    try:
        if json.loads(docker('image','inspect',IMAGE))[0]['Id']!=IMAGE:raise ValueError('Pinned image absent')
        result['container_id']=docker(*cmd).decode().strip();created=True
        c=inspect(name);verify_container(c,name,root);write(root/'inspect.before.private.json',c)
        result['admission_immediately_before_start']=admission()
        docker('start',name);started=time.monotonic()
        while True:
            c=inspect(name)
            result['minimum_host_available_bytes']=min(result['minimum_host_available_bytes'],host_available())
            if result['minimum_host_available_bytes']<2*1024**3:raise RuntimeError('Host headroom violation')
            if not c['State']['Running']:break
            if not result['capture']['captured']:
                capture=collect_if_ready(name,output)
                if capture.get('race'):result['errors'].append(dict(kind='EXEC_RACE',detail=capture.get('error')))
                if capture['captured']:result['capture']=capture
            if time.monotonic()-started>110:raise TimeoutError('Smoke110second outer limit')
            time.sleep(0.25)
    except Exception as exc:
        result['errors'].append(dict(kind=type(exc).__name__,detail=str(exc)[:1000]))
    finally:
        if created:
            retain_terminal_evidence(name,result['container_id'],created_at,root,result)
        if result['capture']['captured'] and result.get('terminal_state',{}).get('ExitCode')==73:
            result['status']='CAPTURED_EXPECTED_SMOKE_EXIT_PENDING_VALIDATION'
        write(root/'execution.json',result)
    return result


def canonical_paths_match(content,expected):
    if content is None:return False
    actual=content.splitlines();wanted=[line.split('  ',1)[1] for line in expected]
    # Locale changes display order, not the required exact unique population.
    return len(actual)==len(set(actual))==len(wanted) and sorted(actual)==sorted(wanted)


def completeness(root):
    root=Path(root);capture=root/'capture';run=json.loads((root/'execution.json').read_text())
    def read(name):
        p=capture/name
        return p.read_text() if p.is_file() else None
    required={'setup.stdout','setup.stderr','exit.code','stage.txt','command-category.txt','passed-stages.txt',
        'mount-ownership.txt','mountinfo.txt','source.paths','cache.paths','source.after.sha256','cache.after.sha256',
        'working-directory.txt','setup.complete','processes.txt','maven.state.txt','memory.peak','memory.events','cpu.stat','cgroup.limits.txt'}
    missing=sorted(n for n in required if not (capture/n).is_file())
    expected_source=(root/'inspection/source.sha256').read_text().splitlines()
    expected_cache=(root/'inspection/cache.sha256').read_text().splitlines()
    def hashes(name,prefix):
        content=read(name)
        return sorted(line.replace(prefix,'',1) for line in content.splitlines()) if content is not None else None
    checks=dict(all_required_fields=not missing,exit_code=read('exit.code')=='73\n',
        stage=read('stage.txt')=='INJECTED_PRE_MAVEN_FAILURE\n',category=read('command-category.txt')=='deliberate_exit_73\n',
        setup_complete=read('setup.complete')=='true\n',
        stdout_sentinel='TD_SMOKE_INJECTED_STDOUT\n' in (read('setup.stdout') or ''),
        stderr_sentinel=(read('setup.stderr') or '')=='TD_SMOKE_INJECTED_STDERR\nSTAGE_FAILED INJECTED_PRE_MAVEN_FAILURE deliberate_exit_73 exit=73\n',
        source_hashes=hashes('source.after.sha256','/source/')==sorted(expected_source),
        cache_hashes=hashes('cache.after.sha256','/runtime-repository/')==sorted(expected_cache),
        source_paths=canonical_paths_match(read('source.paths'),expected_source),
        cache_paths=canonical_paths_match(read('cache.paths'),expected_cache),
        ownership=read('mount-ownership.txt')=='/source 1000:1000:1777\n/runtime-repository 1000:1000:1777\n',
        cwd=read('working-directory.txt')=='/source\n',maven_not_started=read('maven.state.txt')=='NOT_STARTED\n',
        prohibited_process_absent=not set((read('processes.txt') or '').splitlines())&{'java','mvn','javac','sonar-scanner'},
        no_oom=run.get('terminal_state',{}).get('OOMKilled') is False,
        terminal_exit=run.get('terminal_state',{}).get('ExitCode')==73,
        docker_logs_retained=run.get('docker_logs',{}).get('exit_code')==0,
        exactly_one_start=sum(e['action']=='start' for e in run.get('events',[]))==1,
        die_matches=sum(e['action']=='die' and e['exit_code']=='73' for e in run.get('events',[]))==1,
        cleanup=run['cleanup_complete'],
        no_unexpected_capture_error=not any(e['kind']!='EXEC_RACE' for e in run['errors']))
    if read('memory.peak') is not None:
        checks['bounded_peak']=0<int(read('memory.peak'))<=MEMORY
    else:checks['bounded_peak']=False
    result=dict(status='SETUP_AND_CAPTURE_PASS' if all(checks.values()) else
                ('PARTIAL' if checks['setup_complete'] else 'BLOCKED'),checks=checks,
        unavailable=missing,cgroup_peak_memory_bytes=int(read('memory.peak')) if read('memory.peak') else None,
        maven_or_compilation_success=False,expected_injection_exit=73)
    write(root/'capture_completeness.json',result)
    return result
