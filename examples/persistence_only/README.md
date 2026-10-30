# Persistence-only software examples

`observations.json` and `actuals.json` are invented SOFTWARE_VALIDATION_ONLY fixtures. They exercise measured changes, zero, incomparable domains/scopes, missing latest components, unchanged calendar revisions and pending outcomes.

See [operator instructions](../../forecasting_mvp/PERSISTENCE.md) for build/verify/serve commands and exact input schemas. Real operator inputs require their own revision/domain/source admission.

`real_import_verification.json` is an aggregate-only receipt confirming that the implementation replays the frozen real persistence evidence and preserves source IDs/files. It contains no per-origin source records. See the [implementation report](../../PERSISTENCE_IMPLEMENTATION_REPORT.md) for measured results and limitations.
