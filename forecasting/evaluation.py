"""Shared eligible cohorts, timestamp purging, deterministic M0/M1/M2 evaluation."""
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import timedelta
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score

from contracts import atomic_bytes, digest, read_csv, sha256, write_csv, write_json
from .dataset import KEYS, verify_dataset, package_versions, source_hashes
from .schema import (BASE_FEATURES, GRAPH_FEATURES, assert_available, finite, iso,
                     predictor_names, timestamp)


@dataclass(frozen=True)
class EvaluationConfig:
    first_validation_cutoff: str
    validation_weeks: int = 8
    test_weeks: int = 8
    step_weeks: int = 32
    folds: int = 1
    min_train_rows: int = 20
    precision_k: int = 5
    iterations: int = 200
    depth: int = 4
    seed: int = 42
    min_class_events: int = 2
    holdout_repositories: bool = True

    def __post_init__(self):
        timestamp(self.first_validation_cutoff)
        for key in ("validation_weeks", "test_weeks", "step_weeks", "folds", "min_train_rows", "precision_k",
                    "iterations", "depth", "min_class_events"):
            if getattr(self, key) < 1:
                raise ValueError(f"Positive evaluation setting required: {key}")
        # Prevent overlapping evaluation windows across rolling folds.
        if self.step_weeks < self.validation_weeks + self.test_weeks:
            raise ValueError("Rolling evaluation windows overlap")


def load_rows(path):
    path = Path(path)
    manifest = verify_dataset(path)
    _, states = read_csv(path / "module_weekly_state.csv", required=(*KEYS, *BASE_FEATURES, "max_feature_timestamp"), key="observation_id")
    _, labels = read_csv(path / "module_labels.csv", required=(*KEYS, "target_status", "label_end_timestamp"), key="observation_id")
    _, graphs = read_csv(path / "module_graph_features.csv", required=(*KEYS, *GRAPH_FEATURES, "max_feature_timestamp"), key="observation_id")
    labels, graphs = {r["observation_id"]: r for r in labels}, {r["observation_id"]: r for r in graphs}
    if set(labels) != {r["observation_id"] for r in states}:
        raise ValueError("Labels and origins differ")
    rows = []
    contract = manifest["prediction_contract"]
    for state in states:
        label, graph = labels[state["observation_id"]], graphs[state["observation_id"]]
        if any(state[k] != label[k] or state[k] != graph[k] for k in KEYS):
            raise ValueError("Scientific identity mismatch")
        cutoff = state["prediction_timestamp"]
        assert_available(cutoff, [state["max_feature_timestamp"], graph["max_feature_timestamp"]])
        expected_end = timestamp(cutoff) + timedelta(days=contract["horizon_days"])
        if timestamp(label["label_end_timestamp"]) != expected_end or label["horizon"] != contract["horizon"]:
            raise ValueError("Target horizon mismatch")
        if finite(label["growth_threshold_minutes"]) != contract["growth_threshold_minutes"]:
            raise ValueError("Growth threshold mismatch")
        if label["target_status"] != "OBSERVED":
            if label["debt_delta_minutes"] or label["growth_label"]:
                raise ValueError("Unknown target has fabricated values")
            continue
        target = finite(label["debt_delta_minutes"])
        if target is None or int(label["growth_label"]) != int(target > contract["growth_threshold_minutes"]):
            raise ValueError("Invalid observed target/classification")
        current, future = finite(state["sqale_minutes"]), finite(label["future_sqale_minutes"])
        if current is None or future is None or abs(target - (future - current)) > 1e-8 or label["exclusion_reason"]:
            raise ValueError("Observed target disagrees with debt endpoints")
        decomposition = [finite(label[k]) for k in ("retained_debt_delta_minutes", "added_debt_minutes", "removed_debt_minutes")]
        if any(v is None for v in decomposition) or abs(target - (decomposition[0] + decomposition[1] - decomposition[2])) > 1e-8:
            raise ValueError("Debt membership decomposition disagrees with target")
        row = {**state, **{k: graph[k] for k in GRAPH_FEATURES}, **label}
        for k in BASE_FEATURES + GRAPH_FEATURES:
            row[k] = finite(row[k])
        row["debt_delta_minutes"], row["growth_label"] = target, int(label["growth_label"])
        row["membership_changed_target"] = int(label["membership_changed"])
        # Keep current membership movement as a predictor; future movement stays label-side.
        row["membership_changed"] = finite(state["membership_changed"])
        rows.append(row)
    return manifest, sorted(rows, key=lambda r: (timestamp(r["prediction_timestamp"]), r["repository_id"], r["stable_module_id"]))


def make_folds(rows, config):
    folds = []
    first = timestamp(config.first_validation_cutoff)
    repositories = sorted({r["repository_id"] for r in rows})
    for number in range(config.folds):
        validation_start = first + timedelta(weeks=number * config.step_weeks)
        validation_end = validation_start + timedelta(weeks=config.validation_weeks)
        # Validation labels must mature before the untouched test origin period begins.
        validation = [r for r in rows if validation_start <= timestamp(r["prediction_timestamp"]) < validation_end]
        horizon_days = max((timestamp(r["label_end_timestamp"]) - timestamp(r["prediction_timestamp"])).days for r in rows) if rows else 91
        if config.folds > 1 and config.step_weeks * 7 < (config.validation_weeks + config.test_weeks) * 7 + horizon_days:
            raise ValueError("Rolling validation/test windows overlap across folds")
        test_start = validation_end + timedelta(days=horizon_days)
        test_end = test_start + timedelta(weeks=config.test_weeks)
        variants = [("rolling", None)]
        if config.holdout_repositories and len(repositories) >= 3:
            variants += [("repository_holdout", repo) for repo in repositories]
        for kind, heldout in variants:
            train = [r for r in rows if timestamp(r["prediction_timestamp"]) < validation_start
                     and timestamp(r["label_end_timestamp"]) < validation_start
                     and r["repository_id"] != heldout]
            val = [r for r in validation if heldout is None or r["repository_id"] == heldout]
            test = [r for r in rows if test_start <= timestamp(r["prediction_timestamp"]) < test_end
                    and (heldout is None or r["repository_id"] == heldout)]
            # Holdout validation remains held out; fixed hyperparameters never fit on it.
            fold_id = f"{kind}-{number:02d}" + ("-" + digest(heldout)[:12] if heldout else "")
            folds.append({"fold_id": fold_id, "kind": kind, "heldout_repository": heldout,
                          "validation_start": iso(validation_start), "validation_end": iso(validation_end),
                          "test_start": iso(test_start), "test_end": iso(test_end),
                          "train": train, "validation": val, "test": test})
    return folds


def sample_counts(rows):
    # These counts expose dependence; this is not a statistically estimated effective N.
    by_module = defaultdict(list)
    for row in rows:
        by_module[(row["repository_id"], row["stable_module_id"])].append(row)
    disjoint = 0
    for group in by_module.values():
        last_end = None
        for row in sorted(group, key=lambda r: timestamp(r["prediction_timestamp"])):
            if last_end is None or timestamp(row["prediction_timestamp"]) > last_end:
                disjoint += 1
                last_end = timestamp(row["label_end_timestamp"])
    return {"rows": len(rows), "modules": len(by_module), "repositories": len({r["repository_id"] for r in rows}),
            "repository_snapshot_blocks": len({(r["repository_id"], r["prediction_timestamp"]) for r in rows}),
            "nonoverlapping_module_label_windows": disjoint,
            "growth_events": sum(r["growth_label"] for r in rows),
            "changed_debt_rows": sum(r["debt_delta_minutes"] != 0 for r in rows),
            "effective_independent_sample_size": None,
            "effective_sample_note": "Unknown: rows, blocks and disjoint windows remain correlated"}


def metrics(rows, predictions, probabilities, config):
    y = np.array([r["debt_delta_minutes"] for r in rows], dtype=float)
    growth = np.array([r["growth_label"] for r in rows], dtype=int)
    error = np.abs(y - np.asarray(predictions))
    changed = y != 0
    unchanged_membership = np.array([r["membership_changed_target"] == 0 for r in rows])
    persistence = float(np.mean(np.abs(y)))
    positives = int(growth.sum())
    class_ok = positives >= config.min_class_events and len(rows) - positives >= config.min_class_events
    buckets = defaultdict(list)
    for index, row in enumerate(rows):
        buckets[(row["repository_id"], row["prediction_timestamp"])].append(index)
    precision_values = []
    if class_ok:
        for indices in buckets.values():
            ranked = sorted(indices, key=lambda i: (-float(probabilities[i]), rows[i]["observation_id"]))
            selected = ranked[:config.precision_k]
            precision_values.append(float(np.mean(growth[selected])))
    return {**sample_counts(rows), "mae": float(error.mean()), "rmse": float(np.sqrt(np.mean(error ** 2))),
            "mae_improvement_over_persistence": persistence - float(error.mean()),
            "relative_mae_improvement": (persistence - float(error.mean())) / persistence if persistence else None,
            "changed_debt_mae": float(error[changed].mean()) if changed.any() else None,
            "unchanged_membership_mae": float(error[unchanged_membership].mean()) if unchanged_membership.any() else None,
            "growth_pr_auc_average_precision": float(average_precision_score(growth, probabilities)) if class_ok else None,
            "precision_at_k": float(np.mean(precision_values)) if precision_values else None,
            "precision_k": config.precision_k, "precision_eligible_snapshot_blocks": len(precision_values),
            "classification_metric_status": "OBSERVED" if class_ok else "INSUFFICIENT_POSITIVE_OR_NEGATIVE_LABELS",
            "by_module_strategy": {strategy: {"rows": len([r for r in rows if r["module_strategy"] == strategy]),
                "mae": float(np.mean([error[i] for i, r in enumerate(rows) if r["module_strategy"] == strategy]))}
                for strategy in sorted({r["module_strategy"] for r in rows})}}


def feature_matrix(rows, names):
    if not set(names) <= set(BASE_FEATURES + GRAPH_FEATURES):
        raise ValueError("Predictor outside explicit allowlist")
    return np.array([[np.nan if r[k] is None else finite(r[k]) for k in names] for r in rows], dtype=float)


def train_models(train, config, directory):
    from catboost import CatBoostClassifier, CatBoostRegressor
    targets = np.array([r["debt_delta_minutes"] for r in train], dtype=float)
    classes = np.array([r["growth_label"] for r in train], dtype=int)
    parameters = dict(iterations=config.iterations, depth=config.depth, learning_rate=0.05,
                      random_seed=config.seed, thread_count=1, task_type="CPU", has_time=True,
                      verbose=False, allow_writing_files=False)
    models = {}
    directory.mkdir(parents=True)
    for name in ("M1", "M2"):
        features = predictor_names(name)
        matrix = feature_matrix(train, features)
        # Constant feature populations cannot support learning. Export an explicit
        # constant-training fallback, never pretend CatBoost learned structure.
        informative = any(len(set(col[np.isfinite(col)])) > 1 for col in matrix.T)
        if len(set(targets)) > 1 and informative:
            reg = CatBoostRegressor(loss_function="MAE", **parameters)
            reg.fit(matrix, targets)
            reg.save_model(str(directory / f"{name}_regressor.cbm"))
        else:
            reg = float(np.median(targets))
        if len(set(classes)) == 2 and informative:
            classifier = CatBoostClassifier(loss_function="Logloss", **parameters)
            classifier.fit(matrix, classes)
            classifier.save_model(str(directory / f"{name}_classifier.cbm"))
        else:
            classifier = float(classes.mean())
        models[name] = (reg, classifier)
        write_json(directory / f"{name}_model.json", {"features": list(features), "parameters": parameters,
            "regressor_status": "CATBOOST" if not isinstance(reg, float) else "CONSTANT_TRAINING_FALLBACK",
            "regressor_constant": reg if isinstance(reg, float) else None,
            "classifier_status": "CATBOOST" if not isinstance(classifier, float) else "TRAINING_PREVALENCE_FALLBACK",
            "classifier_constant": classifier if isinstance(classifier, float) else None})
    return models


def evaluate_dataset(dataset, output, config):
    manifest, rows = load_rows(dataset)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    experiment = {"status": "RUNNING", "data_version": manifest["data_version"], "data_kind": manifest["data_kind"],
                  "configuration": asdict(config), "environment": package_versions(), "implementation": source_hashes(),
                  "claim": "SOFTWARE_VALIDATION_ONLY" if manifest["data_kind"] == "synthetic" else "EMPIRICAL_EVALUATION; NOT AUTOMATIC MODEL APPROVAL"}
    write_json(output / "experiment_manifest.json", experiment)
    comparisons, predictions, fold_records = [], [], []
    try:
        for fold in make_folds(rows, config):
            counts = {phase: sample_counts(fold[phase]) for phase in ("train", "validation", "test")}
            record = {k: v for k, v in fold.items() if k not in ("train", "validation", "test")}
            record["counts"] = counts
            record["observation_ids"] = {p: [r["observation_id"] for r in fold[p]] for p in counts}
            if len(fold["train"]) < config.min_train_rows or not fold["validation"] or not fold["test"]:
                record.update(status="INSUFFICIENT_DATA", reason="Need purged training, validation and test observations")
                fold_records.append(record)
                continue
            models = train_models(fold["train"], config, output / "models" / fold["fold_id"])
            record["status"] = "EVALUATED"
            fold_records.append(record)
            for phase in ("validation", "test"):
                cohort = fold[phase]
                for model in ("M0", "M1", "M2"):
                    if model == "M0":
                        delta, probability = np.zeros(len(cohort)), np.zeros(len(cohort))
                    else:
                        reg, cls = models[model]
                        matrix = feature_matrix(cohort, predictor_names(model))
                        delta = np.full(len(cohort), reg) if isinstance(reg, float) else reg.predict(matrix)
                        probability = np.full(len(cohort), cls) if isinstance(cls, float) else cls.predict_proba(matrix)[:, 1]
                    comparisons.append({"fold_id": fold["fold_id"], "model": model, "period": phase,
                                        **metrics(cohort, delta, probability, config)})
                    predictions.extend({**{k: r[k] for k in KEYS}, "fold_id": fold["fold_id"], "period": phase,
                        "model": model, "label_end_timestamp": r["label_end_timestamp"],
                        "actual_debt_delta_minutes": r["debt_delta_minutes"], "predicted_debt_delta_minutes": float(d),
                        "actual_growth": r["growth_label"], "predicted_growth_probability": float(p),
                        "membership_changed_target": r["membership_changed_target"]}
                        for r, d, p in zip(cohort, delta, probability))
        write_json(output / "folds.json", fold_records)
        write_json(output / "model_comparison.json", comparisons)
        fields = (*KEYS, "fold_id", "period", "model", "label_end_timestamp", "actual_debt_delta_minutes",
                  "predicted_debt_delta_minutes", "actual_growth", "predicted_growth_probability", "membership_changed_target")
        write_csv(output / "predictions.csv", predictions, fields)
        lines = ["# M0–M2 comparison", "", experiment["claim"], "",
                 "Fixed parameters; validation/test never used to fit models. M0 growth probability is zero.", "",
                 "| Fold | Period | Model | N | MAE | RMSE | MAE gain vs M0 |", "|---|---|---|---:|---:|---:|---:|"]
        lines += [f"| {r['fold_id']} | {r['period']} | {r['model']} | {r['rows']} | {r['mae']:.4f} | {r['rmse']:.4f} | {r['mae_improvement_over_persistence']:.4f} |" for r in comparisons]
        if not comparisons:
            lines += ["", "No eligible evaluation folds. No predictive accuracy claim is available."]
        atomic_bytes(output / "MODEL_COMPARISON.md", ("\n".join(lines) + "\n").encode())
        experiment.update(status="COMPLETE" if comparisons else "INSUFFICIENT_DATA",
                          eligible_counts=sample_counts(rows),
                          repository_holdout_status="ENABLED" if len({r["repository_id"] for r in rows}) >= 3 and config.holdout_repositories else "NOT_ENOUGH_REPOSITORIES_OR_DISABLED",
                          outputs={str(p.relative_to(output)): sha256(p) for p in sorted(output.rglob("*"))
                                   if p.is_file() and p.name != "experiment_manifest.json"})
        write_json(output / "experiment_manifest.json", experiment)
        return experiment
    except BaseException as exc:
        experiment.update(status="FAILED", reason=f"{type(exc).__name__}: {exc}")
        write_json(output / "experiment_manifest.json", experiment)
        raise
