"""Data-only calendar/repository splits; labels crossing boundaries are purged."""
from collections import Counter, defaultdict
from datetime import timedelta
import math

from contracts import digest
from .contracts import utc_iso, utc_timestamp
from .targets import next_monday


def build_splits(rows, track, study_id):
    if len({r["forecast_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate split identities")
    for row in rows:
        horizon = row["horizon_days"]
        if type(horizon) is not int or horizon not in (30, 60, 90) or (
                utc_timestamp(row["endpoint_utc"]) - utc_timestamp(row["origin_utc"])).total_seconds() != horizon * 86400:
            raise ValueError("Split target does not match exact registered horizon")
    intervals = {}
    grouped = defaultdict(list)
    for r in rows:
        if r["track"] == track and r["horizon_days"] == 90:
            grouped[r["repository_id"]].append(utc_timestamp(r["origin_utc"]))
    intervals = {repo: (min(times), max(times)) for repo, times in grouped.items()}
    candidates = []
    # Metadata/eligibility-only largest calendar-overlap cohort; no error/target values used.
    for start in sorted({a for a, _ in intervals.values()}):
        repos = sorted(repo for repo, (a, b) in intervals.items() if a <= start and b >= start + timedelta(days=630))
        if len(repos) < 3:
            continue
        end = min(intervals[repo][1] for repo in repos)
        candidates.append((len(repos), (end - start).total_seconds(), utc_iso(start), repos, end))
    if not candidates:
        return {"status": "BLOCKED", "primary_track": track, "reason": "NO_SHARED_630_DAY_COHORT",
                "assignments": {}, "phase_counts": {}, "registered_policy": "metadata_largest_overlap_v1"}
    _, _, start, repos, end = sorted(candidates, key=lambda x: (-x[0], -x[1], x[2]))[0]
    start = utc_timestamp(start)
    validation_start = next_monday(start + (end - start) * 0.60)
    validation_end = next_monday(start + (end - start) * 0.80)
    test_start = next_monday(validation_end + timedelta(days=90))
    holdout_n = max(2, math.ceil(0.25 * len(repos)))
    held = sorted(repos, key=lambda repo: digest([study_id, repo]))[:holdout_n]
    assignments = {}
    counts = Counter()
    by_track_horizon = defaultdict(Counter)
    for r in rows:
        origin = utc_timestamp(r["origin_utc"])
        endpoint = utc_timestamp(r["endpoint_utc"])
        repo = r["repository_id"]
        if repo not in repos or origin < start or origin > end:
            phase = "EXCLUDED_SHARED_CALENDAR"
        elif repo in held:
            phase = "test_repository" if test_start <= origin <= end else "UNUSED_HELDOUT"
        elif origin < validation_start:
            phase = "train" if endpoint < validation_start else "PURGED_TRAIN_LABEL"
        elif validation_start <= origin < validation_end:
            phase = "validation" if endpoint < test_start else "PURGED_VALIDATION_LABEL"
        elif test_start <= origin <= end:
            phase = "test_temporal"
        else:
            phase = "EMBARGO"
        assignments[r["forecast_id"]] = phase
        if r["track"] == track:
            counts[phase] += 1
        by_track_horizon[(r["track"], r["horizon_days"])][phase] += 1
    phases = ("train", "validation", "test_temporal", "test_repository")
    primary_counts = {str(h): dict(by_track_horizon[(track, h)]) for h in (30, 60, 90)}
    ready = len(repos) >= 6 and all(primary_counts[str(h)].get(p, 0) > 0 for h in (30, 60, 90) for p in phases)
    result = {"status": "PASS" if ready else "PARTIAL", "primary_track": track,
              "registered_policy": "metadata_largest_overlap_v1", "minimum_common_span_days": 630,
              "repository_ids": repos, "held_repository_ids": held,
              "boundaries": {"start": utc_iso(start), "end": utc_iso(end), "validation_start": utc_iso(validation_start),
                             "validation_end": utc_iso(validation_end), "test_start": utc_iso(test_start)},
              "phase_counts": dict(sorted(counts.items())), "per_horizon_counts": primary_counts,
              "per_track_horizon_counts": {f"{t}:{h}": dict(c) for (t, h), c in sorted(by_track_horizon.items())},
              "assignments": dict(sorted(assignments.items())),
              "limitations": ["630-day overlap and six-repository gate are registered project choices, not power guarantees",
                              "Cohort selection uses data availability; disclose selection bias",
                              "Weekly origins overlap; rows are not independent statistical samples"]}
    result["split_id"] = digest(result)
    return result
