"""Software-validation fixtures only; no real measurements or neural runtime."""
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import subprocess
import sys

import pytest

from contracts import digest, read_json, write_json
from forecasting_mvp.io import file_sha256
from forecasting_mvp.persistence_flow import (
    ACTUAL_VERSION, HORIZONS, SOURCE_VERSION, TARGET, archive_projection,
    build, derive, evaluate, import_historical, load_presentation, verify_presentation,
)

EXAMPLES = Path(__file__).resolve().parents[1]/'examples/persistence_only'


@pytest.fixture
def source():
    return read_json(EXAMPLES/'observations.json')


@pytest.fixture
def actuals():
    return read_json(EXAMPLES/'actuals.json')


def resign(root):
    manifest = read_json(root/'manifest.json')
    manifest['artifacts'] = {n: file_sha256(root/n) for n in manifest['artifacts']}
    manifest['bundle_id'] = digest(dict(artifacts=manifest['artifacts'], metadata=manifest['metadata'], kind=manifest['kind']))
    write_json(root/'manifest.json', manifest)


def test_example_complete_flat_pending_measured_and_unavailable(tmp_path, source):
    root = tmp_path/'measured'
    manifest = build(EXAMPLES/'observations.json', root, EXAMPLES/'actuals.json')
    data = load_presentation(root)
    assert manifest['current_accuracy'] == 'UNVALIDATED'
    assert manifest['metadata']['evidence'] == 'SOFTWARE_VALIDATION_ONLY'
    assert manifest['permission_status'] == 'SOURCE_CLAIMS_ONLY_NOT_GRANTED_BY_IMPORT'
    assert len(data['forecasts']) == 12
    for f in data['forecasts']:
        assert f['model'] == 'persistence'
        assert f['prediction_minutes'] == f['origin_stock_minutes']
        assert f['interval_lower'] is f['interval_upper'] is None
        assert f['predicted_change_minutes'] == (0 if f['status'] == 'AVAILABLE' else None)
    h = [r for r in data['history'] if r['repository_id'] == 'synthetic-demo']
    assert [r['measured_change_minutes'] for r in h] == [None, 5, -8, -12, None, None]
    assert h[3]['stock_minutes'] == 0
    missing = [f for f in data['forecasts'] if f['repository_id'] == 'synthetic-missing']
    assert all(f['origin_observation_id'] == 'synthetic-missing-2' and f['prediction_minutes'] is None for f in missing)
    assert {e['status'] for e in data['evaluations']} == {'PENDING', 'MEASURED', 'UNAVAILABLE'}
    measured = [e for e in data['evaluations'] if e['status'] == 'MEASURED']
    assert sorted(e['actual_change_minutes'] for e in measured) == [0, 0, 2]
    assert sorted(e['error_minutes'] for e in measured) == [-2, 0, 0]
    build(EXAMPLES/'observations.json', tmp_path/'pending')
    assert {e['status'] for e in load_presentation(tmp_path/'pending')['evaluations']} == {'PENDING', 'UNAVAILABLE'}
    with pytest.raises(FileExistsError):
        build(EXAMPLES/'observations.json', root)


def test_order_independence_new_origin_and_missing_domain(source):
    history, forecasts = derive(source)
    reverse = deepcopy(source)
    reverse['observations'].reverse()
    assert derive(reverse) == (history, forecasts)
    changed = deepcopy(source)
    changed['observations'][5]['components']['security'] = 2
    assert {f['forecast_id'] for f in derive(changed)[1]} != {f['forecast_id'] for f in forecasts}
    changed['observations'][5]['components']['security'] = None
    changed['observations'][5]['domain_id'] = 'another-domain'
    assert all(f['status'] == 'UNAVAILABLE' for f in derive(changed)[1] if f['repository_id'] == 'synthetic-demo')


@pytest.mark.parametrize('field,value', [
    ('observation_id', '../bad'), ('revision', 'abc'), ('revision_index', True),
    ('observed_utc', '2024-01-01T01:00:00+01:00'), ('observed_utc', '2024-02-30T00:00:00Z'),
    ('domain_id', ''), ('scope_id', None),
])
def test_invalid_observation_fields(source, field, value):
    source['observations'][0][field] = value
    with pytest.raises((ValueError, TypeError)):
        derive(source)


@pytest.mark.parametrize('value', [True, -1, float('nan'), float('inf'), '12', 10**1000])
def test_invalid_components(source, value):
    source['observations'][0]['components']['security'] = value
    with pytest.raises(ValueError):
        derive(source)


@pytest.mark.parametrize('identity', ['observation_id', 'revision', 'revision_index', 'observed_utc'])
def test_duplicate_observation_identities(source, identity):
    source['observations'][1][identity] = source['observations'][0][identity]
    with pytest.raises(ValueError, match='Duplicate'):
        derive(source)


@pytest.mark.parametrize('mutation', ['version', 'horizons', 'extra', 'provenance', 'clock_order', 'clock_overflow'])
def test_strict_source_contract(source, mutation):
    if mutation == 'version': source['version'] = 'unknown'
    elif mutation == 'horizons': source['horizons']['revision_step'] = [30,60,90]
    elif mutation == 'extra': source['observations'][0]['actual'] = 12
    elif mutation == 'provenance': source['source']['permission'] = ''
    elif mutation == 'clock_order': source['observations'][1]['observed_utc'] = '2023-01-01T00:00:00Z'
    else: source['observations'][5]['observed_utc'] = '9999-12-31T00:00:00Z'
    with pytest.raises(ValueError): derive(source)


@pytest.mark.parametrize('field,value', [
    ('forecast_id', 'unknown'), ('target', 'sqale'), ('domain_id', 'other'),
    ('scope_id', 'other'), ('repository_id', 'other'), ('origin_observation_id', 'other'),
    ('horizon_unit', 'elapsed_day'), ('horizon', True), ('endpoint_revision_index', 8),
    ('endpoint_revision', '0000000000000000000000000000000000000006'),
    ('observed_utc', '2020-01-01T00:00:00Z'),
])
def test_wrong_actual_target_domain_clock_endpoint(source, actuals, field, value):
    # Select the revision-step example regardless of serialized row ordering.
    row = next(r for r in actuals['actuals'] if r['horizon_unit'] == 'revision_step')
    row[field] = value
    with pytest.raises(ValueError): evaluate(derive(source)[1], actuals)


def test_actual_calendar_reuse_exact_clock_and_consistency(source, actuals):
    forecasts = derive(source)[1]
    assert sum(e['status'] == 'MEASURED' for e in evaluate(forecasts, actuals)) == 3
    calendar = next(r for r in actuals['actuals'] if r['horizon_unit'] == 'elapsed_day')
    bad = deepcopy(actuals)
    next(r for r in bad['actuals'] if r['forecast_id'] == calendar['forecast_id'])['observed_utc'] = '2024-02-05T00:00:01Z'
    with pytest.raises(ValueError, match='exact UTC'): evaluate(forecasts, bad)
    bad = deepcopy(actuals)
    bad['actuals'].append(deepcopy(bad['actuals'][0]))
    with pytest.raises(ValueError, match='duplicate'): evaluate(forecasts, bad)
    for field, value in [('endpoint_revision_index', 5), ('components', dict(maintainability=8,reliability=2,security=1))]:
        bad = deepcopy(actuals)
        next(r for r in bad['actuals'] if r['forecast_id'] == calendar['forecast_id'])[field] = value
        with pytest.raises(ValueError): evaluate(forecasts, bad)
    bad = deepcopy(actuals)
    next(r for r in bad['actuals'] if r['forecast_id'] == calendar['forecast_id'])['components']['security'] = None
    with pytest.raises(ValueError): evaluate(forecasts, bad)


@pytest.mark.parametrize('contradiction', ['calendar_reversal', 'cross_clock_reversal', 'simultaneous_different_states'])
def test_actual_sequence_order_across_horizons_and_clocks(source, actuals, contradiction):
    forecasts = derive(source)[1]
    # Input order does not determine chronology; unchanged calendar reuse stays valid.
    assert evaluate(forecasts, actuals) == evaluate(forecasts, dict(actuals, actuals=list(reversed(actuals['actuals']))))
    if contradiction == 'calendar_reversal':
        actuals['actuals'] = [r for r in actuals['actuals'] if r['horizon_unit'] == 'elapsed_day']
        for row, index in zip(actuals['actuals'], [20, 10]):
            row['endpoint_revision_index'] = index
            row['endpoint_revision'] = f'{index:040x}'
    else:
        row = next(r for r in actuals['actuals'] if r['horizon_unit'] == 'revision_step')
        row['observed_utc'] = '2024-01-09T00:00:00Z' if contradiction == 'cross_clock_reversal' else '2024-02-05T00:00:00Z'
    with pytest.raises(ValueError, match='chronology contradicts revision sequence'):
        evaluate(forecasts, actuals)


def test_actuals_open_only_after_prediction_seal_and_failed_evidence_retained(tmp_path, monkeypatch):
    import forecasting_mvp.persistence_flow as flow
    original = flow.read_json
    output = tmp_path/'failed'
    def checked(path):
        if Path(path).name == 'actuals.json':
            assert (output/'prediction_seal.json').is_file()
            assert read_json(output/'prediction_seal.json')['actuals_loaded'] is False
            assert not (output/'manifest.json').exists()
            raise ValueError('deliberate evaluator failure')
        return original(path)
    monkeypatch.setattr(flow, 'read_json', checked)
    with pytest.raises(ValueError, match='evaluator failure'):
        build(EXAMPLES/'observations.json', output, EXAMPLES/'actuals.json')
    assert (output/'forecasts.json').is_file()
    assert not (output/'manifest.json').exists()


@pytest.mark.parametrize('tamper', ['hash', 'seal', 'semantics', 'metadata', 'extra', 'missing', 'symlink'])
def test_strict_publication_verification(tmp_path, tamper):
    root = tmp_path/'bundle'
    build(EXAMPLES/'observations.json', root)
    if tamper == 'hash': (root/'history.json').write_text('[]')
    elif tamper == 'seal':
        write_json(root/'prediction_seal.json', {'actuals_loaded': True}); resign(root)
    elif tamper == 'semantics':
        rows = read_json(root/'history.json'); rows[1]['measured_change_minutes'] = 999
        write_json(root/'history.json', rows); resign(root)
    elif tamper == 'metadata':
        m = read_json(root/'manifest.json'); m['metadata']['evidence'] = 'VALIDATED'
        write_json(root/'manifest.json',m); resign(root)
    elif tamper == 'extra': (root/'unlisted.json').write_text('{}')
    elif tamper == 'missing': (root/'history.json').unlink()
    else:
        content = root/'history.json'; content.rename(tmp_path/'outside.json'); content.symlink_to(tmp_path/'outside.json')
    with pytest.raises((ValueError, OSError)): verify_presentation(root)


def historical_fixture(root):
    """226 invented contexts produce the required original export size (678)."""
    root.mkdir()
    sha = lambda i: f'{1000+i:040x}'
    day = lambda i: (date(2020,1,1)+timedelta(days=i)).isoformat()
    stock = lambda i: (i%17)*3
    registration = dict(horizons_revision_steps=[3,4,12],target='total_principal = maintainability + reliability + security estimated remediation minutes',clock='revision_step',evidence='SOFTWARE_VALIDATION_ONLY',rights='Synthetic fixture only.',provenance='Invented test sequence.')
    contexts, predictions, scores = [], [], []
    for i in range(1,227):
        # Deliberately reverse lexical ID order relative to actual history.
        cid = f'context-{227-i:03d}'
        contexts.append(dict(context_id=cid,repository_id='synthetic-archive',past_values=[stock(i-1),stock(i)],history_shas=[sha(i-1),sha(i)],history_commit_dates=[day(i-1),day(i)],origin_sha=sha(i),origin_commit_date=day(i)))
        for h in (3,4,12):
            p = dict(method='persistence',forecast_id=f'{cid}-{h}',context_id=cid,repository_id='synthetic-archive',horizon_revision_steps=h,current=stock(i),prediction=stock(i),raw_prediction=stock(i),signed_delta=0,raw_signed_delta=0,q10=None,q90=None)
            predictions.append(p)
            scores.append(dict(p,actual=stock(i+h),endpoint_sha=sha(i+h),endpoint_commit_date=day(i+h),elapsed_commit_date_days=h))
    for name, data in [('registration.json',registration),('requests.json',dict(clock='revision_step',contexts=contexts)),('predictions.json',predictions),('scored_predictions.json',scores)]: write_json(root/name,data)
    write_json(root/'request_seal.json',{'requests.json':file_sha256(root/'requests.json')})
    write_json(root/'prediction_seal.json',{n:file_sha256(root/n) for n in ['predictions.json','registration.json']})
    historical_manifest(root)
    return registration, dict(clock='revision_step',contexts=contexts), predictions, scores


def historical_manifest(root):
    write_json(root/'artifact_manifest.json',dict(files={p.name:dict(bytes=p.stat().st_size,sha256=file_sha256(p)) for p in root.iterdir() if p.name!='artifact_manifest.json'}))


def test_historical_import_preserves_ids_counts_mae_and_order(tmp_path, monkeypatch):
    src, out = tmp_path/'source', tmp_path/'output'
    registration, requests, predictions, scores = historical_fixture(src)
    import forecasting_mvp.persistence_flow as flow
    original = flow.read_json
    def checked(path):
        if Path(path).name == 'scored_predictions.json':
            assert (out/'prediction_seal.json').is_file()
            assert (out/'archive_origin_seal.json').is_file()
        return original(path)
    monkeypatch.setattr(flow,'read_json',checked)
    import_historical(src,out)
    data = load_presentation(out)
    assert len(data['forecasts']) == 678
    assert {f['forecast_id'] for f in data['forecasts']} == {p['forecast_id'] for p in predictions}
    for h in (3,4,12):
        original_errors = [abs(s['prediction']-s['actual']) for s in scores if s['horizon_revision_steps']==h]
        exported_errors = [e['absolute_error_minutes'] for e in data['evaluations'] if e['horizon']==h]
        assert len(exported_errors) == 226
        assert sum(exported_errors)/226 == sum(original_errors)/226
    assert archive_projection(registration,requests,predictions,scores) == archive_projection(registration,dict(requests,contexts=list(reversed(requests['contexts']))),list(reversed(predictions)),list(reversed(scores)))
    assert data['history'][1]['measured_change_minutes'] == 3
    assert data['forecasts'][-1]['origin_revision'] == requests['contexts'][-1]['origin_sha']
    assert data['manifest']['metadata']['date_precision'] == 'DATE_ONLY_NOT_UTC'


@pytest.mark.parametrize('tamper', ['hash', 'seal', 'actual', 'method', 'unsafe_path'])
def test_historical_rejects_corruption_and_wrong_export(tmp_path, tamper):
    src = tmp_path/'source'
    reg, req, pred, scores = historical_fixture(src)
    if tamper == 'hash': (src/'requests.json').write_text('{}')
    elif tamper == 'seal':
        write_json(src/'request_seal.json',{}); historical_manifest(src)
    elif tamper == 'actual':
        scores[0]['actual'] += 1; write_json(src/'scored_predictions.json',scores); historical_manifest(src)
    elif tamper == 'method':
        pred[0]['method']='chronos'; write_json(src/'predictions.json',pred)
        write_json(src/'prediction_seal.json',{n:file_sha256(src/n) for n in ['predictions.json','registration.json']}); historical_manifest(src)
    else:
        m=read_json(src/'artifact_manifest.json');m['files']['../escape.json']=dict(bytes=0,sha256='0'*64);write_json(src/'artifact_manifest.json',m)
    with pytest.raises((ValueError, OSError)): import_historical(src,tmp_path/'output')
    if tamper == 'actual':
        assert (tmp_path/'output/prediction_seal.json').is_file()
        assert not (tmp_path/'output/manifest.json').exists()


def substitute_known_successor(score, requests):
    origin = next(c for c in requests['contexts'] if c['context_id'] == score['context_id'])
    successor = next(c for c in requests['contexts'] if c['history_shas'][0] == origin['origin_sha'])
    score.update(endpoint_sha=successor['origin_sha'], endpoint_commit_date=successor['origin_commit_date'],
                 actual=successor['past_values'][-1], elapsed_commit_date_days=1)


def test_historical_wrong_step_rejected_after_source_and_presentation_rehash(tmp_path):
    src, out = tmp_path/'source', tmp_path/'complete'
    reg, req, pred, scores = historical_fixture(src)
    import_historical(src, out)
    substitute_known_successor(scores[0], req)
    write_json(src/'scored_predictions.json', scores)
    historical_manifest(src)
    with pytest.raises(ValueError, match='explicit revision-step distance'):
        import_historical(src, tmp_path/'failed-import')
    assert (tmp_path/'failed-import/prediction_seal.json').is_file()
    assert not (tmp_path/'failed-import/manifest.json').exists()
    write_json(out/'archive_scores.json', scores)
    resign(out)
    with pytest.raises(ValueError, match='explicit revision-step distance'):
        verify_presentation(out)


def test_historical_step_does_not_join_disconnected_context_chains(tmp_path):
    reg, req, pred, scores = historical_fixture(tmp_path/'source')
    contexts = [req['contexts'][0], req['contexts'][10]]
    selected = {c['context_id'] for c in contexts}
    req = dict(req, contexts=contexts)
    pred = [p for p in pred if p['context_id'] in selected]
    scores = [s for s in scores if s['context_id'] in selected]
    target = contexts[1]
    scores[0].update(endpoint_sha=target['origin_sha'], endpoint_commit_date=target['origin_commit_date'],
                     actual=target['past_values'][-1], elapsed_commit_date_days=10)
    # No edge establishes a distance between these separate chains. Their date
    # or display ordering must not be substituted for a revision-step distance.
    _, forecasts, evaluations = archive_projection(reg, req, pred, scores)
    assert len(forecasts) == len(evaluations) == 6
    assert next(e for e in evaluations if e['forecast_id'] == scores[0]['forecast_id'])['endpoint_revision'] == target['origin_sha']


def test_cli_and_neural_import_free_subprocess(tmp_path):
    script = r'''
import importlib.abc,json,sys
class NoNeural(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('torch','chronos','transformers') or fullname in ('forecasting_mvp.chronos_run','forecasting_mvp.baseline_run'):
            raise AssertionError('Forbidden research import '+fullname)
sys.meta_path.insert(0, NoNeural())
from forecasting_mvp.cli import main
assert main(['persistence-build','--source',sys.argv[1],'--actuals',sys.argv[2],'--out',sys.argv[3]]) == 0
assert main(['persistence-verify','--bundle',sys.argv[3]]) == 0
assert main(['persistence-build','--source',sys.argv[1],'--out',sys.argv[3]]) == 3
assert main(['persistence-serve','--registry',sys.argv[4],'--host','0.0.0.0']) == 3
'''
    result = subprocess.run([sys.executable,'-c',script,str(EXAMPLES/'observations.json'),str(EXAMPLES/'actuals.json'),str(tmp_path/'bundle'),str(tmp_path)],capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    malformed = tmp_path/'malformed.json'
    malformed.write_text('{"version":1,"version":2}')
    result = subprocess.run([sys.executable,'-m','forecasting_mvp','persistence-build','--source',str(malformed),'--out',str(tmp_path/'invalid')],capture_output=True,text=True)
    assert result.returncode == 3
    assert not (tmp_path/'invalid').exists()


def test_evaluation_summary_macro_pooled_subsets_and_coverage():
    import math
    from forecasting_mvp.persistence_flow import evaluation_summary
    fs = [dict(forecast_id=str(i),horizon_unit='revision_step',horizon=3,status='AVAILABLE') for i in range(4)]
    rows = [dict(forecast_id=str(i),repository_id=repo,horizon_unit='revision_step',horizon=3,status='MEASURED',error_minutes=err,actual_change_minutes=change)
            for i,(repo,err,change) in enumerate([('a',0,0),('a',2,-2),('b',8,8)])]
    rows.append(dict(forecast_id='3',repository_id='b',horizon_unit='revision_step',horizon=3,status='PENDING'))
    s = evaluation_summary(fs,rows)[0]
    assert s['actual_coverage']==.75 and s['pending']==1
    assert s['subsets']['all']['macro_mae_minutes']==4.5
    assert s['subsets']['all']['pooled_mae_minutes']==pytest.approx(10/3)
    assert s['subsets']['all']['macro_rmse_minutes']==pytest.approx((math.sqrt(2)+8)/2)
    assert s['subsets']['all']['pooled_rmse_minutes']==pytest.approx(math.sqrt(68/3))
    assert {k:v['count'] for k,v in s['subsets'].items()}==dict(all=3,changed=2,stable=1,increase=1,decrease=1)
    empty=evaluation_summary([dict(fs[0],status='UNAVAILABLE')],[dict(rows[-1],status='UNAVAILABLE')])[0]
    assert empty['actual_coverage'] is None and empty['subsets']['all']['macro_mae_minutes'] is None
