"""Dataset correctness tests, with no model fitting or prediction."""
from datetime import timedelta
from dataclasses import replace
import json
import csv

import pytest

from contracts import digest, write_json, read_json
from forecasting_mvp.contracts import utc_iso, utc_timestamp, TargetContract
from forecasting_mvp.targets import RepositoryStates, next_monday, context_features
from forecasting_mvp.splits import build_splits
from forecasting_mvp.dataset import DatasetConfig, construct_dataset
from forecasting_mvp.v2_import import HistoryConfig, ingest_history
from forecasting_mvp.io import file_sha256, verify_bundle
from forecasting_mvp.cli import main


def history(n=720, missing=(), profile_changes=None):
    git, obs = [], []
    start = utc_timestamp("2020-01-01T00:00:00Z")
    profile_changes = profile_changes or {}
    profile = "profile1"
    for i in range(n):
        sha = f"{i + 1:040x}"
        stamp = utc_iso(start + timedelta(days=i))
        git.append({"commit_sha": sha, "committer_timestamp": stamp, "first_parent_index": str(i),
                    "parents_json": json.dumps([f"{i:040x}"] if i else [])})
        profile = profile_changes.get(i, profile)
        if i not in missing:
            obs.append({"commit_sha": sha, "committer_timestamp": stamp, "historical_timestamp": stamp,
                        "observation_id": digest([sha, profile, i]), "sqale_index_minutes": str(i * 2),
                        "profile_hash": profile or "", "profile_status": "KNOWN_METADATA_ONLY" if profile else "MISSING",
                        "provenance_status": "AUDITED_IMPORTED", "metric": "SQALE_INDEX", "scope_id": "native_project"})
    return git, obs


@pytest.mark.parametrize("horizon", [30, 60, 90])
def test_exact_calendar_ground_truth(horizon):
    git, obs = history()
    states = RepositoryStates(git, obs)
    origin = "2020-07-01T00:00:00Z"
    label, error = states.endpoint(origin, horizon)
    assert error is None
    assert (utc_timestamp(label["endpoint_utc"]) - utc_timestamp(origin)).total_seconds() == horizon * 86400
    first, _ = states.state(origin)
    assert label["actual_delta_minutes"] == horizon * 2
    assert label["actual_minutes"] - first["value"] == label["actual_delta_minutes"]
    assert label["endpoint_revision"] == git[first["index"] + horizon]["commit_sha"]
    with pytest.raises(ValueError):
        states.endpoint(origin, 91)


def test_unmeasured_revision_never_carries_or_nearest_matches():
    git, obs = history(missing=(210,))
    states = RepositoryStates(git, obs)
    origin = utc_iso(utc_timestamp("2020-01-01T00:00:00Z") + timedelta(days=180))
    assert states.endpoint(origin, 30)[1] == "ENDPOINT_UNMEASURED_SELECTED_REVISION"
    assert states.state(utc_iso(utc_timestamp(origin) + timedelta(days=30, hours=12)))[1] == "UNMEASURED_SELECTED_REVISION"


def test_unchanged_state_needs_archived_extent_and_same_revision():
    git, obs = history(n=3)
    git[1]["committer_timestamp"] = obs[1]["committer_timestamp"] = obs[1]["historical_timestamp"] = "2020-06-01T00:00:00Z"
    git[2]["committer_timestamp"] = obs[2]["committer_timestamp"] = obs[2]["historical_timestamp"] = "2021-01-01T00:00:00Z"
    states = RepositoryStates(git, obs)
    label, error = states.endpoint("2020-02-01T00:00:00Z", 90)
    assert error is None and label["endpoint_state_kind"] == "UNCHANGED_VERIFIED_STATE"
    assert label["actual_minutes"] == 0
    assert states.endpoint("2020-12-01T00:00:00Z", 90)[1] == "ENDPOINT_OUTSIDE_ARCHIVED_HISTORY"


def test_missing_context_masks_and_ttm_lengths():
    git, obs = history(missing=(150, 151))
    states = RepositoryStates(git, obs)
    origin = "2020-07-01T00:00:00Z"
    assert states.context(origin, 90)[1] == "MISSING_CONTEXT_STATE"
    context, error = states.context(origin, 90, masked=True)
    assert error is None and context["missing_count"] == 2
    assert context["values"].count(None) == 2
    assert max(map(utc_timestamp, context["timestamps"])) == utc_timestamp(origin)
    assert states.context(origin, 512)[1] == "INSUFFICIENT_CONTEXT_SPAN"
    dense = RepositoryStates(*history(missing=range(120, 160)))
    assert dense.context(origin, 90, masked=True)[1] == "MASKED_CONTEXT_BELOW_80_PERCENT"


def test_profile_change_revert_between_daily_points_is_not_hidden():
    git, obs = history()
    # A known transition/reversion in the target interval must not be hidden by equal endpoint hashes.
    obs[205]["profile_hash"] = "profile2"
    states = RepositoryStates(git, obs)
    assert states.endpoint("2020-07-01T00:00:00Z", 30)[1] == "TARGET_PROFILE_SEGMENT_CROSSING"
    assert states.context("2020-08-10T00:00:00Z", 90)[1] == "CONTEXT_PROFILE_SEGMENT_CROSSING"


def test_future_mutation_cannot_change_past_features_or_context_id():
    git, obs = history()
    origin = "2020-07-01T00:00:00Z"
    before, _ = RepositoryStates(git, obs).context(origin, 90)
    for row in obs[200:]:
        row["sqale_index_minutes"] = "999999"
    after, _ = RepositoryStates(git, obs).context(origin, 90)
    assert before == after and digest(before) == digest(after)
    assert context_features(before) == context_features(after)
    assert all("endpoint" not in k and "actual" not in k for k in context_features(before))


def test_broken_ancestry_and_inversions_rejected():
    git, obs = history(10)
    git[5]["parents_json"] = "[]"
    with pytest.raises(ValueError, match="ancestry"):
        RepositoryStates(git, obs)
    git, obs = history(10)
    git[5]["committer_timestamp"] = "2019-01-01T00:00:00Z"
    with pytest.raises(ValueError, match="Nonmonotonic"):
        RepositoryStates(git, obs)


def test_duplicate_observation_and_timezone_boundary():
    git, obs = history(10)
    with pytest.raises(ValueError, match="Ambiguous"):
        RepositoryStates(git, obs + [obs[0]])
    assert next_monday("2020-01-06T00:00:00Z") == utc_timestamp("2020-01-06T00:00:00Z")
    assert next_monday("2020-01-06T00:00:01Z") == utc_timestamp("2020-01-13T00:00:00Z")


def split_rows():
    rows = []
    start = utc_timestamp("2010-01-04T00:00:00Z")
    for repo in range(8):
        for day in range(0, 2101, 7):
            for h in (30, 60, 90):
                origin = utc_iso(start + timedelta(days=day))
                rows.append({"repository_id": f"repo{repo}", "track": "core90", "horizon_days": h,
                             "origin_utc": origin, "endpoint_utc": TargetContract(h).endpoint(origin),
                             "forecast_id": digest([repo, day, h])})
    return rows


def test_purged_calendar_and_held_repository_splits():
    rows = split_rows()
    result = build_splits(rows, "core90", "study")
    assert result["status"] == "PASS"
    assert result == build_splits(list(reversed(rows)), "core90", "study")
    held = result["held_repository_ids"]
    assert len(held) == 2
    bounds = {k: utc_timestamp(v) for k, v in result["boundaries"].items()}
    for r in rows:
        phase = result["assignments"][r["forecast_id"]]
        if phase == "train":
            assert r["repository_id"] not in held
            assert utc_timestamp(r["endpoint_utc"]) < bounds["validation_start"]
        if phase == "validation":
            assert r["repository_id"] not in held
            assert utc_timestamp(r["endpoint_utc"]) < bounds["test_start"]
        if phase.startswith("test"):
            assert utc_timestamp(r["origin_utc"]) >= bounds["validation_end"] + timedelta(days=90)
        if r["repository_id"] in held:
            assert phase in ("test_repository", "UNUSED_HELDOUT", "EXCLUDED_SHARED_CALENDAR")


def test_insufficient_splits_report_blocker():
    result = build_splits(split_rows()[:15], "core90", "study")
    assert result["status"] == "BLOCKED"
    assert result["assignments"] == {}


def test_split_rejects_wrong_horizon_and_duplicate_ids():
    rows = split_rows()[:20]
    with pytest.raises(ValueError, match="Duplicate"):
        build_splits(rows + [rows[0]], "core90", "study")
    rows[0]["endpoint_utc"] = TargetContract(60).endpoint(rows[0]["origin_utc"])
    with pytest.raises(ValueError, match="exact"):
        build_splits(rows, "core90", "study")


def test_equal_commit_times_use_chain_order():
    git, obs = history(3)
    git[1]["committer_timestamp"] = obs[1]["committer_timestamp"] = obs[1]["historical_timestamp"] = git[0]["committer_timestamp"]
    state, reason = RepositoryStates(git, obs).state(git[0]["committer_timestamp"])
    assert reason is None and state["commit_sha"] == git[1]["commit_sha"]


def test_full_bundle_construction_deterministic_and_input_guards(tmp_path):
    import sqlite3
    db_path = tmp_path / "source.db"
    with sqlite3.connect(db_path) as db:
        db.executescript("CREATE TABLE SONAR_ANALYSIS(PROJECT_ID,ANALYSIS_KEY,DATE,REVISION); CREATE TABLE SONAR_MEASURES(PROJECT_ID,ANALYSIS_KEY,SQALE_INDEX,QUALITY_PROFILES); CREATE TABLE GIT_COMMITS(PROJECT_ID,COMMIT_HASH,COMMITTER_DATE,PARENTS,IN_MAIN_BRANCH);")
        for r, o in zip(*history(n=220)):
            key = o["observation_id"]
            db.execute("INSERT INTO GIT_COMMITS VALUES(?,?,?,?,?)", ("demo", r["commit_sha"], r["committer_timestamp"], r["parents_json"], "True"))
            db.execute("INSERT INTO SONAR_ANALYSIS VALUES(?,?,?,?)", ("demo", key, o["committer_timestamp"], r["commit_sha"]))
            db.execute("INSERT INTO SONAR_MEASURES VALUES(?,?,?,?)", ("demo", key, o["sqale_index_minutes"], '[{"key":"java","language":"java"}]'))
    bundle = tmp_path / "history/run"
    ingest_history(HistoryConfig(str(db_path), str(tmp_path / "history")), bundle)
    config = DatasetConfig(str(bundle), str(tmp_path / "datasets"))
    first = tmp_path / "datasets/a"
    second = tmp_path / "datasets/b"
    report = construct_dataset(config, first)
    assert report["total_examples"] > 0 and report["models_executed"] is False
    assert report["selected_split_gate"] == "BLOCKED"
    construct_dataset(config, second)
    assert verify_bundle(first) == verify_bundle(second)
    for p in first.iterdir():
        assert p.read_bytes() == (second / p.name).read_bytes()
    with (first / "forecasting_dataset.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert {int(r["horizon_days"]) for r in rows} == {30, 60, 90}
    assert all(float(r["actual_minutes"]) - float(r["origin_minutes"]) == float(r["actual_delta_minutes"]) for r in rows)
    with pytest.raises(ValueError):
        construct_dataset(config, first)
    (bundle / "historical_debt.csv").write_text("tampered")
    with pytest.raises(ValueError):
        construct_dataset(config, tmp_path / "datasets/c")
    with pytest.raises(ValueError):
        replace(config, phase=3)


def test_no_model_commands():
    with pytest.raises(SystemExit):
        main(["predict"])


def test_observed_negative_delta_is_not_clamped():
    git, obs = history()
    obs[212]["sqale_index_minutes"] = "0"
    label, reason = RepositoryStates(git, obs).endpoint("2020-07-01T00:00:00Z", 30)
    assert reason is None and label["actual_minutes"] == 0
    assert label["actual_delta_minutes"] == -364
