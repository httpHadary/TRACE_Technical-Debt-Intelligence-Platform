"""Sealed Chronos comparison on original baseline IDs, plus native intervals."""
from collections import defaultdict
import math

import numpy as np

from .baseline_evaluation import evaluate_baselines, mean

CHRONOS = "chronos_small"
MODELS = ("persistence", "rolling_mean", "linear_trend", CHRONOS)
INTERVAL_FIELDS = ("evaluation_phase", "horizon_days", "subset", "repository_id", "attempted", "successes", "failures",
    "repository_clusters", "macro_coverage80", "pooled_coverage80", "macro_width80", "pooled_width80",
    "macro_interval_score80", "macro_pinball_q10", "macro_pinball_q50", "macro_pinball_q90",
    "coverage_ci_low", "coverage_ci_high", "width_ci_low", "width_ci_high",
    "collapsed_intervals", "collapsed_misses", "near_collapsed_intervals", "raw_collapsed_intervals",
    "constant_contexts", "distinct_origin_measurements", "distinct_context_value_sequences", "uncertainty_status")


def compare_points(chronos, baselines, labels):
    expected = {r["forecast_id"] for r in chronos}
    if expected != set(labels) or len(expected) != len(chronos):
        raise ValueError("Chronos/label identities must be unique and complete")
    controls = [r for r in baselines if r["forecast_id"] in expected]
    if len(controls) != len(expected)*3:
        raise ValueError("Original baseline coverage mismatch")
    full = evaluate_baselines(controls+chronos, labels, models=MODELS)
    success = {r["forecast_id"] for r in chronos if r["inference_status"] == "SUCCESS"}
    matched = evaluate_baselines([r for r in controls+chronos if r["forecast_id"] in success],
                                {fid:labels[fid] for fid in success}, models=MODELS) if success else []
    return full, matched


def select_validation_policy(metrics, predictions):
    if any(r["evaluation_phase"] != "validation" for r in metrics+predictions):
        raise ValueError("Only validation may freeze the selection policy")
    selected = {}
    for h in (30,60,90):
        rows = {r["model"]:r for r in metrics if r["horizon_days"] == h and r["subset"] == "all" and r["repository_id"] == "ALL"}
        if set(rows) != set(MODELS):
            raise ValueError("Missing validation comparison")
        best = min(r["macro_mae"] for r in rows.values())
        champion = next(m for m in MODELS if rows[m]["macro_mae"] <= best*1.01)
        selected[str(h)] = {"champion":champion,"validation_macro_mae":{m:r["macro_mae"] for m,r in rows.items()}}
    return {"status":"FROZEN","selection_phase":"validation","horizons":selected,
            "inference_configuration_changed":False,"fine_tuning":False,
            "policy":"minimum_validation_repository_macro_MAE_within_1percent_prefer_persistence_mean_trend_chronos",
            "failure_policy":"explicit_persistence_on_failure_full_assigned_plus_success_matched_report",
            "interval_policy":"native_q10_q90_only_successes_no_recalibration_no_fabricated_fallback_intervals"}


def interval_metrics(predictions, labels):
    groups, repositories = defaultdict(list), defaultdict(set)
    for row in predictions:
        fid = row["forecast_id"]
        if fid not in labels:
            raise ValueError("Missing interval label")
        label = labels[fid]
        if row["inference_status"] == "SUCCESS":
            qs = [row[k] for k in ("q10","prediction_minutes","q90")]
            if not all(math.isfinite(v) for v in qs) or not 0 <= qs[0] <= qs[1] <= qs[2]:
                raise ValueError("Invalid ordered native stock interval")
        phase,h = row["evaluation_phase"],row["horizon_days"]
        repositories[phase,h].add(row["repository_id"])
        subsets = ["all", "unchanged_debt" if label["actual_delta_minutes"] == 0 else "changing_debt",
                   "constant_history" if row["distinct_context_values"] == 1 else "nonconstant_history"]
        for subset in subsets:
            groups[phase,h,subset].append(row)
    result = []
    for (phase,h),repos in sorted(repositories.items()):
        for subset in ("all","unchanged_debt","changing_debt","constant_history","nonconstant_history"):
            candidates = groups[phase,h,subset]
            for repo in ("ALL",*sorted(repos)):
                attempted = candidates if repo == "ALL" else [r for r in candidates if r["repository_id"] == repo]
                rows = [r for r in attempted if r["inference_status"] == "SUCCESS"]
                per_repo = defaultdict(list)
                collapsed = collapsed_misses = near = raw_collapsed = 0
                for row in rows:
                    actual = labels[row["forecast_id"]]["actual_minutes"]
                    low,point,high = row["q10"],row["prediction_minutes"],row["q90"]
                    covered, width = float(low <= actual <= high), high-low
                    score = width + 10*max(low-actual,0) + 10*max(actual-high,0)
                    pinballs = []
                    for q,prediction in ((.1,low),(.5,point),(.9,high)):
                        error = actual-prediction
                        pinballs.append(max(q*error,(q-1)*error))
                    per_repo[row["repository_id"]].append((covered,width,score,*pinballs))
                    collapsed += width == 0
                    collapsed_misses += width == 0 and not covered
                    near += width <= 1e-6*max(1.,row["current_minutes"])
                    raw_collapsed += row["raw_q90"] == row["raw_q10"]
                stats = [np.array(values,dtype=float).mean(axis=0) for _,values in sorted(per_repo.items())]
                macro = np.array(stats).mean(axis=0).tolist() if stats else [None]*6
                bounds = [None]*4
                if repo == "ALL" and len(stats) >= 2:
                    indices = np.random.default_rng(42).integers(0,len(stats),size=(2000,len(stats)))
                    means = np.array(stats)[indices].mean(axis=1)
                    bounds = [float(v) for j in (0,1) for v in np.quantile(means[:,j],[.025,.975],method="linear")]
                status = "NO_SUCCESSFUL_INTERVALS" if not rows else "SINGLE_REPOSITORY_NO_ROW_CI" if len(stats)<2 else (
                    "EXPLORATORY_FEWER_THAN_8_CLUSTERS" if len(stats)<8 else "REPOSITORY_BOOTSTRAP_CONDITIONAL")
                pooled = [value for values in per_repo.values() for value in values]
                result.append(dict(zip(INTERVAL_FIELDS,(phase,h,subset,repo,len(attempted),len(rows),len(attempted)-len(rows),
                    len(stats),macro[0],mean([v[0] for v in pooled]) if rows else None,macro[1],
                    mean([v[1] for v in pooled]) if rows else None,*macro[2:],*bounds,
                    collapsed,collapsed_misses,near,raw_collapsed,sum(r["distinct_context_values"]==1 for r in rows),
                    len({r["origin_observation_id"] for r in rows}),len({r["context_values_digest"] for r in rows}),status))))
    return result


def plot_results(points, intervals, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    index = {(r["evaluation_phase"],r["horizon_days"],r["model"]):r for r in points if r["subset"]=="all" and r["repository_id"]=="ALL"}
    native = {(r["evaluation_phase"],r["horizon_days"]):r for r in intervals if r["subset"]=="all" and r["repository_id"]=="ALL"}
    fig,axes = plt.subplots(2,2,figsize=(12,8),layout="constrained")
    for i,phase in enumerate(("test_temporal","test_repository")):
        for model,color in zip(MODELS,("#2563eb","#dc2626","#059669","#7c3aed")):
            rows = [index[phase,h,model] for h in (30,60,90)]
            axes[i,0].plot((30,60,90),[r["macro_mae"] for r in rows],marker="o",label=model,color=color)
        ax = axes[i,1]
        rows = [native[phase,h] for h in (30,60,90)]
        ax.plot((30,60,90),[r["macro_coverage80"] for r in rows],marker="o",color="#7c3aed",label="Chronos q10–q90")
        ax.fill_between((30,60,90),[r["coverage_ci_low"] for r in rows],[r["coverage_ci_high"] for r in rows],alpha=.15,color="#7c3aed")
        ax.axhline(.8,color="black",linestyle="--",label="Nominal 80%")
        ax.set_ylim(0,1.02);ax.set_ylabel("Repository-macro interval coverage")
        for j in (0,1):
            ax=axes[i,j];ax.set_title(("Temporal test (15 repositories)" if i==0 else "Held-out test (6 repositories; exploratory)")+
                (" — MAE" if j==0 else " — native intervals"))
            ax.set_xlabel("Exact horizon (days)");ax.set_xticks((30,60,90));ax.grid(alpha=.2);ax.legend(fontsize=8)
        axes[i,0].set_ylabel("Repository-macro MAE (estimated debt minutes)");axes[i,0].set_ylim(bottom=0)
    fig.suptitle("TechDebt360 — frozen-cohort Chronos evaluation\nNative interval coverage; 95% repository-bootstrap bands",fontsize=13)
    fig.savefig(output,dpi=160,metadata={"Software":"TechDebt360 Phase 4.2"});plt.close(fig)
