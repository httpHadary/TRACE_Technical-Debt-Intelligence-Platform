"""Baseline forecasts and evaluation, without pretrained/CatBoost execution."""
from copy import deepcopy
import json
import math

import pytest

from contracts import digest, write_csv, write_json
from forecasting_mvp.baselines import CANDIDATES, MODELS, baseline_predict
from forecasting_mvp.baseline_evaluation import evaluate_baselines, select_parameters, cluster_intervals
from forecasting_mvp.baseline_run import (LABEL_FIELDS, run_baselines, check_final_seal, label_view,
                                         plan_requests, generate_candidates)
from forecasting_mvp.io import file_sha256, publish_manifest, verify_bundle
from forecasting_mvp.prediction_input import admit_prediction_input
from forecasting_mvp.contracts import TargetContract
from test_forecasting_mvp_phase2_1 import frozen_fixture, make_context, resign


def request(values, horizon=30):
    context = make_context()
    context["values"] = list(values)
    resign(context)
    return admit_prediction_input(context, horizon, expected_origin_utc=context["origin_utc"],
                                  measurement_times={"past": "2000-01-01T00:00:00Z"})


@pytest.mark.parametrize("horizon", [30, 60, 90])
def test_exact_horizon_persistence_mean_and_anchored_trend(horizon):
    admitted = request([float(i) for i in range(90)], horizon)
    assert baseline_predict(admitted, "persistence") == (89., 89.)
    assert baseline_predict(admitted, "rolling_mean", 30) == (74.5, 74.5)
    assert baseline_predict(admitted, "linear_trend", 30) == (89. + horizon, 89. + horizon)


def test_clipping_keeps_raw_and_trend_is_anchored_at_current():
    admitted = request([float(89-i) for i in range(90)])
    assert baseline_predict(admitted, "linear_trend", 30) == (-30., 0.)
    for candidate in CANDIDATES:
        assert baseline_predict(request([42.]*90), *candidate) == (42.,42.)
    changed = [float(i) for i in range(90)]
    changed[-1] = 120.
    raw, _ = baseline_predict(request(changed), "linear_trend", 30)
    assert raw > 120.  # extrapolation anchored at the observed origin, not fitted intercept


def test_predictor_has_no_file_or_future_label_access(monkeypatch):
    admitted = request([42.]*90)
    def forbidden(*args, **kwargs):
        raise AssertionError("Prediction tried to open a file")
    monkeypatch.setattr("builtins.open", forbidden)
    for candidate in CANDIDATES:
        assert baseline_predict(admitted, *candidate) == (42.,42.)
    with pytest.raises(ValueError, match="admitted"):
        baseline_predict({"actual_minutes": 42}, "persistence")
    with pytest.raises(ValueError, match="Unregistered"):
        baseline_predict(admitted, "chronos")


def toy_predictions():
    labels, predictions = {}, []
    for i, (repo, actual, mean_pred, trend_pred) in enumerate((("a",20,22,20),("a",30,25,28),("b",10,14,12))):
        metadata = {"forecast_id": str(i), "context_id": str(i), "repository_id": repo, "horizon_days": 30,
                    "endpoint_utc": "2010-02-03T00:00:00Z", "evaluation_phase": "test_temporal"}
        labels[str(i)] = {**metadata, "actual_minutes": actual, "actual_delta_minutes": actual-20,
                         "endpoint_observation_id": f"future-{i}"}
        for model, value, window in (("persistence",20,0),("rolling_mean",mean_pred,7),("linear_trend",trend_pred,30)):
            predictions.append({**metadata, "model": model, "window_days": window, "prediction_minutes": value,
                                "raw_prediction_minutes": value, "current_minutes": 20,
                                "origin_observation_id": f"past-{i}", "context_values_digest": digest(i),
                                "distinct_context_measurements": 1})
    return predictions, labels


def test_metrics_macro_pooled_zero_baseline_and_pairing():
    predictions, labels = toy_predictions()
    metrics = evaluate_baselines(predictions, labels)
    index = {(r["subset"],r["repository_id"],r["model"]):r for r in metrics}
    persistence = index["all","ALL","persistence"]
    assert persistence["macro_mae"] == 7.5
    assert persistence["pooled_mae"] == pytest.approx(20/3)
    assert persistence["macro_rmse"] == pytest.approx((math.sqrt(50)+10)/2)
    mean = index["all","ALL","rolling_mean"]
    assert mean["macro_mae"] == 3.75 and mean["macro_mae_gain_fraction"] == .5
    assert mean["paired_mae_gain_ci_low"] <= 3.75 <= mean["paired_mae_gain_ci_high"]
    unchanged = index["unchanged_debt","ALL","persistence"]
    assert unchanged["macro_mae"] == 0 and unchanged["macro_mae_gain_fraction"] is None
    assert index["unchanged_debt","b","rolling_mean"]["uncertainty_status"] == "NO_EXAMPLES"
    assert index["all","a","persistence"]["macro_mae_ci_low"] is None
    assert metrics == evaluate_baselines(list(reversed(predictions)), labels)
    with pytest.raises(ValueError, match="identical"):
        evaluate_baselines(predictions[:-1], labels)
    with pytest.raises(ValueError, match="Duplicate"):
        evaluate_baselines(predictions+[predictions[0]],labels)
    altered = deepcopy(labels)
    altered["0"]["endpoint_utc"] = "2010-02-04T00:00:00Z"
    with pytest.raises(ValueError, match="identity"):
        evaluate_baselines(predictions,altered)


def test_cluster_bootstrap_is_paired_repository_based_and_deterministic():
    stats={"a":(10.,20.),"b":(20.,40.)}; base={"a":(15.,25.),"b":(25.,45.)}
    bounds=cluster_intervals(stats,base)
    assert bounds==cluster_intervals(dict(reversed(list(stats.items()))),base)
    assert bounds[4:]==[5.,5.]
    assert cluster_intervals({"a":stats["a"]},base)==[None]*6


def test_parameter_selection_validation_only_and_fixed_tie_policy():
    candidates, labels=[],{}
    for h in (30,60,90):
        fid=str(h)
        labels[fid]={"actual_minutes":0.,"evaluation_phase":"validation"}
        for model,window in CANDIDATES:
            candidates.append({"forecast_id":fid,"horizon_days":h,"evaluation_phase":"validation",
                               "repository_id":"validation-repo","model":model,"window_days":window,
                               "prediction_minutes":0. if window==30 else 10.})
    selected=select_parameters(candidates,labels)
    assert all(s["rolling_mean"]["window_days"]==30 for s in selected["parameters"].values())
    assert all(m=="rolling_mean" for m in selected["champions"].values())
    polluted=deepcopy(labels); polluted['future-test']={"actual_minutes":1.,"evaluation_phase":"test_repository"}
    with pytest.raises(ValueError,match="Validation-only"):
        select_parameters(candidates,polluted)
    polluted=deepcopy(labels); polluted['30']["evaluation_phase"]="test_temporal"
    with pytest.raises(ValueError,match="forbidden"):
        select_parameters(candidates,polluted)


def replay_fixture(tmp_path):
    db,bundle,rows,splits,contexts=frozen_fixture(tmp_path)
    # Add the full Phase 2 label contract to the synthetic fixture only.
    write_csv(bundle/'forecasting_labels.csv',[{k:r[k] for k in LABEL_FIELDS} for r in rows],LABEL_FIELDS)
    previous=json.loads((bundle/'manifest.json').read_text())
    (bundle/'manifest.json').unlink()
    manifest=publish_manifest(bundle,list(previous['artifacts']),previous['metadata'])
    history=tmp_path/'history'; history.mkdir()
    observations={c['observation_ids'][0]:{'observation_id':c['observation_ids'][0],'historical_timestamp':'2008-01-01T00:00:00Z'} for c in contexts}
    write_csv(history/'historical_debt.csv',list(observations.values()),('observation_id','historical_timestamp'))
    publish_manifest(history,['historical_debt.csv'],{'phase':1,'source_sha256':file_sha256(db)})
    hardening=tmp_path/'hardening'; hardening.mkdir()
    write_json(hardening/'dataset_validation.json',{'status':'PASS','raw_sql_all_passed':True,'raw_sql_sample_count':100,
        'frozen_artifact_hashes':manifest['artifacts'],'structural_checks':{'split_id':splits['split_id']}})
    publish_manifest(hardening,['dataset_validation.json'],{'phase':'2.1','source_sha256':file_sha256(db)})
    return bundle,history,hardening,splits


def test_end_to_end_seal_order_frozen_ids_and_determinism(tmp_path,monkeypatch):
    import forecasting_mvp.baseline_run as runner
    bundle,history,hardening,splits=replay_fixture(tmp_path)
    initial=verify_bundle(bundle)
    original=runner.label_view
    calls=[]
    def spy(path,expected_ids,*,verify_seal):
        verify_seal()
        phase= 'validation' if all(splits['assignments'][fid]=='validation' for fid in expected_ids) else 'evaluation'
        calls.append(phase)
        if phase=='validation':
            assert (tmp_path/'run1/candidates/manifest.json').exists()
        else:
            check_final_seal(tmp_path/'run1')
        return original(path,expected_ids,verify_seal=verify_seal)
    monkeypatch.setattr(runner,'label_view',spy)
    monkeypatch.setattr(runner,'plot_comparison',lambda metrics,path:path.write_bytes(b'SOFTWARE_VALIDATION_ONLY'))
    report=run_baselines(bundle,history,hardening,tmp_path/'run1')
    assert calls==['validation','evaluation'] and report['model_failures']==0
    assert report['events']==['study_registered_before_predictions','all_candidate_predictions_sealed_before_any_labels',
        'validation_only_labels_loaded','parameters_and_validation_champions_frozen',
        'selected_predictions_sealed_before_test_labels','evaluation_labels_loaded_after_prediction_seal']
    assert report['forecast_ids']==sum(v for phases in splits['per_horizon_counts'].values() for k,v in phases.items()
                                        if k in ('train','validation','test_temporal','test_repository'))
    assert report['selected_prediction_rows']==report['forecast_ids']*3
    selected=json.loads((tmp_path/'run1/selected_parameters.json').read_text())
    assert set(selected['champions'].values())=={'persistence'}
    monkeypatch.setattr(runner,'label_view',original)
    run_baselines(bundle,history,hardening,tmp_path/'run2')
    for artifact in (tmp_path/'run1').rglob('*'):
        if artifact.is_file():
            assert artifact.read_bytes()==(tmp_path/'run2'/artifact.relative_to(tmp_path/'run1')).read_bytes()
    assert verify_bundle(bundle)==initial
    (tmp_path/'run1/baseline_predictions.csv').write_text('tampered')
    with pytest.raises(ValueError,match="changed"):
        label_view(bundle/'forecasting_labels.csv',set(),verify_seal=lambda:check_final_seal(tmp_path/'run1'))
    with pytest.raises(ValueError,match="New output"):
        run_baselines(bundle,history,hardening,tmp_path/'run2')


def test_candidate_generation_does_not_open_labels_or_combined_dataset(tmp_path,monkeypatch):
    from pathlib import Path
    bundle,history,hardening,splits=replay_fixture(tmp_path)
    from forecasting_mvp.baseline_run import historical_measurement_times
    times=historical_measurement_times(history/'historical_debt.csv')
    requests=plan_requests(bundle/'forecasting_features.csv',splits)
    original=Path.open
    def guarded(path,*args,**kwargs):
        assert path.name not in ('forecasting_labels.csv','forecasting_dataset.csv'),"Prediction tried to read targets"
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guarded)
    candidates=generate_candidates(bundle/'forecasting_contexts.jsonl.gz',requests,times)
    assert all(row['prediction_minutes']==0 for row in candidates)
    assert all(not any(k.startswith('actual_') for k in row) for row in candidates)
