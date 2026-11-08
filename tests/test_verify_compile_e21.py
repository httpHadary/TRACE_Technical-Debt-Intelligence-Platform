"""Target-specific read-only proof, with no Docker/Maven invocation."""
from pathlib import Path
import inspect
import pytest
from tools import verify_compile_e21 as v


def test_output_population_is_dynamic_not_t0_count():
    sources=[dict(path='src/main/java/Foo.java'),dict(path='src/test/java/Test.java')]
    classes=dict(classes=[dict(path='a/Foo.class'),dict(path='a/Foo$Inner.class')])
    assert all(v.output_sets_match({'src/main/java/Foo.java'},{'a/Foo.class','a/Foo$Inner.class'},sources,classes).values())
    assert not all(v.output_sets_match({'src/main/java/Foo.java'},{'a/Foo.class'},sources,classes).values())
    assert not all(v.output_sets_match({'src/main/java/Foo.java','src/test/java/Test.java'},{'a/Foo.class','a/Foo$Inner.class'},sources,classes).values())
    assert not all(v.output_sets_match(set(),set(),[],dict(classes=[])).values())


def test_auditor_does_not_execute_or_borrow_t0_expectations():
    source=inspect.getsource(v)
    for forbidden in ('subprocess','.execute_once(','.docker(','.write(','EXPECTED','==37','==106','effective-pom/effective-pom.xml'):
        assert forbidden not in source
    assert 'UNAVAILABLE_NOT_ENUMERATED_BY_REGISTERED_COMPILE' in source
    assert 'UNAVAILABLE_NOT_LOGGED_BY_REGISTERED_COMMAND' in source


@pytest.mark.parametrize('goal',['test','testCompile','manifest','makeAggregateBom','createSPDX','add-module-info','deploy'])
def test_additional_goal_rejected(goal):
    expected=[dict(prefix='compiler',version='3.13.0',goal='compile',execution='default-compile',phase='compile')]
    rows=[dict(expected[0],project='commons-cli'),dict(prefix='bad',version='1',goal=goal,execution='extra',project='commons-cli')]
    assert not v.e.lifecycle_matches(rows,expected)


def test_lifecycle_checks_phase_order_and_identity():
    rows=[dict(prefix='first',version='1',goal='enforce',execution='v',phase='validate'),dict(prefix='compiler',version='3.13.0',goal='compile',execution='default-compile',phase='compile')]
    actual=[dict(r,project='commons-cli') for r in rows]
    assert v.e.lifecycle_matches(actual,rows)
    assert not v.e.lifecycle_matches(actual[::-1],rows)
    actual[0]['project']='unregistered'
    assert not v.e.lifecycle_matches(actual,rows)
