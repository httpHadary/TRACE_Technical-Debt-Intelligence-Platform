"""Contract/failure tests with fake engines. Real six-context smoke is separate."""
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
import sys

import pandas as pd
import pytest

from contracts import digest, write_json
from forecasting_mvp.chronos_adapter import ChronosSmallAdapter, verify_checkpoint, MODEL_ID, REVISION
from forecasting_mvp.chronos_smoke import supervise, prepare_smoke
from forecasting_mvp.chronos_smoke_worker import validate_records,validate_runtime_versions,PINNED_RUNTIME
from forecasting_mvp.contracts import TargetContract, utc_iso, utc_timestamp
from forecasting_mvp.io import verify_bundle, publish_manifest
from forecasting_mvp.prediction_input import admit_prediction_input
from test_forecasting_mvp_phase2_1 import make_context
from test_forecasting_mvp_phase3 import replay_fixture


def request():
    context = make_context()
    return admit_prediction_input(context,90,expected_origin_utc=context["origin_utc"],
                                  measurement_times={"past":"2000-01-01T00:00:00Z"})


class FakeEngine:
    def __init__(self, defect=None):
        self.defect = defect
        self.inputs = []

    def predict_df(self,frame,**kwargs):
        assert set(frame.columns) == {"item_id","timestamp","debt_minutes"}
        assert frame.timestamp.to_numpy().dtype == "datetime64[ns]"  # upstream int64-view compatibility
        assert frame.timestamp.dt.tz is None
        assert kwargs == {"prediction_length":90,"quantile_levels":[.1,.5,.9],"id_column":"item_id",
            "timestamp_column":"timestamp","target":"debt_minutes","context_length":90,"batch_size":1,
            "cross_learning":False,"validate_inputs":True,"freq":"D"}
        self.inputs.append(frame.copy())
        future = pd.date_range(frame.timestamp.iloc[-1]+pd.Timedelta(days=1),periods=90,freq="D")
        result = pd.DataFrame({"item_id":["series"]*90,"timestamp":future,"target_name":["debt_minutes"]*90,
                               "predictions":[999999.]*90,"0.1":[-float(i) for i in range(1,91)],
                               "0.5":[float(i) for i in range(1,91)],"0.9":[2.*i for i in range(1,91)]})
        if self.defect == "shape":result=result.iloc[:-1]
        elif self.defect == "columns":result["actual_minutes"]=123.
        elif self.defect == "timestamp":result.loc[0,"timestamp"]+=pd.Timedelta(days=1)
        elif self.defect == "identity":result.loc[0,"item_id"]="other-series"
        elif self.defect == "nonfinite":result.loc[0,"0.5"]=float("nan")
        elif self.defect == "crossing":result.loc[0,"0.1"]=99.
        return result


def test_cpu_boundary_shape_quantile_units_and_exact_horizons():
    engine = FakeEngine()
    admitted = request()
    path = ChronosSmallAdapter(engine).predict_path(admitted)
    assert len(path) == 90
    for h in (30,60,90):
        point = path[h-1]
        assert point["timestamp"] == TargetContract(h).endpoint(admitted.origin_utc)
        assert point["q50"] == h and point["raw_q10"] == -h and point["q10"] == 0
    assert path == ChronosSmallAdapter(engine).predict_path(admitted)
    assert utc_timestamp(engine.inputs[0].timestamp.iloc[-1].tz_localize("UTC")) == utc_timestamp(admitted.origin_utc)
    assert all(utc_timestamp(t.tz_localize("UTC")) <= utc_timestamp(admitted.origin_utc) for t in engine.inputs[0].timestamp)


@pytest.mark.parametrize("defect,error", [("shape","shape"),("columns","shape"),("timestamp","timestamp"),
    ("identity","identity"),("nonfinite","Nonfinite"),("crossing","crossing")])
def test_reject_malformed_native_outputs(defect,error):
    with pytest.raises(ValueError,match=error):
        ChronosSmallAdapter(FakeEngine(defect)).predict_path(request())


def test_adapter_cannot_receive_labels_or_an_unbound_request():
    with pytest.raises(ValueError,match="Admitted"):
        ChronosSmallAdapter(FakeEngine()).predict_path({"values":[1.]*90,"actual_minutes":7.})
    context=make_context()
    context['evaluation_phase']='test_temporal'
    with pytest.raises(ValueError,match="allowlisted"):
        admit_prediction_input(context,90,expected_origin_utc=context['origin_utc'],measurement_times={})


def sample_records():
    records=[]
    for phase in ('train','validation'):
        for pattern in ('constant','increasing','decreasing'):
            context=make_context(repo=phase+'-'+pattern)
            sid=digest(['phase4_1_metadata_smoke_v1',phase,pattern,context['context_id']])
            forecasts=[]
            for h in (30,60,90):
                target=TargetContract(h,context_policy='core90_90_days')
                forecasts.append({'forecast_id':digest([context['context_id'],target.target_id]),'context_id':context['context_id'],
                    'repository_id':context['repository_id'],'track':'core90','origin_utc':context['origin_utc'],'horizon_days':h,
                    'endpoint_utc':target.endpoint(context['origin_utc']),'evaluation_phase':phase})
            records.append({'sample_id':sid,'evaluation_phase':phase,'pattern':pattern,'context':context,
                            'measurement_times':{'past':'2000-01-01T00:00:00Z'},'forecasts':forecasts})
    policy={'held_repository_ids':['held-repo'], 'samples':[{'sample_id':r['sample_id'],
        'forecast_ids':[f['forecast_id'] for f in r['forecasts']]} for r in records]}
    return records,policy


@pytest.mark.parametrize('defect',['test_phase','held_repo','wrong_horizon','target_column','future_reference','duplicate_sample'])
def test_worker_rejects_forbidden_records_before_loading_model(defect):
    records,policy=sample_records()
    assert len(validate_records(records,policy))==6
    if defect=='test_phase':records[0]['evaluation_phase']='test_temporal'
    elif defect=='held_repo':policy['held_repository_ids'].append(records[0]['context']['repository_id'])
    elif defect=='wrong_horizon':records[0]['forecasts'][0]['horizon_days']=91
    elif defect=='target_column':records[0]['forecasts'][0]['actual_minutes']=123.
    elif defect=='future_reference':records[0]['measurement_times']['past']='2099-01-01T00:00:00Z'
    else:records.append(deepcopy(records[0]))
    with pytest.raises(ValueError):validate_records(records,policy)


def test_supervisor_timeout_memory_and_worker_failure(tmp_path):
    for name,args,options,expected in (
        ('timeout',['-c','import time; time.sleep(5)'],{'timeout':.1},'SMOKE_TIMEOUT'),
        ('memory',['-c','import time; x=bytearray(8*1024*1024); time.sleep(5)'],{'max_rss_bytes':1024*1024},'SMOKE_MEMORY_LIMIT'),
        ('failed',['-c','raise RuntimeError("software_failure")'],{},'WORKER_FAILED')):
        output=tmp_path/name;output.mkdir()
        result=supervise([sys.executable,*args],output,**options)
        assert result['status']=='BLOCKED' and result['failure']==expected
        assert result['elapsed_seconds']<5


def test_unavailable_pattern_cells_block_without_reselection(tmp_path):
    bundle,history,_,splits=replay_fixture(tmp_path)
    baselines=tmp_path/'baselines';baselines.mkdir()
    frozen=verify_bundle(bundle)
    write_json(baselines/'study.json',{'frozen_split_id':splits['split_id'],'frozen_input_hashes':frozen['artifacts']})
    publish_manifest(baselines,['study.json'],{'phase':3,'source_sha256':frozen['metadata']['source_sha256']})
    with pytest.raises(ValueError,match='pattern cells'):
        prepare_smoke(bundle,history,baselines,Path(__file__).resolve().parents[1]/'forecasting_mvp/study.phase0.json',tmp_path/'requests')
    assert not (tmp_path/'requests').exists()


def test_checkpoint_revision_and_weight_pins_are_required(tmp_path):
    write_json(tmp_path/'checkpoint_admission.json',{'model_id':MODEL_ID,'revision':'main','license':'Apache-2.0','artifacts':{}})
    with pytest.raises(ValueError,match='immutable'):
        verify_checkpoint(tmp_path)
    write_json(tmp_path/'checkpoint_admission.json',{'model_id':MODEL_ID,'revision':REVISION,'license':'Apache-2.0','artifacts':{}})
    with pytest.raises(ValueError,match='weight'):
        verify_checkpoint(tmp_path)


@pytest.mark.parametrize('package',['numpy','pandas'])
def test_numerical_runtime_versions_cannot_drift(package):
    validate_runtime_versions(dict(PINNED_RUNTIME))
    versions={**PINNED_RUNTIME,package:'unregistered-version'}
    with pytest.raises(ValueError,match='Pinned'):
        validate_runtime_versions(versions)
