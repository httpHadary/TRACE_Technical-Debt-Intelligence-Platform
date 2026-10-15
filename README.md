# Module technical-debt pipeline

Start with [MODULE_LEVEL_README.md](MODULE_LEVEL_README.md) for the corrected missing-value,
evidence, calendar, output and compatibility contracts.

- [REPAIR_REPORT.md](REPAIR_REPORT.md): repair coverage and validation limits.
- [CHANGES.md](CHANGES.md): current repair and historical changelog.
- [TESTED_ENVIRONMENT.txt](TESTED_ENVIRONMENT.txt): tested dependencies.
- `tests/`: offline regression and end-to-end checks.
- [FORECASTING.md](FORECASTING.md): additive 90/91-day forecasting datasets,
  historical graphs, and reproducible M0–M2 evaluation commands.
- [M3_M4_DESIGN.md](M3_M4_DESIGN.md): causal TCN and GraphSAGE–TCN data interfaces.
- [MILESTONE1_REPORT.md](MILESTONE1_REPORT.md): implementation evidence and remaining gates.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Missing values remain missing. Offline software PASS is not scientific approval or permission
to rescan, train, or execute the separate TechDebt360 V3 experiment.
# MVP phase status

Phase 0 verification, Phase 1 ingestion and Phase 2 exact-target construction are available in
[`forecasting_mvp/`](forecasting_mvp/README.md). See
[`PHASE_2_IMPLEMENTATION_REPORT.md`](PHASE_2_IMPLEMENTATION_REPORT.md) for dataset
statistics, limitations and test evidence.
[`GITHUB_SYNC.md`](GITHUB_SYNC.md) documents the central repository and safe sync.

Phase 2.1 adds raw-SQL validation, independence diagnostics and a strict past-only
input boundary. See [PHASE_2_1_VALIDATION_REPORT.md](PHASE_2_1_VALIDATION_REPORT.md)
and [small evidence files](examples/phase2_1/README.md). The Phase 2 dataset and
splits remain frozen.

Phase 3 statistical baselines have been implemented and evaluated on those
frozen cohorts. See [PHASE_3_IMPLEMENTATION_REPORT.md](PHASE_3_IMPLEMENTATION_REPORT.md)
and [results](examples/phase3/README.md). Persistence, rolling mean and linear trend
are available through the offline `run-baselines` command. Full pretrained
benchmarks, CatBoost and dashboards remain outside this implementation.

Phase 4.1 now admits a separate CPU Chronos-2 Small runtime and a six-context
training/validation smoke test. See [PHASE_4_1_IMPLEMENTATION_REPORT.md](PHASE_4_1_IMPLEMENTATION_REPORT.md)
and [smoke evidence](examples/phase4_1/README.md). Phase 4.1 stopped at that
boundary; its separately authorized evaluation follows below.

Phase 4.2 evaluates the pinned Chronos model against the original baselines on
the unchanged validation, temporal-test and held-repository cohorts. See
[PHASE_4_2_IMPLEMENTATION_REPORT.md](PHASE_4_2_IMPLEMENTATION_REPORT.md) and
[comparison evidence](examples/phase4_2/README.md) for coverage, failure handling,
point/interval metrics and limitations. Later phases remain unauthorized.

Phase 4.2.1 hardens typed inference recovery and audits only the 12 previously
failed contexts. The original experiment remains frozen. See the
[diagnostic report](PHASE_4_2_1_DIAGNOSTIC_REPORT.md) and
[diagnostic evidence](examples/phase4_2_1/README.md). No benchmark was rerun.

Phase 5.1 adds an isolated [schema-v2 data foundation](forecasting_multilanguage/README.md): read-only source adapters, F0/F1 features, exact target-status construction and a strict past-only input boundary. [Implementation/data-readiness report](PHASE_5_1_IMPLEMENTATION_REPORT.md). F2 and the real non-Java pilot remain blocked; no training, inference or scans were run. Earlier experiments stay frozen.

Phase 5.2 pins three real development sources and their historical code states.
See the [preflight report](PHASE_5_2_PREFLIGHT_REPORT.md),
[candidate decision](REAL_PILOT_REPOSITORY_CANDIDATES.md),
[future collection plan](HISTORICAL_SCAN_EXECUTION_PLAN.md) and
[small metadata evidence](examples/phase5_2/README.md).
Collection remains blocked by explicit scope, live-domain, build/runtime and
resource gates. The new `forecasting_multilanguage.preflight` command only
inspects Git source metadata; it cannot run a build, scanner or model.
