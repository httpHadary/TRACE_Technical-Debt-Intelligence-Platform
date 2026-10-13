# TechDebt360 MVP repository

This repository contains the existing pipeline, architecture/research packages and implemented Phase 0/1 foundation and historical ingestion. Phase 1 is PARTIAL for scientific readiness: audited measurements are available, but exact future contexts/labels and pretrained runtimes remain unvalidated. Phase 2 exact-target datasets and purged splits are implemented. Phase 3 has not started.

- [Phase 2 implementation report](PHASE_2_IMPLEMENTATION_REPORT.md)
- [Forecasting feasibility and sample](examples/phase2/README.md)
- [Phase 1 implementation report](PHASE_1_IMPLEMENTATION_REPORT.md)
- [Historical audit and small sample](examples/phase1/README.md)
- [GitHub sync instructions](GITHUB_SYNC.md)
- [Phase 0 implementation report](PHASE_0_IMPLEMENTATION_REPORT.md)
- [Phase 0 source and usage](forecasting_mvp/README.md)
- [MVP plan](architecture-redesign/2026-10-13-forecasting-mvp/README.md)
- [Refined research architecture](architecture-redesign/2026-10-13-refinement/README.md)
- [Original architecture package](architecture-redesign/2026-10-13-techdebt360/README.md)
- [Phase 0 verification evidence](research/forecasting_mvp/phase0/2026-10-13/)
- [Existing pipeline documentation](README.md)

ZIP archives are retained under `architecture-redesign/`. Local dataset paths, hardware snapshots and absolute links in the historical reports identify the original machine; they are provenance, not portable installation defaults. V2, model weights, credentials, virtual environments and generated caches are not included. Configure a new source/output study record before running on another machine.

Phase 2 includes measured future labels and frozen data splits. No model training, forecasts or implementation beyond Phase 2 is part of this upload.
