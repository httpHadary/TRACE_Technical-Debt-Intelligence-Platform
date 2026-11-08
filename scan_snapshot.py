#!/usr/bin/env python3
"""Submit one immutable Git snapshot; exports are committed by collect_snapshot."""
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import uuid

import config
import modules
from contracts import atomic_bytes, read_json, safe_id, sha256, source_path, write_json
from sonar_evidence import DATA, Client, poll_task, profile_metadata, require_analysis, source_inventory


def run(cmd, cwd=None, env=None):
    # Never print arguments: a caller might accidentally include a credential.
    return subprocess.run(cmd, cwd=cwd, env=env, check=True, capture_output=True, text=True)


def read_report(path):
    result = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        if '=' not in line:
            raise ValueError('Malformed scanner task report')
        key, value = line.split('=', 1)
        if key in result or not key or not value:
            raise ValueError('Duplicate/empty scanner task property')
        result[key] = value
    if not all(result.get(k) for k in ('ceTaskId', 'projectKey', 'serverUrl')):
        raise ValueError('Incomplete scanner task report')
    return result


def materialize(repo, commit, destination):
    archive = subprocess.run(['git', '-C', str(repo), 'archive', '--format=tar', commit],
                             check=True, capture_output=True).stdout
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar:
            name = member.name.rstrip('/')
            path = destination / source_path(name)
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                path.parent.mkdir(parents=True, exist_ok=True)
                atomic_bytes(path, tar.extractfile(member).read())
            else:
                raise ValueError('Symlink/special file in scanned source snapshot')


def binary_policy(repo, commit, work, inventory):
    if not config.JAVA_BINARIES_PATH:
        if any(p.suffix == '.class' or p.suffix == '.jar' and {'target', 'build'} & set(p.parts)
               for p in work.rglob('*') if p.is_file()):
            raise ValueError('SOURCE_ONLY contains project bytecode')
        (work / '.td-empty-binaries').mkdir()
        return 'SOURCE_ONLY', '.td-empty-binaries', {'build': 'NOT_RUN'}
    proof = read_json(config.COMPILED_EVIDENCE_FILE)
    if (proof.get('commit') != commit or proof.get('source_inventory') != inventory
            or proof.get('tree') != modules._git(repo, ['rev-parse', f'{commit}^{{tree}}']).strip()
            or proof.get('status') != 'PASS' or type(proof.get('returncode')) is not int or proof['returncode'] != 0
            or proof.get('jdk_major') != 17 or not proof.get('command')
            or not re.fullmatch(r'.+@sha256:[0-9a-f]{64}', config.BUILD_IMAGE)
            or proof.get('image') != config.BUILD_IMAGE):
        raise ValueError('Unverified compiled build/source/runtime evidence')
    if sha256(proof['build_log']) != proof.get('build_log_sha256'):
        raise ValueError('Compiled build log checksum mismatch')
    root = Path(config.JAVA_BINARIES_PATH).resolve()
    if not root.is_dir() or not root.is_relative_to(Path(repo).resolve()):
        raise ValueError('Binary root outside repository')
    files = {str(p.relative_to(root)): p for p in root.rglob('*') if p.is_file()}
    if not files or set(files) != set(proof.get('binaries', {})) or not any(p.endswith('.class') for p in files):
        raise ValueError('Incomplete binary inventory')
    for name, p in files.items():
        if p.is_symlink() or not p.resolve().is_relative_to(root) or sha256(p) != proof['binaries'][name]:
            raise ValueError('Binary path/hash mismatch')
        if name.endswith('.class') and (p.stat().st_size < 8 or p.read_bytes()[:4] != bytes.fromhex('cafebabe')):
            raise ValueError('Invalid JVM class')
        atomic_bytes(work / '.td-compiled' / source_path(name), p.read_bytes())
    return 'COMPILED', '.td-compiled', proof


def scanner_settings(project, label, commit, inventory, binaries):
    if not re.fullmatch(r'[A-Za-z0-9_.:-]+', project):
        raise ValueError('Invalid Sonar project key')
    if any(any(c in item['path'] for c in ',=\\') for item in inventory):
        raise ValueError('Source path cannot be represented safely in scanner properties')
    return ('sonar.projectKey=' + project + '\nsonar.projectVersion=' + label +
            '\nsonar.scm.revision=' + commit + '\nsonar.sources=' + ','.join(i['path'] for i in inventory) +
            '\nsonar.tests=\nsonar.test.inclusions=\nsonar.test.exclusions=**/*\n' +
            'sonar.sourceEncoding=UTF-8\nsonar.java.binaries=' + binaries +
            '\nsonar.java.libraries=\nsonar.working.directory=/td-evidence/work\n')


def scanner_command(attempt, image, network):
    attempt=Path(attempt)
    cmd=['docker','run','--rm']
    if network:
        cmd += ['--network', network]
    return cmd + ['-e','SONAR_TOKEN','-e','SONAR_HOST_URL','-v',f'{attempt / "source"}:/usr/src:ro',
                  '-v',f'{attempt / "scanner-work"}:/td-evidence',
                  '-v',f'{attempt / "scanner.properties"}:/td.properties:ro',
                  '-w','/usr/src',image,'-Dproject.settings=/td.properties']


def scan_snapshot(commit, label, client_factory=Client):
    safe_id(label)
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
        raise ValueError('Full immutable commit required')
    if not re.fullmatch(r'.+@sha256:[0-9a-f]{64}', config.SCANNER_IMAGE):
        raise ValueError('Set SONAR_SCANNER_IMAGE to an immutable image@sha256:digest')
    pointer = DATA / f'pending_{label}.json'
    if pointer.exists() or (DATA / f'complete_{label}.json').exists():
        raise ValueError('Attempt already exists; resume exports or use a fresh workspace')
    attempt = (DATA / 'attempts' / f'{label}_{uuid.uuid4().hex}').resolve()
    attempt.mkdir(parents=True, exist_ok=False)
    record = {'label': label, 'repository_id': config.REPOSITORY_ID, 'commit': commit,
              'project_key': config.PROJECT_KEY, 'attempt_dir': str(attempt), 'status': 'STARTED',
              'sonar_url': config.SONAR_URL, 'scanner_sonar_url': config.SONAR_URL_FROM_SCANNER,
              'docker_network': config.DOCKER_NETWORK, 'original_label': label}
    write_json(pointer, record)
    try:
        inventory = source_inventory(config.REPO_PATH, commit)
        work = attempt / 'source'
        materialize(config.REPO_PATH, commit, work)
        mode, binaries, build = binary_policy(config.REPO_PATH, commit, work, inventory)
        for item in inventory:
            if sha256(work / item['path']) != item['sha256']:
                raise ValueError('Materialized Git/source mismatch')
        record.update(source_inventory=inventory, analysis_mode=mode, build_evidence=build)
        client = client_factory(attempt / 'server_before')
        record['pre_scan_metadata'] = profile_metadata(client, config.PROJECT_KEY)
        scanner_work = attempt / 'scanner-work'
        scanner_work.mkdir(mode=0o777)
        scanner_work.chmod(0o777)
        settings = scanner_settings(config.PROJECT_KEY,label,commit,inventory,binaries)
        atomic_bytes(attempt / 'scanner.properties', settings.encode())
        cmd = scanner_command(attempt,config.SCANNER_IMAGE,config.DOCKER_NETWORK)
        record.update(scanner_command=cmd, report_task_path=str(scanner_work / 'work/report-task.txt'))
        write_json(pointer, record)
        env = {**os.environ, 'SONAR_TOKEN': config.SONAR_TOKEN, 'SONAR_HOST_URL': config.SONAR_URL_FROM_SCANNER}
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        log = result.stdout + result.stderr
        if config.SONAR_TOKEN:
            log = log.replace(config.SONAR_TOKEN, '[REDACTED]')
        atomic_bytes(attempt / 'scanner.log', log.encode())
        record['scanner_returncode'] = result.returncode
        report_path = Path(record['report_task_path'])
        if report_path.exists():
            report = read_report(report_path)
            if report['projectKey'] != config.PROJECT_KEY or report['serverUrl'].rstrip('/') != config.SONAR_URL_FROM_SCANNER.rstrip('/'):
                raise ValueError('Scanner report identity mismatch')
            record['ce_task_id'] = report['ceTaskId']
            write_json(pointer, record)
        if result.returncode != 0 or not record.get('ce_task_id'):
            raise ValueError('Scanner process failed or report-task evidence missing')
        task = poll_task(client, record['ce_task_id'], config.PROJECT_KEY)
        record['analysis_id'] = task['analysisId']
        require_analysis(client, config.PROJECT_KEY, task['analysisId'], commit)
        record['status'] = 'CE_SUCCESS'
        write_json(pointer, record)
        return record
    except BaseException as exc:
        record.update(status='FAILED', reason=f'{type(exc).__name__}: {exc}')
        write_json(pointer, record)
        raise


def main():
    if len(sys.argv) != 3:
        raise SystemExit('Usage: scan_snapshot.py COMMIT week_NN')
    from sonar_evidence import workspace_lock
    with workspace_lock():
        scan_snapshot(*sys.argv[1:])


if __name__ == '__main__':
    main()
