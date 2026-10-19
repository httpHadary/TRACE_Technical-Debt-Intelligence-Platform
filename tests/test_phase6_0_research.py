"""Deterministic software-only coverage. Never loads a checkpoint or real labels."""
from dataclasses import replace
from datetime import timedelta
import copy,json,math,subprocess,sys
from pathlib import Path
import pytest
from forecasting_research.phase6_0 import STATUS,UNIT
from forecasting_research.phase6_0.contracts import Request,iso,utc,response,validate_response
from forecasting_research.phase6_0.synthetic import generate,population,SCENARIOS,CHRONOS_CASES
from forecasting_research.phase6_0.predictors import baseline,bridge,reconstruct,blend,gate,change_features
from forecasting_research.phase6_0.evaluation import metrics,score
from forecasting_research.phase6_0 import artifacts,runtime

@pytest.mark.parametrize('scenario',SCENARIOS)
def test_generator_deterministic_and_exact_targets(scenario):
    c=generate(scenario,1);assert c==generate(scenario,1)
    q=c.request;assert Request.from_dict(q.as_dict())==q
    assert all(utc(t)<=utc(q.origin_utc) for t in q.timestamps)
    assert len(c.future_daily_truth)==90
    for h,v in c.targets().items():
        assert c.future_timestamps[h-1]==q.endpoint(h) and v==c.future_daily_truth[h-1] and math.isfinite(v) and v>=0
    assert q.status==STATUS and q.unit==UNIT

@pytest.mark.parametrize('key,value', [('target',1),('actual',1),('split','test'),('endpoint_value',5),('future_values',[1])])
def test_no_label_or_evaluation_fields(key,value):
    d=generate('constant').request.as_dict();d[key]=value
    with pytest.raises(ValueError):Request.from_dict(d)

@pytest.mark.parametrize('field,value',[('version','v2'),('status','REAL'),('unit','hours'),('horizons',[30,60,91]),('case_id','real-repo'),('origin_utc','2026-01-01')])
def test_wrong_contract(field,value):
    d=generate('constant').request.as_dict();d[field]=value
    with pytest.raises(ValueError):Request.from_dict(d)

@pytest.mark.parametrize('value',[True,-1,float('nan'),float('inf'),'10'])
def test_invalid_values(value):
    d=generate('constant').request.as_dict();d['values'][0]=value
    with pytest.raises(ValueError):Request.from_dict(d)

@pytest.mark.parametrize('change',['future','duplicate','reorder','missing_reason','false_null','no_origin','mutable'])
def test_temporal_and_missing_protection(change):
    d=generate('constant').request.as_dict()
    if change=='future':d['timestamps'][-1]='2026-01-02T00:00:00Z'
    if change=='duplicate':d['timestamps'][1]=d['timestamps'][0]
    if change=='reorder':d['timestamps'][:2]=reversed(d['timestamps'][:2])
    if change=='missing_reason':d['values'][0]=None
    if change=='false_null':d['reasons'][0]='SYNTHETIC_UNOBSERVED'
    if change=='no_origin':d['timestamps']=d['timestamps'][:-1];d['values']=d['values'][:-1];d['reasons']=d['reasons'][:-1]
    with pytest.raises(ValueError):
        if change=='mutable':Request(**d)
        else:Request.from_dict(d)

@pytest.mark.parametrize('model',['persistence','rolling_mean','linear_trend'])
def test_constant_and_zero_expected(model):
    for scenario in ('constant','near_zero'):
        q=generate(scenario).request;r=baseline(q,model)
        assert validate_response(q,r,model)==r
        assert all(p['point']==q.values[-1] for p in r['path'])
        assert all(p['q10'] is None for p in r['path'])

@pytest.mark.parametrize('scenario,slope',[('slow_increase',.25),('slow_decrease',-.25)])
def test_exact_linear_process(scenario,slope):
    c=generate(scenario);r=baseline(c.request,'linear_trend')
    for h,v in c.targets().items():assert r['path'][h-1]['point']==pytest.approx(v)


def test_missing_not_zero_or_carry_and_irregular_elapsed_time():
    q=generate('sparse').request;assert q.values.count(None)>70
    assert baseline(q)['path'][0]['point']==q.values[-1]
    with pytest.raises(ValueError,match='INSUFFICIENT'):baseline(q,'rolling_mean')
    with pytest.raises(ValueError):bridge(q)
    q=generate('irregular').request;assert len(q.values)<90
    assert all(p['point']>=0 for p in baseline(q,'linear_trend')['path'])
    with pytest.raises(ValueError):bridge(q)
    q=replace(q,values=(*q.values[:-1],None),reasons=(*q.reasons[:-1],'SYNTHETIC_UNOBSERVED'))
    with pytest.raises(ValueError,match='MISSING_ORIGIN'):baseline(q)


def test_past_indistinguishable_quiet_future_change():
    a,b=generate('constant'),generate('quiet_then_change')
    assert a.request.values==b.request.values
    assert [p['point'] for p in baseline(a.request)['path']]==[p['point'] for p in baseline(b.request)['path']]
    assert a.targets()!=b.targets() # No forecasting method can see the future process switch.


def path(q,a=1,b=2,c=3):
    return [dict(timestamp_utc=iso(utc(q.origin_utc)+timedelta(days=i)),raw_point=b,raw_q10=a,raw_q50=b,raw_q90=c) for i in range(1,91)]

@pytest.mark.parametrize('issue',['cross','nonfinite','timestamp','shape','wrong_point','identity','unit','extra','negative_quantile'])
def test_response_policy(issue):
    q=generate('constant').request;p=path(q)
    if issue=='cross':p[0]['raw_q10']=4
    if issue=='nonfinite':p[2]['raw_q90']=float('nan')
    if issue=='timestamp':p[-1]['timestamp_utc']=q.endpoint(30)
    if issue=='shape':p.pop()
    if issue=='wrong_point':p[0]['raw_point']=1
    if issue=='negative_quantile':
        r=response(q,'fake',path(q,-3,-2,-1),quantiles=True)
        assert r['path'][0]['point']==0 and r['path'][0]['raw_point']==-2;return
    with pytest.raises(ValueError):
        r=response(q,'fake',p,quantiles=True)
        if issue=='identity':r['request_id']='bad'
        if issue=='unit':r['unit']='hours'
        if issue=='extra':r['target']=0
        validate_response(q,r,'fake')


def test_macro_pooled_and_zero_skill_and_uncertainty():
    rows=[dict(repository_id='a',prediction=0,actual=0,current=0,q10=0,q90=0)]*9
    rows+= [dict(repository_id='b',prediction=10,actual=0,current=20,q10=0,q90=10)]
    m=metrics(rows);assert m['macro_mae']==5 and m['pooled_mae']==1 and m['macro_rmse']==5
    assert m['skill']==.5 and m['macro_coverage80']==1
    assert m==metrics(rows) and m['paired_gain_ci95'] is not None
    assert metrics(rows[:1])['skill'] is None and metrics([]) is None


def test_scoring_population_and_identity_rejection():
    c=generate('constant');q=c.request;r=baseline(q)
    assert score([c],{q.case_id:r},'persistence')['metrics']['90/all']['macro_mae']==0
    with pytest.raises(ValueError):score([c],{},'persistence')
    r['case_id']='wrong'
    with pytest.raises(ValueError):score([c],{q.case_id:r},'persistence')


def test_change_aware_interfaces_and_observation_censoring():
    assert reconstruct(5,-10)==0 and reconstruct(5,2)==7
    assert blend(10,20,0)==10 and blend(10,20,1)==20
    assert gate(10,20,.2,.5)==10 and gate(10,20,.8,.5)==30
    for p in (-.1,1.1,float('nan')):
        with pytest.raises(ValueError):blend(10,20,p)
        with pytest.raises(ValueError):gate(10,20,p,.5)
    assert change_features(generate('constant').request)['days_since_last_observed_transition'] is None
    assert change_features(generate('sparse').request)['unobserved_changes_possible']


def test_generator_population_registered_chronos_subset():
    cases=population();assert len(cases)==42 and len({c.request.identity for c in cases})==42
    assert len(CHRONOS_CASES)==10
    assert all(generate(s,r).request.complete_daily() for s,r in CHRONOS_CASES)


def test_output_fresh_claim_seal_and_symlink(tmp_path,monkeypatch):
    monkeypatch.setattr(artifacts,'TASK_ROOT',tmp_path)
    root=artifacts.fresh(tmp_path/'new');artifacts.write(root/'x.json',{'a':1});files=artifacts.seal(root)
    assert files['x.json']==artifacts.sha(root/'x.json')
    with pytest.raises(FileExistsError):artifacts.fresh(root)
    with pytest.raises(ValueError):artifacts.seal(root)
    link=tmp_path/'alias';link.symlink_to(root,target_is_directory=True)
    with pytest.raises(ValueError):artifacts.fresh(link/'new')
    with pytest.raises(ValueError):artifacts.fresh(tmp_path.parent/'escape')
    with pytest.raises(ValueError):artifacts.fresh(tmp_path/'..'/'escaped-research-task')


def test_resource_ceilings_and_real_timeout(tmp_path):
    with pytest.raises(ValueError):runtime.supervise([],tmp_path,timeout=901)
    receipt=runtime.supervise([sys.executable,'-c','import time;time.sleep(2)'],tmp_path,timeout=.08)
    assert receipt['status']=='BLOCKED_RUNTIME' and receipt['failure']=='TIMEOUT'


def test_kernel_network_denial_child_no_model():
    p=subprocess.run([sys.executable,'-c','from forecasting_research.phase6_0.runtime import deny_network;print(deny_network())'],capture_output=True,text=True,timeout=10)
    assert p.returncode==0 and 'SECCOMP_SOCKET_DENIED' in p.stdout,p.stderr


def test_chronos_recoverable_vs_unexpected(monkeypatch):
    from forecasting_mvp.chronos_adapter import ChronosSmallAdapter,NativeQuantileCrossingError
    from forecasting_research.phase6_0.chronos import predict
    q=generate('constant').request
    class A: pipeline=object()
    def crossing(self,req):
        self.pipeline.rows=[{'0.1':3,'0.5':2,'0.9':4}]
        raise NativeQuantileCrossingError('test')
    monkeypatch.setattr(ChronosSmallAdapter,'predict_path',crossing)
    r=predict(A(),q);assert r['failure']=='NATIVE_QUANTILE_CROSSING' and r['crossings'][0]['step']==1
    def fatal(self,req):raise RuntimeError('software failure')
    monkeypatch.setattr(ChronosSmallAdapter,'predict_path',fatal)
    with pytest.raises(RuntimeError,match='software failure'):predict(A(),q)


def test_registry_no_implicit_fallback_or_new_runtime():
    from forecasting_research.phase6_0.registry import compatible,registry
    q=generate('constant').request
    assert compatible('chronos_small',q,execute=True)['runtime_verified']
    assert compatible('timesfm_2_5',q)['api_compatible']
    for key in ('ttm_daily','ttm_short','ttm_r3'):
        with pytest.raises(ValueError):compatible(key,q)
    for key in ('ttm_daily','timesfm_2_5'):
        with pytest.raises(ValueError):compatible(key,q,execute=True)
    assert registry()['ttm_daily']['revision']=='3442406f106122f414a11f72b4ebfe4878bec89d'
    assert registry()['timesfm_2_5']['license']=='Apache-2.0'


def test_failure_identity_and_response_bool_rejected():
    c=generate('constant');q=c.request
    with pytest.raises(ValueError):score([c],{q.case_id:{'failure':'NATIVE_QUANTILE_CROSSING','request_id':'wrong'}},'chronos_small')
    r=response(q,'fake',path(q,0,1,2),quantiles=True);r['path'][0]['point']=True
    with pytest.raises(ValueError):validate_response(q,r,'fake')


def test_seal_precedes_label_scoring(tmp_path,monkeypatch):
    from forecasting_research.phase6_0 import benchmark
    monkeypatch.setattr(artifacts,'TASK_ROOT',tmp_path)
    monkeypatch.setattr(benchmark,'population',lambda:[generate('constant'),generate('slow_increase')])
    score_function=benchmark.score
    def guarded_score(*args,**kwargs):
        root=tmp_path/'run'
        seal=json.loads((root/'prediction_seal.json').read_text())
        assert seal['labels_scored'] is False and artifacts.sha(root/'predictions.json')==seal['sha256']
        return score_function(*args,**kwargs)
    monkeypatch.setattr(benchmark,'score',guarded_score)
    result=benchmark.run(tmp_path/'run');assert result['persistence']['successful_cases']==2
    assert (tmp_path/'run/manifest.json').exists()


def test_published_summary_arithmetic_only(tmp_path):
    from forecasting_research.phase6_0.summary_audit import audit
    result=audit(tmp_path/'audit.json')
    assert result['checks']==216 and result['raw_label_files_opened']==0
    rows=[r for r in result['point_summaries'] if r['horizon_days']=='90' and r['subset']=='all' and r['evaluation_phase']=='test_temporal']
    assert round(next(r for r in rows if r['model']=='persistence')['repository_macro_mae'],3)==148.708
    assert round(next(r for r in rows if r['model']=='chronos_small')['repository_macro_mae'],3)==157.478


def test_request_identity_does_not_expose_generator_scenario():
    for c in population():
        assert c.scenario not in c.request.case_id
        assert len(c.request.case_id)==42
        assert set(c.request.as_dict())=={'case_id','origin_utc','timestamps','values','reasons','horizons','version','status','unit'}
        assert 'future_daily_truth' not in c.request.as_dict()


def test_unexpected_worker_exit_is_not_success(tmp_path):
    receipt=runtime.supervise([sys.executable,'-c','raise RuntimeError("software failure")'],tmp_path)
    assert receipt['status']=='BLOCKED_RUNTIME' and receipt['failure']=='WORKER_FAILED'
    assert receipt['exit_code']!=0 and 'software failure' in (tmp_path/'worker.log').read_text()


def test_missing_pinned_environment_reports_blocked(tmp_path,monkeypatch):
    monkeypatch.setattr(artifacts,'TASK_ROOT',tmp_path)
    original=Path.is_file
    def probe(p):
        return False if str(p).endswith('.venv-chronos-cpu/bin/python') else original(p)
    monkeypatch.setattr(Path,'is_file',probe)
    result=runtime.run_chronos(tmp_path/'blocked')
    assert result=={'status':'BLOCKED_RUNTIME','failure':'PINNED_ENVIRONMENT_MISSING'}
    assert (tmp_path/'blocked/manifest.json').exists()
