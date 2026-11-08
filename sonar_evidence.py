"""Exact-task collection, complete pagination and immutable snapshot publication."""
import csv
import io
import os
import re
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import requests

import config
import modules
from contracts import (atomic_bytes, digest, insert_csv, read_csv, read_json, safe_id,
                       sha256, source_path, write_csv, write_json)

DATA = Path('data')


@contextmanager
def workspace_lock():
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / 'run.lock'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        path.unlink()


class Client:
    def __init__(self, raw_dir):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.sequence = 0

    def get(self, endpoint, params=None, text=False):
        response = requests.get(config.SONAR_URL.rstrip('/') + endpoint, params=params,
                                auth=(config.SONAR_TOKEN, ''), timeout=(15, 120))
        response.raise_for_status()
        value = response.text.strip() if text else response.json()
        self.sequence += 1
        write_json(self.raw_dir / f'{self.sequence:04d}.json',
                   {'endpoint': endpoint, 'params': params or {}, 'response': value})
        return value


def paginate(fetch, field, identity):
    rows, pages, seen, expected, page = [], [], set(), None, 1
    while True:
        data = fetch(page)
        paging = data.get('paging', {})
        total = data.get('total', paging.get('total'))
        if type(total) is not int or total < 0 or expected is not None and total != expected:
            raise ValueError('Missing/inconsistent API total')
        if paging and (paging.get('pageIndex') != page or paging.get('pageSize') != 500):
            raise ValueError('Inconsistent API pagination')
        expected = total
        items = data.get(field)
        if not isinstance(items, list) or len(items) != min(500, total - len(rows)):
            raise ValueError('Incomplete/extra API page')
        for item in items:
            key = item.get(identity)
            if not key or key in seen:
                raise ValueError('Missing/duplicate API item')
            seen.add(key)
        rows.extend(items)
        pages.append(data)
        if len(rows) == total:
            return rows, pages
        page += 1


def require_analysis(client, project, analysis_id, commit):
    data = client.get('/api/project_analyses/search', {'project': project, 'ps': 1})
    analyses = data.get('analyses', [])
    if not analyses or analyses[0].get('key') != analysis_id or analyses[0].get('revision') != commit:
        raise ValueError('Current project analysis is not the exact requested commit/analysis; export cannot be recovered safely')
    return analyses[0]


def task_identity(task, task_id, project):
    if task.get('id') != task_id or task.get('componentKey') != project:
        raise ValueError('CE task/project mismatch')
    if task.get('status') == 'SUCCESS' and not task.get('analysisId'):
        raise ValueError('Successful CE task lacks analysis ID')
    return task.get('status')


def poll_task(client, task_id, project, attempts=120, sleep=time.sleep):
    for _ in range(attempts):
        task = client.get('/api/ce/task', {'id': task_id}).get('task', {})
        status = task_identity(task, task_id, project)
        if status == 'SUCCESS':
            return task
        if status not in ('PENDING', 'IN_PROGRESS'):
            raise ValueError(f'CE analysis failed: {status}: {task.get("errorMessage", "")}')
        sleep(5)
    raise TimeoutError('CE task did not complete')


def profile_metadata(client, project):
    server = client.get('/api/server/version', text=True)
    plugins = client.get('/api/plugins/installed').get('plugins', [])
    java = [p for p in plugins if p.get('key') == 'java']
    profiles = [p for p in client.get('/api/qualityprofiles/search', {'project': project}).get('profiles', [])
                if p.get('language') == 'java']
    if not server or len(java) != 1 or not java[0].get('version') or len(profiles) != 1:
        raise ValueError('Incomplete Java analyzer/profile metadata')
    profile = profiles[0]['key']
    rules, pages = paginate(lambda p: client.get('/api/rules/search',
        {'activation': 'true', 'qprofile': profile, 'f': 'actives', 'ps': 500, 'p': p}), 'rules', 'key')
    if not rules:
        raise ValueError('Empty active rule domain')
    canonical = []
    for page in pages:
        for rule in page['rules']:
            activations = [a for a in page.get('actives', {}).get(rule['key'], []) if a.get('qProfile') == profile]
            if len(activations) != 1 or not activations[0].get('severity'):
                raise ValueError('Missing/ambiguous profile activation')
            canonical.append({'rule': rule, 'activation': activations[0]})
    return {'sonarqube_version': server, 'java_analyzer_version': java[0]['version'],
            'quality_profile_id': profile, 'quality_profile_hash': digest(sorted(canonical, key=lambda r:r['rule']['key'])),
            'compatible_rule_domain_version': config.COMPATIBLE_RULE_DOMAIN_VERSION,
            'scanner_image': config.SCANNER_IMAGE}


def source_inventory(repo, commit):
    items = []
    for path in modules.list_files(repo, commit):
        if not modules.is_production_file(path):
            continue
        import subprocess
        result = subprocess.run(['git', '-C', str(repo), 'show', f'{commit}:{path}'], check=True, capture_output=True)
        blob = modules._git(repo, ['rev-parse', f'{commit}:{path}']).strip()
        import hashlib
        items.append({'path': path, 'sha256': hashlib.sha256(result.stdout).hexdigest(),
                      'size': len(result.stdout), 'blob': blob})
    if not items:
        raise ValueError('No production Java source; configure explicit legacy source roots if needed')
    return sorted(items, key=lambda r:r['path'])


def pending(label):
    return read_json(DATA / f'pending_{safe_id(label)}.json')


def collect_snapshot(label, client_factory=Client):
    """Resume exports from the exact completed task; this function never starts a scan."""
    record = pending(label)
    if type(record.get('scanner_returncode')) is not int or record['scanner_returncode'] != 0 or not record.get('ce_task_id'):
        raise ValueError('Incomplete/failed scanner evidence; no automatic rescan')
    attempt = Path(record['attempt_dir'])
    if not attempt.resolve().is_relative_to((DATA / 'attempts').resolve()):
        raise ValueError('Attempt is outside workspace')
    exports = attempt / ('exports_' + uuid.uuid4().hex)
    client = client_factory(exports)
    task = poll_task(client, record['ce_task_id'], record['project_key'])
    analysis = task['analysisId']
    if record.get('analysis_id') not in (None, analysis):
        raise ValueError('Analysis changed for task')
    analysis_record = require_analysis(client, record['project_key'], analysis, record['commit'])
    meta = profile_metadata(client, record['project_key'])
    if meta != record['pre_scan_metadata']:
        raise ValueError('Analyzer/profile changed since scan submission')
    from pull_metrics import METRICS
    components, _ = paginate(lambda p: client.get('/api/measures/component_tree',
        {'component': record['project_key'], 'metricKeys': METRICS, 'qualifiers': 'FIL', 'ps': 500, 'p': p}), 'components', 'key')
    from pull_issues import fetch_all, normalize_issues
    def fetch(params, page):
        return client.get('/api/issues/search', {'componentKeys': record['project_key'], 'ps': 500,
            'p': page, 'statuses': 'OPEN,CONFIRMED,REOPENED,RESOLVED,CLOSED', **params})
    issues = normalize_issues(fetch_all({}, [('severities', ['BLOCKER','CRITICAL','MAJOR','MINOR','INFO']),
                                           ('types', ['BUG','VULNERABILITY','CODE_SMELL'])], fetch=fetch))
    require_analysis(client, record['project_key'], analysis, record['commit'])
    if profile_metadata(client, record['project_key']) != meta:
        raise ValueError('Profile changed during export')
    measured, seen = [], set()
    for c in components:
        path = source_path(c['path'])
        if path in seen:
            raise ValueError('Duplicate measured path')
        seen.add(path)
        values = c.get('measures')
        if not isinstance(values, list) or len({v['metric'] for v in values}) != len(values):
            raise ValueError('Invalid measured values')
        measured.append({'file_path': path, 'language': c.get('language', ''),
                         **{v['metric']: v.get('value', '') for v in values}})
    inventory = source_inventory(config.REPO_PATH, record['commit'])
    if inventory != record['source_inventory']:
        raise ValueError('Source identity changed')
    eligible = [r['path'] for r in inventory]
    if {r['file_path'] for r in measured if modules.is_production_file(r['file_path'])} != set(eligible):
        raise ValueError('Analyzed source coverage incomplete')
    fields = ['file_path','language', *METRICS.split(',')]
    write_csv(exports / 'measures.csv', [{k:r.get(k, '') for k in fields} for r in measured], fields)
    write_json(exports / 'issues.json', issues)
    write_json(exports / 'ce_task.json', task)
    write_json(exports / 'analysis.json', analysis_record)
    write_json(exports / 'metadata.json', meta)
    snapshot = {'label': label, 'commit_hash': record['commit'], 'analysis_key': analysis,
                'analysis_date': task.get('executedAt', ''), 'analysis_mode': record['analysis_mode']}
    metadata = {'label': label, **meta, 'analysis_mode': record['analysis_mode']}
    proof = {**record, 'analysis_id': analysis, 'snapshot': snapshot, 'metadata': metadata,
             'export_dir': str(exports.resolve().relative_to(DATA.resolve())),
             'eligible_paths': eligible, 'status': 'COMPLETE', 'normalization': 'NO_IMPLICIT_ZERO',
             'artifacts': {str(p.resolve().relative_to(DATA.resolve())): sha256(p) for p in attempt.rglob('*') if p.is_file()}}
    proof['measures_sha256'] = sha256(exports / 'measures.csv')
    proof['issues_sha256'] = sha256(exports / 'issues.json')
    # Complete proof is the final commit marker. A crash earlier is resumable without scanning.
    atomic_bytes(DATA / f'measures_{label}.csv', (exports / 'measures.csv').read_bytes())
    atomic_bytes(DATA / f'issues_{label}.json', (exports / 'issues.json').read_bytes())
    upsert_equal(DATA / 'snapshots.csv', snapshot)
    upsert_equal(DATA / 'analysis_metadata.csv', metadata)
    write_json(DATA / f'complete_{label}.json', proof)
    return proof


def export_main():
    import sys
    if len(sys.argv) != 2:
        raise SystemExit('Usage: pull_*.py week_NN')
    label = safe_id(sys.argv[1])
    with workspace_lock():
        if (DATA / f'complete_{label}.json').exists():
            record = read_json(DATA / f'complete_{label}.json')
            verify_snapshot(label, config.REPO_PATH, record['commit'])
        else:
            collect_snapshot(label)


def upsert_equal(path, row):
    if Path(path).exists():
        _, rows = read_csv(path, required=row, key='label')
        existing = [r for r in rows if r['label'] == row['label']]
        if existing:
            if existing[0] != row:
                raise ValueError('Conflicting existing snapshot row')
            return
    insert_csv(path, row)


def verify_snapshot(label, repo, commit):
    proof = read_json(DATA / f'complete_{safe_id(label)}.json')
    if (proof.get('status') != 'COMPLETE' or proof.get('commit') != commit or proof.get('project_key') != config.PROJECT_KEY
            or proof.get('repository_id') != config.REPOSITORY_ID or proof.get('label') != label
            or proof.get('sonar_url') != config.SONAR_URL or proof.get('scanner_sonar_url') != config.SONAR_URL_FROM_SCANNER
            or proof.get('analysis_mode') not in ('COMPILED','SOURCE_ONLY')
            or type(proof.get('scanner_returncode')) is not int or proof['scanner_returncode'] != 0):
        raise ValueError('Snapshot provenance mismatch')
    for path, checksum in proof.get('artifacts', {}).items():
        candidate = DATA / source_path(path)
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(DATA.resolve()) or sha256(candidate) != checksum:
            raise ValueError('Raw evidence checksum mismatch')
    if not proof.get('artifacts') or not proof.get('ce_task_id') or not proof.get('analysis_id'):
        raise ValueError('Incomplete raw/task evidence')
    attempt = Path(proof['attempt_dir'])
    report_path = attempt / 'scanner-work/work/report-task.txt'
    if (not attempt.resolve().is_relative_to((DATA / 'attempts').resolve())
            or Path(proof['report_task_path']) != report_path):
        raise ValueError('Wrong scanner report path')
    from scan_snapshot import read_report, scanner_command, scanner_settings
    report = read_report(report_path)
    if (report['ceTaskId'] != proof['ce_task_id'] or report['projectKey'] != proof['project_key']
            or report['serverUrl'].rstrip('/') != config.SONAR_URL_FROM_SCANNER.rstrip('/')):
        raise ValueError('Original task report disagrees with snapshot')
    exports = DATA / source_path(proof['export_dir'])
    required = [report_path, attempt / 'scanner.log', attempt / 'scanner.properties',
                *[exports / name for name in ('ce_task.json', 'analysis.json', 'metadata.json', 'measures.csv', 'issues.json')]]
    if any(str(p.resolve().relative_to(DATA.resolve())) not in proof['artifacts'] for p in required):
        raise ValueError('Required raw file missing from checksum manifest')
    task = read_json(exports / 'ce_task.json')
    if task_identity(task, proof['ce_task_id'], proof['project_key']) != 'SUCCESS' or task['analysisId'] != proof['analysis_id']:
        raise ValueError('Incomplete CE success evidence')
    analysis_record = read_json(exports / 'analysis.json')
    if analysis_record.get('key') != proof['analysis_id'] or analysis_record.get('revision') != commit:
        raise ValueError('Analysis revision mismatch')
    metadata = read_json(exports / 'metadata.json')
    if metadata != proof['pre_scan_metadata'] or proof['metadata'] != {'label': label, **metadata, 'analysis_mode': proof['analysis_mode']}:
        raise ValueError('Metadata binding mismatch')
    image=metadata.get('scanner_image','')
    if not re.fullmatch(r'.+@sha256:[0-9a-f]{64}',image) or proof['scanner_command'] != scanner_command(attempt,image,proof['docker_network']):
        raise ValueError('Uncontrolled scanner invocation')
    binaries='.td-empty-binaries' if proof['analysis_mode']=='SOURCE_ONLY' else '.td-compiled'
    expected_settings=scanner_settings(proof['project_key'],proof['original_label'],commit,proof['source_inventory'],binaries)
    if (attempt/'scanner.properties').read_text(encoding='utf-8') != expected_settings:
        raise ValueError('Scanner scope/revision/mode differs from recorded source')
    for item in proof['source_inventory']:
        path=attempt/'source'/source_path(item['path'])
        if path.is_symlink() or not path.resolve().is_relative_to((attempt/'source').resolve()) or sha256(path)!=item['sha256']:
            raise ValueError('Scanned source differs from Git inventory')
    if proof['analysis_mode']=='SOURCE_ONLY':
        empty=attempt/'source/.td-empty-binaries'
        if not empty.is_dir() or empty.is_symlink() or any(empty.iterdir()) or proof.get('build_evidence') != {'build':'NOT_RUN'}:
            raise ValueError('SOURCE_ONLY empty binaries/no-build evidence contradicted')
    if proof['snapshot']['analysis_key'] != proof['analysis_id'] or proof['snapshot']['commit_hash'] != commit or proof['snapshot']['analysis_mode'] != proof['analysis_mode']:
        raise ValueError('Snapshot analysis binding mismatch')
    for kind in ('measures', 'issues'):
        suffix = 'csv' if kind == 'measures' else 'json'
        if sha256(DATA / f'{kind}_{label}.{suffix}') != proof[kind + '_sha256']:
            raise ValueError('Changed normalized export')
    if source_inventory(repo, commit) != proof['source_inventory'] or proof['eligible_paths'] != [r['path'] for r in proof['source_inventory']]:
        raise ValueError('Git/source inventory mismatch')
    for filename, field in [('snapshots.csv', 'snapshot'), ('analysis_metadata.csv', 'metadata')]:
        _, rows = read_csv(DATA / filename, key='label')
        found = [r for r in rows if r['label'] == label]
        if found != [proof[field]]:
            raise ValueError('Snapshot/metadata identity mismatch')
    return proof
