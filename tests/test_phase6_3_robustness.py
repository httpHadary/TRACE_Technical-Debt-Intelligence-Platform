"""Mechanical/toy fits only before preregistration; no registered-population fitting."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
import ast
import json
import math
import numpy as np
import pytest
from forecasting_research.phase6_0.contracts import Request,digest,iso,utc
from forecasting_research.phase6_0.artifacts import write,sha
from forecasting_research.phase6_3 import STATUS,VERSION,HORIZONS
from forecasting_research.phase6_3.population import specs,population,generate,trajectory,FAMILIES,OOD,pulse
from forecasting_research.phase6_3.models import METHODS,features,fit,predict,configs,direction_probabilities,weighted_logistic
from forecasting_research.phase6_3.selection import risk,choose,select
from forecasting_research.phase6_3.calibration import build,apply,choose as choose_interval
from forecasting_research.phase6_3.evaluation import direction_metrics
from forecasting_research.phase6_3.study import POLICY,LIMITS,prepare,verify,Labels,prediction_seal,verify_prediction_seal,safe
from forecasting_research.phase6_3.run import limit_failure


def request(values=(10.,10.,10.)):
    origin=datetime(2051,1,1,tzinfo=timezone.utc)
    return Request('synthetic-mechanical-test',iso(origin),
                   tuple(iso(origin-timedelta(days=len(values)-1-i)) for i in range(len(values))),
                   tuple(values),tuple(None if v is not None else 'SYNTHETIC_UNOBSERVED' for v in values))


@pytest.fixture(scope='module')
def cases(): return population()


@pytest.fixture(scope='module')
def transfer_fixture():
    root=Path(__file__).parents[1]/'examples/phase6_2'
    model=json.loads((root/'models.json').read_text());selection=json.loads((root/'selection.json').read_text())
    calibration=json.loads((root/'calibration.json').read_text());calibration.pop('scope');calibration.pop('source_sha256')
    return dict(model=model,selection=selection,calibration=calibration,refitted=False)


@pytest.fixture(scope='module')
def toy_rows():
    rows=[]
    for i in range(36):
        mode=i%3;base=100.+i
        vals=[base if mode==0 else base+.3*k if mode==1 else base+80-.3*k for k in range(180)]
        req=replace(request(tuple(vals)),case_id='synthetic-toy-unit-'+str(i))
        direction=(0,1,-1)[mode]
        targets={str(h):dict(timestamp_utc=req.endpoint(h),value=max(0.,vals[-1]+direction*.25*h)) for h in HORIZONS}
        rows.append(dict(partition='train',request=req.as_dict(),targets=targets))
    return rows


@pytest.fixture(scope='module')
def state(toy_rows,transfer_fixture):
    before=digest(transfer_fixture);model=fit(toy_rows,transfer_fixture)
    assert digest(transfer_fixture)==before
    return model


def test_preregistered_primary_and_resource_caps():
    assert POLICY['primary_candidate']=='adaptive_persistence'
    assert POLICY['root_seed']==63020261020
    assert POLICY['point_safety']['large_decrease_relative_deterioration_max']==.05
    assert LIMITS['rss_bytes']==2*1024**3 and LIMITS['wall_seconds']==900 and LIMITS['numerical_threads']==2
    assert configs('adaptive_persistence')[0]['shrink']==0
    assert len(configs('adaptive_persistence'))==33
    assert sum(len(configs(m)) for m in METHODS[:-1])==73


def test_population_identity_and_isolation(cases):
    from collections import Counter
    assert Counter(c['spec']['partition'] for c in cases)==dict(train=384,validation=192,calibration=192,test=256,ood=160)
    for field in ('history_sha256','parameters_sha256'):
        assert len({c[field] for c in cases})==len(cases)
    assert not set(FAMILIES)&set(OOD) and len(OOD)==8
    assert digest(cases)==digest(population())


@pytest.mark.parametrize('family',FAMILIES+OOD)
def test_each_mechanism_contract(cases,family):
    c=next(c for c in cases if c['spec']['family']==family)
    r=Request.from_dict(c['request'])
    assert r.values[-1] is not None and len(r.values)<=180
    assert all(utc(t)<=utc(r.origin_utc) for t in r.timestamps)
    assert all(v is None or v>=0 for v in r.values)
    assert all(c['targets'][str(h)]['timestamp_utc']==r.endpoint(h) for h in HORIZONS)


@pytest.mark.parametrize('h',HORIZONS)
@pytest.mark.parametrize('family',OOD)
def test_ood_has_both_classes_and_directions(cases,family,h):
    signs=[]
    for c in cases:
        if c['spec']['partition']=='ood' and c['spec']['family']==family:
            d=c['targets'][str(h)]['value']-c['request']['values'][-1]
            signs.append(0 if d==0 else 1 if d>0 else -1)
    assert signs.count(0)==10 and signs.count(1)==5 and signs.count(-1)==5


def test_returns_and_future_timing_not_features():
    spec=next(s for s in specs() if s['family']=='return_origin')
    past,future,_=trajectory(spec)
    assert all(future[h-1]==past[-1] for h in HORIZONS)
    assert any(v!=past[-1] for v in future) and pulse(30)==0
    c=generate(spec);r=Request.from_dict(c['request'])
    assert not any(k in r.as_dict() for k in ('family','partition','targets','direction','event_day'))
    for key in ('family','future','direction','actual','partition'):
        obj=r.as_dict();obj[key]=1
        with pytest.raises(ValueError): Request.from_dict(obj)


def test_missingness_zero_and_immutable_features():
    f=features(request((1.,None,1.,1.)))
    assert f['gap_censored'] and f['plateau_lower_bound_days']==1
    assert f['missing_records']==1
    with pytest.raises(TypeError): f['current']=0
    with pytest.raises(TypeError): f['vector'][0]=0
    z=features(request((0.,0.,0.)))
    assert z['metric_scale']==0 and z['model_scale']==1
    with pytest.raises(ValueError): features(request((1.,None)))


@pytest.mark.parametrize('bad',[math.nan,math.inf,-1.,True])
def test_invalid_stock(bad):
    with pytest.raises(ValueError): request((1.,bad))


@pytest.mark.parametrize('h',HORIZONS)
def test_future_cutoff(h):
    r=request()
    assert (utc(r.endpoint(h))-utc(r.origin_utc)).days==h
    with pytest.raises(ValueError): replace(r,timestamps=r.timestamps[:-1]+(r.endpoint(h),))


@pytest.mark.parametrize('method',METHODS[:-1])
@pytest.mark.parametrize('h',HORIZONS)
def test_all_methods_pure_repeatable_and_anchored(state,method,h):
    r=request();config=configs(method)[0]
    before=digest(state)
    a=predict(r,state,config,h);b=predict(r,state,config,h)
    assert a==b and digest(state)==before
    assert a['point']==max(0.,a['raw_stock'])
    assert a['raw_signed_delta']==a['raw_stock']-r.values[-1]
    assert a['status']==STATUS and a['timestamp_utc']==r.endpoint(h)
    if method=='adaptive_persistence': assert a['point']==r.values[-1]
    if method=='frozen_phase6_2': assert a['is_frozen_transfer']
    if a['direction_probabilities'] is not None:
        assert sum(a['direction_probabilities'])==pytest.approx(1)


def test_direction_negative_and_stock_clipping(state):
    state=json.loads(json.dumps(state));head=state['direction_heads']['30']['1.0/none']
    head['ovr']=[dict(kind='single_class',probability=p) for p in (0.,0.,1.)]
    head['decrease']=[-10.]+[0.]*48;head['increase']=[10.]+[0.]*48
    conf=dict(method='adaptive_persistence',alpha=1.,balance='none',threshold=.75,minimum=.02,shrink=.5)
    p=predict(request((1.,1.,1.)),state,conf,30)
    assert p['raw_downward_component']==-10 and p['raw_signed_delta']<0 and p['raw_stock']<0 and p['point']==0
    assert p['intentional_shrinkage']<.5  # Observed-gap reliability is past-only.


def test_invalid_probabilities_and_class_weight():
    with pytest.raises(ValueError): direction_probabilities(dict(ovr=[dict(kind='single_class',probability=0)]*3),np.ones((1,2)))
    with pytest.raises(ValueError): direction_probabilities(dict(ovr=[dict(kind='single_class',probability=-1)]*3),np.ones((1,2)))
    with pytest.raises(ValueError): weighted_logistic(np.ones((2,2)),[0,1],[-1,1],1.)
    assert weighted_logistic(np.ones((2,2)),[0,0],[1,1],1.)['eligible'] is False


def test_invalid_gate_config_and_input_identity(state):
    config=dict(configs('adaptive_persistence')[0],shrink=False)
    with pytest.raises(ValueError): predict(request(),state,config,30)
    with pytest.raises(ValueError): predict(request(),state,dict(method='adaptive_persistence',alpha=1.,threshold=.123),30)
    with pytest.raises(ValueError): predict(request(),dict(state,version='wrong'),configs('persistence')[0],30)


@pytest.mark.parametrize('part',['validation','calibration','test','ood'])
def test_training_role_protection(part,toy_rows,transfer_fixture):
    row=dict(toy_rows[0],partition=part)
    with pytest.raises(ValueError): fit([row],transfer_fixture)


def test_new_fit_and_frozen_transfer_are_distinct(state,transfer_fixture,toy_rows):
    assert not state['transfer_refitted']
    assert state['binary_new_fit']['train_requests_sha256']!=transfer_fixture['model']['train_requests_sha256']
    assert state['binary_new_fit']['preprocessor']['fit_partition']=='train'
    assert digest(fit(toy_rows,transfer_fixture))==digest(state)


def test_selection_safety_and_parsimony():
    rows=[dict(current=100.,actual=100. if i<8 else 20.,prediction=100.,model_scale=100.,family=str(i%4)) for i in range(16)]
    assert risk(rows)['safety_eligible']
    unsafe=[dict(r,prediction=90.) for r in rows]
    assert not risk(unsafe)['safety_eligible']
    choices=[dict(config='simple',risk=dict(safety_eligible=True,normalized_family_error=.1005)),
             dict(config='complex',risk=dict(safety_eligible=True,normalized_family_error=.1))]
    assert choose(choices)['config']=='simple'
    with pytest.raises(ValueError): select({}, {}, {}, {}, partition='test')


def calibration_rows():
    return [dict(family=str(i%4),actual=10.+(i%5-2),prediction=10.,current=10.,model_scale=10.) for i in range(40)]


@pytest.mark.parametrize('kind',['shared_symmetric','signed_global','direction_stratified'])
def test_calibration_partition_bins_order_and_bounded_widening(kind):
    rows=calibration_rows();state=build(rows,kind,'calibration')
    q=apply(10.,10.,10.,state,1.25)
    assert q['quantiles'][0]<=q['quantiles'][1]<=q['quantiles'][2]
    assert state['bins']['increase']['fallback_to_global']
    with pytest.raises(ValueError): build(rows,kind,'test')
    with pytest.raises(ValueError): apply(10,10,10,state,2.)
    if kind!='direction_stratified':
        state['global_quantiles']=[1.,0.,-1.]
        with pytest.raises(ValueError): apply(10,10,10,state)


def test_interval_selection_and_direction_diagnostics():
    rows=calibration_rows()
    chosen=choose_interval(rows,rows)
    assert chosen['selection_partition']=='validation'
    with pytest.raises(ValueError): choose_interval(rows,rows,partition='ood')
    rows=[dict(current=10.,actual=a,direction_probabilities=p) for a,p in [(10.,[1.,0.,0.]),(20.,[0.,1.,0.]),(0.,[0.,0.,1.])]]
    m=direction_metrics(rows)
    assert m['macro_f1']==1 and m['multiclass_brier']==0


def test_registration_labels_seals_and_symlinks(tmp_path,monkeypatch,transfer_fixture):
    from forecasting_research.phase6_3 import study
    root=tmp_path/'studies';old=tmp_path/'prior';root.mkdir();old.mkdir()
    write(old/'population.json',[])
    write(old/'registration.json',dict(inputs={'population.json':sha(old/'population.json')}))
    monkeypatch.setattr(study,'ROOT',root);monkeypatch.setattr(study,'OLD',old)
    monkeypatch.setattr(study,'transfer',lambda:transfer_fixture)
    out=root/'one';prepare(out);assert verify(out)['total']==1184
    events=[];labels=Labels(out,events)
    with pytest.raises(ValueError): labels.read('validation','fit')
    with pytest.raises(FileNotFoundError): labels.read('test','score')
    assert labels.read('train','fit')
    for name in ('models.json','selection.json','calibration.json','predictions.json'): write(out/name,{'fixture':True})
    prediction_seal(out);assert labels.read('test','score') and labels.read('diagnostics','score')
    (out/'predictions.json').write_text('{}')
    with pytest.raises(ValueError): verify_prediction_seal(out)
    with pytest.raises(ValueError): labels.read('ood','score')
    (root/'alias').symlink_to(out,target_is_directory=True)
    with pytest.raises(ValueError): safe(root/'alias/new',fresh=True)
    with pytest.raises(ValueError): safe(root/'../outside',fresh=True)
    with pytest.raises(FileExistsError): prepare(out)


def test_resource_failures_and_finally_receipt(tmp_path,monkeypatch):
    assert limit_failure(901,0,0,0)=='TIMEOUT'
    assert limit_failure(0,2*1024**3+1,0,0)=='RSS_LIMIT'
    assert limit_failure(0,0,8*1024**2+1,0)=='LOG_LIMIT'
    assert limit_failure(0,0,0,64*1024**2+1)=='OUTPUT_LIMIT'
    from forecasting_research.phase6_3 import worker
    monkeypatch.setattr(worker,'safe',lambda p:tmp_path)
    def fail(path): raise ValueError('DELIBERATE_UNIT_FAILURE')
    monkeypatch.setattr(worker,'execute',fail)
    import socket
    connect,create=socket.socket.connect,socket.create_connection
    try:
        with pytest.raises(ValueError): worker.main(tmp_path)
    finally: socket.socket.connect=connect;socket.create_connection=create
    receipt=json.loads((tmp_path/'worker_resources.json').read_text())
    assert receipt['failure']['message']=='DELIBERATE_UNIT_FAILURE' and receipt['peak_rss_bytes']>0


def test_pure_predict_interface_and_no_native_model_imports():
    root=Path(__file__).parents[1]/'forecasting_research/phase6_3'
    for file in root.glob('*.py'):
        tree=ast.parse(file.read_text())
        modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        modules += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
        assert not any(m and m.startswith(('torch','chronos','timesfm','transformers','sqlite3')) for m in modules)
    tree=ast.parse((root/'models.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='predict')
    assert [a.arg for a in fn.args.args]==['request','state','config','horizon']
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='open' for n in ast.walk(fn))
