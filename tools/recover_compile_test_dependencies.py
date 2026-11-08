"""E.0.3: exact observed test roots and their static descriptor closure; no Maven.

One fresh non-resumable acquisition ledger. POMs and JARs are XML/ZIP data only.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import time
import urllib.error
import urllib.request
from tools.maven_recovery.acquisition import Acquisition, BudgetExceeded, CENTRAL, relative_path, parse_xml
from tools.maven_recovery.model import Models, NS, text
from tools.recover_phase5_2_2_d_2 import verify_rows, enforce_process_limits

BASE = 'b3dc64abea6451395cf5dc170fbb95077a09acf0'
ROOTS = (('org.junit.jupiter', 'junit-jupiter-api', '5.11.1'),
         ('org.junit.jupiter', 'junit-jupiter-engine', '5.11.1'),
         ('org.junit.jupiter', 'junit-jupiter-params', '5.11.1'),
         ('commons-io', 'commons-io', '2.17.0'), ('org.mockito', 'mockito-core', '4.11.0'))
RESEARCH = Path('/home/hp/tst/research/forecasting_mvp')
SOURCE = RESEARCH / 'phase5_2_2_e_0_2/2026-10-18/inputs'
D3 = RESEARCH / 'phase5_2_2_d_3/2026-10-16'
LOCAL = (Path('/home/hp/.m2/repository'),
         Path('/home/hp/tst/td360_v3_real_operator_v0100/workspace/m2-cache/repository'))
MAX_REQUESTS, MAX_BYTES, MAX_ARTIFACT = 200, 64 * 1024**2, 32 * 1024**2
MAX_DISK, MAX_SECONDS = 256 * 1024**2, 600
FIELDS = ('coordinates', 'extension', 'classifier', 'path', 'source_url', 'bytes', 'sha256', 'repository_checksum')


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, value):
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    tmp.replace(path)


def published_seeds(base):
    """Bind all 653 records to published D.2 + separate D.3 helper evidence."""
    d2 = json.loads((base / 'examples/phase5_2_2_d_2/dependency_manifest.json').read_text())
    d3 = json.loads((base / 'examples/phase5_2_2_d_3/helper_dependency_manifest.json').read_text())
    if (d2['requests'], d3['requests'], len(d2['artifacts']), len(d3['artifacts'])) != (52, 112, 624, 29):
        raise ValueError('Published seed/ledger identities changed')
    rows = d2['artifacts'] + d3['artifacts']
    if len({r['path'] for r in rows}) != 653:
        raise ValueError('Seed identities overlap')
    return rows


def frozen_context(base):
    identity = json.loads((base / 'examples/phase5_2_2_d_3/effective_model_identity.json').read_text())
    effective = D3 / 'effective-pom/effective-pom.xml'
    if sha(effective) != identity['effective_pom_sha256']:
        raise ValueError('Frozen actual effective POM mismatch')
    if (D3 / 'active-profiles/active-profiles.txt').read_bytes() != (base / 'examples/phase5_2_2_d_3/active-profiles.txt').read_bytes():
        raise ValueError('Frozen active profiles mismatch')
    pom = parse_xml(effective.read_bytes())
    roots = [Models.dependency(e, {}) for e in pom.findall('m:dependencies/m:dependency', NS)]
    if [tuple(r['gav']) for r in roots] != list(ROOTS) or any(r['scope'] != 'test' for r in roots):
        raise ValueError('Observed roots differ from actual T0 effective dependencies')
    failure = json.loads((base / 'examples/phase5_2_2_e_0_2/failure_manifest.json').read_text())
    frontier = sorted(relative_path(*g, ext) for g in ROOTS for ext in ('pom', 'jar'))
    if sorted(r['path'] for r in failure['missing_artifacts']) != frontier:
        raise ValueError('Actual Maven failure frontier changed')
    management = {Models.depkey(r): r for r in
                  (Models.dependency(e, {}) for e in pom.findall('m:dependencyManagement/m:dependencies/m:dependency', NS))}
    return roots, management, dict(effective_pom_sha256=sha(effective),
        source_commit=identity['commit_sha'], source_tree=identity['tree_sha'],
        historical_pom_sha256=identity['pom_sha256'], explicit_profiles=[],
        inherited_profile_evidence='Published D.3 active-profiles.txt; no Maven executed here',
        compiler_release='8', maven_test_skip=True, before_frontier=frontier)


class Recovery(Acquisition):
    def __init__(self, root, source, rows, local=LOCAL):
        root, source = Path(root).absolute(), Path(source).absolute()
        if root.is_relative_to(source) or source.is_relative_to(root):
            raise ValueError('Independent cache required')
        for protected in (*local, *(RESEARCH / n for n in
                ('phase5_2_2_d', 'phase5_2_2_d_1', 'phase5_2_2_d_2', 'phase5_2_2_d_3',
                 'phase5_2_2_e_0', 'phase5_2_2_e_0_1', 'phase5_2_2_e_0_2'))):
            if root.is_relative_to(protected) or protected.is_relative_to(root):
                raise ValueError('Earlier cache/task is read-only')
        verified = verify_rows(source, dict(artifacts=rows))
        super().__init__(root)
        self.seed_paths = set(verified)
        self.local = tuple(Path(p) for p in local)
        self.http_events, self.local_checks, self.origins = [], [], {}
        self.network_enabled = False
        self.seal()
        for name, row in sorted(verified.items()):
            self.check_disk(row['bytes'])
            src, dst = source / 'repository' / name, self.cache / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            with src.open('rb') as left, dst.open('xb') as right:
                shutil.copyfileobj(left, right, 65536)
            if sha(dst) != row['sha256'] or dst.stat().st_ino == src.stat().st_ino:
                raise ValueError('Independent copy failed')
            self.records[name] = copy.deepcopy(row)
        self.seal()

    def check_disk(self, extra=0):
        size = sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
        if size + extra > MAX_DISK:
            raise BudgetExceeded('E.0.3 disk ceiling')
        return size

    def get(self, group, artifact, version, extension='pom', classifier=''):
        name = relative_path(group, artifact, version, extension, classifier)
        raw = super().get(group, artifact, version, extension, classifier)
        if name not in self.seed_paths:
            self.records[name]['origin'] = self.origins.get(name, 'CENTRAL_HTTPS_DOWNLOAD')
            # Enforce concrete coordinate/CRC/provenance validation before final admission.
            verify_rows(self.root, dict(artifacts=[self.records[name]]))
        self.seal()
        return raw

    def fetch(self, path, limit):
        if not self.network_enabled:
            raise ValueError('OFFLINE_MISSING: ' + path)
        if '..' in path or not re.fullmatch(r'[A-Za-z0-9_./-]+', path):
            raise ValueError('Unsafe path')
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
        req = urllib.request.Request(url, headers={'User-Agent': 'TechDebt360-E03-exact-test-roots'})
        for attempt in range(1, 4):
            if self.requests >= MAX_REQUESTS or time.monotonic() - self.started >= MAX_SECONDS:
                raise BudgetExceeded('E.0.3 request/time ceiling')
            if self.bytes >= MAX_BYTES:
                raise BudgetExceeded('E.0.3 transfer ceiling')
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
                    raise BudgetExceeded('E.0.3 response/payload ceiling')
                raw = bytearray()
                while expected is None or len(raw) < expected:
                    if time.monotonic() - self.started >= MAX_SECONDS:
                        raise BudgetExceeded('E.0.3 wall-time ceiling')
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
        result = dict(version='e03-test-dependency-recovery-v1', base_commit=BASE, repository=CENTRAL,
            seed_count=len(self.seed_paths & self.records.keys()), seed_expected=len(self.seed_paths),
            new_count=len(self.records.keys() - self.seed_paths),
            requests=self.requests, transferred_bytes=self.bytes, elapsed_seconds=time.monotonic() - self.started,
            prior_request_ledgers=dict(D=2000, D1=400, D2=52, D3=112),
            limits=dict(requests=MAX_REQUESTS, response_bytes=MAX_BYTES, artifact_bytes=MAX_ARTIFACT,
                        disk_bytes=MAX_DISK, wall_seconds=MAX_SECONDS, cpus=1, process_address_space_bytes=1073741824),
            actual_address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],
            cpu_affinity=sorted(os.sched_getaffinity(0)), peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            http_events=self.http_events, transport_failures=self.transport_failures,
            local_source_checks=self.local_checks,
            artifacts=[dict(r, origin='E02_VERIFIED_INDEPENDENT_COPY' if n in self.seed_paths else self.origins.get(n, 'CENTRAL_HTTPS_DOWNLOAD'))
                       for n, r in sorted(self.records.items())],
            maven_executions=0, downloaded_code_executions=0, compile_attempts=0,
            trust='TLS repository identity and same-origin published checksum; not independent publisher signatures')
        write(self.root / 'dependency_manifest.json', result)
        self.check_disk()
        return result


class OfflineCache:
    def __init__(self, root):
        self.root = Path(root)
        self.cache = self.root / 'repository'
        manifest = json.loads((self.root / 'dependency_manifest.json').read_text())
        if manifest['version'] != 'e03-test-dependency-recovery-v1' or manifest['repository'] != CENTRAL:
            raise ValueError('Not E.0.3 evidence')
        self.records = verify_rows(root, manifest)
        self.used_paths = set()
    get = Acquisition.get
    def fetch(self, path, limit):
        raise ValueError('OFFLINE_MISSING: ' + path)


def static_closure(a, roots, management):
    """BFS nearest/first candidate selection with exact T0 management overrides.

    This remains a descriptor audit, not a resolved Maven runtime classpath.
    Dependency POM test/provided/optional declarations do not propagate.
    """
    models = Models(a)
    queue = [(copy.deepcopy(r), [], (), True) for r in roots]
    selected, visited, edges, omitted, missing = {}, set(), [], [], []
    for row, trail, excluded, direct in queue:
        key = Models.depkey(row)
        declared = copy.deepcopy(row)
        if not direct and key in management:
            row = copy.deepcopy(row)
            managed = management[key]
            row['gav'][2] = managed['gav'][2]
            row['exclusions'] += managed['exclusions']
        gav = tuple(row['gav'])
        relative_path(*gav, row['type'], row['classifier'])
        if row['type'] not in ('jar', 'pom'):
            raise ValueError('Unknown artifact handler: ' + row['type'])
        if key in selected and selected[key] != gav:
            omitted.append(dict(declared=declared, reason='NEAREST_FIRST_MEDIATION', selected=list(selected[key]), trail=trail))
            continue
        selected.setdefault(key, gav)
        visit = (gav, tuple(excluded))
        if visit in visited:
            continue
        visited.add(visit)
        try:
            model = models.remote(gav)
        except ValueError as exc:
            if not str(exc).startswith('OFFLINE_MISSING: '):
                raise
            missing.append(dict(gav=list(gav), path=str(exc).removeprefix('OFFLINE_MISSING: ')))
            continue
        if row['type'] == 'jar':
            try:
                a.get(*gav, 'jar', row['classifier'])
            except ValueError as exc:
                if not str(exc).startswith('OFFLINE_MISSING: '):
                    raise
                missing.append(dict(gav=list(gav), path=str(exc).removeprefix('OFFLINE_MISSING: ')))
        edges.append(dict(gav=list(gav), declared=declared, effective_type=row['type'],
                          effective_scope='test', trail=trail, root=direct, exclusions=[list(v) for v in excluded]))
        for dep in model['dependencies']:
            reason = None
            combined = tuple(excluded) + tuple(tuple(x) for x in row['exclusions'])
            if dep['optional']:
                reason = 'OPTIONAL_NOT_PROPAGATED'
            elif dep['scope'] not in ('compile', 'runtime'):
                reason = 'NON_TRANSITIVE_SCOPE_' + dep['scope']
            elif any(g in ('*', dep['gav'][0]) and ar in ('*', dep['gav'][1]) for g, ar in combined):
                reason = 'EXCLUDED_BY_ANCESTOR'
            if reason:
                omitted.append(dict(parent=list(gav), dependency=dep, reason=reason))
            else:
                queue.append((copy.deepcopy(dep), trail + [list(gav)], combined, False))
    metadata = []
    profile_unknowns = []
    for name in sorted(p for p in a.used_paths if p.endswith('.pom') and p in a.records):
        data = (a.cache / name).read_bytes()
        pom = parse_xml(data)
        dependency_profiles = []
        for p in pom.findall('m:profiles/m:profile', NS):
            if p.find('m:dependencies', NS) is not None or p.find('m:dependencyManagement', NS) is not None:
                # Exact remote model activation is not proven by D.3's project model.
                dependency_profiles.append(text(p, 'id'))
        if dependency_profiles:
            profile_unknowns.append(dict(path=name, profiles=dependency_profiles,
                status='UNKNOWN_REMOTE_DESCRIPTOR_DEPENDENCY_PROFILE_ACTIVATION'))
        parent = pom.find('m:parent', NS)
        metadata.append(dict(path=name, sha256=hashlib.sha256(data).hexdigest(), packaging=text(pom, 'packaging', 'jar'),
            parent=[text(parent, k) for k in ('groupId', 'artifactId', 'version')] if parent is not None else None,
            imported_boms=[Models.dependency(e, {}) for e in pom.findall('m:dependencyManagement/m:dependencies/m:dependency', NS)
                           if text(e, 'scope') == 'import'],
            dependency_management=[Models.dependency(e, {}) for e in pom.findall('m:dependencyManagement/m:dependencies/m:dependency', NS)],
            dependency_profiles=dependency_profiles))
    selected_models = [dict(gav=list(k), chain=v['chain'], imports=v['imports'], dependencies=v['dependencies'],
                            management=list(v['management'].values()), profiles=v['profiles'])
                       for k, v in sorted(models.models.items())]
    return dict(version='e03-static-test-closure-v1', edges=edges, omitted=omitted,
                pom_metadata=metadata, models=selected_models, unresolved=models.issues,
                missing=missing,
                dependency_profile_uncertainties=profile_unknowns, resolved_runtime_classpath=False,
                actual_maven_build_readiness='UNKNOWN', claims_no_compile_success=True)


def run(base, output):
    enforce_process_limits()
    rows = published_seeds(base)
    q = json.loads((RESEARCH / 'phase5_2_2_e_0/2026-10-16/prerequisites.json').read_text())
    if len(q['artifact_records']) != len(rows) or {r['path']: {k:r[k] for k in FIELDS} for r in q['artifact_records']} != {r['path']: {k:r[k] for k in FIELDS} for r in rows}:
        raise ValueError('Published/seed prerequisites differ')
    roots, management, context = frozen_context(base)
    a = Recovery(output, SOURCE, rows)
    before = context['before_frontier']
    if any(p in a.records for p in before):
        raise ValueError('Exact original frontier is not absent')
    write(a.root / 'registration.json', dict(version='e03-registration-v1', **context,
        seed_records_sha256=hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        seed_count=653, local_source_ids=['approved-local-0', 'approved-local-1']))
    a.network_enabled = True
    stop = None
    closure = None
    try:
        # Recover all five observed roots before broadening via descriptor data.
        for gav in ROOTS:
            a.get(*gav, 'pom')
            a.get(*gav, 'jar')
        closure = static_closure(a, roots, management)
    except (BudgetExceeded, ValueError, OSError, urllib.error.URLError) as exc:
        stop = dict(type=type(exc).__name__, reason=str(exc)[:1500])
    finally:
        a.network_enabled = False
        # Independent no-network audit; raw ledger and artifact bytes unchanged.
        try:
            closure = static_closure(OfflineCache(a.root), roots, management)
        except (ValueError, OSError) as exc:
            if closure is None:
                closure = dict(unresolved=[dict(type=type(exc).__name__, reason=str(exc)[:1500])],
                               dependency_profile_uncertainties=[], edges=[], pom_metadata=[])
        unresolved = closure['unresolved'] + closure['dependency_profile_uncertainties'] + closure.get('missing', [])
        after = [p for p in before if p not in a.records]
        status = ('BLOCKED' if stop and stop['type'] != 'BudgetExceeded' else 'PARTIAL') if stop else (
            'PARTIAL' if after or unresolved else 'STATIC_TEST_DEPENDENCY_CLOSURE_COMPLETE')
        receipt = dict(version='e03-frontier-comparison-v1', status=status, stop=stop,
            exact_roots_status='RECOVERED_EXACT_ROOTS' if not after else 'PARTIAL', before=before, after=after,
            resolved=sorted(set(before) & set(a.records)), required_identities=len(closure['edges']),
            missing_or_uncertain=unresolved, maven_build_readiness='UNKNOWN', compile_success=False)
        verify_rows(a.root, dict(artifacts=list(a.records.values())))
        seed_unchanged = all(sha(a.cache / r['path']) == r['sha256'] for r in rows)
        if not seed_unchanged:
            raise ValueError('Seed artifact altered')
        write(a.root / 'closure_evidence.json', closure)
        write(a.root / 'frontier_comparison.json', receipt)
        write(a.root / 'seed_verification.json', dict(status='PASS', seed_count=653,
            all_seed_hashes_match=seed_unchanged, copied_not_hardlinked=True, original_ledgers=dict(D=2000,D1=400,D2=52,D3=112)))
        a.seal()
    return a, receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    p.add_argument('--audit-only', action='store_true')
    args = p.parse_args()
    enforce_process_limits()
    base = Path(__file__).resolve().parents[1]
    if args.audit_only:
        roots, management, _ = frozen_context(base)
        print(json.dumps(static_closure(OfflineCache(args.output), roots, management), sort_keys=True, indent=2))
        return
    a, receipt = run(base, args.output)
    print(json.dumps(dict(status=receipt['status'], requests=a.requests, transferred_bytes=a.bytes,
                         seed_count=len(a.seed_paths), new_count=len(a.records)-len(a.seed_paths)), indent=2))


if __name__ == '__main__':
    main()
