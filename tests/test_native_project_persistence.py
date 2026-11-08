"""Entirely SYNTHETIC native envelopes and tiny local Git objects; no Click scan."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
from threading import Thread

import pytest

from contracts import read_json, write_json, digest
from forecasting_multilanguage.contracts import DOMAIN_FIELDS
from forecasting_multilanguage.native_project import (ARCHIVE_VERSION, METRICS, UNIT, ingest, language, scoped)
from forecasting_mvp.persistence_flow import build, derive, evaluate, load_presentation, verify_presentation
from forecasting_mvp.api import create_server


def run_git(root, *args, day=None):
    env = dict(os.environ, GIT_AUTHOR_NAME='Synthetic', GIT_COMMITTER_NAME='Synthetic', GIT_AUTHOR_EMAIL='synthetic@example.invalid', GIT_COMMITTER_EMAIL='synthetic@example.invalid')
    if day: env.update(GIT_AUTHOR_DATE=day, GIT_COMMITTER_DATE=day)
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, env=env).stdout.decode().strip()


def fixture_archive(tmp_path, languages=('py',), missing=False, equal_times=False):
    """Invented 15-state history with measured states 0, 1, 2, 5, 6, 14."""
    repo, archive = tmp_path/'git', tmp_path/'archive'
    repo.mkdir(); archive.mkdir()
    run_git(repo, 'init', '-q')
    extensions = {'py': 'py', 'java': 'java', 'js': 'jsx', 'ts': 'tsx', 'xml': 'xml'}
    files = sorted('src/file.' + extensions[k] for k in languages)
    commits = []
    for i in range(15):
        for path in files:
            p = repo/path; p.parent.mkdir(exist_ok=True); p.write_text(f'SYNTHETIC code state {i}\n')
        run_git(repo, 'add', '.')
        stamp = f'2024-01-{1 if equal_times and i == 1 else i+1:02d}T00:00:00Z'
        run_git(repo, 'commit', '-qm', f'Synthetic state {i}', day=stamp)
        commits.append((run_git(repo, 'rev-parse', 'HEAD'), run_git(repo, 'rev-parse', 'HEAD^{tree}'), stamp))
    scope = dict(roots=['src'], excluded_paths=[], review_status='REVIEWED_NO_UNRESOLVED_GENERATED_VENDOR_OR_NONCODE', reviewer='Synthetic fixture author')
    programming = sorted(set(languages)-{'xml'})
    reg = dict(repository_id='synthetic-native', family_id='synthetic-family', canonical_url='https://example.invalid/synthetic', tip_sha=commits[-1][0], ref_observed_utc='2024-06-01T00:00:00Z', declared_languages=programming, scope=scope)
    domain = {k: 'synthetic' for k in DOMAIN_FIELDS}
    for k in domain:
        if k.endswith('sha256'): domain[k] = 'a'*64
    domain.update(build_mode='java_compiled' if 'java' in languages else 'source_only', scope_policy_sha256=digest(scope), metric_mode='STANDARD', metric_semantics='native_standard_remediation_minutes',
                  plugins=[dict(key='javascript' if lang in ('js','ts') else lang, language='js' if lang in ('js','ts') else lang, version='synthetic-1', binary_sha256='b'*64) for lang in sorted(set('js' if k in ('js','ts') else k for k in languages))])
    index = dict(version=ARCHIVE_VERSION, source=dict(source_id='synthetic-native-source', kind='SYNTHETIC', description='Invented native envelopes, not a Click export.', permission='Synthetic test-only source rights claim.', provenance='Tiny local Git fixture; no scanner ran.'), registration=reg, domain=domain, horizons=dict(revision_step=[3,4,12], elapsed_day=[30,60,90]), entries=[])
    for i in (0,1,2,5,6,14):
        sha, tree, stamp = commits[i]
        binding = dict(project_key='synthetic:project', analysis_id=f'synthetic-analysis-{i}', revision=sha, source_tree_sha=tree)
        expected = [p for p in files if language(p) in programming]
        analyzed = [dict(path=p, language=language(p)) for p in files]
        docs = dict(
            measures=dict(binding, component=dict(key=binding['project_key'], qualifier='TRK', measures=[dict(metric=k,value=str(10+i if k=='sqale_index' else 2),unit=UNIT) for k in METRICS if not (missing and k=='security_remediation_effort')] + [dict(metric='ncloc',value=str(7*len(languages)),unit='lines'),dict(metric='ncloc_language_distribution',value=';'.join(k+'=7' for k in languages),unit='native_language_distribution')])),
            inventory=dict(binding, git_files=files, production_paths=expected, reviewed_paths=files),
            files=dict(binding,pagination_complete=True,files=analyzed),
            coverage=dict(binding,status='COMPLETE',expected_source_files=len(expected),analyzed_files=len(expected),failed_files=0,unsupported_files=0,analyzed_source_files=[r for r in analyzed if r['path'] in expected]),
            scanner=dict(binding,exit_code=0,sensors_complete=True,ce_task_id=f'task-{i}'),
            ce=dict(binding,task=dict(id=f'task-{i}',status='SUCCESS',analysisId=binding['analysis_id'],componentKey=binding['project_key'])))
        entry = dict(binding,state_utc=stamp,executed_utc='2024-02-01T00:00:00Z',available_utc='2024-02-01T01:00:00Z',retrieved_utc='2024-02-02T00:00:00Z',artifacts={})
        for role, data in docs.items():
            path = f'{i}-{role}.json'; write_json(archive/path,data)
            entry['artifacts'][role] = dict(path=path,sha256=hashlib.sha256((archive/path).read_bytes()).hexdigest())
        index['entries'].append(entry)
    path=tmp_path/'index.json';write_json(path,index)
    return path, archive, repo, index


def source_from(fixture, target='native_total_principal_minutes', last=3):
    path, archive, repo, index = fixture
    selected = deepcopy(index); selected['entries'] = selected['entries'][:last]
    write_json(path,selected)
    return ingest(path, archive, repo, target)


@pytest.mark.parametrize('languages', [('py',),('java',),('js',),('ts',),('js','ts'),('py','js','ts','xml'),('java','py','js','ts')])
def test_synthetic_ingestion_persistence_languages_targets(tmp_path,languages):
    fixture=fixture_archive(tmp_path,languages)
    source=source_from(fixture)
    history,forecasts=derive(source)
    assert [r['stock_minutes'] for r in history]==[14,15,16]
    assert history[-1]['measured_change_minutes']==1
    assert forecasts[0]['prediction_minutes']==16 and forecasts[0]['predicted_change_minutes']==0
    assert forecasts[0]['interval_lower'] is None
    assert forecasts[0]['native']['languages']=={k:7 for k in languages}
    assert forecasts[0]['native']['ancillary_languages']==(['xml'] if 'xml' in languages else [])
    first=build(source,tmp_path/'principal')
    assert first['version']=='persistence.presentation.v2'
    assert verify_presentation(tmp_path/'principal')==first
    sqale=source_from(fixture,'native_sqale_index_minutes')
    sh,sf=derive(sqale)
    assert sf[0]['prediction_minutes']==12
    assert sf[0]['forecast_id']!=forecasts[0]['forecast_id']
    assert sh[0]['target']=='native_sqale_index_minutes'
    assert build(sqale,tmp_path/'sqale')['bundle_id']!=first['bundle_id']


def test_missing_component_retains_sqale_and_latest_missing(tmp_path):
    fixture=fixture_archive(tmp_path,missing=True)
    principal=source_from(fixture)
    sqale=source_from(fixture,'native_sqale_index_minutes')
    assert derive(principal)[1][0]['prediction_minutes'] is None
    assert derive(sqale)[1][0]['prediction_minutes']==12
    assert derive(sqale)[0][-1]['components']['security'] is None


def mutate_artifact(fixture, role, fn):
    path,archive,repo,index=fixture
    ref=index['entries'][0]['artifacts'][role]
    doc=read_json(archive/ref['path']);fn(doc);write_json(archive/ref['path'],doc)
    ref['sha256']=hashlib.sha256((archive/ref['path']).read_bytes()).hexdigest()
    write_json(path,index)


@pytest.mark.parametrize('failure', ['duplicate_metric','number','negative','bool','unit','file','identity','tree','partial','scanner','ce','pagination','analyzer','language','ncloc','mode','domain','inventory','review','scope','missing_distribution'])
def test_rejects_invalid_native_evidence(tmp_path,failure):
    f=fixture_archive(tmp_path)
    if failure=='duplicate_metric': mutate_artifact(f,'measures',lambda d:d['component']['measures'].append(d['component']['measures'][0]))
    elif failure in ('number','negative','bool','unit'):
        values={'number':'NaN','negative':-1,'bool':True,'unit':'hours'}
        mutate_artifact(f,'measures',lambda d:d['component']['measures'][0].update({('unit' if failure=='unit' else 'value'):values[failure]}))
    elif failure=='file': mutate_artifact(f,'measures',lambda d:d['component'].update(qualifier='FIL'))
    elif failure in ('identity','tree'): mutate_artifact(f,'measures',lambda d:d.update({('analysis_id' if failure=='identity' else 'source_tree_sha'):'0'*40}))
    elif failure=='partial': mutate_artifact(f,'coverage',lambda d:d.update(analyzed_files=0))
    elif failure=='scanner': mutate_artifact(f,'scanner',lambda d:d.update(sensors_complete=False))
    elif failure=='ce': mutate_artifact(f,'ce',lambda d:d['task'].update(status='FAILED'))
    elif failure=='pagination': mutate_artifact(f,'files',lambda d:d.update(pagination_complete=False))
    elif failure=='language': mutate_artifact(f,'measures',lambda d:d['component']['measures'][-1].update(value='java=7'))
    elif failure=='ncloc': mutate_artifact(f,'measures',lambda d:d['component']['measures'][-2].update(value='100'))
    elif failure=='inventory': mutate_artifact(f,'inventory',lambda d:d.update(git_files=['invented.py']))
    elif failure=='review': mutate_artifact(f,'inventory',lambda d:d.update(reviewed_paths=[]))
    elif failure=='missing_distribution': mutate_artifact(f,'measures',lambda d:d['component']['measures'].pop())
    else:
        index=f[3]
        if failure=='analyzer': index['domain']['plugins'][0]['language']='java'
        if failure=='mode': index['domain']['metric_mode']='MQR'
        if failure=='domain': index['domain']['scanner_version']='unknown'
        if failure=='scope': index['domain']['scope_policy_sha256']='0'*64
        write_json(f[0],index)
    with pytest.raises(ValueError): ingest(f[0],f[1],f[2],'native_sqale_index_minutes')


def test_raw_hash_duplicate_json_and_invalid_target(tmp_path):
    f=fixture_archive(tmp_path)
    with pytest.raises(ValueError): ingest(f[0],f[1],f[2],'unknown')
    ref=f[3]['entries'][0]['artifacts']['measures'];file=f[1]/ref['path']
    file.write_text('{"component":1,"component":2}')
    with pytest.raises(ValueError,match='digest'): ingest(f[0],f[1],f[2],'native_sqale_index_minutes')
    ref['sha256']=hashlib.sha256(file.read_bytes()).hexdigest();write_json(f[0],f[3])
    with pytest.raises(ValueError,match='Duplicate JSON'): ingest(f[0],f[1],f[2],'native_sqale_index_minutes')


def actual_projection(source,future,forecast,index):
    row=future['observations'][index]
    return dict(forecast_id=forecast['forecast_id'],target=forecast['target'],repository_id=row['repository_id'],origin_observation_id=forecast['origin_observation_id'],domain_id=row['domain_id'],scope_id=row['scope_id'],horizon_unit=forecast['horizon_unit'],horizon=forecast['horizon'],endpoint_revision=row['revision'],endpoint_revision_index=row['revision_index'],observed_utc=row['observed_utc'] if forecast['horizon_unit']=='revision_step' else forecast['endpoint_utc'],components=row['components'],native=row['native'])


def actuals_fixture(tmp_path,target='native_sqale_index_minutes'):
    fixture=fixture_archive(tmp_path)
    source=source_from(fixture,target)
    future=source_from(fixture,target,last=6)
    forecasts=derive(source)[1]
    forecast=next(f for f in forecasts if f['horizon_unit']=='revision_step' and f['horizon']==3)
    row=actual_projection(source,future,forecast,3)
    actuals=dict(version='persistence.actuals.v2',source=source['source'],target=target,unit=UNIT,admission=future['admission'],actuals=[row])
    return source,future,forecasts,actuals


def test_native_actuals_target_isolation_chronology_and_seal(tmp_path,monkeypatch):
    source,future,forecasts,actuals=actuals_fixture(tmp_path)
    assert next(e for e in evaluate(forecasts,actuals) if e['status']=='MEASURED')['actual_minutes']==15
    for field,value in [('target','native_total_principal_minutes'),('horizon_unit','elapsed_day'),('endpoint_revision_index',1),('observed_utc','2024-01-02T00:00:00Z')]:
        bad=deepcopy(actuals);bad['actuals'][0][field]=value
        with pytest.raises(ValueError):evaluate(forecasts,bad)
    actualpath=tmp_path/'actuals.json';write_json(actualpath,actuals)
    import forecasting_mvp.persistence_flow as flow
    original=flow.read_json
    def checked(path):
        if Path(path)==actualpath: assert (tmp_path/'with-actuals/prediction_seal.json').exists()
        return original(path)
    monkeypatch.setattr(flow,'read_json',checked)
    build(source,tmp_path/'with-actuals',actualpath);build(source,tmp_path/'without-actuals')
    assert (tmp_path/'with-actuals/forecasts.json').read_bytes()==(tmp_path/'without-actuals/forecasts.json').read_bytes()
    assert (tmp_path/'with-actuals/prediction_seal.json').read_bytes()==(tmp_path/'without-actuals/prediction_seal.json').read_bytes()
    assert load_presentation(tmp_path/'with-actuals')['evaluation_summary'][0]['target']=='native_sqale_index_minutes'


def test_actual_no_stale_measurement_across_unmeasured_commit(tmp_path):
    source,future,forecasts,actuals=actuals_fixture(tmp_path)
    f=next(f for f in forecasts if f['horizon_unit']=='elapsed_day' and f['horizon']==30)
    actuals['actuals']=[actual_projection(source,future,f,4)]
    # State 6 was measured, but Git state 14 is selected at the 30-day cutoff.
    with pytest.raises(ValueError,match='exact Git state'):evaluate(forecasts,actuals)
    actuals['actuals']=[actual_projection(source,future,f,5)]
    assert any(e['status']=='MEASURED' for e in evaluate(forecasts,actuals))


def test_evidence_tamper_and_source_target_ids(tmp_path):
    f=fixture_archive(tmp_path);source=source_from(f)
    changed=deepcopy(source);changed['observations'][0]['components']['security']=999
    with pytest.raises(ValueError,match='identity'):derive(changed)
    changed=deepcopy(source);changed['target']='native_sqale_index_minutes'
    with pytest.raises(ValueError,match='identity'):derive(changed)
    build(source,tmp_path/'bundle')
    (tmp_path/'bundle/source.json').write_text('{}')
    with pytest.raises(ValueError,match='hash'):verify_presentation(tmp_path/'bundle')


def test_v2_api_and_clis(tmp_path):
    fixture=fixture_archive(tmp_path,('py','js','ts','xml'));source=source_from(fixture,'native_sqale_index_minutes')
    from forecasting_mvp.cli import main
    registry=tmp_path/'registry';registry.mkdir()
    assert main(['persistence-ingest-native','--index',str(fixture[0]),'--archive',str(fixture[1]),'--git',str(fixture[2]),'--target','native_sqale_index_minutes','--out',str(registry/'v2')])==0
    manifest=verify_presentation(registry/'v2')
    server=create_server(registry,port=0);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        conn=http.client.HTTPConnection('127.0.0.1',server.server_port)
        route='/api/mvp/v1/bundles/'+manifest['bundle_id']+'/repositories/synthetic-native'
        for resource in ('history','forecasts?horizon_unit=revision_step&horizon=3','evaluations?horizon_unit=revision_step&horizon=3'):
            conn.request('GET',route+'/'+resource);response=conn.getresponse();rows=json.loads(response.read())
            assert response.status==200 and rows[0]['target']=='native_sqale_index_minutes'
            assert rows[0]['native']['languages']==dict(py=7,js=7,ts=7,xml=7)
        conn.close()
    finally:server.shutdown();server.server_close();thread.join()
    from forecasting_multilanguage.cli import main as mlmain
    path=tmp_path/'source.json'
    assert mlmain(['ingest-native-project','--index',str(fixture[0]),'--archive',str(fixture[1]),'--git',str(fixture[2]),'--target','native_sqale_index_minutes','--output',str(path)])==0
    assert read_json(path)==source
    assert main(['persistence-ingest-native','--index',str(fixture[0]),'--archive',str(fixture[1]),'--git',str(fixture[2]),'--target','unknown','--out',str(tmp_path/'invalid')])==3


def test_java_requires_compiled_domain(tmp_path):
    f=fixture_archive(tmp_path,('java','py'))
    f[3]['domain']['build_mode']='source_only';write_json(f[0],f[3])
    with pytest.raises(ValueError,match='java_compiled'):
        ingest(f[0],f[1],f[2],'native_sqale_index_minutes')


def test_equal_time_observation_is_explicitly_blocked_without_invented_time(tmp_path):
    f=fixture_archive(tmp_path,equal_times=True)
    with pytest.raises(ValueError,match='sharing a UTC second'):
        source_from(f)


def test_changed_actual_native_values_cannot_escape_archive_binding(tmp_path):
    source,future,forecasts,actuals=actuals_fixture(tmp_path)
    altered=deepcopy(actuals);altered['actuals'][0]['components']['maintainability']=999
    with pytest.raises(ValueError,match='binding'):
        evaluate(forecasts,altered)


def test_actuals_cannot_switch_native_project_on_same_git_lineage(tmp_path):
    from forecasting_multilanguage.native_project import validate_admission
    source,future,forecasts,actuals=actuals_fixture(tmp_path)
    admission=actuals['admission']
    for entry,proof in zip(admission['entries'],admission['evidence']):
        entry['project_key']='synthetic:other-project'
        for role,raw in proof.items():
            doc=json.loads(raw);doc['project_key']=entry['project_key']
            if role=='measures':doc['component']['key']=entry['project_key']
            if role=='ce':doc['task']['componentKey']=entry['project_key']
            proof[role]=json.dumps(doc)
            entry['artifacts'][role]['sha256']=hashlib.sha256(proof[role].encode()).hexdigest()
    actuals['actuals'][0]['native']=validate_admission(admission)[3]['native']
    with pytest.raises(ValueError,match='project differs'):
        evaluate(forecasts,actuals)


def test_scoped_git_submodule_cannot_claim_complete_source_coverage(tmp_path):
    f=fixture_archive(tmp_path)
    repo=f[2];index=f[3]
    run_git(repo,'update-index','--add','--cacheinfo','160000,'+run_git(repo,'rev-parse','HEAD')+',src/dependency')
    run_git(repo,'commit','-qm','Synthetic gitlink',day='2024-01-20T00:00:00Z')
    sha=run_git(repo,'rev-parse','HEAD');tree=run_git(repo,'rev-parse','HEAD^{tree}')
    index['registration']['tip_sha']=sha
    entry=deepcopy(index['entries'][-1]);entry.update(revision=sha,source_tree_sha=tree,state_utc='2024-01-20T00:00:00Z')
    for role,ref in entry['artifacts'].items():
        doc=read_json(f[1]/ref['path']);doc.update(revision=sha,source_tree_sha=tree)
        if role=='inventory':
            doc['git_files']=sorted(doc['git_files']+['src/dependency']);doc['reviewed_paths']=doc['git_files']
        write_json(f[1]/ref['path'],doc)
        ref['sha256']=hashlib.sha256((f[1]/ref['path']).read_bytes()).hexdigest()
    index['entries']=[entry];write_json(f[0],index)
    with pytest.raises(ValueError,match='Regular Git'):
        ingest(f[0],f[1],f[2],'native_sqale_index_minutes')


def test_missing_latest_sqale_does_not_reuse_older_value(tmp_path):
    f=fixture_archive(tmp_path)
    entry=f[3]['entries'][2];ref=entry['artifacts']['measures']
    doc=read_json(f[1]/ref['path']);doc['component']['measures']=[r for r in doc['component']['measures'] if r['metric']!='sqale_index']
    write_json(f[1]/ref['path'],doc);ref['sha256']=hashlib.sha256((f[1]/ref['path']).read_bytes()).hexdigest()
    source=source_from(f,'native_sqale_index_minutes')
    history,forecasts=derive(source)
    assert history[0]['stock_minutes']==10 and history[-1]['stock_minutes'] is None
    assert all(f['status']=='UNAVAILABLE' and f['prediction_minutes'] is None for f in forecasts)


def test_source_inventory_cannot_hide_git_symlink(tmp_path):
    f=fixture_archive(tmp_path)
    repo=f[2];(repo/'src/file.py').unlink();(repo/'src/file.py').symlink_to('../outside.py')
    run_git(repo,'add','src/file.py');run_git(repo,'commit','-qm','Synthetic symlink',day='2024-01-20T00:00:00Z')
    sha=run_git(repo,'rev-parse','HEAD');tree=run_git(repo,'rev-parse','HEAD^{tree}')
    index=f[3];index['registration']['tip_sha']=sha
    entry=deepcopy(index['entries'][-1]);entry.update(revision=sha,source_tree_sha=tree,state_utc='2024-01-20T00:00:00Z')
    for role,ref in entry['artifacts'].items():
        doc=read_json(f[1]/ref['path']);doc.update(revision=sha,source_tree_sha=tree);write_json(f[1]/ref['path'],doc)
        ref['sha256']=hashlib.sha256((f[1]/ref['path']).read_bytes()).hexdigest()
    index['entries']=[entry];write_json(f[0],index)
    with pytest.raises(ValueError,match='Regular Git'):
        ingest(f[0],f[1],f[2],'native_sqale_index_minutes')


@pytest.mark.parametrize('source',[[],None,True,1,'invalid'])
def test_malformed_source_remains_value_error(source):
    with pytest.raises(ValueError):derive(source)
