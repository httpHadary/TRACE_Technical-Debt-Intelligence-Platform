"""Task D.1: independent bounded ledger and verified copies; no Maven execution."""
import copy
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
from .acquisition import Acquisition, BudgetExceeded, CENTRAL, parse_xml, relative_path

MAX_REQUESTS = 400
MAX_BYTES = 96 * 1024 * 1024
MAX_ARTIFACT = 32 * 1024 * 1024
MAX_SECONDS = 900
MAX_DISK = 352 * 1024 * 1024


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return h.hexdigest()


class Continuation(Acquisition):
    def __init__(self, root, source, published):
        target = Path(root).absolute()
        self.source = Path(source).absolute()
        if target.is_relative_to(self.source) or self.source.is_relative_to(target):
            raise ValueError('Continuation must be separate from Task D')
        # Check separation before creating anything: even a rejected destination
        # must leave the old cache completely unchanged.
        super().__init__(target)
        self.network_enabled = False
        self.seed_paths = set()
        self.events = []
        old = json.loads((self.source / 'dependency_manifest.json').read_text())
        if old['version'] != 'task-d-acquisition-v1' or old['repository'] != CENTRAL or old['requests'] != 2000:
            raise ValueError('Task D identity/accounting mismatch')
        self.parent = dict(manifest_sha256=digest(self.source / 'dependency_manifest.json'),
                           requests=old['requests'], transferred_bytes=old['transferred_bytes'])
        expected = {r['path']: r for r in published['artifacts']}
        if len(expected) != len(old['artifacts']):
            raise ValueError('Published seed inventory mismatch')
        for row in old['artifacts']:
            path = relative_path(*row['coordinates'], row['extension'], row['classifier'])
            reference = expected.get(path)
            if reference is None or any(row[k] != reference[k] for k in
                    ('coordinates','path','sha256','bytes','extension','classifier','source_url','repository_checksum')):
                raise ValueError('Published seed artifact mismatch')
            p = self.source / 'repository' / path
            if any(v.is_symlink() for v in (p, *p.parents)) or p.stat().st_size > MAX_ARTIFACT:
                raise ValueError('Unsafe seed file')
            raw = p.read_bytes()
            if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('Seed integrity mismatch')
            checksum = row['repository_checksum']
            if checksum['url'] != CENTRAL + path + '.' + checksum['algorithm'] or hashlib.new(checksum['algorithm'],raw).hexdigest() != checksum['value']:
                raise ValueError('Seed repository-checksum mismatch')
            if row['extension'] == 'jar':
                with zipfile.ZipFile(io.BytesIO(raw)) as jar:
                    if sum(i.file_size for i in jar.infolist()) > 128 * 1024 * 1024 or jar.testzip() is not None:
                        raise ValueError('Seed JAR integrity mismatch')
            else:
                pom = parse_xml(raw);ns = {'m':'http://maven.apache.org/POM/4.0.0'}
                for key, value in zip(('groupId','artifactId','version'),row['coordinates']):
                    actual = pom.findtext('m:'+key,namespaces=ns)
                    if actual is None and key != 'artifactId':
                        actual = pom.findtext('m:parent/m:'+key,namespaces=ns)
                    if actual != value:
                        raise ValueError('Seed POM coordinate mismatch')
            target = self.cache / path;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as dest:
                dest.write(raw)
            if digest(target) != row['sha256'] or target.stat().st_ino == p.stat().st_ino:
                raise ValueError('Independent seed copy verification failed')
            self.records[path] = copy.deepcopy(row);self.seed_paths.add(path)
        self.check_disk()
        self.seal()

    def check_disk(self, extra=0):
        size = sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
        if size + extra > MAX_DISK:
            raise BudgetExceeded('Continuation disk cap exceeded')
        return size

    def fetch(self, path, limit):
        if not self.network_enabled:
            raise ValueError('OFFLINE_MISSING: ' + path)
        if not re.fullmatch(r'[A-Za-z0-9_./-]+',path) or '..' in path:
            raise ValueError('Unsafe repository path')
        self.check_disk(MAX_ARTIFACT)
        url = CENTRAL + path
        request = urllib.request.Request(url,headers={'User-Agent':'TechDebt360-Task-D.1-bounded-acquisition'})
        for attempt in range(1,4):
            if self.requests >= MAX_REQUESTS or time.monotonic()-self.started >= MAX_SECONDS:
                raise BudgetExceeded('Task D.1 request/time cap exhausted')
            self.requests += 1
            try:
                response = self.opener.open(request,timeout=15)
                break
            except urllib.error.HTTPError as exc:
                self.events.append(dict(path=path,kind='HTTP',status=exc.code))
                raise
            except (urllib.error.URLError,TimeoutError) as exc:
                self.transport_failures.append(dict(path=path,attempt=attempt,error_type=type(exc).__name__))
                if attempt == 3:
                    raise
                time.sleep(0.25)
        with response:
            if response.status != 200 or response.geturl() != url:
                raise ValueError('Unexpected repository response')
            remaining = MAX_BYTES - self.bytes
            cap = min(limit,remaining)
            length = response.headers.get('Content-Length')
            expected = int(length) if length is not None else None
            if cap <= 0 or (expected is not None and (expected < 0 or expected > cap)):
                raise BudgetExceeded('Task D.1 payload/artifact cap exhausted')
            raw = bytearray()
            while expected is None or len(raw) < expected:
                if time.monotonic()-self.started >= MAX_SECONDS:
                    raise BudgetExceeded('Task D.1 wall-time cap exhausted')
                allowance = min(65536,cap-len(raw))
                if allowance <= 0:
                    raise BudgetExceeded('Cannot prove EOF within payload cap')
                chunk = response.read(allowance)
                if not chunk:
                    if expected is not None and len(raw) != expected:
                        raise ValueError('Truncated artifact response')
                    break
                self.bytes += len(chunk);raw.extend(chunk)
            return bytes(raw)

    def seal(self):
        result = dict(version='task-d1-acquisition-v1',repository=CENTRAL,parent_task_d=self.parent,
            requests=self.requests,transferred_bytes=self.bytes,seed_count=len(self.seed_paths),
            new_count=len(self.records)-len(self.seed_paths),elapsed_seconds=time.monotonic()-self.started,
            limits=dict(memory_bytes=1073741824,cpus=1,max_requests=MAX_REQUESTS,max_transfer_bytes=MAX_BYTES,
                        per_artifact_bytes=MAX_ARTIFACT,max_seconds=MAX_SECONDS,disk_bytes=MAX_DISK),
            cpu_affinity=sorted(os.sched_getaffinity(0)),address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            transport_failures=self.transport_failures,http_events=self.events,
            artifacts=[dict(r,origin='TASK_D_VERIFIED_COPY' if p in self.seed_paths else 'TASK_D1_CENTRAL')
                       for p,r in sorted(self.records.items())],
            project_goals_executed=0,downloaded_artifacts_executed=0,original_cache_modified=False,
            trust_limit='HTTPS and same-origin checksum; no independent publisher signature authentication')
        temp = self.root/'dependency_manifest.json.tmp'
        temp.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        temp.replace(self.root/'dependency_manifest.json')
        return result


class ReadOnlyCache:
    """Reverify a finished D.1 batch without accounting changes or network I/O."""
    def __init__(self, root):
        self.root=Path(root).absolute();self.cache=self.root/'repository'
        manifest=json.loads((self.root/'dependency_manifest.json').read_text())
        if (manifest['version']!='task-d1-acquisition-v1' or manifest['repository']!=CENTRAL
                or not 0<=manifest['requests']<=MAX_REQUESTS
                or not 0<=manifest['transferred_bytes']<=MAX_BYTES
                or manifest['parent_task_d']['requests']!=2000):
            raise ValueError('Continuation ledger identity/limits mismatch')
        self.records={};self.used_paths=set();self.network_enabled=False
        for row in manifest['artifacts']:
            path=relative_path(*row['coordinates'],row['extension'],row['classifier'])
            p=self.cache/path
            if (path!=row['path'] or path in self.records or any(v.is_symlink() for v in (p,*p.parents))
                    or p.stat().st_size!=row['bytes'] or row['bytes']>MAX_ARTIFACT or digest(p)!=row['sha256']):
                raise ValueError('Read-only cache artifact integrity/identity mismatch')
            self.records[path]=row
        if len(self.records)!=manifest['seed_count']+manifest['new_count']:
            raise ValueError('Continuation artifact-count mismatch')

    def get(self, group, artifact, version, extension='pom', classifier=''):
        path=relative_path(group,artifact,version,extension,classifier);self.used_paths.add(path)
        if path not in self.records:
            raise ValueError('OFFLINE_MISSING: '+path)
        p=self.cache/path
        if any(v.is_symlink() for v in (p,*p.parents)) or digest(p)!=self.records[path]['sha256']:
            raise ValueError('Read-only cache changed during audit')
        return p.read_bytes()
