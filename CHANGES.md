# 2026-10-10 module-pipeline repair

The authoritative current contract is [MODULE_LEVEL_README.md](MODULE_LEVEL_README.md).
Missing observations are now explicit, never zero-imputed. Exact task/revision/source/profile
evidence and complete export pagination are required. Module definitions use the earliest snapshot;
calendar T0 and fixed partitions replace commit-date T0 and moving splits. Validation is read-only,
failures stop orchestration, exports can resume without scanning, and output generations prevent
stale/duplicate/wrong-repository combination. Regression tests include an offline 138-week pipeline.

This intentionally rejects incomplete legacy evidence. No automatic migration or real re-scan occurred.
Historical entries below describe older behavior; their zero-fill, `--fix`, auto-rescan and credential
instructions are superseded. See REPAIR_REPORT.md for results and remaining validation limits.

# Historical: v3 -- contiguous weeks, midpoint-centred T0, no-blank mart

| File | Change |
|---|---|
| `config.py` | `HISTORY_WEEKS=26`, `HORIZON_WEEKS=12`, `T0_WEEKS=100`, `DEFAULT_WEEKS=138`; flags `DROP_INELIGIBLE_ROWS`, `REQUIRE_ALL_TARGETS_OBSERVED`, `FILL_OMITTED_ZERO_MEASURES`. |
| `weekly_commits.py` | `origin_start_date()` = repo midpoint (computed from git) - 26 weeks, so the first T0 week starts exactly at the midpoint. |
| `run_all_repos.py`, `run_pipeline.py` | Blank / `midpoint` start_date -> `origin_start_date()`. `held_repository` defaults to `NONE` instead of blank. |
| `scan_weekly_snapshots.py` | Weeks whose commit equals the previous week's are no longer skipped: measures/issues/snapshot/metadata rows are copied from the previous snapshot (no re-scan). week_01..week_N always exist. |
| `td_utils.py` | `assert_contiguous_weeks()`. Called by `compute_sonar_trend_features.py` and `compute_finding_lifecycle.py` (fail loudly on gaps like 1,14,18). |
| `pull_metrics.py` | Java files: `cognitive_complexity` and `duplicated_*` that Sonar omits (value 0) are stored as 0. Only applies to snapshots scanned AFTER this change. |
| `build_td_mart.py` | Emits only T0 weeks 27..(N-12); production Java files only; eligible rows only; all 3 targets OBSERVED; empty reason columns -> `NONE`; prints a blank-column report. |
| `repos.csv` | commons-io only (start_date and weeks blank -> computed). |

Run:  python3 run_all_repos.py repos.csv --repos-dir <local clones> --output-dir <runs>

# What changed vs. the old GradProject pipeline

Output: `td_mart.csv` now has the same 124 columns, in the same order, as the technicaldebt_3m mart.

| File | Change |
|---|---|
| `build_td_mart.py` | Rewritten to the new schema (`week`, `*_t0` git columns, no 30d/90d/180d, no `path_at_*`, single `max_feature_ts`, `split_family=CHRONOLOGICAL`), 3m horizon = 12 weeks, fixed target column order. Effort parsing handles days. |
| `compute_git_window_features.py` | Now writes the new `*_t0` git columns. Full git history is walked once (true file age). Rename paths (`a/{old => new}/F.java`) are resolved correctly. |
| `compute_sonar_trend_features.py` | Uses shared `td_utils.parse_minutes` (old parser ignored `d`). |
| `td_utils.py` (new) | Sonar effort -> minutes: `1d2h30min`, `45min`, `2d`; 1 day = 8 h. |
| `weekly_commits.py` | Week = (start, start+7d] (old code dropped the 7th day). Added `midpoint_start_date()` and `available_weeks()`. |
| `config.py` (new) | `REPO_PATH`, `BRANCH`, `DEFAULT_WEEKS=120`; `KAFKA_REPO_PATH` kept as alias. **Copy your Sonar URL/token/Docker settings into it.** |
| `run_all_repos.py` | Blank `start_date` = repo midpoint; branch auto-detected; weeks capped to what exists; combine step no longer breaks on `held_repository`. |
| `run_pipeline.py` | `midpoint` start for a single local repo. |
| `repos.csv` (new) | commons-cli, commons-csv, commons-io, slf4j. |

Unchanged: `scan_*`, `pull_*`, `pipeline_total_line.py`, `add_weekly_commits_churn.py`, `pipeline_g3.py`,
`compute_ownership_entropy.py`, `compute_lineage.py`, `compute_finding_lifecycle.py`.

## Fix: numeric week ordering (compute_sonar_trend_features, compute_finding_lifecycle, compute_issue_persistence, merge_measures_issues)
`sorted()` on 'week_NN' strings put week_100..week_138 between week_10 and week_14, scrambling every
index-based rolling window once a run has 100+ weeks. Effects seen in td_mart.csv: T0 weeks 100-113 had
"6m history missing" and were dropped; week_114 had blank finding_arrivals_6m/closures_6m; windows for
weeks 120-126 mixed in old weeks; 6m windows for weeks 27-39 reached into weeks 100+ (future).
`td_utils.sorted_week_labels()` sorts numerically and fails on gaps. Verified on a synthetic 138-week fixture.

## Consistency release (td_pipeline_final)
| # | Change | Why |
|---|---|---|
| 1 | `weekly_commits.py`: T0 commit resolved with an explicit UTC timestamp (`--before=YYYY-MM-DDTHH:MM:SS+0000`) | A bare date makes git use the *current clock time*, so boundary-day commits were in/out depending on when each script ran |
| 2 | `pipeline_total_line.py` uses the shared resolver (own calendar removed) | One source of truth for which commit is T0 |
| 3 | `compute_git_window_features.py` buckets by **committer** date (UTC), not author date | A patch authored earlier but landed later was not in the repo at an earlier T0 (look-ahead leakage) |
| 4 | `add_weekly_commits_churn.py` reuses the same collector | `commits_g3`/`churn_g3` now always equal `commits_t0`/`churn_t0` (36 rows differed before: timezone + rename parsing) |
| 5 | `config.py` + `build_td_mart.py`: non-production filter extended (`examples/`, `samples/`, `benchmarks/`, `*-template/`, files named `*Benchmark*`, `*Example*`, `*Sample*`) | gson/jsoup/webgoat demo and benchmark code was counted as production |
| 6 | `validate_snapshots.py` (new): compares Sonar `lines` per file with Git line count per scanned commit; `--fix` deletes bad snapshots | Catches stale Sonar scans (webgoat weeks 32-34) |
| 7 | `run_all_repos.py`: git line counts first, scan, validate (auto re-scan once), then features | Stale scans are repaired automatically; run fails if they persist |
| 8 | `scan_snapshot.py`: accepts only an analysis that is NEW since the scan started, waits for the Compute Engine queue to drain, warns if Sonar's revision differs | Removes the "recorded the previous week's analysis" race |
| 9 | `scan_weekly_snapshots.py`: a week recorded with a different commit than now resolved is re-scanned (was: skipped); copies of a re-scanned source are refreshed | Existing runs stay consistent after change #1 |
| 10 | `build_td_mart.py`: prints a warning if any row has `ncloc_t0 > total_lines_g3` | Last line of defence |

# Module-level release
| File | Change |
|---|---|
| `modules.py` (new) | file -> module mapping (`build` / `package` / `auto`), frozen in `module_strategy.json`. |
| `build_module_mart.py` (new) | Aggregates the weekly Sonar snapshots + git per module. Writes `module_weekly_state.csv`, `module_latest_snapshot.csv`, `module_td_mart.csv`. Adds `sqale_index`, `sqale_debt_ratio`, `sqale_rating`, SQALE trends and `SQALE_3w/1m/3m` targets. |
| `weekly_update.py` (new) | Weekly collection wrapper (`run_all_repos.py --weekly-update --level module`). |
| `run_all_repos.py` | `--level module|file|both` (default module), `--weekly-update`, `--refresh-start`; local branch fast-forwarded to origin in weekly mode; **start_date pinned** in `repo_context.json`; combine step also writes `combined_module_td_mart.csv` / `combined_module_weekly_state.csv`. |
| `run_pipeline.py` | `--level module|file|both`. |
| `config.py` | `MODULE_STRATEGY`, `MODULE_PACKAGE_EXTRA_DEPTH`, `BUILD_DESCRIPTORS`, `DEV_COST_PER_LINE_MIN`, `SQALE_RATING_BOUNDS`. |
Unchanged: all scan/pull/validate scripts and every file-level feature script (still run with `--level file|both`).
See MODULE_LEVEL_README.md.
