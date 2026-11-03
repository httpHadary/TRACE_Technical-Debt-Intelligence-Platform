# Offline multi-language end-to-end evidence

Fixture-backed verification of the implementation at `990d3f3`, recorded
2026-11-03. No real SonarQube measurement or forecast-accuracy claim is made.

[Report](REPORT.md) · [Result receipt](result.json) ·
[Browser receipt](browser_receipt.json) · [JS/TS screenshot](jsts-principal.png)

The checked-in bundles cover Python, JavaScript + TypeScript, and Python with
missing security effort. Each case has distinct SQALE and total-principal
bundles. The CLI, persistence values/seals/replay, 18 direct API requests, and
actual rendered dashboard passed. Screenshots cover all six bundles. Existing
421-test results were reused at the matching implementation commit, not rerun.
Real Click measurement validation remains blocked by the stopped SonarQube
service and unavailable authenticated scan environment; no scans ran.

## Inspect existing evidence without scans

From the repository root:

```bash
python3 -m forecasting_mvp persistence-verify \
  --bundle examples/offline_multilanguage_e2e/registry/python-sqale
python3 -m forecasting_mvp persistence-serve \
  --registry examples/offline_multilanguage_e2e/registry
```

Open the loopback URL printed by the server and choose a bundle. The source is
labeled `SYNTHETIC` / `SOFTWARE_VALIDATION_ONLY` throughout. Fixture SQALE is
12 minutes; total principal is 16 when all three components exist, and remains
unavailable when security is missing. These are not measurements of Click.

## Reproduce the focused offline check

Use Python 3.12+ with the repository's existing pytest dependency, Git and an
**already installed** Playwright Python/Chromium runtime. No browser or package
installation is performed. The browser Python may be the same interpreter as
the runner or a separate existing virtual environment.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  examples/offline_multilanguage_e2e/run_offline.py \
  --out /tmp/td360-offline-new-run \
  --browser-python /path/to/existing/playwright-venv/bin/python
```

The output must be fresh and outside this evidence package. The runner reuses
`tests/test_native_project_persistence.py` to create explicitly synthetic Git
objects and native-shaped envelopes. It invokes the existing ingestion CLI,
serves a temporary loopback API, drives the real dashboard in cached headless
Chromium with CSP enabled, records receipts/screenshots, verifies tracked files
are unchanged, and shuts down its browser/server. It does not contact SonarQube,
scan repositories, run models or repeat the full regression suite. API future
actuals remain pending; this validates integration, not prediction accuracy.

`publication_manifest.json` binds the published files. Sealed bundle bytes and
screenshots are preserved from the original successful local run. Only unsealed
reporting paths and runner configuration were made portable. The original
CSP-related harness attempt is described in the report; the published browser
check uses the successful locator assertions.

The portable runner was executed successfully before publication: six bundle
IDs match the original run exactly, 18 API checks and all six rendered-browser
cases passed. See [publication check](publication_check.json).
