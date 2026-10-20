"""Independent evidence checks, never a numerical study rerun."""
import importlib.util
from pathlib import Path
import pytest

path=Path(__file__).resolve().parents[1]/'tools/verify_phase6_4.py'
spec=importlib.util.spec_from_file_location('audit64',path)
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


@pytest.mark.parametrize('a,b',[(1,1.1),(None,0),(float('nan'),1)])
def test_false_arithmetic_rejected(a,b):
    with pytest.raises(ValueError):audit.close(a,b)


def test_exact_null_allowed():audit.close(None,None)


def test_family_balance_not_pooled():
    rows=[dict(family='a',value=1)]*10+[dict(family='b',value=9)]
    assert audit.macro(rows,lambda r:r['value'])==5


def test_large_decreases_and_exact_stability():
    rows=[dict(current=100,actual=70,scale_band=0),dict(current=100,actual=100,scale_band=0)]
    assert audit.filter_rows(rows,'large_decrease')==rows[:1]
    assert audit.filter_rows(rows,'unchanged')==rows[1:]


def test_auditor_has_no_fit_or_forecast_call():
    source=path.read_text()
    assert '.predict(' not in source and '.fit(' not in source
