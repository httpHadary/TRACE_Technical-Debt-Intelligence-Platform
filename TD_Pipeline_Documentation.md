# Technical Debt Prediction Pipeline — Documentation for the AI Team

> Historical file-level documentation. For the repaired module pipeline, use
> [MODULE_LEVEL_README.md](MODULE_LEVEL_README.md). In particular, implicit zero filling,
> destructive `--fix`, automatic rescanning, unpinned scanners and moving module splits
> described in older documentation are not the current module contract. Existing real data
> was not migrated or rescanned by this repair.

**What this produces:** a file-level, weekly regression dataset (`td_mart.csv` per repository, `combined_td_mart.csv` across repositories) for predicting **future Technical Debt Principal** of Java source files.

**Version described here:** `td_pipeline_final` (numeric week-ordering fix + consistency release; see §12).
**Status of verification:** the mart builder, git features, trend/lifecycle features and the calendar were tested on synthetic repos and fixtures. The SonarQube scanning steps were run by the data-engineering side (first run: `commons-io`); nothing in this document was re-run against the four target repositories yet.

---

## 1. The prediction problem in one paragraph

Every row is **one Java file at one weekly snapshot (called T0)**. The features describe the file at or before T0 (its Git history, its SonarQube findings and their trends). The targets are the file's **Technical Debt Principal** 3 weeks, 4 weeks (≈1 month) and 12 weeks (≈3 months) after T0.

```
TD_Principal = Bug remediation effort
             + Vulnerability remediation effort
             + Code Smell remediation effort
```

All three are SonarQube's estimated remediation effort, **in minutes**, summed over the file's **active** issues (status `OPEN`, `CONFIRMED` or `REOPENED`). One SonarQube day = 8 hours = 480 minutes.

| Target | Meaning |
|---|---|
| `TD_3w` | TD_Principal of the same file 3 weeks after T0 |
| `TD_1m` | TD_Principal of the same file 4 weeks after T0 |
| `TD_3m` | TD_Principal of the same file 12 weeks after T0 |

`technical_debt_minutes_t0` is TD_Principal **at T0** and is a *feature*. Future values are only ever targets.

---

## 2. Repositories

Chosen set (see `repos.csv`):

| Repository | Why it was chosen |
|---|---|
| `commons-lang` | Mature, many source files, steady activity |
| `jsoup` | Single module, very active |
| `gson` | Small, steady, different coding style |
| `webgoat` | Application (not a library) with intentionally insecure code → real vulnerability findings, so the *vulnerability* component of TD_Principal is non-zero |

Considered and rejected: `javalin` (~90 % Kotlin; the pipeline keeps `.java` only), `opensearch` (too large for ~138 SonarQube scans), `junit4` (maintenance mode, very few commits), `commons-codec` (small and low-activity; first backup), `calcite` (large, slow; second backup).

The first run used `commons-io` (low activity — see §11).

---

## 3. Time model (the calendar)

All repositories use the same calendar logic (`weekly_commits.py`):

| Quantity | Definition |
|---|---|
| **Midpoint** | Date halfway between the repo's first commit and its latest commit on the branch |
| **Week 1 start** | `midpoint − 26 weeks` (a 6-month warm-up so every long trailing window is full) |
| **Week k** | The interval `(start + 7(k−1) days, start + 7k days]` |
| **T0 of week k** | The **latest commit on the branch whose committer date is ≤ the end of week k** (UTC, resolved with an explicit timestamp so it does not depend on the clock time of the run) |
| **Run length** | 138 weeks by default = 26 warm-up + 100 T0 weeks + 12 horizon weeks |
| **T0 weeks that become rows** | Weeks **27 … 126**. Week 27 starts exactly at the midpoint. |
| **Warm-up weeks 1–26** | Used only as history. Never rows. |
| **Horizon weeks 127–138** | Used only to build targets for the last T0 weeks. Never rows. |

* A week with no new commit has the same T0 commit as the previous week. It is **not** re-scanned: its SonarQube snapshot (measures, issues, metadata) is **copied** from the previous week, so week numbers stay contiguous. Every rolling window downstream is index-based and requires contiguity; the scripts abort if a week is missing.
* `week_NN` labels must always be ordered **numerically**, never as strings (`week_100` sorts before `week_11` as a string). See §12.

---

## 4. Pipeline stages

Run per repository, in this order (`run_all_repos.py` orchestrates everything):

| # | Script | Input | Output (per repo working dir) |
|---|---|---|---|
| 0 | `run_all_repos.py` | `repos.csv` | Clones repo, picks branch, computes midpoint/start/weeks, writes `repo_context.json` |
| 1 | `scan_weekly_snapshots.py` → `scan_snapshot.py` | weekly commits | Checks out each weekly commit, runs SonarQube scanner (Docker), records `data/snapshots.csv` |
| 1a | `pull_metrics.py` | SonarQube API | `data/measures_week_NN.csv` — per-file Sonar measures |
| 1b | `pull_issues.py` | SonarQube API | `data/issues_week_NN.json` — every issue, all statuses |
| 1c | `pull_analysis_metadata.py` | SonarQube API | `data/analysis_metadata.csv` — analyzer/rule-set fingerprint |
| 1d | `validate_snapshots.py --fix` | measures + git line counts | Detects **stale Sonar scans** (Sonar `lines` ≠ Git line count for many files at one commit), deletes them and triggers one automatic re-scan; the run fails if they persist |
| 2 | `pipeline_total_line.py` (runs **before** the scan) | Git | `weekly_total_lines/week_NN.csv` — physical line count of every `.java` file at T0 |
| 3 | `add_weekly_commits_churn.py` | Git | adds per-week `commits`, `churn` to the above |
| 4 | `pipeline_g3.py` | step 3 | `weekly_g3_features/week_NN.csv` — adds `churn_rate` (and unused acceleration/burstiness columns) |
| 5 | `compute_git_window_features.py` | Git | `git_window_features/week_NN.csv` — the `*_t0` git features |
| 6 | `compute_ownership_entropy.py` | Git | `ownership_entropy/…` (**not used by the mart** — see §11) |
| 7 | `compute_lineage.py` | Git | `lineage/week_NN.csv` — stable file identity across renames |
| 8 | `compute_sonar_trend_features.py` | steps 1a/1b | `sonar_trends/week_NN.csv` — slopes/volatility over trailing windows |
| 9 | `compute_finding_lifecycle.py` | step 1b | `finding_lifecycle/week_NN.csv` — finding arrivals/closures |
| 10 | `build_td_mart.py` | all of the above | **`td_mart.csv`** |
| 11 | `run_all_repos.py` (combine) | each `td_mart.csv` | **`combined_td_mart.csv`** |

### SonarQube scan settings (consistent across all weeks)

* `sonar.sources=.`, `sonar.exclusions=**/test/**,**/generated/**,**/*.scala,**/build/**,**/vendor/**`
* Scanner: `sonarsource/sonar-scanner-cli` in Docker.
* **Analysis mode `SOURCE_ONLY`** (no compiled bytecode). Some Java rules only fire with bytecode, so absolute finding counts are lower than a compiled analysis. The mode is identical for all weeks, so trends and targets stay comparable. It is recorded in `analysis_mode`.
* `pull_issues.py` pulls **all statuses** (`OPEN, CONFIRMED, REOPENED, RESOLVED, CLOSED`), splitting queries by severity/type to stay under SonarQube's 10,000-result cap. Downstream code keeps **active** issues only (`OPEN, CONFIRMED, REOPENED`) for debt and finding counts.
* Issue effort is stored as the raw Sonar string (`5min`, `1h30min`, `2d`, `1d2h`) and converted by one shared parser (`td_utils.parse_minutes`): `d = 480 min`, `h = 60 min`, `min = 1`.
* `pull_metrics.py` fetches per-file measures (ncloc, lines, complexity, cognitive_complexity, duplication, comment density, violations, ratings, sqale_index, coverage, …). SonarQube omits some zero-valued file measures (`cognitive_complexity`, `duplicated_*`); for Java files with `ncloc > 0` these omissions are stored as `0` (`FILL_OMITTED_ZERO_MEASURES = True`).

---

## 5. How a row is built

For each T0 week 27…126 and for each file that Sonar measured at that T0 commit:

1. Take the file's Sonar measures and **active** issues at T0 → Sonar-state features.
2. Join the file's Git features, g3 features, lineage row, Sonar trend row and lifecycle row for the same week, keyed by file path.
3. Look up the **same lineage** at T0+3, T0+4, T0+12 weeks and sum that file's active-issue effort there → targets.
4. Apply eligibility and target gating (§8) and the row filters (§9).
5. Assign the chronological split (§10).

---

## 6. Column dictionary

The mart has **124 columns** (125 in `combined_td_mart.csv`, which adds `held_repository`). They are listed in file order.

Legend — **Role:** `ID` identifier / metadata, `FEAT` model input, `FILT` eligibility/filter flag, `TARGET` label (never an input), `SPLIT` split bookkeeping.

### 6.1 Identity and metadata

| Column | Role | Definition |
|---|---|---|
| `origin_id` | ID | First 20 hex chars of `sha1("{repository_id}:{file_path}:{t0_week_number}")`. Unique per row. |
| `repository_id` | ID | Repository name from `repos.csv`. |
| `artifact_id` | ID | File path (relative to repo root) at T0. |
| `lineage_id` | ID | Stable identity of the file across renames (§6.2). Use it to group rows of the same file. |
| `language` | ID | Sonar's language of the file (`java`). Constant. |
| `path_at_t0` | ID | Same as `artifact_id`. |
| `t0` | ID | Committer date (ISO-8601) of the T0 commit. |
| `week` | ID | Calendar week label `week_NN` (string). **Sort numerically.** |
| `commit_hash_t0` | ID | Git commit hash that was scanned for this week. |
| `sonar_analysis_key_t0` | ID | SonarQube analysis key of that scan. |
| `lineage_confidence` | FILT | `HIGH`, `AMBIGUOUS` or `UNSUPPORTED` (§6.2). |

### 6.2 Lineage (`compute_lineage.py`)

* Week 1: every `.java` file gets a lineage id = first 16 hex chars of `sha1("{project_key}:{path}")`.
* Between consecutive *distinct* weekly commits, `git diff -M -C --name-status` yields Added / Deleted / Renamed / Copied events (`.java` only).
  * **Rename:** the file keeps its `lineage_id` under the new path.
  * **Add:** new lineage id, confidence `HIGH`.
  * **Delete:** the lineage ends.
  * **Copy, or one source renamed to several targets:** confidence `AMBIGUOUS` (and it stays `AMBIGUOUS` for later weeks).
  * Files not touched by the diff carry their identity forward unchanged.
* The mart only trusts lineage with confidence `HIGH` or `MEDIUM` when matching a file to its future self (`MEDIUM` is never produced by the current lineage script, so effectively `HIGH` only).
* Targets use **only unambiguous mappings** (a lineage id that maps to exactly one path at the horizon week).

### 6.3 Analyzer contract (used to guard the targets)

| Column | Role | Definition |
|---|---|---|
| `sonarqube_version` | ID | `GET /api/server/version`. |
| `java_analyzer_version` | ID | Installed Java plugin `version + build`. |
| `quality_profile_id` | ID | Name of the project's active Java quality profile. |
| `quality_profile_hash` | ID | `sha256` over the sorted `(rule key, severity, params)` of every active rule in that profile. Equal hash ⇔ identical rule set. |
| `analysis_mode` | ID | `SOURCE_ONLY` (or `COMPILED` if `JAVA_BINARIES_PATH` is set). |
| `compatible_rule_domain_version` | ID | Constant `td-rule-domain-v1`. |

A target is **excluded** if T0 and the horizon snapshot differ in `sonarqube_version`, `java_analyzer_version`, `quality_profile_hash` or `analysis_mode`, because debt would no longer be comparable.

### 6.4 Eligibility flags

| Column | Role | Definition |
|---|---|---|
| `production_source_file` | FILT | `path` ends with `.java`, contains none of `/test/`, `/tests/`, `/generated/`, `/build/`, `/vendor/`, `/example(s)/`, `/sample(s)/`, `/benchmark(s)/`, `/jmh/`, `/template/`, `-template/`, and the file name is not `*Benchmark*.java`, `*Example*.java` or `*Sample*.java`. |
| `sonar_available_t0` | FILT | Always `True` (the file is in the T0 Sonar measures). |
| `history_complete` | FILT | `True` if `git_history_missing_t0 == False` **and** `td_history_missing_6m == False` **and** the file has a git feature row. |
| `eligible_t0` | FILT | `production_source_file AND history_complete`. |
| `exclusion_reason_t0` | FILT | `;`-joined reasons (`not_production_source_file`, `history_incomplete`). With default row filters the value is the string `NONE` for every kept row (§9). |

### 6.5 Size

| Column | Role | Definition |
|---|---|---|
| `ncloc_t0` | FEAT | SonarQube `ncloc` for the file at T0 — non-comment, non-blank lines of code. |

### 6.6 Git features, current week (`compute_git_window_features.py`)

The "current week" is the 7-day window `(T0 − 7 days, T0]` — the week that ends at T0. Merge commits are excluded. Dates are **committer dates in UTC** (the moment a commit actually entered the branch). Only commits dated ≤ T0 are ever read. History is walked once from the first commit, keyed by file path.

| Column | Role | Definition |
|---|---|---|
| `commits_t0` | FEAT | Number of commits touching the file this week. |
| `lines_added_t0` | FEAT | Lines added this week (Git `--numstat`). |
| `lines_deleted_t0` | FEAT | Lines deleted this week. |
| `churn_t0` | FEAT | `lines_added_t0 + lines_deleted_t0`. |
| `authors_t0` | FEAT | Number of distinct authors this week. |
| `file_age_days_t0` | FEAT | Days between T0 and the file's first commit under its current path. |
| `days_since_last_change_t0` | FEAT | Days between T0 and the file's last commit ≤ T0. |
| `churn_acceleration_t0` | FEAT | `churn(this week) − churn(previous week)`. Empty only for the first calendar week of the run. |
| `commit_burstiness_t0` | FEAT | Population variance ÷ mean of the file's **weekly commit counts for weeks 1…T0** (zero-activity weeks count as 0). `0` if mean ≤ 0 or fewer than 2 weeks. |
| `churn_burstiness_t0` | FEAT | Same formula on weekly churn. |
| `last_change_missing_t0` | FLAG | `True` if the file has no commit ≤ T0. `False` for every kept row. |
| `git_history_missing_t0` | FLAG | `True` if the repository's earliest commit is *after* the start of week 1 (i.e. the run starts before the repo has history). `False` under midpoint start. |

### 6.7 "g3" features (`pipeline_total_line.py`, `add_weekly_commits_churn.py`, `pipeline_g3.py`)

| Column | Role | Definition |
|---|---|---|
| `total_lines_g3` | FEAT | Physical line count of the file at the T0 commit (`git show commit:path`, including comments and blanks). |
| `commits_g3` | FEAT | Non-merge commits touching the file in the week. |
| `churn_g3` | FEAT | Lines added + deleted in the week. |
| `churn_rate_g3` | FEAT | `churn_g3 / total_lines_g3` (empty if `total_lines = 0`). |

`commits_g3` and `churn_g3` are **identical** to `commits_t0` and `churn_t0` (both come from the same collector). Keep one pair.

### 6.8 Sonar state at T0 (from the T0 snapshot only)

| Column | Role | Definition |
|---|---|---|
| `finding_count_t0` | FEAT | Number of **active** issues on the file at T0. |
| `finding_density_t0` | FEAT | `1000 × finding_count_t0 / ncloc_t0` — findings per 1,000 lines. Empty if `ncloc = 0`. |
| `bug_remediation_effort_t0` | FEAT | Sum of effort (min) of active issues of type `BUG`. |
| `vulnerability_remediation_effort_t0` | FEAT | Same, type `VULNERABILITY`. |
| `code_smell_remediation_effort_t0` | FEAT | Same, type `CODE_SMELL`. |
| `technical_debt_minutes_t0` | FEAT | **TD_Principal at T0** = sum of effort of all active issues. Equals the sum of the three columns above. |
| `technical_debt_density_t0` | FEAT | `1000 × technical_debt_minutes_t0 / ncloc_t0` — minutes of debt per 1,000 lines. |
| `blocker_finding_count_t0`, `critical_finding_count_t0`, `major_finding_count_t0`, `minor_finding_count_t0`, `info_finding_count_t0` | FEAT | Active issues by Sonar severity. Sum = `finding_count_t0`. |
| `code_smell_count_t0`, `bug_count_t0`, `vulnerability_count_t0` | FEAT | Active issues by type. Sum = `finding_count_t0`. |
| `complexity_t0` | FEAT | Sonar cyclomatic complexity of the file. |
| `cognitive_complexity_t0` | FEAT | Sonar cognitive complexity (0 filled when Sonar omits it). |
| `duplicated_lines_density_t0` | FEAT | % of lines in duplicated blocks (0 filled when omitted). |
| `comment_lines_density_t0` | FEAT | % of comment lines. |

### 6.9 Sonar trend features (`compute_sonar_trend_features.py`)

Each trend uses the **last *w* weekly snapshots ending at and including T0**, with *w* = 3 (`_3w`), 4 (`_1m`), 12 (`_3m`), 26 (`_6m`). Backward-looking only. The per-week series are:

* `DD` = active findings per 1,000 lines
* `TDD` = **hours** of remediation effort per 1,000 lines (`minutes / 60 / KLOC`) — note this unit differs from `technical_debt_density_t0` (minutes per KLOC)
* `CC` = `complexity / KLOC`, `CogC` = `cognitive_complexity / KLOC`
* `DP` = `duplicated_lines_density` (%)

The slope is the ordinary-least-squares slope against the week index `1…w` (units: change per week). Volatility is the population standard deviation of the series. If **any** point in the window is missing (file absent that week, or `ncloc = 0`), slope and volatility are empty.

For each suffix `{3w, 1m, 3m, 6m}` (36 columns):

| Column pattern | Role | Meaning |
|---|---|---|
| `finding_density_slope_{s}`, `finding_density_volatility_{s}` | FEAT | Trend / spread of `DD` |
| `technical_debt_density_slope_{s}`, `technical_debt_density_volatility_{s}` | FEAT | Trend / spread of `TDD` |
| `complexity_slope_{s}` | FEAT | Trend of `CC` |
| `cognitive_complexity_slope_{s}` | FEAT | Trend of `CogC` |
| `duplication_slope_{s}` | FEAT | Trend of `DP` |
| `td_history_points_{s}` | FLAG | How many of the *w* points exist (0…w) |
| `td_history_missing_{s}` | FLAG | `True` if the window is incomplete. `td_history_missing_6m` feeds `history_complete`. |

### 6.10 Finding lifecycle (`compute_finding_lifecycle.py`)

For window *w* ∈ {3, 4, 12, 26} weeks (suffix `3w`, `1m`, `3m`, `6m`), compare the set of **active issue keys on the file now (T0)** with the set *w* weeks earlier:

| Column | Role | Definition |
|---|---|---|
| `finding_arrivals_{s}` | FEAT | `|active now − active w weeks ago|` — issues active now that were not active then |
| `finding_closures_{s}` | FEAT | `|active w weeks ago − active now|` — issues active then that are gone now |

It compares only the two end points: an issue that appeared *and* was fixed inside the window counts as neither. Empty for the first *w* weeks of a run (not enough history); with the default row filter all kept rows are populated.

### 6.11 Targets

For each horizon *h* ∈ {`3w` (+3 weeks), `1m` (+4 weeks), `3m` (+12 weeks)}:

| Column | Role | Definition |
|---|---|---|
| `TD_{h}` | **TARGET** | TD_Principal of the same lineage at T0 + *h* weeks (minutes). A file that exists at the horizon with no active issues is an observed **0**. |
| `TD_{h}_status` | **TARGET** | `OBSERVED`, `UNKNOWN_OBSERVATION`, `UNKNOWN_LINEAGE` or `EXCLUDED` (§8). |
| `TD_{h}_exclusion_reason` | **TARGET** | `;`-joined reasons, or `NONE` for observed targets. |
| `bug_remediation_effort_{h}` | **TARGET** | Bug component of `TD_{h}`. |
| `vulnerability_remediation_effort_{h}` | **TARGET** | Vulnerability component. |
| `code_smell_remediation_effort_{h}` | **TARGET** | Code-smell component. |

`TD_{h} = bug + vulnerability + code_smell` for every observed row (verified: 0 mismatches). Also verified: `TD_{h}` of a row equals `technical_debt_minutes_t0` of the same lineage's row *h* weeks later (0 mismatches).

### 6.12 Leakage metadata and split columns

| Column | Role | Definition |
|---|---|---|
| `max_feature_ts` | SPLIT | Upper bound of every feature timestamp = the T0 commit date. Equal to `t0`. |
| `split_family` | SPLIT | `CHRONOLOGICAL`, or `REPOSITORY_HELD_OUT` for held-out repos in the combined file. |
| `partition` | SPLIT | `TRAIN`, `VALIDATION`, `TEST`, `PURGED`, `UNASSIGNED` (§10). |
| `fold_id` | SPLIT | `chrono_<partition>` or `repo_holdout`. |
| `held_repository` | SPLIT | Combined file only. The repo id if held out, otherwise `NONE`. |

---

## 7. Leakage rules (what is and is not allowed)

* **Features only read data dated ≤ T0.** Git windows, Sonar trends and lifecycle windows all look *backward* from T0. The suffixes on features (`_3w`, `_1m`, `_3m`, `_6m`) are **look-back windows**; the same labels on targets (`TD_3w`, `TD_1m`, `TD_3m`) are **look-ahead horizons**.
* **Future snapshots are read in exactly one place:** the target construction (and the lineage/analyzer check that decides whether a target is valid).
* **Never use as model inputs:** `TD_*`, `TD_*_status`, `TD_*_exclusion_reason`, `bug_/vulnerability_/code_smell_remediation_effort_{3w|1m|3m}`.
* **Do not use as inputs:** identifiers (`origin_id`, `artifact_id`, `path_at_t0`, `lineage_id`, `commit_hash_t0`, `sonar_analysis_key_t0`), `t0`, `max_feature_ts`, `partition`, `fold_id`, `split_family`, `held_repository`.
* The same file appears in many weekly rows. For cross-validation inside TRAIN, **group by `lineage_id`**, otherwise near-identical rows of one file land on both sides of a fold.

---

## 8. Target gating (per horizon, independently)

A target is `OBSERVED` only if all of the following hold. Otherwise it is left empty and gets a status:

| Reason string | Meaning |
|---|---|
| `t0_not_eligible` | The T0 row is not `eligible_t0` |
| `lineage_unsupported_or_ambiguous` | Lineage confidence is not `HIGH`/`MEDIUM` |
| `sonar_unavailable_at_horizon` | The file (via its lineage) is not in the horizon snapshot — deleted, renamed ambiguously, or moved |
| `analyzer_incompatible_t0_horizon` | Sonar version / Java analyzer / quality-profile hash / analysis mode changed |
| `horizon_not_scanned_yet` | The horizon week is beyond the scanned range |

Status precedence: `UNKNOWN_OBSERVATION` (if `sonar_unavailable_at_horizon`) → `UNKNOWN_LINEAGE` → `EXCLUDED`. **Missing targets are never imputed.**

---

## 9. Row filters (defaults in `config.py`)

| Setting | Default | Effect |
|---|---|---|
| `DROP_INELIGIBLE_ROWS` | `True` | Keep only `.java` production files with a full 26-week history behind them |
| `REQUIRE_ALL_TARGETS_OBSERVED` | `True` | Keep only rows whose `TD_3w`, `TD_1m` **and** `TD_3m` are all `OBSERVED` |
| `FILL_OMITTED_ZERO_MEASURES` | `True` | Store omitted zero Sonar measures as `0` |

Consequences with the defaults:

* There are **no empty cells** in the mart. Reason columns contain the literal string `NONE` (not a null). Some tools treat the string `None`/`NONE` as missing — read with `keep_default_na=False` or convert explicitly.
* The status/eligibility/flag columns are **constant** (all `OBSERVED`, `True`, `False`, …). Drop constant columns before training.
* The dataset only contains files that **survive at least 12 weeks** after T0. Files deleted or renamed within the horizon are filtered out (survivorship bias). Set `REQUIRE_ALL_TARGETS_OBSERVED = False` for the full dataset with per-horizon statuses, and filter each target on its own `*_status == "OBSERVED"`.

---

## 10. Train / validation / test split

Chronological, by T0 week, in `build_td_mart.py`:

1. List the distinct T0 weeks that have rows (`n`).
2. `TRAIN` = first 60 % of weeks, `VALIDATION` block = next 20 %, `TEST` block = remaining ≈20 %.
3. **Purge:** the first 12 weeks of the validation block and the first 12 weeks of the test block are labelled `PURGED`, so a training row's 12-week target window cannot overlap validation/test rows. `PURGED` rows must be dropped.

With the default 100 T0 weeks (27…126) the expected result is:

| Partition | T0 weeks | Count |
|---|---|---|
| TRAIN | 27 … 86 | 60 |
| PURGED | 87 … 98 and 107 … 118 | 24 |
| VALIDATION | 99 … 106 | 8 |
| TEST | 119 … 126 | 8 |

**Important:** because the purge is 12 weeks long, a run needs **≈100+ T0 weeks** to get usable validation and test sets. At 60 weeks, VALIDATION and TEST are empty. `build_td_mart.py` prints a warning if either is empty.

Repository hold-out: `run_all_repos.py --holdout-repos <id>` relabels all rows of those repos as `partition=TEST`, `split_family=REPOSITORY_HELD_OUT`, `fold_id=repo_holdout`, `held_repository=<id>` in `combined_td_mart.csv`. Suggested hold-out: `webgoat` (most different from the libraries).

---

## 11. Known limitations and data-quality notes

1. **Persistence baseline is very strong.** In the first run (`commons-io`), `TD_3w`/`TD_1m`/`TD_3m` equalled `technical_debt_minutes_t0` in 99.6 % / 99.4 % / 97.6 % of rows, and ~50 % of targets were exactly 0. Only ~1 % of rows had any commit in their week; 53 of 86 weeks reused the previous week's commit. Always report the **persistence baseline** (`TD_h = technical_debt_minutes_t0`) and consider modelling the **change** `TD_h − technical_debt_minutes_t0`. More active repositories were chosen to improve this.
2. **Constant / redundant columns.** Besides the constants in §9, `vulnerability_*` columns are 0 for libraries with no Sonar vulnerabilities (expected to vary for `webgoat`), and `commits_g3`/`churn_g3` duplicate `commits_t0`/`churn_t0`.
3. **Unused script outputs.** `compute_ownership_entropy.py` writes `ownership_entropy_180d`, but the mart builder does not read it. `pipeline_g3.py` also writes acceleration/burstiness columns that the mart ignores. Adding ownership entropy to the mart is a small change if the team wants it.
4. **Renames and file age.** Git history is keyed by path (no `--follow`). After a rename, `file_age_days_t0` and the Git history restart under the new path. Lineage (and therefore targets) does follow renames.
5. **Units differ between related columns:** `technical_debt_density_t0` is minutes/KLOC; the `technical_debt_density_*` slope/volatility columns are in hours/KLOC.
6. **SOURCE_ONLY analysis** under-reports findings that need bytecode; consistent across weeks but not comparable to a compiled analysis.
7. **Effort units.** 1 day = 8 hours is SonarQube's default; if a server uses a different working-day length the conversion in `td_utils.py` must change.
8. **Scan timing / stale scans.** `scan_snapshot.py` now accepts only an analysis that is new since the scan started and waits for the Compute Engine queue to drain. `validate_snapshots.py` additionally cross-checks every scanned commit against Git (Sonar `lines` vs Git line count). In the previous run, 11 webgoat files at weeks 32–34 showed stale Sonar numbers; with this release such snapshots are removed and re-scanned automatically.
9. **Restricted row set.** Test/generated/vendor/example paths and non-Java files are excluded; with the default filters only files with a full 26-week history and a surviving 12-week future remain.

---

## 12. Change log relevant to anyone who saw earlier outputs

| Issue | Effect | Status |
|---|---|---|
| Week labels sorted as strings (`week_100` before `week_11`) in the Sonar-trend and finding-lifecycle scripts | With 100+ weeks, rolling windows were scrambled: T0 weeks 100–113 lost their 6-month history and were dropped, week 114 had blank `finding_arrivals_6m/closures_6m`, windows for weeks ~120–126 mixed in old weeks, and 6-month windows for weeks 27–39 reached into weeks 100+ (future data) | **Fixed** with `td_utils.sorted_week_labels()` (numeric sort + gap check). Verified on a synthetic 138-week fixture: before the fix 81 wrong slopes / 14 weeks with missing history; after the fix 0. **Any mart built before this fix must be rebuilt** (`compute_sonar_trend_features.py`, `compute_finding_lifecycle.py`, `build_td_mart.py`; no re-scan needed). |
| Effort parser ignored the `d` (day) unit and could mis-read `1d2h` as 12 h | Under-/mis-stated debt for issues over one working day | Fixed — shared `parse_minutes` (`d = 480 min`) |
| Week window covered 6 days instead of 7 | Commits on the 7th day were never counted | Fixed — week = 7 days |
| T0 commit resolved with a bare date (`--before=YYYY-MM-DD`) | Git fills in the *current clock time*, so boundary-day commits were in or out depending on when each script ran (up to ~1 day of fuzziness, different scripts could disagree) | **Fixed** — explicit UTC timestamp, one shared resolver |
| Git features bucketed by author date | Commits authored in week *k* but landed later counted toward week *k* (look-ahead, 12 rows in the last check) | **Fixed** — committer date |
| g3 churn script dropped timezones without converting and used older rename parsing | `commits_g3`/`churn_g3` differed from `commits_t0`/`churn_t0` in 36 rows | **Fixed** — same collector |
| Stale Sonar scan (webgoat weeks 32–34: ncloc > physical lines) | Wrong T0 features for ~62 rows and wrong 3w/1m targets for neighbours | **Guarded** — `validate_snapshots.py` + automatic re-scan; scan waits for a *new* analysis |
| Demo/benchmark code counted as production (jsoup `examples/`, gson `metrics/` + `examples/`, webgoat `SampleAttack`) | Non-production files in the mart | **Fixed** — extended filter |
| Git rename paths (`a/{old => new}/F.java`) parsed wrongly in the git-window script | Lost history for renamed files | Fixed in `compute_git_window_features.py` (the g3 churn script still uses the older rename handling) |
| `held_repository` crashed the combine step | Combine failed with hold-out repos | Fixed |

Note on sorting: the `week` column is a string. When loading the mart in pandas, sort by `week.str[5:].astype(int)`, not by the string.

---

## 13. Suggested use for modelling

* **Inputs (≈90 columns):** all columns marked `FEAT` in §6, after dropping constant and duplicate columns.
* **One model per target** (`TD_3w`, `TD_1m`, `TD_3m`); train on rows where that target's `*_status == "OBSERVED"`.
* **Splits:** use `partition`; drop `PURGED`; use grouped CV on `lineage_id` inside TRAIN.
* **Baselines to beat:** (a) persistence `TD_h = technical_debt_minutes_t0`, (b) predicting the change from persistence, (c) per-repo mean.
* **Metrics:** MAE and RMSE in minutes, plus the same on the *delta* and on rows where the target changed (otherwise the many unchanged files dominate).
* **Heavy-tailed target:** consider `log1p` or modelling the delta.
* **Check generalisation across repositories** with the repo hold-out.

---

## 14. How to run

```bash
# prerequisites: Python 3 (pandas, numpy, requests), Git, Docker, a running SonarQube
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
# create a user token in SonarQube, then:
export SONAR_TOKEN=<token>          # PowerShell: $env:SONAR_TOKEN="<token>"

# optional hold-out: add --holdout-repos webgoat
python3 run_all_repos.py repos.csv --repos-dir <local_clone_dir> --output-dir ./runs
```

`repos.csv`:

```
repository_id,git_url,branch,start_date,weeks
commons-lang,https://github.com/apache/commons-lang.git,master,,
jsoup,https://github.com/jhy/jsoup.git,master,,
gson,https://github.com/google/gson.git,main,,
webgoat,https://github.com/WebGoat/WebGoat.git,main,,
```

Blank `start_date` = computed from the repo midpoint (§3). Blank `weeks` = 138. The branch falls back to the clone's default branch if the listed one does not exist.

Useful flags: `--skip-scan` (rebuild features and mart without rescanning), `--resume-from <repo>`, `--holdout-repos a,b`.

Outputs: `runs/<repo>/td_mart.csv` per repository and `runs/combined_td_mart.csv`. After the build, `build_td_mart.py` prints the number of rows per partition, how many targets were observed, and any column that still has blank cells.

**First thing to check after the first scan:** open one `data/issues_week_XX.json` and confirm `effort_minutes` holds real values (e.g. `"5min"`); empty values would make all debt 0.
