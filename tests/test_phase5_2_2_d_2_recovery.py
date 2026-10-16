"""D.2 regression proof with in-memory transports; no actual network/builds."""
import copy
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request
import pytest
from tools import recover_phase5_2_2_d_2 as d2
from tools.maven_recovery import acquisition as d0
from tools.maven_recovery import continuation as d1


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def fail(*args,**kwargs):raise AssertionError('Unit tests cannot contact repositories')
    monkeypatch.setattr(urllib.request.OpenerDirector,'open',fail)


def pom(artifact='seed'):
    return f'<project><groupId>g</groupId><artifactId>{artifact}</artifactId><version>1</version></project>'.encode()


@pytest.fixture
def seed(tmp_path):
    a=d0.Acquisition(tmp_path/'d1');raw=pom()
    a.fetch=lambda p,limit:hashlib.sha512(raw).hexdigest().encode() if p.endswith('.sha512') else raw
    a.get('g','seed','1');m=a.seal()
    m.update(version='task-d1-acquisition-v1',requests=400,parent_task_d=dict(requests=2000))
    (a.root/'dependency_manifest.json').write_text(json.dumps(m))
    return a.root,m


def test_seed_copies_do_not_reset_or_modify_prior_ledgers(tmp_path,seed):
    source,manifest=seed;before=(source/'dependency_manifest.json').read_bytes()
    a=d2.Recovery(tmp_path/'d2',*seed);src=source/'repository/g/seed/1/seed-1.pom';dst=a.cache/'g/seed/1/seed-1.pom'
    assert src.read_bytes()==dst.read_bytes() and src.stat().st_ino!=dst.stat().st_ino
    assert a.requests==a.bytes==0 and a.get('g','seed','1')==pom()
    assert (source/'dependency_manifest.json').read_bytes()==before
    assert a.parent['task_d_requests']==2000 and a.parent['task_d1_requests']==400
    assert d0.MAX_REQUESTS==2000 and d1.MAX_REQUESTS==400 and d2.MAX_REQUESTS==100


def test_nested_or_existing_destination_never_changes_seed(tmp_path,seed):
    source,_=seed
    with pytest.raises(ValueError):d2.Recovery(source/'nested',*seed)
    assert not (source/'nested').exists()
    with pytest.raises(ValueError):d2.Recovery('/home/hp/tst/research/forecasting_mvp/phase5_2_2_d/2026-10-16/isolated-cache/d2-forbidden',*seed)
    a=d2.Recovery(tmp_path/'d2',*seed)
    with pytest.raises(FileExistsError):d2.Recovery(a.root,*seed)


@pytest.mark.parametrize('change',['bytes','published','checksum','coordinates'])
def test_seed_reverification_rejects_tampering_before_creation(tmp_path,seed,change):
    source,m=seed;m=copy.deepcopy(m)
    if change=='bytes':(source/'repository/g/seed/1/seed-1.pom').write_bytes(b'changed')
    elif change=='published':m['requests']=399
    elif change=='checksum':
        m['artifacts'][0]['repository_checksum']['value']='0'*128
        (source/'dependency_manifest.json').write_text(json.dumps(m))
    else:
        m['artifacts'][0]['coordinates'][1]='other'
        (source/'dependency_manifest.json').write_text(json.dumps(m))
    with pytest.raises((ValueError,FileNotFoundError)):d2.Recovery(tmp_path/'d2',source,m)
    assert not (tmp_path/'d2').exists()


class Response:
    status=200
    def __init__(self,path,raw):self.path=path;self.raw=raw;self.headers={'Content-Length':str(len(raw))}
    def geturl(self):return d0.CENTRAL+self.path
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n):r=self.raw[:n];self.raw=self.raw[n:];return r


def test_checksum_requests_count_and_cached_files_are_not_downloaded(tmp_path,seed):
    a=d2.Recovery(tmp_path/'d2',*seed);a.network_enabled=True;raw=pom('new')
    class Opener:
        def open(self,req,timeout):
            path=req.full_url.removeprefix(d0.CENTRAL)
            if path.endswith(('.sha512','.sha256')):raise urllib.error.HTTPError(req.full_url,404,'fixture',None,None)
            return Response(path,hashlib.sha1(raw).hexdigest().encode() if path.endswith('.sha1') else raw)
    a.opener=Opener();a.get('g','new','1');assert a.requests==4
    a.get('g','new','1');a.get('g','seed','1');assert a.requests==4
    assert a.seal()['new_count']==1


def test_100th_request_cannot_admit_artifact_without_checksum(tmp_path,seed):
    a=d2.Recovery(tmp_path/'d2',*seed);a.network_enabled=True;a.requests=99
    class Opener:
        def open(self,req,timeout):return Response('g/new/1/new-1.pom',pom('new'))
    a.opener=Opener()
    with pytest.raises(d2.BudgetExceeded):a.get('g','new','1')
    assert a.requests==100 and len(a.records)==1
    assert not (a.cache/'g/new/1/new-1.pom').exists()


@pytest.mark.parametrize('kind',['transfer','individual','disk'])
def test_strict_payload_and_disk_caps(tmp_path,seed,kind):
    a=d2.Recovery(tmp_path/'d2',*seed);a.network_enabled=True
    if kind=='disk':
        with pytest.raises(d2.BudgetExceeded):a.check_disk(d2.MAX_DISK)
        return
    class Opener:
        def open(self,req,timeout):
            r=Response('g/new/1/new-1.pom',b'')
            r.headers={'Content-Length':str(10 if kind=='transfer' else d2.MAX_ARTIFACT+1)}
            r.read=lambda _:pytest.fail('Over-limit body cannot be read')
            return r
    a.opener=Opener()
    if kind=='transfer':a.bytes=d2.MAX_BYTES-5
    before=a.bytes
    with pytest.raises(d2.BudgetExceeded):a.fetch('g/new/1/new-1.pom',d2.MAX_ARTIFACT)
    assert a.bytes==before


def test_offline_audit_cannot_contact_repository_or_mutate_ledger(tmp_path,seed):
    a=d2.Recovery(tmp_path/'d2',*seed);a.seal();before=(a.root/'dependency_manifest.json').read_bytes()
    reader=d2.OfflineCache(a.root)
    assert reader.get('g','seed','1')==pom()
    with pytest.raises(ValueError,match='OFFLINE_MISSING'):reader.get('g','missing','1')
    assert (a.root/'dependency_manifest.json').read_bytes()==before


def test_redirect_rejected_and_retries_counted(tmp_path,seed,monkeypatch):
    a=d2.Recovery(tmp_path/'d2',*seed);a.network_enabled=True
    class Redirect:
        def open(self,*args,**kwargs):
            r=Response('g/new/1/new-1.pom',b'fixture');r.geturl=lambda:'https://unapproved.example/artifact'
            return r
    a.opener=Redirect()
    with pytest.raises(ValueError,match='response'):a.fetch('g/new/1/new-1.pom',100)
    class Timeout:
        def open(self,*args,**kwargs):raise urllib.error.URLError('fixture timeout')
    a.opener=Timeout();monkeypatch.setattr(d2.time,'sleep',lambda _:None)
    with pytest.raises(urllib.error.URLError):a.fetch('g/new/1/new-1.pom',100)
    assert a.requests==4 and len(a.transport_failures)==3


def test_integrity_failure_is_not_a_static_closure_pass(tmp_path,seed):
    a=d2.Recovery(tmp_path/'d2',*seed);a.network_enabled=True
    class Opener:
        def open(self,req,timeout):
            path=req.full_url.removeprefix(d0.CENTRAL)
            return Response(path,b'0'*128 if path.endswith('.sha512') else pom('new'))
    a.opener=Opener()
    with pytest.raises(ValueError,match='checksum mismatch'):a.get('g','new','1')
    assert len(a.records)==1 and not (a.cache/'g/new/1/new-1.pom').exists()


def test_published_frontier_and_readiness_preserve_frozen_identities():
    base=Path(__file__).resolve().parents[1];out=base/'examples/phase5_2_2_d_2'
    m=json.loads((out/'dependency_manifest.json').read_text());q=json.loads((out/'requirements.json').read_text())
    f=json.loads((out/'frontier_comparison.json').read_text());matrix=json.loads((out/'compile_readiness_matrix.json').read_text())
    assert m['seed_count']==611 and m['new_count']==13 and m['requests']==52
    assert m['parent_ledgers']['task_d1_requests']==400 and m['parent_ledgers']['task_d_requests']==2000
    assert m['limits']['requests']==100 and m['transferred_bytes']<=32*1024*1024
    assert m['limits']['disk_bytes']==256*1024*1024 and m['limits']['seconds']==600
    assert m['address_space_limit_bytes']==1073741824 and len(m['cpu_affinity'])==1
    assert f['status']=='PASS_STATIC_CLOSURE_COMPLETE' and f['after']==[] and len(f['resolved'])==2
    assert d2.static_status(q)=='PASS_STATIC_CLOSURE_COMPLETE'
    assert len(matrix)==6 and all(s['offline_build_readiness']=='UNKNOWN' for s in matrix)
    assert all(s['static_closure_status']=='PASS_STATIC_CLOSURE_COMPLETE' for s in matrix)
    assert all(s['missing_paths']==[] and s['unknown_profile_count']>0 for s in matrix)
    old=json.loads((base/'examples/phase5_2_2_d_1/compile_readiness_matrix.json').read_text())
    identity=lambda s:(s['commit_sha'],s['tree_sha'],s['pom_sha256'],s['offset_days'])
    assert {identity(s) for s in matrix}=={identity(s) for s in old}
    assert not list(out.rglob('*.pom')) and not list(out.rglob('*.jar'))
    for name,h in json.loads((out/'manifest.json').read_text())['artifacts'].items():
        assert d2.digest(out/name)==h


def test_static_completeness_never_claims_effective_model_or_build_readiness():
    q=dict(missing_paths=[],unresolved=[dict(kind='PROFILE',reason='UNKNOWN')],states=[dict(plugins=[])],offline_build_readiness='UNKNOWN')
    assert d2.static_status(q)=='PASS_STATIC_CLOSURE_COMPLETE'
    assert q['offline_build_readiness']=='UNKNOWN'
    q['missing_paths']=['g/missing/1/missing-1.pom'];assert d2.static_status(q)=='PARTIAL'
    q['missing_paths']=[];q['unresolved'].append(dict(kind='DEPENDENCY',reason='Unresolved version'))
    assert d2.static_status(q)=='PARTIAL'


def test_resource_gate_precedes_any_real_work(tmp_path,monkeypatch):
    monkeypatch.setattr(d2.os,'sched_getaffinity',lambda _: {0,1})
    with pytest.raises(ValueError,match='Require taskset'):d2.execute(tmp_path,tmp_path/'new')
