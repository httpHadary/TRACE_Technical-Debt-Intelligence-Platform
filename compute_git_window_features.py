#!/usr/bin/env python3
"""
Computes weekly Git/process features per file (one row = one file x one weekly T0).

Current-week features (the week ending at T0):
    commits_t0, lines_added_t0, lines_deleted_t0, churn_t0, authors_t0
State-at-T0 features:
    file_age_days_t0, days_since_last_change_t0
Temporal features:
    churn_acceleration_t0   churn this week minus churn last week
    commit_burstiness_t0    variance/mean of weekly commit counts, weeks 1..T0
    churn_burstiness_t0     variance/mean of weekly churn, weeks 1..T0
Missingness:
    last_change_missing_t0, git_history_missing_t0

No future information is used: every number only looks at events dated <= T0.
The whole git history is walked once (from the first commit), so file_age is the
true age, and git_history_missing_t0 is False whenever the repo already had
commits before week 1 (always the case when week 1 starts at the repo midpoint).

Usage:
    python3 compute_git_window_features.py <start_date> [branch] [weeks]
"""
import bisect
import csv
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

import config
from weekly_commits import resolve_weekly_commits

OUTPUT_DIR = Path("git_window_features")

FIELDNAMES = [
    "artifact_id", "week", "t0", "commit_hash_t0",
    "commits_t0", "lines_added_t0", "lines_deleted_t0", "churn_t0", "authors_t0",
    "file_age_days_t0", "days_since_last_change_t0",
    "churn_acceleration_t0", "commit_burstiness_t0", "churn_burstiness_t0",
    "last_change_missing_t0", "git_history_missing_t0",
]

_BRACE = re.compile(r"^(.*?)\{(.*?) => (.*?)\}(.*)$")


def clean_numstat_path(path):
    """'a/{old => new}/F.java' -> 'a/new/F.java';  'Old.java => New.java' -> 'New.java'."""
    if "=>" not in path:
        return path
    m = _BRACE.match(path)
    if m:
        pre, _old, new, post = m.groups()
        return (pre + new + post).replace("//", "/")
    return path.split("=>")[-1].strip()


def run_git(repo_path, args):
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed:\n{' '.join(args)}\n\n{result.stderr}")
    return result.stdout


def collect_history(repo_path, end_commit):
    """{file_path: [(commit_date, author, added, deleted), ...]} for the whole history up to end_commit.
    Dates are COMMITTER dates in UTC: a patch authored earlier but landed later was NOT in the
    repository at an earlier T0, so author dates would leak future commits into past weeks."""
    out = run_git(repo_path, ["log", end_commit, "--no-merges",
                              "--format=COMMIT|%cI|%an", "--numstat"])
    history, commit_date, author = {}, None, None
    for line in out.splitlines():
        if line.startswith("COMMIT|"):
            _, iso, author = line.split("|", 2)
            commit_date = pd.Timestamp(iso)
            commit_date = commit_date.tz_convert(None) if commit_date.tzinfo is not None else commit_date
            continue
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        path = clean_numstat_path(path)
        history.setdefault(path, []).append(
            (commit_date, author,
             int(added) if added.isdigit() else 0,
             int(deleted) if deleted.isdigit() else 0))
    return history


def burstiness(values):
    """Variance / mean; 0.0 if fewer than 2 points or mean <= 0."""
    if len(values) <= 1:
        return 0.0
    mean = sum(values) / len(values)
    if mean <= 0:
        return 0.0
    return sum((v - mean) ** 2 for v in values) / len(values) / mean


def main():
    if len(sys.argv) not in (2, 3, 4):
        print(__doc__)
        sys.exit(1)
    start_date = sys.argv[1]
    branch = sys.argv[2] if len(sys.argv) >= 3 else config.BRANCH
    max_weeks = int(sys.argv[3]) if len(sys.argv) == 4 else config.DEFAULT_WEEKS
    if max_weeks <= 0:
        raise ValueError("weeks must be greater than zero")

    weeks = resolve_weekly_commits(config.REPO_PATH, start_date, branch, max_weeks=max_weeks)
    if not weeks:
        print("No weeks resolved -- check start_date/branch.")
        return
    committed = [w for w, b in weeks.items() if b["commit"]]
    if not committed:
        print("No weeks contain a resolved commit.")
        return

    first_week, last_week = min(weeks), max(weeks)
    first_start = weeks[first_week]["start"]
    latest_commit = weeks[last_week]["commit"] or weeks[max(committed)]["commit"]

    print(f">>> Walking git history once (up to {latest_commit[:8]})")
    history = collect_history(config.REPO_PATH, latest_commit)
    for events in history.values():
        events.sort(key=lambda e: e[0])

    all_dates = [e[0] for evs in history.values() for e in evs]
    history_floor = min(all_dates) if all_dates else None
    repository_history_missing = history_floor is None or history_floor > first_start
    print(f">>> Repository history floor: {history_floor} | git_history_missing: {repository_history_missing}")

    # Week k window = (start_k, end_k]; windows are contiguous, so an event's week is
    # the first k whose end >= event time (events <= week-1 start belong to no week).
    ends = [weeks[w]["end"] for w in sorted(weeks)]
    week_numbers = sorted(weeks)

    def week_of(ts):
        if ts <= first_start:
            return None
        i = bisect.bisect_left(ends, ts)
        return week_numbers[i] if i < len(week_numbers) else None

    # Per-file weekly buckets, computed ONCE.
    zero = {"commits": 0, "lines_added": 0, "lines_deleted": 0, "churn": 0, "authors": set()}
    buckets = {}
    for fpath, events in history.items():
        per_week = {}
        for ts, author, a, d in events:
            w = week_of(ts)
            if w is None:
                continue
            b = per_week.setdefault(w, {"commits": 0, "lines_added": 0, "lines_deleted": 0,
                                        "churn": 0, "authors": set()})
            b["commits"] += 1
            b["lines_added"] += a
            b["lines_deleted"] += d
            b["churn"] += a + d
            b["authors"].add(author)
        buckets[fpath] = per_week

    OUTPUT_DIR.mkdir(exist_ok=True)
    for week in week_numbers:
        bounds = weeks[week]
        if not bounds["commit"]:
            print(f"week_{week:02d}: skipped (no resolved commit)")
            continue
        label = f"week_{week:02d}"
        t0 = bounds["end"]
        rows = []
        for fpath, events in history.items():
            event_times = [e[0] for e in events]
            n_t0 = bisect.bisect_right(event_times, t0)   # events dated <= T0
            if n_t0 == 0:
                continue  # file has no history yet at T0 (not a T0 file)
            per_week = buckets[fpath]
            cur = per_week.get(week, zero)
            first_change, last_change = event_times[0], event_times[n_t0 - 1]

            commit_series = [per_week.get(w, zero)["commits"] for w in range(first_week, week + 1)]
            churn_series = [per_week.get(w, zero)["churn"] for w in range(first_week, week + 1)]
            prev = per_week.get(week - 1, zero) if (week - 1) >= first_week else None

            rows.append({
                "artifact_id": fpath, "week": week,
                "t0": t0.strftime("%Y-%m-%d"), "commit_hash_t0": bounds["commit"],
                "commits_t0": cur["commits"],
                "lines_added_t0": cur["lines_added"],
                "lines_deleted_t0": cur["lines_deleted"],
                "churn_t0": cur["churn"],
                "authors_t0": len(cur["authors"]),
                "file_age_days_t0": (t0 - first_change).days,
                "days_since_last_change_t0": (t0 - last_change).days,
                "churn_acceleration_t0": (cur["churn"] - prev["churn"]) if prev is not None else "",
                "commit_burstiness_t0": burstiness(commit_series),
                "churn_burstiness_t0": burstiness(churn_series),
                "last_change_missing_t0": False,
                "git_history_missing_t0": repository_history_missing,
            })

        with open(OUTPUT_DIR / f"{label}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{label}.csv done ({len(rows)} files)")


if __name__ == "__main__":
    main()
