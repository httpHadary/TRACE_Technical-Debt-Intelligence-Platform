# Focused offline multi-language validation — 2026-11-03

**PASS: fixture-backed ingestion → target separation → persistence → HTTP API →
rendered dashboard. Real Sonar measurements remain unverified.**

Implementation is unchanged at `990d3f3aafa3e31f585519e55af62f1b1dbc3bb7`.
No authentic Python or JS/TS native export was found in the bounded existing
Phase 5.2/5.2.1/6.6 and multi-language validation evidence. Those readiness records
still report zero native measurements. This does not assert absence from every
private archive. We reused the existing explicitly SYNTHETIC, Sonar-shaped
fixture builder and the 421-test verification already recorded for this exact
commit; the full regression suite was not repeated.

| Fixture case | Maintainability SQALE | Total principal | Result |
| --- | ---: | ---: | --- |
| Python | 12 min | 16 min (12 + 2 + 2) | Both targets pass end to end |
| JavaScript + TypeScript | 12 min | 16 min (12 + 2 + 2) | Both targets pass end to end |
| Python, security effort absent | 12 min | Unavailable | Missingness retained end to end |

These are invented **fixture values**, not Click measurements. All bundles and
screens show `SYNTHETIC` / `SOFTWARE_VALIDATION_ONLY` provenance. NCLOC values are
also fixture data. Project effort was never allocated using language shares.

Six bundles were built through the real `persistence-ingest-native` CLI and
verified through semantic replay. Each has three origin-history observations
and six persistence endpoints; SQALE/principal IDs are disjoint. Forecasts repeat
the selected stock with zero projected change when available and null intervals.
Eighteen direct HTTP API requests checked history, forecasts and pending or
unavailable evaluations. The actual dashboard then loaded the same bundles in
already installed cached Chromium. All six target/case combinations rendered
correct target names, stocks, language coverage, provenance and history; revision
step 3 and elapsed day 30 selections passed. All six registered horizon options
were present. No browser page errors or external browser requests occurred.

The browser's first validation-harness attempt hit CSP's string-evaluation
restriction. Locator assertions fixed the harness; CSP stayed enabled, the
already-created bundles/API results were reused, and no product code changed.
The successful browser receipt supersedes that harness attempt. Screenshots were
captured for all six cases; JS/TS principal and missing-security principal were
also visually inspected. Existing integration tests already cover Java and mixed
repositories; those completed checks were reused, not rerun or relabeled as real.

Evidence:

- [Machine-readable result](result.json), [API receipt](api_receipt.json),
  [rendered-browser receipt](browser_receipt.json).
- [JS/TS dashboard screenshot](jsts-principal.png),
  [missing-security dashboard screenshot](python-missing-security-principal.png).
- [CLI/fixture runner](run_offline.py), [browser check](browser_check.py).
  The published runner combines the successful fixture/API flow and corrected
  browser assertions, accepts a fresh output path and explicit browser Python,
  and does not install dependencies or download browsers.

Unverified: authentic scanner/CE completion, installed analyzer coverage and
Standard-mode semantics on real projects, real SQALE/principal values, actual
source coverage, operator permissions, export normalization from live responses,
and forecasting accuracy. Fixture-authored scope/reviewer/domain/completion
claims are not real evidence. API future actuals are correctly pending.

No scans, historical replay, model runs, image pulls, installs, server starts or
product changes were performed. SHA-256 checks confirm tracked code/tests and the
pre-existing validation measurements are unchanged. Frozen historical source
artifacts are checked separately in [preservation receipt](preservation.json).
The local validation HTTP servers and Chromium were stopped after the check.

A single small Python scan was separately prepared locally, not executed. The
cached Sonar images exist; `td-target-sonar` is stopped and its configured port
19003 refuses connections. No Sonar token/endpoint is set in the current process
environment; authentication and Execute Analysis permission are unverified.
Concrete one-scan/server approval is not recorded. The plan pins the newest
cached Click snapshot, identifies its upstream-recency limit, preserves the old
Sonar volumes and specifies prerequisites, bounds and both-target consumption of
a single export. No JS/TS or mixed scan setup is prepared yet.

Publication note: sealed `registry/` artifacts and screenshots are byte-identical
to the successful local run. Unsealed `cases.json` and `result.json` use relative
bundle paths for portability; their measurements and results are unchanged.
[Reproduction instructions](README.md) describe the portable validation runner.
