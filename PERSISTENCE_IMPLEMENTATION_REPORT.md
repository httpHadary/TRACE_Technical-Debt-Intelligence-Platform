# Persistence-only MVP implementation

Date: 2026-10-30, Africa/Cairo.

The persistence flow is implemented: validated observations → constant-stock forecasts → sealed presentation bundle → measured endpoint evaluation → read-only local dashboard. The active flow imports no neural runtime and runs no Chronos or hybrid forecast. Historical research commands/code retain their original behavior.

## Run it

From the repository root, using the existing Python requirements:

```bash
registry=$(mktemp -d)
python3 -m forecasting_mvp persistence-build \
  --source examples/persistence_only/observations.json \
  --actuals examples/persistence_only/actuals.json \
  --out "$registry/example"
python3 -m forecasting_mvp persistence-verify --bundle "$registry/example"
python3 -m forecasting_mvp persistence-serve --registry "$registry" --port 8765
```

Open `http://127.0.0.1:8765`. These example observations/actuals are explicitly synthetic software validation. For real use, supply the observation/actual schemas documented in [PERSISTENCE.md](forecasting_mvp/PERSISTENCE.md). Never put private input data or generated research bundles in a public Git checkout.

The separate `persistence-import` command projects the already sealed principal study into persistence-only display records. It verifies the original artifact manifest, prediction/request seals and target membership. No source study is rerun or rewritten.

## Delivered behavior

- Strict component/repository/revision/domain/clock input validation, including observed zero versus missing and latest unavailable origins without carry-forward.
- Persistence points equal origin stock; projected change is zero and forecast intervals are null.
- Signed measured changes appear only between compatible observations. Domain/scope breaks and missing components remain explicit.
- Optional future actuals are opened after prediction sealing; mismatched identities fail and absent actuals remain pending. An unchanged selected revision is valid at an exact calendar cutoff when its measurement/index remain consistent.
- COMPLETE bundles carry artifact hashes, deterministic IDs, source claims and recomputable semantic checks. Failed evaluator outputs retain their sealed evidence without a completed manifest; existing output directories cannot be overwritten.
- Read-only loopback API and static dashboard support repository/horizon selection, history/components, forecast points, measured/pending actual errors and bundle-wide per-horizon MAE/RMSE/coverage/change-subgroup summaries. Other model queries are rejected.

## Verification

Final implementation check: **199 tests passed** across the new flow/API tests and existing Phase 0/1/2/2.1/3 compatibility tests.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_persistence_flow.py tests/test_persistence_api.py \
  tests/test_forecasting_mvp_phase0.py tests/test_forecasting_mvp_phase1.py \
  tests/test_forecasting_mvp_phase2.py tests/test_forecasting_mvp_phase2_1.py \
  tests/test_forecasting_mvp_phase3.py
```

Read-only import of the real frozen principal bundle produced **678 persistence endpoints** from 226 origins. Original IDs and all 147 source files were preserved; only persistence appears in the active forecast projection. Each horizon's macro MAE matches the original evidence:

| Measured revision horizon | Endpoints | Equal-repository MAE, estimated minutes |
|---|---:|---:|
| 3 | 226 | 104.420724 |
| 4 | 226 | 135.550811 |
| 12 | 226 | 384.541132 |

These are reused exposed retrospective results, not fresh validation or evidence that persistence anticipates changes. A small import receipt is in [examples/persistence_only/real_import_verification.json](examples/persistence_only/real_import_verification.json); raw imported observations/predictions remain outside Git.

Node parsed the actual dashboard JavaScript. A live-API logic smoke executed that JavaScript with a minimal DOM test double, exercising synthetic and real historical bundles, repository selection, horizon selection, displayed forecast/history and evaluation summaries. **Rendered visual browser QA was unavailable because the session exposed no browser surface.** HTTP/static/security/invalid-query/corruption checks passed through the automated tests.

## Limits and remaining work

The implementation consumes operator-provided measurements; it does not perform a new Sonar scan or certify source/analyzer authenticity. A live current-repository scan/demo is still a separate collection step. Current-domain forecast accuracy remains unvalidated. Persistence assumes zero future change and supplies no statistical interval.

Revision-step and elapsed-day target contracts remain separate. A registered operator-provided 30/60/90-day point projection is supported, but retrospective total-principal calendar data/admission and its accuracy study remain gated. The old revision experiment cannot establish calendar-day performance. Source permission statements remain claims; importing a bundle grants no data-use rights.

Private local verification artifacts reside under `/home/hp/tst/research/forecasting_mvp/persistence_only_implementation/2026-10-30/`. No dataset, checkpoint, credential, private approval or new model execution is included in the publication.
