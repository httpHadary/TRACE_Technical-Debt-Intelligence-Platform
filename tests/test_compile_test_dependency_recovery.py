"""E.0.3 unit proof: synthetic XML/ZIP only; no network, Maven or containers."""
import copy
import hashlib
import io
import json
from pathlib import Path
import urllib.error
import urllib.request
import zipfile
import pytest
from tools import recover_compile_test_dependencies as e03
from tools.maven_recovery.acquisition import Acquisition, BudgetExceeded, CENTRAL, relative_path
from tools.maven_recovery.model import Models, parse_xml


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(urllib.request.OpenerDirector, 'open', lambda *a, **k: pytest.fail('Network forbidden in unit tests'))


def pom(artifact='seed', body='', group='g', version='1'):
    return f'<project><groupId>{group}</groupId><artifactId>{artifact}</artifactId><version>{version}</version>{body}</project>'.encode()


def jar():
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, 'w') as z:
        z.writestr('fixture.txt', 'synthetic; never executed')
    return raw.getvalue()


@pytest.fixture
def seed(tmp_path):
    a = Acquisition(tmp_path / 'seed')
    raw = pom()
    a.fetch = lambda p, limit: hashlib.sha512(raw).hexdigest().encode() if p.endswith('.sha512') else raw
    a.get('g', 'seed', '1')
    return a.root, list(a.records.values())


def recovery(tmp_path, seed, local=()):
    a = e03.Recovery(tmp_path / 'new', *seed, local=local)
    a.network_enabled = True
    return a


class Response:
    status = 200
    def __init__(self, path, raw):
        self.path, self.raw = path, raw
        self.headers = {'Content-Length': str(len(raw))}
    def geturl(self): return CENTRAL + self.path
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, n):
        raw, self.raw = self.raw[:n], self.raw[n:]
        return raw


def transport(a, raw, missing_checksums=()):
    class Opener:
        def open(self, req, timeout):
            p = req.full_url.removeprefix(CENTRAL)
            assert req.full_url.startswith(CENTRAL) and timeout == 15
            algorithm = p.rsplit('.', 1)[-1]
            if algorithm in missing_checksums:
                raise urllib.error.HTTPError(req.full_url, 404, 'fixture', None, None)
            return Response(p, hashlib.new(algorithm, raw).hexdigest().encode() if algorithm in ('sha512','sha256','sha1') else raw)
    a.opener = Opener()


def test_independent_seed_and_no_ledger_reset(tmp_path, seed):
    source, rows = seed
    before = (source / 'dependency_manifest.json').read_bytes()
    a = recovery(tmp_path, seed)
    p = rows[0]['path']
    assert (a.cache/p).read_bytes() == (source/'repository'/p).read_bytes()
    assert (a.cache/p).stat().st_ino != (source/'repository'/p).stat().st_ino
    assert a.requests == a.bytes == 0
    assert a.get('g','seed','1') == pom()
    assert a.requests == 0
    assert (source/'dependency_manifest.json').read_bytes() == before
    assert a.seal()['prior_request_ledgers'] == dict(D=2000,D1=400,D2=52,D3=112)


@pytest.mark.parametrize('kind', ['bytes','hash','source','checksum','coords'])
def test_seed_tampering_rejected_before_creation(tmp_path, seed, kind):
    source, rows = seed
    rows = copy.deepcopy(rows)
    if kind == 'bytes': (source/'repository'/rows[0]['path']).write_bytes(b'wrong')
    elif kind == 'hash': rows[0]['sha256'] = '0'*64
    elif kind == 'source': rows[0]['source_url'] = 'https://unapproved.invalid/pom'
    elif kind == 'checksum': rows[0]['repository_checksum']['value'] = '0'*128
    else: rows[0]['coordinates'][0] = 'other'
    with pytest.raises((ValueError, FileNotFoundError)):
        recovery(tmp_path, (source,rows))
    assert not (tmp_path/'new').exists()


def test_existing_or_nested_cache_rejected(tmp_path, seed):
    source, rows = seed
    with pytest.raises(ValueError): e03.Recovery(source/'child',source,rows,local=())
    a = recovery(tmp_path, seed)
    with pytest.raises(FileExistsError): e03.Recovery(a.root,source,rows,local=())


def test_checksum_fallback_and_request_accounting(tmp_path, seed):
    a = recovery(tmp_path, seed)
    transport(a,pom('new'),('sha512','sha256'))
    assert a.get('g','new','1') == pom('new')
    assert a.requests == 4
    assert len(a.http_events) == 2
    a.get('g','new','1')
    assert a.requests == 4


def test_local_bytes_require_remote_checksum_before_admission(tmp_path, seed):
    local = tmp_path/'approved'
    name = relative_path('g','local','1')
    p = local/name
    p.parent.mkdir(parents=True)
    p.write_bytes(pom('local'))
    a = recovery(tmp_path,seed,local=(local,))
    transport(a,pom('local'))
    a.get('g','local','1')
    assert a.requests == 1  # only SHA512 downloaded
    assert a.records[name]['origin'] == 'APPROVED_LOCAL_BYTES_FRESH_CENTRAL_CHECKSUM'
    assert a.bytes == 128


def test_untrusted_local_candidate_hash_mismatch_never_admitted(tmp_path,seed):
    local = tmp_path/'approved'
    p = local/relative_path('g','local','1')
    p.parent.mkdir(parents=True)
    p.write_bytes(pom('wrong'))
    a = recovery(tmp_path,seed,local=(local,))
    transport(a,pom('local'))
    with pytest.raises(ValueError,match='checksum mismatch'):a.get('g','local','1')
    assert relative_path('g','local','1') not in a.records


def test_200_request_ceiling_counts_last_attempt_and_no_reset(tmp_path,seed):
    a = recovery(tmp_path,seed)
    a.requests = 199
    transport(a,pom('new'))
    with pytest.raises(BudgetExceeded): a.get('g','new','1')
    assert a.requests == 200
    assert relative_path('g','new','1') not in a.records
    assert json.loads((a.root/'dependency_manifest.json').read_text())['requests'] == 200
    with pytest.raises(BudgetExceeded): a.fetch('g/new/1/new-1.pom',32)
    assert a.requests == 200


@pytest.mark.parametrize('kind',['payload','artifact','disk','time'])
def test_resource_caps_fail_closed_before_read(tmp_path,seed,kind,monkeypatch):
    a = recovery(tmp_path,seed)
    if kind == 'disk':
        with pytest.raises(BudgetExceeded):a.check_disk(e03.MAX_DISK)
        return
    if kind == 'time':
        a.started -= e03.MAX_SECONDS+1
        with pytest.raises(BudgetExceeded):a.fetch('g/new/1/new-1.pom',32)
        assert a.requests == 0
        return
    class Opener:
        def open(self,req,timeout):
            r = Response('g/new/1/new-1.pom',b'')
            r.headers['Content-Length'] = str(20 if kind == 'payload' else e03.MAX_ARTIFACT+1)
            r.read = lambda _:pytest.fail('Over-limit response body must not be read')
            return r
    a.opener=Opener()
    if kind == 'payload':a.bytes=e03.MAX_BYTES-10
    before=a.bytes
    with pytest.raises(BudgetExceeded):a.fetch('g/new/1/new-1.pom',e03.MAX_ARTIFACT)
    assert a.bytes == before


@pytest.mark.parametrize('bad',['../escape','https://wrong.invalid/a','g/x/1/x-1.pom?query'])
def test_transport_path_allowlist(tmp_path,seed,bad):
    a=recovery(tmp_path,seed)
    with pytest.raises(ValueError):a.fetch(bad,100)
    assert a.requests == 0


def test_redirect_response_refused(tmp_path,seed):
    a = recovery(tmp_path,seed)
    class Opener:
        def open(self,*args,**kwargs):
            r=Response('g/new/1/new-1.pom',pom('new'))
            r.geturl=lambda:'https://other.invalid/x'
            return r
    a.opener=Opener()
    with pytest.raises(ValueError,match='identity'):a.get('g','new','1')


def test_jar_integrity_not_executed(tmp_path,seed):
    a=recovery(tmp_path,seed)
    transport(a,jar())
    a.get('g','binary','1','jar')
    assert a.records[relative_path('g','binary','1','jar')]['integrity'] == 'ZIP_CRC'


def test_invalid_jar_rejected(tmp_path,seed):
    a=recovery(tmp_path,seed)
    transport(a,b'not a ZIP')
    with pytest.raises(zipfile.BadZipFile):a.get('g','binary','1','jar')
    assert relative_path('g','binary','1','jar') not in a.records


class MemoryCache:
    def __init__(self,tmp_path,poms):
        self.cache=tmp_path
        self.used_paths=set()
        self.records={}
        for (g,ar,v),raw in poms.items():
            for ext,data in [('pom',raw),('jar',jar())]:
                name=relative_path(g,ar,v,ext)
                p=self.cache/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                self.records[name]=dict(path=name,sha256=hashlib.sha256(data).hexdigest())
    def get(self,g,ar,v,extension='pom',classifier=''):
        name=relative_path(g,ar,v,extension,classifier);self.used_paths.add(name)
        if name not in self.records:raise ValueError('OFFLINE_MISSING: '+name)
        return (self.cache/name).read_bytes()


def dependency(ar,version='1',extra=''):
    return f'<dependency><groupId>g</groupId><artifactId>{ar}</artifactId><version>{version}</version>{extra}</dependency>'


def root_row(ar='root'):
    return Models.dependency(parse_xml(pom(body='<dependencies>'+dependency(ar)+'</dependencies>')).find('m:dependencies/m:dependency',e03.NS),{})


def test_scope_optional_exclusions_and_no_unrelated_plugins(tmp_path):
    deps=dependency('keep')+dependency('test',extra='<scope>test</scope>')+dependency('provided',extra='<scope>provided</scope>')+dependency('optional',extra='<optional>true</optional>')+dependency('excluded')
    a=MemoryCache(tmp_path,{('g','root','1'):pom('root','<dependencies>'+deps+'</dependencies>'),('g','keep','1'):pom('keep')})
    row=root_row();row['exclusions']=[['g','excluded']]
    q=e03.static_closure(a,[row],{})
    assert [r['gav'][1] for r in q['edges']]==['root','keep']
    assert len(q['omitted'])==4
    assert all('plugin' not in n for n in a.used_paths)
    assert all(r['effective_scope']=='test' for r in q['edges'])


def test_root_management_overrides_declared_transitive_version(tmp_path):
    a=MemoryCache(tmp_path,{('g','root','1'):pom('root','<dependencies>'+dependency('keep','2')+'</dependencies>'),('g','keep','3'):pom('keep',version='3')})
    managed=root_row('keep');managed['gav'][2]='3'
    q=e03.static_closure(a,[root_row()],{Models.depkey(managed):managed})
    assert q['edges'][1]['gav']==['g','keep','3']
    assert q['edges'][1]['declared']['gav']==['g','keep','2']
    assert not any('/keep/2/' in p for p in a.used_paths)


def test_parent_bom_metadata_without_downloading_managed_unreferenced_libraries(tmp_path):
    parent=pom('parent','<packaging>pom</packaging><dependencyManagement><dependencies>'+dependency('keep','2')+'</dependencies></dependencyManagement>')
    child=b'<project><parent><groupId>g</groupId><artifactId>parent</artifactId><version>1</version></parent><artifactId>root</artifactId><dependencies><dependency><groupId>g</groupId><artifactId>keep</artifactId></dependency></dependencies></project>'
    a=MemoryCache(tmp_path,{('g','root','1'):child,('g','parent','1'):parent,('g','keep','2'):pom('keep',version='2')})
    q=e03.static_closure(a,[root_row()],{})
    assert q['edges'][1]['gav']==['g','keep','2']
    assert any(m['parent']==['g','parent','1'] for m in q['pom_metadata'])
    assert relative_path('g','parent','1','jar') not in a.used_paths


def test_unknown_dependency_profile_stays_unknown(tmp_path):
    a=MemoryCache(tmp_path,{('g','root','1'):pom('root','<profiles><profile><id>unknown</id><activation><os><family>unknown</family></os></activation><dependencies>'+dependency('not-selected')+'</dependencies></profile></profiles>')})
    q=e03.static_closure(a,[root_row()],{})
    assert q['dependency_profile_uncertainties']
    assert q['unresolved'][0]['kind']=='PROFILE'
    assert not any('not-selected' in p for p in a.used_paths)
    assert q['resolved_runtime_classpath'] is False
    assert q['actual_maven_build_readiness']=='UNKNOWN'


def test_published_frozen_context_matches_actual_maven_failure():
    base=Path(__file__).resolve().parents[1]
    rows=e03.published_seeds(base)
    assert len(rows)==653 and len({r['path'] for r in rows})==653
    failure=json.loads((base/'examples/phase5_2_2_e_0_2/failure_manifest.json').read_text())
    assert sorted(r['path'] for r in failure['missing_artifacts'])==sorted(relative_path(*g,ext) for g in e03.ROOTS for ext in ('pom','jar'))


def test_no_execution_entrypoint_and_old_ledgers_not_modified():
    import inspect
    source=inspect.getsource(e03)
    assert 'subprocess' not in source and 'os.system' not in source and 'docker' not in source
    assert e03.MAX_REQUESTS==200 and e03.MAX_BYTES==64*1024**2
    from tools.recover_phase5_2_2_d_2 import MAX_REQUESTS as d2
    from tools.maven_recovery.continuation import MAX_REQUESTS as d1
    from tools.maven_recovery.acquisition import MAX_REQUESTS as d
    assert (d,d1,d2)==(2000,400,100)


def test_offline_audit_collects_distinct_missing_branches_without_network(tmp_path):
    a=MemoryCache(tmp_path,{('g','root','1'):pom('root','<dependencies>'+dependency('missing-a')+dependency('missing-b')+'</dependencies>')})
    q=e03.static_closure(a,[root_row()],{})
    assert sorted(x['gav'][1] for x in q['missing'])==['missing-a','missing-b']
    assert q['resolved_runtime_classpath'] is False


def test_imported_bom_manages_only_referenced_dependency(tmp_path):
    bom=pom('bom','<packaging>pom</packaging><dependencyManagement><dependencies>'+dependency('keep','2')+dependency('unreferenced','7')+'</dependencies></dependencyManagement>')
    root=pom('root','<dependencyManagement><dependencies>'+dependency('bom',extra='<scope>import</scope><type>pom</type>')+'</dependencies></dependencyManagement><dependencies><dependency><groupId>g</groupId><artifactId>keep</artifactId></dependency></dependencies>')
    a=MemoryCache(tmp_path,{('g','root','1'):root,('g','bom','1'):bom,('g','keep','2'):pom('keep',version='2')})
    q=e03.static_closure(a,[root_row()],{})
    assert [r['gav'] for r in q['edges']]==[['g','root','1'],['g','keep','2']]
    assert not any('unreferenced' in p for p in a.used_paths)
    assert not any('/bom/1/bom-1.jar' in p for p in a.used_paths)
    assert any(m['imports']==[['g','bom','1']] for m in q['models'])


def test_nearest_first_mediation_does_not_fetch_later_conflicting_version(tmp_path):
    a=MemoryCache(tmp_path,{('g','root','1'):pom('root','<dependencies>'+dependency('keep','1')+dependency('other')+'</dependencies>'),('g','keep','1'):pom('keep'),('g','other','1'):pom('other','<dependencies>'+dependency('keep','2')+'</dependencies>')})
    q=e03.static_closure(a,[root_row()],{})
    assert any(x['reason']=='NEAREST_FIRST_MEDIATION' and x['selected']==['g','keep','1'] for x in q['omitted'])
    assert not any('/keep/2/' in p for p in a.used_paths)
