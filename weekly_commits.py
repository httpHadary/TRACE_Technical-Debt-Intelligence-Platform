"""
Shared weekly calendar + T0 commit resolver (single source of truth).

Week k covers (start + 7(k-1) days, start + 7k days]; T0 = latest commit on
`branch` dated before the end of that week. Weeks with no commit stay in the
dict with commit=None (calendar weeks are never compressed).

Also provides midpoint_start_date(): the date halfway between the repo's
first and latest commit, and origin_start_date(): midpoint minus the history
warm-up, used when no start_date is given (so T0 begins at the midpoint).
"""
import subprocess
from pathlib import Path

import pandas as pd


def _run_git(repo_path, args):
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed:\n{' '.join(args)}\n\n{result.stderr}")
    return result.stdout


def midpoint_start_date(repo_path, branch="master"):
    """Halfway point (midnight, 'YYYY-MM-DD') between the first and latest commit on `branch`."""
    roots = _run_git(repo_path, ["log", "--max-parents=0", "--format=%cI", branch]).split()
    if not roots:
        raise RuntimeError(f"No commits found on branch '{branch}'.")
    first = min(pd.Timestamp(d).tz_localize(None) if pd.Timestamp(d).tzinfo is None
                else pd.Timestamp(d).tz_convert(None) for d in roots)
    last = pd.Timestamp(_run_git(repo_path, ["log", "-1", "--format=%cI", branch]).strip())
    last = last.tz_convert(None) if last.tzinfo is not None else last
    return (first + (last - first) / 2).normalize().strftime("%Y-%m-%d")


def origin_start_date(repo_path, branch="master", history_weeks=26):
    """
    Week-1 start such that the FIRST T0 week (week history_weeks+1) starts exactly at the
    repo midpoint: midpoint - history_weeks*7 days. Everything (midpoint, start) is computed
    from the repo's own git history.
    """
    mid = pd.Timestamp(midpoint_start_date(repo_path, branch))
    return (mid - pd.Timedelta(days=7 * history_weeks)).strftime("%Y-%m-%d")


def available_weeks(repo_path, start_date, branch="master"):
    """How many whole 7-day weeks fit between start_date and the latest commit."""
    last = pd.Timestamp(_run_git(repo_path, ["log", "-1", "--format=%cI", branch]).strip())
    last = last.tz_convert(None) if last.tzinfo is not None else last
    return max(0, (last - pd.Timestamp(start_date)).days // 7)


def resolve_weekly_commits(repo_path, start_date, branch="master", max_weeks=None):
    """
    Returns {week_number: {"start": Timestamp, "end": Timestamp, "commit": str|None}}.
    `end` = start + 7 days. Capped at max_weeks and at the latest commit date.
    """
    repo_path = Path(repo_path)
    start_date = pd.Timestamp(start_date)

    latest_date = pd.Timestamp(_run_git(repo_path, ["log", "-1", "--format=%cI", branch]).strip())
    latest_date = latest_date.tz_convert(None) if latest_date.tzinfo is not None else latest_date

    weeks, current_start, week_number = {}, start_date, 1
    while current_start + pd.Timedelta(days=7) <= latest_date:
        if max_weeks is not None and week_number > max_weeks:
            break
        weeks[week_number] = {
            "start": current_start,
            "end": current_start + pd.Timedelta(days=7),
        }
        current_start += pd.Timedelta(days=7)
        week_number += 1

    for bounds in weeks.values():
        # EXPLICIT UTC timestamp. A bare date ("2020-01-03") makes git fill in the CURRENT
        # clock time, so which boundary-day commits were included depended on when the script
        # ran. A full timestamp makes T0 reproducible (committer date <= week end, inclusive).
        before_ts = bounds["end"].strftime("%Y-%m-%dT%H:%M:%S") + "+0000"
        commit = _run_git(repo_path, ["rev-list", '--first-parent', "-1", f"--before={before_ts}", branch]).strip()
        bounds["commit"] = commit or None

    return weeks
