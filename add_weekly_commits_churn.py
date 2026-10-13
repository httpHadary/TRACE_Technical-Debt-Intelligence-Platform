#!/usr/bin/env python3
"""
Computes per-file, per-week `commits` and `churn` and merges them into
pipeline_total_line.py's output -- filling in the columns
pipeline_g3.py requires (artifact_id, churn, commits, total_lines) that
nothing else in this pipeline currently produces.

commits_this_week / churn_this_week are NOT the trailing 30d/90d/180d
windows compute_git_window_features.py computes -- they're just "how
much happened inside THIS single 7-day calendar week", matching
pipeline_total_line.py's own week boundaries exactly (same
resolve_weekly_commits() call, so week_XX here is guaranteed to line up
with week_XX in weekly_total_lines/).

  commits   count of commits touching this file with a commit date
            inside (week.start, week.end] (no-merges)
  churn     lines added + deleted by those commits

Run this AFTER pipeline_total_line.py and BEFORE pipeline_g3.py. It
reads weekly_total_lines/week_XX.csv (for the file list + total_lines)
and OVERWRITES each file in place, adding the two new columns.

Usage:
    python3 add_weekly_commits_churn.py <start_date> [branch] [weeks] [total_lines_dir]

Example (matching a 60-week run):
    python3 add_weekly_commits_churn.py 2011-08-01 trunk 60 weekly_total_lines
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd

import config
from weekly_commits import resolve_weekly_commits


def run_git(repo_path, args):
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed:\n{' '.join(args)}\n\n{result.stderr}")
    return result.stdout


# Same collector as compute_git_window_features.py (committer date, UTC, correct rename
# handling) so commits_g3 / churn_g3 always equal commits_t0 / churn_t0.
from compute_git_window_features import collect_history as _collect_history


def collect_history(repo_path, end_commit, since=None, until=None):
    """{file_path: [(date, added, deleted), ...]} -- whole history up to end_commit."""
    full = _collect_history(repo_path, end_commit)
    return {p: [(d, a, dl) for (d, _author, a, dl) in ev] for p, ev in full.items()}


def events_in(events, start, end):
    """(start, end] inclusive of end -- same convention compute_git_window_features.py uses."""
    return [e for e in events if start < e[0] <= end]


def main():
    if len(sys.argv) not in (2, 3, 4, 5):
        print(__doc__)
        sys.exit(1)
    start_date_arg = sys.argv[1]
    branch = sys.argv[2] if len(sys.argv) >= 3 else "trunk"
    max_weeks = int(sys.argv[3]) if len(sys.argv) >= 4 else 26
    total_lines_dir = Path(sys.argv[4]) if len(sys.argv) == 5 else Path("weekly_total_lines")

    weeks = resolve_weekly_commits(config.KAFKA_REPO_PATH, start_date_arg, branch, max_weeks=max_weeks)
    weeks = {w: b for w, b in weeks.items() if b["commit"]}
    if not weeks:
        print("No weeks resolved -- check start_date/branch.")
        return

    latest_commit = list(weeks.values())[-1]["commit"]
    earliest_start = list(weeks.values())[0]["start"]
    latest_end = list(weeks.values())[-1]["end"]

    print(f">>> Walking git history once: {earliest_start.date()} -> {latest_end.date()}")
    history = collect_history(
        config.KAFKA_REPO_PATH, latest_commit,
        earliest_start.strftime("%Y-%m-%dT00:00:00"),
        latest_end.strftime("%Y-%m-%dT23:59:59"),
    )

    for week, bounds in weeks.items():
        label = f"week_{week:02d}"
        total_lines_file = total_lines_dir / f"{label}.csv"
        if not total_lines_file.exists():
            print(f">>> {label}: {total_lines_file} not found -- run pipeline_total_line.py first, skipping.")
            continue

        rows = []
        for fpath, events in history.items():
            evs = events_in(events, bounds["start"], bounds["end"])
            if not evs:
                continue
            rows.append({
                "artifact_id": fpath,
                "commits": len(evs),
                "churn": sum(a + d for _, a, d in evs),
            })
        commits_df = pd.DataFrame(rows, columns=["artifact_id", "commits", "churn"])

        total_lines_df = pd.read_csv(total_lines_file)
        # Idempotency: if this file already has commits/churn from a
        # previous run, drop them first -- otherwise pandas' merge()
        # would silently rename both sides to commits_x/commits_y
        # instead of overwriting, and every line below would KeyError.
        total_lines_df = total_lines_df.drop(columns=["commits", "churn"], errors="ignore")
        merged = total_lines_df.merge(commits_df, on="artifact_id", how="left")
        merged["commits"] = merged["commits"].fillna(0).astype(int)
        merged["churn"] = merged["churn"].fillna(0).astype(int)

        merged.to_csv(total_lines_file, index=False)
        print(f">>> {label}: added commits/churn for {len(merged):,} files "
              f"({(merged['commits'] > 0).sum():,} touched this week)")

    print(">>> Done. Next: python3 pipeline_g3.py <total_lines_dir> <output_dir>")


if __name__ == "__main__":
    main()
