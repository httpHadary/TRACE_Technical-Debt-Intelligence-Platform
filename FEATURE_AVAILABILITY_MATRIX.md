# Feature availability matrix — Phase 5

Date: 2026-10-15. **Design only; no feature matrix was constructed or model fitted.** Evidence definitions, source hash, read-only SQL and dataset limitations: [Phase 5 report](PHASE_5_RESEARCH_REPORT.md#local-evidence). The denominator below is the **raw 66,711 Sonar rows**, not training-ready states or independent time points. New schemas and past-only gates: [architecture](MULTILANGUAGE_ARCHITECTURE.md).

## Classification rules

- **VERIFIED AVAILABLE:** named raw values/identities were found and their stated coverage checked this run. They still require as-of, ancestry, domain and scope admission before use.
- **DERIVABLE:** a deterministic past-only computation is specified from existing or admitted inputs; it has not been materialized/validated as an MVP feature. Any unresolved quality prerequisite remains explicit.
- **MISSING:** the required semantic measurement or provenance is absent/unverified. A similarly named column or language profile does not establish it.
- **LEAKAGE RISK:** the naive source/use can reveal future outcomes or post-cutoff state. Exclude from predictors until independent historical event/version evidence and tests resolve it. A risk classification does not claim every stored value is actually contaminated.

Each proposed feature below has one primary classification. Current source availability and integration readiness are distinct. Unknown becomes null plus a missing-reason code, never debt=0.

## Raw snapshot coverage

Valid means SQLite integer/real, nonnegative; numeric text in a metric column must be separately parsed/validated, not silently accepted. Git numstats are a separate known text representation below. Observed zero is a real raw value, not an imputation.

| Raw metric | Classification | Valid nonnegative | SQL nulls | Observed zeros |
| --- | --- | --- | --- | --- |
| SQALE_INDEX | VERIFIED AVAILABLE | 66,711 | 0 | 31 |
| NCLOC | VERIFIED AVAILABLE | 66,685 | 26 | 0 |
| LINES | VERIFIED AVAILABLE | 66,685 | 26 | 0 |
| FILES | VERIFIED AVAILABLE | 66,685 | 26 | 0 |
| CLASSES | VERIFIED AVAILABLE | 66,683 | 28 | 0 |
| FUNCTIONS | VERIFIED AVAILABLE | 66,683 | 28 | 0 |
| STATEMENTS | VERIFIED AVAILABLE | 66,683 | 28 | 6 |
| COMPLEXITY | VERIFIED AVAILABLE | 66,683 | 28 | 6 |
| COGNITIVE_COMPLEXITY | VERIFIED AVAILABLE | 66,683 | 28 | 20 |
| CODE_SMELLS | VERIFIED AVAILABLE | 66,711 | 0 | 31 |
| BUGS | VERIFIED AVAILABLE | 66,711 | 0 | 3564 |
| VULNERABILITIES | VERIFIED AVAILABLE | 66,711 | 0 | 4460 |
| VIOLATIONS | VERIFIED AVAILABLE | 66,711 | 0 | 31 |
| SQALE_DEBT_RATIO | VERIFIED AVAILABLE | 66,711 | 0 | 31 |
| SQALE_RATING | VERIFIED AVAILABLE | 66,711 | 0 | 0 |
| DUPLICATED_LINES | VERIFIED AVAILABLE | 66,711 | 0 | 145 |
| DUPLICATED_LINES_DENSITY | VERIFIED AVAILABLE | 66,685 | 0 | 119 |
| COMMENT_LINES | VERIFIED AVAILABLE | 66,685 | 26 | 0 |
| DEVELOPMENT_COST | VERIFIED AVAILABLE | 66,711 | 0 | 26 |
| COVERAGE | VERIFIED AVAILABLE | 66,677 | 34 | 66677 |
| TEAM_SIZE | MISSING | 0 | 0 | 0 |
| BUSINESS_VALUE | MISSING | 0 | 0 | 0 |

`DUPLICATED_LINES_DENSITY`: 26 nonnumeric cells despite zero SQL nulls, so null-only checks are insufficient. `COVERAGE`: every numeric value is zero; instrumentation/import provenance is missing, so exclude it from the initial predictive feature set. `DEVELOPMENT_COST` is an analyzer estimate/setting-derived quantity, not actual spending. Native snapshot counts (`CODE_SMELLS`, `BUGS`, `VULNERABILITIES`) can be valid features at a matched past analysis; adding their efforts together does not preserve the maintainability target.

## Proposed feature and evidence matrix

| Feature / evidence family | Primary classification | Actual source and status | As-of/quality condition; disposition |
| --- | --- | --- | --- |
| Current maintainability stock | VERIFIED AVAILABLE | `SONAR_MEASURES.SQALE_INDEX`, 66,711 numeric values | Exact project+analysis+revision, known compatible domain and cutoff-state proof; core F0 |
| Historical observation identity/time | VERIFIED AVAILABLE | Existing `historical_debt.csv` analysis/revision/state timestamps | Existing audit limitations remain; exact UTC, no latest/nearest join |
| Native size: NCLOC, lines, files | VERIFIED AVAILABLE | 66,685 numeric rows each | Same snapshot and scope; null on 26 rows; F1 NCLOC/files |
| Cyclomatic/cognitive complexity | VERIFIED AVAILABLE | 66,683 numeric rows each | Preserve language/definition/domain; not identical latent constructs across languages; F1 |
| Classes/functions/statements | VERIFIED AVAILABLE | 66,683 numeric rows each | Optional, language-specific applicability flags; not required across all languages |
| Aggregate smell/bug/vulnerability counts | VERIFIED AVAILABLE | 66,711 numeric rows each; distinct categories | Same past analysis; F1; no conversion of count/probability to minutes |
| Duplication/comment measures | VERIFIED AVAILABLE | Coverage table above | Keep percentages vs counts distinct; F1 duplication density, others optional |
| Current debt ratio/rating | VERIFIED AVAILABLE | 66,711 numeric rows each | Derived from debt, size and analyzer settings; redundant with debt/NCLOC; optional ablation, not evidence of actual effort |
| Git project/SHA/parents/committer times | VERIFIED AVAILABLE | 153,994 records, existing Phase 1 Git export | Restrict to cutoff-reachable admitted lineage, reject inversions/unresolved boundaries; never infer online historical branch availability from today's tip |
| Raw file-change additions/removals | VERIFIED AVAILABLE | 1,142,878 text integer pairs, all parseable; Git keys resolve | Contains 23,321 conflicting keys; not yet a safe aggregate |
| Commits/active days in trailing30/90d | DERIVABLE | Deduplicated accepted Git SHAs and UTC times | Count unique events on cutoff ancestry; no change-row multiplicity; F1 |
| Distinct changed source paths in30d | DERIVABLE | Unique `(SHA,path)` records plus versioned production-file classification | Conflicting numstats do not justify double-counting paths; no future rename/path map; F1 |
| Days since last commit within90d; no-commit flag | DERIVABLE | Complete past Git window | No event in a verified complete window is zero activity, not missing history. Exact elapsed time is null when only a90d lower bound is known; flag censoring |
| Churn/additions/removals30/90d | DERIVABLE | Raw numstats or pinned first-parent `git diff --numstat` | **Blocked** until duplicate/conflict and merge/binary/rename policy checks pass; F2 only |
| Churn per KLOC / acceleration / burstiness | DERIVABLE | Reconciled event windows and known denominator | Defer beyond initial F2; no missing-to-zero, no incomplete-window acceleration |
| Distinct author IDs / ownership summaries | DERIVABLE | Past nonempty author identifiers | Counts identifiers, not certified unique humans; no raw identifiers in X; current mailmap must not rewrite past knowledge; defer |
| Repository/file age | DERIVABLE | Earliest verified reachable commit / admitted path lineage | Shallow history yields lower bound, not true creation age; file age requires rename proof; optional only |
| Native language distribution | VERIFIED AVAILABLE | Positive Java/js/php/css/web/xml NCLOC counts in report | Source-coverage evidence, not independent non-Java corpus. C# profile-only evidence is insufficient |
| Language proportions / dominant/mixed family | DERIVABLE | Same-cutoff production NCLOC by canonical analyzer language | Normalize only over known analyzed production scope; unknown denominator -> null, not0; F1 family metadata |
| Complexity per KLOC | DERIVABLE | Same-snapshot complexity and NCLOC | 1000×complexity/NCLOC only for positive known NCLOC; optional ablation |
| Debt changes at past30/60/90d lags | DERIVABLE | Exact past cutoff-state observations | Missing exact past state -> null; no nearest-date proxy; F0 uses30d change |
| Debt slope/SD over past90d | DERIVABLE | >=3 distinct measured states/analysis timestamps within `[t0−90d,t0]` | Actual elapsed-day OLS, equal weight per admitted observation, no replicated grid states as independent scans; F0 |
| Complexity/NCLOC/issue-count trends | DERIVABLE | Same compatible-domain sparse past observations | Same minimum-distinct-state gate; no slope across analyzer/scope reset; optional post-F1 ablation |
| Distinct scan/state/value counts; observation age | DERIVABLE | Existing provenance/context identities | Report all separately; repeated equal values can be real measurements, repeated carried states are not independent; F0 |
| Immutable server/plugin/rule/build domain | MISSING | V2 has quality profile metadata but no complete versioned bundle | Old archive remains legacy development-only for strict-domain claims. New snapshot manifests mandatory |
| Standalone Python/Go/C++/C#/TS historical stock | MISSING | No positive language-distribution evidence for those languages in V2; no newly admitted external archive | Capability docs are not historical measurements. Acquire separately |
| Per-language or per-file V2 debt stock | MISSING | `SONAR_MEASURES` has no path/language-keyed metric rows | Do not allocate aggregate debt by NCLOC share or spread it over files |
| Actual developer repair hours / business criticality | MISSING | No validated matching repair-effort or criticality labels | SQALE/Jira estimates are not observed repair labor. No arbitrary criticality scores |
| Genuine historical test coverage | MISSING | Raw zeros exist but test/instrumentation history is unverified | No assertion that zeros mean no tests; omit initial feature |
| Stars/forks/downloads/team size as of t0 | MISSING | No timestamped historical service snapshots; `TEAM_SIZE` contains no numeric observations | Today's GitHub metadata is not a past feature. Static source license/URL used for eligibility, not X |
| Final Sonar issue status/severity/effort | LEAKAGE RISK | 1,024,614 issue records exported over their lifecycle, not full immutable per-scan issue snapshots | Final fields may include later edits/suppressions/rule changes; do not reconstruct old active debt with current values |
| Issue arrivals/closures / open counts from lifecycle export | LEAKAGE RISK | Creation/close analysis references exist but do not certify versioned issue attributes or intermediate reopenings | Same-cutoff aggregate measures are safe alternative; lifecycle feature requires event-time snapshots and availability proof |
| Jira status/resolution/fix version/time spent | LEAKAGE RISK | 61,402 records, creation/update/resolution and final values | A creation date does not make the final row available at creation. No full as-of changelog verified |
| Refactorings as known pre-cutoff events | DERIVABLE | 362,253 mined rows with commit identities | Requires past parent-diff validation and deduplication; mining version/provenance must be fixed; optional, not initial pilot |
| SZZ/future-fixing-commit or future defect labels | LEAKAGE RISK | 52,428 SZZ links use later fixing history | Never put eventual bug-introduction/fix knowledge into X; separate task labels if studied later |
| Unrestricted numeric selection from legacy wide marts | LEAKAGE RISK | Older module/NPF marts mix current features, combined-effort values and future label fields | Strictly project allowed past columns; no dataframe-wide numeric-column shortcut |
| Three-category combined remediation stock | DERIVABLE | Same-cutoff maintainability/reliability/security effort measures where admitted | A separate composite estimand, not native SQALE or actual labor; excluded from the primary target |
| `TD_*`, future paths/efforts, target availability, partition/holdout role | LEAKAGE RISK | Labels/evaluation metadata in wide marts and split registries | Keep in label/evaluation stores; rejected by model-facing allowlist |
| Nearest/latest Sonar values, bidirectional fill, future interpolation | LEAKAGE RISK | Legacy nearest-value helper and ordinary dataframe fills | Do not use for either feature or ground-truth state reconstruction |
| Learned embeddings/pretrained TD classifier scores | MISSING | Not registered historical features for the new cohort | Existing Java-specific classifiers do not establish multilingual label validity; no model execution or probability-to-effort conversion |

## Frozen proposed first feature groups

These are **column specifications**, not measured feature values. Each value also carries `missing_reason` and source dependencies in the feature-evidence store. No transformation is fitted in this phase.

**F0 — debt/history control:**

```text
debt_minutes_t0
debt_observation_age_days
distinct_debt_states_90d
distinct_debt_analyses_90d
debt_change_30d
debt_ols_slope_90d
debt_std_90d
```

**F1 additions — first useful supervised experiment:**

```text
ncloc_t0
files_t0
complexity_t0
cognitive_complexity_t0
code_smells_t0
bugs_t0
vulnerabilities_t0
duplicated_lines_density_t0
commits_30d
commits_90d
active_commit_days_30d
changed_source_paths_30d
days_since_last_commit_in_90d
no_commit_in_complete_90d
scope_language_family
```

**F2 optional additions — only after churn gate:**

```text
lines_added_30d
lines_removed_30d
churn_30d
lines_added_90d
lines_removed_90d
churn_90d
```

Missing indicators/reasons accompany F0/F1/F2; they are derived from **past input observability only**, never whether future labels exist. Do not include current repository ID/URL/path, raw author IDs, future-label status, split role, or high-cardinality analysis/domain hashes as predictors. Analyzer/language manifests remain control/provenance fields; only the low-cardinality `scope_language_family` is a model covariate in F1. Different metric semantics are stratified, not solved by feeding a hash into a tree model.

## Exact derivation and missingness rules

Git event windows are `(t0−L days,t0]` in UTC, with L=30 or90. Trend windows include endpoints `[t0−90d,t0]`, require >=3 distinct measured source states and timestamps, and use elapsed days; copied daily positions are excluded from the independent-observation count. Counts of commits with equal timestamps still use unique SHAs; ties preserve validated ancestry order. Refuse complete-window claims when parents/history are unresolved, a shallow boundary intrudes or a relevant timestamp inversion is unresolved.

Churn means additions+removals for admitted nonbinary production-source file changes against the **first parent**, with a separate documented root-commit empty-tree policy and each merge counted once under that same first-parent difference. Deleted source files are classified from their parent tree; new files from the child; renames follow pinned Git detection options or a disclosed no-renames add/delete convention. Do not silently mix the legacy no-merge convention. A binary/unparseable file delta is null for that affected aggregate, with missing/binary counts; it is not0. Raw conflicting duplicate keys must be resolved against immutable Git objects, not deduplicated arbitrarily. If a relevant event cannot be reconciled, mark the affected window missing. The primary F1 experiment can proceed without F2.

Current debt requires an exact cutoff-state observation or a proved unchanged state with the same admitted domain and no intervening unmeasured change. Past30-day lag has its **own** state proof; lack of that proof gives null lag/change, not current debt carried backward. Legitimate observed zero debt is retained. Nonpositive/unknown ratio denominator gives null plus reason. Invalid tokens (`None`, empty, nonfinite) are missing/bad-source values rather than zero. If a feature is wholly absent in development, freeze its transform as dropped and record the policy before final inference; do not learn a global imputer from test rows.

Operational mode requires both event/state time and actual input availability <=t0. Retrospective fixed-analyzer reconstruction permits later computation from a past immutable state but must explicitly label its availability assumption. It cannot support an online historical availability claim. See the architecture's dual-clock contract.

## Pilot priorities and unresolved gates

F0/F1 is the smallest useful comparison: it tests debt history against debt history plus Git activity/size/complexity/categories without relying on unsafe churn or mutable lifecycle fields. Add F2 only when every included churn aggregate has a conflict-resolution or explicit-missing provenance record. Do not wait for all proposed features, all seven languages or pretrained embeddings before proving the data contracts.

No feature performance, improvement, cross-language transfer or error reduction has been measured in Phase5. Feature availability is not predictive value. Feature-group ablations, model selection and confirmatory claims follow the [proposed protocol](PHASE_5_RESEARCH_REPORT.md#confirmatory-evaluation-protocol--proposed-not-executed) only after new authorization.
