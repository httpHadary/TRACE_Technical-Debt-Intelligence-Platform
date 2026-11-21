# Two TD pipelines compared

- **Team pipeline** = `td_pipeline_final` (the 30-script, file-level pipeline with `build_td_mart.py`)
- **Our pipeline** = `td_pipeline.py` + `history.py` + `build_mart.py` (this folder)

## Short answer: one pipeline, not two

Don't run both and join their columns. They measure the code in different ways (different weeks,
different scan mode, different files, different rule sets), so a team-pipeline column next to one of
ours would describe a *different measurement* of the same file. Instead, our pipeline now has
**one extra step, `history.py`**, which adds the requested columns at **all three levels** from the
data we already collect, plus the good ideas of the team pipeline (lineage, targets with a status,
stale-scan check, analyzer fingerprint).

## Differences

| Topic | Team pipeline | Our pipeline | Why it matters |
|---|---|---|---|
| Levels | File only | **Project, module, file** (same columns, `level` column) | Module/project forecasting needs the same features |
| Weeks | Own calendar: repo midpoint ± 26-week warm-up, 100 T0 weeks, 12 horizon weeks | Paper's exact commits (`align_paper.py`) or regular weekly commits | Ours can be checked against the paper; theirs can't |
| Build | **No build** (`SOURCE_ONLY` scan) | Built with JDK 8 / Maven 3.6.3, scanned with bytecode (like the paper) | Several Java rules need bytecode → theirs finds fewer issues |
| Files scanned | Everything under the repo root except tests/generated/examples | `src/main/java` of every module | Different file sets → different ncloc and TD |
| Quality profile | Server default (today: **Sonar way core**, 274 rules) unless changed | **Sonar way comprehensive** (618 rules) | With core, retrofit had a flat 8 code smells for 99 weeks. Their "TD unchanged in 99.6% of rows" finding may partly come from this |
| TD definition | Sum of effort of open issues per file (issues API) | `sqale_index + reliability + security remediation effort` (measures API) | Same idea, different source; ours adds up exactly file → module → project |
| CK metrics | None (needs compiled code) | CKJM Extended, **LOC-weighted like the paper** | Paper's key feature `Ca` is CK |
| Halstead | None | Yes (keyword-counting bug fixed) | |
| Git windows | This week only + burstiness over all history | 21/30/90/180 days + weekly lags/changes | Requested windows |
| Look-ahead in git | Walks from the newest commit and keeps commits *dated* ≤ T0 | Also requires the commit to be **reachable from the T0 commit** | A side-branch commit merged after T0 leaked into their T0 rows (tested) |
| Lineage | File renames between weeks | File renames **+ history follows renames + module lineage** | |
| Targets | `TD_3w/1m/3m`, gated by analyzer fingerprint | `target_td_3w/1m/3m` + status at all 3 levels; fingerprint recorded per run | Same horizons (3, 4, 12 weeks) |
| Row filters | Drops rows without all 3 targets and without 26 weeks of history | Keeps every row, with status/flags | Theirs keeps only files that survive 12 weeks (**survivorship bias**); filter at modelling time instead |
| Train/test split | Built in (60/20/20, 12-week purge) | Not built in | Their purge rule is good - reuse it in modelling |
| Checks | Stale-scan check | 27 automatic checks incl. stale scans, keys, lag/target correctness, cross-level sums, paper comparison | |
| Week labels | `week_NN` strings (had a sorting bug, fixed) | ISO dates | No string-sort risk |
| Non-production code | Excludes `examples/`, `samples/`, benchmarks | Keeps the `samples` module (the paper did too) | Drop `module == "samples"` at modelling time if wanted |

## What we took from the team pipeline

1. **File lineage** (`lineage_id`, `lineage_status`, `lineage_confidence`) - follows renames; AMBIGUOUS files get no targets.
2. **Targets with a status** instead of silently dropping rows.
3. **Stale-scan check**: SonarQube's line count per file must equal git's for that commit (`validate.py --repo`).
4. **Analyzer fingerprint**: SonarQube version + quality profile + hash of its active rules, written to `analysis_meta.csv` every run.
5. Their feature definitions where they exist (burstiness = variance/mean, knowledge fragmentation = author entropy, complexity per KLOC slopes).

## What the team pipeline should take from ours (if they keep using it)

1. Set the quality profile explicitly (comprehensive) - check `quality_profile_id` in their mart.
2. Only count commits reachable from the T0 commit.
3. Keep all rows and filter per target status, to avoid survivorship bias.
4. CK metrics need a build; source-only scans can't give them.
