"""E.0.5 bounded descriptor recovery; no Maven/Java execution or compile retry."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import time
import urllib.error
import urllib.request
import zipfile
from tools import recover_compile_test_dependencies as seed
from tools.maven_recovery.acquisition import BudgetExceeded, CENTRAL, parse_xml, relative_path
from tools.maven_recovery.model import Models, NS, text
from tools.recover_phase5_2_2_d_2 import verify_rows, enforce_process_limits

BASE='2ab7993630135c3921b86c6d8739b92d3afa69a8'
FELIX=('org.apache.felix','maven-bundle-plugin','5.1.9')
WARNINGS=(('log4j','log4j','1.2.12'),('logkit','logkit','1.0.1'),('avalon-framework','avalon-framework','4.1.3'))
RESEARCH=seed.RESEARCH
SOURCE=RESEARCH/'phase5_2_2_e_0_3/2026-10-18/recovery-1'
MANIFEST='73de04d94fe2a1c85fd49f38bfdc14df47e0f93855a8ac5258a10d72f714b113'
CACHE_ID='f4bc6cbab0f8e0bc14557408173290a8453854c35226b40348bffe7a58011daa'
MAX_REQUESTS,MAX_BYTES,MAX_ARTIFACT=120,48*1024**2,32*1024**2
MAX_DISK,MAX_SECONDS=256*1024**2,600
sha,write=seed.sha,seed.write
PHASES=('validate','initialize','generate-sources','process-sources','generate-resources','process-resources',
        'compile','process-classes','generate-test-sources','process-test-sources','generate-test-resources',
        'process-test-resources','test-compile','process-test-classes','test','prepare-package','package',
        'pre-integration-test','integration-test','post-integration-test','verify','install','deploy')


class Recovery(seed.Recovery):
    def __init__(self,root,source,rows,local=seed.LOCAL):
        target=Path(root).absolute()
        for parent in (RESEARCH/'phase5_2_2_e_0_3',RESEARCH/'phase5_2_2_e_0_4'):
            if target.is_relative_to(parent) or parent.is_relative_to(target):raise ValueError('Prior task is read-only')
        super().__init__(root,source,rows,local=local)

    def check_budget(self):
        if self.requests>=MAX_REQUESTS or self.bytes>=MAX_BYTES or time.monotonic()-self.started>=MAX_SECONDS:
            raise BudgetExceeded('E.0.5 request/byte/time ceiling; no continuation authorized')

    def check_disk(self,extra=0):
        size=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
        if size+extra>MAX_DISK:raise BudgetExceeded('E.0.5 disk ceiling')
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
        req = urllib.request.Request(url, headers={'User-Agent': 'TechDebt360-E05-build-plan-metadata'})
        for attempt in range(1, 4):
            if self.requests >= MAX_REQUESTS or time.monotonic() - self.started >= MAX_SECONDS:
                raise BudgetExceeded('E.0.5 request/time ceiling')
            if self.bytes >= MAX_BYTES:
                raise BudgetExceeded('E.0.5 transfer ceiling')
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
                    raise BudgetExceeded('E.0.5 response/payload ceiling')
                raw = bytearray()
                while expected is None or len(raw) < expected:
                    if time.monotonic() - self.started >= MAX_SECONDS:
                        raise BudgetExceeded('E.0.5 wall-time ceiling')
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
        result=dict(version='e05-buildplan-acquisition-v1',base_commit=BASE,repository=CENTRAL,
            target=list(FELIX),seed_count=len(self.seed_paths & self.records.keys()),seed_expected=len(self.seed_paths),
            new_count=len(self.records.keys()-self.seed_paths),requests=self.requests,transferred_bytes=self.bytes,
            elapsed_seconds=time.monotonic()-self.started,prior_request_ledgers=dict(D=2000,D1=400,D2=52,D3=112,E03=56),
            limits=dict(requests=MAX_REQUESTS,response_bytes=MAX_BYTES,artifact_bytes=MAX_ARTIFACT,disk_bytes=MAX_DISK,
                        wall_seconds=MAX_SECONDS,cpus=1,address_space_bytes=1073741824),
            actual_address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],cpu_affinity=sorted(os.sched_getaffinity(0)),
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            http_events=self.http_events,transport_failures=self.transport_failures,local_source_checks=self.local_checks,
            artifacts=[dict(row,origin='E03_VERIFIED_INDEPENDENT_COPY' if name in self.seed_paths else
                            self.origins.get(name,'CENTRAL_HTTPS_DOWNLOAD')) for name,row in sorted(self.records.items())],
            maven_executions=0,java_executions=0,artifact_executions=0,compile_retries=0,
            trust='TLS and same-origin checksum consistency; not independent publisher signatures')
        write(self.root/'dependency_manifest.json',result);self.check_disk()
        return result


class OfflineCache:
    def __init__(self,root):
        self.root=Path(root);self.cache=self.root/'repository'
        m=json.loads((self.root/'dependency_manifest.json').read_text())
        if m['version']!='e05-buildplan-acquisition-v1' or m['repository']!=CENTRAL:raise ValueError('Not E.0.5 cache')
        self.records=verify_rows(root,m);self.used_paths=set()
    get=seed.Acquisition.get
    def fetch(self,path,limit):raise ValueError('OFFLINE_MISSING: '+path)


def verify_seeds(base,source=SOURCE):
    published=base/'examples/phase5_2_2_e_0_3/dependency_manifest.json'
    if sha(published)!=MANIFEST or sha(source/'dependency_manifest.json')!=MANIFEST:raise ValueError('Frozen679 manifest changed')
    m=json.loads(published.read_text())
    if len(m['artifacts'])!=679 or m['requests']!=56:raise ValueError('Frozen679 ledger/population changed')
    rows=verify_rows(source,m)
    identity=''.join(f"{v['sha256']}  {v['bytes']}  {k}\n" for k,v in sorted(rows.items()))
    if hashlib.sha256(identity.encode()).hexdigest()!=CACHE_ID:raise ValueError('Canonical679 cache identity mismatch')
    if {str(p.relative_to(source/'repository')) for p in (source/'repository').rglob('*') if p.is_file()}!=set(rows):
        raise ValueError('Unregistered seed cache paths')
    return list(rows.values())


def jar_member(raw,name,cap=4*1024**2):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        hits=[x for x in z.infolist() if x.filename==name]
        if len(hits)!=1 or hits[0].file_size>cap:raise ValueError('Missing/duplicate/oversized plugin metadata')
        return z.read(hits[0])


def descriptor(a,gav):
    raw=a.get(*gav,'jar');xml=jar_member(raw,'META-INF/maven/plugin.xml');p=parse_xml(xml)
    actual=tuple(p.findtext(k) for k in ('groupId','artifactId','version'))
    if actual!=tuple(gav):raise ValueError('Plugin descriptor coordinate mismatch')
    mojos=[]
    for m in p.findall('mojos/mojo'):
        mojos.append({k:m.findtext(k) for k in ('goal','phase','implementation','requiresDependencyResolution',
                    'requiresDependencyCollection','executePhase','executeGoal','executeLifecycle','requiresProject')})
    return dict(gav=list(gav),jar_sha256=hashlib.sha256(raw).hexdigest(),descriptor_sha256=hashlib.sha256(xml).hexdigest(),
        descriptor_bytes=len(xml),required_java=p.findtext('requiredJavaVersion'),required_maven=p.findtext('requiredMavenVersion'),
        mojos=mojos,declared_descriptor_runtime_dependencies=[{k:d.findtext(k) for k in
            ('groupId','artifactId','version','type','classifier')} for d in p.findall('dependencies/dependency')],
        classes_executed=False,plugin_realm_resolved=False)


def inspect_felix(a):
    models=Models(a);model=models.remote(FELIX)
    p=parse_xml(a.get(*FELIX))
    if text(p,'packaging')!='maven-plugin':raise ValueError('Felix packaging is not maven-plugin')
    data=descriptor(a,FELIX)
    if len([m for m in data['mojos'] if m['goal']=='manifest'])!=1:raise ValueError('Manifest goal unavailable')
    raw=a.get(*FELIX,'jar')
    embedded=jar_member(raw,'META-INF/maven/org.apache.felix/maven-bundle-plugin/pom.properties',16384).decode()
    props={line.split('=',1)[0]:line.split('=',1)[1] for line in embedded.splitlines() if '=' in line and not line.startswith('#')}
    if tuple(props.get(k) for k in ('groupId','artifactId','version'))!=FELIX:raise ValueError('Embedded Maven coordinates mismatch')
    embedded_pom=jar_member(raw,'META-INF/maven/org.apache.felix/maven-bundle-plugin/pom.xml')
    data.update(packaging='maven-plugin',parent_chain=model['chain'],imports=model['imports'],profiles=model['profiles'],
        static_model_issues=models.issues,embedded_pom_sha256=hashlib.sha256(embedded_pom).hexdigest(),
        embedded_pom_equals_external=embedded_pom==a.get(*FELIX),embedded_properties_sha256=hashlib.sha256(embedded.encode()).hexdigest(),
        pom_dependencies=model['dependencies'],dependency_management=list(model['management'].values()),
        required_runtime_downloads_for_observed_descriptor_lookup=[],
        runtime_policy='Descriptor/POM metadata required; Felix goal remains after compile. Runtime graph not acquired or declared resolved.',
        acquired_metadata_paths=sorted(p for p in a.used_paths if p.endswith('.pom')))
    return data


def context(base):
    path=seed.D3/'effective-pom/effective-pom.xml'
    identity=json.loads((base/'examples/phase5_2_2_d_3/effective_model_identity.json').read_text())
    if sha(path)!=identity['effective_pom_sha256']:raise ValueError('T0 effective model changed')
    p=parse_xml(path.read_bytes())
    failure=json.loads((base/'examples/phase5_2_2_e_0_4/failure_manifest.json').read_text())
    if failure['status']!='BLOCKED_DEPENDENCY' or not any(x['fatal_resolution_error'] and
           (x['group'],x['artifact'],x['version'])==FELIX for x in failure['missing_artifacts']):raise ValueError('Observed fatal frontier mismatch')
    return p


def plan_audit(base,a):
    p=context(base);records=[];missing=[];unknown=[]
    managed={(text(x,'groupId','org.apache.maven.plugins'),text(x,'artifactId')):text(x,'version')
             for x in p.findall('m:build/m:pluginManagement/m:plugins/m:plugin',NS)}
    # Jar-packaging default bindings are not dependency-version guesses: use the
    # frozen effective plugin/version declarations, retaining UNKNOWN if absent.
    defaults={'maven-resources-plugin':[('process-resources','resources'),('process-test-resources','testResources')],
        'maven-compiler-plugin':[('compile','compile'),('test-compile','testCompile')],
        'maven-surefire-plugin':[('test','test')], 'maven-jar-plugin':[('package','jar')],
        'maven-install-plugin':[('install','install')], 'maven-deploy-plugin':[('deploy','deploy')]}
    plugins={(text(x,'groupId','org.apache.maven.plugins'),text(x,'artifactId')):x
             for x in p.findall('m:build/m:plugins/m:plugin',NS)}
    for ar in defaults:
        if ('org.apache.maven.plugins',ar) not in plugins:
            unknown.append(dict(plugin=ar,reason='DEFAULT_BINDING_NOT_IN_FROZEN_EFFECTIVE_PLUGIN_LIST'))
    for (group,ar),plugin in plugins.items():
        version=text(plugin,'version') or managed.get((group,ar))
        declared=[]
        for execution in plugin.findall('m:executions/m:execution',NS):
            for goal in execution.findall('m:goals/m:goal',NS):
                declared.append(dict(id=text(execution,'id','default'),phase=text(execution,'phase'),goal=goal.text))
        if not declared and ar not in defaults:continue
        try:relative_path(group,ar,version)
        except ValueError:
            unknown.append(dict(gav=[group,ar,version],reason='UNRESOLVED_EXACT_PLUGIN_VERSION'));continue
        gav=(group,ar,version);d=None
        jarpath=relative_path(*gav,'jar');pompath=relative_path(*gav,'pom')
        needs_descriptor=ar in defaults or any(x['phase'] in PHASES or x['phase'] is None for x in declared)
        if not needs_descriptor:continue
        if jarpath in a.records:
            d=descriptor(a,gav);goals={x['goal']:x for x in d['mojos']}
        else:missing.append(jarpath);goals={}
        if pompath not in a.records:missing.append(pompath)
        for e in declared:
            if e['phase'] is None:
                e['phase']=goals.get(e['goal'],{}).get('phase')
                if e['phase'] is None:unknown.append(dict(gav=list(gav),goal=e['goal'],reason='DEFAULT_PHASE_UNRESOLVED'))
            if d and e['phase'] in PHASES and e['goal'] not in goals:
                unknown.append(dict(gav=list(gav),goal=e['goal'],reason='GOAL_NOT_IN_DESCRIPTOR'))
        records.append(dict(gav=list(gav),executions=declared,default_bindings=defaults.get(ar,[]),
                            descriptor_available=d is not None,pom_available=pompath in a.records,
                            required_as_plan_metadata=True,goal_execution_authorized=False))
    return dict(version='e05-static-plan-v1',tasks='deploy',task_source='Pinned check-buildplan descriptor default; no frozen T0 override',
        plugins=records,missing_paths=sorted(set(missing)),unknown=unknown,
        scope='Static descriptor candidate inventory through deploy, not an executed Maven plan or proof of build readiness',
        actual_plan_resolved=False,full_offline_build_ready=False)


def rat_warnings(a):
    """Search only admitted seed POMs/descriptors. No warning acquisition."""
    targets={g:[] for g in WARNINGS}
    for name,row in sorted(a.records.items()):
        if row['extension']!='pom':continue
        p=parse_xml((a.cache/name).read_bytes())
        for query,kind in [('m:dependencies/m:dependency','DEPENDENCY'),('m:dependencyManagement/m:dependencies/m:dependency','MANAGED_DECLARATION')]:
            for d in p.findall(query,NS):
                gav=tuple(text(d,k) for k in ('groupId','artifactId','version'))
                if gav in targets:targets[gav].append(dict(source_path=name,source_sha256=row['sha256'],kind=kind,scope=text(d,'scope','compile'),optional=text(d,'optional','false'),exclusions=[[text(e,k) for k in ('groupId','artifactId')] for e in d.findall('m:exclusions/m:exclusion',NS)]))
    rat=('org.apache.rat','apache-rat-plugin','0.16.1');d=descriptor(a,rat)
    models=Models(a);queue=[(rat,[])];visited=set();paths={}
    for gav,trail in queue:
        if gav in visited:continue
        visited.add(gav)
        if len(visited)>256:raise ValueError('Bounded RAT metadata graph exceeded')
        if gav in WARNINGS:
            paths[gav]=trail+[list(gav)];continue
        try:model=models.remote(gav)
        except (ValueError,FileNotFoundError):continue
        for dep in model['dependencies']:
            if dep['scope'] in ('compile','runtime') and not dep['optional']:
                queue.append((tuple(dep['gav']),trail+[list(gav)]))
    output=[]
    for gav in WARNINGS:
        output.append(dict(gav=list(gav),pom_present=relative_path(*gav) in a.records,jar_present=relative_path(*gav,'jar') in a.records,
            classification='NONFATAL_WARNING_NO_PROVEN_NEED_FOR_ACQUISITION',acquired=False,
            authoritative_declaration_references=targets[gav],rat_descriptor_sha256=d['descriptor_sha256'],
            observed='E.0.4 RAT completed; warning does not prove a missing required JAR',
            authoritative_candidate_path=paths.get(gav),
            path_status='EXACT_CACHED_POM_DECLARATION_PATH; no Maven mediation/runtime-classpath claim',
            metadata_graph_uncertainties=models.issues))
    return output


def runtime_capacity(rows):
    directories={str(p) for r in rows for p in Path(r['path']).parents}
    payload=sum(r['bytes'] for r in rows);rounded=sum((r['bytes']+4095)//4096*4096 for r in rows)
    total=rounded+len(directories)*4096+16*1024**2
    return dict(status='FITS_128_MIB' if total<=128*1024**2 else 'BLOCKED_RUNTIME_CACHE_CAPACITY',
        artifact_count=len(rows),payload_bytes=payload,rounded_file_bytes=rounded,directory_overhead_bytes=len(directories)*4096,
        metadata_reserve_bytes=16*1024**2,estimated_total_bytes=total,limit_bytes=128*1024**2,
        estimate='4KiB file/directory allocation plus16MiB reserve; actual tmpfs cap remains authoritative')


def run(base,output):
    enforce_process_limits();rows=verify_seeds(base);context(base)
    a=Recovery(output,SOURCE,rows);before=plan_audit(base,a);write(a.root/'plan_before.json',before)
    a.network_enabled=True;stop=None;felix=None
    try:
        # No runtime closure walker: only the fatal plugin + model parents/imports.
        a.get(*FELIX,'pom');a.get(*FELIX,'jar');felix=inspect_felix(a)
    except (BudgetExceeded,ValueError,OSError,urllib.error.URLError,zipfile.BadZipFile) as exc:
        stop=dict(type=type(exc).__name__,reason=str(exc)[:1500])
    finally:
        a.network_enabled=False
        after=plan_audit(base,a);warnings=rat_warnings(a)
        if felix is None:
            try:felix=inspect_felix(a)
            except (ValueError,OSError,urllib.error.URLError) as exc:felix=dict(status='UNAVAILABLE',error=str(exc)[:1200])
        capacity=runtime_capacity(list(a.records.values()))
        exact=all(relative_path(*FELIX,ext) in a.records for ext in ('pom','jar')) and 'descriptor_sha256' in felix
        issues=felix.get('static_model_issues',[])
        status='BLOCKED' if stop and stop['type']!='BudgetExceeded' else ('PARTIAL' if stop else (
            'STATIC_BUILD_PLAN_CLOSURE_COMPLETE' if exact and not after['missing_paths'] and not after['unknown'] and not issues else
            ('RECOVERED_EXACT_FELIX_PLUGIN' if exact else 'PARTIAL')))
        if capacity['status']=='BLOCKED_RUNTIME_CACHE_CAPACITY':status='BLOCKED'
        write(a.root/'plugin_descriptor_evidence.json',felix);write(a.root/'plan_after.json',after)
        write(a.root/'rat_warning_classification.json',warnings);write(a.root/'runtime_cache_capacity.json',capacity)
        write(a.root/'frontier_comparison.json',dict(status=status,stop=stop,exact_plugin_recovered=exact,
            before_missing=before['missing_paths'],after_missing=after['missing_paths'],
            resolved=sorted(set(before['missing_paths'])-set(after['missing_paths'])),unknown=after['unknown'],
            metadata_issues=issues,rat_warnings_still_unresolved=[x['gav'] for x in warnings if not x['pom_present']],
            actual_runtime_plan_resolution='UNVERIFIED',compile_success=False))
        verify_rows(a.root,dict(artifacts=list(a.records.values())))
        assert all(sha(a.cache/r['path'])==r['sha256'] for r in rows)
        a.seal()
    return a


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--audit-only',action='store_true')
    args=p.parse_args();enforce_process_limits();base=Path(__file__).resolve().parents[1]
    if args.audit_only:
        a=OfflineCache(args.output)
        print(json.dumps(dict(felix=inspect_felix(a),plan=plan_audit(base,a),capacity=runtime_capacity(list(a.records.values()))),sort_keys=True,indent=2));return
    a=run(base,args.output)
    print(json.dumps(dict(status=json.loads((a.root/'frontier_comparison.json').read_text())['status'],requests=a.requests,new_artifacts=len(a.records)-len(a.seed_paths),transferred_bytes=a.bytes),indent=2))


if __name__=='__main__':main()
