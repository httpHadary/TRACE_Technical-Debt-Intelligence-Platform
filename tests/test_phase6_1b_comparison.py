"""Engineering tests only. No pretrained execution/download or real-data access."""
from dataclasses import replace
from pathlib import Path
import copy
import json
import math
import pytest
from forecasting_research.phase6_0.contracts import Request, validate_response
from forecasting_research.phase6_0.synthetic import SCENARIOS
from forecasting_research.phase6_1b.population import Spec, history, future, population, specs
from forecasting_research.phase6_1b.adapters import baseline, native_path, UnadmittedModel, BlockedAcquisition, TTM512, TimesFM512
from forecasting_research.phase6_1b.study import safe, MODELS, LIMITS
from forecasting_research.phase6_1b.evaluate import score, summarize, validate_rows, denominator


@pytest.mark.parametrize('scenario',SCENARIOS)
def test_generated_population(scenario):
    s=Spec(scenario,0)
    assert history(s)==history(s)
    assert future(s)==future(s)
    assert all(v['timestamp_utc']==history(s).endpoint(h) for h,v in future(s).items())
    assert set(future(s))=={30,60,90}
    assert history(s).complete_daily(512)==(scenario not in ('sparse','irregular'))


def test_population_disjoint_from_exposed_context_study():
    from forecasting_research.phase6_1a.population import specs as old
    assert not {s.case_id for s in specs()} & {s.case_id for s in old()}
    assert len(population())==42
    assert sum(r['eligible'] for r in population())==36


@pytest.mark.parametrize('model',('persistence','rolling_mean','linear_trend'))
def test_constant_exact_baselines(model):
    req=history(Spec('constant',0));pred=baseline(req,model)
    validate_response(req,pred,model)
    assert all(r['point']==85 for r in pred['path'])
    assert all(r['q10'] is None for r in pred['path'])


def test_trend_exact_anchored_window():
    req=history(Spec('slow_increase',0));pred=baseline(req,'linear_trend')
    assert pred['path'][89]['raw_point']==pytest.approx(req.values[-1]+18)


@pytest.mark.parametrize('field',('actual','targets','future_values','split','labels'))
def test_prediction_request_rejects_labels(field):
    data=history(Spec('constant',0)).as_dict();data[field]=[1]
    with pytest.raises(ValueError):Request.from_dict(data)


@pytest.mark.parametrize('scenario',('sparse','irregular'))
def test_missingness_not_zero_filled(scenario):
    req=history(Spec(scenario,0))
    with pytest.raises(ValueError):baseline(req,'persistence')
    with pytest.raises(ValueError):UnadmittedModel('ttm512').predict(req)


def test_acquisition_gate_no_implicit_fallback():
    with pytest.raises(BlockedAcquisition):UnadmittedModel('ttm512').predict(history(Spec('constant',0)))


def test_native_crossing_not_sorted():
    req=history(Spec('constant',0))
    pred=native_path(req,'timesfm512',[2.]*90,[[3.,2.,1.]]*90)
    assert pred['failure']=='NATIVE_QUANTILE_CROSSING'
    assert pred['crossing_steps']==list(range(1,91))
    assert pred['invalid_raw_path'][0]['raw_q10']==3


@pytest.mark.parametrize('bad',(float('nan'),float('inf'),True,None))
def test_native_nonfinite_fatal(bad):
    req=history(Spec('constant',0))
    with pytest.raises(ValueError):native_path(req,'ttm512',[bad]*90)


def test_raw_and_nonnegative_policy():
    req=history(Spec('near_zero',0))
    pred=native_path(req,'ttm512',[-2.]*90)
    validate_response(req,pred,'ttm512')
    assert pred['path'][0]['raw_point']==-2
    assert pred['path'][0]['point']==0
    assert pred['path'][0]['q10'] is None
    assert denominator(req)==0


def test_identity_and_timestamp_protection():
    req=history(Spec('constant',0));pred=baseline(req,'persistence')
    pred['path'][29]['timestamp_utc']=req.endpoint(60)
    with pytest.raises(ValueError):validate_response(req,pred,'persistence')
    with pytest.raises(ValueError):replace(req,timestamps=req.timestamps[:-1]+(req.endpoint(30),))


def test_incompatible_native_config_rejected_before_execution():
    class Config:context_length=90;prediction_length=96
    class Model:config=Config()
    with pytest.raises(ValueError):TTM512(Model(),8)
    class Forecast:max_context=512;fix_quantile_crossing=True
    class Times:forecast_config=Forecast()
    with pytest.raises(ValueError):TimesFM512(Times())


@pytest.mark.parametrize('path',('/tmp/phase6_1b','/home/hp/tst/research/forecasting_mvp/phase6_1b','/home/hp/tst/research/forecasting_mvp/phase6_1b/x/../old'))
def test_owned_path_guard(path):
    with pytest.raises(ValueError):safe(path)


def test_symlink_guard(tmp_path,monkeypatch):
    import forecasting_research.phase6_1b.study as study
    monkeypatch.setattr(study,'ROOT',tmp_path)
    (tmp_path/'link').symlink_to(tmp_path/'other')
    with pytest.raises(ValueError):safe(tmp_path/'link'/'output')


def engineering_rows(models=MODELS):
    rows=[]
    for spec in (Spec('constant',0),Spec('slow_increase',0),Spec('near_zero',0)):
        req=history(spec)
        for m in models:
            for h in (30,60,90):
                y=future(spec)[h]
                q=req.values[-1] if m in ('chronos512','timesfm512') else None
                rows.append(dict(model=m,case_id=spec.case_id,scenario=spec.scenario,horizon=h,
                    timestamp_utc=y['timestamp_utc'],actual=y['value'],current=req.values[-1],request_id=req.identity,
                    denominator=denominator(req),prediction=req.values[-1],raw_point=req.values[-1],
                    q10=q,q50=q,q90=q,raw_q10=q,raw_q50=q,raw_q90=q))
    return rows


def test_equal_population_pairing_and_blocked_accounting():
    rows=engineering_rows(MODELS[:-1]);reg={'population':population()}
    execution={'timesfm512':{'status':'BLOCKED_RESOURCE'}}
    result=summarize(rows,reg,execution)
    assert result['all_candidate_common_ids']==[]
    assert len(result['all_admitted_common_ids'])==3
    assert result['accounting']['timesfm512']['runtime_blocked']==36
    pair=next(r for r in result['paired'] if r['left']=='chronos512' and r['right']=='ttm512')
    assert pair['n']==3 and pair['normalized_difference']==0 and pair['zero_denominators']==1


def test_duplicate_and_future_target_tampering_rejected():
    rows=engineering_rows();reg={'population':population()}
    with pytest.raises(ValueError):validate_rows(rows+[rows[0]],reg)
    rows[0]['actual']+=1
    with pytest.raises(ValueError):validate_rows(rows,reg)


def test_partial_path_is_not_success():
    rows=engineering_rows()
    with pytest.raises(ValueError):summarize(rows[1:],{'population':population()})


def test_scale_balancing_and_undefined_intervals():
    rows=[dict(scenario='a',prediction=0.,raw_point=0.,actual=1.,current=0.,denominator=1.,q10=None)]*3
    rows+=[dict(scenario='b',prediction=0.,raw_point=0.,actual=9.,current=0.,denominator=0.,q10=None)]
    result=score(rows)
    assert result['mae']==3 and result['equal_scenario_macro_mae']==5
    assert result['normalized_mae']==1 and result['zero_denominators']==1
    assert result['coverage'] is None and result['collapsed_intervals'] is None
    assert result['persistence_skill']==0


def test_cpu_memory_and_no_acquisition_surface():
    assert LIMITS['rss_bytes']==2*1024**3 and LIMITS['seconds']==900 and LIMITS['numerical_threads']==2
    root=Path(__file__).resolve().parents[1]/'forecasting_research/phase6_1b'
    text='\n'.join(p.read_text() for p in root.glob('*.py'))
    assert 'pip install' not in text and 'snapshot_download' not in text
    assert "fix_quantile_crossing=False" in text
    assert "local_files_only=True" in text


def test_native_models_do_not_receive_truth(monkeypatch):
    import forecasting_research.phase6_1b.population as generator
    def forbidden(*args):raise AssertionError('Evaluator-only future function')
    monkeypatch.setattr(generator,'future',forbidden)
    for model in ('persistence','rolling_mean','linear_trend'):
        baseline(history(Spec('slow_increase',0)),model)


def test_runtime_metadata_import_not_shadowed_by_model_loader():
    from forecasting_research.phase6_1b.worker import execute
    assert 'importlib' not in execute.__code__.co_varnames


def test_published_arithmetic_and_native_identity_receipts():
    from forecasting_research.phase6_1b.evaluate import read_rows
    root=Path(__file__).resolve().parents[1]/'examples/phase6_1b'
    reg=json.loads((root/'registration.json').read_text())
    result=summarize(read_rows(root/'endpoints.csv'),reg,json.loads((root/'execution_status.json').read_text()))
    assert result==json.loads((root/'metrics.json').read_text())
    assert result['accounting']['ttm512']['successful']==36
    assert result['accounting']['timesfm512']['runtime_blocked']==36
    admission=json.loads((root/'model_runtime_admission.json').read_text())['models']
    assert admission['ttm512']['revision']=='3442406f106122f414a11f72b4ebfe4878bec89d'
    assert admission['timesfm512']['revision']=='1d952420fba87f3c6dee4f240de0f1a0fbc790e3'
    assert admission['timesfm512']['inference_calls']==0
