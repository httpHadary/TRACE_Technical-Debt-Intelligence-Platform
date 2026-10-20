# Real-world evidence readiness (Phase6.6)

This module inspects metadata descriptions. It does not accept feature values,
measurements, labels or raw payloads, and has no collection, training, prediction,
network or approval interface. It reuses schema-v2 UTC, exact-horizon and strict
90-day-context purge contracts without changing earlier studies.

Run the bounded documentary audit from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.check_phase6_6_readiness
```

Successful execution means the plan is coherent and evidence references match.
The expected result is `READINESS_PLAN_REVIEWED_ADMISSION_BLOCKED`; a zero command
exit is NOT data admission, an experiment approval or proof of predictive utility.
The existing Phase C auditor independently verifies the unchanged24 decisions.
Only20 allowlisted published code/report/metadata files can be direct references.
The inherited Phase C auditor verifies its own documentary evidence graph too.
No dependency installation is needed.

Pure readiness helpers:

- `inspect_signal`: distinct event/version/availability/retrieval clocks; explicit
  complete/unknown/empty-window evidence; origin-time checks; planned deadlines
  distinguished from realized future changes. A SHA256-shaped reference is not an
  independently authenticated archive. `can_admit_data` is always false.
- `inspect_schedule`: exact30/60/90 endpoints, fixed90-day historical context,
  exposed-family rejection, same-family information-interval purging, and global
  prior-role label-availability checks across repositories in OPERATIONAL_ASOF
  scheduling. Retrospective replay needs a separately reviewed schedule. With90-day labels and
  90-day context, a180-day origin gap still shares a boundary and is excluded.
- `feedback_eligibility`: no feedback before the exact endpoint, actual label
  availability and domain agreement. Coherent timing never grants model-update
  permission.

The contract explicitly separates retrospective fixed-analyzer reconstruction
from operational-as-of evidence. It cannot establish historical availability from
a commit date or turn a planned due date into a known future outcome.

Unit tests use original fictional metadata clocks/IDs only. No new synthetic
forecasting population, model state or scored experiment is created. A future
approved data adapter must still use the existing schema-v2 admission, observation,
source-rights, scope/domain, feature and target boundaries. Do not attach these
readiness results directly to a live forecasting or collection process.
