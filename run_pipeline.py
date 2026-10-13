#!/usr/bin/env python3
"""
Runs the full TD-regression pipeline for ONE already-cloned repo (the
one config.py / repo_context.json in this directory points at), in
order, in one command.

For multiple repos given as git URLs, use run_all_repos.py instead --
it does this same sequence per repo, in its own isolated working
directory, and combines the results. This script stays around for
re-running the single local repo you already have cloned (e.g. Kafka)
without a redundant extra clone.

Target: TD_3w / TD_1m / TD_3m (future remediation effort), not the old
NPF-90 binary label -- see build_td_mart.py.

It stops at the first step that fails (non-zero exit code) instead of
plowing ahead with broken/missing inputs for the next step.

Usage:
    python3 run_pipeline.py <start_date|midpoint> [--branch master] [--weeks 120] [--skip-scan]

    start_date "midpoint" = halfway between the repo's first and latest commit.

Example (fresh run starting at the repo midpoint):
    python3 run_pipeline.py midpoint --branch master --weeks 120

Example (data already scanned, just rebuild features + mart):
    python3 run_pipeline.py 2011-08-01 --weeks 60 --skip-scan

Requires: config.py filled in, and every script this calls
(scan_weekly_snapshots.py, pipeline_total_line.py,
add_weekly_commits_churn.py, pipeline_g3.py,
compute_git_window_features.py, compute_ownership_entropy.py,
compute_lineage.py, compute_sonar_trend_features.py,
compute_finding_lifecycle.py, build_td_mart.py) sitting in this same
directory.

NOT run by default (they're diagnostic-only -- their output isn't
consumed by build_td_mart.py, which re-derives everything it needs
directly from data/, git_window_features/, sonar_trends/,
finding_lifecycle/, and lineage/): merge_measures_issues.py,
merge_weekly_features.py, compute_issue_persistence.py, compute_label.py,
build_origin_mart.py. Run them by hand if you still want that per-week
combined view for exploration.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import config

PYTHON = sys.executable

TOTAL_LINES_DIR = "weekly_total_lines"   # pipeline_total_line.py output
G3_DIR = "weekly_g3_features"            # pipeline_g3.py output


def step(title):
    print()
    print("=" * 70)
    print(f">>> {title}")
    print("=" * 70)


def run(cmd, allow_fail=False):
    if len(cmd) > 1 and cmd[0] == PYTHON and cmd[1].endswith('.py'):
        cmd = [cmd[0], str(Path(__file__).resolve().parent / cmd[1]), *cmd[2:]]
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0 and not allow_fail:
        print(f"\n!!! Step failed (exit {result.returncode}): {' '.join(cmd)}")
        print("!!! Stopping here -- fix the error above before re-running.")
        sys.exit(result.returncode)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("start_date", help="e.g. 2015-01-01, or 'midpoint' for the repo's halfway date")
    parser.add_argument("--branch", default=None, help="default: config.BRANCH")
    parser.add_argument("--weeks", type=int, default=config.DEFAULT_WEEKS,
                         help="Total weeks to scan. 26 (trailing history) + 13 (longest horizon, "
                              "TD_3m) + 1 = 40 is the bare minimum for ONE T0 week with all three "
                              "targets observable; default 60 gives more.")
    parser.add_argument("--level", choices=["module", "file", "both"], default="module",
                         help="module (default): module_weekly_state.csv + module_td_mart.csv; "
                              "file: the original td_mart.csv; both.")
    parser.add_argument("--skip-scan", action="store_true",
                         help="Skip step 1 (scan_weekly_snapshots.py) -- use if data/ is already populated")
    args = parser.parse_args()

    from weekly_commits import available_weeks, midpoint_start_date, origin_start_date
    args.branch = args.branch or config.BRANCH
    if args.start_date.lower() in ("midpoint", "auto"):
        midpoint = midpoint_start_date(config.REPO_PATH, args.branch)
        args.start_date = origin_start_date(config.REPO_PATH, args.branch, config.HISTORY_WEEKS)
        print(f">>> repo midpoint = {midpoint}; week 1 starts {config.HISTORY_WEEKS} weeks earlier = {args.start_date}")
    args.weeks = min(args.weeks, available_weeks(config.REPO_PATH, args.start_date, args.branch))
    print(f">>> using {args.weeks} weeks from {args.start_date} on '{args.branch}'")

    date_args = [args.start_date, args.branch, str(args.weeks)]

    # --- Step 1: scan one Sonar snapshot per week -----------------------
    if args.skip_scan:
        step("Step 1: scan_weekly_snapshots.py -- SKIPPED (--skip-scan)")
    else:
        step("Step 1/4: scan_weekly_snapshots.py -- one Sonar snapshot per week")
        run([PYTHON, "scan_weekly_snapshots.py", *date_args])

    # git line counts are needed at BOTH levels (stale-scan validation)
    run([PYTHON, "validate_snapshots.py"])

    if args.level in ("file", "both"):
        run([PYTHON, "pipeline_total_line.py", config.REPO_PATH, TOTAL_LINES_DIR, *date_args])
        # --- Step 2: git-only weekly feature sources ------------------------
        step("Step 2/4: git feature sources (total lines, churn/g3, git windows, ownership, lineage)")
        run([PYTHON, "add_weekly_commits_churn.py", args.start_date, args.branch, str(args.weeks), TOTAL_LINES_DIR])
        run([PYTHON, "pipeline_g3.py", TOTAL_LINES_DIR, G3_DIR])
        run([PYTHON, "compute_git_window_features.py", *date_args])
        run([PYTHON, "compute_ownership_entropy.py", *date_args])
        run([PYTHON, "compute_lineage.py", *date_args])

        # --- Step 3: Sonar trend + lifecycle features ------------------------
        step("Step 3/4: Sonar trend + finding-lifecycle features")
        run([PYTHON, "compute_sonar_trend_features.py"])
        run([PYTHON, "compute_finding_lifecycle.py"])

        # --- Step 4: build the TD-regression mart ----------------------------
        step("Step 4/4: build_td_mart.py -- TD_3w / TD_1m / TD_3m regression targets")
        run([PYTHON, "build_td_mart.py", args.start_date, args.branch, str(args.weeks), G3_DIR])


    if args.level in ("module", "both"):
        step("Module level: build_module_mart.py -- module_weekly_state.csv, module_td_mart.csv")
        run([PYTHON, "build_module_mart.py", *date_args])

    print()
    print("Pipeline finished. -> module_weekly_state.csv / module_td_mart.csv (module) and/or td_mart.csv (file)")


if __name__ == "__main__":
    main()
