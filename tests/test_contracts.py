import pytest
from contracts import read_csv, read_json, source_path, ratio
from td_utils import parse_minutes
import modules
import build_module_mart as mart


@pytest.mark.parametrize('value, expected', [(None,None),('',None),('0',0),('1d2h30min',630),('5min',5),('1.5h',90)])
def test_effort(value, expected):
    assert parse_minutes(value) == expected


@pytest.mark.parametrize('value', ['junk5min', '-1h', '1h2h', 'inf', True, '1mo'])
def test_effort_bad(value):
    with pytest.raises(ValueError):
        parse_minutes(value)


@pytest.mark.parametrize('text', ['a,a\n1,2\n', 'a,b\n1\n', 'a,b\n1,2,3\n', 'a,b\n"bad,2\n', '\n'])
def test_bad_csv(tmp_path, text):
    path = tmp_path/'x.csv'
    path.write_text(text)
    with pytest.raises((ValueError, __import__('csv').Error)):
        read_csv(path)


def test_duplicate_csv_identity(tmp_path):
    path = tmp_path/'x.csv'
    path.write_text('label,value\na,0\na,1\n')
    with pytest.raises(ValueError):
        read_csv(path, key='label')


def test_duplicate_json(tmp_path):
    path = tmp_path/'x.json'
    path.write_text('{"a":0,"a":1}')
    with pytest.raises(ValueError):
        read_json(path)


@pytest.mark.parametrize('path', ['../A.java', '/A.java', 'a//A.java', './A.java', 'a/../A.java', 'a\\A.java', '.', 'a\nA.java'])
def test_unsafe_path(path):
    with pytest.raises(ValueError):
        source_path(path)


@pytest.mark.parametrize('path, expected', [
    ('src/main/java/com/test/Helper.java', True), ('src/main/java/com/sample/Sample.java',True),
    ('build/src/main/java/A.java',False), ('src/test/java/A.java',False), ('README.java',False),
    ('module/src/main/java/com/acme/É.java',True), ('src/main/kotlin/A.kt',False)])
def test_source_scope(path, expected):
    assert modules.is_production_file(path) == expected


def test_ratios_missing_not_zero():
    assert ratio(None, 10) is None
    assert ratio(10, None) is None
    assert ratio(10, 0) is None
    assert ratio(0, 10) == 0


def test_partitions_do_not_move_with_survivors_or_updates():
    full = [{'_t0_week':w, 'week':w} for w in range(27,127)]
    partial = [{'_t0_week':w, 'week':w} for w in (27,86,87,99,106,107,119,126,127)]
    mart.assign_partitions(full)
    mart.assign_partitions(partial)
    expected = {r['week']:r['partition'] for r in full}
    assert all(r['partition'] == expected.get(r['week'],'UNASSIGNED') for r in partial)
    assert sum(r['partition']=='TRAIN' for r in full)==60
    assert sum(r['partition']=='PURGED' for r in full)==24


@pytest.mark.parametrize('field', ['sonarqube_version','java_analyzer_version','quality_profile_hash','compatible_rule_domain_version','scanner_image'])
def test_changed_domain_incompatible(field):
    meta = {k:'same' for k in ['sonarqube_version','java_analyzer_version','quality_profile_hash','compatible_rule_domain_version','scanner_image','analysis_mode']}
    snap = {'analysis_mode':'same'}
    assert mart.analyzers_compatible(meta,snap,meta,snap)
    assert not mart.analyzers_compatible(meta,snap,{**meta,field:'different'},snap)
