"""Phase 0 tests; no training, forecasts, downloads or real Sonar requests."""
from dataclasses import replace
from datetime import datetime
from pathlib import Path
import sqlite3

import pytest

from contracts import read_json, write_csv, write_json
from forecasting_mvp.cli import main
from forecasting_mvp.config import ModelCandidate, StudyConfig
from forecasting_mvp.contracts import Observation, TargetContract, finite_delta, utc_iso
from forecasting_mvp.io import artifact_path, file_sha256, publish_manifest, verify_bundle
from forecasting_mvp.verification import audit_v2, environment_record


@pytest.fixture
def configuration(tmp_path):
    return StudyConfig("phase-0", str(tmp_path / "source.db"),
                       "https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1",
                       "CC-BY-NC-SA-4.0", str(tmp_path / "outputs"), (30, 60, 90),
                       (ModelCandidate("chronos-small", "autogluon/chronos-2-small", "a" * 40,
                                       "Apache-2.0", "primary_pretrained", 90, 1024),))


def test_configuration_round_trip(configuration, tmp_path):
    path = tmp_path / "config.json"
    write_json(path, configuration.record())
    restored = StudyConfig.load(path)
    assert restored == configuration
    assert restored.config_id == configuration.config_id
    assert main(["validate-config", "--config", str(path)]) == 0


@pytest.mark.parametrize("change", [
    {"horizons_days": (30, 60, 91)}, {"horizons_days": (True, 60, 90)},
    {"phase": 1}, {"phase": False}, {"mvp_schema_version": True},
    {"dataset_path": "relative.db"}, {"dataset_license": "unknown"},
    {"models": ()}, {"smoke_timeout_seconds": -1},
])
def test_configuration_rejects_invalid_contract(configuration, change):
    with pytest.raises(ValueError):
        replace(configuration, **change)


def test_outputs_cannot_contain_source(configuration):
    with pytest.raises(ValueError):
        replace(configuration, output_root=str(Path(configuration.dataset_path).parent))


def test_checkpoint_requires_immutable_revision(configuration):
    with pytest.raises(ValueError):
        replace(configuration.models[0], revision="main")


@pytest.mark.parametrize("horizon", [30, 60, 90])
def test_exact_horizon_and_utc(horizon):
    target = TargetContract(horizon)
    origin = "2024-01-01T02:00:00+02:00"
    endpoint = target.endpoint(origin)
    assert (datetime.fromisoformat(endpoint.replace("Z", "+00:00")) -
            datetime.fromisoformat(utc_iso(origin).replace("Z", "+00:00"))).total_seconds() == horizon * 86400
    assert endpoint.endswith("Z")
    assert target.target_id == TargetContract(horizon).target_id


@pytest.mark.parametrize("value", [91, 84, True, 90.0])
def test_target_rejects_non_exact_horizons(value):
    with pytest.raises(ValueError):
        TargetContract(value)


@pytest.mark.parametrize("value", ["2024-01-01T00:00:00", datetime(2024, 1, 1)])
def test_naive_time_rejected(value):
    with pytest.raises(ValueError):
        utc_iso(value)


def test_observation_missing_zero_and_negative_delta(tmp_path):
    raw = dict(repository_id="apache-demo", revision="a" * 40, analysis_id="scan1",
               domain_id="imported-domain", historical_time="2024-01-01T02:00:00+02:00",
               source_hash="b" * 64, value_minutes=None)
    missing = Observation(**raw)
    zero = replace(missing, value_minutes=0)
    assert missing.value_minutes is None and zero.value_minutes == 0
    assert missing.observation_id != zero.observation_id
    assert missing.historical_time == "2024-01-01T00:00:00Z"
    assert finite_delta(-12) == -12
    path = tmp_path / "observations.json"
    write_json(path, [missing.record(), zero.record(), {"delta": finite_delta(-12)}])
    assert read_json(path)[0]["value_minutes"] is None
    write_csv(tmp_path / "values.csv", [{"value": None}, {"value": 0}], ["value"])
    assert (tmp_path / "values.csv").read_text().splitlines() == ["value", '""', "0"]
    with pytest.raises(ValueError):
        replace(missing, value_minutes=-1)
    with pytest.raises(ValueError):
        replace(missing, provenance_status="VERIFIED_SCAN")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_nonfinite_serialization_and_delta_rejected(tmp_path, value):
    with pytest.raises(ValueError):
        finite_delta(value)
    if value is not True:
        with pytest.raises(ValueError):
            write_json(tmp_path / "bad.json", {"value": value})


def test_strict_duplicate_json_reused(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"horizons": 30, "horizons": 90}')
    with pytest.raises(ValueError):
        read_json(path)


def test_bundle_round_trip_and_tampering(tmp_path):
    write_json(tmp_path / "artifact.json", {"zero": 0, "missing": None})
    published = publish_manifest(tmp_path, ["artifact.json"], {"purpose": "phase0-test"})
    assert verify_bundle(tmp_path) == published
    assert main(["verify-bundle", "--bundle", str(tmp_path)]) == 0
    with pytest.raises(ValueError):
        publish_manifest(tmp_path, ["artifact.json"], {})
    (tmp_path / "artifact.json").write_text("changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_bundle(tmp_path)
    assert main(["verify-bundle", "--bundle", str(tmp_path)]) == 3


@pytest.mark.parametrize("path", ["../outside", "/tmp/outside", "nested/../../outside", "x\\y"])
def test_bundle_traversal_rejected(tmp_path, path):
    with pytest.raises(ValueError):
        artifact_path(tmp_path, path)


def test_symlinks_partial_and_bad_manifests(tmp_path):
    (tmp_path / "real").write_text("real")
    (tmp_path / "link").symlink_to(tmp_path / "real")
    with pytest.raises(ValueError):
        artifact_path(tmp_path, "link")
    for record in ([1], {"mvp_schema_version": 1, "status": "FAILED", "artifacts": {"real": file_sha256(tmp_path / "real")}}):
        write_json(tmp_path / "manifest.json", record)
        with pytest.raises(ValueError):
            verify_bundle(tmp_path)


def test_wrong_serializer_and_schema_rejected(tmp_path):
    write_json(tmp_path / "artifact.json", {"zero": 0})
    manifest = publish_manifest(tmp_path, ["artifact.json"], {})
    for field, value in (("serializer", "other"), ("mvp_schema_version", True)):
        write_json(tmp_path / "manifest.json", {**manifest, field: value})
        with pytest.raises(ValueError):
            verify_bundle(tmp_path)


def test_read_only_sqlite_audit_and_missing_schema(tmp_path):
    path = tmp_path / "source.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
          CREATE TABLE SONAR_ANALYSIS(PROJECT_ID, ANALYSIS_KEY, DATE, REVISION);
          CREATE TABLE SONAR_MEASURES(PROJECT_ID, ANALYSIS_KEY, SQALE_INDEX, QUALITY_PROFILES);
          CREATE TABLE GIT_COMMITS(PROJECT_ID, COMMIT_HASH, COMMITTER_DATE, PARENTS, IN_MAIN_BRANCH);
          INSERT INTO SONAR_ANALYSIS VALUES('repo', 'key', '2020-01-01', 'rev');
          INSERT INTO SONAR_MEASURES VALUES('repo', 'key', 0, 'profile');
          INSERT INTO GIT_COMMITS VALUES('repo', 'rev', '2020-01-01', '', 1);
        """)
    before = file_sha256(path)
    audit = audit_v2(path)
    assert audit["status"] == "PASS" and audit["unchanged"]
    assert audit["integrity_check"] == ["ok"]
    assert audit["sqale"]["observed_zero"] == 1
    assert audit["sqale"]["missing"] == 0
    assert audit["joined_measurements"] == 1
    assert audit["forecasting_eligibility"] == "NOT_EVALUATED_PHASE_0"
    assert file_sha256(path) == before
    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE SONAR_ANALYSIS")
    assert audit_v2(path)["status"] == "BLOCKED"


def test_environment_metadata_and_cli_no_later_commands(tmp_path):
    record = environment_record(tmp_path)
    assert record["model_loading"] == "NOT_ATTEMPTED"
    assert record["disk"]["free_bytes"] > 0
    with pytest.raises(SystemExit) as exc:
        main(["predict"])
    assert exc.value.code == 2
