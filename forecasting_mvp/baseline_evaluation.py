"""Paired baseline evaluation; only called after predictions are checksummed."""
from collections import defaultdict
import math

import numpy as np

from .baselines import CANDIDATES, MODELS

METRIC_FIELDS = ("evaluation_phase", "horizon_days", "subset", "repository_id", "model", "window_days",
    "n", "repository_clusters", "macro_mae", "macro_rmse", "pooled_mae", "pooled_rmse",
    "persistence_macro_mae", "macro_mae_gain_minutes", "macro_mae_gain_fraction",
    "macro_mae_ci_low", "macro_mae_ci_high", "macro_rmse_ci_low", "macro_rmse_ci_high",
    "paired_mae_gain_ci_low", "paired_mae_gain_ci_high", "uncertainty_status",
    "distinct_origin_measurements", "distinct_endpoint_measurements", "distinct_context_value_sequences",
    "context_measurements_min", "context_measurements_median", "context_measurements_max", "clipped_predictions")


def mean(values):
    return sum(values) / len(values)


def macro_mae(predictions, labels):
    errors = defaultdict(list)
    for row in predictions:
        errors[row["repository_id"]].append(abs(row["prediction_minutes"] - labels[row["forecast_id"]]["actual_minutes"]))
    if not errors:
        raise ValueError("No validation examples")
    return mean([mean(v) for v in errors.values()])


def select_parameters(candidates, validation_labels):
    """Labels must be exactly the validation IDs; never test-informed selection."""
    validation = [r for r in candidates if r["evaluation_phase"] == "validation"]
    if set(validation_labels) != {r["forecast_id"] for r in validation}:
        raise ValueError("Validation-only label view required")
    if any(r["evaluation_phase"] != "validation" for r in validation_labels.values()):
        raise ValueError("Test/training labels forbidden in parameter selection")
    selection, scores, champions = {}, {}, {}
    for h in (30, 60, 90):
        selection[str(h)], scores[str(h)] = {}, {}
        for model in MODELS:
            options = []
            for name, window in CANDIDATES:
                if name != model:
                    continue
                rows = [r for r in validation if r["horizon_days"] == h and r["model"] == model and r["window_days"] == window]
                score = macro_mae(rows, validation_labels)
                options.append((score, window))
                scores[str(h)][f"{model}:{window}"] = score
            score, window = min(options)  # exact ties favor the shorter registered window
            selection[str(h)][model] = {"window_days": window, "validation_macro_mae": score}
        best = min(s["validation_macro_mae"] for s in selection[str(h)].values())
        champions[str(h)] = next(m for m in MODELS if selection[str(h)][m]["validation_macro_mae"] <= 1.01 * best)
    return {"status": "FROZEN", "selection_phase": "validation", "parameters": selection,
            "validation_scores": scores, "champions": champions,
            "parameter_policy": "minimum_validation_repository_macro_mae_then_shorter_window",
            "champion_policy": "within_one_percent_prefer_persistence_then_mean_then_trend",
            "validation_forecast_ids": sorted(validation_labels)}


def cluster_intervals(repo_stats, persistence_stats, repetitions=2000, seed=42):
    """Paired repository bootstrap, equal repository weighting. No row bootstrap."""
    repos = sorted(repo_stats)
    if len(repos) < 2:
        return [None] * 6
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(repos), size=(repetitions, len(repos)))
    mae = np.array([repo_stats[r][0] for r in repos])
    rmse = np.array([repo_stats[r][1] for r in repos])
    base = np.array([persistence_stats[r][0] for r in repos])
    bounds = []
    for values in (mae, rmse, base - mae):
        bounds.extend(float(v) for v in np.quantile(values[indices].mean(axis=1), [.025, .975], method="linear"))
    return bounds


def evaluate_baselines(predictions, labels, repetitions=2000, seed=42):
    identity = [(r["forecast_id"], r["model"]) for r in predictions]
    if len(set(identity)) != len(identity) or set(labels) != {r["forecast_id"] for r in predictions}:
        raise ValueError("Duplicate/mismatched prediction and label cohorts")
    paired = defaultdict(dict)
    for r in predictions:
        if not math.isfinite(r["prediction_minutes"]) or r["prediction_minutes"] < 0:
            raise ValueError("Invalid predicted stock")
        label = labels[r["forecast_id"]]
        for key in ("context_id", "repository_id", "horizon_days", "endpoint_utc", "evaluation_phase"):
            if str(r[key]) != str(label[key]):
                raise ValueError("Prediction/label identity mismatch")
        if label["actual_minutes"] - r["current_minutes"] != label["actual_delta_minutes"]:
            raise ValueError("Actual signed delta mismatch")
        paired[r["forecast_id"]][r["model"]] = r
    if any(set(v) != set(MODELS) for v in paired.values()):
        raise ValueError("Every model must score identical forecast IDs")
    groups = defaultdict(list)
    repositories = defaultdict(set)
    for r in predictions:
        label = labels[r["forecast_id"]]
        phase, h = r["evaluation_phase"], r["horizon_days"]
        repositories[phase, h].add(r["repository_id"])
        kind = "unchanged_debt" if label["actual_delta_minutes"] == 0 else "changing_debt"
        for subset in ("all", kind):
            groups[phase, h, subset, r["model"]].append(r)
    metrics = []
    for (phase, h), repos in sorted(repositories.items()):
        for subset in ("all", "unchanged_debt", "changing_debt"):
            baseline = groups[phase, h, subset, "persistence"]
            base_errors = defaultdict(list)
            for r in baseline:
                base_errors[r["repository_id"]].append(r["prediction_minutes"] - labels[r["forecast_id"]]["actual_minutes"])
            base_stats = {repo: (mean([abs(e) for e in es]), math.sqrt(mean([e*e for e in es]))) for repo, es in base_errors.items()}
            for model in MODELS:
                selected = groups[phase, h, subset, model]
                for repository in ("ALL", *sorted(repos)):
                    rows = selected if repository == "ALL" else [r for r in selected if r["repository_id"] == repository]
                    errors = defaultdict(list)
                    for r in rows:
                        errors[r["repository_id"]].append(r["prediction_minutes"] - labels[r["forecast_id"]]["actual_minutes"])
                    stats = {repo: (mean([abs(e) for e in es]), math.sqrt(mean([e*e for e in es]))) for repo, es in errors.items()}
                    all_errors = [e for es in errors.values() for e in es]
                    mae = mean([s[0] for s in stats.values()]) if stats else None
                    rmse = mean([s[1] for s in stats.values()]) if stats else None
                    pmae = mean([base_stats[repo][0] for repo in stats]) if stats else None
                    gain = pmae - mae if stats else None
                    ci = cluster_intervals(stats, base_stats, repetitions, seed) if repository == "ALL" and stats else [None]*6
                    diversity = sorted(r["distinct_context_measurements"] for r in rows)
                    status = "NO_EXAMPLES" if not rows else "SINGLE_REPOSITORY_NO_ROW_CI" if len(stats) < 2 else (
                        "EXPLORATORY_FEWER_THAN_8_CLUSTERS" if len(stats) < 8 else "REPOSITORY_BOOTSTRAP_CONDITIONAL")
                    metrics.append(dict(zip(METRIC_FIELDS, (phase, h, subset, repository, model,
                        selected[0]["window_days"] if selected else None, len(rows), len(stats), mae, rmse,
                        mean([abs(e) for e in all_errors]) if rows else None,
                        math.sqrt(mean([e*e for e in all_errors])) if rows else None,
                        pmae, gain, gain / pmae if pmae else None, *ci, status,
                        len({r["origin_observation_id"] for r in rows}),
                        len({labels[r["forecast_id"]]["endpoint_observation_id"] for r in rows}),
                        len({r["context_values_digest"] for r in rows}),
                        diversity[0] if rows else None, diversity[len(rows)//2] if rows else None,
                        diversity[-1] if rows else None, sum(r["raw_prediction_minutes"] < 0 for r in rows)))))
    return metrics


def plot_comparison(metrics, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    indexed = {(r["evaluation_phase"], r["horizon_days"], r["model"]): r for r in metrics
               if r["repository_id"] == "ALL" and r["subset"] == "all"}
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    for row_i, phase in enumerate(("test_temporal", "test_repository")):
        for col_i, statistic in enumerate(("mae", "rmse")):
            ax = axes[row_i, col_i]
            for model, color in zip(MODELS, ("#2563eb", "#dc2626", "#059669")):
                points = [indexed[phase, h, model] for h in (30, 60, 90)]
                y = [p[f"macro_{statistic}"] for p in points]
                lower = [p[f"macro_{statistic}_ci_low"] for p in points]
                upper = [p[f"macro_{statistic}_ci_high"] for p in points]
                ax.plot((30, 60, 90), y, marker="o", color=color, label=model.replace("_", " "))
                ax.fill_between((30, 60, 90), lower, upper, color=color, alpha=.12)
            ax.set_title(("Familiar-repository temporal test" if row_i == 0 else "Held-out repository test") + f" — {statistic.upper()}")
            ax.set_xlabel("Exact forecast horizon (days)")
            ax.set_ylabel("Repository-macro error (estimated debt minutes)")
            ax.set_xticks((30, 60, 90))
            ax.set_ylim(bottom=0)
            ax.grid(alpha=.2)
            ax.legend(fontsize=9)
    fig.suptitle("TechDebt360: real statistical baseline results\n95% paired repository-bootstrap bands; held-out bounds are exploratory (6 clusters)", fontsize=13)
    fig.savefig(output, dpi=160, metadata={"Software": "TechDebt360 Phase 3"})
    plt.close(fig)
