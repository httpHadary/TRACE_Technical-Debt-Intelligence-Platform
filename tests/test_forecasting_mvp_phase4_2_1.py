"""Diagnostic-only hardening: typed recovery, fatal contracts and immutable inputs."""
from copy import deepcopy
import json

import pytest

from contracts import write_json,write_csv
from forecasting_mvp.chronos_adapter import ChronosSmallAdapter,NativeQuantileCrossingError
from forecasting_mvp.chronos_eval_worker import admitted_records,infer_records
import forecasting_mvp.chronos_eval_worker as worker
from forecasting_mvp.chronos_diagnostics import (CapturePipeline,raw_path_diagnostics,input_characteristics,
                                              published_interval_diagnostics,run_diagnostics)
from forecasting_mvp.io import publish_manifest
from test_forecasting_mvp_phase4_1 import FakeEngine,request
from test_forecasting_mvp_phase4_2 import prepared


def admitted():
    records,policy=prepared()
    return admitted_records(records,policy)


def test_only_typed_native_crossings_recover_with_explicit_no_interval_fallback():
    rows,failures,_=infer_records(admitted(),ChronosSmallAdapter(FakeEngine('crossing')),False)
    assert len(failures)==3 and len(rows)==9
    assert all(f['error_type']=='NativeQuantileCrossingError' for f in failures)
    assert all(r['inference_status']=='PERSISTENCE_FALLBACK' and r['prediction_minutes']==r['current_minutes']
               and r['q10'] is None and r['q90'] is None for r in rows)


@pytest.mark.parametrize('error',[
    RuntimeError('CPU execution failed'),MemoryError('out of memory'),AssertionError('invalid software state'),
    TypeError('unexpected return type'),KeyError('missing output key'),OSError('unexpected IO failure'),
    ValueError('Native quantile crossing; do not manufacture sorted quantiles'),
    ValueError('unexpected generic value error')])
def test_unexpected_software_runtime_errors_are_fatal_even_with_matching_message(error):
    class FailingAdapter:
        def predict_path(self,request):raise error
    with pytest.raises(type(error)) as caught:infer_records(admitted(),FailingAdapter(),False)
    assert caught.value is error


@pytest.mark.parametrize('defect',['shape','columns','timestamp','identity','nonfinite'])
def test_invalid_native_contract_never_becomes_persistence_fallback(defect):
    with pytest.raises(ValueError) as caught:
        infer_records(admitted(),ChronosSmallAdapter(FakeEngine(defect)),False)
    assert not isinstance(caught.value,NativeQuantileCrossingError)


@pytest.mark.parametrize('later_defect',['identity','timestamp','nonfinite'])
def test_early_crossing_cannot_mask_later_fatal_identity_or_numeric_contract(later_defect):
    class MixedDefects(FakeEngine):
        def predict_df(self,*args,**kwargs):
            frame=super().predict_df(*args,**kwargs)
            frame.loc[0,'0.1']=99.
            if later_defect=='identity':frame.loc[89,'item_id']='wrong-series'
            elif later_defect=='timestamp':frame.loc[89,'timestamp']+=__import__('pandas').Timedelta(days=1)
            else:frame.loc[89,'0.9']=float('nan')
            return frame
    with pytest.raises(ValueError) as caught:
        infer_records(admitted(),ChronosSmallAdapter(MixedDefects()),False)
    assert not isinstance(caught.value,NativeQuantileCrossingError)


@pytest.mark.parametrize('repeat_failure',[NativeQuantileCrossingError('crossing on repeat'),RuntimeError('runtime repeat failure')])
def test_valid_first_path_then_repeat_failure_aborts(repeat_failure):
    class FirstValid:
        calls=0
        def predict_path(self,request):
            self.calls+=1
            if self.calls==2:raise repeat_failure
            return ChronosSmallAdapter(FakeEngine()).predict_path(request)
    with pytest.raises(type(repeat_failure)) as caught:infer_records(admitted(),FirstValid(),True)
    assert caught.value is repeat_failure


def test_valid_paths_and_identical_repeats_keep_exact_original_values():
    rows,failures,_=infer_records(admitted(),ChronosSmallAdapter(FakeEngine()),True)
    assert failures==[] and len(rows)==9
    assert all(r['raw_q10']==-r['horizon_days'] and r['q10']==0
               and r['prediction_minutes']==r['horizon_days'] and r['q90']==2*r['horizon_days']
               and r['maximum_repeat_difference']==0 for r in rows)


def test_late_fatal_error_does_not_publish_partial_worker_results(tmp_path,monkeypatch):
    records,policy=prepared();root=tmp_path/'requests';root.mkdir()
    (root/'requests.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    write_json(root/'policy.json',policy);publish_manifest(root,['policy.json','requests.jsonl'],{'phase':'4.2'})
    monkeypatch.setattr(worker,'verify_checkpoint',lambda p:{})
    monkeypatch.setattr(worker.importlib.metadata,'version',lambda p:worker.PINNED_RUNTIME[p])
    class LateFailure:
        calls=0
        def predict_path(self,request):
            self.calls+=1
            if self.calls==2:raise MemoryError('fatal after a valid context')
            return ChronosSmallAdapter(FakeEngine()).predict_path(request)
    monkeypatch.setattr(worker.ChronosSmallAdapter,'load_cpu',lambda p:LateFailure())
    output=tmp_path/'unpublished'
    with pytest.raises(MemoryError):worker.execute(root,tmp_path/'checkpoint',output)
    assert not output.exists()


def test_top_level_fatal_boundary_returns_blocked_without_fallback(tmp_path,monkeypatch,capsys):
    def fail(*args):raise RuntimeError('fatal execution error')
    monkeypatch.setattr(worker,'execute',fail)
    monkeypatch.setattr('sys.argv',['worker','--requests',str(tmp_path),'--checkpoint',str(tmp_path),'--out',str(tmp_path/'out')])
    assert worker.main()==3
    result=json.loads(capsys.readouterr().out)
    assert result=={'status':'BLOCKED','error_type':'RuntimeError','error':'fatal execution error'}
    assert not (tmp_path/'out').exists()


def test_raw_diagnostic_magnitude_all_steps_endpoints_and_capture_invariance():
    engine=FakeEngine();capture=CapturePipeline(engine);adapter=ChronosSmallAdapter(capture);req=request()
    original=adapter.predict_path(req)
    frame=capture.result.copy()
    frame.loc[0,'0.1']=99.
    frame.loc[29,'0.1']=35.
    frame.loc[59,'0.9']=57.
    rows,summary=raw_path_diagnostics(frame,req)
    assert summary['crossing_steps']==[1,30,60]
    assert summary['lower_crossing_steps']==[1,30] and summary['upper_crossing_steps']==[60]
    assert summary['maximum_crossing_minutes']==98.
    assert [r['ordered'] for r in summary['selected_endpoints']]==[False,False,True]
    assert all(r['step_days'] in (30,60,90) for r in rows if r['selected_endpoint'])
    assert original==ChronosSmallAdapter(FakeEngine()).predict_path(req)
    assert frame.loc[0,'0.1']==99. and frame.loc[59,'0.9']==57.  # no sorting or correction
    bad=frame.copy();bad.loc[89,'item_id']='other'
    with pytest.raises(ValueError,match='identity'):raw_path_diagnostics(bad,req)


def test_past_input_characteristics_are_descriptive_only():
    record,req=admitted()[0]
    actual=input_characteristics(req,record['context'])
    assert actual['context_days']==90 and actual['distinct_measurements']==1
    assert actual['constant_history'] and actual['population_std_minutes']==0
    assert actual['past_value_transitions']==0 and actual['past_net_change_minutes']==0


def test_interval_diagnostics_read_published_metrics_only_no_new_labels(tmp_path,monkeypatch):
    data=[{'repository_id':'ALL','successes':10,'pooled_coverage80':.6,'collapsed_misses':2}]
    write_csv(tmp_path/'chronos_interval_metrics.csv',data,tuple(data[0]))
    result=published_interval_diagnostics(tmp_path)
    assert result[0]['pooled_misses']==4 and result[0]['noncollapsed_misses']==2
    data[0]['pooled_coverage80']=.65
    write_csv(tmp_path/'chronos_interval_metrics.csv',data,tuple(data[0]))
    with pytest.raises(ValueError,match='Nonintegral'):published_interval_diagnostics(tmp_path)


def test_diagnostic_scope_rejects_other_studies_before_inference_or_output(tmp_path,monkeypatch):
    import forecasting_mvp.chronos_diagnostics as diagnostic
    benchmark=tmp_path/'benchmark';benchmark.mkdir()
    monkeypatch.setattr(diagnostic,'verify_bundle',lambda p:{'metadata':{'phase':'4.2'}})
    monkeypatch.setattr(diagnostic,'read_json',lambda p:{'study_id':'different-study','failed_contexts':12})
    with pytest.raises(ValueError,match='published 12-failure'):
        run_diagnostics(benchmark,tmp_path/'checkpoint','not-a-runtime',tmp_path/'out')
    assert not (tmp_path/'out').exists()
    with pytest.raises(ValueError,match='separate'):
        run_diagnostics(benchmark,tmp_path/'checkpoint','not-a-runtime',benchmark/'out')
