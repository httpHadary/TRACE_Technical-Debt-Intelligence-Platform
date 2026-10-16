"""Exactly one offline T0 compilation; no acquisition or automatic retry."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import tarfile
import time
import uuid
from tools.inspect_phase5_2_2_d_3 import sha, write, docker, host_available, COMMIT, TREE, POM, IMAGE
from tools.recover_phase5_2_2_d_2 import verify_rows, enforce_process_limits
from tools.recover_phase5_2_2_d import git

BASE='96d5f308e1b955dd53ac368c48f7b35a0e6c709c'
MEMORY=2*1024**3
LABEL='techdebt360.phase522e0'
PREVIOUS=Path('/home/hp/tst/research/forecasting_mvp/phase5_2_2_d_3/2026-10-16')


def command():
    return ['/usr/share/maven/bin/mvn','--offline','--batch-mode','--no-transfer-progress','--errors',
        '-s','/inspection/settings.xml','-gs','/inspection/settings.xml',
        '-Dmaven.repo.local=/runtime-repository','-Duser.home=/tmp',
        '-Dmaven.test.skip=true','-Dmaven.compiler.release=8','compile']


def verify_and_prepare(base,root):
    """Verify published evidence before any executable build container exists."""
    base,root=Path(base),Path(root)
    if root.is_relative_to(PREVIOUS) or any(p.is_symlink() or (p/'.git').exists() for p in (root,*root.parents)):
        raise ValueError('Fresh isolated output outside Git required')
    identity=json.loads((base/'examples/phase5_2_2_d_3/effective_model_identity.json').read_text())
    effective=PREVIOUS/'effective-pom/effective-pom.xml'
    if (identity['commit_sha']!=COMMIT or identity['tree_sha']!=TREE or identity['pom_sha256']!=POM
            or sha(effective)!=identity['effective_pom_sha256']
            or sha(PREVIOUS/'source_identity.json')!=identity['source_id']):
        raise ValueError('D.3 source/model identity changed')
    if (PREVIOUS/'active-profiles/active-profiles.txt').read_bytes()!=(base/'examples/phase5_2_2_d_3/active-profiles.txt').read_bytes():
        raise ValueError('Active profile evidence changed')
    originals=[(PREVIOUS.parent.parent/'phase5_2_2_d_2/2026-10-16/recovery-1',
        base/'examples/phase5_2_2_d_2/dependency_manifest.json',624),
        (PREVIOUS/'helper-1',base/'examples/phase5_2_2_d_3/helper_dependency_manifest.json',29)]
    records={}
    for source,published,count in originals:
        m=json.loads(published.read_text())
        if json.loads((source/'dependency_manifest.json').read_text())!=m or len(m['artifacts'])!=count:
            raise ValueError('Published artifact manifest mismatch')
        verified=verify_rows(source,m)
        if records.keys() & verified.keys():raise ValueError('Historical/helper identity collision')
        records.update(verified)
    previous_runtime=json.loads((PREVIOUS/'runtime_cache_manifest.json').read_text())
    if {r['path']:r for r in previous_runtime['artifacts']}!=records:
        raise ValueError('D.3 runtime inventory changed')
    seeds=root/'inputs';seeds.mkdir(exist_ok=False)
    cache=seeds/'repository';cache.mkdir()
    for name,row in records.items():
        src=PREVIOUS/'runtime-repository'/name
        if src.is_symlink() or sha(src)!=row['sha256']:raise ValueError('D.3 runtime artifact changed')
        dest=cache/name;dest.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as left,dest.open('xb') as right:shutil.copyfileobj(left,right,65536)
        if sha(dest)!=row['sha256'] or dest.stat().st_ino==src.stat().st_ino:
            raise ValueError('Independent artifact copy mismatch')
        dest.chmod(0o444)
    source=json.loads((PREVIOUS/'source_identity.json').read_text())
    config=json.loads((base/'examples/phase5_2/replay_sources.example.json').read_text())
    repo=next(r['path'] for r in config if r['repository_id']=='apache/commons-cli')
    if git(repo,'rev-parse',COMMIT+'^{tree}').decode().strip()!=TREE:raise ValueError('Frozen Git tree changed')
    actual={}
    for raw in git(repo,'ls-tree','-r','-z',COMMIT).split(b'\0'):
        if raw:
            head,name=raw.split(b'\t');mode,kind,oid=head.decode().split()
            actual[name.decode()]=(mode,kind,oid)
    if len(source['entries'])!=117 or actual!={r['path']:(r['mode'],'blob',r['git_blob']) for r in source['entries']}:
        raise ValueError('Full frozen source inventory mismatch')
    tree=seeds/'source';tree.mkdir()
    for row in source['entries']:
        src=PREVIOUS/'source'/row['path'];data=src.read_bytes()
        if src.is_symlink() or sha(src)!=row['sha256'] or hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=row['git_blob']:
            raise ValueError('Frozen source blob mismatch')
        dest=tree/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        dest.chmod(0o555 if row['mode']=='100755' else 0o444)
    inspection=root/'inspection';inspection.mkdir()
    settings=PREVIOUS/'inspection/settings.xml'
    if sha(settings)!=identity['settings_sha256']:raise ValueError('Registered settings changed')
    shutil.copyfile(settings,inspection/'settings.xml');(inspection/'wrapper.sh').write_text(WRAPPER)
    result=dict(version='phase522e0-prerequisites-v1',commit_sha=COMMIT,tree_sha=TREE,pom_sha256=POM,
        effective_pom_sha256=sha(effective),active_profiles_sha256=sha(PREVIOUS/'active-profiles/active-profiles.txt'),
        historical_artifacts=624,helper_artifacts=29,independent_runtime_copies=653,tracked_files=117,
        source_entries=source['entries'],artifact_records=list(records.values()),
        expected_lifecycle=[p for p in json.loads((base/'examples/phase5_2_2_d_3/static_vs_maven.json').read_text())['effective_plugins']
                            if any(e['required_through_compile'] for e in p['executions'])],
        old_ledgers=[2000,400,52,112],downloads=0)
    write(root/'prerequisites.json',result)
    return result


WRAPPER='''#!/bin/sh
set -u
[ "$(cat /sys/fs/cgroup/memory.max)" = "2147483648" ] || exit 120
[ "$(cat /sys/fs/cgroup/memory.swap.max)" = "0" ] || exit 121
read quota period < /sys/fs/cgroup/cpu.max
[ "$quota" != max ] && [ "$quota" -le "$period" ] || exit 122
cp -R /inputs/source/. /source/ || exit 123
chmod -R u+w /source || exit 123
cp -R /inputs/repository/. /runtime-repository/ || exit 123
chmod -R u+w /runtime-repository || exit 123
cd /source || exit 123
find . -type f -print0 | sort -z | xargs -0 sha256sum > /output/source-before.sha256
find /runtime-repository -type f -print0 | sort -z | xargs -0 sha256sum > /output/cache-before.sha256
cut -d ' ' -f 1 /proc/uptime > /output/start.uptime
timeout --signal=TERM --kill-after=5s 240s "$@" > /output/maven.stdout 2> /output/maven.stderr
status=$?
printf '%s\\n' "$status" > /output/build.exit
cut -d ' ' -f 1 /proc/uptime > /output/end.uptime
cat /sys/fs/cgroup/memory.peak > /output/memory.peak
cat /sys/fs/cgroup/cpu.stat > /output/cpu.stat
cat /sys/fs/cgroup/memory.events > /output/memory.events
find . -type f -print0 | sort -z | xargs -0 sha256sum > /output/source-after.sha256
find /runtime-repository -type f -print0 | sort -z | xargs -0 sha256sum > /output/cache-after.sha256
du -sb /source /runtime-repository /tmp /output > /output/disk-usage.txt
if [ -d target/classes ]; then cp -R target/classes /output/classes; fi
if [ -d target/test-classes ]; then touch /output/unexpected-test-classes; fi
touch /output/ready
count=0
while [ ! -f /output/collected ] && [ "$count" -lt 30 ]; do sleep 1; count=$((count+1)); done
exit "$status"
'''


def resource_admission():
    available=host_available()
    if available<MEMORY+2*1024**3:raise RuntimeError('BLOCKED_RESOURCES: RAM below container plus2GiB headroom')
    if docker('ps','-q').strip():raise RuntimeError('BLOCKED_RESOURCES: concurrent container requires review')
    conflicts=[]
    for proc in Path('/proc').iterdir():
        if proc.name.isdigit():
            try:
                comm=(proc/'comm').read_text().strip()
                if comm in ('java','mvn','sonar-scanner'):conflicts.append(dict(pid=proc.name,comm=comm))
            except (FileNotFoundError,PermissionError):continue
    if conflicts:raise RuntimeError('BLOCKED_RESOURCES: Java/Maven/Sonar process '+str(conflicts))
    free=shutil.disk_usage('/home/hp/tst').free
    if free<512*1024**2:raise RuntimeError('BLOCKED_RESOURCES: insufficient bounded evidence storage')
    return dict(available_ram_bytes=available,free_disk_bytes=free,minimum_host_headroom_bytes=2*1024**3,
        concurrent_build_or_sonar_processes=conflicts,running_containers=0)


def validate_container(c,name,root):
    h,cfg=c['HostConfig'],c['Config']
    if (c['Name']!='/'+name or c['Image']!=IMAGE or cfg['Labels'].get(LABEL)!=name
        or cfg['User']!='1000:1000' or cfg['Cmd']!=['/inspection/wrapper.sh',*command()]
        or h['NetworkMode']!='none' or h['Memory']!=MEMORY or h['MemorySwap']!=MEMORY
        or h['NanoCpus']!=1000000000 or h['PidsLimit']!=64 or not h['ReadonlyRootfs'] or h['Privileged']
        or 'ALL' not in h['CapDrop'] or 'no-new-privileges' not in h['SecurityOpt']):
        raise ValueError('Build isolation mismatch')
    binds={m['Destination']:m for m in c['Mounts'] if m['Type']=='bind'}
    expected={'/inputs':str(root/'inputs'),'/inspection':str(root/'inspection')}
    if set(binds)!=set(expected) or any(binds[k]['RW'] or binds[k]['Source']!=v for k,v in expected.items()):
        raise ValueError('Unregistered/writable host bind')
    if any(m['Type'] not in ('bind','tmpfs') for m in c['Mounts']):raise ValueError('Unexpected volume')


def extract_evidence(raw,output):
    if len(raw)>32*1024**2:raise ValueError('Evidence archive cap')
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
        names=set()
        for item in archive:
            name=item.name.removeprefix('./');p=Path(name)
            if item.isdir():continue
            if (not item.isfile() or p.is_absolute() or '..' in p.parts or name in names
                or item.size>8*1024**2 or (len(p.parts)>1 and p.parts[0]!='classes')):
                raise ValueError('Unsafe build evidence entry')
            names.add(name);dest=output/p;dest.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(item) as stream:dest.write_bytes(stream.read())
    if not {'build.exit','memory.peak','maven.stdout','maven.stderr','source-before.sha256','source-after.sha256'}<=names:
        raise ValueError('Incomplete build evidence')


def namespace_archive(name):
    def small_stack():resource.setrlimit(resource.RLIMIT_STACK,(1048576,1048576))
    env=dict(os.environ,GOMAXPROCS='1',GOMEMLIMIT='64MiB',MALLOC_ARENA_MAX='1')
    result=subprocess.run(['docker','exec',name,'tar','--format=ustar','-C','/output','-cf','-','.'],
        capture_output=True,env=env,preexec_fn=small_stack,timeout=20)
    if result.returncode or len(result.stdout)>32*1024**2:raise ValueError('Build evidence export failed')
    return result.stdout


def execute_once(root):
    root=Path(root).absolute();enforce_process_limits()
    # O_EXCL claim is never reset, even on resource/startup/capture failure.
    with (root/'attempt_claim.json').open('x') as stream:json.dump(dict(command=command(),max_attempts=1),stream)
    admission=resource_admission();write(root/'resource_admission.json',admission)
    name='td522e0-'+uuid.uuid4().hex[:12];output=root/'build';output.mkdir(exist_ok=False)
    env={'HOME':'/tmp','MAVEN_CONFIG':'/tmp/.m2','MAVEN_SKIP_RC':'true','MAVEN_ARGS':'',
        'MAVEN_OPTS':'-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp',
        'JAVA_TOOL_OPTIONS':'','JDK_JAVA_OPTIONS':''}
    cmd=['create','--name',name,'--label',LABEL+'='+name,'--pull','never','--network','none',
        '--memory',str(MEMORY),'--memory-swap',str(MEMORY),'--cpus','1','--pids-limit','64',
        '--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only',
        '--shm-size','8388608','--ulimit','fsize=8388608:8388608','--ulimit','nofile=1024:1024',
        '--log-driver','local','--log-opt','max-size=1m','--log-opt','max-file=1','--log-opt','compress=false',
        '--workdir','/source','--entrypoint','/bin/sh']
    for directory,size in [('source',128),('runtime-repository',128),('tmp',128),('output',32)]:
        cmd+=['--tmpfs',f'/{directory}:rw,nosuid,nodev,noexec,size={size*1024**2},mode=1777']
    for key,value in env.items():cmd+=['--env',key+'='+value]
    for directory in ('inputs','inspection'):cmd+=['--mount',f'type=bind,src={root/directory},dst=/{directory},readonly']
    cmd += [IMAGE,'/inspection/wrapper.sh',*command()]
    if json.loads(docker('image','inspect',IMAGE))[0]['Id']!=IMAGE:raise ValueError('Pinned image missing')
    docker(*cmd);started=time.monotonic();minimum_ram=host_available();collected=False
    result=dict(command=command(),environment=env,image=IMAGE,container=name,attempts=1,network='none',
        memory_bytes=MEMORY,heap_max_bytes=768*1024**2,swap_allowance_bytes=0,cpus=1,pids=64,
        build_timeout_seconds=240,host_outer_timeout_seconds=260,writable_tmpfs_total_bytes=416*1024**2,
        single_file_cap_bytes=8*1024**2,source_revision=COMMIT,cleanup_complete=False)
    try:
        inspected=json.loads(docker('inspect',name))[0];validate_container(inspected,name,root)
        checks=[]
        reference=json.loads((Path(__file__).resolve().parents[1]/'examples/phase5_2_2_b/runtime_evidence.json').read_text())
        for path in ('usr/share/maven/bin/mvn','usr/share/maven/lib/maven-core-3.9.11.jar',
                     'opt/java/openjdk/bin/java','opt/java/openjdk/release'):
            target=output/Path(path).name;docker('cp',name+':/'+path,str(target));value=sha(target);target.unlink()
            if not any(v['path']==path and v['sha256']==value for v in reference['artifact_checks']):
                raise ValueError('Pinned executable hash mismatch')
            checks.append(dict(path=path,sha256=value))
        # Re-admit immediately before the only startup; no unrelated service changes.
        result['admission_immediately_before_start']=resource_admission()
        docker('start',name)
        while True:
            current=json.loads(docker('inspect',name))[0];minimum_ram=min(minimum_ram,host_available())
            if minimum_ram<2*1024**3:raise RuntimeError('Host2GiB headroom violation')
            if not current['State']['Running']:break
            if docker('exec',name,'/bin/sh','-c','if test -f /output/ready; then echo READY; fi').strip()==b'READY' and not collected:
                extract_evidence(namespace_archive(name),output)
                docker('exec',name,'/bin/sh','-c','touch /output/collected');collected=True
            if time.monotonic()-started>260:raise TimeoutError('Build outer timeout')
            time.sleep(0.5)
        result.update(exit_code=current['State']['ExitCode'],oom_killed=current['State']['OOMKilled'],
            captured=collected,binary_checks=checks,host_wall_seconds=time.monotonic()-started,
            minimum_host_available_bytes=minimum_ram,host_config={k:inspected['HostConfig'][k] for k in
                ('NetworkMode','Memory','MemorySwap','NanoCpus','PidsLimit','ReadonlyRootfs','Tmpfs','Ulimits','SecurityOpt','CapDrop')})
        if collected:
            result.update(maven_exit_code=int((output/'build.exit').read_text()),
                cgroup_peak_memory_bytes=int((output/'memory.peak').read_text()),
                goal_wall_seconds=float((output/'end.uptime').read_text())-float((output/'start.uptime').read_text()))
        return result
    except Exception as exc:
        result.update(execution_error=dict(type=type(exc).__name__,reason=str(exc)[:1000]),
            minimum_host_available_bytes=minimum_ram,captured=collected)
        raise
    finally:
        current=json.loads(docker('inspect',name))[0]
        if current['Config']['Labels'].get(LABEL)!=name:raise ValueError('Cleanup ownership mismatch')
        docker('rm','-f','-v',name);result['cleanup_complete']=True
        write(root/'execution.json',result)


def classify_result(exit_code,stdout,stderr,classes_complete=False,compiler_started=False,oom=False):
    combined=stdout+'\n'+stderr
    if oom or exit_code in (124,137,143):return 'BLOCKED_BUILD_OR_RESOURCE'
    if exit_code==0:return 'COMPILE_PASS' if classes_complete and compiler_started else 'PARTIAL'
    if re.search(r'could not be resolved|has not been downloaded|Cannot access .*offline|Could not find artifact',combined,re.I):
        return 'BLOCKED_DEPENDENCY'
    if re.search(r'not a git repository|\.git.*(?:missing|not found)|SCM.*(?:failed|failure|unable)',combined,re.I):
        return 'BLOCKED_SCM_CONTEXT'
    return 'BLOCKED_BUILD_OR_RESOURCE'
