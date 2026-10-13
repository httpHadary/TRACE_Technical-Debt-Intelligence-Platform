from pathlib import Path
import pytest
import config
import scan_snapshot
import sonar_evidence as evidence
from contracts import read_json, sha256, write_json
from pull_issues import fetch_all


def test_exact_task_roundtrip_and_secret_redaction(sandbox):
    proof = sandbox['collect']()
    assert evidence.verify_snapshot('week_01',sandbox['repo'],sandbox['commit']) == proof
    assert sandbox['docker_calls'] == 1
    assert proof['analysis_mode']=='SOURCE_ONLY'
    assert proof['normalization']=='NO_IMPLICIT_ZERO'
    assert 'sonar.working.directory=/td-evidence/work' in (Path(proof['attempt_dir'])/'scanner.properties').read_text()
    assert 'SECRET_TEST_TOKEN' not in (Path(proof['attempt_dir'])/'scanner.log').read_text()
    assert not any('SECRET_TEST_TOKEN' in v for v in proof['scanner_command'])


def test_partial_export_resumes_without_rescan(sandbox):
    scan_snapshot.scan_snapshot(sandbox['commit'],'week_01',client_factory=sandbox['client'])
    sandbox['fail_endpoint']='/api/issues/search'
    with pytest.raises(OSError):
        evidence.collect_snapshot('week_01',client_factory=sandbox['client'])
    assert not Path('data/complete_week_01.json').exists()
    assert not Path('data/snapshots.csv').exists()
    sandbox['fail_endpoint']=None
    evidence.collect_snapshot('week_01',client_factory=sandbox['client'])
    assert sandbox['docker_calls']==1


@pytest.mark.parametrize('status',['FAILED','CANCELED',None])
def test_ce_failure_not_success(sandbox,status):
    sandbox['ce_status']=status
    with pytest.raises(ValueError):
        sandbox['collect']()
    assert not Path('data/complete_week_01.json').exists()
    assert read_json('data/pending_week_01.json')['status']=='FAILED'


def test_wrong_revision_fails(sandbox):
    sandbox['revision']='b'*40
    with pytest.raises(ValueError):
        sandbox['collect']()


def test_nonzero_scanner_preserves_task_but_not_success(sandbox):
    sandbox['returncode']=1
    with pytest.raises(ValueError):
        sandbox['collect']()
    pending=read_json('data/pending_week_01.json')
    assert pending['ce_task_id']=='task1'
    with pytest.raises(ValueError):
        evidence.collect_snapshot('week_01',client_factory=sandbox['client'])


def test_changed_profile_parameter_fails_export(sandbox):
    scan_snapshot.scan_snapshot(sandbox['commit'],'week_01',client_factory=sandbox['client'])
    sandbox['profile_parameter']='2'
    with pytest.raises(ValueError):
        evidence.collect_snapshot('week_01',client_factory=sandbox['client'])


@pytest.mark.parametrize('mutation',['checksum','report','task','analysis','missing_manifest','normalized',
                                    'source','scope','argv','empty_binaries'])
def test_evidence_tampering_fails(sandbox,mutation):
    proof=sandbox['collect']()
    exports=Path('data')/proof['export_dir']
    path=Path(proof['attempt_dir'])/'scanner.log'
    if mutation=='checksum':
        path.write_text('changed')
    elif mutation=='report':
        path=Path(proof['report_task_path'])
        path.write_text('ceTaskId=WRONG\nprojectKey=p:sample\nserverUrl='+config.SONAR_URL_FROM_SCANNER+'\n')
    elif mutation=='task':
        path=exports/'ce_task.json'
        obj=read_json(path); obj['status']='FAILED'; write_json(path,obj)
    elif mutation=='analysis':
        path=exports/'analysis.json'
        obj=read_json(path); obj['revision']='c'*40; write_json(path,obj)
    elif mutation=='missing_manifest':
        del proof['artifacts'][str(Path(proof['report_task_path']).relative_to(Path('data').resolve()))]
    elif mutation=='source':
        path=Path(proof['attempt_dir'])/'source'/sandbox['paths'][0]
        path.write_text('different source')
    elif mutation=='scope':
        path=Path(proof['attempt_dir'])/'scanner.properties'
        path.write_text(path.read_text().replace('sonar.tests=','sonar.tests=src/test/java'))
    elif mutation=='argv':
        proof['scanner_command'][-2]='scanner:latest'
    elif mutation=='empty_binaries':
        (Path(proof['attempt_dir'])/'source/.td-empty-binaries/A.class').write_bytes(b'fake')
    else:
        Path('data/issues_week_01.json').write_text('[{}]')
    if mutation in ('report','task','analysis','source','scope'):
        proof['artifacts'][str(path.resolve().relative_to(Path('data').resolve()))]=sha256(path)
    write_json('data/complete_week_01.json',proof)
    with pytest.raises(ValueError):
        evidence.verify_snapshot('week_01',sandbox['repo'],sandbox['commit'])


def test_repeated_scan_refused(sandbox):
    sandbox['collect']()
    with pytest.raises(ValueError):
        sandbox['collect']()
    assert sandbox['docker_calls']==1


@pytest.mark.parametrize('issue_api',[False,True])
@pytest.mark.parametrize('defect',['short','duplicate','total','index'])
def test_pagination_fail_closed(issue_api,defect):
    field='issues' if issue_api else 'components'
    def fetch(page):
        items=[{'key':str(n)} for n in range(500)] if page==1 else [{'key':'500'}]
        total=501
        if page==2:
            if defect=='short': items=[]
            if defect=='duplicate': items=[{'key':'0'}]
            if defect=='total': total=502
        return {'total':total,field:items,'paging':{'pageSize':500,'pageIndex':99 if defect=='index' else page,'total':total}}
    with pytest.raises(ValueError):
        if issue_api:
            fetch_all({},[],lambda params,page:fetch(page))
        else:
            evidence.paginate(fetch,field,'key')


def test_zero_result_pages_observed():
    assert evidence.paginate(lambda p:{'total':0,'components':[]},'components','key')[0]==[]
    assert fetch_all({},[],lambda params,p:{'total':0,'issues':[]})==[]


def test_issue_split_cannot_hide_missing_population(monkeypatch):
    import pull_issues
    monkeypatch.setattr(pull_issues,'MAX_RESULTS_PER_QUERY',2)
    def fetch(params,page):
        return {'total':3,'issues':[]} if not params else {'total':1,'issues':[{'key':'duplicate'}]}
    with pytest.raises(ValueError):
        fetch_all({},[('types',['A','B','C'])],fetch)


def test_duplicate_report_property_rejected(tmp_path):
    path=tmp_path/'report.txt'
    path.write_text('ceTaskId=a\nceTaskId=b\nprojectKey=p\nserverUrl=http://localhost\n')
    with pytest.raises(ValueError):
        scan_snapshot.read_report(path)
