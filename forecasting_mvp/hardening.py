"""Read-only Phase 2.1 validation of frozen data; no fitting or forecasting."""
import ast
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import re
import sqlite3

from contracts import digest, read_csv, read_json, write_csv, write_json
from .contracts import TargetContract, utc_iso, utc_timestamp
from .dataset import FIELDS, FEATURE_FIELDS
from .io import file_sha256, verify_bundle, publish_manifest
from .prediction_input import admit_prediction_input
from .splits import build_splits
from .targets import TRACKS, context_features


def require(condition, message):
    if not condition:
        raise ValueError(message)


def delta_kind(row):
    delta = float(row["actual_delta_minutes"])
    return "negative" if delta < 0 else "positive" if delta > 0 else "zero"


def stratified_sample(rows, minimum=100):
    """Hash-smallest in every available marginal/crossed cell, plus edge cases.

    Label stratification is for validation ONLY; never changes cohorts or fitting.
    Rare cases are deliberately overrepresented. Not a prevalence estimate.
    """
    winners = {}
    edges = {}
    for row in rows:
        h, phase = row["horizon_days"], row["evaluation_phase"]
        keys = (("repo_horizon", row["repository_id"], h),
                ("track_horizon_split_state_delta", row["track"], h, phase,
                 row["endpoint_state_kind"], delta_kind(row)),
                ("repo_split", row["repository_id"], phase))
        for key in keys:
            if key not in winners or row["forecast_id"] < winners[key]["forecast_id"]:
                winners[key] = row
        group = (row["track"], h, phase)
        for name, value in (("earliest", row["origin_utc"]), ("latest", row["origin_utc"]),
                            ("lowest_actual", float(row["actual_minutes"])),
                            ("lowest_delta", float(row["actual_delta_minutes"])),
                            ("most_missing", int(row["missing_count"])),
                            ("fewest_measurements", int(row["distinct_observation_ids"]))):
            key = (name, *group)
            rank = (value, row["forecast_id"])
            if name in ("latest", "most_missing"):
                rank = (-utc_timestamp(value).timestamp() if name == "latest" else -value, row["forecast_id"])
            if key not in edges or rank < edges[key][0]:
                edges[key] = (rank, row)
    chosen = {r["forecast_id"]: r for r in winners.values()}
    chosen.update({r["forecast_id"]: r for _, r in edges.values()})
    for row in sorted(rows, key=lambda r: r["forecast_id"]):
        if len(chosen) >= min(minimum, len(rows)):
            break
        chosen[row["forecast_id"]] = row
    return sorted(chosen.values(), key=lambda r: r["forecast_id"])


def validate_frozen(rows, splits, study_id):
    require(len({r["forecast_id"] for r in rows}) == len(rows), "Duplicate forecast identities")
    require(len({(r["repository_id"], r["track"], r["origin_utc"], r["horizon_days"]) for r in rows}) == len(rows),
            "Duplicate semantic forecast identities")
    for row in rows:
        target = TargetContract(row["horizon_days"], context_policy=f'{row["track"]}_{row["context_days"]}_days')
        require(row["endpoint_utc"] == target.endpoint(row["origin_utc"]), "Not an exact registered endpoint")
        require(row["target_id"] == target.target_id and row["forecast_id"] == digest([row["context_id"], target.target_id]),
                "Forecast/target identity mismatch")
        require(row["track"] in TRACKS and row["context_days"] == TRACKS[row["track"]][0]
                and row["horizon_days"] in TRACKS[row["track"]][1], "Unregistered context/track")
        origin = utc_timestamp(row["origin_utc"])
        require(origin.weekday() == 0 and origin.hour == origin.minute == origin.second == origin.microsecond == 0,
                "Not a registered Monday origin")
        for name in ("origin_minutes", "actual_minutes", "actual_delta_minutes"):
            value = float(row[name])
            require(value == value and abs(value) != float("inf") and (name == "actual_delta_minutes" or value >= 0),
                    "Invalid/missing stock or delta")
        require(float(row["actual_minutes"]) - float(row["origin_minutes"]) == float(row["actual_delta_minutes"]),
                "Signed target delta mismatch")
        same = row["origin_revision"] == row["endpoint_revision"]
        require(row["endpoint_state_kind"] == ("UNCHANGED_VERIFIED_STATE" if same else "MEASURED_CHANGED_STATE"),
                "Endpoint state-kind mismatch")
        require(not same or (row["origin_observation_id"] == row["endpoint_observation_id"]
                            and float(row["actual_delta_minutes"]) == 0), "Unchanged state has different measurement")
        require(row["evaluation_phase"] == splits["assignments"].get(row["forecast_id"]), "Frozen assignment mismatch")
    # Pure data-policy recomputation: no writing, fitting, outcomes or cohort edits.
    rebuilt = build_splits(rows, splits["primary_track"], study_id)
    require(rebuilt == splits, "Frozen split policy/digest mismatch")
    return {"status": "PASS", "rows_checked": len(rows), "duplicate_forecast_ids": 0,
            "duplicate_semantic_ids": 0, "exact_horizons": [30, 60, 90],
            "split_id": splits["split_id"], "frozen_policy_recomputed_identically": True}


def raw_time(value):
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    # Dataset release convention: naïve SONAR_ANALYSIS.DATE is imported as UTC.
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def raw_profile(value):
    """Independent lexical normalization, including separators inside objects."""
    if not value:
        return None
    text = re.sub(r'"(?:\\.|[^"\\])*"|;', lambda m: "," if m[0] == ";" else m[0], str(value))
    try:
        profiles = json.loads(text)
    except ValueError:
        return None
    if not isinstance(profiles, list) or not profiles or any(not isinstance(p, dict) or not p.get("key")
            or not p.get("language") for p in profiles) or len({p["language"] for p in profiles}) != len(profiles):
        return None
    return digest(sorted(profiles, key=lambda p: json.dumps(p, sort_keys=True, separators=(",", ":"))))


class RawSQLHistory:
    """Independent source oracle; never uses Phase 1 rows or RepositoryStates."""
    QUERIES = (
        "SELECT PROJECT_ID,COMMIT_HASH,COMMITTER_DATE,PARENTS,IN_MAIN_BRANCH FROM GIT_COMMITS ORDER BY PROJECT_ID,COMMIT_HASH",
        "SELECT PROJECT_ID,ANALYSIS_KEY,DATE,REVISION FROM SONAR_ANALYSIS ORDER BY PROJECT_ID,ANALYSIS_KEY,REVISION",
        "SELECT PROJECT_ID,ANALYSIS_KEY,SQALE_INDEX,QUALITY_PROFILES FROM SONAR_MEASURES ORDER BY PROJECT_ID,ANALYSIS_KEY",
    )

    def __init__(self, path, source_hash, projects):
        self.source_hash = source_hash
        git, analyses, measures = defaultdict(dict), defaultdict(list), defaultdict(list)
        with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA temp_store=MEMORY")
            for project, sha, stamp, parents, main in db.execute(self.QUERIES[0]):
                if project in projects and str(main).strip().lower() in ("true", "1"):
                    require(sha not in git[project], "Duplicate raw Git identity")
                    git[project][sha] = (raw_time(stamp), tuple(ast.literal_eval(parents)))
            for project, key, stamp, sha in db.execute(self.QUERIES[1]):
                if project in projects and key and str(key).strip():
                    analyses[project, sha].append((key, raw_time(stamp)))
            for project, key, value, profiles in db.execute(self.QUERIES[2]):
                if project in projects:
                    measures[project, key].append((value, profiles))
        self.chains, self.times, self.measurements, self.segments = {}, {}, {}, {}
        self.measurement_times = {}
        for project in sorted(projects):
            commits = git[project]
            referenced = {p for _, parents in commits.values() for p in parents if p in commits}
            tips = set(commits) - referenced
            require(len(tips) == 1, "Raw source has ambiguous mainline")
            chain, current, seen = [], next(iter(tips)), set()
            while True:
                require(current in commits and current not in seen, "Unresolved raw ancestry")
                seen.add(current)
                chain.append(current)
                _, parents = commits[current]
                if not parents:
                    break
                current = parents[0]
            chain.reverse()
            times = [commits[sha][0] for sha in chain]
            require(all(a <= b for a, b in zip(times, times[1:])), "Raw timestamp inversion")
            measured = {}
            for sha in commits:
                candidates = analyses.get((project, sha), [])
                if len(candidates) != 1:
                    continue
                key, stamp = candidates[0]
                candidates_m = measures.get((project, key), [])
                if len(candidates_m) != 1 or stamp != commits[sha][0]:
                    continue
                value, profiles = candidates_m[0]
                if value is None or str(value).strip() == "":
                    value = None
                else:
                    value = float(value)
                obs_id = digest([source_hash, project, key, sha])
                measured[sha] = {"value": value, "profile": raw_profile(profiles), "observation_id": obs_id,
                                 "analysis_id": key, "timestamp": utc_iso(stamp)}
                self.measurement_times[obs_id] = utc_iso(stamp)
            segment, prior, segments = 0, None, []
            for sha in chain:
                if sha in measured:
                    profile = measured[sha]["profile"]
                    if profile is None or profile != prior:
                        segment += 1
                    prior = profile
                segments.append(segment)
            self.chains[project], self.times[project] = chain, times
            self.measurements[project], self.segments[project] = measured, segments

    def selected(self, project, cutoff):
        stamp = utc_timestamp(cutoff)
        times = self.times[project]
        require(times[0] <= stamp <= times[-1], "Cutoff outside raw archived history")
        index = bisect_right(times, stamp) - 1
        sha = self.chains[project][index]
        return index, sha, self.measurements[project].get(sha)

    def validate_example(self, row, context):
        project = row["source_project_id"]
        require(row["repository_id"] == "v2-" + digest(project)[:24], "Repository/source mismatch")
        first_i, first_sha, first = self.selected(project, row["origin_utc"])
        last_i, last_sha, last = self.selected(project, row["endpoint_utc"])
        for prefix, sha, measured in (("origin", first_sha, first), ("endpoint", last_sha, last)):
            require(measured is not None and measured["value"] is not None, "Unmeasured exact selected endpoint")
            require(sha == row[prefix + "_revision"] and measured["observation_id"] == row[prefix + "_observation_id"],
                    "Raw selected revision/measurement mismatch")
            require(measured["value"] == float(row["origin_minutes" if prefix == "origin" else "actual_minutes"]),
                    "Raw SQALE mismatch")
            require(measured["profile"] == row["profile_hash"], "Raw profile mismatch")
        require(last["value"] - first["value"] == float(row["actual_delta_minutes"]), "Raw signed delta mismatch")
        start_i, _, _ = self.selected(project, context["context_start_utc"])
        require(len(set(self.segments[project][start_i:last_i + 1])) == 1, "Raw profile barrier crossed")
        for stamp, value, ref in zip(context["timestamps"], context["values"], context["observation_ids"]):
            _, _, measurement = self.selected(project, stamp)
            if measurement is None or measurement["value"] is None:
                require(value is None and ref is None, "Fabricated/carry-forward raw context measurement")
            else:
                require(value == measurement["value"] and ref == measurement["observation_id"], "Raw past context mismatch")
        return {"forecast_id": row["forecast_id"], "origin_analysis_id": first["analysis_id"],
                "endpoint_analysis_id": last["analysis_id"], "origin_chain_index": first_i,
                "endpoint_chain_index": last_i, "context_points_checked": len(context["values"]), "status": "PASS"}


def independence(rows, context_info):
    """Descriptive counts; none is an effective independent sample size estimate."""
    by_repo = defaultdict(list)
    for r in rows:
        by_repo[r["repository_id"]].append(r)
    overlapping, nonoverlap, adjacent, context_overlap = 0, 0, 0, 0
    for group in by_repo.values():
        ordered = sorted(group, key=lambda r: r["origin_utc"])
        last_selected_end = None
        for i, r in enumerate(ordered):
            if last_selected_end is None or r["origin_utc"] >= last_selected_end:
                nonoverlap += 1
                last_selected_end = r["endpoint_utc"]
            if i:
                prev = ordered[i - 1]
                adjacent += 1
                overlapping += r["origin_utc"] < prev["endpoint_utc"]
                context_overlap += (utc_timestamp(r["origin_utc"]) - timedelta(days=r["context_days"] - 1)
                                    <= utc_timestamp(prev["origin_utc"]))
    zero = sum(delta_kind(r) == "zero" for r in rows)
    unchanged = sum(r["endpoint_state_kind"] == "UNCHANGED_VERIFIED_STATE" for r in rows)
    refs = {ref for r in rows for ref in context_info[r["context_id"]]["refs"]}
    distinct_counts = sorted(int(r["distinct_observation_ids"]) for r in rows)
    return {"rows": len(rows), "repositories": len(by_repo), "unchanged_revision_rows": unchanged,
            "changed_revision_rows": len(rows) - unchanged, "unchanged_debt_rows": zero,
            "changing_debt_rows": len(rows) - zero, "zero_delta_fraction": zero / len(rows),
            "changed_revision_zero_delta_rows": zero - unchanged,
            "positive_delta_rows": sum(delta_kind(r) == "positive" for r in rows),
            "negative_delta_rows": sum(delta_kind(r) == "negative" for r in rows),
            "zero_origin_stock_rows": sum(float(r["origin_minutes"]) == 0 for r in rows),
            "zero_endpoint_stock_rows": sum(float(r["actual_minutes"]) == 0 for r in rows),
            "distinct_origin_measurements": len({r["origin_observation_id"] for r in rows}),
            "distinct_endpoint_measurements": len({r["endpoint_observation_id"] for r in rows}),
            "distinct_origin_endpoint_pairs": len({(r["origin_observation_id"], r["endpoint_observation_id"]) for r in rows}),
            "distinct_context_measurements": len(refs),
            "distinct_context_measurement_sequences": len({context_info[r["context_id"]]["refs_digest"] for r in rows}),
            "distinct_context_value_sequences": len({context_info[r["context_id"]]["values_digest"] for r in rows}),
            "distinct_context_values_min": min(context_info[r["context_id"]]["distinct_values"] for r in rows),
            "context_distinct_measurements_min_median_max": [distinct_counts[0], distinct_counts[len(rows)//2], distinct_counts[-1]],
            "daily_context_slots": sum(r["context_days"] for r in rows),
            "missing_context_slots": sum(r["missing_count"] for r in rows),
            "adjacent_window_pairs": adjacent, "overlapping_adjacent_label_pairs": overlapping,
            "overlapping_adjacent_context_pairs": context_overlap,
            "greedy_nonoverlapping_label_windows": nonoverlap, "effective_independent_sample_size": None}


def cross_split_reuse(rows, context_info):
    """Past contexts may overlap across time splits; disclose measurement reuse.

    This is not grounds for relabeling fixed cohorts. Fit labels must remain
    purged; historical inputs can legitimately be shared with later contexts.
    """
    groups = defaultdict(list)
    for row in rows:
        if row["evaluation_phase"] in ("train", "validation", "test_temporal", "test_repository"):
            groups[(row["track"], row["horizon_days"])].append(row)
    result = {}
    for key, group in sorted(groups.items()):
        by_phase = defaultdict(list)
        for row in group:
            by_phase[row["evaluation_phase"]].append(row)
        pairs = {}
        phases = sorted(by_phase)
        for i, a in enumerate(phases):
            for b in phases[i + 1:]:
                left, right = by_phase[a], by_phase[b]
                pairs[a + ":" + b] = {
                    "shared_endpoint_measurements": len({r["endpoint_observation_id"] for r in left} &
                                                         {r["endpoint_observation_id"] for r in right}),
                    "shared_context_measurements": len({ref for r in left for ref in context_info[r["context_id"]]["refs"]} &
                                                        {ref for r in right for ref in context_info[r["context_id"]]["refs"]}),
                    "shared_context_value_sequences": len({context_info[r["context_id"]]["values_digest"] for r in left} &
                                                          {context_info[r["context_id"]]["values_digest"] for r in right}),
                    "overlapping_label_window_pairs": sum(1 for l in left for r in right
                        if l["repository_id"] == r["repository_id"] and l["origin_utc"] < r["endpoint_utc"]
                        and r["origin_utc"] < l["endpoint_utc"])}
        result[":".join(map(str, key))] = pairs
    return result


def audit_dataset(bundle, source_db, output, *, study_id="phase-2-v2-calendar-v1"):
    bundle, source_db, output = Path(bundle).resolve(), Path(source_db).resolve(), Path(output).resolve()
    require(not output.exists() and not output.is_relative_to(bundle) and not bundle.is_relative_to(output)
            and not source_db.is_relative_to(output), "New separate output directory required")
    frozen = verify_bundle(bundle)
    code_hashes = {p.name: file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
    require(frozen["metadata"].get("phase") == 2, "Frozen Phase 2 bundle required")
    manifest_hash = file_sha256(bundle / "manifest.json")
    source_hash = file_sha256(source_db)
    require(source_hash == frozen["metadata"]["source_sha256"], "Raw source hash mismatch")
    header, rows = read_csv(bundle / "forecasting_dataset.csv", required=FIELDS, key="forecast_id")
    require(tuple(header) == FIELDS, "Unexpected dataset fields")
    for row in rows:
        for key in ("horizon_days", "context_days", "missing_count", "distinct_observation_ids"):
            row[key] = int(row[key])
    splits = read_json(bundle / "forecasting_splits.json")
    structural = validate_frozen(rows, splits, study_id)
    sample = stratified_sample(rows)
    require(len(sample) >= 100, "At least 100 independent raw-SQL checks required")
    raw = RawSQLHistory(source_db, source_hash, {r["source_project_id"] for r in rows})
    header, features = read_csv(bundle / "forecasting_features.csv", required=FEATURE_FIELDS, key="context_id")
    require(tuple(header) == FEATURE_FIELDS, "Unexpected model-facing feature fields; targets/evaluation labels forbidden")
    features = {r["context_id"]: r for r in features}
    linked = defaultdict(list)
    for r in rows:
        linked[r["context_id"]].append(r)
    sample_linked = defaultdict(list)
    for r in sample:
        sample_linked[r["context_id"]].append(r)
    context_info, sql_checks = {}, []
    with gzip.open(bundle / "forecasting_contexts.jsonl.gz", "rt", encoding="utf-8") as stream:
        for line in stream:
            context = json.loads(line)
            cid = context["context_id"]
            require(cid not in context_info and cid in linked and cid in features, "Duplicate/unlinked context identity")
            representative = linked[cid][0]
            admitted = admit_prediction_input(context, representative["horizon_days"],
                expected_origin_utc=representative["origin_utc"], measurement_times=raw.measurement_times)
            summary = context_features(context)
            feature = features[cid]
            for key in ("repository_id", "track", "origin_utc"):
                require(context[key] == representative[key] == feature[key], "Feature/context binding mismatch")
            for key, value in summary.items():
                stored = feature[key]
                require((stored == "" if value is None else stored == value if isinstance(value, str) else float(stored) == value),
                        "Feature not derived exclusively from past context")
            flags = {k: v is not None for k, v in summary.items() if k != "max_feature_utc"}
            require(json.loads(feature["availability_flags_json"]) == flags, "Feature availability mismatch")
            for row in linked[cid]:
                for key in ("context_days", "known_fraction", "missing_count", "distinct_observation_ids", "profile_hash"):
                    require(str(context[key]) == str(row[key]), "Dataset/context summary mismatch")
                require(float(row["origin_minutes"]) == admitted.values[-1]
                        and row["origin_observation_id"] == context["observation_ids"][-1], "Origin context mismatch")
            context_info[cid] = {"refs": tuple(sorted({ref for ref in context["observation_ids"] if ref})),
                                "refs_digest": digest(context["observation_ids"]), "values_digest": digest(context["values"]),
                                "distinct_values": len({v for v in context["values"] if v is not None})}
            for row in sample_linked[cid]:
                sql_checks.append(raw.validate_example(row, context))
    require(set(context_info) == set(linked) == set(features), "Missing/unreferenced contexts/features")
    _, labels = read_csv(bundle / "forecasting_labels.csv", key="forecast_id")
    require(len(labels) == len(rows), "Label projection count mismatch")
    by_id = {r["forecast_id"]: r for r in rows}
    for label in labels:
        require(label["forecast_id"] in by_id and all(str(by_id[label["forecast_id"]][k]) == v for k, v in label.items()),
                "Label projection mismatch")
    del labels, features, raw
    grouped, repo_grouped = defaultdict(list), defaultdict(list)
    for r in rows:
        key = (r["track"], r["horizon_days"], r["evaluation_phase"])
        grouped[key].append(r)
        repo_grouped[(r["repository_id"], *key)].append(r)
    quality = {"status": "PASS", "rows": len(rows), "unique_contexts": len(context_info),
               "model_executions": 0, "primary_track": splits["primary_track"],
               "per_track_horizon_split": {":".join(map(str, k)): independence(v, context_info) for k, v in sorted(grouped.items())},
               "per_repository_track_horizon_split": {":".join(map(str, k)): independence(v, context_info) for k, v in sorted(repo_grouped.items())},
               "cross_split_reuse": cross_split_reuse(rows, context_info),
               "interpretation": ["Different Git revisions can have identical SQALE; zero delta is not necessarily unchanged state",
                   "Daily contexts reuse underlying scans; counts and greedy disjoint windows are descriptive, not effective N",
                   "Tracks are alternatives, not additional independent observations",
                   "Diagnostic label stratification does not alter frozen splits or tune model selection"]}
    sample_counts = {name: dict(sorted(Counter(str(r[name]) for r in sample).items())) for name in
                     ("repository_id", "track", "horizon_days", "evaluation_phase", "endpoint_state_kind")}
    sample_counts["delta_sign"] = dict(sorted(Counter(delta_kind(r) for r in sample).items()))
    require(file_sha256(source_db) == source_hash and verify_bundle(bundle) == frozen
            and file_sha256(bundle / "manifest.json") == manifest_hash, "Input changed during audit")
    require(code_hashes == {p.name: file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
            "Implementation changed during audit")
    result = {"status": "PASS", "phase": "2.1", "models_executed": False, "frozen_dataset_rebuilt": False,
              "phase_3_readiness": "PARTIAL", "readiness_reasons": ["Imported analyzer/availability provenance remains incomplete",
                  "Pretrained package/weight/hardware admission remains unverified; no model execution authorized"],
              "source_sha256": source_hash, "frozen_manifest_sha256": manifest_hash,
              "implementation_sha256": code_hashes,
              "frozen_artifact_hashes": frozen["artifacts"], "structural_checks": structural,
              "contexts_checked": len(context_info), "feature_rows_checked": len(context_info), "label_rows_checked": len(rows),
              "raw_sql_sample_count": len(sample), "raw_sql_all_passed": len(sql_checks) == len(sample),
              "raw_sql_context_points_checked": sum(r["context_points_checked"] for r in sql_checks),
              "stratification_policy": "hash_min_marginal_and_crossed_cells_plus_edges_v1",
              "sample_counts": sample_counts, "raw_sql_queries": list(RawSQLHistory.QUERIES),
              "raw_sql_checks": sorted(sql_checks, key=lambda r: r["forecast_id"]),
              "limitations": ["Imported naive Sonar dates are interpreted as UTC, not historical online availability",
                  "Full analyzer/build/rules metadata remains unavailable", "No performance or statistical independence claimed",
                  "Raw SQL checks are stratified spot validation, not exhaustive independent proof of every label"]}
    require(result["raw_sql_all_passed"], "Incomplete raw SQL checks")
    output.mkdir(parents=True)
    write_json(output / "dataset_validation.json", result)
    write_json(output / "dataset_quality.json", quality)
    write_csv(output / "raw_sql_validation_sample.csv", sample, FIELDS)
    publish_manifest(output, ["dataset_validation.json", "dataset_quality.json", "raw_sql_validation_sample.csv"],
                     {"phase": "2.1", "status": "PASS", "models_executed": False, "source_sha256": source_hash})
    return result
