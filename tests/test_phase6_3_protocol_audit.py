"""Documentary checks detect, rather than repair/relabel, a frozen run deviation."""
from copy import deepcopy
from tools.audit_phase6_3_protocol import assess
from forecasting_research.phase6_3.selection import choose


def fixtures():
    selection=dict(horizons={str(h):dict(configs=dict(adaptive_persistence=dict(method='adaptive_persistence',shrink=.5)),
                   method_safety=dict(adaptive_persistence=True),risks=dict(adaptive_persistence=dict(large_decrease_n=12))) for h in (30,60,90)})
    metrics=dict(aggregate=[dict(method='adaptive_persistence',partition='test',horizon=h,scale='all',stratum='large_decrease',n=12) for h in (30,60,90)])
    return selection,metrics


def test_valid_protocol_is_distinct_from_forecast_improvement():
    s,m=fixtures();assert assess(s,m)['phase_status']=='PASS'


def test_unverified_active_ap_is_protocol_deviation():
    s,m=fixtures();s['horizons']['30']['method_safety']['adaptive_persistence']=False
    r=assess(s,m);assert r['phase_status']=='PARTIAL'
    assert r['issues'][0]['kind']=='PROTOCOL_DEVIATION' and r['corrected_predictions']==0


def test_zero_adjustment_does_not_get_relabelled_active():
    s,m=fixtures();s['horizons']['30']['method_safety']['adaptive_persistence']=False
    s['horizons']['30']['configs']['adaptive_persistence']['shrink']=0
    assert not assess(s,m)['issues']


def test_empty_decrease_stratum_stays_unavailable():
    s,m=fixtures();m['aggregate'][0]['n']=0
    r=assess(s,m);assert r['phase_status']=='PARTIAL' and r['issues'][0]['metric_status']=='UNAVAILABLE'


def test_small_stratum_stays_exploratory():
    s,m=fixtures();m['aggregate'][0]['n']=3
    assert assess(s,m)['issues'][0]['metric_status']=='EXPLORATORY'


def test_frozen_selector_defect_is_reproduced_without_any_fitting():
    candidates=[dict(config=dict(shrink=0.),risk=dict(safety_eligible=False,normalized_family_error=.2)),
                dict(config=dict(shrink=.5),risk=dict(safety_eligible=False,normalized_family_error=.1))]
    before=deepcopy(candidates);result=choose(candidates)
    assert result['any_safe'] is False and result['config']['shrink']==.5
    assert candidates==before  # Historical behavior is evidenced, not silently patched.
