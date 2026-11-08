# TechDebt360 MVP migration

## What this branch contains

This branch brings the complete tracked tree from
[`FadyYosry77/TechDebt360-MVP`](https://github.com/FadyYosry77/TechDebt360-MVP)
into the TRACE repository. The source history is preserved as a second parent of
the migration merge commit, so the original implementation commits remain
available for review with `git log --follow` and the source remote.

## Migration provenance

| Item | Value |
| --- | --- |
| Destination repository | `httpHadary/TRACE_Technical-Debt-Intelligence-Platform` |
| Migration branch | `migration/techdebt360-mvp` |
| Destination base | `dev` |
| Source repository | `FadyYosry77/TechDebt360-MVP` |
| Source branch | `main` |
| Source revision | `998cd32bf7cc6dfd607702df5db9f338b812ad6c` |
| Migration approach | Merge with unrelated histories preserved |

The existing TRACE `.github/` governance files and `test` marker from `dev` were
retained. The root `README.md` and `.gitignore` were combined to document both
projects and protect both Java/JVM and Python-generated artifacts.

## Where to start

1. Read the root [`README.md`](../README.md) for the project overview and active
   MVP status.
2. Read [`forecasting_mvp/README.md`](../forecasting_mvp/README.md) for the
   implementation entry point.
3. Read [`forecasting_mvp/PERSISTENCE.md`](../forecasting_mvp/PERSISTENCE.md)
   for the current persistence workflow.
4. Run the offline test suite after installing the pinned development
   requirements:

   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements-dev.txt
   .venv/bin/python -m pytest -q
   ```

## Directory guide

- `forecasting_mvp/`: active MVP implementation and local serving flow.
- `forecasting_multilanguage/`: multi-language ingestion and readiness contracts.
- `forecasting/`: shared forecasting data and evaluation foundations.
- `forecasting_research/`: archived research-stage forecasting modules.
- `tests/`: offline regression and integration coverage.
- `examples/`: published validation evidence and reproducible artifacts.
- `architecture-redesign/`: architecture plans, reviews, and implementation roadmaps.
- `research/`: research records and experiment inputs.
- `tools/`: recovery, inspection, build, and verification helpers.

## Scope note

This migration intentionally does not claim that the imported research artifacts
are production-ready. The source repository's existing reports and README retain
their phase boundaries, limitations, and frozen-experiment warnings.
