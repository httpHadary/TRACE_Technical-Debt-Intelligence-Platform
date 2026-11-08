"""E.4.1: one offline T+60 compile against the independently verified753-file cache.

No acquisition or retry mode. Archived adapters and smoke records stay unchanged.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import time
import tarfile
import uuid
from tools import build_sandbox as b
from tools import build_compile_e02 as prior
from tools.recover_phase5_2_2_d import git
from tools.maven_recovery.acquisition import relative_path

BASE='93ed9d27f38800fd3064d3c28b4b9490c979ac01'
LABEL='techdebt360.phase522e41'
MODE='--e41-offline-compile'
MEMORY=2*1024**3
OPTIONS=prior.OPTIONS
ALLOWED=prior.ALLOWED|{'source.modes.before','source.modes.after','repository-usage.before.txt','repository-usage.after.txt'}
RESEARCH=Path('/home/hp/tst/research/forecasting_mvp')
RECOVERY=RESEARCH/'phase5_2_2_e_4/2026-10-19/recovery-1'
MANIFEST='396219aa616a8724f4a1d00285e04b4ad4f19bc8921e67e0ef6bc79c69c474d7'
CACHE_ID='ce62e9b970dfeeaf397f8ec67774c4c4d2a16a216d89075023e1ac944477a2cf'
COMMIT='aad30eff27ac5c9a13194125226653c6c2826c58'
TREE='d7434665397c8dd8156fff7ecaed29a14feeb951'
POM='1c82171f91da0f4aa2994bb367e4c9ef8e65414940100be081715605739d9e0b'
SOURCE_MANIFEST='e7e7286b86b9c1f22935b9e142abc2343243b482b52e823d9a2640ee76a2d016'
SETTINGS='3d40c2cbbd0003df1f8e4be9ac970f77c9446c03235aab00c6ef738b4701c200'
SOURCE=RESEARCH/'phase5_2_2_e_4/2026-10-19/source'
REPOSITORY_CAP=128*1024**2
METADATA_RESERVE=16*1024**2
TASK=RESEARCH/'phase5_2_2_e_4_1/2026-10-19'
maven_command=prior.maven_command
parse_class=prior.parse_class


def class_manifest(root):
    root=Path(root);expected={};package_info=[]
    for p in (root/'inputs/source/src/main').rglob('*.java'):
        text=p.read_text();match=re.search(r'^\s*package\s+([\w.]+)\s*;',text,re.M)
        if not match:raise ValueError('Production source package unavailable')
        name=match[1].replace('.','/')+'/'+p.stem
        if p.name=='package-info.java':package_info.append(name)
        else:
            stripped=re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
            if not re.search(r'\b(?:class|interface|enum|@interface)\s+'+re.escape(p.stem)+r'\b',stripped):
                raise ValueError('Top-level source declaration mismatch')
            expected[name]=p.name
    result=dict(status='NOT_PRODUCED',expected_top_level=sorted(expected),expected_top_level_count=len(expected),
        package_info_sources=package_info,classes=[],resources=[],missing_top_level=sorted(expected),complete=False)
    archive=root/'capture/classes.tar'
    if not archive.exists():return result
    seen=set();total=0;errors=[]
    with tarfile.open(archive,'r:') as tar:
        for member in tar:
            if member.isdir():continue
            name=member.name.removeprefix('./');p=PurePosixPath(name)
            if (not member.isfile() or p.is_absolute() or '..' in p.parts or '\\' in name
                or name in seen or member.size>8*1024**2 or len(seen)>=1024):
                raise ValueError('Unsafe class archive')
            total+=member.size
            if total>32*1024**2:raise ValueError('Class archive expansion cap')
            seen.add(name)
            with tar.extractfile(member) as stream:raw=stream.read()
            if not name.endswith('.class'):
                result['resources'].append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
                continue
            parsed=parse_class(raw)
            if parsed['internal_name']+'.class'!=name:raise ValueError('Class identity/path mismatch')
            owner=parsed['internal_name'].split('$',1)[0]
            kind='top_level' if parsed['internal_name'] in expected else ('package_info' if parsed['internal_name'] in package_info else 'nested')
            if (kind=='package_info' and parsed['source_file']!='package-info.java') or (kind!='package_info' and (owner not in expected or parsed['source_file']!=expected[owner])):
                errors.append(dict(path=name,reason='SourceFile/production identity mismatch'))
            if kind=='nested' and re.match(r'^[0-9]',parsed['internal_name'].split('$',1)[1]):kind='anonymous'
            result['classes'].append(dict(path=name,kind=kind,bytes=len(raw),sha256=__import__('hashlib').sha256(raw).hexdigest(),**parsed))
    actual={x['internal_name'] for x in result['classes'] if x['kind']=='top_level'}
    result.update(status='VERIFIED' if not errors and actual==set(expected) else 'INCOMPLETE',
        missing_top_level=sorted(set(expected)-actual),errors=errors,class_count=len(result['classes']),
        complete=not errors and actual==set(expected))
    return result



def wrapper_script():
    script=prior.wrapper_script()
    changes={'--e02-offline-compile':MODE,'explicit_e02_compile':'explicit_e41_compile',
             '# E.0.2 allowlisted':'# E.4.1 allowlisted',
             '[ "$(find /source -type f | wc -l)" -eq 117 ]':
             '[ "$(find /source -type f | wc -l)" -eq 138 ]',
             '[ "$(find /runtime-repository -type f | wc -l)" -eq 653 ]':
             '[ "$(find /runtime-repository -type f | wc -l)" -eq 753 ]'}
    for before,after in changes.items():
        if script.count(before)!=1:raise ValueError('Pinned setup recipe changed')
        script=script.replace(before,after)
    anchor="printf 'true\\n' > \"$OUT/setup.complete\""
    if script.count(anchor)!=1:raise ValueError('Setup capture anchor changed')
    script=script.replace(anchor,"find /source -type f -printf '%m %P\\n' | sort > \"$OUT/source.modes.before\"\n"+anchor)
    post='    if [ -f \"$OUT/maven.exit\" ]; then'
    if script.count(post)!=1:raise ValueError('Post-capture anchor changed')
    script=script.replace(post,post+"\n        find /source -type f -printf '%m %P\\n' | sort > \"$OUT/source.modes.after\"",1)
    usage='df -B1 /runtime-repository; du -s -B1 /runtime-repository; stat -f -c "block_size=%S blocks=%b free_blocks=%f available_blocks=%a files=%c free_files=%d" /runtime-repository'
    script=script.replace(anchor,'{ '+usage+'; } > "$OUT/repository-usage.before.txt"\n'+anchor)
    script=script.replace(post,post+'\n        { '+usage+'; } > "$OUT/repository-usage.after.txt"',1)
    return script


def production_inputs(sources):
    paths=sorted(r['path'] for r in sources if r['path'].startswith('src/main/') and r['path'].endswith('.java'))
    if len(paths)!=36 or len(set(paths))!=36 or sum('/cli/help/' in p for p in paths)!=10:
        raise ValueError('Exact36-source population including10 help-package files required')
    return paths


def capacity(rows):
    directories={str(parent) for row in rows for parent in PurePosixPath(row['path']).parents}
    rounded=sum(((r['bytes']+4095)//4096)*4096 for r in rows)
    estimated=rounded+len(directories)*4096+METADATA_RESERVE
    if estimated>REPOSITORY_CAP:raise ValueError('753 artifacts plus metadata do not fit128MiB tmpfs')
    return dict(payload_bytes=sum(r['bytes'] for r in rows),rounded_file_bytes=rounded,
        estimated_directory_bytes=len(directories)*4096,metadata_reserve_bytes=METADATA_RESERVE,
        estimated_total_bytes=estimated,repository_tmpfs_bytes=REPOSITORY_CAP,
        estimate='4KiB allocation blocks/directories plus16MiB metadata reserve; kernel tmpfs cap remains authoritative')


def verify_cache(base):
    published=base/'examples/phase5_2_2_e_4/dependency_manifest.json'
    if b.sha(RECOVERY/'dependency_manifest.json')!=MANIFEST or b.sha(published)!=MANIFEST:
        raise ValueError('Frozen E.4 manifest identity mismatch')
    manifest=json.loads(published.read_text())
    if len(manifest['artifacts'])!=753 or manifest['requests']!=8:
        raise ValueError('Frozen E.4 inventory/ledger changed')
    records=b.verify_rows(RECOVERY,manifest)
    identity=''.join(f"{row['sha256']}  {row['bytes']}  {name}\n" for name,row in sorted(records.items()))
    if hashlib.sha256(identity.encode()).hexdigest()!=CACHE_ID:raise ValueError('Canonical753-artifact identity mismatch')
    actual={str(p.relative_to(RECOVERY/'repository')) for p in (RECOVERY/'repository').rglob('*') if p.is_file()}
    if actual!=set(records):raise ValueError('Unregistered recovery-cache files')
    return manifest,records


def registered_lifecycle(base,repository):
    """Derive compile-bound identities from T+60 metadata and verified descriptors.

    This is a static allowlist, not evidence that any goal executed. Order is
    constrained by phase; same-phase execution order is observed, not borrowed.
    """
    import zipfile
    from tools.maven_recovery.acquisition import parse_xml
    phases=['validate','initialize','generate-sources','process-sources','generate-resources','process-resources','compile']
    matrix=json.loads((Path(base)/'examples/phase5_2_2_e_4/buildplan_descriptor_verification.json').read_text())
    result=[]
    for plugin in matrix['plugins']:
        g,a,v=plugin['gav'];path=Path(repository)/relative_path(g,a,v,'jar')
        if b.sha(path)!=plugin['jar_sha256']:raise ValueError('Target descriptor JAR changed')
        with zipfile.ZipFile(path) as jar:raw=jar.read('META-INF/maven/plugin.xml')
        if hashlib.sha256(raw).hexdigest()!=plugin['descriptor_sha256']:raise ValueError('Target descriptor changed')
        xml=parse_xml(raw)
        if [xml.findtext(k) for k in ('groupId','artifactId','version')]!=plugin['gav']:raise ValueError('Descriptor GAV changed')
        prefix=xml.findtext('goalPrefix')
        candidates=list(plugin['configured_executions'])+[dict(phase=phase,goal=goal,id='default-'+goal) for phase,goal in plugin['default_bindings']]
        for candidate in candidates:
            if candidate['phase'] not in phases:continue
            row=dict(prefix=prefix,version=v,goal=candidate['goal'],execution=candidate['id'],phase=candidate['phase'],gav=plugin['gav'])
            if row not in result:result.append(row)
    return sorted(result,key=lambda row:phases.index(row['phase']))


def lifecycle_matches(order,expected):
    from collections import Counter
    keys=('prefix','version','goal','execution')
    identity=lambda row:tuple(row[k] for k in keys)
    if Counter(map(identity,order))!=Counter(map(identity,expected)) or any(row['project']!='commons-cli' for row in order):return False
    phase={identity(row):['validate','initialize','generate-sources','process-sources','generate-resources','process-resources','compile'].index(row['phase']) for row in expected}
    ranks=[phase[identity(row)] for row in order]
    return ranks==sorted(ranks)


def prepare(base,root):
    base,root=Path(base),Path(root).absolute()
    protected=[RESEARCH/name for name in ('phase5_2_2_d','phase5_2_2_d_1','phase5_2_2_d_2','phase5_2_2_d_3',
        'phase5_2_2_e_0','phase5_2_2_e_0_1','phase5_2_2_e_0_2','phase5_2_2_e_0_3',
        'phase5_2_2_e_0_4','phase5_2_2_e_0_5','phase5_2_2_e_0_5_1','phase5_2_2_e_0_6','phase5_2_2_e_1','phase5_2_2_e_1_1','phase5_2_2_e_2','phase5_2_2_e_2_1','phase5_2_2_e_3','phase5_2_2_e_3_1','phase5_2_2_e_4')]
    protected += [Path('/home/hp/.m2'),Path('/home/hp/tst/td360_v3_real_operator_v0100/workspace/m2-cache')]
    if (any(p.is_symlink() or (p/'.git').exists() for p in (root,*root.parents))
        or any(root.is_relative_to(p) or p.is_relative_to(root) for p in protected)):
        raise ValueError('Fresh independent output outside Git/previous tasks/user caches required')
    if root!=TASK/'attempt-1' or root.resolve()!=root:
        raise ValueError('Exclusive E.4.1 task path required')
    owner=json.loads((TASK/'owner.json').read_text())
    if owner!=dict(phase='E.4.1',base=BASE,exclusive_root=str(TASK)):
        raise ValueError('E.4.1 task ownership mismatch')
    manifest,records=verify_cache(base)
    budget=capacity(list(records.values()))
    source_authority=base/'examples/phase5_2_2_e_4/source_manifest.json'
    if b.sha(source_authority)!=SOURCE_MANIFEST or b.sha(SOURCE.parent/'source_manifest.json')!=SOURCE_MANIFEST:
        raise ValueError('Frozen T+60 source authority changed')
    q=json.loads(source_authority.read_text())
    if (q['commit'],q['tree'],q['pom_sha256'],q['actual_effective_model_sha256'])!=(COMMIT,TREE,POM,None) or len(q['source_entries'])!=138:
        raise ValueError('Frozen T+60 source identity mismatch')
    config=json.loads((base/'examples/phase5_2/replay_sources.example.json').read_text())
    repo=next(x['path'] for x in config if x['repository_id']=='apache/commons-cli')
    for kind,oid in [('commit',COMMIT),('tree',TREE)]:
        raw=git(repo,'cat-file',kind,oid)
        if hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=oid:raise ValueError('Frozen Git object mismatch')
    if git(repo,'rev-parse',COMMIT+'^{tree}').decode().strip()!=TREE:raise ValueError('T+60 tree mismatch')
    actual={}
    for row in git(repo,'ls-tree','-r','-z',COMMIT).split(b'\0'):
        if row:
            head,name=row.split(b'\t');mode,kind,oid=head.decode().split();actual[name.decode()]=(mode,kind,oid)
    if actual!={x['path']:(x['mode'],'blob',x['git_blob']) for x in q['source_entries']}:raise ValueError('T+60 full Git inventory mismatch')
    # Shared tool settings only: no T0 model/profile assertions are transferred.
    settings=RESEARCH/'phase5_2_2_d_3/2026-10-16/inspection/settings.xml'
    if b.sha(settings)!=SETTINGS:raise ValueError('Isolated settings changed')
    lifecycle=registered_lifecycle(base,RECOVERY/'repository')
    root.mkdir(parents=True,exist_ok=False,mode=0o700)
    inputs=root/'inputs';inspection=root/'inspection';inspection.mkdir();inputs.mkdir()
    for kind,rows,source in [('source',q['source_entries'],SOURCE),('repository',list(records.values()),RECOVERY/'repository')]:
        for row in rows:
            name=row['path'];p=PurePosixPath(name);src=source/name
            if p.is_absolute() or '..' in p.parts or '\\' in name or '\n' in name:raise ValueError('Unsafe seed path')
            if any(v.is_symlink() for v in (src,*src.parents)) or b.sha(src)!=row['sha256']:raise ValueError('Seed integrity mismatch')
            if kind=='source':
                if src.stat().st_mode & 0o777!=(0o555 if row['mode']=='100755' else 0o444):
                    raise ValueError('Frozen source executable mode changed')
                raw=src.read_bytes()
                if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=row['git_blob']:raise ValueError('Source Git blob mismatch')
            dst=inputs/kind/name;dst.parent.mkdir(parents=True,exist_ok=True)
            with src.open('rb') as left,dst.open('xb') as right:shutil.copyfileobj(left,right,65536)
            if b.sha(dst)!=row['sha256'] or dst.stat().st_ino==src.stat().st_ino:raise ValueError('Independent copy mismatch')
            dst.chmod(0o555 if row.get('mode')=='100755' else 0o444)
        filename='source.sha256' if kind=='source' else 'cache.sha256'
        (inspection/filename).write_text(''.join(x['sha256']+'  '+x['path']+'\n' for x in sorted(rows,key=lambda r:r['path'])))
    if b.sha(inputs/'source/pom.xml')!=POM:raise ValueError('Historical POM mismatch')
    shutil.copyfile(settings,inspection/'settings.xml')
    (inspection/'wrapper.sh').write_text(wrapper_script())
    b.write(root/'artifact_seed_manifest.json',manifest)
    b.write(root/'source_seed_manifest.json',dict(entries=q['source_entries']))
    b.write(root/'compile_registration.json',dict(version='e41-offline-compile-v1',base_commit=BASE,
        mode=MODE,commit=COMMIT,tree=TREE,pom_sha256=POM,effective_pom_sha256=None,parent_version='78',apache_parent_version='33',source_manifest_sha256=SOURCE_MANIFEST,
        lifecycle=lifecycle,production_java_sources=production_inputs(q['source_entries']),actual_active_profiles='UNAVAILABLE_NOT_ENUMERATED_BY_COMPILE',
        source_files=138,artifacts=753,seed_manifest_sha256=MANIFEST,cache_identity_sha256=CACHE_ID,
        command=maven_command(),image=b.IMAGE,settings_sha256=SETTINGS,explicit_profiles=[],
        memory_bytes=MEMORY,heap_max_bytes=768*1024**2,cpus=1,pids=64,swap_bytes=0,
        setup_template_sha256=b.sha(Path(b.__file__).with_name('build_sandbox_setup.sh')),
        executed_wrapper_sha256=b.sha(inspection/'wrapper.sh'),capacity=budget,maximum_attempts=1,downloads=0))
    return dict(status='INPUTS_VERIFIED',artifacts=753,source_files=138,independent_copies=True,capacity=budget)


def verify_prepared(root):
    root=Path(root);q=json.loads((root/'compile_registration.json').read_text())
    if (q['version']!='e41-offline-compile-v1' or q['mode']!=MODE or q['command']!=maven_command()
        or (q['commit'],q['tree'],q['pom_sha256'],q['effective_pom_sha256'])!=(COMMIT,TREE,POM,None)
        or (q['image'],q['memory_bytes'],q['heap_max_bytes'],q['maximum_attempts'])!=(b.IMAGE,MEMORY,768*1024**2,1)
        or q['artifacts']!=753 or q['source_files']!=138 or q['executed_wrapper_sha256']!=b.sha(root/'inspection/wrapper.sh')
        or q['executed_wrapper_sha256']!=hashlib.sha256(wrapper_script().encode()).hexdigest()
        or q['seed_manifest_sha256']!=MANIFEST or b.sha(root/'artifact_seed_manifest.json')!=MANIFEST
        or q['settings_sha256']!='3d40c2cbbd0003df1f8e4be9ac970f77c9446c03235aab00c6ef738b4701c200'
        or q['settings_sha256']!=b.sha(root/'inspection/settings.xml')):raise ValueError('Prepared registration changed')
    if q['parent_version']!='78' or q['apache_parent_version']!='33' or q['source_manifest_sha256']!=SOURCE_MANIFEST or b.sha(SOURCE.parent/'source_manifest.json')!=SOURCE_MANIFEST:
        raise ValueError('Target source/parent identity changed')
    if q['lifecycle']!=registered_lifecycle(Path(__file__).resolve().parents[1],root/'inputs/repository'):
        raise ValueError('Target lifecycle registration changed')
    rows=json.loads((root/'artifact_seed_manifest.json').read_text())['artifacts']
    sources=json.loads((root/'source_seed_manifest.json').read_text())['entries']
    if sources!=json.loads((SOURCE.parent/'source_manifest.json').read_text())['source_entries']:raise ValueError('Source manifest changed')
    if q['production_java_sources']!=production_inputs(sources):raise ValueError('Compiler input registration changed')
    for kind,entries in [('repository',rows),('source',json.loads((root/'source_seed_manifest.json').read_text())['entries'])]:
        if len(entries)!=(753 if kind=='repository' else 138):raise ValueError('Seed population mismatch')
        directory=root/'inputs'/kind
        if {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}!={r['path'] for r in entries}:raise ValueError('Extra or missing input files')
        for row in entries:
            p=directory/row['path']
            if any(v.is_symlink() for v in (p,*p.parents)) or b.sha(p)!=row['sha256']:raise ValueError('Prepared seed changed')
            if kind=='source' and (p.stat().st_mode & 0o777)!=(0o555 if row['mode']=='100755' else 0o444):
                raise ValueError('Prepared source mode changed')
        expected=''.join(x['sha256']+'  '+x['path']+'\n' for x in sorted(entries,key=lambda x:x['path']))
        if (root/'inspection'/('cache.sha256' if kind=='repository' else 'source.sha256')).read_text()!=expected:
            raise ValueError('Container verification manifest changed')
    return capacity(rows)


def admission(root):
    evidence=b.admission()
    if evidence['available_ram_bytes']<4*1024**3:raise RuntimeError('BLOCKED_RESOURCES: less than4GiB available RAM')
    evidence.update(required_available_bytes=4*1024**3,container_budget_bytes=MEMORY,headroom_bytes=2*1024**3,
        repository_capacity=capacity(json.loads((Path(root)/'artifact_seed_manifest.json').read_text())['artifacts']))
    return evidence


def validate_container(c,name,root):
    b.assert_owned(c,name,LABEL);h=c['HostConfig'];cfg=c['Config']
    env=dict(v.split('=',1) for v in cfg['Env'])
    required_env={'HOME':'/tmp','MAVEN_CONFIG':'/tmp/.m2','MAVEN_SKIP_RC':'true','MAVEN_ARGS':'',
        'MAVEN_OPTS':OPTIONS,'JAVA_TOOL_OPTIONS':'','JDK_JAVA_OPTIONS':''}
    if any(env.get(k)!=v for k,v in required_env.items()):raise ValueError('E.4.1 environment mismatch')
    if (c['Image']!=b.IMAGE or cfg['User']!='1000:1000' or cfg['Cmd']!=['/inspection/wrapper.sh','--e41-offline-compile']
        or cfg['Entrypoint']!=['/bin/sh'] or cfg['WorkingDir']!='/source' or env.get('MAVEN_OPTS')!=OPTIONS
        or h['Memory']!=MEMORY or h['MemorySwap']!=MEMORY or h['NanoCpus']!=1000000000 or h['PidsLimit']!=64
        or h['ShmSize']!=8388608 or h['NetworkMode']!='none' or not h['ReadonlyRootfs'] or h['Privileged'] or h.get('CapAdd')
        or 'ALL' not in h['CapDrop'] or 'no-new-privileges' not in h['SecurityOpt'] or h['Tmpfs']!=b.tmpfs_options()):
        raise ValueError('E.4.1 isolation or command mismatch')
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
    with (root/'attempt_claim.json').open('x') as f:json.dump(dict(mode='E41_OFFLINE_COMPILE',maximum_attempts=1),f)
    result=dict(status='BLOCKED_BUILD_OR_RESOURCE',capture=dict(captured=False),errors=[],cleanup_complete=False,
        attempts=1,command=maven_command(),maven_environment={'MAVEN_OPTS':OPTIONS},mode='E41_OFFLINE_COMPILE')
    try:verify_prepared(root)
    except Exception as exc:
        result['errors'].append(dict(kind='INPUT_INTEGRITY',detail=str(exc)))
        b.write(root/'execution.json',result);return result
    try:resource=admission(root)
    except Exception as exc:
        result['substatus']='BLOCKED_RESOURCES';result['errors'].append(dict(kind='RESOURCE_ADMISSION',detail=str(exc)))
        b.write(root/'execution.json',result);return result
    b.write(root/'resource_admission.json',resource)
    (root/'capture').mkdir(exist_ok=False)
    name='td522e41-'+uuid.uuid4().hex[:12];created=False;created_at=time.time()
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
    cmd += [b.IMAGE,'/inspection/wrapper.sh','--e41-offline-compile'];result['create_command']=cmd
    try:
        if json.loads(b.docker('image','inspect',b.IMAGE))[0]['Id']!=b.IMAGE:raise ValueError('Pinned image missing')
        result['container_id']=b.docker(*cmd).decode().strip();created=True
        c=b.inspect(name);validate_container(c,name,root);b.write(root/'inspect.before.private.json',c)
        checks=[];reference=json.loads((Path(__file__).resolve().parents[1]/'examples/phase5_2_2_b/runtime_evidence.json').read_text())
        for path in ('usr/share/maven/bin/mvn','usr/share/maven/lib/maven-core-3.9.11.jar','opt/java/openjdk/bin/java','opt/java/openjdk/release'):
            dst=root/Path(path).name;b.docker('cp',name+':/'+path,str(dst));value=b.sha(dst);dst.unlink()
            if not any(v['path']==path and v['sha256']==value for v in reference['artifact_checks']):raise ValueError('Pinned binary mismatch')
            checks.append(dict(path=path,sha256=value))
        result['binary_checks']=checks;result['admission_immediately_before_start']=admission(root)
        b.docker('start',name);started=time.monotonic()
        while True:
            c=b.inspect(name);result['minimum_host_available_bytes']=min(result['minimum_host_available_bytes'],b.host_available())
            if result['minimum_host_available_bytes']<2*1024**3:raise RuntimeError('Host2GiB headroom violation')
            if not c['State']['Running']:break
            if not result['capture']['captured']:
                captured=collector(name,root/'capture')
                if captured.get('race'):result['errors'].append(dict(kind='EXEC_RACE',detail=captured.get('error')))
                if captured['captured']:result['capture']=captured
            if time.monotonic()-started>265:raise TimeoutError('E41 outer monitor timeout')
            time.sleep(0.25)
        result['host_execution_seconds']=time.monotonic()-started
    except Exception as exc:result['errors'].append(dict(kind=type(exc).__name__,detail=str(exc)[:1500]))
    finally:
        if created:b.retain_terminal_evidence(name,result['container_id'],created_at,root,result,owner_label=LABEL,collector=collector)
        b.write(root/'execution.json',result)
    return result



def finalize_evidence(root,result,run):
    cap=root/'capture'
    required={'setup.stdout','setup.stderr','setup.complete','passed-stages.txt','stage.txt','command-category.txt',
        'exit.code','maven.stdout','maven.stderr','maven.exit','memory.peak','memory.events','cpu.stat',
        'cgroup.limits.txt','repository-usage.before.txt','repository-usage.after.txt','source.verify.exit','source.post.sha256','cache.post.sha256','post-capture.complete'}
    missing=sorted(n for n in required if not (cap/n).is_file())
    checks=dict(required_capture_available=not missing,logs_complete=result['logs']['complete'],
        source_hashes=result['tracked_source_hashes_unchanged'],all753_artifacts_unchanged=result['cache_changes']['seed_artifacts_unchanged'],
        cleanup=run['cleanup_complete'],docker_logs=run.get('docker_logs',{}).get('exit_code')==0,
        no_oom=run.get('terminal_state',{}).get('OOMKilled') is False,
        one_start=sum(x['action']=='start' for x in run.get('events',[]))==1,
        terminal_exits_agree=result['maven_exit'] is not None and result['maven_exit']==result['docker_exit'],
        no_unexpected_controller_errors=not any(x['kind']!='EXEC_RACE' for x in run['errors']))
    plugin_failure=any(x in (result['first_error'] or '') for x in ('Plugin ','plugin ','could not be resolved'))
    plugin_failure=plugin_failure or bool(re.search(r'PluginResolutionException|PluginContainerException', (cap/'maven.stdout').read_text(errors='replace') if (cap/'maven.stdout').exists() else ''))
    for row in result['missing_artifacts']:
        if row.get('disposition')=='MISSING_DESCRIPTOR_WARNING':
            from tools.verify_compile_e06 import warning_context
            stdout=(cap/'maven.stdout').read_text(errors='replace') if (cap/'maven.stdout').exists() else ''
            observed=next((w for w in warning_context(stdout) if w['gav']==[row['group'],row['artifact'],row['version']]),None)
            row.update(fatal=False,dependency_domain=observed['dependency_domain'] if observed else 'UNKNOWN',
                observed_during=observed['observed_during'] if observed else None)
        else:row.update(fatal=True,dependency_domain='PLUGIN_RUNTIME_OR_PLUGIN_ARTIFACT' if plugin_failure else 'PROJECT_DEPENDENCY')
    if result['status']=='COMPILE_PASS' and not all(checks.values()):result['status']='PARTIAL'
    result.update(evidence_completeness=dict(checks=checks,unavailable=missing,complete=all(checks.values())),
        expected_seed_count=753,explicit_profiles=[],profile_enumeration='UNAVAILABLE_NOT_ENUMERATED_BY_REGISTERED_COMPILE',actual_effective_pom_sha256=None,downloads=0)
    b.write(root/'result.json',result)
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
    q=json.loads((root/'artifact_seed_manifest.json').read_text());seed={x['path']:x['sha256'] for x in q['artifacts']}
    if len(seed)!=753:raise ValueError('E.4.1 requires exactly753 admitted artifacts')
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
            and lifecycle_matches(order,json.loads((root/'compile_registration.json').read_text())['lifecycle'])
            and state.get('ExitCode')==0 and any(x['prefix']=='compiler' and x['goal']=='compile' for x in order)) else 'PARTIAL'
    elif absent and re.search(r'not be resolved|not been downloaded|Could not find artifact',combined,re.I):status='BLOCKED_DEPENDENCY'
    elif re.search(r'not a git repository|\.git.*(?:missing|not found)|SCM.*(?:failed|failure)', '\n'.join(error_lines),re.I):status='BLOCKED_SCM_CONTEXT'
    else:status='BLOCKED_BUILD_OR_RESOURCE'
    result=dict(status=status,version='e41-result-v1',maven_actually_launched=launched,maven_exit=maven_exit,
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
        compiler_classpath='NOT_REACHED' if not any(x['prefix']=='compiler' for x in order) else 'UNAVAILABLE_NOT_LOGGED_BY_REGISTERED_COMMAND',
        cleanup_complete=run['cleanup_complete'],retry_performed=False)
    return finalize_evidence(root,result,run)


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-only',action='store_true')
    mode.add_argument('--e41-offline-compile',action='store_true')
    args=parser.parse_args();b.enforce_process_limits()
    root=Path(args.root).absolute();base=Path(__file__).resolve().parents[1]
    if root!=TASK/'attempt-1' or root.resolve()!=root:raise ValueError('Wrong E.4.1 task root')
    if args.prepare_only:result=prepare(base,root)
    else:
        execution=execute_once(root)
        result=analyze(root)
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__=='__main__':main()
