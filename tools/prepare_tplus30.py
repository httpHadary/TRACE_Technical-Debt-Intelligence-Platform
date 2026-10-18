"""E.3: T+30 static Maven readiness with one bounded exact recovery batch.

XML/ZIP inspection only. Never executes Maven, Java or containers. The E.1
transport is versioned with retries disabled and its own durable request ledger.
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

BASE='ce833d41f9d65ff59179beee5a08cc7bb6293e12'
TASK=seed.RESEARCH/'phase5_2_2_e_3/2026-10-18'
SOURCE=seed.RESEARCH/'phase5_2_2_e_2/2026-10-18/recovery-1'
MANIFEST='abbfd6711f2d16b4eb4f0992d819c01cb85c8cef385f6a7c9effb2136d35e4b6'
CACHE_ID='e4870752be9fc1517fbdbb6eb785a704211950630839ac12e39d562725e95ecf'
COMMIT='7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b'
TREE='a2ff09febdac9da6e6ee422a9144ad09d81113bf'
POM='674975083520370c7a691778fa6fcdfe2eb0ae672c48abc923ffc75688c73e8e'
TRACKED_FILES=137
JAVA_FILES=36
TARGETS=(('org.junit.jupiter','junit-jupiter-api','5.11.2'),
 ('org.junit.jupiter','junit-jupiter-engine','5.11.2'),
 ('org.junit.jupiter','junit-jupiter-params','5.11.2'),
 ('org.apache.commons','commons-text','1.12.0'),
 ('org.apache.maven.plugins','maven-surefire-plugin','3.5.1'),
 ('org.cyclonedx','cyclonedx-maven-plugin','2.9.0'))
MAX_REQUESTS,MAX_BYTES,MAX_ARTIFACT=200,64*1024**2,32*1024**2
MAX_DISK,MAX_SECONDS=256*1024**2,600
USER=reference.USER
sha,write,canonical=reference.sha,reference.write,reference.canonical
project_model=reference.project_model
plugin_rows=reference.plugin_rows
plan_inventory=reference.plan_inventory
summary=reference.summary
ScopedCache=reference.ScopedCache


def owned_output(root,task=TASK):
    root,task=Path(root).absolute(),Path(task).absolute()
    if root!=task/'recovery-1' or root.resolve()!=root or task.resolve()!=task:
        raise ValueError('Exclusive E.3 output path required')
    if any(p.is_symlink() or (p/'.git').exists() for p in (root,*root.parents)):
        raise ValueError('Symlink/Git task path forbidden')
    owner=json.loads((task/'owner.json').read_text())
    if owner!=dict(phase='E.3',base=BASE,exclusive_root=str(task)):
        raise ValueError('Task ownership mismatch')
    if root.exists():raise FileExistsError('Non-resumable exclusive acquisition claim')
    return root


def verify_seeds(base,source=SOURCE):
    published=Path(base)/'examples/phase5_2_2_e_2/dependency_manifest.json'
    if sha(published)!=MANIFEST or sha(source/'dependency_manifest.json')!=MANIFEST:
        raise ValueError('Frozen734 manifest changed')
    manifest=json.loads(published.read_text())
    if len(manifest['artifacts'])!=734 or manifest['requests']!=67:
        raise ValueError('Frozen734 population/ledger changed')
    records=verify_rows(source,manifest)
    if canonical(records)!=CACHE_ID:raise ValueError('Canonical734 cache identity mismatch')
    actual={str(p.relative_to(source/'repository')) for p in (source/'repository').rglob('*') if p.is_file()}
    if actual!=set(records):raise ValueError('Unregistered seed paths')
    return list(records.values())


class Recovery(seed.Recovery):
    def __init__(self,root,source,rows,local=seed.LOCAL,task=TASK):
        target=owned_output(root,task)
        for name in ('phase5_2_2_d','phase5_2_2_d_1','phase5_2_2_d_2','phase5_2_2_d_3',
                'phase5_2_2_e_0','phase5_2_2_e_0_1','phase5_2_2_e_0_2','phase5_2_2_e_0_3',
                'phase5_2_2_e_0_4','phase5_2_2_e_0_5','phase5_2_2_e_0_5_1','phase5_2_2_e_0_6',
                'phase5_2_2_e_1','phase5_2_2_e_1_1','phase5_2_2_e_2','phase5_2_2_e_2_1'):
            protected=seed.RESEARCH/name
            if target.is_relative_to(protected) or protected.is_relative_to(target):
                raise ValueError('Previous phase is read-only')
        # The transport's literal ceilings must agree before it can be reused.
        if (MAX_REQUESTS,MAX_BYTES,MAX_ARTIFACT,MAX_SECONDS)!=(reference.MAX_REQUESTS,reference.MAX_BYTES,reference.MAX_ARTIFACT,reference.MAX_SECONDS):
            raise ValueError('Frozen transport budget mismatch')
        self.task=Path(task).absolute();self.completed=[]
        super().__init__(target,source,rows,local=local)

    def check_budget(self):
        if self.requests>=MAX_REQUESTS or self.bytes>=MAX_BYTES or time.monotonic()-self.started>=MAX_SECONDS:
            raise BudgetExceeded('E.3 request/byte/time ceiling; no continuation authorized')

    def check_disk(self,extra=0):
        size=sum(p.stat().st_size for p in self.task.rglob('*') if p.is_file())
        if size+extra>MAX_DISK:raise BudgetExceeded('E.3 total task storage ceiling')
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
        req = urllib.request.Request(url, headers={'User-Agent': 'TechDebt360-E3-build-plan-metadata'})
        for attempt in range(1, 2):
            if self.requests >= MAX_REQUESTS or time.monotonic() - self.started >= MAX_SECONDS:
                raise BudgetExceeded('E.3 request/time ceiling')
            if self.bytes >= MAX_BYTES:
                raise BudgetExceeded('E.3 transfer ceiling')
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
                    raise BudgetExceeded('E.3 response/payload ceiling')
                raw = bytearray()
                while expected is None or len(raw) < expected:
                    if time.monotonic() - self.started >= MAX_SECONDS:
                        raise BudgetExceeded('E.3 wall-time ceiling')
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
        result=dict(version='e3-descriptor-acquisition-v1',base_commit=BASE,repository=CENTRAL,
            seed_expected=len(self.seed_paths),seed_count=len(self.seed_paths & self.records.keys()),
            new_count=len(self.records.keys()-self.seed_paths),requests=self.requests,transferred_bytes=self.bytes,
            elapsed_seconds=time.monotonic()-self.started,completed_roots=self.completed,
            prior_request_ledgers=dict(D=2000,D1=400,D2=52,D3=112,E03=56,E05=12,E051=52,E1=32,E2=67),
            limits=dict(requests=MAX_REQUESTS,response_bytes=MAX_BYTES,artifact_bytes=MAX_ARTIFACT,
                task_storage_bytes=MAX_DISK,wall_seconds=MAX_SECONDS,cpus=1,address_space_bytes=1073741824),
            actual_address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],cpu_affinity=sorted(os.sched_getaffinity(0)),
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,http_events=self.http_events,
            transport_failures=self.transport_failures,local_source_checks=self.local_checks,
            artifacts=[dict(row,origin='E2_VERIFIED_INDEPENDENT_COPY' if name in self.seed_paths else
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
        if manifest['version']!='e3-descriptor-acquisition-v1' or manifest['repository']!=CENTRAL:
            raise ValueError('Not E.3 cache')
        self.records=verify_rows(root,manifest);self.used_paths=set()
    def fetch(self,path,limit):raise ValueError('OFFLINE_MISSING: '+path)


def source_inputs(base):
    """Verify and export only the single registered target; never run its code."""
    registry=json.loads(gzip.decompress((base/'examples/phase5_2_1/source_inventory.json.gz').read_bytes()))
    state=next(s for s in registry['source_states'] if s['commit_sha']==COMMIT)
    if state['tree_sha']!=TREE or state['offset_days']!=30 or len(state['inventory']['entries'])!=TRACKED_FILES:
        raise ValueError('Frozen T+30 registration changed')
    repo=next(r['path'] for r in json.loads((base/'examples/phase5_2/replay_sources.example.json').read_text()) if r['repository_id']=='apache/commons-cli')
    for kind,oid in [('commit',COMMIT),('tree',TREE)]:
        raw=git(repo,'cat-file',kind,oid)
        if hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=oid:
            raise ValueError('Git object identity mismatch')
    if git(repo,'rev-parse',COMMIT+'^{tree}').decode().strip()!=TREE:raise ValueError('T+30 tree changed')
    actual=[]
    for line in git(repo,'ls-tree','-r','-z',COMMIT).split(b'\0'):
        if line:
            left,name=line.split(b'\t');mode,kind,oid=left.decode().split();actual.append((name.decode(),mode,kind,oid))
    expected=[(r['path'],r['mode'],r['object_type'],r['git_object_id']) for r in state['inventory']['entries']]
    if sorted(actual)!=sorted(expected):raise ValueError('T+30 full inventory mismatch')
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
    if sha(destination/'pom.xml')!=POM:raise ValueError('T+30 historical POM changed')
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
        raise ValueError('Registered T+30 requirements mismatch')
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
    result={k:{baseline:left[k],'t_plus30':right[k],'equal':left[k]==right[k]} for k in fields}
    result['changed_properties']={k:{baseline:left['properties'].get(k),'t_plus30':right['properties'].get(k)}
        for k in sorted(left['properties'].keys()|right['properties'].keys()) if left['properties'].get(k)!=right['properties'].get(k)}
    l={r['path']:r['sha256'] for r in left['source']['source_entries']}
    r={r['path']:r['sha256'] for r in right['source']['source_entries']}
    result['source_changes']=dict(added=sorted(r.keys()-l.keys()),removed=sorted(l.keys()-r.keys()),
        changed=sorted(k for k in l.keys()&r.keys() if l[k]!=r[k]),
        changed_production_java=sorted(k for k in l.keys()&r.keys() if l[k]!=r[k] and k.startswith('src/main/') and k.endswith('.java')))
    result.update(actual_tplus30_effective_pom_sha256=None,method='Independent static parent inheritance, not actual Maven effective models',
        remaining_actual_maven_model='UNKNOWN',compiler_release='8',maven_test_skip=True,explicit_profiles=[])
    return result


def differential_closure(a,plan,baseline):
    """Changed compile-plugin conservative closure relative to successful T0."""
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
        roots.append(row['gav']);edges+=models.closure([root],reason='Changed T+30 compile plugin '+artifact)
    return dict(roots=roots,edges=edges,issues=models.issues,runtime_resolution='UNKNOWN_STATIC_CANDIDATES_ONLY',
        unchanged_plugin_scope='T0 success is reuse evidence only; project metadata and all descriptors independently rechecked')


def audit(base,a,manifest):
    model,models=project_model(a,(TASK/'source/pom.xml').read_bytes(),[r['path'] for r in manifest['source_entries']],['commons-cli',COMMIT])
    t0q=json.loads((seed.RESEARCH/'phase5_2_2_e_0/2026-10-16/prerequisites.json').read_text())
    t0,t0models=project_model(a,(seed.RESEARCH/'phase5_2_2_e_0_2/2026-10-18/inputs/source/pom.xml').read_bytes(),[r['path'] for r in t0q['source_entries']],['commons-cli',t0q['commit_sha']])
    plan=plan_inventory(a,model)
    closure=seed.static_closure(ScopedCache(a),model['dependencies'],model['management'])
    changed=differential_closure(a,plan,t0)
    registered=registered_candidates(base,a,plan)
    missing=set(plan['missing_paths'])|{r['path'] for r in closure['missing']}|{r['path'] for r in registered if not r['present']}
    for gav in TARGETS:missing.update(relative_path(*gav,ext) for ext in ('pom','jar') if relative_path(*gav,ext) not in a.records)
    for issue in changed['issues']+models.issues:
        match=re.search(r'OFFLINE_MISSING: ([A-Za-z0-9_./-]+)',str(issue.get('reason','')))
        if match:missing.add(match[1])
    target=summary(model,models,manifest)
    t0summary=summary(t0,t0models,dict(commit=t0q['commit_sha'],pom_sha256=t0q['pom_sha256'],tracked_files=117,
        source_entries=t0q['source_entries'],production_java_sources=[r['path'] for r in t0q['source_entries'] if r['path'].startswith('src/main/') and r['path'].endswith('.java')]))
    return dict(target=target,t0=t0summary,plan=plan,test_closure=closure,
        changed_compile_plugin_closure=changed,registered_candidates=registered,missing_paths=sorted(missing),
        comparisons=dict(t0_vs_tplus30=comparison(t0summary,target,'t0')),later_common_requirements=later_common_requirements(base,a,model))


def later_common_requirements(base,a,target):
    """Read only later POMs/registered inventories; no other revision recovery."""
    registry=json.loads(gzip.decompress((Path(base)/'examples/phase5_2_1/source_inventory.json.gz').read_bytes()))
    requirements=json.loads((Path(base)/'examples/phase5_2_2_d/requirements.json').read_text())
    repo=next(r['path'] for r in json.loads((Path(base)/'examples/phase5_2/replay_sources.example.json').read_text()) if r['repository_id']=='apache/commons-cli')
    class CachedOnly:
        cache=a.cache;records=a.records
        def get(self,g,art,v,extension='pom',classifier=''):
            path=relative_path(g,art,v,extension,classifier)
            if path not in self.records:raise ValueError('OTHER_REVISION_METADATA_UNAVAILABLE: '+path)
            return a.get(g,art,v,extension,classifier)
    result=[]
    for days in (60,90):
        state=next(r for r in registry['source_states'] if r['repository_id']=='apache/commons-cli' and r['offset_days']==days)
        original=next(r for r in requirements['states'] if r['commit_sha']==state['commit_sha'])
        if git(repo,'rev-parse',state['commit_sha']+'^{tree}').decode().strip()!=state['tree_sha']:
            raise ValueError('Later source state identity changed')
        raw=git(repo,'show',state['commit_sha']+':pom.xml')
        if hashlib.sha256(raw).hexdigest()!=original['pom_sha256']:raise ValueError('Later POM changed')
        model,models=project_model(CachedOnly(),raw,[r['path'] for r in state['inventory']['entries']],['commons-cli',state['commit_sha']])
        candidate={tuple(r['gav']) for r in model['dependencies']}
        expected={tuple(r['gav']) for r in target['dependencies']}
        plugins,unknown=plugin_rows(model)
        result.append(dict(offset_days=days,commit=state['commit_sha'],tree=state['tree_sha'],pom_sha256=original['pom_sha256'],
            tracked_files=len(state['inventory']['entries']),production_java_files=sum(r['path'].startswith('src/main/') and r['path'].endswith('.java') for r in state['inventory']['entries']),
            parent_chain=model['chain'],imports=model['imports'],common_direct_dependencies=[list(g) for g in sorted(candidate&expected)],
            differing_direct_dependencies=[list(g) for g in sorted(candidate-expected)],
            plugin_versions=[r['gav'] for r in plugins],static_model_issues=models.issues,unknown_plugins=unknown,
            actual_effective_model_sha256=None,actual_active_profiles='UNKNOWN_NOT_EXECUTED',
            other_revision_artifacts_acquired=0,source_export_created=False,scope='Read-only common metadata comparison; no build-readiness claim for this revision'))
    return result


def compiler_profile_scope(a,identity):
    """Prove only the scope of a remote build property, never profile activation.

    Commons Parent58 is not a T+30 project parent. The three exact dependency
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
    status='PASS_STATIC_T_PLUS_30_READINESS' if not stop and not after['missing_paths'] and not any(r['blocking'] for r in relevance) else 'PARTIAL'
    if (stop and stop['type']!='BudgetExceeded') or capacity['status']=='BLOCKED_RUNTIME_CACHE_CAPACITY':status='BLOCKED'
    return dict(status=status,issues=relevance,missing_paths=after['missing_paths'],stop=stop,
        actual_effective_model_sha256=None,actual_maven_execution='NOT_EXECUTED',compile_success=False,
        capacity_status=capacity['status'],scope='Static paths/descriptors/closure only; actual model,profiles and classpaths remain unverified')


def verify_successful_builds():
    from tools.verify_compile_e06 import audit as verify_t0
    from tools.verify_compile_e11 import audit as verify_t30
    from tools.verify_compile_e21 import audit as verify_t90
    proofs={}
    for name,path,auditor in [('t0','phase5_2_2_e_0_6/2026-10-18/attempt-1',verify_t0),('tminus30','phase5_2_2_e_1_1/2026-10-18/attempt-1',verify_t30),('tminus90','phase5_2_2_e_2_1/2026-10-18/attempt-1',verify_t90)]:
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
            manifest_sha256=sha(a.root/'dependency_manifest.json'),seed_count=734,seed_manifest_sha256=MANIFEST,
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
