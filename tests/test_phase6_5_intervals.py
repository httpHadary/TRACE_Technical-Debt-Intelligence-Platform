import pytest
from tools.verify_phase6_5_intervals import calculate

def test_interval_score_and_coverage():
    r=calculate([(0.,2.,1.,0.),(1.,3.,5.,10.)])
    assert r['coverage']==.5 and r['mean_width']==2 and r['interval_score']==12
    assert r['normalized_mean_width']==1.1

def test_missing_group_is_unavailable():assert calculate([]) is None

@pytest.mark.parametrize('row',[(2.,1.,0.,1.),(-1.,1.,0.,1.),(0.,1.,float('nan'),1.)])
def test_bad_interval_is_never_repaired(row):
    with pytest.raises(ValueError):calculate([row])
