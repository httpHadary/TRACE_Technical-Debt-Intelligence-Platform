import copy
import json
import math
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
import pytest
from forecasting_research.phase6_0.contracts import Request, iso, utc, digest
from forecasting_research.phase6_5 import contracts as c, population as pop, model as m, experiment as e, evaluation as ev
from forecasting_research.phase6_5.runner import limit_failure


def row(i=0,role='train',family='growth'):return pop.generate(11,role,family,i)
def req(i=1):return c.InformationRequest.from_dict(row(i)['request'])

@pytest.fixture(scope='module')
def state():return m.fit([row(i,'train',f) for f in pop.FAMILIES for i in range(32)])

@pytest.mark.parametrize('h',[30,60,90])
def test_origin_and_exact_endpoints(h,state):
    r=req();p=m.Predictor(state).predict(r,h,'intent_median')
    assert p['timestamp_utc']==iso(utc(r.debt.origin_utc)+timedelta(days=h))
    assert p==m.Predictor(state).predict(r,h,'intent_median')

@pytest.mark.parametrize('bad',[True,0,29,31,91,'30'])
def test_bad_horizon(bad,state):
    with pytest.raises(ValueError):m.Predictor(state).predict(req(),bad,'persistence')

@pytest.mark.parametrize('key',['future_direction','future_debt','partition','family','future_changepoint'])
def test_request_future_fields_rejected(key):
    r=req().as_dict();r[key]=1
    with pytest.raises(ValueError):c.InformationRequest.from_dict(r)

@pytest.mark.parametrize('key',['actual','outcome','actual_future_churn'])
def test_signal_extra_fields_rejected(key):
    s=req().signals[0].as_dict();s[key]=1
    with pytest.raises(ValueError):c.Signal.from_dict(s)

def test_two_clocks_event_old_but_late_availability():
    r=req();late=pop.delayed(r)
    assert late.signals[0].event_utc<r.debt.origin_utc
    assert late.signal('declared_intent',30)==(None,'NOT_AVAILABLE_AT_ORIGIN')

@pytest.mark.parametrize('method',['activity_median','intent_median','adaptive_local','adaptive_stress'])
def test_delayed_signal_does_not_discard_case_or_invent_value(state,method):
    r=pop.delayed(req());p=m.Predictor(state).predict(r,90,method,1.)
    assert p['point']==r.debt.values[-1] and p['reason']=='NOT_AVAILABLE_AT_ORIGIN'

def test_missing_window_is_not_zero():
    r=req();s=next(v for v in r.signals if v.name=='observed_activity')
    with pytest.raises(ValueError):replace(s,complete=False,value=0)
    missing=replace(s,complete=False,value=None)
    assert missing.usable(r.debt.origin_utc)==(False,'INCOMPLETE_WINDOW')

@pytest.mark.parametrize('change',[dict(status='ADMITTED_MEASUREMENT'),dict(purpose='REAL_TRAINING'),dict(unit='minutes'),dict(value=True),dict(value=2),dict(provenance_sha256='bad')])
def test_bad_or_unapproved_signal(change):
    s=next(v for v in req().signals if v.name=='declared_intent')
    with pytest.raises(ValueError):replace(s,**change)

def test_temporal_order_rejected():
    s=req().signals[0]
    with pytest.raises(ValueError):replace(s,event_utc='2050-01-01T00:00:00Z')

def test_duplicate_signal_rejected():
    r=req()
    with pytest.raises(ValueError):replace(r,signals=r.signals+(r.signals[0],))

def test_future_debt_observation_rejected():
    r=req().debt.as_dict();r['timestamps'][-1]=iso(utc(r['origin_utc'])+timedelta(days=1))
    with pytest.raises(ValueError):Request.from_dict(r)

@pytest.mark.parametrize('role',['validation','calibration','test','unseen'])
def test_no_fitting_other_roles(role):
    family=pop.UNSEEN[0] if role=='unseen' else 'growth'
    with pytest.raises(ValueError):m.fit([row(1,role,family)])

def test_no_preprocessing_test_labels(state):
    before=digest(state);p=m.Predictor(state);p.predict(req(70),90,'intent_median')
    assert before==digest(state)

def test_signed_delta_and_zero_clipping(state):
    s=copy.deepcopy(state)
    s['cells']['intent:90']={str(i):[-2.]*40 for i in (-1,0,1)}
    p=m.Predictor(s).predict(req(),90,'intent_median')
    assert p['raw_delta']<0 and p['raw_stock']<0 and p['point']==0

def test_absent_is_protected(state):
    r=replace(req(),signals=());p=m.Predictor(state).predict(r,30,'adaptive_local',1.)
    assert p['point']==r.debt.values[-1] and p['reason']=='ABSENT_SIGNAL'

def test_sparse_and_irregular_preserve_actual_observations():
    r=c.InformationRequest.from_dict(row(1,'train','sparse')['request'])
    assert None in r.debt.values
    z=c.InformationRequest.from_dict(row(1,'unseen','irregular_history')['request'])
    assert len(z.debt.values)<96

@pytest.mark.parametrize('q,expect',[(.1,-1),(.5,0),(.9,2)])
def test_empirical_zero_mass(q,expect):assert m.quantile([-1,0,0,0,2],q)==expect

@pytest.mark.parametrize('xs,q',[([], .5),([math.nan],.5),([1],0),([1],1.1)])
def test_bad_distribution(xs,q):
    with pytest.raises(ValueError):m.quantile(xs,q)

def validation_rows(a):
    rs=[]
    for i in range(90):
        actual=[90.,100.,110.][i%3]
        rs.append(dict(role='validation',family=str(i%6),actual=actual,current=100.,scale=100.,point=100.+a*(actual-100.)))
    return rs

def test_validation_only_selection():
    with pytest.raises(ValueError):m.risk([dict(role='test')])

def test_fixed_selection_protects_and_strict_gain():
    rs={a:validation_rows(0) for a in m.SHRINKS}
    assert m.select(rs)['shrink']==0
    rs={a:validation_rows(a) for a in m.SHRINKS}
    assert m.select(rs)['shrink']==1

def test_robust_selection_respects_reversal():
    rs={a:validation_rows(a) for a in m.SHRINKS}
    stress={a:[dict(r,actual=200-r['actual']) for r in rows] for a,rows in rs.items()}
    assert m.select(rs,[stress])['shrink']==0

def test_no_training_support_no_adjustment(state):
    s=copy.deepcopy(state);s['cells']['intent:30']={}
    assert m.Predictor(s).predict(req(),30,'intent_median')['reason']=='INSUFFICIENT_TRAIN_SUPPORT'

def test_zero_denominator_counted_not_epsilon():
    r=dict(case_id='a',actual=1.,point=0.,current=0.,scale=1.,family='a')
    z=ev.aggregate([r]);assert z['zero_denominators']==1 and z['unfloored_normalized_mae'] is None

def test_invalid_interval_rejected():
    with pytest.raises(ValueError):ev.interval_metrics([dict(lo=2.,hi=1.,actual=1.)])

def test_metric_identity():
    r=dict(case_id='a',actual=4.,point=3.,current=2.,scale=2.,family='a')
    z=ev.aggregate([r]);assert z['mae']==1 and z['raw_skill']==.5 and z['normalized_skill']==.5

def test_balanced_identical_information_bound():
    for current in (1.,10.,100.):
        outcomes=[current*.6,current,current*1.4]
        base=sum(abs(current-y) for y in outcomes)
        for x in (0.,current*.2,current*.6,current,current*1.2,current*2):
            assert sum(abs(x-y) for y in outcomes)>=base-1e-12

def test_paired_worlds_cannot_change_forecast(state):
    r=row(7,'test');request=c.InformationRequest.from_dict(r['request'])
    assert r['targets']!=r['reversed_targets']
    p=m.Predictor(state)
    predictions=[p.predict(request,90,'adaptive_local',1.) for _ in ('targets','hidden_targets','reversed_targets')]
    assert predictions[0]==predictions[1]==predictions[2]

@pytest.mark.parametrize('p',['/tmp/a','/home/hp/tst/research/forecasting_mvp/phase6_4/x','/home/hp/tst/research/forecasting_mvp/phase6_5/../other'])
def test_output_path_rejected(p):
    with pytest.raises(ValueError):e.safe(p)

def test_symlink_boundary(tmp_path,monkeypatch):
    monkeypatch.setattr(e,'ROOT',tmp_path);(tmp_path/'link').symlink_to('/tmp',target_is_directory=True)
    with pytest.raises(ValueError):e.safe(tmp_path/'link'/'x')

def test_exclusive_artifact_write(tmp_path):
    p=tmp_path/'a';e.write(p,{'one':1})
    with pytest.raises(FileExistsError):e.write(p,{'one':2})

def test_labels_require_complete_seal(tmp_path):
    with pytest.raises(FileNotFoundError):e.open_labels(tmp_path,11,'test')
    e.write(tmp_path/'11.prediction_seal.json',dict(files={},registration_sha256='bad'))
    with pytest.raises(ValueError):e.open_labels(tmp_path,11,'test')

@pytest.mark.parametrize('args,reason',[((901,0,0,0),'TIMEOUT'),((0,2*1024**3+1,0,0),'RSS_LIMIT'),((0,0,9*1024**2,0),'LOG_LIMIT'),((0,0,0,129*1024**2),'OUTPUT_LIMIT')])
def test_failure_limits(args,reason):assert limit_failure(*args)==reason

def test_full_toy_prepare_manifest_and_claim(tmp_path,monkeypatch):
    monkeypatch.setattr(e,'ROOT',tmp_path);monkeypatch.setattr(e,'REPLICAS',(11,))
    monkeypatch.setattr(pop,'COUNTS',{k:4 for k in pop.ROLES})
    p=tmp_path/'new';registration=e.prepare(p)
    assert e.verify(p)==registration
    assert (p/'11.validation_hidden.targets.json').exists()
    with pytest.raises(FileExistsError):e.prepare(p)
    (p/'11.test.requests.json').write_text('[]')
    with pytest.raises(ValueError):e.verify(p)

def test_no_new_runtime_or_acquisition():
    folder=Path(e.__file__).parent
    for p in folder.glob('*.py'):
        source=p.read_text()
        for forbidden in ('import torch','import numpy','from_pretrained','pip install','import requests','urlopen('):assert forbidden not in source


def test_toy_end_to_end_prediction_seal_before_labels(tmp_path,monkeypatch):
    monkeypatch.setattr(e,'ROOT',tmp_path);monkeypatch.setattr(e,'REPLICAS',(11,))
    monkeypatch.setattr(pop,'COUNTS',{k:4 for k in pop.ROLES})
    p=tmp_path/'study';e.prepare(p);result=e.execute(p)
    assert result['status']=='COMPLETED' and result['predictions']==(24*4+16)*3*len(m.METHODS)
    events=e.read(p/'events.json');seal=next(v['sequence'] for v in events if v['event']=='FINAL_PREDICTIONS_SEALED')
    assert all(v['sequence']>seal for v in events if v['event']=='FINAL_LABELS_OPENED')
    for role in e.FINAL:assert e.open_labels(p,11,role)
    (p/'11.test.predictions.json').write_text('[]')
    with pytest.raises(ValueError):e.open_labels(p,11,'test')


@pytest.mark.parametrize('bad',[True,False,float('nan'),-1,2,'0.5'])
def test_invalid_shrink(state,bad):
    with pytest.raises(ValueError):m.Predictor(state).predict(req(),90,'adaptive_local',bad)


@pytest.fixture
def toy_study(tmp_path,monkeypatch):
    monkeypatch.setattr(e,'ROOT',tmp_path);monkeypatch.setattr(e,'REPLICAS',(11,))
    monkeypatch.setattr(pop,'COUNTS',{k:4 for k in pop.ROLES})
    p=tmp_path/'audit';e.prepare(p);e.execute(p);return p

def test_independent_audit_checks_every_prediction(toy_study):
    from tools.verify_phase6_5 import audit
    r=audit(toy_study);assert r['status']=='PASS' and r['predictions_verified']==2688

def test_independent_audit_rejects_prediction_tamper(toy_study):
    from tools.verify_phase6_5 import audit
    (toy_study/'11.test.predictions.json').write_text('[]')
    with pytest.raises(ValueError):audit(toy_study)

def test_independent_audit_rejects_metric_tamper(toy_study):
    from tools.verify_phase6_5 import audit
    p=toy_study/'metrics.json';a=e.read(p);a[0]['strata']['all']['mae']+=1;p.write_text(json.dumps(a))
    with pytest.raises(ValueError):audit(toy_study)

def test_admitted_intent_is_not_outcome_identity(state):
    r=req();s=copy.deepcopy(state)
    s['cells']['intent:90']={str(i):[i*.2]*40 for i in (-1,0,1)}
    signals=tuple(replace(v,value=-1) if v.name=='declared_intent' else v for v in r.signals)
    low=replace(r,signals=signals)
    high=replace(r,signals=tuple(replace(v,value=1) if v.name=='declared_intent' else v for v in r.signals))
    p=m.Predictor(s)
    assert p.predict(low,90,'intent_median')['raw_delta']<0<p.predict(high,90,'intent_median')['raw_delta']
