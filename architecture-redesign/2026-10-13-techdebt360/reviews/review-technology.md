# Technology and forecasting reviewer gate

Reviewed 2026-10-13: architecture spine, `OPTIMAL_SYSTEM_ARCHITECTURE.md`, `DATASET_AND_FORECAST_FEASIBILITY.md`, and `digests/forecast-models.md`; inspected code-model digest and the exact local runtime/manifests for supporting checks. This is the independent current-technology floor lens, not the complete rubric/security/data review. No design, source or configuration edits; no installs, scans or inference.

**Verdict: conditionally sound research architecture; resolve the cadence/endpoint contract before a forecasting handoff.** No critical technology finding. One high and four medium findings below. The named checkpoints exist, and the architecture correctly treats their utility as unproven, preserves task semantics and separates incompatible runtimes. No forecast accuracy winner or minimum hardware guarantee is justified.

## High

### T1 — Calendar endpoint is not yet bound to native forecast steps

**Locations:** `OPTIMAL_SYSTEM_ARCHITECTURE.md:123`, `:160`; spine AD-6/AD-7; `DATASET_AND_FORECAST_FEASIBILITY.md:67`, `:80`.

The API asks for `horizon_days`, but foundation-model horizons are integer observations. The feasibility proposal collects weekly histories plus exact90 supplemental endpoint scans. A weekly origin's 13th future point is 91 days, not 90; merely acquiring a 90-day label does not make the native weekly model forecast that time. Imported V2 also has irregular commit observations. The current rule says “actual cadence” but does not bind how an adapter handles a non-integral endpoint or irregular/missing origin history. Two builders could silently treat irregular scans as equally spaced, round 90/7, interpolate model output, or switch to daily padding, all producing different scientific tasks while appearing compliant.

**Evidence:** both Chronos configs express patch/output lengths in observations; TimesFM 2.5 receives 1D arrays and horizon counts; Toto 1.0 README says timestamp information is expected by the API but unused by that model release. [Chronos config](https://huggingface.co/amazon/chronos-2/raw/main/config.json) (Amazon, undated; accessed 2026-10-13), [TimesFM card](https://huggingface.co/google/timesfm-2.5-200m-pytorch) (Google, updated 2025-10-02; accessed 2026-10-13), [Toto README](https://raw.githubusercontent.com/DataDog/toto/main/README.md) (Datadog, updates February/April 2026; accessed 2026-10-13). These are observed publisher contracts, not independent performance evidence.

**Resolution — discuss then bind:** registry/target contract must include frequency/step duration, grid anchor, native step count, supported missingness treatment, context selection and exact endpoint mapping. Reject adapters when `(endpoint-origin)/step` is non-integral unless an explicitly named and evaluated mapping method is part of the experiment. Keep weekly approx91 in its own task; exact90 requires a compatible cadence or a distinct endpoint regression/irregular-time adapter. Document any input imputation using only origin-available values and retain observed masks; no input transformation creates additional measured history or target ground truth. No benchmark execution is needed to correct the design.

## Medium

### T2 — Universal 90% interval gate exceeds some native quantile contracts

**Locations:** `DATASET_AND_FORECAST_FEASIBILITY.md:69`; `digests/forecast-models.md`, model contracts and benchmark protocol.

The proposed shared gate requires calibrated 90% intervals. TimesFM 2.5, the checked TTM-r3 configuration and Moirai 2.0 natively expose deciles 0.1–0.9; their central native interval is 80%, not 90%. Chronos configurations include 0.05/0.95 and Toto samples permit those quantiles. Adapters could invent tail quantiles or unfairly disqualify decile models without a stated policy. “Separate calibration evidence” is the right general invariant but does not yet specify this gate's construction.

**Evidence:** [TimesFM config](https://huggingface.co/google/timesfm-2.5-200m-pytorch/raw/main/config.json) (Google), [TTM config](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r3/raw/main/config.json) (IBM), [Moirai config](https://huggingface.co/Salesforce/moirai-2.0-R-small/raw/main/config.json) (Salesforce); undated inspected configs, all accessed 2026-10-13.

**Resolution — clear design fix:** use native shared 80% coverage/width and decile losses for the common comparison, or preregister a validation-only calibration layer for a separate 90% deployment claim. Unsupported tail quantiles stay null. Never relabel a 0.1–0.9 interval as 90%.

### T3 — Exact model runtime profiles belong in the integration gate, including existing tabular conflicts

**Locations:** spine Stack/AD-7; `OPTIMAL_SYSTEM_ARCHITECTURE.md:68`, `:126`, `:180`; digest dependency sections.

Runtime isolation is already the correct binding decision. The remaining handoff must retain concrete package constraints, not imply that all optional research adapters inherit the Python/CatBoost seed. Local `requirements-forecast-lock.txt` uses NumPy 2.4.4, pandas 3.0.2 and scikit-learn 1.8.0. Current Uni2TS manifest pins NumPy ~=1.26.0 and Torch >=2.1,<2.5; Toto docs require Torch >=2.5 and current requirements pin 2.7.0; current Granite manifest requires Torch >=2.10,<2.12 and scikit-learn <1.8. Package manifest declarations establish these conflicts, not proof that any complete environment works.

**Evidence:** local `td_pipeline_module_level/td_pipeline/requirements-forecast-lock.txt`; [Uni2TS manifest](https://raw.githubusercontent.com/SalesforceAIResearch/uni2ts/main/pyproject.toml), [Toto requirements](https://raw.githubusercontent.com/DataDog/toto/main/requirements.txt), [Granite manifest](https://raw.githubusercontent.com/ibm-granite/granite-tsfm/main/pyproject.toml) (Salesforce/Datadog/IBM, undated current sources; accessed 2026-10-13).

**Resolution — defer with explicit activation check:** preserve one adapter-specific lock/image profile per incompatible runtime, lock tokenizer/code SHA alongside weights, and require smoke-load/schema/missingness/resource verification before an adapter is eligible. Do not install or execute them during this design task. A compact profile matrix should be incorporated into the model research companion, including the existing CatBoost runner.

### T4 — Research-only route requires a role that is not declared

**Locations:** `OPTIMAL_SYSTEM_ARCHITECTURE.md:146`, `:160`; spine consistency conventions.

Declared roles are reader/analyst/approver/admin, while the forecast route permits `RESEARCH_ONLY` under an “explicit research role.” There is no defined role or permission mapping. A builder could expose experimental predictions to every analyst; another could make the endpoint permanently unreachable. This directly affects the scientific-validation boundary and demonstration behavior.

**Resolution — clear design fix:** define an explicit research-execution permission granted to a named existing role or add a research role consistently. Require explicit research mode on requests and returned records, and label research outputs in a separate view; normal dashboards continue to require `VALIDATED`.

### T5 — Restore and capacity envelope lacks a measurable acceptance boundary

**Locations:** `OPTIMAL_SYSTEM_ARCHITECTURE.md:75`, `:176`, `:180`, `:184`.

Deployment, authentication, sandboxing, observability and backups are covered; no whole operational dimension is absent. However, 100GB is correctly only a reservation, and retention of frozen artifacts, build dependency caches, model weights and SQLite backup pairs has no capacity/backpressure rule. Restore verification checks hashes, but does not define handling of restored active leases or still-running external CE tasks. Two implementations could resubmit the same scan after a restore or exhaust disk while publishing a cohort.

**Resolution — discuss operational target:** name backup RPO/RTO and maximum cohort/artifact budget as assumptions to validate during the first pilot. Bind low-space refusal before scan/model launch and cohort publication; reserve staging/backup headroom; reconstruct or quarantine RUNNING/WAITING_EXTERNAL jobs after restore until external-task reconciliation completes. Select SQLite online backup or a quiesced consistent-copy strategy with the referenced blob manifest, rather than implying an arbitrary live DB file copy. [SQLite corruption guidance](https://www.sqlite.org/howtocorrupt.html) (SQLite project, living documentation; accessed 2026-10-13) documents the danger of backup/copy while a transaction is active.

## Verified decisions and retained limitations

- FastAPI 0.142.2 is a real current release dated 2026-09-30; its proposed use is a seed, not a tested integrated runtime. [Official release](https://github.com/fastapi/fastapi/releases/tag/0.142.2) (FastAPI, 2026-09-30; accessed 2026-10-13). API dependency compatibility is explicitly deferred, which is appropriate here.
- Local runtime checks returned Python 3.12.3 and SQLite 3.45.1; `techdebt360_v3_analyzer_domain_v152/pyproject.toml` declares td360-v3 0.15.2 and Python >=3.11. The CatBoost 1.2.8 seed matches the retained lock. These are inspected environment/source facts, not upgrade recommendations.
- Single-host SQLite and short transactions fit the declared deployment; the single-writer limitation and network-share restriction are correctly explicit. [SQLite transactions](https://www.sqlite.org/lang_transaction.html) (SQLite project, updated 2026-02-18; accessed 2026-10-13).
- Qwen7B first candidate and optional CodeRank retrieval are task-aligned research choices supported by the code-model digest; no existing finding path depends on an unlicensed specialist. The 24GB/quantized envelopes are labeled estimates, and CPU generation may be disabled.
- All six exact forecast IDs expose weights/configs. TTM-r3's main 512→30 is not the entire family; the checked 512→96 branch is valid metadata evidence. The digest appropriately labels other branch catalogue entries as publisher declarations and defers their runtime test.
- Moirai's noncommercial weight license and independent-univariate limitation are respected. TimesFM 2.5 XReg is distinct from TimesFM 3.0 native multivariate support. Toto 1.0 import/runtime paths remain distinct from current Toto 2.0. No model's telemetry pretraining is treated as proof of maintainability-minute validity.
- The forecast digest's approximate Moirai token-equivalent context is explicitly an estimate, not a guaranteed raw API maximum. No hard Toto context maximum was established, and the digest correctly avoids calling that unlimited capacity.

No inferred requirement for an upgrade, new vector database, Java rewrite, microservices or additional model is supported by this review. The principal missing consistency rule is the calendar-to-step bridge, followed by shared uncertainty semantics; fixing those makes the proposed conditional research track reviewable without executing it.
