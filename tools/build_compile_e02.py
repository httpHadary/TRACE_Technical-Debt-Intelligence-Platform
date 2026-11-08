"""E.0.2: one registered T0 offline compile, no recovery or retry entry point."""
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import tarfile
import time
import uuid
from tools import build_sandbox as b
from tools.recover_phase5_2_2_d import git
from tools.maven_recovery.acquisition import relative_path

BASE='67f2d304e2739e281edbc88e59fcc5840c4f1dea'
LABEL='techdebt360.phase522e02'
MEMORY=2*1024**3
OPTIONS='-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp'
ALLOWED=b.ALLOWED|{'maven.stdout','maven.stderr','maven.exit','maven.started.uptime','maven.ended.uptime',
    'source.post.sha256','cache.post.sha256','source.verify.stdout','source.verify.stderr','source.verify.exit',
    'classes.tar','test-classes.present','post-capture.errors','post-capture.complete','log.sizes',
    'compiler-inputs.txt','compiler-created.txt','disk-usage.txt'}


def maven_command():
    return ['/usr/share/maven/bin/mvn','--offline','--batch-mode','--no-transfer-progress','--errors',
        '-s','/inspection/settings.xml','-gs','/inspection/settings.xml','-Dmaven.repo.local=/runtime-repository',
        '-Duser.home=/tmp','-Dmaven.test.skip=true','-Dmaven.compiler.release=8','compile']


POST_CAPTURE='''
    # Post-build diagnostics cannot replace the original setup/Maven exit code.
    if [ -f "$OUT/maven.exit" ]; then
        (cd /source && sha256sum --quiet -c /inspection/source.sha256) > "$OUT/source.verify.stdout" 2> "$OUT/source.verify.stderr"
        printf '%s\\n' "$?" > "$OUT/source.verify.exit"
        find /source -type f -print0 | sort -z | xargs -0 sha256sum > "$OUT/source.post.sha256"
        find /runtime-repository -type f -print0 | sort -z | xargs -0 sha256sum > "$OUT/cache.post.sha256"
        if [ -d /source/target/classes ]; then
            tar --format=ustar -C /source/target/classes -cf "$OUT/classes.tar" . || printf 'classes_tar_failed\\n' >> "$OUT/post-capture.errors"
        fi
        if [ -d /source/target/test-classes ]; then printf 'true\\n' > "$OUT/test-classes.present"; fi
        if [ -f /source/target/maven-status/maven-compiler-plugin/compile/default-compile/inputFiles.lst ]; then
            cp /source/target/maven-status/maven-compiler-plugin/compile/default-compile/inputFiles.lst "$OUT/compiler-inputs.txt"
        fi
        if [ -f /source/target/maven-status/maven-compiler-plugin/compile/default-compile/createdFiles.lst ]; then
            cp /source/target/maven-status/maven-compiler-plugin/compile/default-compile/createdFiles.lst "$OUT/compiler-created.txt"
        fi
        wc -c "$OUT/maven.stdout" "$OUT/maven.stderr" > "$OUT/log.sizes"
        printf 'TD_MAVEN_STDOUT_LAST_65536_BYTES_BEGIN\\n' >&3
        tail -c 65536 "$OUT/maven.stdout" >&3
        printf '\\nTD_MAVEN_STDOUT_EXCERPT_END\\n' >&3
        printf 'TD_MAVEN_STDERR_LAST_65536_BYTES_BEGIN\\n' >&4
        tail -c 65536 "$OUT/maven.stderr" >&4
        printf '\\nTD_MAVEN_STDERR_EXCERPT_END\\n' >&4
        du -sb /source /runtime-repository /tmp /output > "$OUT/disk-usage.txt"
        printf 'true\\n' > "$OUT/post-capture.complete"
    fi
'''


def wrapper_script():
    """Versioned adapter from a hash-bound setup; original smoke script unmodified."""
    import shlex
    source=Path(b.__file__).with_name('build_sandbox_setup.sh').read_text()
    prefix,sentinel=source.split('# Deliberate sentinel, independent of historical sources/plugins. No Maven path.',1)
    if 'INJECTED_PRE_MAVEN_FAILURE' not in sentinel:raise ValueError('Unexpected smoke template')
    mode='run_stage MODE reject_non_smoke test "${1:-}" = --no-maven-smoke'
    guard='[ "$(cat /sys/fs/cgroup/memory.max)" = "1073741824" ]'
    if prefix.count(mode)!=1 or prefix.count(guard)!=1:raise ValueError('Setup template identity mismatch')
    prefix=prefix.replace(mode,'run_stage MODE explicit_e02_compile test "${1:-}" = --e02-offline-compile')
    prefix=prefix.replace(guard,'[ "$(cat /sys/fs/cgroup/memory.max)" = "2147483648" ]')
    prefix=prefix.replace('    for metric in memory.peak memory.events cpu.stat; do',POST_CAPTURE+'\n    for metric in memory.peak memory.events cpu.stat; do',1)
    return prefix+'''# E.0.2 allowlisted original lifecycle, exactly one launch.
STAGE=MAVEN_LIFECYCLE
COMMAND_CATEGORY=offline_compile
printf 'LAUNCH_REQUESTED\\n' > "$OUT/maven.state.txt"
cut -d ' ' -f 1 /proc/uptime > "$OUT/maven.started.uptime"
timeout --signal=TERM --kill-after=5s 240s '''+shlex.join(maven_command())+''' > "$OUT/maven.stdout" 2> "$OUT/maven.stderr"
maven_status=$?
printf '%s\\n' "$maven_status" > "$OUT/maven.exit"
cut -d ' ' -f 1 /proc/uptime > "$OUT/maven.ended.uptime"
if [ "$maven_status" -eq 0 ]; then printf 'MAVEN_LIFECYCLE\\n' >> "$OUT/passed-stages.txt"; fi
exit "$maven_status"
'''


def prepare(base,root):
    base,root=Path(base),Path(root)
    # Reuses E.0.1's independent copies/checksum/Git-blob validation, not E.0 runner.
    b.prepare(base,root)
    q=json.loads((b.E0/'prerequisites.json').read_text())
    config=json.loads((base/'examples/phase5_2/replay_sources.example.json').read_text())
    repo=next(x['path'] for x in config if x['repository_id']=='apache/commons-cli')
    if git(repo,'rev-parse',b.COMMIT+'^{tree}').decode().strip()!=b.TREE:raise ValueError('Pinned Git tree changed')
    actual={}
    for row in git(repo,'ls-tree','-r','-z',b.COMMIT).split(b'\0'):
        if row:
            header,name=row.split(b'\t');mode,kind,oid=header.decode().split();actual[name.decode()]=(mode,kind,oid)
    if actual!={r['path']:(r['mode'],'blob',r['git_blob']) for r in q['source_entries']}:
        raise ValueError('Full Git inventory changed')
    if b.sha(root/'inputs/source/pom.xml')!=b.POM:raise ValueError('Historical POM changed')
    d3=b.E0.parent.parent/'phase5_2_2_d_3/2026-10-16'
    identity=json.loads((base/'examples/phase5_2_2_d_3/effective_model_identity.json').read_text())
    if b.sha(d3/'effective-pom/effective-pom.xml')!=identity['effective_pom_sha256']:
        raise ValueError('Effective model changed')
    if (d3/'active-profiles/active-profiles.txt').read_bytes()!=(base/'examples/phase5_2_2_d_3/active-profiles.txt').read_bytes():
        raise ValueError('Profile evidence changed')
    if b.sha(d3/'inspection/settings.xml')!=identity['settings_sha256']:raise ValueError('Settings changed')
    shutil.copyfile(d3/'inspection/settings.xml',root/'inspection/settings.xml')
    (root/'inspection/wrapper.sh').write_text(wrapper_script())
    b.write(root/'compile_registration.json',dict(version='e02-offline-compile-v1',base_commit=BASE,
        commit=b.COMMIT,tree=b.TREE,pom_sha256=b.POM,command=maven_command(),image=b.IMAGE,
        memory_bytes=MEMORY,heap_max_bytes=768*1024**2,cpus=1,pids=64,swap_bytes=0,
        mode='--e02-offline-compile',source_files=117,artifacts=653,explicit_profiles=[],
        setup_template_sha256=b.sha(Path(b.__file__).with_name('build_sandbox_setup.sh')),
        executed_wrapper_sha256=b.sha(root/'inspection/wrapper.sh'),settings_sha256=identity['settings_sha256'],
        effective_pom_sha256=identity['effective_pom_sha256'],downloads=0,maximum_attempts=1))


def admission():
    evidence=b.admission()
    if evidence['available_ram_bytes']<4*1024**3:raise RuntimeError('BLOCKED_RESOURCES: less than4GiB available RAM')
    evidence.update(required_available_bytes=4*1024**3,container_budget_bytes=MEMORY,headroom_bytes=2*1024**3)
    return evidence


def validate_container(c,name,root):
    b.assert_owned(c,name,LABEL);h=c['HostConfig'];cfg=c['Config']
    env=dict(v.split('=',1) for v in cfg['Env'])
    if (c['Image']!=b.IMAGE or cfg['User']!='1000:1000' or cfg['Cmd']!=['/inspection/wrapper.sh','--e02-offline-compile']
        or cfg['Entrypoint']!=['/bin/sh'] or cfg['WorkingDir']!='/source' or env.get('MAVEN_OPTS')!=OPTIONS
        or h['Memory']!=MEMORY or h['MemorySwap']!=MEMORY or h['NanoCpus']!=1000000000 or h['PidsLimit']!=64
        or h['NetworkMode']!='none' or not h['ReadonlyRootfs'] or h['Privileged'] or h.get('CapAdd')
        or 'ALL' not in h['CapDrop'] or 'no-new-privileges' not in h['SecurityOpt'] or h['Tmpfs']!=b.tmpfs_options()):
        raise ValueError('E.0.2 isolation or command mismatch')
    limits={v['Name']:(v['Soft'],v['Hard']) for v in h['Ulimits']}
    if limits.get('fsize')!=(8388608,8388608) or limits.get('nofile')!=(1024,1024):raise ValueError('Output limits changed')
    binds={m['Destination']:m for m in c['Mounts'] if m['Type']=='bind'}
    expected={'/inputs':str(root/'inputs'),'/inspection':str(root/'inspection')}
    if set(binds)!=set(expected) or any(binds[k]['RW'] or binds[k]['Source']!=v for k,v in expected.items()):
        raise ValueError('Unapproved mount')
    if any(m['Type'] not in ('bind','tmpfs') for m in c['Mounts']):raise ValueError('Unexpected volume')


def collector(name,output):
    return b.collect_if_ready(name,output,extractor=lambda raw,dest:b.extract_archive(raw,dest,allowed=ALLOWED))


def execute_once(root):
    root=Path(root).absolute();b.enforce_process_limits()
    with (root/'attempt_claim.json').open('x') as f:json.dump(dict(mode='E02_OFFLINE_COMPILE',maximum_attempts=1),f)
    result=dict(status='BLOCKED_BUILD_OR_RESOURCE',capture=dict(captured=False),errors=[],cleanup_complete=False,
        attempts=1,command=maven_command(),maven_environment={'MAVEN_OPTS':OPTIONS},mode='E02_OFFLINE_COMPILE')
    try:resource=admission()
    except Exception as exc:
        result['substatus']='BLOCKED_RESOURCES';result['errors'].append(dict(kind='RESOURCE_ADMISSION',detail=str(exc)))
        b.write(root/'execution.json',result);return result
    b.write(root/'resource_admission.json',resource)
    (root/'capture').mkdir(exist_ok=False)
    name='td522e02-'+uuid.uuid4().hex[:12];created=False;created_at=time.time()
    result.update(container=name,image=b.IMAGE,minimum_host_available_bytes=resource['available_ram_bytes'])
    env={'HOME':'/tmp','MAVEN_CONFIG':'/tmp/.m2','MAVEN_SKIP_RC':'true','MAVEN_ARGS':'',
        'MAVEN_OPTS':OPTIONS,'JAVA_TOOL_OPTIONS':'','JDK_JAVA_OPTIONS':'','TD_CAPTURE_HOLD_SECONDS':'15'}
    cmd=['create','--name',name,'--label',LABEL+'='+name,'--pull','never','--network','none',
        '--memory',str(MEMORY),'--memory-swap',str(MEMORY),'--cpus','1','--pids-limit','64',
        '--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only',
        '--shm-size','8388608','--ulimit','fsize=8388608:8388608','--ulimit','nofile=1024:1024',
        '--log-driver','local','--log-opt','max-size=1m','--log-opt','max-file=1','--log-opt','compress=false',
        '--workdir','/source','--entrypoint','/bin/sh']
    for key,value in env.items():cmd+=['--env',key+'='+value]
    for path,options in b.tmpfs_options().items():cmd+=['--tmpfs',path+':'+options]
    for path in ('inputs','inspection'):cmd+=['--mount',f'type=bind,src={root/path},dst=/{path},readonly']
    cmd += [b.IMAGE,'/inspection/wrapper.sh','--e02-offline-compile'];result['create_command']=cmd
    try:
        if json.loads(b.docker('image','inspect',b.IMAGE))[0]['Id']!=b.IMAGE:raise ValueError('Pinned image missing')
        result['container_id']=b.docker(*cmd).decode().strip();created=True
        c=b.inspect(name);validate_container(c,name,root);b.write(root/'inspect.before.private.json',c)
        checks=[];reference=json.loads((Path(__file__).resolve().parents[1]/'examples/phase5_2_2_b/runtime_evidence.json').read_text())
        for path in ('usr/share/maven/bin/mvn','usr/share/maven/lib/maven-core-3.9.11.jar','opt/java/openjdk/bin/java','opt/java/openjdk/release'):
            dst=root/Path(path).name;b.docker('cp',name+':/'+path,str(dst));value=b.sha(dst);dst.unlink()
            if not any(v['path']==path and v['sha256']==value for v in reference['artifact_checks']):raise ValueError('Pinned binary mismatch')
            checks.append(dict(path=path,sha256=value))
        result['binary_checks']=checks;result['admission_immediately_before_start']=admission()
        b.docker('start',name);started=time.monotonic()
        while True:
            c=b.inspect(name);result['minimum_host_available_bytes']=min(result['minimum_host_available_bytes'],b.host_available())
            if result['minimum_host_available_bytes']<2*1024**3:raise RuntimeError('Host2GiB headroom violation')
            if not c['State']['Running']:break
            if not result['capture']['captured']:
                captured=collector(name,root/'capture')
                if captured.get('race'):result['errors'].append(dict(kind='EXEC_RACE',detail=captured.get('error')))
                if captured['captured']:result['capture']=captured
            if time.monotonic()-started>265:raise TimeoutError('E02 outer monitor timeout')
            time.sleep(0.25)
        result['host_execution_seconds']=time.monotonic()-started
    except Exception as exc:result['errors'].append(dict(kind=type(exc).__name__,detail=str(exc)[:1500]))
    finally:
        if created:b.retain_terminal_evidence(name,result['container_id'],created_at,root,result,owner_label=LABEL,collector=collector)
        b.write(root/'execution.json',result)
    return result


def parse_class(raw):
    """Structural class-file parsing, not a substitute for JVM bytecode verification."""
    offset=0
    def take(n):
        nonlocal offset
        if n<0 or offset+n>len(raw):raise ValueError('Truncated class structure')
        value=raw[offset:offset+n];offset+=n;return value
    def u2():return struct.unpack('>H',take(2))[0]
    def u4():return struct.unpack('>I',take(4))[0]
    if take(4)!=b'\xca\xfe\xba\xbe':raise ValueError('Invalid class magic')
    minor,major=u2(),u2()
    if major!=52:raise ValueError('Expected Java8 major52')
    count=u2();pool=[None]*count;index=1
    while index<count:
        tag=take(1)[0]
        if tag==1:value=take(u2())
        elif tag in (7,8,16):value=u2()
        elif tag in (3,4,9,10,11,12,18):value=take(4)
        elif tag in (5,6):
            value=take(8);pool[index]=(tag,value);index+=2
            if index>count:raise ValueError('Invalid double-slot constant')
            continue
        elif tag==15:value=take(3)
        else:raise ValueError('Unsupported Java8 constant tag')
        pool[index]=(tag,value);index+=1
    def constant(i,tag):
        if not 0<i<count or pool[i] is None or pool[i][0]!=tag:raise ValueError('Invalid constant reference')
        return pool[i][1]
    def utf(i):return constant(i,1).decode('utf-8')
    flags=u2();this=u2();parent=u2();name=utf(constant(this,7))
    if parent:constant(parent,7)
    for _ in range(u2()):constant(u2(),7)
    def attributes():
        rows=[]
        for _ in range(u2()):
            label=utf(u2());data=take(u4());rows.append((label,data))
        return rows
    for _kind in ('fields','methods'):
        for _ in range(u2()):
            u2();utf(u2());utf(u2());attributes()
    source=None
    for label,data in attributes():
        if label=='SourceFile':
            if len(data)!=2:raise ValueError('Invalid SourceFile attribute')
            source=utf(struct.unpack('>H',data)[0])
    if offset!=len(raw):raise ValueError('Trailing class bytes')
    return dict(internal_name=name,major=major,minor=minor,source_file=source,access_flags=flags)


def class_manifest(root):
    root=Path(root);expected={};package_info=[]
    for p in (root/'inputs/source/src/main').rglob('*.java'):
        text=p.read_text();match=re.search(r'^\s*package\s+([\w.]+)\s*;',text,re.M)
        if not match:raise ValueError('Production source package unavailable')
        name=match[1].replace('.','/')+'/'+p.stem
        if p.name=='package-info.java':package_info.append(name)
        else:expected[name]=p.name
    result=dict(status='NOT_PRODUCED',expected_top_level=sorted(expected),expected_top_level_count=len(expected),
        package_info_sources=package_info,classes=[],missing_top_level=sorted(expected),complete=False)
    archive=root/'capture/classes.tar'
    if not archive.exists():return result
    seen=set();total=0;errors=[]
    with tarfile.open(archive,'r:') as tar:
        for member in tar:
            if member.isdir():continue
            name=member.name.removeprefix('./');p=PurePosixPath(name)
            if (not member.isfile() or p.is_absolute() or '..' in p.parts or '\\' in name
                or not name.endswith('.class') or name in seen or member.size>8*1024**2 or len(seen)>=1024):
                raise ValueError('Unsafe class archive')
            total+=member.size
            if total>32*1024**2:raise ValueError('Class archive expansion cap')
            seen.add(name)
            with tar.extractfile(member) as stream:raw=stream.read()
            parsed=parse_class(raw)
            if parsed['internal_name']+'.class'!=name:raise ValueError('Class identity/path mismatch')
            owner=parsed['internal_name'].split('$',1)[0]
            kind='top_level' if parsed['internal_name'] in expected else ('package_info' if parsed['internal_name'] in package_info else 'nested')
            if kind!='package_info' and (owner not in expected or parsed['source_file']!=expected[owner]):
                errors.append(dict(path=name,reason='SourceFile/production identity mismatch'))
            result['classes'].append(dict(path=name,kind=kind,bytes=len(raw),sha256=__import__('hashlib').sha256(raw).hexdigest(),**parsed))
    actual={x['internal_name'] for x in result['classes'] if x['kind']=='top_level'}
    result.update(status='VERIFIED' if not errors and actual==set(expected) else 'INCOMPLETE',
        missing_top_level=sorted(set(expected)-actual),errors=errors,class_count=len(result['classes']),
        complete=not errors and actual==set(expected))
    return result


def analyze(root):
    root=Path(root);cap=root/'capture';run=json.loads((root/'execution.json').read_text())
    def read(n):
        p=cap/n
        return p.read_text(errors='replace') if p.is_file() else None
    stdout=read('maven.stdout');stderr=read('maven.stderr');combined=(stdout or '')+'\n'+(stderr or '')
    launched=bool(stdout and re.search(r'Scanning for projects|Building Apache Commons CLI|\[INFO\] ---',stdout))
    maven_exit=int(read('maven.exit')) if read('maven.exit') is not None else None
    order=[]
    for line in (stdout or '').splitlines():
        m=re.search(r'--- ([^: ]+):([^: ]+):([^ ]+) \(([^)]+)\) @ ([^ ]+) ---',line)
        if m:order.append(dict(prefix=m[1],version=m[2],goal=m[3],execution=m[4],project=m[5]))
    error_lines=[x for x in combined.splitlines() if x.startswith('[ERROR]')]
    missing=[];seen=set()
    for line in combined.splitlines():
        if not re.search(r'not be resolved|not been downloaded|offline|Could not find artifact',line,re.I):continue
        for m in re.finditer(r'(?<![\w.-])([\w.-]+):([\w.-]+):(pom|jar|test-jar|maven-plugin):(?:([\w.-]+):)?([\w.-]+)',line):
            group,artifact,kind,classifier,version=m.groups();classifier=classifier or ''
            try:path=relative_path(group,artifact,version,'pom' if kind=='pom' else 'jar',classifier)
            except ValueError:continue
            if path in seen:continue
            seen.add(path);present=(root/'inputs/repository'/path).is_file()
            missing.append(dict(group=group,artifact=artifact,type=kind,classifier=classifier,version=version,path=path,
                seed_bytes_present=present,disposition='CACHED_REFERENCE_IN_ERROR_CHAIN' if present else 'ABSENT_FROM_REGISTERED_CACHE',evidence=line[:2000]))
    absent=[x for x in missing if not x['seed_bytes_present']]
    missing_poms=[]
    for line in combined.splitlines():
        m=re.search(r'The POM for ([\w.-]+):([\w.-]+):jar:([\w.-]+) is missing',line)
        if m:
            group,artifact,version=m.groups();path=relative_path(group,artifact,version,'pom')
            present=(root/'inputs/repository'/path).is_file()
            row=dict(group=group,artifact=artifact,type='pom',classifier='',version=version,path=path,
                seed_bytes_present=present,disposition='MISSING_DESCRIPTOR_WARNING',evidence=line)
            if not present:missing_poms.append(row)
    source_ok=read('source.verify.exit')=='0\n'
    q=json.loads((b.E0/'prerequisites.json').read_text());seed={x['path']:x['sha256'] for x in q['artifact_records']}
    cache_after={}
    for line in (read('cache.post.sha256') or '').splitlines():
        digest,name=line.split('  ',1);cache_after[name.removeprefix('/runtime-repository/')]=digest
    cache=dict(assessment='OBSERVED' if read('cache.post.sha256') is not None else 'UNAVAILABLE',
        seed_artifacts_unchanged=bool(cache_after) and all(cache_after.get(k)==v for k,v in seed.items()),
        missing_or_changed_seed_artifacts=sorted(k for k,v in seed.items() if cache_after.get(k)!=v) if cache_after else [],
        added_metadata=[dict(path=k,sha256=v) for k,v in sorted(cache_after.items()) if k not in seed])
    logs=dict(stdout_bytes=(cap/'maven.stdout').stat().st_size if stdout is not None else None,
              stderr_bytes=(cap/'maven.stderr').stat().st_size if stderr is not None else None)
    logs['complete']=all(v is not None and v<8*1024**2 for v in logs.values())
    try:classes=class_manifest(root)
    except Exception as exc:classes=dict(status='INVALID_OR_UNAVAILABLE',complete=False,error=str(exc))
    if classes.get('status')=='NOT_PRODUCED' and read('source.post.sha256') is not None:
        observed=[line.split('  ',1)[1] for line in read('source.post.sha256').splitlines() if line.endswith('.class')]
        classes['post_build_class_paths']=observed
        classes['class_count']=0 if not observed else None
        classes['absence_verified_from_complete_post_build_inventory']=not observed
    state=run.get('terminal_state',{});oom=state.get('OOMKilled') is True
    unapproved=[x for x in order if x['goal'] in ('testCompile','test','package','install','deploy','site')]
    if run.get('substatus')=='BLOCKED_RESOURCES':status='BLOCKED_BUILD_OR_RESOURCE'
    elif oom or maven_exit in (124,137,143):status='BLOCKED_BUILD_OR_RESOURCE'
    elif read('setup.complete')!='true\n':status='BLOCKED_BUILD_OR_RESOURCE'
    elif not launched or maven_exit is None:status='PARTIAL'
    elif maven_exit==0:
        status='COMPILE_PASS' if (classes['complete'] and source_ok and cache['seed_artifacts_unchanged']
            and not unapproved and not (cap/'test-classes.present').exists() and logs['complete']
            and state.get('ExitCode')==0 and any(x['prefix']=='compiler' and x['goal']=='compile' for x in order)) else 'PARTIAL'
    elif absent and re.search(r'not be resolved|not been downloaded|Could not find artifact',combined,re.I):status='BLOCKED_DEPENDENCY'
    elif re.search(r'not a git repository|\.git.*(?:missing|not found)|SCM.*(?:failed|failure)',combined,re.I):status='BLOCKED_SCM_CONTEXT'
    else:status='BLOCKED_BUILD_OR_RESOURCE'
    result=dict(status=status,version='e02-result-v1',maven_actually_launched=launched,maven_exit=maven_exit,
        docker_exit=state.get('ExitCode'),setup_complete=read('setup.complete')=='true\n',actual_plugin_order=order,
        first_error=error_lines[0] if error_lines else None,error_excerpt=error_lines[:12],
        runtime_dependency_references=missing,missing_artifacts=absent+missing_poms,
        missing_jars=absent,missing_pom_descriptors=missing_poms,cache_changes=cache,logs=logs,
        tracked_source_hashes_unchanged=source_ok,classes=classes,unapproved_phase_evidence=unapproved,
        test_classes_present=(cap/'test-classes.present').exists(),oom_killed=oom,
        cgroup_peak_memory_bytes=int(read('memory.peak')) if read('memory.peak') else None,
        maven_duration_seconds=(float(read('maven.ended.uptime'))-float(read('maven.started.uptime')))
                               if read('maven.ended.uptime') and read('maven.started.uptime') else None,
        actual_scm_lines=[x for x in combined.splitlines() if re.search(r'git repository|SCM|buildnumber|buildNumber',x)][:15],
        compiler_classpath='NOT_REACHED' if not any(x['prefix']=='compiler' for x in order) else 'See actual compiler logs/output manifest',
        cleanup_complete=run['cleanup_complete'],retry_performed=False)
    b.write(root/'result.json',result)
    return result
