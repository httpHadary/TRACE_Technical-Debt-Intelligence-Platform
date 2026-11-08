# Phase 4.2.1: diagnostic-only Chronos hardening evidence

Source data: The Technical Debt Dataset V2, release 2.0.1; Valentina Lenarduzzi,
Nyyti Saarimäki and Davide Taibi (2019):
https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1
Derived past-context and diagnostic outputs retain attribution and CC BY-NC-SA 4.0:
https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: scoped replay of only 12 published failed contexts, raw quantile capture,
paired diagnostic repetitions and descriptive arithmetic on existing interval metrics.
Model-card license Apache-2.0; no weights redistributed.

[Diagnostic report](../../PHASE_4_2_1_DIAGNOSTIC_REPORT.md): Phase 4.2.1 PASS;
the original Phase 4.2 experiment remains PARTIAL and unchanged.

- `diagnostic_raw_quantiles.csv`: 12 contexts × 2 repeats × 90 native diagnostic steps;
  **not replacement forecast predictions** and not a newly scored cohort.
- `failed_context_inputs.json`: exact past-only requests for those 12 contexts.
- `diagnostic_summary.json`: every crossing step/magnitude, native endpoint values,
  input diversity, repeated equality, pins and source/runtime/resource identities.
- `published_interval_diagnostics.json`: all published macro strata with descriptive
  integer miss decompositions; no new label evaluation/calibration.
- `constant_precision_evidence.json`: observed saved raw collapse and float32 spacing;
  installed normalizer source hashes support a qualified scale/rounding explanation.
- `preservation.json`: original data/splits/forecasts/config/metrics/dependencies and
  published Phase 4.2 report/evidence remain byte-identical.
- Test XML, resources and `diagnostic_worker_manifest.json` (original worker receipt).
- Root `manifest.json`: checksums of actually published diagnostic evidence.

Replay uses the report's bounded diagnostic module, never the benchmark command.
Future hardening of quantile recovery is not applied retroactively to old forecasts.
