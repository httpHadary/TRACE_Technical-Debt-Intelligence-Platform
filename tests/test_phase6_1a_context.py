"""Software-only paired-context tests. No checkpoint/model execution."""
from pathlib import Path
from dataclasses import replace
from datetime import timedelta
import json,copy,sys
import pytest
import pandas as pd
from forecasting_research.phase6_0.contracts import Request,response,utc,iso
from forecasting_research.phase6_0.predictors import baseline
from forecasting_research.phase6_1a.population import Spec,history,short,future,population,specs,SCENARIOS
from forecasting_research.phase6_1a.adapter import ContextAdapter,NativePathCrossing
from forecasting_research.phase6_1a import study
from forecasting_research.phase6_1a.evaluate import endpoint_rows,summarize,denominator,validate_crossing,read_endpoints
from forecasting_research.phase6_1a.run import supervise

@pytest.mark.parametrize('scenario',SCENARIOS)
def test_generated_long_short_shared_origin_independent_future(scenario):
    s=Spec(scenario,0);long=history(s);truth=future(s)
    assert long==history(s) and truth==future(s)
    assert all(utc(t)<=utc(long.origin_utc) for t in long.timestamps)
    assert s.scenario not in long.case_id
    if scenario not in ('sparse','irregular'):
        assert long.complete_daily(512);a=short(long);assert a.complete_daily(90)
        assert a.values==long.values[-90:] and a.timestamps==long.timestamps[-90:] and a.case_id==long.case_id
        assert a.origin_utc==long.origin_utc
        for h in (30,60,90):assert truth[h]['timestamp_utc']==a.endpoint(h)==long.endpoint(h)
    else:
        assert not long.complete_daily(512)
        with pytest.raises(ValueError):short(long)
    assert set(truth)=={30,60,90}


def test_population_complete_and_exclusions():
    p=population();assert len(p)==42 and sum(r['eligible'] for r in p)==36
    assert len({r['case_id'] for r in p})==42
    assert all(r['history_positions']==512 and r['known']==512 for r in p if r['eligible'])
    assert {r['scenario'] for r in p if not r['eligible']}=={'sparse','irregular'}
    assert all(s.seed!=s.seed+100000!=s.seed+200000 for s in specs())


def test_analytic_truth_values_and_unobservable_jump():
    a,b=Spec('constant',0),Spec('quiet_then_change',0)
    assert history(a).values==history(b).values
    assert future(a)[30]['value']==100 and future(b)[30]['value']==160
    c=Spec('slow_increase',0)
    for h in (30,60,90):assert future(c)[h]['value']==300+.25*h
    assert denominator(short(history(a)))==0
    assert denominator(short(history(c)))==.25
    assert denominator(short(history(Spec('slow_increase',2))))>0


class FakePipeline:
    model_context_length=8192;model_prediction_length=1024
    def __init__(self,issue=None):self.issue=issue;self.calls=[]
    def predict_df(self,df,prediction_length,quantile_levels,context_length,freq,**kwargs):
        self.calls.append((len(df),prediction_length,quantile_levels,context_length,freq,kwargs))
        origin=pd.Timestamp(df['timestamp'].iloc[-1])
        rows=[{'item_id':'series','timestamp':origin+pd.Timedelta(days=i),'target_name':'debt_minutes',
               'predictions':1.,'0.1':-2.,'0.5':-1.,'0.9':3.} for i in range(1,91)]
        if self.issue=='cross':rows[0]['0.1']=2.
        if self.issue=='late_identity':rows[0]['0.1']=2.;rows[-1]['item_id']='wrong'
        if self.issue=='time':rows[-1]['timestamp']+=pd.Timedelta(days=1)
        if self.issue=='nan':rows[4]['0.9']=float('nan')
        if self.issue=='shape':rows.pop()
        return pd.DataFrame(rows)

@pytest.mark.parametrize('length',[90,512])
def test_adapter_exact_api_input_and_nonnegative_raw_policy(length):
    engine=FakePipeline();a=ContextAdapter(engine);q=history(Spec('constant',0));q=short(q) if length==90 else q
    r=a.predict(q,length)
    assert engine.calls[0][:5]==(length,90,[.1,.5,.9],length,'D')
    assert engine.calls[0][5]['cross_learning'] is False
    assert r['path'][89]['timestamp_utc']==q.endpoint(90)
    assert r['path'][0]['point']==0 and r['path'][0]['raw_point']==-1 and r['path'][0]['q10']==0

@pytest.mark.parametrize('issue',['cross','late_identity','time','nan','shape'])
def test_native_path_errors_precedence(issue):
    a=ContextAdapter(FakePipeline(issue));q=history(Spec('constant',0))
    with pytest.raises(NativePathCrossing if issue=='cross' else ValueError) as err:a.predict(q,512)
    if issue=='cross':
        exc=err.value;assert exc.steps==[1]
        failure=dict(failure='NATIVE_QUANTILE_CROSSING',request_id=q.identity,crossing_steps=exc.steps,invalid_raw_path=exc.path)
        validate_crossing(q,failure)
        failure['request_id']='wrong'
        with pytest.raises(ValueError):validate_crossing(q,failure)
    else:assert not isinstance(err.value,NativePathCrossing)

@pytest.mark.parametrize('kind',['91','sparse','irregular','wrong_length','future','label','unit','mutable'])
def test_incompatible_requests_rejected_before_pipeline(kind):
    p=FakePipeline();a=ContextAdapter(p);q=history(Spec('constant',0))
    with pytest.raises(ValueError):
        if kind=='91':a.predict(q,91)
        elif kind in ('sparse','irregular'):a.predict(history(Spec(kind,0)),512)
        elif kind=='wrong_length':a.predict(short(q),512)
        else:
            d=q.as_dict()
            if kind=='future':d['timestamps'][-1]=q.endpoint(30)
            elif kind=='label':d['actual']=42
            elif kind=='unit':d['unit']='hours'
            if kind=='mutable':Request(**d)
            else:a.predict(Request.from_dict(d),512)
    assert p.calls==[]


def test_missing_api_or_capacity():
    p=FakePipeline();p.model_context_length=128
    with pytest.raises(ValueError):ContextAdapter(p)
    class NoAPI:
        def predict_df(self,df):pass
    with pytest.raises(ValueError):ContextAdapter(NoAPI())


def synthetic_predictions(reg,requests):
    from forecasting_research.phase6_1a.study import MODELS
    result={m:{} for m in MODELS}
    for cid,pair in requests.items():
        a,b=(Request.from_dict(pair[k]) for k in ('90','512'))
        for m in MODELS[:3]:result[m][cid]=baseline(a,m)
        for m,q in [('chronos90',a),('chronos512',b)]:
            path=[dict(timestamp_utc=iso(utc(q.origin_utc)+timedelta(days=i)),raw_point=q.values[-1],raw_q10=q.values[-1],raw_q50=q.values[-1],raw_q90=q.values[-1]) for i in range(1,91)]
            result[m][cid]=response(q,m,path,quantiles=True)
    return result

@pytest.fixture
def prepared(tmp_path,monkeypatch):
    monkeypatch.setattr(study,'ROOT',tmp_path)
    reg=study.prepare(tmp_path/'study');r,requests=study.verify(tmp_path/'study')
    return tmp_path/'study',reg,requests


def test_frozen_registration_precedes_predictions_and_cannot_rewrite(prepared):
    path,reg,requests=prepared
    assert len(requests)==36 and len(reg['population'])==42 and not (path/'predictions.json').exists()
    assert reg['limits']['wall_seconds']==900
    assert reg['runtime']['chronos-forecasting']=='2.3.2'
    with pytest.raises(FileExistsError):study.prepare(path)
    d=json.loads((path/'requests.json').read_text());d[next(iter(d))]['90']['values'][-1]=100000
    (path/'requests.json').write_text(json.dumps(d))
    with pytest.raises(ValueError):study.verify(path)


def test_endpoint_scoring_is_paired_exact_and_reproducible(prepared,tmp_path):
    path,reg,requests=prepared;pred=synthetic_predictions(reg,requests)
    rows=endpoint_rows(reg,requests,pred);r=summarize(rows,reg)
    assert len(rows)==540 and r['eligible_cases']==36 and len(r['all_method_matched_ids'])==36
    assert all(r['paired'][str(h)]['mean_absolute_error_512_minus_90']==0 for h in (30,60,90))
    import csv
    with (tmp_path/'rows.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    assert summarize(read_endpoints(tmp_path/'rows.csv'),reg)==r
    assert r['all_method_matched']['persistence']['30']['all']['normalization_undefined']>0
    rows[0]['actual']+=1
    with pytest.raises(ValueError):summarize(rows,reg)


def test_failure_population_retained_no_silent_fallback(prepared):
    path,reg,requests=prepared;pred=synthetic_predictions(reg,requests);cid=next(iter(requests))
    q=Request.from_dict(requests[cid]['512']);engine=ContextAdapter(FakePipeline('cross'))
    try:engine.predict(q,512)
    except NativePathCrossing as exc:
        pred['chronos512'][cid]=dict(failure='NATIVE_QUANTILE_CROSSING',request_id=q.identity,crossing_steps=exc.steps,invalid_raw_path=exc.path)
    rows=endpoint_rows(reg,requests,pred);r=summarize(rows,reg)
    assert len(rows)==540 and r['successful_contexts']['chronos512']==35 and len(r['native_pair_ids'])==35
    assert r['failure_rate']['chronos512']==1/36
    failed=[x for x in rows if x['status']=='NATIVE_FAILURE'];assert len(failed)==3 and all(x['prediction'] is None for x in failed)
    with pytest.raises(ValueError):summarize(rows[:-1],reg)


def test_path_protection(tmp_path,monkeypatch):
    monkeypatch.setattr(study,'ROOT',tmp_path)
    for p in (tmp_path,tmp_path/'..'/'escape',tmp_path.parent/'outside'):
        with pytest.raises(ValueError):study.safe(p)
    link=tmp_path/'alias';link.symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError):study.safe(link/'output')


def test_timeout_and_fatal_exit(tmp_path):
    a=tmp_path/'a';a.mkdir();r=supervise([sys.executable,'-c','import time;time.sleep(2)'],a,timeout=.05)
    assert r['failure']=='TIMEOUT' and r['status']=='BLOCKED_RUNTIME'
    b=tmp_path/'b';b.mkdir();r=supervise([sys.executable,'-c','raise RuntimeError("fatal")'],b)
    assert r['failure']=='WORKER_FAILED' and r['exit_code']!=0
    with pytest.raises(ValueError):supervise([],tmp_path,timeout=901)


def test_seal_before_truth_and_fresh_exclusive_attempt(prepared,monkeypatch):
    from forecasting_research.phase6_1a import evaluate as module
    from forecasting_research.phase6_0.artifacts import write,sha
    path,reg,requests=prepared
    with pytest.raises(FileNotFoundError):module.evaluate(path,reg,requests)
    pred=synthetic_predictions(reg,requests);h=write(path/'predictions.json',pred)
    write(path/'prediction_seal.json',dict(sha256=h,labels_scored=False,registration_sha256=sha(path/'registration.json')))
    result=module.evaluate(path,reg,requests);assert result['eligible_cases']==36
    assert sha(path/'predictions.json')==h
    (path/'prediction_seal.json').write_text(json.dumps({'sha256':h,'labels_scored':True}))
    with pytest.raises(ValueError):module.evaluate(path,reg,requests)


def test_resource_admission_claim_is_consumed_without_worker(prepared,monkeypatch):
    from forecasting_research.phase6_1a import run as runner
    path,reg,requests=prepared
    monkeypatch.setattr(runner,'admission',lambda path:dict(eligible=False,available_host_ram_bytes=1))
    def forbidden(*args,**kwargs):raise AssertionError('Worker must not start')
    monkeypatch.setattr(runner,'supervise',forbidden)
    result=runner.run(path);assert result['status']=='BLOCKED_RESOURCES'
    assert (path/'attempt.json').exists() and (path/'manifest.json').exists()
    with pytest.raises(FileExistsError):runner.run(path)
