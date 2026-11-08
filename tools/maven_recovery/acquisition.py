"""Single-threaded HTTPS-only Maven Central acquisition with fail-closed integrity."""
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
import io

CENTRAL = 'https://repo.maven.apache.org/maven2/'
MAX_BYTES = 256 * 1024 * 1024
MAX_ARTIFACT = 32 * 1024 * 1024
MAX_REQUESTS = 2000
MAX_SECONDS = 1800


class BudgetExceeded(RuntimeError):
    """Fatal acquisition bound: no catch-and-continue fetching after this."""


def relative_path(group, artifact, version, extension='pom', classifier=''):
    values = (group, artifact, version) + ((classifier,) if classifier else ())
    if (not all(isinstance(v, str) and re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', v) for v in values)
            or any('..' in v for v in values) or extension not in ('pom', 'jar')
            or version.upper() in ('LATEST', 'RELEASE') or 'SNAPSHOT' in version.upper()):
        raise ValueError('Exact immutable release coordinates required')
    return '/'.join((group.replace('.', '/'), artifact, version,
                     artifact + '-' + version + ('-' + classifier if classifier else '') + '.' + extension))


def parse_xml(raw):
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('XML entities/DTD forbidden')
    root = ET.fromstring(raw)
    # Maven Central contains valid old namespace-free POMs. Normalize only
    # project models; plugin.xml descriptors deliberately keep their own shape.
    if root.tag == 'project':
        for element in root.iter():
            if isinstance(element.tag, str) and not element.tag.startswith('{'):
                element.tag = '{http://maven.apache.org/POM/4.0.0}' + element.tag
    return root


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Repository redirect forbidden')


class Acquisition:
    def __init__(self, root, resume=False):
        self.root = Path(root).absolute()
        if any(p.is_symlink() for p in (self.root, *self.root.parents)):
            raise ValueError('Symlink cache forbidden')
        if any((p / '.git').exists() for p in (self.root, *self.root.parents)):
            raise ValueError('Dependency cache must remain outside Git')
        for protected in (Path('/home/hp/.m2'), Path('/home/hp/tst/td360_v3_real_operator_v0100/workspace/m2-cache')):
            if self.root.is_relative_to(protected):
                raise ValueError('Existing user caches are read-only')
        if not resume:
            self.root.mkdir(parents=True, mode=0o700, exist_ok=False)
        self.cache = self.root / 'repository'
        self.cache.mkdir(mode=0o700, exist_ok=resume)
        self.started = time.monotonic()
        self.records = {}
        self.used_paths = set()
        self.transport_failures = []
        self.requests = self.bytes = self.previous_seconds = 0
        self.previous_peak_rss_kib = 0
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        if resume:
            old = json.loads((self.root / 'dependency_manifest.json').read_text())
            if old['repository'] != CENTRAL or old['version'] != 'task-d-acquisition-v1':
                raise ValueError('Not a Task D isolated cache')
            self.requests, self.bytes = old['requests'], old['transferred_bytes']
            self.previous_seconds = old['elapsed_seconds']
            self.previous_peak_rss_kib = old['peak_rss_kib']
            self.transport_failures = old.get('transport_failures', [])
            for row in old['artifacts']:
                path = relative_path(*row['coordinates'], row['extension'], row['classifier'])
                p = self.cache / path
                if path != row['path'] or any(v.is_symlink() for v in (p, *p.parents)):
                    raise ValueError('Cache identity changed')
                raw = p.read_bytes()
                if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                    raise ValueError('Cached artifact integrity changed')
                self.records[path] = row

    def fetch(self, path, limit):
        if not re.fullmatch(r'[A-Za-z0-9_./-]+', path) or '..' in path:
            raise ValueError('Unsafe repository path')
        url = CENTRAL + path
        request = urllib.request.Request(url, headers={'User-Agent': 'TechDebt360-Task-D-static-acquisition'})
        response = None
        for attempt in range(1, 4):
            if self.requests >= MAX_REQUESTS or self.previous_seconds + time.monotonic() - self.started > MAX_SECONDS:
                raise BudgetExceeded('Acquisition request/time cap exceeded')
            self.requests += 1
            try:
                response = self.opener.open(request, timeout=15)
                break
            except urllib.error.HTTPError:
                raise
            except (urllib.error.URLError, TimeoutError) as exc:
                self.transport_failures.append(dict(path=path, attempt=attempt, error_type=type(exc).__name__))
                if attempt == 3:
                    raise
                time.sleep(0.25)
        with response:
            if response.status != 200 or response.geturl() != url:
                raise ValueError('Unexpected repository response')
            if response.headers.get('Content-Length') and int(response.headers['Content-Length']) > limit:
                raise BudgetExceeded('Artifact exceeds response cap')
            raw = bytearray()
            while True:
                if self.previous_seconds + time.monotonic() - self.started > MAX_SECONDS:
                    raise BudgetExceeded('Acquisition wall-time cap exceeded')
                chunk = response.read(min(65536, limit - len(raw) + 1))
                if not chunk:
                    break
                self.bytes += len(chunk)
                raw.extend(chunk)
                if len(raw) > limit or self.bytes > MAX_BYTES:
                    raise BudgetExceeded('Acquisition byte cap exceeded')
        return bytes(raw)

    def get(self, group, artifact, version, extension='pom', classifier=''):
        path = relative_path(group, artifact, version, extension, classifier)
        self.used_paths.add(path)
        if path in self.records:
            dest = self.cache / path
            if any(p.is_symlink() for p in (dest, *dest.parents)):
                raise ValueError('Cache symlink introduced')
            raw = dest.read_bytes()
            if hashlib.sha256(raw).hexdigest() != self.records[path]['sha256']:
                raise ValueError('Cached artifact integrity changed')
            return raw
        raw = self.fetch(path, MAX_ARTIFACT)
        checksum = None
        for algorithm in ('sha512', 'sha256', 'sha1'):
            try:
                text = self.fetch(path + '.' + algorithm, 4096).decode('ascii').strip()
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    continue
                raise
            expected = text.split()[0].lower()
            if not re.fullmatch('[0-9a-f]{%d}' % (hashlib.new(algorithm).digest_size * 2), expected):
                raise ValueError('Invalid repository checksum')
            if hashlib.new(algorithm, raw).hexdigest() != expected:
                raise ValueError('Repository checksum mismatch')
            checksum = dict(algorithm=algorithm, value=expected, url=CENTRAL + path + '.' + algorithm)
            break
        if checksum is None:
            raise ValueError('No repository checksum; artifact rejected')
        if extension == 'pom':
            pom = parse_xml(raw)
            ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
            for key, expected in (('groupId', group), ('artifactId', artifact), ('version', version)):
                value = pom.findtext('m:' + key, namespaces=ns)
                if value is None and key != 'artifactId':
                    value = pom.findtext('m:parent/m:' + key, namespaces=ns)
                if value is not None and '${' not in value and value != expected:
                    raise ValueError('POM coordinate mismatch')
        else:
            with zipfile.ZipFile(io.BytesIO(raw)) as jar:
                if sum(i.file_size for i in jar.infolist()) > 128 * 1024 * 1024:
                    raise ValueError('JAR uncompressed byte cap exceeded')
                if jar.testzip() is not None:
                    raise ValueError('JAR CRC failure')
        dest = self.cache / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if any(p.is_symlink() for p in (dest, *dest.parents)) or dest.exists():
            raise ValueError('Refusing cache collision/symlink')
        with dest.open('xb') as stream:
            stream.write(raw)
        self.records[path] = dict(coordinates=[group, artifact, version], extension=extension,
            classifier=classifier, path=path, source_url=CENTRAL + path, bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(), repository_checksum=checksum,
            integrity='XML_AND_COORDINATES' if extension == 'pom' else 'ZIP_CRC')
        self.seal()
        return raw

    def seal(self):
        import resource
        result = dict(version='task-d-acquisition-v1', repository=CENTRAL,
            requests=self.requests, transferred_bytes=self.bytes,
            transport_failures=self.transport_failures,
            elapsed_seconds=self.previous_seconds + time.monotonic() - self.started,
            limits=dict(memory_bytes=1073741824, cpus=1, max_seconds=MAX_SECONDS,
                max_transfer_bytes=MAX_BYTES, max_requests=MAX_REQUESTS, per_artifact_bytes=MAX_ARTIFACT),
            cpu_affinity=sorted(os.sched_getaffinity(0)),
            address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],
            peak_rss_kib=max(self.previous_peak_rss_kib, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            artifacts=sorted(self.records.values(), key=lambda r: r['path']),
            project_goals_executed=0, downloaded_artifacts_executed=0, user_caches_modified=False,
            trust_limit='HTTPS repository identity plus same-origin checksum; no independent publisher-signature verification')
        temp = self.root / 'dependency_manifest.json.tmp'
        temp.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
        temp.replace(self.root / 'dependency_manifest.json')
        return result


class OfflineAcquisition(Acquisition):
    """Audit the remaining exact frontier after the network budget is exhausted."""
    def fetch(self, path, limit):
        raise ValueError('OFFLINE_MISSING: ' + path)
