#!/usr/bin/env python3
"""
Weekly data collection (module level). Schedule this once a week.

What it does for every repo in repos.csv (thin wrapper around run_all_repos.py --weekly-update):
  1. git fetch + fast-forward the local clone to origin/<branch>
  2. reuse the start_date pinned in <output-dir>/<repo>/repo_context.json (first run pins it),
     so week_NN labels never shift as the repo grows
  3. scan ONLY the weeks that are new since the last run (already-scanned weeks are skipped;
     calendar weeks with no new commit are copied, not re-scanned)
  4. rebuild module_weekly_state.csv (all weeks x modules, incl. sqale_index), module_latest_snapshot.csv,
     module_td_mart.csv and the combined_* files

Usage:
    export SONAR_TOKEN=<token>
    python3 weekly_update.py repos.csv --repos-dir <clones> --output-dir <runs> [--holdout-repos a,b]

Cron (Sundays 02:00):
    0 2 * * 0  cd /path/to/td_pipeline && SONAR_TOKEN=xxx python3 weekly_update.py repos.csv \
               --repos-dir /data/clones --output-dir /data/runs >> weekly_update.log 2>&1
Windows Task Scheduler: weekly trigger, action = python weekly_update.py repos.csv --repos-dir ... --output-dir ...
(SonarQube must be running and SONAR_TOKEN set for the task's user.)
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    here = Path(__file__).resolve().parent / "run_all_repos.py"
    cmd = [sys.executable, str(here), "--weekly-update", "--level", "module", *sys.argv[1:]]
    sys.exit(subprocess.call(cmd))
