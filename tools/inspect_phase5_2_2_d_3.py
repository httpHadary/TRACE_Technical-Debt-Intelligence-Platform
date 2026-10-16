"""D.3: bounded Help3.5.1 acquisition and exact T0-only offline inspection inputs.

No lifecycle goals, compilation or generic dependency acquisition entry point.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import shutil
import time
import zipfile
from tools.maven_recovery.acquisition import Acquisition, BudgetExceeded, CENTRAL, parse_xml, relative_path
from tools.maven_recovery.model import Models
from tools.recover_phase5_2_2_d_2 import verify_rows, enforce_process_limits

BASE = 'fbfd7bb0fde4a367e97d4e118b8cf2a26dd93079'
COMMIT = '4ff0d4adbc2161677e71050ba23c152831f6ad83'
TREE = 'ac7521be84b2820a83f7b960d329a15521408214'
POM = 'b75fb9813e3c06121caa7d84c31a471b646465966079cf10ec4c7a2e4aba55f2'
HELPER = ('org.apache.maven.plugins', 'maven-help-plugin', '3.5.1')
IMAGE = 'sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82'
MEMORY = 1536 * 1024 * 1024
MAX_REQUESTS = 150
MAX_BYTES = 64 * 1024 * 1024
MAX_DISK = 256 * 1024 * 1024
GOALS = ('active-profiles', 'effective-pom')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def verified_seed(source, published, destination):
    source, destination = Path(source).absolute(), Path(destination).absolute()
    if source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('Runtime cache must be independent')
    if any(p.is_symlink() or (p / '.git').exists() for p in (destination, *destination.parents)):
        raise ValueError('Unsafe runtime cache')
    manifest = json.loads((source / 'dependency_manifest.json').read_text())
    if (manifest != published or len(manifest.get('artifacts', [])) != 624 or manifest.get('requests') != 52
            or manifest.get('parent_ledgers', {}).get('task_d1_requests') != 400
            or manifest.get('parent_ledgers', {}).get('task_d_requests') != 2000):
        raise ValueError('Frozen D.2 evidence mismatch')
    records = verify_rows(source, manifest)
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, row in records.items():
        src = source / 'repository' / name
        dst = destination / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        with src.open('rb') as left, dst.open('xb') as right:
            shutil.copyfileobj(left, right, 65536)
        if sha(dst) != row['sha256'] or dst.stat().st_ino == src.stat().st_ino:
            raise ValueError('Independent copy failed')
    return records


class HelperAcquisition(Acquisition):
    """One helper-only ledger; historical artifacts are verified local reads."""
    def __init__(self, root, seed, records):
        super().__init__(root)
        self.seed, self.seed_records = Path(seed), records
        self.events = []
        self.seal()

    def get(self, group, artifact, version, extension='pom', classifier=''):
        name = relative_path(group, artifact, version, extension, classifier)
        if name in self.seed_records:
            self.used_paths.add(name)
            p = self.seed / name
            if p.is_symlink() or sha(p) != self.seed_records[name]['sha256']:
                raise ValueError('Historical seed changed')
            return p.read_bytes()
        return super().get(group, artifact, version, extension, classifier)

    def fetch(self, path, limit):
        # Reuse D.2 transport invariants with this task's independent limits.
        import re
        import urllib.request
        import urllib.error
        if '..' in path or not re.fullmatch('[A-Za-z0-9_./-]+', path):
            raise ValueError('Unsafe path')
        url = CENTRAL + path
        req = urllib.request.Request(url, headers={'User-Agent': 'TechDebt360-D3-helper-only'})
        for attempt in range(1, 4):
            if self.requests >= MAX_REQUESTS or time.monotonic() - self.started > 600:
                raise BudgetExceeded('D.3 helper request/time cap')
            self.requests += 1
            self.seal()  # Count attempts even when interrupted or rejected.
            try:
                response = self.opener.open(req, timeout=15)
                break
            except urllib.error.HTTPError as exc:
                self.events.append(dict(path=path, status=exc.code)); self.seal()
                raise
            except (urllib.error.URLError, TimeoutError) as exc:
                self.transport_failures.append(dict(path=path, attempt=attempt, error=type(exc).__name__))
                self.seal()
                if attempt == 3:
                    raise
        with response:
            if response.status != 200 or response.geturl() != url:
                raise ValueError('Repository identity changed')
            cap = min(limit, MAX_BYTES - self.bytes)
            length = response.headers.get('Content-Length')
            expected = int(length) if length is not None else None
            if cap <= 0 or (expected is not None and not 0 <= expected <= cap):
                raise BudgetExceeded('D.3 helper payload cap')
            raw = bytearray()
            while expected is None or len(raw) < expected:
                if time.monotonic() - self.started > 600:
                    raise BudgetExceeded('D.3 helper time cap')
                size = min(65536, cap - len(raw))
                if size <= 0:
                    raise BudgetExceeded('Cannot establish EOF within cap')
                chunk = response.read(size)
                if not chunk:
                    if expected is not None and len(raw) != expected:
                        raise ValueError('Truncated response')
                    break
                self.bytes += len(chunk)
                raw.extend(chunk)
            self.seal()
            return bytes(raw)

    def seal(self):
        value = dict(version='task-d3-helper-acquisition-v1', repository=CENTRAL,
            helper=list(HELPER), requests=self.requests, transferred_bytes=self.bytes,
            elapsed_seconds=time.monotonic() - self.started, artifacts=list(self.records.values()),
            reused_seed_paths=sorted(self.used_paths & self.seed_records.keys()),
            http_events=self.events, transport_failures=self.transport_failures,
            limits=dict(requests=MAX_REQUESTS, response_bytes=MAX_BYTES, artifact_bytes=32*1024*1024,
                        address_space_bytes=1073741824, cpus=1, seconds=600, helper_disk_bytes=MAX_DISK),
            address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],
            cpu_affinity=sorted(os.sched_getaffinity(0)),
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            maven_executions_during_acquisition=0,
            trust='HTTPS and same-origin checksum; not independent publisher signatures')
        write(self.root / 'dependency_manifest.json', value)
        if sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file()) > MAX_DISK:
            raise BudgetExceeded('Helper cache disk cap')
        return value


def prepare_helper(a):
    """Bounded by the pinned plugin's own flattened runtime descriptor only.

    Read parent/import metadata for those exact runtime artifacts; do not walk
    arbitrary project, optional or test dependency graphs.
    """
    models = Models(a)
    models.remote(HELPER)
    raw = a.get(*HELPER, 'jar')
    with zipfile.ZipFile(io.BytesIO(raw)) as jar:
        descriptor = jar.read('META-INF/maven/plugin.xml')
        root = parse_xml(descriptor)
    if root.findtext('version') != HELPER[2]:
        raise ValueError('Helper descriptor version mismatch')
    descriptors = []
    for goal in GOALS:
        mojo = next(m for m in root.findall('mojos/mojo') if m.findtext('goal') == goal)
        if mojo.findtext('executePhase') or mojo.findtext('executeGoal') or mojo.findtext('requiresDependencyResolution'):
            raise ValueError('Helper would fork lifecycle or resolve project dependencies')
        descriptors.append(dict(goal=goal, requires_project=mojo.findtext('requiresProject'),
                                fork_phase=mojo.findtext('executePhase'), fork_goal=mojo.findtext('executeGoal')))
    dependencies = []
    for dep in root.findall('dependencies/dependency'):
        gav = tuple(dep.findtext(k) for k in ('groupId', 'artifactId', 'version'))
        if dep.findtext('type', 'jar') != 'jar':
            raise ValueError('Unsupported helper runtime type')
        models.remote(gav)
        a.get(*gav, 'jar')
        dependencies.append(list(gav))
    # Metadata issues are explicit; no broad follow-up acquisition.
    unresolved = [i for i in models.issues if i['kind'] != 'PROFILE']
    if unresolved:
        raise ValueError('Helper metadata unresolved: ' + repr(unresolved))
    result = dict(helper=list(HELPER), required_java=root.findtext('requiredJavaVersion'),
        required_maven=root.findtext('requiredMavenVersion'), goals=descriptors,
        jar_sha256=hashlib.sha256(raw).hexdigest(),
        descriptor_sha256=hashlib.sha256(descriptor).hexdigest(),
        descriptor_runtime_dependencies=dependencies, metadata_profile_unknowns=models.issues,
        scope='Pinned helper descriptor runtime plus parent/import metadata only',
        fully_resolved_project_classpath=False)
    write(a.root / 'helper_readiness.json', result)
    a.seal()
    return result


def maven_command(goal):
    if goal not in GOALS:
        raise ValueError('Only approved model goals')
    return ['/usr/share/maven/bin/mvn', '--offline', '--batch-mode', '--no-transfer-progress',
        '-s', '/inspection/settings.xml', '-gs', '/inspection/settings.xml',
        '-Dmaven.repo.local=/runtime-repository', '-Duser.home=/tmp',
        '-Dmaven.test.skip=true', '-Dmaven.compiler.release=8',
        '-Doutput=/output/' + ('active-profiles.txt' if goal == GOALS[0] else 'effective-pom.xml'),
        ':'.join(HELPER) + ':' + goal]


def materialize_source(base, output):
    """Copy every pinned tracked blob, including excluded/test/profile markers."""
    import gzip
    from tools.recover_phase5_2_2_d import git
    base, output = Path(base), Path(output)
    config = json.loads((base / 'examples/phase5_2/replay_sources.example.json').read_text())
    repo = next(r['path'] for r in config if r['repository_id'] == 'apache/commons-cli')
    if git(repo, 'rev-parse', COMMIT + '^{tree}').decode().strip() != TREE:
        raise ValueError('Pinned tree mismatch')
    reference = json.loads(gzip.decompress((base / 'examples/phase5_2_1/source_inventory.json.gz').read_bytes()))
    state = next(s for s in reference['source_states'] if s['commit_sha'] == COMMIT)
    entries = state['inventory']['entries']
    raw = git(repo, 'ls-tree', '-r', '-z', COMMIT)
    actual = []
    for item in raw.split(b'\0'):
        if item:
            head, path = item.split(b'\t'); mode, kind, oid = head.decode().split()
            actual.append((path.decode(), mode, kind, oid))
    expected = [(e['path'], e['mode'], e['object_type'], e['git_object_id']) for e in entries]
    if sorted(actual) != sorted(expected):
        raise ValueError('Registered full-source inventory mismatch')
    if any(n in dict((x[0], x) for x in actual) for n in
           ('.mvn/extensions.xml', '.mvn/maven.config', '.mvn/jvm.config')):
        raise ValueError('Unreviewed Maven execution configuration')
    output.mkdir(parents=True, exist_ok=False)
    evidence = []
    for name, mode, kind, oid in sorted(actual):
        p = Path(name)
        if kind != 'blob' or mode not in ('100644', '100755') or p.is_absolute() or '..' in p.parts:
            raise ValueError('Unsafe pinned source entry')
        data = git(repo, 'cat-file', 'blob', oid)
        computed = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if computed != oid:
            raise ValueError('Git blob identity mismatch')
        dest = output / name; dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data); dest.chmod(0o555 if mode == '100755' else 0o444)
        evidence.append(dict(path=name, git_blob=oid, sha256=sha(dest), bytes=len(data), mode=mode))
    if sha(output / 'pom.xml') != POM:
        raise ValueError('Pinned POM mismatch')
    # Empty parent-relative POM location and no .git match the registered detached
    # export context; no export-ignore filtering or convenience marker creation.
    return dict(commit_sha=COMMIT, tree_sha=TREE, pom_sha256=POM, entries=evidence,
                production_files=len(state['inventory']['production_paths']),
                scope_id=state['inventory']['scope_id'], inventory_id=state['inventory']['inventory_id'],
                git_metadata_present=False, full_tracked_population=True)


def host_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) * 1024
    raise ValueError('Host RAM evidence unavailable')


def extract_output(raw, output):
    """Bounded namespace export; Docker archive API omits these tmpfs contents."""
    import tarfile
    allowed={'start.uptime','end.uptime','maven.stdout','maven.stderr','goal.exit',
             'memory.peak','cpu.stat','memory.events','ready','active-profiles.txt','effective-pom.xml'}
    if len(raw)>2*1024*1024:
        raise ValueError('Evidence archive cap')
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
        seen=set()
        for item in archive:
            if item.name in ('.','./') and item.isdir():continue
            name=item.name.removeprefix('./')
            if name not in allowed or not item.isfile() or name in seen or item.size>1024*1024:
                raise ValueError('Unexpected output archive entry')
            seen.add(name)
            with archive.extractfile(item) as stream:
                (Path(output)/name).write_bytes(stream.read())
    if not {'goal.exit','memory.peak','memory.events','maven.stdout','maven.stderr'}<=seen:
        raise ValueError('Incomplete model evidence')


def docker(*args, timeout=20):
    import subprocess
    def small_stack():
        resource.setrlimit(resource.RLIMIT_STACK, (1048576, 1048576))
    env = dict(os.environ, GOMAXPROCS='1', GOMEMLIMIT='64MiB', MALLOC_ARENA_MAX='1')
    result = subprocess.run(['docker', *map(str, args)], capture_output=True, env=env,
                            preexec_fn=small_stack, timeout=timeout)
    if len(result.stdout) + len(result.stderr) > 2*1024*1024:
        raise ValueError('Docker response bound exceeded')
    if result.returncode:
        raise RuntimeError('Docker ' + args[0] + ': ' + result.stderr.decode(errors='replace')[:1000])
    return result.stdout


WRAPPER = '''#!/bin/sh
set -u
[ "$(cat /sys/fs/cgroup/memory.max)" = "1610612736" ] || exit 120
[ "$(cat /sys/fs/cgroup/memory.swap.max)" = "0" ] || exit 121
read quota period < /sys/fs/cgroup/cpu.max
[ "$quota" != max ] && [ "$quota" -le "$period" ] || exit 122
cut -d ' ' -f 1 /proc/uptime > /output/start.uptime
timeout --signal=TERM --kill-after=5s 180s "$@" > /output/maven.stdout 2> /output/maven.stderr
status=$?
printf '%s\\n' "$status" > /output/goal.exit
cut -d ' ' -f 1 /proc/uptime > /output/end.uptime
cat /sys/fs/cgroup/memory.peak > /output/memory.peak
cat /sys/fs/cgroup/cpu.stat > /output/cpu.stat
cat /sys/fs/cgroup/memory.events > /output/memory.events
touch /output/ready
count=0
while [ ! -f /output/collected ] && [ "$count" -lt 30 ]; do
  sleep 1
  count=$((count + 1))
done
exit "$status"
'''


def verify_container(c, name, root):
    h, cfg = c['HostConfig'], c['Config']
    if (c['Name'] != '/' + name or c['Image'] != IMAGE or cfg['User'] != '1000:1000'
            or h['NetworkMode'] != 'none' or h['Memory'] != MEMORY or h['MemorySwap'] != MEMORY
            or h['NanoCpus'] != 1000000000 or h['PidsLimit'] != 64 or not h['ReadonlyRootfs']
            or h['Privileged'] or 'ALL' not in h['CapDrop']
            or 'no-new-privileges' not in h['SecurityOpt']):
        raise ValueError('Maven sandbox isolation mismatch')
    binds = {m['Destination']: m for m in c['Mounts'] if m['Type'] == 'bind'}
    expected = {'/source': str(root/'source'), '/runtime-repository': str(root/'runtime-repository'),
                '/inspection': str(root/'inspection')}
    if set(binds) != set(expected) or any(binds[k]['RW'] or binds[k]['Source'] != v for k,v in expected.items()):
        raise ValueError('Maven sandbox mount mismatch')
    if any(m['Type'] not in ('bind', 'tmpfs') for m in c['Mounts']):
        raise ValueError('Unexpected sandbox volume')
    if not any(u['Name']=='fsize' and u['Hard']==8388608 for u in h['Ulimits']):
        raise ValueError('Missing output limit')


def run_goal(root, goal):
    """One sequential JVM, offline, immutable inputs, owned-container cleanup."""
    import uuid
    root = Path(root).absolute(); command = maven_command(goal)
    if host_available() < MEMORY + 2*1024*1024*1024:
        raise ValueError('Insufficient RAM for container plus2GiB host headroom')
    if docker('ps', '-q').strip():
        raise ValueError('Concurrent container execution requires independent resource review')
    if json.loads(docker('image', 'inspect', IMAGE))[0]['Id'] != IMAGE:
        raise ValueError('Pinned build image mismatch')
    name = 'td522d3-' + uuid.uuid4().hex[:12] + '-' + goal
    output = root / goal; output.mkdir(exist_ok=False)
    env = {'HOME':'/tmp', 'MAVEN_CONFIG':'/tmp/.m2', 'MAVEN_SKIP_RC':'true', 'MAVEN_ARGS':'',
           'MAVEN_OPTS':'-Xms32m -Xmx512m -XX:ActiveProcessorCount=1 -Duser.home=/tmp',
           'JAVA_TOOL_OPTIONS':'', 'JDK_JAVA_OPTIONS':''}
    cmd = ['create','--name',name,'--label','techdebt360.phase522d3='+name,'--pull','never',
           '--network','none','--memory',str(MEMORY),'--memory-swap',str(MEMORY),'--cpus','1',
           '--pids-limit','64','--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges',
           '--read-only','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=134217728,mode=1777',
           '--tmpfs','/output:rw,nosuid,nodev,noexec,size=33554432,mode=1777','--shm-size','8388608',
           '--ulimit','fsize=8388608:8388608','--ulimit','nofile=1024:1024',
           '--log-driver','local','--log-opt','max-size=1m','--log-opt','max-file=1',
           '--log-opt','compress=false','--workdir','/source','--entrypoint','/bin/sh']
    for key,value in env.items(): cmd += ['--env',key+'='+value]
    for src,dst in [('source','/source'),('runtime-repository','/runtime-repository'),('inspection','/inspection')]:
        cmd += ['--mount',f'type=bind,src={root/src},dst={dst},readonly']
    cmd += [IMAGE,'/inspection/wrapper.sh',*command]
    docker(*cmd)
    started = time.monotonic(); minimum_ram = host_available(); final = None
    try:
        inspect = json.loads(docker('inspect',name))[0]; verify_container(inspect,name,root)
        # Hash launchers/core/runtime directly from the never-started container.
        binary_checks=[]
        for path in ('usr/share/maven/bin/mvn','usr/share/maven/lib/maven-core-3.9.11.jar',
                     'opt/java/openjdk/bin/java','opt/java/openjdk/release'):
            target = output / Path(path).name
            docker('cp',name+':/'+path,str(target))
            binary_checks.append(dict(path=path,sha256=sha(target)))
            target.unlink()  # Keep identities, not duplicate third-party binaries.
        expected=json.loads((Path(__file__).resolve().parents[1]/'examples/phase5_2_2_b/runtime_evidence.json').read_text())
        for row in binary_checks:
            if not any(v['path']==row['path'] and v['sha256']==row['sha256'] for v in expected['artifact_checks']):
                raise ValueError('Pinned binary hash mismatch')
        docker('start',name)
        collected=False
        while True:
            final=json.loads(docker('inspect',name))[0]
            minimum_ram=min(minimum_ram,host_available())
            if minimum_ram < 2*1024*1024*1024:
                raise RuntimeError('Host2GiB headroom violated')
            if not final['State']['Running']:break
            ready=docker('exec',name,'/bin/sh','-c','if test -f /output/ready; then echo READY; fi').strip()
            if ready==b'READY' and not collected:
                extract_output(docker('exec',name,'tar','--format=ustar','-C','/output','-cf','-','.'),output)
                docker('exec',name,'/bin/sh','-c','touch /output/collected')
                collected=True
            if time.monotonic()-started>190:raise TimeoutError('Model goal outer timeout')
            time.sleep(0.5)
        if not collected:
            raise RuntimeError('Goal evidence not collected before tmpfs teardown')
        code=int((output/'goal.exit').read_text())
        if code!=final['State']['ExitCode']:
            raise ValueError('Container and Maven exit mismatch')
        result=dict(goal=goal,command=command,container=name,image=IMAGE,exit_code=code,
            container_exit_code=final['State']['ExitCode'],oom_killed=final['State']['OOMKilled'],
            host_wall_seconds=time.monotonic()-started,minimum_host_available_bytes=minimum_ram,
            cgroup_peak_memory_bytes=int((output/'memory.peak').read_text()) if (output/'memory.peak').exists() else None,
            binary_checks=binary_checks,environment=env,isolation_verified=True,
            network='none',memory_bytes=MEMORY,memory_swap_bytes=MEMORY,cpus=1,pids=64,
            heap_max_bytes=512*1024*1024,timeout_seconds=180,source_and_artifact_mounts_readonly=True,
            inspected_host_config={k:inspect['HostConfig'][k] for k in
                ('NetworkMode','Memory','MemorySwap','NanoCpus','PidsLimit','ReadonlyRootfs','CapDrop','SecurityOpt','Tmpfs','Ulimits')})
        write(output/'execution.json',result)
        return result
    finally:
        owned=json.loads(docker('inspect',name))[0]
        if owned['Config']['Labels'].get('techdebt360.phase522d3')!=name:
            raise ValueError('Container cleanup ownership mismatch')
        docker('rm','-f','-v',name)


def compare_model(base, root):
    """Reconcile only actual T0 project-model evidence; do not infer classpaths."""
    import re
    from tools.maven_recovery.model import NS, text, PHASES
    base, root = Path(base), Path(root)
    report = (root/'active-profiles/active-profiles.txt').read_text()
    active = {(source, name) for name,source in
              re.findall(r'^ - (\S+) \(source: ([^)]+)\)$', report, re.M)}
    effective = parse_xml((root/'effective-pom/effective-pom.xml').read_bytes())
    requirements = json.loads((base/'examples/phase5_2_2_d_2/requirements.json').read_text())
    static = next(s for s in requirements['states'] if s['commit_sha']==COMMIT)
    if static['tree_sha']!=TREE or static['pom_sha256']!=POM:
        raise ValueError('Static T0 identity changed')
    rows=[];chain=set()
    for record in static['profile_decisions']:
        source=':'.join(record['model']);chain.add(source)
        enabled=(source,record['id']) in active
        rows.append(dict(model=record['model'],profile_id=record['id'],
            maven_status='ACTIVE' if enabled else 'INACTIVE_IN_THIS_CONTEXT',
            static_active=record['active'],agrees=enabled is record['active']))
    expected={( ':'.join(r['model']),r['profile_id']) for r in rows if r['maven_status']=='ACTIVE'}
    if expected!=active:
        raise ValueError('Unexpected Maven profile identity')
    dependencies=[]
    for e in effective.findall('m:dependencies/m:dependency',NS):
        dependencies.append(dict(gav=[text(e,k) for k in ('groupId','artifactId','version')],
            scope=text(e,'scope','compile'),optional=text(e,'optional','false')=='true'))
    old_deps=json.loads((base/'examples/phase5_2_2_d/requirements.json').read_text())
    old_deps=next(s['declared_dependencies'] for s in old_deps['states'] if s['commit_sha']==COMMIT)
    comparison=dict(static=old_deps,maven=dependencies,
        identity_version_scope_equal=sorted((tuple(r['gav']),r['scope']) for r in old_deps)==
                                   sorted((tuple(r['gav']),r['scope']) for r in dependencies),
        final_runtime_classpaths_resolved=False)
    plugins=[]
    cached={r['path'] for r in json.loads((root/'runtime_cache_manifest.json').read_text())['artifacts']}
    for e in effective.findall('m:build/m:plugins/m:plugin',NS):
        gav=[text(e,'groupId','org.apache.maven.plugins'),text(e,'artifactId'),text(e,'version')]
        executions=[]
        for x in e.findall('m:executions/m:execution',NS):
            for g in x.findall('m:goals/m:goal',NS):
                explicit=text(x,'phase');phase=explicit;origin='EFFECTIVE_POM_EXPLICIT'
                if not phase:
                    origin='UNKNOWN_DESCRIPTOR_NOT_IN_CACHE'
                    try:p=root/'runtime-repository'/relative_path(*gav,'jar')
                    except ValueError:p=None
                    if p is not None and p.exists():
                        with zipfile.ZipFile(p) as z:desc=parse_xml(z.read('META-INF/maven/plugin.xml'))
                        mojo=next((m for m in desc.findall('mojos/mojo') if m.findtext('goal')==g.text),None)
                        if mojo is not None:
                            phase=mojo.findtext('phase');origin='CACHED_DESCRIPTOR_DEFAULT'
                executions.append(dict(id=text(x,'id','default'),goal=g.text,phase=phase,
                    phase_origin=origin,required_through_compile=phase in PHASES if phase else None,
                    executed=False))
        paths=[]
        try:paths=[relative_path(*gav,ext) for ext in ('pom','jar')]
        except ValueError:pass
        plugins.append(dict(gav=gav,executions=executions,descriptor_artifacts_present=bool(paths) and all(p in cached for p in paths),
            runtime_closure_resolved=False))
    unknown=json.loads((base/'examples/phase5_2_2_d_2/unknown_profile_evidence.json').read_text())
    unknown=[dict(r,d3_project_model_status='OUTSIDE_T0_PROJECT_INHERITANCE_CHAIN',
        actual_activation='NOT_OBSERVED_REMAINS_UNKNOWN',runtime_classpath_verification='PENDING')
        for r in unknown if ':'.join(r['model']) not in chain]
    result=dict(version='task-d3-static-versus-maven-v1',commit_sha=COMMIT,tree_sha=TREE,
        status='MODEL_VERIFIED' if all(r['agrees'] for r in rows) and comparison['identity_version_scope_equal'] else 'PARTIAL',
        effective_pom_sha256=sha(root/'effective-pom/effective-pom.xml'),
        active_profile_count=len(active),inactive_profile_count=len(rows)-len(active),
        project_profiles=rows,all_project_profile_decisions_agree=all(r['agrees'] for r in rows),
        dependency_declarations=comparison,effective_plugins=plugins,
        unresolved_transitive_profile_sources=unknown,
        literal_open_jdk_activation=dict(literal='[9',source_model=['org.apache.commons','commons-parent','58'],
            status='NOT_A_T0_PROJECT_PARENT_NOT_DIRECTLY_EVALUATED',
            actual_t0_jdk9_activation='[9,)',actual_t0_profile='jdk9+',
            no_auxiliary_project_or_goal_executed=True),
        runtime_missing_artifacts_observed=[],project_runtime_classpath='NOT_RESOLVED',
        historical_compilation='NOT_ATTEMPTED',offline_java_build_readiness='UNKNOWN')
    return result
