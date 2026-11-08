"""Deterministic synthetic mechanics; never import or execute pretrained models."""
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
import ast
import json
import math
import numpy as np
import pytest
from forecasting_research.phase6_0.contracts import Request, utc, iso, digest
from forecasting_research.phase6_0.artifacts import write, sha
from forecasting_research.phase6_0.predictors import reconstruct, gate, blend
from forecasting_research.phase6_2 import HORIZONS, STATUS
from forecasting_research.phase6_2.features import extract, baseline, NAMES
from forecasting_research.phase6_2.population import specs, generate, population, FAMILIES, OOD
from forecasting_research.phase6_2.models import (fit, predict, configs, probability, logistic, transform_fit,
    transform, weighted_quantile, mixture, METHODS)
from forecasting_research.phase6_2.study import POLICY, LIMITS, prepare, verify, safe, Labels, prediction_seal, verify_prediction_seal
from forecasting_research.phase6_2.worker import select, calibrate, validate_predictions
from forecasting_research.phase6_2.evaluation import forecast_metrics, classification_metrics, interval_metrics, paired
from forecasting_research.phase6_2.run import limit_failure


def request(values=(1.,2.,3.,4.)):
    req,_,_ = generate(specs()[0])
    origin = utc(req.origin_utc)
    stamps = tuple(iso(origin-timedelta(days=len(values)-1-i)) for i in range(len(values)))
    return replace(req,timestamps=stamps,values=tuple(values),reasons=tuple(None if v is not None else 'SYNTHETIC_UNOBSERVED' for v in values))


@pytest.fixture(scope='module')
def cases():
    return population()


@pytest.fixture(scope='module')
def state(cases):
    chosen = [c for c in cases if c['spec']['partition']=='train' and c['spec']['index']<2]
    return fit([dict(partition='train',request=c['request'],targets={str(h):v for h,v in c['targets'].items()}) for c in chosen])


@pytest.mark.parametrize('h',HORIZONS)
def test_exact_endpoints(h):
    r = request()
    assert utc(r.endpoint(h))-utc(r.origin_utc)==timedelta(days=h)
    assert r.endpoint(h).endswith('Z')


def test_population_counts_disjoint_and_repeatable(cases):
    from collections import Counter
    assert Counter(c['spec']['partition'] for c in cases)==dict(train=384,validation=128,calibration=128,test=192,ood=48)
    assert len({c['history_sha256'] for c in cases})==len(cases)
    assert len({c['parameters_sha256'] for c in cases})==len(cases)
    assert len({c['spec']['case_id'] for c in cases})==len(cases)
    assert {c['spec']['family'] for c in cases if c['spec']['partition']=='ood'}==set(OOD)
    assert not set(OOD)&set(FAMILIES)
    assert digest(cases)==digest(population())


@pytest.mark.parametrize('family',FAMILIES+OOD)
def test_mechanism_timestamp_missingness_and_stock(cases,family):
    c = next(c for c in cases if c['spec']['family']==family)
    r = Request.from_dict(c['request'])
    assert len(r.values)<=180
    assert all(utc(t)<=utc(r.origin_utc) for t in r.timestamps)
    assert all(v is None or v>=0 for v in r.values)
    assert all(c['targets'][h]['timestamp_utc']==r.endpoint(h) for h in HORIZONS)
    if family=='sparse':
        assert None in r.values and extract(r)['gap_censored']
    if family=='irregular':
        assert len(r.values)<180 and None not in r.values


def test_future_noise_does_not_enter_history():
    spec = next(s for s in specs() if s['family']=='stationary_noise')
    r,truth,_ = generate(spec)
    assert not any(k in r.as_dict() for k in ('targets','family','partition','changed','actual'))
    assert set(truth)==set(HORIZONS)


def test_future_cutoff_and_label_fields_rejected():
    r = request()
    with pytest.raises(ValueError):
        replace(r,timestamps=r.timestamps[:-1]+(r.endpoint(30),))
    for name in ('targets','changed','future_values','partition','p_change'):
        obj=r.as_dict();obj[name]=1
        with pytest.raises(ValueError):
            Request.from_dict(obj)


def test_missing_not_zero_or_unchanged():
    r = request((10.,None,10.,10.))
    f = extract(r)
    assert f['gap_censored'] and f['missing_records']==1
    assert f['observed_changes']==0 and f['plateau_lower_bound_days']==1
    assert f['days_since_observed_change'] is None
    assert f['metric_scale']==10
    assert f['vector'][NAMES.index('contiguous_transition_fraction')]==0
    z = extract(request((0.,0.,0.)))
    assert z['metric_scale']==0 and z['model_scale']==1
    assert z['vector'][NAMES.index('relative_variability')] is None
    with pytest.raises(ValueError):
        extract(request((1.,2.,None)))


@pytest.mark.parametrize('values',[(1.,math.nan),(1.,math.inf),(1.,-1.),(1.,True)])
def test_invalid_measurements(values):
    with pytest.raises(ValueError):
        request(values)


def test_analytic_features_and_baselines():
    r=request((1.,2.,3.,4.))
    f=extract(r)
    assert f['observed_changes']==3 and f['observed_transition_fraction']==1
    assert baseline(r,'persistence',30)==4
    assert baseline(r,'rolling_mean',30)==2.5
    assert baseline(r,'anchored_trend',30)==34
    assert len(f['vector'])==len(NAMES)


@pytest.mark.parametrize('current,delta,expected',[(10,-15,0),(0,20,20),(5,-3,2),(0,0,0)])
def test_signed_reconstruction(current,delta,expected):
    assert reconstruct(current,delta)==expected


@pytest.mark.parametrize('p',[-.1,1.1,math.nan,math.inf,True])
def test_invalid_probabilities(p):
    with pytest.raises(ValueError):
        probability(p)


def test_gating_blending_and_mixture():
    assert gate(10,5,.3,.75)==10
    assert gate(10,-20,.9,.75)==0
    assert blend(10,30,.25)==15
    assert mixture(.1,10,[-2,2])[1]==0
    assert mixture(.9,-10,[-2,2])[1]<0
    assert weighted_quantile([(-2,.2),(0,.6),(3,.2)],.5)==0
    with pytest.raises(ValueError):
        weighted_quantile([(1,.4)],.5)
    with pytest.raises(ValueError):
        mixture(.5,5,[])


def test_preprocessor_only_fit_statistics():
    a=[None]*len(NAMES);b=[2.]*len(NAMES)
    prep,x=transform_fit([a,b])
    before=digest(prep)
    z=transform(prep,[[1e6]*len(NAMES)])
    assert np.isfinite(x).all() and np.isfinite(z).all()
    assert digest(prep)==before and prep['fit_partition']=='train'
    assert len(prep['mean'])==2*len(NAMES)


def test_single_class_explicit():
    model=logistic(np.ones((3,2)),[1,1,1],1.)
    assert not model['eligible'] and model['kind']=='single_class' and model['probability']==1


@pytest.mark.parametrize('partition',['test','validation','calibration','ood'])
def test_fit_partition_protection(cases,partition):
    c=cases[0]
    with pytest.raises(ValueError):
        fit([dict(partition=partition,request=c['request'],targets=c['targets'])])


@pytest.mark.parametrize('method',METHODS[:-1])
@pytest.mark.parametrize('h',HORIZONS)
def test_models_finite_deterministic_and_past_only(state,method,h):
    req=request((20.,20.,20.,10.))
    config=configs(method)[0]
    a=predict(req,state,config,h)
    b=predict(req,state,config,h)
    assert a==b and a['status']==STATUS and a['point']>=0
    assert a['raw_signed_delta']==a['raw_stock']-10
    if a['p_change'] is not None:
        assert 0<=a['p_change']<=1
    if a['mixture_quantiles'] is not None:
        q=a['mixture_quantiles'];assert q[0]<=q[1]<=q[2]


def test_model_selection_and_calibration_partition_protection(state):
    with pytest.raises(ValueError):
        select(state,{}, {}, {}, partition='test')
    with pytest.raises(ValueError):
        calibrate(state,{}, {}, {}, partition='test')


def test_forecast_metrics_zero_denominator_and_scales():
    rows=[dict(case_id=str(i),family='a',prediction=p,actual=a,current=0.,metric_scale=scale)
          for i,(p,a,scale) in enumerate([(0.,2.,0.),(1.,2.,2.)])]
    m=forecast_metrics(rows)
    assert m['mae']==1.5 and m['zero_denominators']==1 and m['normalized_mae']==.5
    assert m['normalized_persistence_skill']==.5
    assert forecast_metrics([])['mae'] is None


def test_classification_perfect_and_single_class():
    rows=[dict(current=1,actual=a,probability=p) for a,p in [(1,.1),(2,.9)]]
    m=classification_metrics(rows,.75)
    assert m['precision']==m['recall']==m['f1']==m['roc_auc']==m['pr_auc_average_precision']==1
    assert m['brier_score']==pytest.approx(.01)
    m=classification_metrics([rows[0]],.5)
    assert m['roc_auc'] is None and m['pr_auc_average_precision'] is None and m['recall'] is None
    tied=classification_metrics([dict(rows[0],probability=.5),dict(rows[1],probability=.5)],.5)
    assert tied['roc_auc']==tied['pr_auc_average_precision']==.5


def test_intervals_never_sort():
    rows=[dict(actual=1,q=[0.,1.,2.])]
    m=interval_metrics(rows,'q')
    assert m['coverage80']==1 and m['width80']==2 and m['pinball50']==0
    with pytest.raises(ValueError):
        interval_metrics([dict(actual=1,q=[2.,1.,0.])],'q')


def test_paired_family_bootstrap_and_mismatch():
    rows=[]
    for method, prediction in [('persistence',0),('model',1)]:
        for i in range(4):
            rows.append(dict(method=method,prediction=prediction,actual=2,current=0,
                             metric_scale=2,family=str(i//2),case_id=str(i),request_id=str(i),horizon=30,partition='test'))
    m=paired(rows,'persistence','model',30,'test')
    assert m['equal_family_difference']==-1 and m['family_bootstrap_ci95']==[-1,-1]
    assert m==paired(rows,'persistence','model',30,'test')
    with pytest.raises(ValueError):
        paired(rows[:-1],'persistence','model',30,'test')


def test_resource_limit_reasons():
    assert limit_failure(0,0,0,0) is None
    for args,reason in [((901,0,0,0),'TIMEOUT'),((0,2*1024**3+1,0,0),'RSS_LIMIT'),
                        ((0,0,8*1024**2+1,0),'LOG_LIMIT'),((0,0,0,64*1024**2+1),'OUTPUT_LIMIT')]:
        assert limit_failure(*args)==reason


def test_paths_registration_and_label_seals(tmp_path,monkeypatch):
    from forecasting_research.phase6_2 import study
    monkeypatch.setattr(study,'ROOT',tmp_path)
    root=tmp_path/'study'
    prepare(root)
    assert verify(root)['total']==880
    events=[];labels=Labels(root,events)
    with pytest.raises(ValueError):
        labels.read('validation','fit')
    with pytest.raises(FileNotFoundError):
        labels.read('test','score')
    assert labels.read('train','fit')
    for name in ('models.json','selection.json','calibration.json','predictions.json'):
        write(root/name,{'fixture':True})
    prediction_seal(root)
    assert labels.read('test','score')
    assert events[-1]['prediction_seal_verified']
    (root/'predictions.json').write_text('{}')
    with pytest.raises(ValueError):
        verify_prediction_seal(root)
    with pytest.raises(ValueError):
        labels.read('ood','score')
    (tmp_path/'alias').symlink_to(root,target_is_directory=True)
    with pytest.raises(ValueError):
        safe(tmp_path/'alias/new',fresh=True)
    with pytest.raises(ValueError):
        safe(tmp_path/'../outside')
    with pytest.raises(FileExistsError):
        prepare(root)


def test_policy_preserves_unknowns_and_prohibited_modules():
    assert POLICY['pretrained']['chronos']=='NOT_EXECUTED_NO_SEPARATE_APPROVAL'
    root=Path(__file__).parents[1]/'forecasting_research/phase6_2'
    for path in root.glob('*.py'):
        tree=ast.parse(path.read_text())
        modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        modules += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
        assert not any(m and m.startswith(('torch','transformers','chronos','timesfm','sklearn','sqlite3')) for m in modules)
    predictor=ast.parse((root/'models.py').read_text())
    fn=next(n for n in predictor.body if isinstance(n,ast.FunctionDef) and n.name=='predict')
    assert [a.arg for a in fn.args.args]==['request','state','config','horizon']
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='open' for n in ast.walk(fn))


def test_worker_finally_resource_capture_exists():
    from forecasting_research.phase6_2 import worker
    tree=ast.parse(Path(worker.__file__).read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    trap=next(n for n in fn.body if isinstance(n,ast.Try))
    assert trap.finalbody
    assert 'worker_resources.json' in ast.get_source_segment(Path(worker.__file__).read_text(),trap)


def test_worker_exception_retains_resources(tmp_path,monkeypatch):
    from forecasting_research.phase6_2 import worker
    monkeypatch.setattr(worker,'safe',lambda p: tmp_path)
    def fail(root):
        raise ValueError('DELIBERATE_UNIT_TEST_FAILURE')
    monkeypatch.setattr(worker,'execute',fail)
    # main installs a process-local network guard: restore sockets after this unit test.
    import socket
    connect,create=socket.socket.connect,socket.create_connection
    try:
        with pytest.raises(ValueError,match='DELIBERATE_UNIT_TEST_FAILURE'):
            worker.main(tmp_path)
    finally:
        socket.socket.connect=connect
        socket.create_connection=create
    receipt=json.loads((tmp_path/'worker_resources.json').read_text())
    assert receipt['status']=='FAIL' and receipt['peak_rss_bytes']>0
    assert receipt['failure']==dict(type='ValueError',message='DELIBERATE_UNIT_TEST_FAILURE')
    assert not (tmp_path/'outcome.json').exists()


def test_bad_training_timestamp_and_unknown_config(cases,state):
    c=cases[0]
    targets={str(h):dict(v) for h,v in c['targets'].items()}
    targets['30']['timestamp_utc']=targets['60']['timestamp_utc']
    with pytest.raises(ValueError,match='endpoint identity'):
        fit([dict(partition='train',request=c['request'],targets=targets)])
    for config in (None,dict(method='hard_gate',alpha=1.,threshold=.333),dict(method='fake')):
        with pytest.raises(ValueError):
            predict(request(),state,config,30)


def test_training_repeatability(cases):
    chosen=[c for c in cases if c['spec']['partition']=='train' and c['spec']['index']==0]
    rows=[dict(partition='train',request=c['request'],targets={str(h):v for h,v in c['targets'].items()}) for c in chosen]
    assert digest(fit(rows))==digest(fit(rows))


def test_unobserved_gap_transition_is_censored():
    f=extract(request((1.,None,3.)))
    assert f['observed_changes']==1 and f['gap_censored']
    assert f['plateau_lower_bound_days']==0
    assert f['vector'][NAMES.index('contiguous_transition_fraction')] is None
    f=extract(request((None,None,3.,3.)))
    assert f['vector'][NAMES.index('missing_fraction')]==.5


def test_existing_numpy_runtime_integrity():
    from forecasting_research.phase6_2.runtime import identity
    a=identity();b=identity()
    assert a==b and a['numpy_version']=='2.4.4'
    assert a['recorded_files']>900
    assert a['canonical_files_sha256']==digest(a['files'])
