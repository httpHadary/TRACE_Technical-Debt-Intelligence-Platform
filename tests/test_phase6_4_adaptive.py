import copy
import json
from datetime import timedelta
from pathlib import Path
import numpy as np
import pytest
from forecasting_research.phase6_0.contracts import Request,iso,utc
from forecasting_research.phase6_4 import model,population,selection,study,evaluation
from forecasting_research.phase6_4.run import limit_failure


@pytest.fixture(scope='module',autouse=True)
def independent_fixture_streams():
    # Test fits/labels never consume the registered scientific population.
    with pytest.MonkeyPatch.context() as m:
        m.setattr(population,'REPLICAS',(11,12))
        yield


@pytest.fixture(scope='module')
def trained():
    rows=[population.generate(population.REPLICAS[0],'train',f,i) for f in population.FAMILIES for i in range(12)]
    return model.fit(rows)


def req(family='growth',index=19):
    return Request.from_dict(population.generate(population.REPLICAS[0],'train',family,index)['request'])


def scores(safe=False):
    return [dict(config=c,risk=dict(safe=safe,score=.1 if i else 1.,base=1.,adequate=safe)) for i,c in enumerate(model.CONFIGS)]


def test_no_safe_always_returns_protected():
    r=selection.choose(scores(False))
    assert r['config']['shrink']==0 and not r['admitted_adjustment']


def test_safe_requires_meaningful_improvement():
    s=scores(True)
    for r in s:r['risk']['score']=.99
    assert selection.choose(s)['config']['shrink']==0


def test_safe_eligible_selected_deterministically():
    s=scores(True);s[1]['risk']['safe']=False
    assert selection.choose(s)['config']==s[2]['config']


def test_incomplete_selection_rejected():
    with pytest.raises(ValueError):selection.choose(scores()[:-1])


@pytest.mark.parametrize('partition',['validation','calibration','test','ood','identifiability'])
def test_no_nontraining_fit(partition):
    r=population.generate(population.REPLICAS[0],'train','growth',0);r['metadata']['partition']=partition
    with pytest.raises(ValueError):model.fit([r])


@pytest.mark.parametrize('h',[30,60,90])
def test_endpoint_and_repeatability(trained,h):
    p=model.Predictor(trained);r=req()
    a=p.predict(r,h);assert a==p.predict(r,h)
    assert a['timestamp_utc']==iso(utc(r.origin_utc)+timedelta(days=h))
    assert a['point']==r.values[-1]


@pytest.mark.parametrize('h',[True,0,29,31,91,'30'])
def test_invalid_horizons(trained,h):
    with pytest.raises(ValueError):model.Predictor(trained).predict(req(),h)


def test_future_feature_rejected(trained):
    r=req().as_dict();r['future_direction']='up'
    with pytest.raises(ValueError):Request.from_dict(r)
    with pytest.raises(ValueError):model.Predictor(trained).predict(r,30)


def test_cutoff_rejects_future_timestamp():
    r=req().as_dict();r['timestamps'][-1]=iso(utc(r['origin_utc'])+timedelta(days=1))
    with pytest.raises(ValueError):Request.from_dict(r)


def test_native_missingness_preserved():
    r=req('sparse');f=model.features(r)
    assert None in r.values and f['gap_censored'] and f['missing_records']>0
    assert f['plateau_lower_bound_days']==0


def test_irregular_does_not_create_observations():
    r=req('irregular');assert len(r.values)<256 and model.features(r)['observed_count']==len(r.values)


@pytest.mark.parametrize('q,expected',[(.1,-5),(.5,0),(.9,7)])
def test_distribution_mass_quantiles(q,expected):assert model.quantile(np.array([-5,0,0,0,7]),q)==expected


def test_quantile_validation():
    for v,q in [([], .5),([float('nan')],.5),([1],1.1)]:
        with pytest.raises(ValueError):model.quantile(np.array(v),q)


def test_negative_signed_magnitudes_valid(trained):
    p=model.Predictor(trained);r=p.predict(req('decay',20),90,'local_median',dict(k=16,confidence=.6,shrink=1.))
    assert r['downward_median']<0 and r['point']>=0


@pytest.mark.parametrize('family',population.OOD)
def test_hidden_branch_cannot_affect_prediction(trained,family):
    rs=[population.generate(population.REPLICAS[1],'identifiability',family,i) for i in range(3)]
    assert len({r['metadata']['history_sha256'] for r in rs})==1
    assert len({r['targets']['30']['value'] for r in rs})==3
    p=model.Predictor(trained)
    for h in (30,60,90):
        out=[p.predict(Request.from_dict(r['request']),h,config=model.CONFIGS[1]) for r in rs]
        assert len({r['point'] for r in out})==1


def test_known_zero_and_constant(trained):
    r=req();p=model.Predictor(trained)
    for value in (0.,100.):
        zero=Request(r.case_id,r.origin_utc,r.timestamps,tuple(value for _ in r.values),tuple(None for _ in r.values))
        assert p.predict(zero,90)['point']==value


def test_ood_families_absent_from_training():assert not set(population.FAMILIES)&set(population.OOD)


def test_training_only_normalization(trained):
    assert trained['preprocessor']['fit_partition']=='train'
    before=json.dumps(trained,sort_keys=True)
    model.Predictor(trained).predict(req('growth',45),90,config=model.CONFIGS[1])
    assert json.dumps(trained,sort_keys=True)==before


def test_bad_probability_config(trained):
    with pytest.raises(ValueError):model.Predictor(trained).predict(req(),30,config=dict(k=16,confidence=1.2,shrink=1.))


def test_nan_risk_rejected():
    with pytest.raises(ValueError):selection.risk([dict(partition='validation',actual=1,point=float('nan'),current=1,model_scale=1)])


def test_no_test_risk_selection():
    with pytest.raises(ValueError):selection.risk([dict(partition='test')])


def test_insufficient_subgroup_not_safe():
    rs=[dict(partition='validation',actual=100.,point=100.,current=100.,model_scale=100.,family='x')]*100
    assert not selection.risk(rs)['safe']


def test_explicit_zero_denominator():
    row=dict(point=1.,actual=2.,current=0.,model_scale=1.,metric_scale=0.,family='a')
    m=evaluation.metrics([row]);assert m['zero_denominator_count']==1 and m['unfloored_normalized_skill'] is None


def test_invalid_interval_not_sorted():
    with pytest.raises(ValueError):evaluation.interval_metrics([dict(q=[2,1])],'q')


def test_model_scale_skill_arithmetic():
    rows=[dict(point=2.,actual=3.,current=1.,model_scale=2.,metric_scale=2.,family='x')]
    r=evaluation.metrics(rows);assert r['mae']==1 and r['raw_skill']==.5 and r['normalized_skill']==.5


@pytest.mark.parametrize('path',['/tmp/x','/home/hp/tst/research/forecasting_mvp/phase6_3/x','/home/hp/tst/research/forecasting_mvp/phase6_4/../x'])
def test_output_boundary(path):
    with pytest.raises(ValueError):study.safe(path)


def test_symlink_boundary(tmp_path,monkeypatch):
    monkeypatch.setattr(study,'ROOT',tmp_path)
    (tmp_path/'alias').symlink_to('/tmp',target_is_directory=True)
    with pytest.raises(ValueError):study.safe(tmp_path/'alias'/'new')


def test_targets_unavailable_before_seal(tmp_path):
    with pytest.raises(FileNotFoundError):study.open_targets(tmp_path,1,'test')


def test_target_seal_tamper(tmp_path):
    (tmp_path/'registration.json').write_text('{}')
    (tmp_path/'1.prediction_seal.json').write_text(json.dumps(dict(registration_sha256='bad',files={})))
    with pytest.raises(ValueError):study.open_targets(tmp_path,1,'test')


@pytest.mark.parametrize('args,reason',[((901,0,0,0),'TIMEOUT'),((0,2*1024**3+1,0,0),'RSS_LIMIT'),((0,0,9*1024**2,0),'LOG_LIMIT'),((0,0,0,129*1024**2),'OUTPUT_LIMIT')])
def test_resource_failure(args,reason):assert limit_failure(*args)==reason


def test_clean_budget():assert limit_failure(1,1024,0,0) is None


def test_prediction_does_not_read_labels():
    text=Path(model.__file__).read_text()
    prediction=text[text.index('class Predictor:'):]
    assert 'open(' not in prediction and 'targets' not in prediction and 'partition' not in prediction


def test_no_pretrained_or_installation_routes():
    root=Path(model.__file__).parent
    for p in root.glob('*.py'):
        text=p.read_text()
        for forbidden in ('import torch','import transformers','pip install','from_pretrained','subprocess.run(["mvn"'):
            assert forbidden not in text
