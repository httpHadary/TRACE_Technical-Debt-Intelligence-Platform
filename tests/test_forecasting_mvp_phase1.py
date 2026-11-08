"""Synthetic source integrity/ancestry tests only; no models or future labels."""
from dataclasses import replace
from pathlib import Path
import csv
import sqlite3

import pytest

from contracts import read_json
from forecasting_mvp.cli import main
from forecasting_mvp.io import file_sha256, verify_bundle
from forecasting_mvp.v2_import import HistoryConfig, ingest_history, mainline_audit, parse_parents, profile_record


S1, S2, S3 = "a" * 40, "b" * 40, "c" * 40
PROFILE = '[{"key":"java-profile";"language":"java";"name":"Test; profile";"rulesUpdatedAt":"2020-01-01"}]'


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "source.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
          CREATE TABLE SONAR_ANALYSIS(PROJECT_ID, ANALYSIS_KEY, DATE, REVISION);
          CREATE TABLE SONAR_MEASURES(PROJECT_ID, ANALYSIS_KEY, SQALE_INDEX, QUALITY_PROFILES);
          CREATE TABLE GIT_COMMITS(PROJECT_ID, COMMIT_HASH, COMMITTER_DATE, PARENTS, IN_MAIN_BRANCH);
        """)
        for sha, stamp, parents in [(S1, "2020-01-01", []), (S2, "2020-01-02", [S1]), (S3, "2020-01-03", [S2])]:
            db.execute("INSERT INTO GIT_COMMITS VALUES(?,?,?,?,?)", ("org.apache:demo", sha, stamp + "T00:00:00+00:00", str(parents), "True"))
        db.execute("INSERT INTO SONAR_ANALYSIS VALUES(?,?,?,?)", ("org.apache:demo", "scan1", "2020-01-01 00:00:00", S1))
        db.execute("INSERT INTO SONAR_ANALYSIS VALUES(?,?,?,?)", ("org.apache:demo", "scan3", "2020-01-03 00:00:00", S3))
        db.execute("INSERT INTO SONAR_MEASURES VALUES(?,?,?,?)", ("org.apache:demo", "scan1", 0, PROFILE))
        db.execute("INSERT INTO SONAR_MEASURES VALUES(?,?,?,?)", ("org.apache:demo", "scan3", None, PROFILE))
    return path


def config_for(path, tmp_path):
    return HistoryConfig(str(path), str(tmp_path / "out"), file_sha256(path))


def csv_rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def test_extraction_missingness_provenance_and_determinism(database, tmp_path):
    config = config_for(database, tmp_path)
    first, second = tmp_path / "out/first", tmp_path / "out/second"
    before = file_sha256(database)
    audit = ingest_history(config, first)
    repeat = ingest_history(config, second)
    assert audit == repeat
    assert file_sha256(database) == before
    assert audit["source"]["unchanged"]
    assert audit["counts"]["historical_debt_rows"] == 2
    assert audit["counts"]["missing_debt_values"] == 1
    assert audit["counts"]["observed_zero_debt"] == 1
    assert audit["counts"]["unmeasured_revisions"] == 1
    assert audit["counts"]["in_span_unmeasured_revisions"] == 1
    assert audit["future_labels_constructed"] is False
    rows = csv_rows(first / "historical_debt.csv")
    assert rows[0]["sqale_index_minutes"] == "0.0"
    assert rows[1]["sqale_index_minutes"] == ""
    assert {r["source_project_id"] for r in rows} == {"org.apache:demo"}
    assert {r["mainline_status"] for r in rows} == {"FIRST_PARENT"}
    assert rows[0]["historical_timestamp"] == "2020-01-01T00:00:00Z"
    assert all(r["source_sha256"] == before and r["provenance_status"] == "AUDITED_IMPORTED" for r in rows)
    assert not any("actual_future" in k or "label_end" in k for k in rows[0])
    for p in first.iterdir():
        assert p.read_bytes() == (second / p.name).read_bytes()
    assert verify_bundle(first)["status"] == "COMPLETE"
    with pytest.raises(ValueError):
        ingest_history(config, first)


def test_mainline_uses_ancestry_not_latest_time():
    commits = {S1: {"parents": (), "time": "2020-01-05T00:00:00Z"},
               S2: {"parents": (S1,), "time": "2020-01-02T00:00:00Z"}}
    audit, indices = mainline_audit(commits)
    assert audit["selected_tip"] == S2
    assert indices == {S1: 0, S2: 1}
    assert audit["first_parent_timestamp_inversions"] == 1


def test_ambiguous_tips_and_missing_parents():
    commits = {S1: {"parents": (), "time": "2020-01-01T00:00:00Z"},
               S2: {"parents": (), "time": "2020-01-02T00:00:00Z"}}
    audit, indices = mainline_audit(commits)
    assert audit["selected_tip"] is None and indices == {}
    assert audit["boundary"] == "AMBIGUOUS_TIPS"
    audit, indices = mainline_audit({S2: {"parents": (S1,), "time": "2020-01-02T00:00:00Z"}})
    assert audit["boundary"] == "MISSING_FIRST_PARENT"
    assert audit["missing_parent_edges"] == 1


def test_no_tip_cycle_and_merge_non_first_parent():
    commits = {S1: {"parents": (S2,), "time": "2020-01-01T00:00:00Z"},
               S2: {"parents": (S1,), "time": "2020-01-02T00:00:00Z"}}
    audit, indices = mainline_audit(commits)
    assert audit["boundary"] == "NO_TIP_OR_CYCLE" and not indices
    commits[S1]["parents"] = ()
    commits[S2]["parents"] = ()
    commits[S3] = {"parents": (S1, S2), "time": "2020-01-03T00:00:00Z"}
    audit, indices = mainline_audit(commits)
    assert audit["selected_tip"] == S3
    assert S1 in indices and S2 not in indices


def test_profiles_normalize_order_and_preserve_strings():
    profiles, status = profile_record(PROFILE)
    assert status == "KNOWN_METADATA_ONLY"
    assert profiles[0]["name"] == "Test; profile"
    assert profile_record(None) == (None, "MISSING")
    assert profile_record("invalid") == (None, "INVALID")
    assert profile_record('[{"key":"x","language":"java"},{"key":"y","language":"java"}]')[1] == "INVALID"


def test_disconnected_cycle_is_not_hidden_by_valid_tip():
    commits = {S1: {"parents": (S2,), "time": "2020-01-01T00:00:00Z"},
               S2: {"parents": (S1,), "time": "2020-01-02T00:00:00Z"},
               S3: {"parents": (), "time": "2020-01-03T00:00:00Z"}}
    audit, indices = mainline_audit(commits)
    assert audit["boundary"] == "CYCLIC_GRAPH"
    assert audit["selected_tip"] is None and indices == {}
    assert audit["cyclic_or_cycle_dependent_nodes"] == 2


def test_changed_profile_and_time_inversion_split_metadata_segments(database, tmp_path):
    with sqlite3.connect(database) as db:
        db.execute("UPDATE GIT_COMMITS SET COMMITTER_DATE='2019-12-31T00:00:00+00:00' WHERE COMMIT_HASH=?", (S3,))
        db.execute("UPDATE SONAR_ANALYSIS SET DATE='2019-12-31 00:00:00' WHERE ANALYSIS_KEY='scan3'")
    result = tmp_path / "out/run"
    audit = ingest_history(config_for(database, tmp_path), result)
    rows = csv_rows(result / "historical_debt.csv")
    assert audit["repositories"][0]["ancestry"]["first_parent_timestamp_inversions"] == 1
    assert len({r["domain_segment_id"] for r in rows}) == 2
    assert any(r["chronology_status"] == "INVERTED_FIRST_PARENT_EDGE" for r in rows)


def test_missing_measurement_excluded_duplicate_git_not_merged(database, tmp_path):
    with sqlite3.connect(database) as db:
        db.execute("DELETE FROM SONAR_MEASURES WHERE ANALYSIS_KEY='scan3'")
        db.execute("INSERT INTO GIT_COMMITS SELECT * FROM GIT_COMMITS WHERE COMMIT_HASH=?", (S1,))
    audit = ingest_history(config_for(database, tmp_path), tmp_path / "out/result")
    assert audit["exclusion_reason_counts"]["MISSING_MEASUREMENT"] == 1
    assert audit["git_exclusion_reason_counts"]["DUPLICATE_GIT_KEY"] == 1
    assert audit["counts"]["historical_debt_rows"] == 0


@pytest.mark.parametrize("value", ["__import__('os').system('false')", "['short']", "{}", str([S1, S1])])
def test_invalid_parents_no_execution(value):
    with pytest.raises((ValueError, SyntaxError)):
        parse_parents(value)


@pytest.mark.parametrize("mutation,reason", [
    ("UPDATE SONAR_MEASURES SET SQALE_INDEX=-1 WHERE ANALYSIS_KEY='scan1'", "Invalid measurement"),
    ("UPDATE SONAR_ANALYSIS SET DATE='2020-01-04' WHERE ANALYSIS_KEY='scan1'", "ANALYSIS_COMMIT_TIMESTAMP_MISMATCH"),
    ("UPDATE SONAR_ANALYSIS SET ANALYSIS_KEY='' WHERE ANALYSIS_KEY='scan1'", "BLANK_ANALYSIS_KEY"),
    ("INSERT INTO SONAR_MEASURES SELECT * FROM SONAR_MEASURES WHERE ANALYSIS_KEY='scan1'", "DUPLICATE_MEASURE_KEY"),
    ("INSERT INTO SONAR_ANALYSIS SELECT * FROM SONAR_ANALYSIS WHERE ANALYSIS_KEY='scan1'", "DUPLICATE_ANALYSIS_KEY"),
    ("UPDATE GIT_COMMITS SET COMMITTER_DATE='2020-01-01' WHERE COMMIT_HASH='" + S1 + "'", "UNADMITTED_GIT_REVISION"),
])
def test_exclusions_not_silent_repair(database, tmp_path, mutation, reason):
    with sqlite3.connect(database) as db:
        db.execute(mutation)
    audit = ingest_history(config_for(database, tmp_path), tmp_path / "out/result")
    assert audit["status"] == "PARTIAL"
    assert any(reason in key for key in audit["exclusion_reason_counts"])
    assert audit["counts"]["excluded_analyses"] >= 1


def test_profile_changes_and_missing_metadata_retained(database, tmp_path):
    with sqlite3.connect(database) as db:
        db.execute("UPDATE SONAR_MEASURES SET QUALITY_PROFILES=NULL WHERE ANALYSIS_KEY='scan3'")
    result = tmp_path / "out/run"
    audit = ingest_history(config_for(database, tmp_path), result)
    assert audit["status"] == "PARTIAL"
    rows = csv_rows(result / "historical_debt.csv")
    assert rows[1]["domain_id"] == "" and rows[1]["profile_status"] == "MISSING"
    assert "PROFILE_MISSING" in rows[1]["limitations"]


def test_source_hash_schema_output_and_config_guards(database, tmp_path):
    config = config_for(database, tmp_path)
    with pytest.raises(ValueError):
        ingest_history(replace(config, expected_source_sha256="0" * 64), tmp_path / "out/run")
    assert not (tmp_path / "out/run").exists()
    with pytest.raises(ValueError):
        ingest_history(config, tmp_path / "outside")
    with pytest.raises(ValueError):
        replace(config, phase=2)
    with pytest.raises(ValueError):
        replace(config, dataset_license="unknown")
    with sqlite3.connect(database) as db:
        db.execute("DROP TABLE SONAR_ANALYSIS")
    with pytest.raises(ValueError, match="schema"):
        ingest_history(replace(config, expected_source_sha256=None), tmp_path / "out/run")


def test_phase1_cli(database, tmp_path, capsys):
    from contracts import write_json
    from dataclasses import asdict
    config = tmp_path / "config.json"
    write_json(config, asdict(config_for(database, tmp_path)))
    status = main(["ingest-history", "--config", str(config), "--out", str(tmp_path / "out/run")])
    assert status == 0
    assert '"future_labels_constructed": false' in capsys.readouterr().out
    assert read_json(tmp_path / "out/run/historical_data_audit.json")["counts"]["historical_debt_rows"] == 2


def test_source_change_prevents_publication(database, tmp_path, monkeypatch):
    import forecasting_mvp.v2_import as importer
    config = config_for(database, tmp_path)
    original = file_sha256(database)
    checks = iter([original, "0" * 64])
    monkeypatch.setattr(importer, "file_sha256", lambda path: next(checks))
    with pytest.raises(ValueError, match="Source changed"):
        ingest_history(config, tmp_path / "out/run")
    assert not (tmp_path / "out/run").exists()
