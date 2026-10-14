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
are available through the offline `run-baselines` command. Pretrained models,
CatBoost, dashboards and Phase 4 remain outside this implementation.
