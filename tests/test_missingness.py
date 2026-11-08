import csv
import json

import pytest

import build_module_mart as mart
import modules


@pytest.fixture
def aggregate(tmp_path, monkeypatch):
    monkeypatch.setattr(mart, 'DATA_DIR', tmp_path)
    mapper = modules.ModuleMapper({'strategy': 'package', 'package_base': 'com.acme', 'extra_depth': 1})

    def run(rows, issues=(), missing_export=False):
        with (tmp_path / 'measures_week_01.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'ncloc', *mart.SUM_MEASURES])
            writer.writeheader()
            writer.writerows(rows)
        if not missing_export:
            (tmp_path / 'issues_week_01.json').write_text(json.dumps(list(issues)))
        return mart.aggregate_week('week_01', mapper)
    return run


def file(name='A', complexity='10', **extra):
    return {'file_path': f'src/main/java/com/acme/core/{name}.java', 'ncloc': '100',
            'lines': '120', 'complexity': complexity, **extra}


def issue(name='A', **extra):
    return {'key': 'i1', 'component': f'p:src/main/java/com/acme/core/{name}.java',
            'status': 'OPEN', 'type': 'CODE_SMELL', 'severity': 'MAJOR',
            'effort_minutes': '1h', **extra}


def test_blank_is_unknown():
    assert mart.fnum('') is None


def test_explicit_zero_is_observed():
    assert mart.fnum('0') == 0


@pytest.mark.parametrize('value', ['broken', 'NaN', 'inf', '-1', True])
def test_invalid_numeric_rejected(value):
    with pytest.raises(ValueError):
        mart.fnum(value)


def test_incomplete_sum_is_unknown(aggregate):
    states, _ = aggregate([file(), file('B', '')])
    assert states['com.acme.core']['complexity'] is None


def test_missing_issues_is_unknown(aggregate):
    states, _ = aggregate([file()], missing_export=True)
    assert states['com.acme.core']['td'] is None


def test_unmeasured_issue_rejected(aggregate):
    with pytest.raises(ValueError):
        aggregate([file()], [issue('OUTSIDE')])


def test_duplicate_measure_rejected(aggregate):
    with pytest.raises(ValueError):
        aggregate([file(), file()])


def test_duplicate_issue_rejected(aggregate):
    with pytest.raises(ValueError):
        aggregate([file()], [issue(), issue()])


def test_unknown_issue_type_rejected(aggregate):
    with pytest.raises(ValueError):
        aggregate([file()], [issue(type=None)])


def test_known_empty_issue_population_is_zero(aggregate):
    states,_=aggregate([file()],[])
    row=mart.state_to_columns(states['com.acme.core'])
    assert row['finding_count_t0']==0 and row['technical_debt_minutes_t0']==0
    assert row['issues_status']=='OBSERVED'


def test_missing_effort_is_not_zero_debt(aggregate):
    states,_=aggregate([file()],[issue(effort_minutes=None)])
    row=mart.state_to_columns(states['com.acme.core'])
    assert row['finding_count_t0']==1
    assert row['technical_debt_minutes_t0'] is None
    assert row['code_smell_remediation_effort_t0'] is None
    assert row['bug_remediation_effort_t0']==0  # observed absence, not imputation
    assert row['max_file_td_t0'] is None
    assert row['effort_status']=='UNKNOWN_OBSERVATION'
    assert row['missing_effort_findings']==1


def test_partial_sum_observation_accounting(aggregate):
    states,_=aggregate([file(),file('B','')])
    row=mart.state_to_columns(states['com.acme.core'])
    assert row['complexity_status']=='UNKNOWN_OBSERVATION'
    assert row['complexity_partial_sum']==10
    assert row['complexity_observed_files']==1 and row['complexity_missing_files']==1


def test_missing_sqale_never_becomes_healthy_rating(aggregate):
    states,_=aggregate([file()])
    row=mart.state_to_columns(states['com.acme.core'])
    assert row['sqale_rating_t0'] is None and row['sqale_debt_ratio_t0'] is None


def test_zero_ncloc_module_retained_but_density_unknown(aggregate):
    states,_=aggregate([file(ncloc='0')])
    row=mart.state_to_columns(states['com.acme.core'])
    assert row['file_count_t0']==1 and row['ncloc_t0']==0
    assert row['finding_density_t0'] is None


@pytest.mark.parametrize('sqale',['0','10','100'])
def test_reconciliation_is_an_error_not_a_warning(aggregate,sqale):
    with pytest.raises(ValueError,match='disagree'):
        aggregate([file(sqale_index=sqale)],[issue(effort_minutes='60')])


def test_exact_project_prefix_supports_colons(aggregate,monkeypatch):
    monkeypatch.setattr(mart.config,'PROJECT_KEY','org:repo')
    states,_=aggregate([file()],[issue(component='org:repo:src/main/java/com/acme/core/A.java')])
    assert states['com.acme.core']['td']==60


def test_other_project_rejected(aggregate,monkeypatch):
    monkeypatch.setattr(mart.config,'PROJECT_KEY','expected')
    with pytest.raises(ValueError,match='another project'):
        aggregate([file()],[issue()])
