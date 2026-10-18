"""E.4: T+60 static Maven readiness with one bounded exact recovery batch.

XML/ZIP inspection only. Never executes Maven, Java or containers. A separate
80-request transport has no retries and a durable, exclusive acquisition ledger.
"""
import argparse
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import time
import urllib.error
import zipfile
from tools import prepare_tminus30 as reference
from tools import recover_compile_test_dependencies as seed
from tools import recover_buildplan_plugin as previous
from tools import recover_buildplan_frontier as descriptor_tools
from tools.recover_phase5_2_2_d import git
from tools.recover_phase5_2_2_d_2 import verify_rows, enforce_process_limits
from tools.maven_recovery.acquisition import BudgetExceeded, CENTRAL, relative_path, parse_xml
from tools.maven_recovery.model import Models, NS, text, expand

BASE='9c582dcf2916b18061885002ad4d136e787d0757'
TASK=seed.RESEARCH/'phase5_2_2_e_4/2026-10-19'
SOURCE=seed.RESEARCH/'phase5_2_2_e_3/2026-10-18/recovery-1'
MANIFEST='2e77c1a9578231e6b9f8d6425fb6ebe45304d7905f8e91d02346e1ca0d199fa9'
CACHE_ID='a6469c15e4a99fcb4b59f8c4c3a9c19892523cffa8a5a2467711cda11399b463'
COMMIT='aad30eff27ac5c9a13194125226653c6c2826c58'
TREE='d7434665397c8dd8156fff7ecaed29a14feeb951'
POM='1c82171f91da0f4aa2994bb367e4c9ef8e65414940100be081715605739d9e0b'
TRACKED_FILES=138
JAVA_FILES=36
TARGETS=(('commons-io','commons-io','2.18.0'),)
MAX_REQUESTS,MAX_BYTES,MAX_ARTIFACT=80,24*1024**2,16*1024**2
MAX_DISK,MAX_SECONDS=256*1024**2,600
USER=reference.USER
sha,write,canonical=reference.sha,reference.write,reference.canonical
project_model=reference.project_model
plugin_rows=reference.plugin_rows
summary=reference.summary
ScopedCache=reference.ScopedCache


def owned_output(root,task=TASK):
    root,task=Path(root).absolute(),Path(task).absolute()
    if root!=task/'recovery-1' or root.resolve()!=root or task.resolve()!=task:
        raise ValueError('Exclusive E.4 output path required')
    if any(p.is_symlink() or (p/'.git').exists() for p in (root,*root.parents)):
        raise ValueError('Symlink/Git task path forbidden')
    owner=json.loads((task/'owner.json').read_text())
    if owner!=dict(phase='E.4',base=BASE,exclusive_root=str(task)):
        raise ValueError('Task ownership mismatch')
    if root.exists():raise FileExistsError('Non-resumable exclusive acquisition claim')
    return root


def verify_seeds(base,source=SOURCE):
    published=Path(base)/'examples/phase5_2_2_e_3/dependency_manifest.json'
    if sha(published)!=MANIFEST or sha(source/'dependency_manifest.json')!=MANIFEST:
        raise ValueError('Frozen751 manifest changed')
    manifest=json.loads(published.read_text())
    if len(manifest['artifacts'])!=751 or manifest['requests']!=46:
        raise ValueError('Frozen751 population/ledger changed')
    records=verify_rows(source,manifest)
    if canonical(records)!=CACHE_ID:raise ValueError('Canonical751 cache identity mismatch')
    actual={str(p.relative_to(source/'repository')) for p in (source/'repository').rglob('*') if p.is_file()}
    if actual!=set(records):raise ValueError('Unregistered seed paths')
    return list(records.values())


class Recovery(seed.Recovery):
    def __init__(self,root,source,rows,local=seed.LOCAL,task=TASK):
        target=owned_output(root,task)
        for name in ('phase5_2_2_d','phase5_2_2_d_1','phase5_2_2_d_2','phase5_2_2_d_3',
                'phase5_2_2_e_0','phase5_2_2_e_0_1','phase5_2_2_e_0_2','phase5_2_2_e_0_3',
                'phase5_2_2_e_0_4','phase5_2_2_e_0_5','phase5_2_2_e_0_5_1','phase5_2_2_e_0_6',
                'phase5_2_2_e_1','phase5_2_2_e_1_1','phase5_2_2_e_2','phase5_2_2_e_2_1','phase5_2_2_e_3','phase5_2_2_e_3_1'):
            protected=seed.RESEARCH/name
            if target.is_relative_to(protected) or protected.is_relative_to(target):
                raise ValueError('Previous phase is read-only')
        self.task=Path(task).absolute();self.completed=[]
        super().__init__(target,source,rows,local=local)

    def check_budget(self):
        if self.requests>=MAX_REQUESTS or self.bytes>=MAX_BYTES or time.monotonic()-self.started>=MAX_SECONDS:
            raise BudgetExceeded('E.4 request/byte/time ceiling; no continuation authorized')

    def check_disk(self,extra=0):
        size=sum(p.stat().st_size for p in self.task.rglob('*') if p.is_file())
        if size+extra>MAX_DISK:raise BudgetExceeded('E.4 total task storage ceiling')
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
        req = urllib.request.Request(url, headers={'User-Agent': 'TechDebt360-E4-build-plan-metadata'})
        for attempt in range(1, 2):
            if self.requests >= MAX_REQUESTS or time.monotonic() - self.started >= MAX_SECONDS:
                raise BudgetExceeded('E.4 request/time ceiling')
            if self.bytes >= MAX_BYTES:
                raise BudgetExceeded('E.4 transfer ceiling')
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
                if attempt == 1:
                    raise
        try:
            with response:
                if response.status != 200 or response.geturl() != url:
                    raise ValueError('Repository identity/redirect mismatch')
                cap = min(limit, MAX_ARTIFACT, MAX_BYTES - self.bytes)
                length = response.headers.get('Content-Length')
                expected = int(length) if length is not None else None
                if cap <= 0 or (expected is not None and not 0 <= expected <= cap):
                    raise BudgetExceeded('E.4 response/payload ceiling')
                raw = bytearray()
                while expected is None or len(raw) < expected:
                    if time.monotonic() - self.started >= MAX_SECONDS:
                        raise BudgetExceeded('E.4 wall-time ceiling')
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
        result=dict(version='e4-descriptor-acquisition-v1',base_commit=BASE,repository=CENTRAL,
            seed_expected=len(self.seed_paths),seed_count=len(self.seed_paths & self.records.keys()),
            new_count=len(self.records.keys()-self.seed_paths),requests=self.requests,transferred_bytes=self.bytes,
            elapsed_seconds=time.monotonic()-self.started,completed_roots=self.completed,
            prior_request_ledgers=dict(D=2000,D1=400,D2=52,D3=112,E03=56,E05=12,E051=52,E1=32,E2=67,E3=46),
            limits=dict(requests=MAX_REQUESTS,response_bytes=MAX_BYTES,artifact_bytes=MAX_ARTIFACT,
                task_storage_bytes=MAX_DISK,wall_seconds=MAX_SECONDS,cpus=1,address_space_bytes=1073741824),
            actual_address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],cpu_affinity=sorted(os.sched_getaffinity(0)),
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,http_events=self.http_events,
            transport_failures=self.transport_failures,local_source_checks=self.local_checks,
            artifacts=[dict(row,origin='E3_VERIFIED_INDEPENDENT_COPY' if name in self.seed_paths else
                self.origins.get(name,'CENTRAL_HTTPS_DOWNLOAD')) for name,row in sorted(self.records.items())],
            maven_executions=0,java_executions=0,artifact_executions=0,containers_started=0,
            transport_source_sha256=sha(Path(__file__)),http_automatic_retries=0,
            trust='TLS and same-origin checksums; no independent publisher-signature claim')
        write(self.root/'dependency_manifest.json',result);self.check_disk();return result


class OfflineCache:
    get=seed.Acquisition.get
    def __init__(self,root):
        self.root=Path(root);self.cache=self.root/'repository'
        manifest=json.loads((self.root/'dependency_manifest.json').read_text())
        if manifest['version']!='e4-descriptor-acquisition-v1' or manifest['repository']!=CENTRAL:
            raise ValueError('Not E.4 cache')
        self.records=verify_rows(root,manifest);self.used_paths=set()
    def fetch(self,path,limit):raise ValueError('OFFLINE_MISSING: '+path)


def plan_inventory(a,model):
    """Each descriptor receives independent metadata-path tracking, even on reuse."""
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
            checked=descriptor_tools.inspect_plugin(ScopedCache(a),row)
            checked.update(configured_plugin_xml=row['configuration'],missing_paths=[])
        except ValueError as exc:
            if not str(exc).startswith('OFFLINE_MISSING: '):raise
            path=str(exc).removeprefix('OFFLINE_MISSING: ');missing.append(path)
            checked=dict(gav=list(gav),missing_paths=[path],execution_status='NOT_EXECUTED',metadata_status='INCOMPLETE')
        output.append(checked)
    return dict(plugins=output,missing_paths=sorted(set(missing)),unknown=unknown,
        tasks=reference.buildplan_tasks(a,model),actual_maven_plan_calculated=False)


def source_inputs(base):
    """Verify and export only the single registered target; never run its code."""
    registry=json.loads(gzip.decompress((base/'examples/phase5_2_1/source_inventory.json.gz').read_bytes()))
    state=next(s for s in registry['source_states'] if s['commit_sha']==COMMIT)
    if state['tree_sha']!=TREE or state['offset_days']!=60 or len(state['inventory']['entries'])!=TRACKED_FILES:
        raise ValueError('Frozen T+60 registration changed')
    repo=next(r['path'] for r in json.loads((base/'examples/phase5_2/replay_sources.example.json').read_text()) if r['repository_id']=='apache/commons-cli')
    for kind,oid in [('commit',COMMIT),('tree',TREE)]:
        raw=git(repo,'cat-file',kind,oid)
        if hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=oid:
            raise ValueError('Git object identity mismatch')
    if git(repo,'rev-parse',COMMIT+'^{tree}').decode().strip()!=TREE:raise ValueError('T+60 tree changed')
    actual=[]
    for line in git(repo,'ls-tree','-r','-z',COMMIT).split(b'\0'):
        if line:
            left,name=line.split(b'\t');mode,kind,oid=left.decode().split();actual.append((name.decode(),mode,kind,oid))
    expected=[(r['path'],r['mode'],r['object_type'],r['git_object_id']) for r in state['inventory']['entries']]
    if sorted(actual)!=sorted(expected):raise ValueError('T+60 full inventory mismatch')
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
    if sha(destination/'pom.xml')!=POM:raise ValueError('T+60 historical POM changed')
    production=[r['path'] for r in rows if r['path'].startswith('src/main/') and r['path'].endswith('.java')]
    if len(production)!=JAVA_FILES:raise ValueError('Frozen36-source inventory mismatch')
    manifest=dict(commit=COMMIT,tree=TREE,pom_sha256=POM,tracked_files=TRACKED_FILES,source_entries=rows,
        production_java_sources=production,
        actual_effective_model_sha256=None,maven_executions=0)
    write(TASK/'source_manifest.json',manifest)
    return manifest



def registered_candidates(base,a,plan):
    authority=json.loads((Path(base)/'examples/phase5_2_2_d/requirements.json').read_text())
    state=next(s for s in authority['states'] if s['commit_sha']==COMMIT)
    if (state['pom_sha256'],state['tree_sha'],state['parent_version'])!=(POM,TREE,'78'):
        raise ValueError('Registered T+60 requirements mismatch')
    records=[]
    for plugin in state['plugins']:
        flag=plugin['required_through_compile']
        candidate=next((r for r in plan['plugins'] if r['gav']==plugin['gav']),None)
        phases=('validate','initialize','generate-sources','process-sources','generate-resources','process-resources','compile')
        observed_static=bool(candidate and not candidate.get('missing_paths') and any(
            r['phase'] in phases for r in candidate['configured_executions']+[dict(phase=p) for p,g in candidate['default_bindings']]))
        if not (flag is True or flag is None and observed_static):continue
        for dep in plugin['dependencies']:
            for ext in ('pom','jar') if dep['type']!='pom' else ('pom',):
                path=relative_path(*dep['gav'],ext,dep.get('classifier',''))
                records.append(dict(path=path,gav=dep['gav'],extension=ext,reason=dep['reason'],present=path in a.records,legacy_required_through_compile=flag,target_descriptor_requires_compile=observed_static))
    return records


def comparison(left,right,baseline):
    fields=('parent_chain','imports','dependencies','dependency_management','profiles','plugins','build_sections')
    result={k:{baseline:left[k],'t_plus60':right[k],'equal':left[k]==right[k]} for k in fields}
    result['changed_properties']={k:{baseline:left['properties'].get(k),'t_plus60':right['properties'].get(k)}
        for k in sorted(left['properties'].keys()|right['properties'].keys()) if left['properties'].get(k)!=right['properties'].get(k)}
    l={r['path']:r['sha256'] for r in left['source']['source_entries']}
    r={r['path']:r['sha256'] for r in right['source']['source_entries']}
    result['source_changes']=dict(added=sorted(r.keys()-l.keys()),removed=sorted(l.keys()-r.keys()),
        changed=sorted(k for k in l.keys()&r.keys() if l[k]!=r[k]),
        changed_production_java=sorted(k for k in l.keys()&r.keys() if l[k]!=r[k] and k.startswith('src/main/') and k.endswith('.java')))
    result.update(actual_tplus60_effective_pom_sha256=None,method='Independent static parent inheritance, not actual Maven effective models',
        remaining_actual_maven_model='UNKNOWN',compiler_release='8',maven_test_skip=True,explicit_profiles=[])
    return result


def differential_closure(a,plan,baseline):
    """Changed compile-plugin conservative closure relative to successful T+30."""
    models=Models(a);edges=[];roots=[]
    phases=('validate','initialize','generate-sources','process-sources','generate-resources','process-resources','compile')
    for row in plan['plugins']:
        if row.get('missing_paths'):continue
        if not any(e['phase'] in phases for e in row['configured_executions']+[dict(phase=p,goal=g) for p,g in row['default_bindings']]):continue
        group,artifact,version=row['gav'];old=baseline['plugins'].get((group,artifact))
        if old is None:old=baseline['managed_plugins'].get((group,artifact))
        old_version=expand(text(old,'version'),baseline['properties']) if old is not None else None
        if version==old_version:continue
        root=dict(gav=row['gav'],type='jar',classifier='',scope='compile',optional=False,exclusions=[])
        roots.append(row['gav']);edges+=models.closure([root],reason='Changed T+60 compile plugin '+artifact)
    return dict(roots=roots,edges=edges,issues=models.issues,runtime_resolution='UNKNOWN_STATIC_CANDIDATES_ONLY',
        unchanged_plugin_scope='T+30 success is reuse evidence only; project metadata and all descriptors independently rechecked')


def audit(base,a,manifest):
    model,models=project_model(a,(TASK/'source/pom.xml').read_bytes(),[r['path'] for r in manifest['source_entries']],['commons-cli',COMMIT])
    baseline_source=seed.RESEARCH/'phase5_2_2_e_3/2026-10-18/source'
    baseline_manifest=json.loads((baseline_source.parent/'source_manifest.json').read_text())
    baseline,baseline_models=project_model(a,(baseline_source/'pom.xml').read_bytes(),
        [r['path'] for r in baseline_manifest['source_entries']],['commons-cli',baseline_manifest['commit']])
    plan=plan_inventory(a,model)
    closure=seed.static_closure(ScopedCache(a),model['dependencies'],model['management'])
    changed=differential_closure(a,plan,baseline)
    registered=registered_candidates(base,a,plan)
    missing=set(plan['missing_paths'])|{r['path'] for r in closure['missing']}|{r['path'] for r in registered if not r['present']}
    for gav in TARGETS:missing.update(relative_path(*gav,ext) for ext in ('pom','jar') if relative_path(*gav,ext) not in a.records)
    for issue in changed['issues']+models.issues:
        match=re.search(r'OFFLINE_MISSING: ([A-Za-z0-9_./-]+)',str(issue.get('reason','')))
        if match:missing.add(match[1])
    target=summary(model,models,manifest)
    baseline_summary=summary(baseline,baseline_models,baseline_manifest)
    return dict(target=target,tplus30=baseline_summary,plan=plan,test_closure=closure,
        changed_compile_plugin_closure=changed,registered_candidates=registered,missing_paths=sorted(missing),
        comparisons=dict(tplus30_vs_tplus60=comparison(baseline_summary,target,'t_plus30')))



def compiler_profile_scope(a,identity):
    """Prove only the scope of a remote build property, never profile activation.

    Commons Parent58 is not a T+60 project parent. The three exact dependency
    models have an unresolved profile setting only maven.compiler.release, which
    has no property-reference consumer anywhere in those inheritance layers.
    It therefore cannot select a different dependency/BOM/parent coordinate.
    """
    allowed={('org.apache.commons','commons-lang3','3.13.0'),('commons-codec','commons-codec','1.16.0'),('commons-io','commons-io','2.13.0')}
    if tuple(identity) not in allowed:return None
    layers=Models(a).layers(parse_xml(a.get(*identity)))
    parent=next((p for p in layers if text(p,'artifactId')=='commons-parent' and text(p,'version')=='58'),None)
    if parent is None:return None
    profile=next((p for p in parent.findall('m:profiles/m:profile',NS) if text(p,'id')=='jdk9-compiler'),None)
    if profile is None or [p.tag.rsplit('}',1)[-1] for p in profile]!=['id','activation','properties']:return None
    activation=profile.find('m:activation',NS)
    if len(activation)!=1 or text(activation,'jdk')!='[9':return None
    props=profile.find('m:properties',NS)
    if len(props)!=1 or props[0].tag.rsplit('}',1)[-1]!='maven.compiler.release' or props[0].text!='${commons.compiler.release}':return None
    # Any property reference or activation reading this name defeats the proof.
    for layer in layers:
        for element in layer.iter():
            value=(element.text or '')+' '+str(element.attrib)
            if '${maven.compiler.release}' in value or (element.tag.rsplit('}',1)[-1]=='name' and (element.text or '').lstrip('!')=='maven.compiler.release'):
                return None
    paths=[]
    for layer in layers:
        parent_node=layer.find('m:parent',NS)
        group=text(layer,'groupId') or (text(parent_node,'groupId') if parent_node is not None else None)
        version=text(layer,'version') or (text(parent_node,'version') if parent_node is not None else None)
        gav=[group,text(layer,'artifactId'),version];raw=a.get(*gav)
        paths.append(dict(gav=gav,path=relative_path(*gav),sha256=hashlib.sha256(raw).hexdigest()))
    return dict(profile_id='jdk9-compiler',activation_literal='[9',activation='UNKNOWN_NOT_MAVEN_EVALUATED',
        profile_xml=__import__('xml.etree.ElementTree',fromlist=['tostring']).tostring(profile,encoding='unicode'),
        verified_layers=paths,only_defined_property='maven.compiler.release',property_reference_consumers=0,
        target_parent_version='78',remote_parent_version='58',
        reason='Remote dependency own compiler property only; no consumer in its inherited POM declarations. It does not propagate into Commons CLI project inheritance or dependency identities.')


def issue_relevance(a,issues):
    rows=reference.issue_relevance(a,issues)
    for row in rows:
        if row.get('kind')!='PROFILE' or 'jdk9-compiler' not in str(row.get('reason')):continue
        proof=compiler_profile_scope(a,row.get('identity',[]))
        if proof is not None:
            row.update(blocking=False,disposition='NON_PROPAGATING_REMOTE_COMPILER_PROPERTY',scope_evidence=proof)
    return rows


def decision(a,after,stop,capacity):
    issues=after['target']['static_model_issues']+after['plan']['unknown']+after['test_closure']['unresolved']+after['test_closure']['dependency_profile_uncertainties']+after['changed_compile_plugin_closure']['issues']
    for row in after['plan']['plugins']:issues+=row.get('static_model_issues',[])
    relevance=issue_relevance(a,issues)
    status='PASS_STATIC_T_PLUS_60_READINESS' if not stop and not after['missing_paths'] and not any(r['blocking'] for r in relevance) else 'PARTIAL'
    if (stop and stop['type']!='BudgetExceeded') or capacity['status']=='BLOCKED_RUNTIME_CACHE_CAPACITY':status='BLOCKED'
    return dict(status=status,issues=relevance,missing_paths=after['missing_paths'],stop=stop,
        actual_effective_model_sha256=None,actual_maven_execution='NOT_EXECUTED',compile_success=False,
        capacity_status=capacity['status'],scope='Static paths/descriptors/closure only; actual model,profiles and classpaths remain unverified')


def verify_successful_builds():
    from tools.verify_compile_e06 import audit as verify_t0
    from tools.verify_compile_e11 import audit as verify_t30
    from tools.verify_compile_e21 import audit as verify_t90
    from tools.verify_compile_e31 import audit as verify_tplus30
    proofs={}
    for name,path,auditor in [('t0','phase5_2_2_e_0_6/2026-10-18/attempt-1',verify_t0),('tminus30','phase5_2_2_e_1_1/2026-10-18/attempt-1',verify_t30),('tminus90','phase5_2_2_e_2_1/2026-10-18/attempt-1',verify_t90),('tplus30','phase5_2_2_e_3_1/2026-10-19/attempt-1',verify_tplus30)]:
        root=seed.RESEARCH/path;proof=auditor(root)
        if proof['status']!='COMPILE_PASS':raise ValueError(name+' prior evidence no longer verifies')
        proof['claim_sha256']=sha(root/'attempt_claim.json')
        proof['execution_sha256']=sha(root/'execution.json')
        proof['class_archive_sha256']=sha(root/'capture/classes.tar')
        proofs[name]=proof
    return proofs


def run(base,output):
    enforce_process_limits();owned_output(output);rows=verify_seeds(base)
    proofs=verify_successful_builds();write(TASK/'successful_builds_verification.json',proofs)
    manifest=source_inputs(base);a=Recovery(output,SOURCE,rows)
    before=audit(base,a,manifest);write(a.root/'audit_before.json',before)
    a.network_enabled=True;stop=None
    try:
        for gav in TARGETS:
            a.check_budget();a.get(*gav,'pom');a.get(*gav,'jar')
            if gav[1].endswith('-maven-plugin') or gav[1].startswith('maven-'):
                # Resolve only original descriptor goals/metadata for this plugin.
                current,_=project_model(a,(TASK/'source/pom.xml').read_bytes(),[r['path'] for r in manifest['source_entries']],['commons-cli',COMMIT])
                candidate=next(row for row in plugin_rows(current)[0] if tuple(row['gav'])==gav)
                descriptor=previous.descriptor(a,gav);goals={r['goal']:r for r in descriptor['mojos']}
                for execution in candidate['executions']:
                    if execution['phase'] is None:execution['phase']=goals.get(execution['goal'],{}).get('phase')
                descriptor_tools.inspect_plugin(a,candidate)
            a.completed.append(list(gav));a.seal()
            print(json.dumps(dict(root=list(gav),requests=a.requests,status='EXACT_ROOT_VERIFIED')),flush=True)
        audit(base,a,manifest)
    except (BudgetExceeded,ValueError,OSError,urllib.error.URLError,zipfile.BadZipFile) as exc:
        stop=dict(type=type(exc).__name__,reason=str(exc)[:1500])
    finally:
        a.network_enabled=False
        after=audit(base,a,manifest);capacity=previous.runtime_capacity(list(a.records.values()))
        qualification=decision(a,after,stop,capacity)
        write(a.root/'audit_after.json',after);write(a.root/'configuration_difference.json',after['comparisons'])
        write(a.root/'runtime_cache_capacity.json',capacity)
        write(a.root/'frontier_comparison.json',dict(**qualification,before=before['missing_paths'],after=after['missing_paths'],
            resolved=sorted(set(before['missing_paths'])-set(after['missing_paths'])),
            newly_exposed_resolved_paths=sorted(set(a.records)-{r['path'] for r in rows}-set(before['missing_paths']))))
        checked=verify_rows(a.root,dict(artifacts=list(a.records.values())))
        if any(sha(a.cache/r['path'])!=r['sha256'] for r in rows):raise ValueError('Seed changed')
        a.seal();write(a.root/'cache_identity.json',dict(artifact_count=len(checked),canonical_sha256=canonical(checked),
            manifest_sha256=sha(a.root/'dependency_manifest.json'),seed_count=751,seed_manifest_sha256=MANIFEST,
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
