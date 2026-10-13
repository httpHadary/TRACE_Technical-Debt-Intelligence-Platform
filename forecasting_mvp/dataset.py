"""Phase 2 exact targets, past-only projections and data-only feasibility gates."""
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import timedelta
import json
import gzip
from pathlib import Path

from contracts import digest, read_csv, read_json, write_csv, write_json
from .io import file_sha256, publish_manifest, verify_bundle
from .contracts import TargetContract, utc_iso, utc_timestamp
from .targets import RepositoryStates, TRACKS, context_features, next_monday
from .splits import build_splits

FIELDS = ("forecast_id", "context_id", "repository_id", "source_project_id", "track", "context_days",
          "origin_utc", "origin_revision", "origin_observation_id", "origin_minutes", "profile_hash",
          "horizon_days", "target_id", "endpoint_utc", "endpoint_revision", "endpoint_observation_id",
          "endpoint_state_kind", "actual_minutes", "actual_delta_minutes", "known_fraction", "missing_count",
          "distinct_observation_ids", "provenance_status", "evaluation_phase")
FEATURE_FIELDS = ("context_id", "repository_id", "track", "origin_utc", "current_minutes", "known_fraction",
                  "distinct_observation_ids", "max_feature_utc", "lag7", "lag30", "lag60", "mean30", "slope30",
                  "std30", "mean90", "slope90", "std90", "availability_flags_json")


@dataclass(frozen=True)
class DatasetConfig:
    history_bundle: str
    output_root: str
    study_id: str = "phase-2-v2-calendar-v1"
    phase: int = 2
    mvp_schema_version: int = 1

    def __post_init__(self):
        if type(self.phase) is not int or self.phase != 2 or type(self.mvp_schema_version) is not int or self.mvp_schema_version != 1:
            raise ValueError("Only Phase 2 / schema 1 dataset construction supported")
        if not isinstance(self.study_id, str) or not self.study_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in self.study_id):
            raise ValueError("Explicit safe study ID required")
        if not all(isinstance(p, str) and Path(p).is_absolute() for p in (self.history_bundle, self.output_root)):
            raise ValueError("Absolute registered input/output paths required")
        if Path(self.history_bundle).resolve().is_relative_to(Path(self.output_root).resolve()):
            raise ValueError("History must be outside output root")

    @classmethod
    def load(cls, path):
        return cls(**read_json(path))


def read_history(root):
    manifest = verify_bundle(root)
    if manifest["metadata"].get("phase") != 1:
        raise ValueError("Verified Phase 1 bundle required")
    audit = read_json(Path(root) / "historical_data_audit.json")
    _, observations = read_csv(Path(root) / "historical_debt.csv", required=("observation_id", "repository_id", "commit_sha", "profile_hash", "source_sha256"), key="observation_id")
    _, git = read_csv(Path(root) / "git_history.csv", required=("repository_id", "commit_sha", "committer_timestamp", "parents_json", "first_parent_index"), key=("repository_id", "commit_sha"))
    if not audit["source"]["unchanged"] or audit["source"]["sha256"] != manifest["metadata"]["source_sha256"]:
        raise ValueError("Source provenance mismatch")
    if any(r["source_sha256"] != audit["source"]["sha256"] for r in observations):
        raise ValueError("Observation source hash mismatch")
    if len(observations) != audit["counts"]["historical_debt_rows"] or len(git) != audit["counts"]["git_history_rows"]:
        raise ValueError("Source audit row count mismatch")
    return manifest, audit, observations, git


def construct_dataset(config, output):
    code_hashes = {p.name: file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
    root = Path(config.history_bundle).resolve()
    output = Path(output).resolve()
    if output.exists() or not output.is_relative_to(Path(config.output_root).resolve()):
        raise ValueError("New output directory in configured root required")
    manifest, audit, observations, git = read_history(root)
    obs_by_repo, git_by_repo = defaultdict(list), defaultdict(list)
    for r in observations:
        obs_by_repo[r["repository_id"]].append(r)
    for r in git:
        if r["mainline_status"] == "FIRST_PARENT":
            git_by_repo[r["repository_id"]].append(r)
    examples, contexts, features = [], {}, {}
    excluded = {}
    repository_stats = []
    for repository in audit["repositories"]:
        repo = repository["repository_id"]
        ancestry = repository["ancestry"]
        if not ancestry.get("selected_tip"):
            excluded[repo] = {"source_project_id": repository["source_project_id"], "reason": "AMBIGUOUS_OR_UNRESOLVED_MAINLINE"}
            continue
        if ancestry.get("boundary") or ancestry.get("missing_parent_edges") or ancestry.get("cyclic_or_cycle_dependent_nodes"):
            excluded[repo] = {"source_project_id": repository["source_project_id"], "reason": "INCOMPLETE_OR_CYCLIC_ANCESTRY"}
            continue
        if ancestry.get("first_parent_timestamp_inversions"):
            excluded[repo] = {"source_project_id": repository["source_project_id"], "reason": "NONMONOTONIC_MAINLINE_ISOLATED", "inversion_count": ancestry["first_parent_timestamp_inversions"]}
            continue
        states = RepositoryStates(git_by_repo[repo], obs_by_repo[repo])
        if states.chain[-1]["commit_sha"] != ancestry["selected_tip"]:
            raise ValueError("Phase 1 graph-tip binding mismatch")
        origin = next_monday(states.times[0])
        candidates = Counter()
        rejections = defaultdict(Counter)
        accepted = Counter()
        context_coverage = defaultdict(list)
        endpoint_kinds = Counter()
        rejected_origin_samples = defaultdict(list)
        while origin <= states.times[-1]:
            for track, (length, horizons) in TRACKS.items():
                context, context_reason = states.context(origin, length, masked=track == "masked90")
                if context is not None:
                    context_coverage[track].append(context["known_fraction"])
                for horizon in horizons:
                    key = f"{track}:{horizon}"
                    candidates[key] += 1
                    if context_reason:
                        rejections[key][context_reason] += 1
                        if len(rejected_origin_samples[key + ":" + context_reason]) < 3:
                            rejected_origin_samples[key + ":" + context_reason].append(utc_iso(origin))
                        continue
                    label, reason = states.endpoint(origin, horizon)
                    if reason:
                        rejections[key][reason] += 1
                        if len(rejected_origin_samples[key + ":" + reason]) < 3:
                            rejected_origin_samples[key + ":" + reason].append(utc_iso(origin))
                        continue
                    context_id = digest([repo, track, context])
                    if context_id not in contexts:
                        contexts[context_id] = {"context_id": context_id, "repository_id": repo, "track": track, **context}
                        summary = context_features(context)
                        features[context_id] = {"context_id": context_id, "repository_id": repo, "track": track,
                                                "origin_utc": context["origin_utc"], **summary,
                                                "availability_flags_json": json.dumps({k: v is not None for k, v in summary.items() if k != "max_feature_utc"}, sort_keys=True, separators=(",", ":"))}
                    target = TargetContract(horizon, context_policy=f"{track}_{length}_days")
                    first, _ = states.state(origin)
                    forecast_id = digest([context_id, target.target_id])
                    examples.append({"forecast_id": forecast_id, "context_id": context_id, "repository_id": repo,
                                     "source_project_id": repository["source_project_id"], "track": track,
                                     "context_days": length, "origin_utc": utc_iso(origin), "origin_revision": first["commit_sha"],
                                     "origin_observation_id": first["observation_id"], "origin_minutes": first["value"],
                                     "profile_hash": context["profile_hash"], "horizon_days": horizon,
                                     "target_id": target.target_id, **label, "known_fraction": context["known_fraction"],
                                     "missing_count": context["missing_count"], "distinct_observation_ids": context["distinct_observation_ids"],
                                     "provenance_status": "IMPORTED_METADATA_APPROXIMATION", "evaluation_phase": "UNASSIGNED"})
                    accepted[key] += 1
                    endpoint_kinds[label["endpoint_state_kind"]] += 1
            origin += timedelta(days=7)
        grid_counts = Counter()
        day = states.times[0].replace(hour=0, minute=0, second=0, microsecond=0)
        if day < states.times[0]:
            day += timedelta(days=1)
        while day <= states.times[-1]:
            _, reason = states.state(day)
            grid_counts[reason or "KNOWN_MEASURED_STATE"] += 1
            day += timedelta(days=1)
        grid_n = sum(grid_counts.values())
        repository_stats.append({"repository_id": repo, "source_project_id": repository["source_project_id"],
                                 "candidate_counts": dict(candidates), "eligible_counts": dict(accepted),
                                 "rejection_counts": {k: dict(v) for k, v in rejections.items()},
                                 "rejected_origin_samples": dict(rejected_origin_samples),
                                 "daily_selected_state_counts": dict(grid_counts),
                                 "daily_missing_fraction": 1 - grid_counts["KNOWN_MEASURED_STATE"] / grid_n if grid_n else None,
                                 "context_known_fraction": {t: {"count": len(v), "minimum": min(v), "average": sum(v) / len(v)} for t, v in context_coverage.items()},
                                 "endpoint_state_counts": dict(endpoint_kinds), "first_parent_commits": len(states.chain)})
    examples.sort(key=lambda r: (r["repository_id"], r["track"], r["origin_utc"], r["horizon_days"]))
    if len({r["forecast_id"] for r in examples}) != len(examples):
        raise ValueError("Duplicate forecast identities")
    core = build_splits(examples, "core90", config.study_id)
    # Freeze the fallback from data only. No model predictions or error-driven selection exist.
    splits = core if core["status"] == "PASS" else build_splits(examples, "masked90", config.study_id)
    primary_track = splits["primary_track"]
    for r in examples:
        r["evaluation_phase"] = splits["assignments"].get(r["forecast_id"], "NO_VALID_SPLIT")
    counts = Counter((r["track"], r["horizon_days"]) for r in examples)
    independence = {}
    for track, horizon in sorted(counts):
        subset = [r for r in examples if r["track"] == track and r["horizon_days"] == horizon]
        grouped = defaultdict(list)
        for row in subset:
            grouped[row["repository_id"]].append(row)
        blocks = 0
        for group in grouped.values():
            end = None
            for row in sorted(group, key=lambda r: r["origin_utc"]):
                if end is None or utc_timestamp(row["origin_utc"]) > end:
                    blocks += 1
                    end = utc_timestamp(row["endpoint_utc"])
        independence[f"{track}:{horizon}"] = {
            "distinct_repository_origin_revisions": len({(r["repository_id"], r["origin_revision"]) for r in subset}),
            "distinct_repository_endpoint_revisions": len({(r["repository_id"], r["endpoint_revision"]) for r in subset}),
            "greedy_nonoverlapping_label_windows": blocks,
            "unchanged_selected_state_endpoints": sum(r["endpoint_state_kind"] == "UNCHANGED_VERIFIED_STATE" for r in subset),
            "observed_zero_delta": sum(r["actual_delta_minutes"] == 0 for r in subset),
            "effective_independent_sample_size": None}
    per_horizon_repos = {f"{t}:{h}": len({r["repository_id"] for r in examples if r["track"] == t and r["horizon_days"] == h}) for t, (_, hs) in TRACKS.items() for h in hs}
    feasibility = {"phase": 2, "status": "PARTIAL" if examples else "BLOCKED", "config": asdict(config),
                   "source_sha256": audit["source"]["sha256"], "history_manifest_sha256": file_sha256(root / "manifest.json"),
                   "input_observations": len(observations), "input_git_records": len(git), "input_repositories": len(audit["repositories"]),
                   "excluded_repositories": excluded, "repository_statistics": repository_stats,
                   "eligible_example_counts": {f"{t}:{h}": n for (t, h), n in sorted(counts.items())},
                   "independence_diagnostics": independence,
                   "eligible_repository_counts": per_horizon_repos, "total_examples": len(examples), "unique_contexts": len(contexts),
                   "primary_track": primary_track, "core_split_gate": core["status"], "selected_split_gate": splits["status"],
                   "phase3_readiness": "RESEARCH_COMPARISON_READY_RUNTIME_PENDING" if splits["status"] == "PASS" else "LIMITED_OR_BLOCKED_EVALUATION_COHORT",
                   "model_contexts": {"chronos_small": {"context_days": 90, "complete_track": "core90", "masked_track": "masked90"},
                                      "ttm30": {"context_days": 90, "native_horizon": 30, "track": "core90", "complete_required": True},
                                      "ttm60": {"context_days": 180, "native_horizon": 60, "track": "ttm60", "complete_required": True},
                                      "ttm90": {"context_days": 512, "native_horizon": 96, "crop_to": 90, "track": "ttm90", "complete_required": True}},
                   "policy": {"horizons_days": [30, 60, 90], "grid": "daily UTC, weekly Monday origins",
                              "masked_minimum_known_fraction": 0.8, "inversions": "exclude entire affected repository",
                              "metadata": "same known observed profile segment; unknown between-scan settings remain unverified",
                              "target": "native project SQALE estimated remediation minutes; signed future minus origin delta",
                              "state_selection": "last exact first-parent revision at/before cutoff, chain-order ties"},
                   "models_executed": False, "labels_constructed": True,
                   "limitations": ["Retrospective imported metadata approximation, not verified online availability or full analyzer invariance",
                                   "Unmeasured changed states are never forward-filled; masked contexts retain nulls",
                                   "Duplicate unchanged state observations and overlapping origins are not independent samples",
                                   "TTM tracks have different contexts; compare only identical registered cohorts",
                                   "Pretrained runtime/accuracy not verified; no training or inference executed"]}
    feasibility["implementation_sha256"] = code_hashes
    if code_hashes != {p.name: file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}:
        raise ValueError("Implementation changed during construction")
    if verify_bundle(root) != manifest:
        raise ValueError("Input bundle changed during construction")
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "forecasting_dataset.csv", examples, FIELDS)
    write_json(output / "forecasting_splits.json", splits)
    write_json(output / "forecasting_feasibility.json", feasibility)
    write_csv(output / "forecasting_features.csv", [features[k] for k in sorted(features)], FEATURE_FIELDS)
    label_fields = ("forecast_id", "context_id", "repository_id", "track", "horizon_days", "endpoint_utc",
                    "endpoint_revision", "endpoint_observation_id", "actual_minutes", "actual_delta_minutes", "evaluation_phase")
    write_csv(output / "forecasting_labels.csv", [{k: r[k] for k in label_fields} for r in examples], label_fields)
    # Deterministic gzip avoids repeatedly storing timestamp/identity arrays uncompressed.
    with (output / "forecasting_contexts.jsonl.gz").open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=1) as f:
            for key in sorted(contexts):
                f.write((json.dumps(contexts[key], sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8"))
    sample = []
    for key in sorted({(r["track"], r["horizon_days"]) for r in examples}):
        sample.extend([r for r in examples if (r["track"], r["horizon_days"]) == key][:2])
    write_csv(output / "forecasting_dataset_sample.csv", sample, FIELDS)
    publish_manifest(output, ["forecasting_dataset.csv", "forecasting_splits.json", "forecasting_feasibility.json",
                            "forecasting_features.csv", "forecasting_labels.csv", "forecasting_contexts.jsonl.gz", "forecasting_dataset_sample.csv"],
                     {"phase": 2, "status": feasibility["status"], "source_sha256": audit["source"]["sha256"],
                      "models_executed": False, "primary_track": primary_track})
    return feasibility
