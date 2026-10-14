"""Phase 4.2 analytical metrics, labels/seals, failures and past-only contract."""
from copy import deepcopy
from pathlib import Path
import json

import pytest

from contracts import digest,write_csv,write_json
from forecasting_mvp.chronos_eval_worker import admitted_records,infer_records,FIELDS
from forecasting_mvp.chronos_evaluation import interval_metrics,compare_points,select_validation_policy,MODELS
from forecasting_mvp.chronos_run import seal,check_seal
from forecasting_mvp.baseline_run import label_view
from forecasting_mvp.io import publish_manifest
from test_forecasting_mvp_phase4_1 import sample_records,FakeEngine
from forecasting_mvp.chronos_adapter import ChronosSmallAdapter


def prepared(stage='validation'):
    records,_=sample_records()
    records=[{'context':r['context'],'measurement_times':r['measurement_times'],'forecasts':r['forecasts']}
             for r in records if r['evaluation_phase']=='validation']
    policy={'phase':'4.2','stage':stage,'held_repository_ids':[], 'contexts':len(records),
            'forecast_ids':sorted(f['forecast_id'] for r in records for f in r['forecasts'])}
    return records,policy


def test_label_free_native_inference_repeat_and_failure_fallback():
    records,policy=prepared()
    admitted=admitted_records(records,policy)
    predictions,failures,_=infer_records(admitted,ChronosSmallAdapter(FakeEngine()),True)
    assert len(predictions)==9 and failures==[]
    assert all(r['inference_status']=='SUCCESS' and r['maximum_repeat_difference']==0 for r in predictions)
    assert all(r['prediction_minutes']==r['horizon_days'] for r in predictions)
    failed,failures,_=infer_records(admitted,ChronosSmallAdapter(FakeEngine('crossing')),False)
    assert len(failures)==3 and len(failed)==9
    assert all(r['inference_status']=='PERSISTENCE_FALLBACK' and r['q10'] is None and r['q90'] is None
               and r['prediction_minutes']==r['current_minutes'] for r in failed)


def test_nondeterministic_pilot_repeat_blocks_instead_of_fallback():
    records,policy=prepared()
    admitted=admitted_records(records,policy)
    class DifferentRepeats:
        calls=0
        def predict_path(self,request):
            self.calls+=1
            return [{'valid_but_different_repeat':self.calls}]
    with pytest.raises(ValueError,match='Deterministic pilot repeat mismatch'):
        infer_records(admitted,DifferentRepeats(),True)


@pytest.mark.parametrize('defect',['test_in_validation','future_column','wrong_horizon','wrong_count','duplicate','held_repo'])
def test_frozen_worker_request_guards(defect):
    records,policy=prepared()
    if defect=='test_in_validation':records[0]['forecasts'][0]['evaluation_phase']='test_temporal'
    elif defect=='future_column':records[0]['forecasts'][0]['actual_minutes']=3
    elif defect=='wrong_horizon':records[0]['forecasts'][0]['horizon_days']=91
    elif defect=='wrong_count':policy['forecast_ids'].pop()
    elif defect=='duplicate':records.append(deepcopy(records[0]))
    elif defect=='held_repo':policy['held_repository_ids']=[records[0]['context']['repository_id']]
    with pytest.raises(ValueError):admitted_records(records,policy)


def interval_fixture():
    rows=[];labels={};controls=[]
    for i,(repo,actual,current,low,point,high,distinct) in enumerate([
        ('a',12.,10.,10.,10.,10.,1),('a',10.,10.,9.,10.,11.,1),('b',15.,10.,10.,12.,20.,3)]):
        base={'forecast_id':str(i),'context_id':str(i),'repository_id':repo,'track':'core90','origin_utc':'2010-01-04T00:00:00Z',
              'horizon_days':30,'endpoint_utc':'2010-02-03T00:00:00Z','evaluation_phase':'test_temporal',
              'window_days':0,'current_minutes':current,'origin_observation_id':'past-'+str(i),
              'distinct_context_measurements':distinct,'distinct_context_values':distinct,'context_values_digest':digest(i)}
        rows.append({**base,'model':'chronos_small','prediction_minutes':point,'raw_prediction_minutes':point,
            'q10':low,'q90':high,'raw_q10':low,'raw_q90':high,'inference_status':'SUCCESS'})
        labels[str(i)]={**{k:base[k] for k in ('forecast_id','context_id','repository_id','horizon_days','endpoint_utc','evaluation_phase')},
                       'actual_minutes':actual,'actual_delta_minutes':actual-current,'endpoint_observation_id':'future-'+str(i)}
        for model in MODELS[:-1]:controls.append({**base,'model':model,'raw_prediction_minutes':current,'prediction_minutes':current})
    return rows,labels,controls


def test_native_coverage_width_pinball_collapsed_constant_contexts_and_pairing():
    rows,labels,controls=interval_fixture()
    metrics=interval_metrics(rows,labels)
    index={(r['subset'],r['repository_id']):r for r in metrics}
    all_=index['all','ALL']
    assert all_['macro_coverage80']==.75 and all_['pooled_coverage80']==pytest.approx(2/3)
    assert all_['macro_width80']==5.5 and all_['pooled_width80']==4.
    constant=index['constant_history','ALL']
    assert constant['collapsed_intervals']==1 and constant['collapsed_misses']==1
    assert constant['near_collapsed_intervals']==1 and constant['raw_collapsed_intervals']==1
    assert constant['macro_coverage80']==.5
    assert all_['coverage_ci_low']<=.75<=all_['coverage_ci_high']
    assert index['all','a']['coverage_ci_low'] is None
    full,matched=compare_points(rows,controls,labels)
    assert full==matched
    indexed={(r['model'],r['subset'],r['repository_id']):r for r in full}
    assert indexed['chronos_small','all','ALL']['macro_mae']==2.
    assert indexed['persistence','all','ALL']['macro_mae']==3.
    bad=deepcopy(rows);bad[0]['q90']=9.
    with pytest.raises(ValueError,match='ordered'):interval_metrics(bad,labels)


def test_failure_rows_are_not_fabricated_intervals_and_success_comparison_is_paired():
    rows,labels,controls=interval_fixture()
    row=rows[0];row.update(inference_status='PERSISTENCE_FALLBACK',q10=None,q90=None,
                           raw_q10=None,raw_q90=None,prediction_minutes=row['current_minutes'])
    metrics=interval_metrics(rows,labels)
    all_=next(r for r in metrics if r['subset']=='all' and r['repository_id']=='ALL')
    assert all_['attempted']==3 and all_['successes']==2 and all_['failures']==1
    full,matched=compare_points(rows,controls,labels)
    assert {r['n'] for r in matched if r['subset']=='all' and r['repository_id']=='ALL'}=={2}
    assert {r['n'] for r in full if r['subset']=='all' and r['repository_id']=='ALL'}=={3}


def test_selection_cannot_receive_test_results():
    rows,labels,controls=interval_fixture();metrics,_=compare_points(rows,controls,labels)
    with pytest.raises(ValueError,match='Only validation'):select_validation_policy(metrics,rows)
    synthetic=[]
    for h in (30,60,90):
        for model in MODELS:
            synthetic.append({'evaluation_phase':'validation','horizon_days':h,'subset':'all','repository_id':'ALL',
                              'model':model,'macro_mae':10. if model!='chronos_small' else 9.})
    policy=select_validation_policy(synthetic,[])
    assert all(v['champion']=='chronos_small' for v in policy['horizons'].values())
    assert policy['inference_configuration_changed'] is False


def test_labels_cannot_open_before_verified_seal_and_frozen_selection(tmp_path,monkeypatch):
    results=tmp_path/'test/results';results.mkdir(parents=True)
    write_csv(results/'predictions.csv',[],FIELDS)
    write_json(results/'worker_summary.json',{'status':'PASS'})
    publish_manifest(results,['predictions.csv','worker_summary.json'],{'phase':'4.2'})
    write_json(tmp_path/'selection.json',{'status':'FROZEN'})
    expected=seal(tmp_path,'test');check_seal(tmp_path,'test',expected)
    (tmp_path/'selection.json').write_text('tampered')
    original=Path.open
    def guard(path,*args,**kwargs):
        assert path.name!='labels.csv','Numerical labels opened before seal verification'
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guard)
    with pytest.raises(ValueError,match='selection changed'):
        label_view(tmp_path/'labels.csv',set(),verify_seal=lambda:check_seal(tmp_path,'test',expected))


def test_end_to_end_validation_freeze_test_seals_and_original_baselines(tmp_path,monkeypatch):
    import sys
    import forecasting_mvp.chronos_run as runner
    import forecasting_mvp.baseline_run as baseline_runner
    from forecasting_mvp.io import verify_bundle
    from test_forecasting_mvp_phase3 import replay_fixture
    bundle,history,hardening,splits=replay_fixture(tmp_path)
    baseline=tmp_path/'baselines'
    monkeypatch.setattr(baseline_runner,'plot_comparison',lambda metrics,path:path.write_bytes(b'SOFTWARE_VALIDATION_ONLY'))
    baseline_runner.run_baselines(bundle,history,hardening,baseline)
    frozen_baseline=verify_bundle(baseline)
    smoke=tmp_path/'smoke';(smoke/'results').mkdir(parents=True)
    write_json(smoke/'results/chronos_smoke_summary.json',{'revision':runner.REVISION})
    source=frozen_baseline['metadata']['source_sha256']
    publish_manifest(smoke,['results/chronos_smoke_summary.json'],{'phase':'4.1','source_sha256':source})
    checkpoint=tmp_path/'checkpoint';checkpoint.mkdir()
    monkeypatch.setattr(runner,'verify_checkpoint',lambda path:{'revision':runner.REVISION})
    monkeypatch.setattr(runner,'plot_results',lambda p,i,path:path.write_bytes(b'SOFTWARE_VALIDATION_ONLY'))
    stages=[]
    def worker(runtime,requests,checkpoint,output,timeout):
        stages.append(requests.name)
        output.mkdir();results=output/'results';results.mkdir()
        policy=json.loads((requests/'policy.json').read_text())
        with (requests/'requests.jsonl').open() as stream:records=[json.loads(line) for line in stream]
        admitted=admitted_records(records,policy)
        predictions,failures,_=infer_records(admitted,ChronosSmallAdapter(FakeEngine()),policy['stage']=='pilot')
        assert not failures
        write_csv(results/'predictions.csv',predictions,FIELDS)
        summary={'failed_contexts':0,'successful_contexts':len(records),'pilot_repeats_equal':True}
        write_json(results/'worker_summary.json',summary)
        publish_manifest(results,['predictions.csv','worker_summary.json'],{'phase':'4.2'})
        return summary
    monkeypatch.setattr(runner,'run_worker',worker)
    original=runner.label_view;label_phases=[]
    out=tmp_path/'evaluation'
    def labels(path,ids,*,verify_seal):
        verify_seal()
        phases={splits['assignments'][fid] for fid in ids}
        label_phases.append(phases)
        if phases=={'validation'}:
            assert stages==['pilot','validation'] and not (out/'selection.json').exists()
        else:
            assert stages==['pilot','validation','test']
            assert (out/'selection.json').exists() and (out/'test_prediction_seal.json').exists()
        return original(path,ids,verify_seal=verify_seal)
    monkeypatch.setattr(runner,'label_view',labels)
    result=runner.run_chronos(bundle,history,baseline,smoke,sys.executable,checkpoint,out)
    assert result['status']=='PASS' and result['test_ids_unchanged']
    assert label_phases==[{'validation'},{'test_temporal','test_repository'}]
    assert verify_bundle(baseline)==frozen_baseline
    assert result['events'].index('all_temporal_and_held_test_predictions_sealed_before_test_labels') < result['events'].index('test_numerical_labels_loaded_after_seal')
    assert result['original_baseline_metrics_identical']
