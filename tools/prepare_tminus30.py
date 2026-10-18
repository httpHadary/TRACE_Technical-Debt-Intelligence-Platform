"""E.1 sequential descriptor-only recovery. Never executes Maven or Java."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import time
import urllib.error
import urllib.request
import zipfile
import gzip
import copy
import xml.etree.ElementTree as ET
from tools import recover_buildplan_frontier as descriptor_tools
from tools.recover_phase5_2_2_d import git
from tools import recover_buildplan_plugin as previous
from tools import recover_compile_test_dependencies as seed
from tools.maven_recovery.acquisition import BudgetExceeded, CENTRAL, relative_path, parse_xml
from tools.maven_recovery.model import Models, NS, text, expand
from tools.recover_phase5_2_2_d_2 import verify_rows, enforce_process_limits

BASE='55ec402053952da10919faec0466a840298eb5fd'
TASK=seed.RESEARCH/'phase5_2_2_e_1/2026-10-18'
SOURCE=seed.RESEARCH/'phase5_2_2_e_0_5_1/2026-10-18/recovery-1'
MANIFEST='ed23ccde95a89081c1c19f3de39ee9199a50b15eacf0647e316f62acf1f97b84'
CACHE_ID='a84a27a2f5f9d9bed4af8dbf56a04a91b2910580f66c67952362d215f62d0b22'
TARGETS=(('org.junit.jupiter','junit-jupiter-api','5.11.0'),
 ('org.junit.jupiter','junit-jupiter-engine','5.11.0'),
 ('org.junit.jupiter','junit-jupiter-params','5.11.0'),
 ('org.apache.maven.plugins','maven-surefire-plugin','3.4.0'))
COMMIT='fb6293fcd6a9b55ac8ecb550af6572daaed18fa1'
TREE='598dec4901a9adcf8e55b241c9689a8db6219c29'
POM='2f322b0751115f2a5e93aabfb83372dc0511d57bbd8b4f178f08d5b449ff3fcf'
USER={'maven.test.skip':'true','maven.compiler.release':'8','user.home':'/tmp'}
MAX_REQUESTS,MAX_BYTES,MAX_ARTIFACT=200,64*1024**2,32*1024**2
MAX_DISK,MAX_SECONDS=256*1024**2,600
sha=seed.sha

def write(path,value):
    path=Path(path);temporary=Path(str(path)+'.tmp')
    with temporary.open('w') as stream:
        stream.write(json.dumps(value,sort_keys=True,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)
    directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)



def owned_output(root, task=TASK):
    """Validate exact phase owner before any write; no inferred or shared roots."""
    root,task=Path(root).absolute(),Path(task).absolute()
    if root!=task/'recovery-1' or root.resolve()!=root or task.resolve()!=task:
        raise ValueError('Exclusive E.1 output path required')
    if any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('Symlink task path forbidden')
    if any((p/'.git').exists() for p in (root,*root.parents)):
        raise ValueError('Task must remain outside Git')
    owner=json.loads((task/'owner.json').read_text())
    if owner!=dict(phase='E.1',base=BASE,exclusive_root=str(task)):
        raise ValueError('Task ownership mismatch')
    if root.exists():raise FileExistsError('Non-resumable exclusive acquisition claim')
    return root


def verify_seeds(base,source=SOURCE):
    published=Path(base)/'examples/phase5_2_2_e_0_5_1/dependency_manifest.json'
    if sha(published)!=MANIFEST or sha(source/'dependency_manifest.json')!=MANIFEST:
        raise ValueError('Frozen697 manifest changed')
    manifest=json.loads(published.read_text())
    if len(manifest['artifacts'])!=697 or manifest['requests']!=52:
        raise ValueError('Frozen697 population/ledger changed')
    rows=verify_rows(source,manifest)
    identity=canonical(rows)
    if identity!=CACHE_ID:raise ValueError('Canonical697 cache identity mismatch')
    paths={str(p.relative_to(source/'repository')) for p in (source/'repository').rglob('*') if p.is_file()}
    if paths!=set(rows):raise ValueError('Unregistered seed paths')
    return list(rows.values())


def canonical(rows):
    return hashlib.sha256(''.join(f"{v['sha256']}  {v['bytes']}  {k}\n" for k,v in sorted(rows.items())).encode()).hexdigest()


class Recovery(seed.Recovery):
    def __init__(self,root,source,rows,local=seed.LOCAL,task=TASK):
        target=owned_output(root,task)
        for name in ('phase5_2_2_e_0_3','phase5_2_2_e_0_4','phase5_2_2_e_0_5','phase5_2_2_e_0_5_1','phase5_2_2_e_0_6'):
            protected=seed.RESEARCH/name
            if target.is_relative_to(protected) or protected.is_relative_to(target):
                raise ValueError('Previous phase is read-only')
        self.task=Path(task).absolute();self.completed=[]
        super().__init__(target,source,rows,local=local)

    def check_budget(self):
        if self.requests>=MAX_REQUESTS or self.bytes>=MAX_BYTES or time.monotonic()-self.started>=MAX_SECONDS:
            raise BudgetExceeded('E.1 request/byte/time ceiling; no continuation authorized')

    def check_disk(self,extra=0):
        # Includes snapshots, ledgers, reports and all candidate-cache files.
        size=sum(p.stat().st_size for p in self.task.rglob('*') if p.is_file())
        if size+extra>MAX_DISK:raise BudgetExceeded('E.1 total task storage ceiling')
        return size

    def fetch(self, path, limit):
        if not self.network_enabled:
            raise ValueError('OFFLINE_MISSING: ' + path)
        if '..' in path or not re.fullmatch(r'[A-Za-z0-9_./-]+', path):
            raise ValueError('Unsafe path')
        self.check_budget()
        self.check_disk(MAX_ARTIFACT)
        # Existing bytes are only candidates. Acquisition.get still requires a
        # fresh same-origin Central checksum, coordinate checks and ZIP CRCs.
        if path.endswith(('.jar', '.pom')):
            for i, root in enumerate(self.local):
                p = root / path
                safe = not any(x.is_symlink() for x in (p, *p.parents))
                found = safe and p.is_file()
                row = dict(path=path, source_id='approved-local-' + str(i), exists=found,
                           admitted_by_filename=False)
                self.local_checks.append(row)
                if found:
                    if not 0 < p.stat().st_size <= min(limit, MAX_ARTIFACT):
                        raise ValueError('Unsafe local candidate size')
                    raw = p.read_bytes()
                    row.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                               disposition='CANDIDATE_REQUIRES_FRESH_CENTRAL_CHECKSUM')
                    self.origins[path] = 'APPROVED_LOCAL_BYTES_FRESH_CENTRAL_CHECKSUM'
                    self.seal()
                    return raw
        url = CENTRAL + path
        req = urllib.request.Request(url, headers={'User-Agent': 'TechDebt360-E1-build-plan-metadata'})
        for attempt in range(1, 4):
            if self.requests >= MAX_REQUESTS or time.monotonic() - self.started >= MAX_SECONDS:
                raise BudgetExceeded('E.1 request/time ceiling')
            if self.bytes >= MAX_BYTES:
                raise BudgetExceeded('E.1 transfer ceiling')
            self.requests += 1
            self.seal()  # durable attempt accounting before any I/O
            try:
                response = self.opener.open(req, timeout=15)
                break
            except urllib.error.HTTPError as exc:
                self.http_events.append(dict(path=path, status=exc.code))
                exc.close()  # error bodies not read; no hidden retries
                self.seal()
                raise
            except (urllib.error.URLError, TimeoutError) as exc:
                self.transport_failures.append(dict(path=path, attempt=attempt, type=type(exc).__name__))
                self.seal()
                if attempt == 3:
                    raise
        try:
            with response:
                if response.status != 200 or response.geturl() != url:
                    raise ValueError('Repository identity/redirect mismatch')
                cap = min(limit, MAX_ARTIFACT, MAX_BYTES - self.bytes)
                length = response.headers.get('Content-Length')
                expected = int(length) if length is not None else None
                if cap <= 0 or (expected is not None and not 0 <= expected <= cap):
                    raise BudgetExceeded('E.1 response/payload ceiling')
                raw = bytearray()
                while expected is None or len(raw) < expected:
                    if time.monotonic() - self.started >= MAX_SECONDS:
                        raise BudgetExceeded('E.1 wall-time ceiling')
                    allowance = min(65536, cap - len(raw))
                    if allowance <= 0:
                        raise BudgetExceeded('Cannot establish EOF within byte ceiling')
                    chunk = response.read(allowance)
                    if not chunk:
                        if expected is not None and len(raw) != expected:
                            raise ValueError('Truncated response')
                        break
                    self.bytes += len(chunk)
                    raw.extend(chunk)
                return bytes(raw)
        finally:
            self.seal()

    def seal(self):
        result=dict(version='e1-descriptor-acquisition-v1',base_commit=BASE,repository=CENTRAL,
            seed_expected=len(self.seed_paths),seed_count=len(self.seed_paths & self.records.keys()),
            new_count=len(self.records.keys()-self.seed_paths),requests=self.requests,transferred_bytes=self.bytes,
            elapsed_seconds=time.monotonic()-self.started,completed_roots=self.completed,
            prior_request_ledgers=dict(D=2000,D1=400,D2=52,D3=112,E03=56,E05=12,E051=52),
            limits=dict(requests=MAX_REQUESTS,response_bytes=MAX_BYTES,artifact_bytes=MAX_ARTIFACT,
                task_storage_bytes=MAX_DISK,wall_seconds=MAX_SECONDS,cpus=1,address_space_bytes=1073741824),
            actual_address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],
            cpu_affinity=sorted(os.sched_getaffinity(0)),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            http_events=self.http_events,transport_failures=self.transport_failures,local_source_checks=self.local_checks,
            artifacts=[dict(row,origin='E051_VERIFIED_INDEPENDENT_COPY' if name in self.seed_paths else
                self.origins.get(name,'CENTRAL_HTTPS_DOWNLOAD')) for name,row in sorted(self.records.items())],
            maven_executions=0,java_executions=0,artifact_executions=0,containers_started=0,
            trust='TLS and same-origin checksums; no independent publisher-signature claim')
        write(self.root/'dependency_manifest.json',result);self.check_disk();return result


class OfflineCache:
    get=seed.Acquisition.get
    def __init__(self,root):
        self.root=Path(root);self.cache=self.root/'repository'
        manifest=json.loads((self.root/'dependency_manifest.json').read_text())
        if manifest['version']!='e1-descriptor-acquisition-v1' or manifest['repository']!=CENTRAL:
            raise ValueError('Not E.1 cache')
        self.records=verify_rows(root,manifest);self.used_paths=set()
    def fetch(self,path,limit):raise ValueError('OFFLINE_MISSING: '+path)


# Jar-packaging phases/goals are unchanged pinned-Maven semantics. Exact versions
# must come from this revision's inherited/managed metadata, never from T0.
DEFAULTS={'maven-resources-plugin':[('process-resources','resources'),('process-test-resources','testResources')],
 'maven-compiler-plugin':[('compile','compile'),('test-compile','testCompile')],
 'maven-surefire-plugin':[('test','test')],'maven-jar-plugin':[('package','jar')],
 'maven-install-plugin':[('install','install')],'maven-deploy-plugin':[('deploy','deploy')]}


def source_inputs(base):
    """Verify and export only the single registered target; never run its code."""
    registry=json.loads(gzip.decompress((base/'examples/phase5_2_1/source_inventory.json.gz').read_bytes()))
    state=next(s for s in registry['source_states'] if s['commit_sha']==COMMIT)
    if state['tree_sha']!=TREE or state['offset_days']!=-30 or len(state['inventory']['entries'])!=116:
        raise ValueError('Frozen T-30 registration changed')
    repo=next(r['path'] for r in json.loads((base/'examples/phase5_2/replay_sources.example.json').read_text()) if r['repository_id']=='apache/commons-cli')
    if git(repo,'rev-parse',COMMIT+'^{tree}').decode().strip()!=TREE:raise ValueError('T-30 tree changed')
    actual=[]
    for line in git(repo,'ls-tree','-r','-z',COMMIT).split(b'\0'):
        if line:
            left,name=line.split(b'\t');mode,kind,oid=left.decode().split();actual.append((name.decode(),mode,kind,oid))
    expected=[(r['path'],r['mode'],r['object_type'],r['git_object_id']) for r in state['inventory']['entries']]
    if sorted(actual)!=sorted(expected):raise ValueError('T-30 full inventory mismatch')
    destination=TASK/'source';destination.mkdir(exist_ok=False,mode=0o700);rows=[]
    for name,mode,kind,oid in sorted(actual):
        if kind!='blob' or mode not in ('100644','100755') or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Unsafe source entry')
        if name in ('.mvn/maven.config','.mvn/jvm.config','.mvn/extensions.xml'):raise ValueError('Unreviewed Maven input')
        raw=git(repo,'cat-file','blob',oid)
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=oid:raise ValueError('Git blob mismatch')
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        target.chmod(0o555 if mode=='100755' else 0o444)
        rows.append(dict(path=name,mode=mode,git_blob=oid,bytes=len(raw),sha256=sha(target)))
    if sha(destination/'pom.xml')!=POM:raise ValueError('T-30 historical POM changed')
    manifest=dict(commit=COMMIT,tree=TREE,pom_sha256=POM,tracked_files=116,source_entries=rows,
        production_java_sources=[r['path'] for r in rows if r['path'].startswith('src/main/') and r['path'].endswith('.java')],
        actual_effective_model_sha256=None,maven_executions=0)
    write(TASK/'source_manifest.json',manifest)
    return manifest


def project_model(a,raw,files,identity):
    models=Models(a);model=models.build(parse_xml(raw),files,USER,identity)
    model['build_sections']=[]
    for layer in models.layers(parse_xml(raw)):
        for name in ('defaultGoal','sourceDirectory','testSourceDirectory','directory','outputDirectory','testOutputDirectory','resources','testResources'):
            element=layer.find('m:build/m:'+name,NS)
            if element is not None:
                model['build_sections'].append(dict(section=name,declaring_artifact=text(layer,'artifactId'),
                    xml=expand(ET.tostring(element,encoding='unicode'),model['properties']),
                    status='STATIC_INHERITANCE_INPUT_NOT_ACTUAL_EFFECTIVE_BUILD_SECTION'))
    return model,models


def plugin_rows(model):
    plugins=dict(model['plugins']);unknown=[];rows=[]
    for artifact in DEFAULTS:
        key=('org.apache.maven.plugins',artifact)
        if key not in plugins:
            if key not in model['managed_plugins']:
                unknown.append(dict(plugin=artifact,status='UNKNOWN_EXACT_DEFAULT_PLUGIN_VERSION'));continue
            plugins[key]=copy.deepcopy(model['managed_plugins'][key])
    for (group,artifact),element in plugins.items():
        managed=model['managed_plugins'].get((group,artifact))
        version=expand(text(element,'version') or (text(managed,'version') if managed is not None else None),model['properties'])
        executions=[dict(id=text(x,'id','default'),phase=text(x,'phase'),goal=g.text)
            for x in element.findall('m:executions/m:execution',NS) for g in x.findall('m:goals/m:goal',NS)]
        if artifact not in DEFAULTS and not any(x['phase'] is None or x['phase'] in previous.PHASES for x in executions):continue
        try:relative_path(group,artifact,version)
        except ValueError:
            unknown.append(dict(gav=[group,artifact,version],status='UNKNOWN_EXACT_PLUGIN_VERSION'));continue
        rows.append(dict(gav=[group,artifact,version],executions=executions,default_bindings=DEFAULTS.get(artifact,[]),
            configuration=ET.tostring(element,encoding='unicode'),execution_status='NOT_EXECUTED'))
    return rows,unknown


def buildplan_tasks(a,model):
    key=('org.apache.maven.plugins','maven-artifact-plugin');plugin=model['plugins'][key]
    gav=(*key,expand(text(plugin,'version'),model['properties']))
    raw=a.get(*gav,'jar');desc=parse_xml(previous.jar_member(raw,'META-INF/maven/plugin.xml'))
    mojo=next(x for x in desc.findall('mojos/mojo') if x.findtext('goal')=='check-buildplan')
    default=mojo.find('configuration/tasks').get('default-value')
    configured=[expand(e.text,model['properties']) for e in plugin.findall('m:configuration/m:tasks',NS)]
    for execution in plugin.findall('m:executions/m:execution',NS):
        if any(g.text=='check-buildplan' for g in execution.findall('m:goals/m:goal',NS)):
            configured += [expand(e.text,model['properties']) for e in execution.findall('m:configuration/m:tasks',NS)]
    selected=configured[-1] if configured else model['properties'].get('check.buildplan.tasks',default)
    if selected!='deploy':raise ValueError('Unsupported original plan task; do not silently assume deploy')
    return dict(selected=selected,configured_values=configured,descriptor_default=default,
        descriptor_sha256=hashlib.sha256(previous.jar_member(raw,'META-INF/maven/plugin.xml')).hexdigest(),
        actual_maven_plan_calculated=False)


def plan_inventory(a,model):
    rows,unknown=plugin_rows(model);output=[];missing=[]
    for row in rows:
        gav=tuple(row['gav']);paths=[relative_path(*gav,ext) for ext in ('pom','jar')]
        absent=[p for p in paths if p not in a.records]
        if absent and not getattr(a,'network_enabled',False):
            missing+=absent;output.append(dict(gav=list(gav),executions=row['executions'],default_bindings=row['default_bindings'],
                missing_paths=absent,execution_status='NOT_EXECUTED'));continue
        for ext in ('pom','jar'):a.get(*gav,ext)
        # Resolve default phases from this exact descriptor, then verify original goals.
        descriptor=previous.descriptor(a,gav);goals={x['goal']:x for x in descriptor['mojos']}
        for execution in row['executions']:
            if execution['phase'] is None:execution['phase']=goals.get(execution['goal'],{}).get('phase')
            if execution['phase'] is None:unknown.append(dict(gav=list(gav),goal=execution['goal'],status='UNKNOWN_DEFAULT_PHASE'))
        try:
            checked=descriptor_tools.inspect_plugin(a,row)
            checked.update(configured_plugin_xml=row['configuration'],missing_paths=[])
        except ValueError as exc:
            if not str(exc).startswith('OFFLINE_MISSING: '):raise
            path=str(exc).removeprefix('OFFLINE_MISSING: ');missing.append(path)
            checked=dict(gav=list(gav),missing_paths=[path],execution_status='NOT_EXECUTED',metadata_status='INCOMPLETE')
        output.append(checked)
    return dict(plugins=output,missing_paths=sorted(set(missing)),unknown=unknown,
        tasks=buildplan_tasks(a,model),actual_maven_plan_calculated=False)


def summary(model,models,manifest):
    rows,_=plugin_rows(model)
    return dict(parent_chain=model['chain'],imports=model['imports'],properties=model['properties'],
        dependencies=model['dependencies'],dependency_management=list(model['management'].values()),
        profiles=[dict(row,runtime_decision='UNKNOWN_NOT_MAVEN_EVALUATED') for row in model['profiles']],
        static_model_issues=models.issues,plugins=rows,source=manifest,build_sections=model.get('build_sections',[]),
        actual_effective_model_sha256=None,actual_maven_executed=False)


class ScopedCache:
    """Keep a closure's metadata provenance separate from other plan inspections."""
    def __init__(self,parent):
        self.parent=parent;self.cache=parent.cache;self.records=parent.records;self.used_paths=set()
    def get(self,group,artifact,version,extension='pom',classifier=''):
        self.used_paths.add(relative_path(group,artifact,version,extension,classifier))
        return self.parent.get(group,artifact,version,extension,classifier)


def registered_candidates(base,a):
    authority=json.loads((base/'examples/phase5_2_2_d/requirements.json').read_text())
    state=next(s for s in authority['states'] if s['commit_sha']==COMMIT)
    if state['pom_sha256']!=POM or state['tree_sha']!=TREE or state['parent_version']!='74':raise ValueError('Registered requirements mismatch')
    records=[]
    for plugin in state['plugins']:
        if plugin['required_through_compile'] is not True:continue
        for dep in plugin['dependencies']:
            for ext in ('pom','jar') if dep['type']!='pom' else ('pom',):
                path=relative_path(*dep['gav'],ext,dep.get('classifier',''))
                records.append(dict(path=path,gav=dep['gav'],extension=ext,reason=dep['reason'],present=path in a.records))
    return records


def compare(left,right):
    fields=('parent_chain','imports','dependencies','dependency_management','profiles','plugins','build_sections')
    result={k:dict(t0=left[k],t_minus_30=right[k],equal=left[k]==right[k]) for k in fields}
    result['changed_properties']={k:dict(t0=left['properties'].get(k),t_minus_30=right['properties'].get(k))
        for k in sorted(left['properties'].keys()|right['properties'].keys()) if left['properties'].get(k)!=right['properties'].get(k)}
    left_files={r['path']:r['sha256'] for r in left.get('source',{}).get('source_entries',[])}
    right_files={r['path']:r['sha256'] for r in right.get('source',{}).get('source_entries',[])}
    result['source_changes']=dict(added=sorted(right_files.keys()-left_files.keys()),removed=sorted(left_files.keys()-right_files.keys()),
        changed=sorted(k for k in left_files.keys()&right_files.keys() if left_files[k]!=right_files[k]),
        t0_java_sources=left.get('source',{}).get('production_java_sources',[]),
        t_minus30_java_sources=right.get('source',{}).get('production_java_sources',[]))
    result.update(actual_tminus30_effective_pom_sha256=None,method='Separate static inherited models; never a T0 effective-model substitution',
        remaining_actual_maven_model='UNVERIFIED',compiler_release='8',maven_test_skip=True,explicit_profiles=[])
    return result


def differential_closure(a,model,t0):
    """Only changed compile-plugin roots; unchanged bytes have actual T0 evidence."""
    models=Models(a);edges=[];roots=[]
    for row in plan_inventory(a,model)['plugins']:
        if row.get('missing_paths'):continue
        if not any(e['phase'] in ('validate','initialize','generate-sources','process-sources','generate-resources','process-resources','compile') for e in row['configured_executions']+[
                dict(phase=p,goal=g) for p,g in row['default_bindings']]):continue
        group,artifact,version=row['gav'];old=t0['plugins'].get((group,artifact))
        if old is None:old=t0['managed_plugins'].get((group,artifact))
        old_version=expand(text(old,'version'),t0['properties']) if old is not None else None
        if version==old_version:continue
        root=dict(gav=row['gav'],type='jar',classifier='',scope='compile',optional=False,exclusions=[])
        roots.append(row['gav']);edges+=models.closure([root],reason='Changed T-30 compile plugin '+artifact)
    return dict(roots=roots,edges=edges,issues=models.issues,runtime_resolution='UNKNOWN_STATIC_CANDIDATES_ONLY',
        unchanged_plugin_scope='Pinned T0 success is reuse evidence, not proof of T-30 effective-model equivalence')


def audit(base,a,manifest):
    raw=(TASK/'source/pom.xml').read_bytes();files=[r['path'] for r in manifest['source_entries']]
    model,models=project_model(a,raw,files,['commons-cli',COMMIT])
    t0raw=(seed.RESEARCH/'phase5_2_2_e_0_2/2026-10-18/inputs/source/pom.xml').read_bytes()
    t0q=json.loads((seed.RESEARCH/'phase5_2_2_e_0/2026-10-16/prerequisites.json').read_text())
    t0,t0models=project_model(a,t0raw,[r['path'] for r in t0q['source_entries']],['commons-cli',t0q['commit_sha']])
    plan=plan_inventory(a,model)
    closure=seed.static_closure(ScopedCache(a),model['dependencies'],model['management'])
    changed=differential_closure(a,model,t0)
    registered=registered_candidates(base,a)
    missing=set(plan['missing_paths'])|{r['path'] for r in closure['missing']}|{r['path'] for r in registered if not r['present']}
    for gav in TARGETS:
        missing.update(relative_path(*gav,ext) for ext in ('pom','jar') if relative_path(*gav,ext) not in a.records)
    return dict(target=summary(model,models,manifest),t0=summary(t0,t0models,dict(commit=t0q['commit_sha'],pom_sha256=t0q['pom_sha256'],tracked_files=117,source_entries=t0q['source_entries'],production_java_sources=[r['path'] for r in t0q['source_entries'] if r['path'].startswith('src/main/') and r['path'].endswith('.java')])),
        plan=plan,test_closure=closure,changed_compile_plugin_closure=changed,registered_candidates=registered,
        missing_paths=sorted(missing))



def issue_relevance(a,issues):
    """Preserve activation UNKNOWN; distinguish dependency build-only test config.

    A dependency's own test-plugin configuration is not inherited into the
    consuming Commons CLI project. No activation result is invented.
    """
    records=[]
    for issue in issues:
        row=dict(issue,activation='UNKNOWN_NOT_MAVEN_EVALUATED',blocking=True)
        if issue.get('kind')=='PROFILE' and issue.get('identity')==['org.apache.sshd','sshd-core','2.9.2']:
            path=relative_path(*issue['identity']);pom=parse_xml(a.get(*issue['identity']))
            profile=next((x for x in pom.findall('m:profiles/m:profile',NS) if text(x,'id')=='no-containers-for-windows'),None)
            if profile is not None:
                only_build=all(x.tag.split('}')[-1] in ('id','activation','build') for x in profile)
                build=profile.find('m:build',NS)
                plugins=profile.findall('m:build/m:plugins/m:plugin',NS)
                confined=build is not None and all(x.tag.split('}')[-1]=='plugins' for x in build)
                harmless=bool(plugins) and all(text(x,'artifactId')=='maven-surefire-plugin' and
                    all(y.tag.split('}')[-1] in ('groupId','artifactId','version','configuration') for y in x)
                    for x in plugins)
                if only_build and confined and harmless:
                    row.update(blocking=False,disposition='NON_PROPAGATING_REMOTE_TEST_PLUGIN_CONFIG',
                        pom_path=path,pom_sha256=hashlib.sha256(a.get(*issue['identity'])).hexdigest(),
                        profile_xml=ET.tostring(profile,encoding='unicode'),
                        reason_for_scope='Only SSHD own Surefire configuration; no dependency, dependency-management, properties or repository change. Not a Commons CLI parent profile.')
        records.append(row)
    return records


def decision(a,after,stop,capacity):
    issues=after['target']['static_model_issues']+after['plan']['unknown']+after['test_closure']['unresolved']+after['test_closure']['dependency_profile_uncertainties']+after['changed_compile_plugin_closure']['issues']
    for row in after['plan']['plugins']:issues+=row.get('static_model_issues',[])
    relevance=issue_relevance(a,issues)
    status='PASS_STATIC_T_MINUS_30_READINESS' if not stop and not after['missing_paths'] and not any(r['blocking'] for r in relevance) else 'PARTIAL'
    if (stop and stop['type']!='BudgetExceeded') or capacity['status']=='BLOCKED_RUNTIME_CACHE_CAPACITY':status='BLOCKED'
    return dict(status=status,issues=relevance,missing_paths=after['missing_paths'],stop=stop,
        actual_effective_model_sha256=None,actual_maven_execution='NOT_EXECUTED',compile_success=False,
        scope='Static paths, descriptors and test closure only; activation and actual Maven model/runtime remain unverified')


def run(base,output):
    enforce_process_limits();owned_output(output);rows=verify_seeds(base)
    # T0 success is independently rechecked without launching anything.
    from tools.verify_compile_e06 import audit as verify_t0
    t0=verify_t0(seed.RESEARCH/'phase5_2_2_e_0_6/2026-10-18/attempt-1')
    if t0['status']!='COMPILE_PASS':raise ValueError('T0 evidence no longer verifies')
    write(TASK/'t0_preservation_verification.json',{k:v for k,v in t0.items() if k!='classes'})
    manifest=source_inputs(base);a=Recovery(output,SOURCE,rows)
    before=audit(base,a,manifest);write(a.root/'audit_before.json',before)
    a.network_enabled=True;stop=None
    try:
        for gav in TARGETS:
            a.check_budget();a.get(*gav,'pom');a.get(*gav,'jar')
            if gav==TARGETS[-1]:descriptor_tools.inspect_plugin(a,dict(gav=list(gav),executions=[],default_bindings=[('test','test')]))
            a.completed.append(list(gav));a.seal()
            print(json.dumps(dict(root=list(gav),requests=a.requests,status='EXACT_ROOT_VERIFIED')),flush=True)
        # This traversal adds only actual test closure, exact plan descriptors,
        # and the changed through-compile plugin's authoritative candidate graph.
        audit(base,a,manifest)
    except (BudgetExceeded,ValueError,OSError,urllib.error.URLError,zipfile.BadZipFile) as exc:
        stop=dict(type=type(exc).__name__,reason=str(exc)[:1500])
    finally:
        a.network_enabled=False;after=audit(base,a,manifest)
        capacity=previous.runtime_capacity(list(a.records.values()))
        qualification=decision(a,after,stop,capacity);issues=qualification['issues'];status=qualification['status']
        write(a.root/'audit_after.json',after);write(a.root/'configuration_difference.json',compare(after['t0'],after['target']))
        write(a.root/'runtime_cache_capacity.json',capacity)
        write(a.root/'frontier_comparison.json',dict(status=status,stop=stop,before=before['missing_paths'],after=after['missing_paths'],
            resolved=sorted(set(before['missing_paths'])-set(after['missing_paths'])),issues=issues,
            actual_tminus30_effective_model_sha256=None,compile_success=False,actual_maven_execution='NOT_AUTHORIZED_NOT_EXECUTED'))
        checked=verify_rows(a.root,dict(artifacts=list(a.records.values())))
        if any(sha(a.cache/r['path'])!=r['sha256'] for r in rows):raise ValueError('Seed changed')
        a.seal();write(a.root/'cache_identity.json',dict(artifact_count=len(checked),canonical_sha256=canonical(checked),
            manifest_sha256=sha(a.root/'dependency_manifest.json'),seed_count=697,seed_manifest_sha256=MANIFEST,
            seed_identity_sha256=CACHE_ID,all_hashes_provenance_pom_crc_verified=True,independent_copies=True))
    return a


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    parser.add_argument('--audit-only',action='store_true');args=parser.parse_args();enforce_process_limits()
    base=Path(__file__).resolve().parents[1]
    if args.audit_only:
        a=OfflineCache(args.output);manifest=json.loads((TASK/'source_manifest.json').read_text())
        print(json.dumps(audit(base,a,manifest),sort_keys=True,indent=2));return
    a=run(base,args.output)
    print(json.dumps(dict(status=json.loads((a.root/'frontier_comparison.json').read_text())['status'],requests=a.requests,
        artifact_count=len(a.records),response_bytes=a.bytes)))


if __name__=='__main__':main()
