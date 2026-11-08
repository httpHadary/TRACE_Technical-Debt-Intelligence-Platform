"""Frozen-cohort, raw-SQL and past-only boundary tests; no model execution."""
from copy import deepcopy
from datetime import timedelta
import gzip
import json
import sqlite3

import pytest

from contracts import digest, write_csv, write_json
from forecasting_mvp.contracts import TargetContract, utc_iso, utc_timestamp
from forecasting_mvp.dataset import FIELDS, FEATURE_FIELDS
from forecasting_mvp.hardening import (RawSQLHistory, audit_dataset,
                                      raw_profile, stratified_sample, validate_frozen)
from forecasting_mvp.io import file_sha256, publish_manifest, verify_bundle
from forecasting_mvp.prediction_input import admit_prediction_input
from forecasting_mvp.splits import build_splits
from forecasting_mvp.targets import context_features
from forecasting_mvp.cli import main


def make_context(repo="repo", origin="2010-01-04T00:00:00Z", ref="past", track="core90"):
    length = {"core90": 90, "masked90": 90, "ttm60": 180, "ttm90": 512}[track]
    start = utc_timestamp(origin) - timedelta(days=length - 1)
    context = {"origin_utc": origin, "context_start_utc": utc_iso(start), "context_days": length,
               "timestamps": [utc_iso(start + timedelta(days=i)) for i in range(length)],
               "values": [0.0] * length, "observation_ids": [ref] * length,
               "known_fraction": 1.0, "missing_count": 0, "distinct_observation_ids": 1,
               "missing_reasons": [None] * length, "profile_hash": "profile", "metadata_segment": 1,
               "max_feature_utc": origin}
    return {"context_id": digest([repo, track, context]), "repository_id": repo, "track": track, **context}


def resign(context):
    content = {k: v for k, v in context.items() if k not in ("context_id", "repository_id", "track")}
    context["context_id"] = digest([context["repository_id"], context["track"], content])
    return context


def admit(context, horizon=30, times=None):
    return admit_prediction_input(context, horizon, expected_origin_utc="2010-01-04T00:00:00Z",
                                  measurement_times=times or {"past": "2008-01-01T00:00:00Z"})


@pytest.mark.parametrize("key", ["actual_minutes", "actual_delta_minutes", "endpoint_utc", "endpoint_revision",
    "endpoint_observation_id", "evaluation_phase", "target_id", "forecast_id", "labels", "future_measurements"])
def test_reject_any_target_label_or_future_store(key):
    context = make_context()
    context[key] = "forbidden"
    with pytest.raises(ValueError, match="allowlisted"):
        admit(context)


def test_reject_full_dataset_projection_and_wrong_external_cutoff():
    with pytest.raises(ValueError, match="allowlisted"):
        admit({k: "bad" for k in FIELDS})
    context = make_context(origin="2010-01-11T00:00:00Z")
    with pytest.raises(ValueError, match="cutoff"):
        admit(context)


def test_future_measurements_and_wrong_grid_rejected():
    context = make_context()
    with pytest.raises(ValueError, match="Future measurement"):
        admit(context, times={"past": "2010-01-05T00:00:00Z"})
    context["timestamps"][-1] = "2010-01-05T00:00:00Z"
    with pytest.raises(ValueError, match="Past-only"):
        admit(resign(context))
    context = make_context()
    context["observation_ids"][0] = "unknown"
    with pytest.raises(ValueError, match="provenance"):
        admit(resign(context))


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True])
def test_invalid_observed_values_rejected(value):
    context = make_context()
    context["values"][0] = value
    with pytest.raises(ValueError, match="nonnegative"):
        admit(context)


def test_immutable_payload_is_independent_of_future_store_and_label_mutation():
    context = make_context()
    request = admit(context)
    original = request.model_payload()
    context["values"][-1] = 999
    payload = request.model_payload()
    payload["past_values"][-1] = 123
    assert request.model_payload() == original
    assert set(original) == {"horizon_days", "timestamps", "past_values"}
    with pytest.raises(AttributeError):
        request.values = (999,)
    context = make_context()
    extra = {"past": "2008-01-01T00:00:00Z", "unused-future": "2099-01-01T00:00:00Z"}
    assert admit(context, times=extra).model_payload() == original


def test_masks_and_identity_are_checked():
    context = make_context(track="masked90")
    context["values"][0] = context["observation_ids"][0] = None
    context["missing_reasons"][0] = "UNMEASURED_SELECTED_REVISION"
    context["missing_count"], context["known_fraction"] = 1, 89 / 90
    context = resign(context)
    assert admit(context).values[0] is None
    context["missing_count"] = 0
    with pytest.raises(ValueError, match="summary"):
        admit(context)
    context = make_context()
    context["context_id"] = "tampered"
    with pytest.raises(ValueError, match="identity"):
        admit(context)
    with pytest.raises(ValueError):
        admit(make_context(), 91)


def frozen_fixture(tmp_path):
    """Small realistic serialized bundle, reused scans, archived coverage, 8 repos."""
    db_path, bundle = tmp_path / "source.db", tmp_path / "frozen"
    bundle.mkdir()
    with sqlite3.connect(db_path) as db:
        db.executescript("CREATE TABLE GIT_COMMITS(PROJECT_ID,COMMIT_HASH,COMMITTER_DATE,PARENTS,IN_MAIN_BRANCH);"
                         "CREATE TABLE SONAR_ANALYSIS(PROJECT_ID,ANALYSIS_KEY,DATE,REVISION);"
                         "CREATE TABLE SONAR_MEASURES(PROJECT_ID,ANALYSIS_KEY,SQALE_INDEX,QUALITY_PROFILES);")
        for repo in range(8):
            project = f"project-{repo}"
            db.execute("INSERT INTO GIT_COMMITS VALUES(?,?,?,?,?)", (project, "a"*40, "2008-01-01T00:00:00Z", "[]", "True"))
            db.execute("INSERT INTO GIT_COMMITS VALUES(?,?,?,?,?)", (project, "b"*40, "2020-01-01T00:00:00Z", repr(["a"*40]), "True"))
            db.execute("INSERT INTO SONAR_ANALYSIS VALUES(?,?,?,?)", (project, "analysis", "2008-01-01 00:00:00", "a"*40))
            db.execute("INSERT INTO SONAR_MEASURES VALUES(?,?,?,?)", (project, "analysis", 0, '[{"key":"java";"language":"java"}]'))
    source_hash = file_sha256(db_path)
    contexts, rows, features = [], [], []
    for repo in range(8):
        project = f"project-{repo}"
        rid = "v2-" + digest(project)[:24]
        ref = digest([source_hash, project, "analysis", "a"*40])
        for day in range(0, 701, 7):
            origin = utc_iso(utc_timestamp("2010-01-04T00:00:00Z") + timedelta(days=day))
            context = make_context(rid, origin, ref)
            context["profile_hash"] = raw_profile('[{"key":"java";"language":"java"}]')
            resign(context)
            contexts.append(context)
            summary = context_features(context)
            features.append({"context_id": context["context_id"], "repository_id": rid, "track": "core90", "origin_utc": origin,
                             **summary, "availability_flags_json": json.dumps({k: v is not None for k, v in summary.items()
                                                                              if k != "max_feature_utc"})})
            for h in (30, 60, 90):
                target = TargetContract(h, context_policy="core90_90_days")
                rows.append({"forecast_id": digest([context["context_id"], target.target_id]), "context_id": context["context_id"],
                    "repository_id": rid, "source_project_id": project, "track": "core90", "context_days": 90,
                    "origin_utc": origin, "origin_revision": "a"*40, "origin_observation_id": ref, "origin_minutes": 0.0,
                    "profile_hash": context["profile_hash"], "horizon_days": h, "target_id": target.target_id,
                    "endpoint_utc": target.endpoint(origin), "endpoint_revision": "a"*40, "endpoint_observation_id": ref,
                    "endpoint_state_kind": "UNCHANGED_VERIFIED_STATE", "actual_minutes": 0.0, "actual_delta_minutes": 0.0,
                    "known_fraction": 1.0, "missing_count": 0, "distinct_observation_ids": 1,
                    "provenance_status": "IMPORTED_METADATA_APPROXIMATION"})
    splits = build_splits(rows, "core90", "test-study")
    for row in rows:
        row["evaluation_phase"] = splits["assignments"][row["forecast_id"]]
    write_csv(bundle / "forecasting_dataset.csv", rows, FIELDS)
    write_csv(bundle / "forecasting_features.csv", features, FEATURE_FIELDS)
    label_fields = ("forecast_id", "context_id", "actual_minutes", "actual_delta_minutes", "evaluation_phase")
    write_csv(bundle / "forecasting_labels.csv", [{k: r[k] for k in label_fields} for r in rows], label_fields)
    write_json(bundle / "forecasting_splits.json", splits)
    with gzip.open(bundle / "forecasting_contexts.jsonl.gz", "wt") as stream:
        for context in contexts:
            stream.write(json.dumps(context) + "\n")
    publish_manifest(bundle, [p.name for p in bundle.iterdir()], {"phase": 2, "source_sha256": source_hash})
    return db_path, bundle, rows, splits, contexts


def test_frozen_validation_stratification_and_diagnostics(tmp_path):
    db_path, bundle, rows, splits, contexts = frozen_fixture(tmp_path)
    assert validate_frozen(rows, splits, "test-study")["status"] == "PASS"
    sample = stratified_sample(rows)
    assert len(sample) >= 100 and sample == stratified_sample(list(reversed(rows)))
    assert {r["repository_id"] for r in sample} == {r["repository_id"] for r in rows}
    altered = deepcopy(rows)
    altered[0]["endpoint_utc"] = "2010-04-05T00:00:00Z"
    with pytest.raises(ValueError, match="exact"):
        validate_frozen(altered, splits, "test-study")
    altered = deepcopy(rows)
    altered[1]["forecast_id"] = altered[0]["forecast_id"]
    with pytest.raises(ValueError, match="Duplicate"):
        validate_frozen(altered, splits, "test-study")
    altered_splits = deepcopy(splits)
    altered_splits["boundaries"]["test_start"] = altered_splits["boundaries"]["validation_end"]
    with pytest.raises(ValueError, match="Frozen split"):
        validate_frozen(rows, altered_splits, "test-study")
    original = verify_bundle(bundle)
    result = audit_dataset(bundle, db_path, tmp_path / "audit1", study_id="test-study")
    assert result["status"] == "PASS" and result["raw_sql_sample_count"] >= 100
    assert result["raw_sql_all_passed"] and result["models_executed"] is False
    audit_dataset(bundle, db_path, tmp_path / "audit2", study_id="test-study")
    for artifact in (tmp_path / "audit1").iterdir():
        assert artifact.read_bytes() == (tmp_path / "audit2" / artifact.name).read_bytes()
    assert verify_bundle(bundle) == original
    quality = json.loads((tmp_path / "audit1/dataset_quality.json").read_text())
    metrics = quality["per_track_horizon_split"]["core90:30:train"]
    assert metrics["zero_delta_fraction"] == 1 and metrics["distinct_context_measurements"] < metrics["daily_context_slots"]
    assert all(p["overlapping_label_window_pairs"] == 0 for p in quality["cross_split_reuse"]["core90:90"].values())
    with pytest.raises(ValueError, match="New separate"):
        audit_dataset(bundle, db_path, bundle / "nested", study_id="test-study")


def test_raw_oracle_rejects_fabrication_unmeasured_changes_and_bad_ancestry(tmp_path):
    db, bundle, rows, _, contexts = frozen_fixture(tmp_path)
    raw = RawSQLHistory(db, file_sha256(db), {r["source_project_id"] for r in rows})
    row = deepcopy(rows[0])
    row["actual_minutes"] = 42
    with pytest.raises(ValueError, match="Raw SQALE"):
        raw.validate_example(row, contexts[0])
    row = deepcopy(rows[0])
    raw.measurements[row["source_project_id"]].clear()
    with pytest.raises(ValueError, match="Unmeasured"):
        raw.validate_example(row, contexts[0])
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE GIT_COMMITS SET PARENTS=? WHERE PROJECT_ID='project-0' AND COMMIT_HASH=?", (repr(["c"*40]), "b"*40))
    with pytest.raises(ValueError, match="Unresolved|ambiguous"):
        RawSQLHistory(db, file_sha256(db), {"project-0"})


@pytest.mark.parametrize("track,horizon", [("core90", 90), ("masked90", 60), ("ttm60", 60), ("ttm90", 90)])
def test_registered_context_shapes_and_past_only_store_access(track, horizon):
    class PastOnlyLookup(dict):
        def __getitem__(self, key):
            assert key == "past", "Prediction attempted access to an unreferenced measurement"
            return super().__getitem__(key)
    context = make_context(track=track)
    request = admit(context, horizon, PastOnlyLookup(past="2000-01-01T00:00:00Z"))
    assert len(request.values) == context["context_days"]
    assert all(utc_timestamp(t) <= utc_timestamp(request.origin_utc) for t in request.timestamps)


def test_frozen_holdout_assignment_tampering_and_semantic_duplicates(tmp_path):
    _, _, rows, splits, _ = frozen_fixture(tmp_path)
    held = next(r for r in rows if r["evaluation_phase"] == "test_repository")
    modified_rows, modified_splits = deepcopy(rows), deepcopy(splits)
    for row in modified_rows:
        if row["forecast_id"] == held["forecast_id"]:
            row["evaluation_phase"] = "train"
    modified_splits["assignments"][held["forecast_id"]] = "train"
    with pytest.raises(ValueError, match="Frozen split"):
        validate_frozen(modified_rows, modified_splits, "test-study")
    duplicate = deepcopy(rows[0])
    duplicate["forecast_id"] = "different-id-same-forecast"
    with pytest.raises(ValueError, match="semantic"):
        validate_frozen(rows + [duplicate], splits, "test-study")


def test_stratification_covers_rare_delta_and_state_groups():
    rows = []
    for i in range(120):
        rows.append({"forecast_id": digest(i), "repository_id": f"r{i%3}", "horizon_days": (30,60,90)[i%3],
                     "track": "core90", "evaluation_phase": ("train", "validation", "test_temporal", "test_repository")[i%4],
                     "endpoint_state_kind": "UNCHANGED_VERIFIED_STATE" if i < 10 else "MEASURED_CHANGED_STATE",
                     "actual_delta_minutes": -1 if i == 119 else 0 if i < 20 else 1,
                     "actual_minutes": 0 if i == 119 else 1,
                     "origin_utc": utc_iso(utc_timestamp("2010-01-04T00:00:00Z") + timedelta(days=i*7)),
                     "missing_count": 1 if i == 119 else 0, "distinct_observation_ids": 1 if i == 119 else 10})
    chosen = stratified_sample(rows)
    assert len(chosen) >= 100 and chosen == stratified_sample(list(reversed(rows)))
    assert rows[-1] in chosen


def test_raw_profile_quoted_semicolons_and_invalid_metadata():
    assert raw_profile('[{"key":"java";"language":"java";"name":"x; y"}]') == digest([{"key":"java", "language":"java", "name":"x; y"}])
    assert raw_profile("invalid") is None
    assert raw_profile('[{"key":"a","language":"java"},{"key":"b","language":"java"}]') is None


def test_reject_label_columns_in_model_facing_feature_artifact(tmp_path):
    from contracts import read_csv
    _, bundle, _, _, _ = frozen_fixture(tmp_path)
    manifest = verify_bundle(bundle)
    fields, rows = read_csv(bundle / "forecasting_features.csv")
    for row in rows:
        row["actual_minutes"] = "leaked-label"
    write_csv(bundle / "forecasting_features.csv", rows, fields + ["actual_minutes"])
    # This is an explicitly tampered synthetic fixture, never the real frozen bundle.
    (bundle / "manifest.json").unlink()
    publish_manifest(bundle, list(manifest["artifacts"]), manifest["metadata"])
    with pytest.raises(ValueError, match="model-facing feature fields"):
        audit_dataset(bundle, tmp_path / "source.db", tmp_path / "rejected", study_id="test-study")
    assert not (tmp_path / "rejected").exists()


def test_prediction_command_remains_unavailable():
    with pytest.raises(SystemExit):
        main(["predict"])
