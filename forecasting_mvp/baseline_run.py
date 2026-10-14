"""Phase 3 replay: register -> past-only candidates -> seal -> select -> seal -> score."""
from collections import Counter, defaultdict
import csv
import gzip
import importlib.metadata
import json
import math
from pathlib import Path
import platform

from contracts import digest, read_csv, read_json, write_csv, write_json
from .baselines import CANDIDATES, MODELS, baseline_predict
from .baseline_evaluation import METRIC_FIELDS, evaluate_baselines, plot_comparison, select_parameters
from .contracts import TargetContract, utc_timestamp
from .dataset import FEATURE_FIELDS
from .io import file_sha256, publish_manifest, verify_bundle
from .prediction_input import admit_prediction_input

PHASES = ("train", "validation", "test_temporal", "test_repository")
PREDICTION_FIELDS = ("forecast_id", "context_id", "repository_id", "track", "origin_utc", "horizon_days",
    "endpoint_utc", "evaluation_phase", "model", "window_days", "raw_prediction_minutes", "prediction_minutes",
    "current_minutes", "origin_observation_id", "distinct_context_measurements", "distinct_context_values",
    "context_values_digest")
LABEL_FIELDS = ("forecast_id", "context_id", "repository_id", "track", "horizon_days", "endpoint_utc",
                "endpoint_revision", "endpoint_observation_id", "actual_minutes", "actual_delta_minutes", "evaluation_phase")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def plan_requests(features_path, splits):
    """Routing comes from past features + immutable assignments, never target rows."""
    header, features = read_csv(features_path, required=FEATURE_FIELDS, key="context_id")
    require(tuple(header) == FEATURE_FIELDS, "Strict past feature schema required")
    require(splits["primary_track"] == "core90" and splits["status"] == "PASS", "Phase 3 needs frozen complete primary cohort")
    requests = defaultdict(dict)
    counts = Counter()
    for feature in features:
        if feature["track"] != "core90":
            continue
        for h in (30, 60, 90):
            target = TargetContract(h, context_policy="core90_90_days")
            fid = digest([feature["context_id"], target.target_id])
            phase = splits["assignments"].get(fid)
            if phase not in PHASES:
                continue
            requests[feature["context_id"]][h] = {"forecast_id": fid, "context_id": feature["context_id"],
                "repository_id": feature["repository_id"], "track": "core90", "origin_utc": feature["origin_utc"],
                "horizon_days": h, "endpoint_utc": target.endpoint(feature["origin_utc"]), "evaluation_phase": phase}
            counts[h, phase] += 1
    for h in (30, 60, 90):
        for phase in PHASES:
            require(counts[h, phase] == splits["per_horizon_counts"][str(h)].get(phase, 0) > 0,
                    "Frozen primary cohort is missing requests")
    return dict(requests)


def historical_measurement_times(path):
    """Metadata-only projection: debt values are neither converted nor returned."""
    result = {}
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        require({"observation_id", "historical_timestamp"} <= set(reader.fieldnames or ()), "Historical reference metadata missing")
        for row in reader:
            oid, stamp = row["observation_id"], row["historical_timestamp"]
            require(oid not in result, "Duplicate historical reference")
            utc_timestamp(stamp)
            result[oid] = stamp
    return result


def generate_candidates(context_path, requests, measurement_times):
    """The predictor receives only an admitted request; routing is outside it."""
    candidates, seen = [], set()
    with gzip.open(context_path, "rt", encoding="utf-8") as stream:
        for line in stream:
            context = json.loads(line)
            cid = context["context_id"]
            if cid not in requests:
                continue
            require(cid not in seen, "Duplicate requested context")
            seen.add(cid)
            # Do not pass a complete historical measurement store into the boundary.
            past_times = {ref: measurement_times[ref] for ref in set(context["observation_ids"]) if ref is not None}
            for h, metadata in sorted(requests[cid].items()):
                admitted = admit_prediction_input(context, h, expected_origin_utc=metadata["origin_utc"], measurement_times=past_times)
                require(admitted.repository_id == metadata["repository_id"], "Context routing mismatch")
                for model, window in CANDIDATES:
                    raw, point = baseline_predict(admitted, model, window)
                    candidates.append({**metadata, "model": model, "window_days": window,
                        "raw_prediction_minutes": raw, "prediction_minutes": point, "current_minutes": admitted.values[-1],
                        "origin_observation_id": context["observation_ids"][-1],
                        "distinct_context_measurements": context["distinct_observation_ids"],
                        "distinct_context_values": len({v for v in admitted.values if v is not None}),
                        "context_values_digest": digest(list(admitted.values))})
    require(seen == set(requests), "Requested context missing from archive")
    expected = sum(len(v) for v in requests.values()) * len(CANDIDATES)
    require(len(candidates) == expected, "Incomplete baseline coverage")
    return sorted(candidates, key=lambda r: (r["forecast_id"], r["model"], r["window_days"]))


def label_view(path, expected_ids, *, verify_seal):
    """Gate first; only admit labels for the explicit caller's allowed ID set.

    CSV must be scanned for routing IDs; other rows' actual values are not
    converted, retained or exposed. Selection receives only validation labels.
    """
    verify_seal()
    labels = {}
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == LABEL_FIELDS, "Strict label schema required")
        for row in reader:
            fid = row["forecast_id"]
            if fid not in expected_ids:
                continue
            require(fid not in labels, "Duplicate evaluation label")
            row["horizon_days"] = int(row["horizon_days"])
            for key in ("actual_minutes", "actual_delta_minutes"):
                row[key] = float(row[key])
                require(math.isfinite(row[key]) and (key == "actual_delta_minutes" or row[key] >= 0), "Invalid actual stock/delta")
            labels[fid] = row
    require(set(labels) == expected_ids, "Missing allowed evaluation labels")
    return labels


def check_final_seal(root):
    record = read_json(root / "prediction_seal.json")
    require(record["status"] == "SEALED", "Predictions must be sealed before evaluation")
    for name, expected in record["artifacts"].items():
        require(name in ("baseline_predictions.csv", "selected_parameters.json")
                and file_sha256(root / name) == expected, "Sealed predictions/parameters changed")


def run_baselines(bundle, history_bundle, hardening_bundle, output):
    bundle, history, hardening, output = map(lambda p: Path(p).resolve(), (bundle, history_bundle, hardening_bundle, output))
    require(not output.exists() and all(not output.is_relative_to(p) and not p.is_relative_to(output)
            for p in (bundle, history, hardening)), "New output directory separate from inputs required")
    # Verification hashes label bytes but does NOT load numeric label values.
    frozen, hmanifest, hardened = verify_bundle(bundle), verify_bundle(history), verify_bundle(hardening)
    require(frozen["metadata"].get("phase") == 2 and hmanifest["metadata"].get("phase") == 1
            and hardened["metadata"].get("phase") == "2.1", "Verified Phase 1/2/2.1 inputs required")
    require(len({m["metadata"]["source_sha256"] for m in (frozen, hmanifest, hardened)}) == 1, "Input source mismatch")
    validation = read_json(hardening / "dataset_validation.json")
    splits = read_json(bundle / "forecasting_splits.json")
    require(validation["status"] == "PASS" and validation["raw_sql_all_passed"]
            and validation["raw_sql_sample_count"] >= 100 and validation["frozen_artifact_hashes"] == frozen["artifacts"]
            and validation["structural_checks"]["split_id"] == splits["split_id"], "Hardening evidence does not bind frozen cohort")
    code = {p.name: file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
    input_manifest_hashes = {stage: file_sha256(p / "manifest.json") for stage, p in
                            (("phase1", history), ("phase2", bundle), ("phase2_1", hardening))}
    study = {"study_name": "phase-3-core90-statistical-baselines-v1", "phase": 3, "primary_track": "core90",
        "source_sha256": frozen["metadata"]["source_sha256"], "input_manifest_sha256": input_manifest_hashes,
        "frozen_split_id": splits["split_id"], "frozen_input_hashes": frozen["artifacts"],
        "model_candidates": [{"model": m, "window_days": w} for m, w in CANDIDATES],
        "horizons_days": [30, 60, 90], "trend_policy": "daily_OLS_slope_anchored_at_current",
        "clipping_policy": "max_zero_for_all_models_keep_raw", "seasonal_naive": "DEFERRED_no_registered_seasonality_evidence",
        "selection_metric": "validation_repository_macro_MAE", "parameter_tie_break": "shorter_window",
        "champion_tie_policy": "within_1percent_prefer_persistence_mean_trend",
        "uncertainty": {"method": "paired_equal_weight_repository_bootstrap_percentile", "repetitions": 2000,
                        "seed": 42, "confidence": .95, "small_cluster_caution_threshold": 8},
        "metric": "SQALE_INDEX", "unit": "estimated_maintainability_remediation_minutes",
        "interpretation": "imported_research_archive_not_actual_developer_effort",
        "implementation_sha256": code, "runtime": {"python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"), "matplotlib": importlib.metadata.version("matplotlib")}}
    study_id = digest(study)
    output.mkdir(parents=True)
    write_json(output / "study.json", {"study_id": study_id, **study})
    events = ["study_registered_before_predictions"]
    requests = plan_requests(bundle / "forecasting_features.csv", splits)
    times = historical_measurement_times(history / "historical_debt.csv")
    candidates = generate_candidates(bundle / "forecasting_contexts.jsonl.gz", requests, times)
    del times
    candidate_root = output / "candidates"
    candidate_root.mkdir()
    write_csv(candidate_root / "candidate_predictions.csv", candidates, PREDICTION_FIELDS)
    candidate_seal = publish_manifest(candidate_root, ["candidate_predictions.csv"],
        {"phase": 3, "stage": "all_candidate_predictions_sealed_before_any_labels", "study_id": study_id,
         "forecast_ids": sum(len(v) for v in requests.values()), "prediction_rows": len(candidates)})
    events.append("all_candidate_predictions_sealed_before_any_labels")

    def check_candidates():
        require(verify_bundle(candidate_root) == candidate_seal, "Candidate seal changed")
    val_ids = {r["forecast_id"] for r in candidates if r["evaluation_phase"] == "validation"}
    val_labels = label_view(bundle / "forecasting_labels.csv", val_ids, verify_seal=check_candidates)
    events.append("validation_only_labels_loaded")
    selected = select_parameters(candidates, val_labels)
    del val_labels
    write_json(output / "selected_parameters.json", selected)
    events.append("parameters_and_validation_champions_frozen")
    predictions = [r for r in candidates if r["window_days"] == selected["parameters"][str(r["horizon_days"])][r["model"]]["window_days"]]
    check_candidates()
    write_csv(output / "baseline_predictions.csv", predictions, PREDICTION_FIELDS)
    prediction_seal = {"status": "SEALED", "study_id": study_id, "candidate_manifest_sha256": file_sha256(candidate_root / "manifest.json"),
        "test_labels_loaded": False, "artifacts": {name: file_sha256(output / name) for name in
            ("baseline_predictions.csv", "selected_parameters.json")},
        "forecast_id_digests": {phase: digest(sorted({r["forecast_id"] for r in predictions if r["evaluation_phase"] == phase})) for phase in PHASES}}
    write_json(output / "prediction_seal.json", prediction_seal)
    events.append("selected_predictions_sealed_before_test_labels")
    labels = label_view(bundle / "forecasting_labels.csv", {r["forecast_id"] for r in predictions},
                        verify_seal=lambda: check_final_seal(output))
    events.append("evaluation_labels_loaded_after_prediction_seal")
    metrics = evaluate_baselines(predictions, labels)
    require(all(set(r) == set(METRIC_FIELDS) for r in metrics), "Incomplete metric serialization")
    write_csv(output / "baseline_metrics.csv", metrics, METRIC_FIELDS)
    plot_comparison(metrics, output / "baseline_comparison.png")
    # A small fixed-ID sample per model/horizon/phase; never an evaluation cohort.
    sample = []
    for phase in PHASES:
        for h in (30, 60, 90):
            ids = sorted({r["forecast_id"] for r in predictions if r["evaluation_phase"] == phase and r["horizon_days"] == h})[:3]
            sample.extend(r for r in predictions if r["forecast_id"] in ids)
    write_csv(output / "baseline_predictions_sample.csv", sample, PREDICTION_FIELDS)
    check_final_seal(output)
    require(verify_bundle(bundle) == frozen and verify_bundle(history) == hmanifest and verify_bundle(hardening) == hardened
            and all(file_sha256(p / "manifest.json") == input_manifest_hashes[s] for s, p in
                    (("phase1", history), ("phase2", bundle), ("phase2_1", hardening))), "Frozen inputs changed during replay")
    require(code == {p.name: file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}, "Implementation changed during replay")
    audit = {"status": "PASS", "phase": 3, "study_id": study_id, "events": events,
        "candidate_rows": len(candidates), "selected_prediction_rows": len(predictions),
        "forecast_ids": len(labels), "scored_metric_rows": len(metrics), "model_failures": 0,
        "coverage": "all_frozen_primary_active_IDs_all_three_models", "frozen_inputs_unchanged": True,
        "combined_dataset_parsed_for_predictions": False, "pretrained_models_or_catboost_run": False,
        "phase4_readiness": "PARTIAL_pretrained_runtime_resource_and_provenance_admission_required"}
    write_json(output / "run_audit.json", audit)
    publish_manifest(output, ["study.json", "selected_parameters.json", "prediction_seal.json", "baseline_predictions.csv",
        "baseline_metrics.csv", "baseline_comparison.png", "baseline_predictions_sample.csv", "run_audit.json",
        "candidates/manifest.json", "candidates/candidate_predictions.csv"],
        {"phase": 3, "status": "PASS", "study_id": study_id, "source_sha256": study["source_sha256"]})
    return audit
