"""Output-only policy checks, with no historical execution."""
import inspect
import pytest
from tools import verify_compile_e06 as v


def order():
    return [dict(zip(('prefix','version','goal','execution'),row),project='commons-cli') for row in v.EXPECTED]


def test_original_goal_sequence_and_deploy_mentions_are_distinct():
    assert v.lifecycle_check(order())
    stdout='[INFO] --- artifact:3.5.1:check-buildplan (check-buildplan) @ commons-cli ---\n[INFO] no known issue with org.apache.maven.plugins:maven-deploy-plugin:3.1.2\n'
    assert not v.warning_context(stdout)


@pytest.mark.parametrize('goal',['test','testCompile','manifest','makeAggregateBom','createSPDX','add-module-info','deploy'])
def test_any_unapproved_actual_goal_prevents_compile_proof(goal):
    rows=order();rows.append(dict(prefix='unexpected',version='1',goal=goal,execution='extra',project='commons-cli'))
    assert not v.lifecycle_check(rows)


def test_rat_pom_warnings_never_become_project_or_fatal_dependencies():
    text='[INFO] --- apache-rat:0.16.1:check (rat-check) @ commons-cli ---\n[WARNING] The POM for log4j:log4j:jar:1.2.12 is missing, no dependency information available\n'
    row=v.warning_context(text)[0]
    assert row['observed_during']['prefix']=='apache-rat' and not row['fatal']
    assert row['dependency_domain']=='PLUGIN_METADATA_COLLECTION'
    assert row['required_runtime_jar']=='UNKNOWN_NOT_INFERRED_FROM_POM_WARNING'


def test_no_banner_preserves_unknown_warning_domain():
    row=v.warning_context('[WARNING] The POM for logkit:logkit:jar:1.0.1 is missing')[0]
    assert row['observed_during'] is None and row['dependency_domain']=='UNKNOWN'


def test_mode_identity_preserves_paths_and_rejects_duplicates():
    assert v.modes('644 pom.xml\n755 path with spaces.sh\n')=={'pom.xml':'644','path with spaces.sh':'755'}
    with pytest.raises(ValueError):v.modes('644 pom.xml\n644 pom.xml\n')


def test_audit_cannot_run_build_or_modify_private_evidence():
    source=inspect.getsource(v)
    assert 'subprocess' not in source and '.execute_once(' not in source and '.write(' not in source
    assert '.docker(' not in source and 'urllib' not in source
