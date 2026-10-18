"""E.0.5.1 sequential descriptor-only recovery. Never executes Maven or Java."""
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
from tools import recover_buildplan_plugin as previous
from tools import recover_compile_test_dependencies as seed
from tools.maven_recovery.acquisition import BudgetExceeded, CENTRAL, relative_path, parse_xml
from tools.maven_recovery.model import Models, NS, text
from tools.recover_phase5_2_2_d_2 import verify_rows, enforce_process_limits

BASE='b80afcf305943de5dc1c3efc5bf51b04c2146810'
TASK=seed.RESEARCH/'phase5_2_2_e_0_5_1/2026-10-18'
SOURCE=seed.RESEARCH/'phase5_2_2_e_0_5/2026-10-18/recovery-1'
MANIFEST='b19c9c644d21b9a8700ff1628beb1516aa286f1f4f0b917f2a94dd893868a202'
CACHE_ID='1d56fa167a1a296a680bd22bba4f5223e4d2a90fe099dc38fe8a1703b046120d'
TARGETS=(('org.apache.maven.plugins','maven-surefire-plugin','3.5.0'),
 ('org.apache.maven.plugins','maven-install-plugin','3.1.2'),
 ('org.apache.maven.plugins','maven-deploy-plugin','3.1.2'),
 ('org.cyclonedx','cyclonedx-maven-plugin','2.8.1'),
 ('org.moditect','moditect-maven-plugin','1.2.2.Final'),
 ('org.spdx','spdx-maven-plugin','0.7.4'))
MAX_REQUESTS,MAX_BYTES,MAX_ARTIFACT=160,48*1024**2,32*1024**2
MAX_DISK,MAX_SECONDS=256*1024**2,600
sha,write=seed.sha,seed.write


def owned_output(root, task=TASK):
    """Validate exact phase owner before any write; no inferred or shared roots."""
    root,task=Path(root).absolute(),Path(task).absolute()
    if root!=task/'recovery-1' or root.resolve()!=root or task.resolve()!=task:
        raise ValueError('Exclusive E.0.5.1 output path required')
    if any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('Symlink task path forbidden')
    if any((p/'.git').exists() for p in (root,*root.parents)):
        raise ValueError('Task must remain outside Git')
    owner=json.loads((task/'owner.json').read_text())
    if owner!=dict(phase='E.0.5.1',base=BASE,exclusive_root=str(task)):
        raise ValueError('Task ownership mismatch')
    if root.exists():raise FileExistsError('Non-resumable exclusive acquisition claim')
    return root


def verify_seeds(base,source=SOURCE):
    published=Path(base)/'examples/phase5_2_2_e_0_5/dependency_manifest.json'
    if sha(published)!=MANIFEST or sha(source/'dependency_manifest.json')!=MANIFEST:
        raise ValueError('Frozen682 manifest changed')
    manifest=json.loads(published.read_text())
    if len(manifest['artifacts'])!=682 or manifest['requests']!=12:
        raise ValueError('Frozen682 population/ledger changed')
    rows=verify_rows(source,manifest)
    identity=canonical(rows)
    if identity!=CACHE_ID:raise ValueError('Canonical682 cache identity mismatch')
    paths={str(p.relative_to(source/'repository')) for p in (source/'repository').rglob('*') if p.is_file()}
    if paths!=set(rows):raise ValueError('Unregistered seed paths')
    return list(rows.values())


def canonical(rows):
    return hashlib.sha256(''.join(f"{v['sha256']}  {v['bytes']}  {k}\n" for k,v in sorted(rows.items())).encode()).hexdigest()


class Recovery(seed.Recovery):
    def __init__(self,root,source,rows,local=seed.LOCAL,task=TASK):
        target=owned_output(root,task)
        for name in ('phase5_2_2_e_0_3','phase5_2_2_e_0_4','phase5_2_2_e_0_5'):
            protected=seed.RESEARCH/name
            if target.is_relative_to(protected) or protected.is_relative_to(target):
                raise ValueError('Previous phase is read-only')
        self.task=Path(task).absolute();self.completed=[]
        super().__init__(target,source,rows,local=local)

    def check_budget(self):
        if self.requests>=MAX_REQUESTS or self.bytes>=MAX_BYTES or time.monotonic()-self.started>=MAX_SECONDS:
            raise BudgetExceeded('E.0.5.1 request/byte/time ceiling; no continuation authorized')

    def check_disk(self,extra=0):
        # Includes snapshots, ledgers, reports and all candidate-cache files.
        size=sum(p.stat().st_size for p in self.task.rglob('*') if p.is_file())
        if size+extra>MAX_DISK:raise BudgetExceeded('E.0.5.1 total task storage ceiling')
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
        req = urllib.request.Request(url, headers={'User-Agent': 'TechDebt360-E051-build-plan-metadata'})
        for attempt in range(1, 4):
            if self.requests >= MAX_REQUESTS or time.monotonic() - self.started >= MAX_SECONDS:
                raise BudgetExceeded('E.0.5.1 request/time ceiling')
            if self.bytes >= MAX_BYTES:
                raise BudgetExceeded('E.0.5.1 transfer ceiling')
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
                    raise BudgetExceeded('E.0.5.1 response/payload ceiling')
                raw = bytearray()
                while expected is None or len(raw) < expected:
                    if time.monotonic() - self.started >= MAX_SECONDS:
                        raise BudgetExceeded('E.0.5.1 wall-time ceiling')
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
        result=dict(version='e051-descriptor-acquisition-v1',base_commit=BASE,repository=CENTRAL,
            seed_expected=len(self.seed_paths),seed_count=len(self.seed_paths & self.records.keys()),
            new_count=len(self.records.keys()-self.seed_paths),requests=self.requests,transferred_bytes=self.bytes,
            elapsed_seconds=time.monotonic()-self.started,completed_plugins=self.completed,
            prior_request_ledgers=dict(D=2000,D1=400,D2=52,D3=112,E03=56,E05=12),
            limits=dict(requests=MAX_REQUESTS,response_bytes=MAX_BYTES,artifact_bytes=MAX_ARTIFACT,
                task_storage_bytes=MAX_DISK,wall_seconds=MAX_SECONDS,cpus=1,address_space_bytes=1073741824),
            actual_address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],
            cpu_affinity=sorted(os.sched_getaffinity(0)),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            http_events=self.http_events,transport_failures=self.transport_failures,local_source_checks=self.local_checks,
            artifacts=[dict(row,origin='E05_VERIFIED_INDEPENDENT_COPY' if name in self.seed_paths else
                self.origins.get(name,'CENTRAL_HTTPS_DOWNLOAD')) for name,row in sorted(self.records.items())],
            maven_executions=0,java_executions=0,artifact_executions=0,containers_started=0,
            trust='TLS and same-origin checksums; no independent publisher-signature claim')
        write(self.root/'dependency_manifest.json',result);self.check_disk();return result


class OfflineCache:
    get=seed.Acquisition.get
    def __init__(self,root):
        self.root=Path(root);self.cache=self.root/'repository'
        manifest=json.loads((self.root/'dependency_manifest.json').read_text())
        if manifest['version']!='e051-descriptor-acquisition-v1' or manifest['repository']!=CENTRAL:
            raise ValueError('Not E.0.5.1 cache')
        self.records=verify_rows(root,manifest);self.used_paths=set()
    def fetch(self,path,limit):raise ValueError('OFFLINE_MISSING: '+path)


def expected_goals(row):
    return sorted({x['goal'] for x in row['executions'] if x['phase'] in previous.PHASES or x['phase'] is None}
                  | {x[1] for x in row['default_bindings']})


def inspect_plugin(a,row):
    gav=tuple(row['gav']);rawpom=a.get(*gav)
    if text(parse_xml(rawpom),'packaging')!='maven-plugin':raise ValueError('Not maven-plugin packaging')
    d=previous.descriptor(a,gav);goals=[m['goal'] for m in d['mojos']]
    expected=expected_goals(row)
    if len(goals)!=len(set(goals)) or not set(expected)<=set(goals):
        raise ValueError('Frozen goal absent or duplicate descriptor goals')
    rawjar=a.get(*gav,'jar');prefix=f'META-INF/maven/{gav[0]}/{gav[1]}/'
    embedded=previous.jar_member(rawjar,prefix+'pom.properties',16384)
    properties={line.split('=',1)[0].strip():line.split('=',1)[1].strip() for line in embedded.decode().splitlines()
                if '=' in line and not line.lstrip().startswith(('#','!'))}
    if tuple(properties.get(k) for k in ('groupId','artifactId','version'))!=gav:
        raise ValueError('Embedded pom.properties GAV mismatch')
    modeler=Models(a);used_before=set(a.used_paths);model=modeler.remote(gav)
    # No dependency closure walker is used: Models reads parents/imports as POM data only.
    metadata_paths=sorted(a.used_paths-used_before | {relative_path(*gav)})
    runtime=[]
    for dep in d['declared_descriptor_runtime_dependencies']:
        entry=dict(dep,status='UNKNOWN_RUNTIME_RESOLUTION_NOT_EXECUTED')
        try:
            path=relative_path(dep['groupId'],dep['artifactId'],dep['version'],dep.get('type') or 'jar',dep.get('classifier') or '')
            entry.update(path=path,cache_present=path in a.records)
        except ValueError:entry.update(path=None,cache_present=False)
        runtime.append(entry)
    d.update(packaging='maven-plugin',pom_sha256=hashlib.sha256(rawpom).hexdigest(),
        embedded_properties_sha256=hashlib.sha256(embedded).hexdigest(),embedded_properties_gav_verified=True,
        expected_goals=expected,expected_goals_verified=True,configured_executions=row['executions'],
        default_bindings=row['default_bindings'],parent_chain=model['chain'],imports=model['imports'],
        profiles=model['profiles'],static_model_issues=modeler.issues,metadata_paths=metadata_paths,
        dependency_management=list(model['management'].values()),pom_dependencies=model['dependencies'],
        runtime_requirements=runtime,execution_status='NOT_EXECUTED',
        runtime_classpath_status='UNKNOWN',actual_maven_plan_verified=False)
    return d


def frozen_inventory(base,a):
    before=previous.plan_audit(base,a)
    frozen=json.loads((base/'examples/phase5_2_2_e_0_5/plan_after.json').read_text())
    expected=sorted(relative_path(*g,ext) for g in TARGETS for ext in ('pom','jar'))
    if frozen['missing_paths']!=expected or frozen['unknown'] or json.loads(json.dumps(before))!=frozen:
        raise ValueError('Frozen descriptor frontier/model changed')
    targets={tuple(x['gav']):x for x in before['plugins']}
    if not set(TARGETS)<=set(targets):raise ValueError('Exact plugins absent from frozen plan')
    return before,targets


def summarize(before,after,matrix,stop,capacity):
    issues=[dict(gav=m['gav'],issues=m.get('static_model_issues',[])) for m in matrix if m.get('static_model_issues')]
    incomplete=[m['gav'] for m in matrix if m.get('execution_status')!='NOT_EXECUTED' or m.get('error')]
    status='PASS_STATIC_DESCRIPTOR_CLOSURE'
    if stop or after['missing_paths'] or after['unknown'] or issues or incomplete:status='PARTIAL'
    if (stop and stop['type']!='BudgetExceeded') or capacity['status']=='BLOCKED_RUNTIME_CACHE_CAPACITY':status='BLOCKED'
    return dict(status=status,stop=stop,before_missing=before['missing_paths'],after_missing=after['missing_paths'],
        resolved=sorted(set(before['missing_paths'])-set(after['missing_paths'])),unknown=after['unknown'],
        metadata_issues=issues,incomplete_plugins=incomplete,actual_runtime_plan_resolution='UNVERIFIED',
        compile_success=False,full_offline_build_ready=False)


def run(base,output):
    enforce_process_limits();owned_output(output);rows=verify_seeds(base);previous.context(base)
    a=Recovery(output,SOURCE,rows)
    return acquire_descriptors(base,a,rows)


def acquire_descriptors(base,a,rows):
    before,registry=frozen_inventory(base,a)
    write(a.root/'plan_before.json',before);results=[];stop=None;a.network_enabled=True
    try:
        for gav in TARGETS:
            a.check_budget();a.get(*gav,'pom');a.get(*gav,'jar')
            result=inspect_plugin(a,registry[gav])
            if result['static_model_issues']:raise ValueError('Required plugin model metadata remains unresolved')
            results.append(result);a.completed.append(list(gav));a.seal()
            write(a.root/'completed_plugin_evidence.json',results)
            print(json.dumps(dict(plugin=list(gav),status='DESCRIPTOR_VERIFIED',requests=a.requests)),flush=True)
    except (BudgetExceeded,ValueError,OSError,urllib.error.URLError,zipfile.BadZipFile) as exc:
        stop=dict(type=type(exc).__name__,reason=str(exc)[:1500])
    finally:
        a.network_enabled=False;after=previous.plan_audit(base,a);matrix=[]
        for row in after['plugins']:
            try:matrix.append(inspect_plugin(a,row))
            except (ValueError,OSError,urllib.error.URLError) as exc:
                matrix.append(dict(gav=row['gav'],execution_status='NOT_EXECUTED',error=str(exc)[:1500]))
        capacity=previous.runtime_capacity(list(a.records.values()))
        comparison=summarize(before,after,matrix,stop,capacity)
        write(a.root/'plugin_verification_matrix.json',matrix);write(a.root/'plan_after.json',after)
        write(a.root/'runtime_cache_capacity.json',capacity);write(a.root/'frontier_comparison.json',comparison)
        reverified=verify_rows(a.root,dict(artifacts=list(a.records.values())))
        if any(sha(a.cache/r['path'])!=r['sha256'] for r in rows):raise ValueError('Seed preservation failure')
        a.seal()
        write(a.root/'cache_identity.json',dict(artifact_count=len(reverified),canonical_sha256=canonical(reverified),
            dependency_manifest_sha256=sha(a.root/'dependency_manifest.json'),seed_count=len(rows),
            seed_manifest_sha256=MANIFEST,seed_canonical_sha256=CACHE_ID,independent_copies=True,
            task_storage_bytes=a.check_disk(),all_artifacts_reverified=True))
    return a


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--audit-only',action='store_true')
    args=p.parse_args();enforce_process_limits();base=Path(__file__).resolve().parents[1]
    if args.audit_only:
        a=OfflineCache(args.output)
        print(json.dumps(dict(plan=previous.plan_audit(base,a),plugins=[inspect_plugin(a,r) for r in previous.plan_audit(base,a)['plugins']],
            capacity=previous.runtime_capacity(list(a.records.values())),canonical_sha256=canonical(a.records)),sort_keys=True,indent=2));return
    a=run(base,args.output)
    print(json.dumps(dict(status=json.loads((a.root/'frontier_comparison.json').read_text())['status'],requests=a.requests,
        artifacts=len(a.records),transferred_bytes=a.bytes),sort_keys=True))


if __name__=='__main__':main()
