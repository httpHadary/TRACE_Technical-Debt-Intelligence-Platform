# Phase 5.2.2-A — Source and rights review

Date: **2026-10-16**. Base commit:
`7ce6d0e99c3701bdb774823ae6b192edabb42008`.

**Task A PASS: review completed. Rights/admission remain BLOCKED pending human
decisions.** All18 frozen source states match the implemented production-scope
contracts. No registration, source state, contract, benchmark or previous report
was changed. Task B was not started.

The principal rights finding is specific: the cached offline license extraction
for the pinned Java/Python/JS analyzers contains **SSAL v1.0, dated2024-11-13**,
including an external-AI restriction in its definition of permitted purpose.
No permission for TechDebt360's intended AI use of analyzer-provided data has
been established. Source-code licenses do not resolve that analyzer restriction
or independently approve publication of a derived dataset.

## Evidence and review boundary

Reviewed the Phase5.2.1 report and all three published readiness records:

- `examples/phase5_1/pilot_and_source_readiness.json`;
- `examples/phase5_2/readiness_manifest.json`;
- `examples/phase5_2_1/readiness_manifest.json`.

Their hashes are recorded in the new checklist. Their historical gate statuses
remain unchanged. The new evidence distinguishes completed static review from
legal/policy approval and operational admission.

Deliverables:

- [Machine-readable checklist](examples/phase5_2_2_a/content_rights_checklist.json).
- [Compressed per-file content evidence](examples/phase5_2_2_a/source_content_evidence.json.gz).
- [Verification and preservation](examples/phase5_2_2_a/verification.json).
- [Bounded, sequential audit tool](tools/review_phase5_2_2_a.py).

The source review reuses the cached content inspection from the interrupted
Phase5.2.2 work, then checks actual Git tree/blob identities and rehashes every
unique in-root blob once. Cached findings must match the actual content hash,
byte length, path, language, role and inventory ID. Repeated blobs across states
reuse that verified result. No source code, analyzer binary, full license/rule
text, credentials or downloaded dependency is published in this Task A bundle.

## Source population and exact inventory checks

| Development family | Root / languages | Production path-state entries | Noncode in-root entries | Outside-root entries | Unique in-root blobs |
| --- | --- | ---: | ---: | ---: | ---: |
| Commons CLI | `src/main`; Java |186|6|570|61|
| Click | `src/click`; Python |96|6|773|38|
| Django Browser Reload | `src/django_browser_reload`; Python+JS |60|6|343|12|

There are **2,046 tracked path-state entries**, including **342 production**,18
explicit noncode and1,686 outside-root entries. The per-family unique-blob counts
sum to111 because Click and Browser Reload share the same empty `py.typed`
blob. Globally, **110 unique in-root blobs /1,932,710 bytes** were verified.

All18 original commit/tree/cutoff/project-key identities were checked against
active states on the pinned complete first-parent lineages. The source population
remains26 Java files at the first three CLI cutoffs and36 at the last three;
16 Click Python files throughout;8 Python+2 JS Browser Reload files throughout.
Distinct production inventories remain5/4/3, not18 independent debt histories.

The version is still `production-root-study-v1`, with all existing scope,
feature and target identifiers unchanged. The three exposed development families
remain quarantined. No new held-out family was enrolled. No numerical debt
measurement, future label or model result was accessed for source selection.

### Generated/vendor code, unknown files and exclusions

Every in-root file is a regular UTF-8 Git blob. No unknown production suffix,
symlink/submodule, empty production population or inventory mismatch was found
at these18 states. The explicit noncode entries are Java Javadoc overview HTML
and the Python `py.typed` package markers. They are recorded rather than silently
assigned debt or treated as failed source files.

The cached inspection flagged33 generated-text occurrences across the18 states,
representing21 distinct blob/line findings. All occur in three Java classes:
`HelpFormatter`, `AbstractHelpFormatter` and `TextStyle`. Inspection of the
recorded context identifies documentation about generated usage text or a
Builder's output, not generated Java source. These are explicitly dispositioned
as `HELP_TEXT_OUTPUT_NOT_GENERATED_SOURCE` or
`BUILDER_OUTPUT_NOT_GENERATED_SOURCE`. No vendor/copy-origin pattern was flagged.
An unexpected generated/vendor signal makes the audit fail; it is not approved
by default.

This is a completed **static content review with stated limitations**, not an
independent ownership audit or proof that no unattributed copying exists.
Absence of a marker alone cannot establish legal origin. Accordingly, this
report emits no admission-ready source-review attestation and grants no rights.

Tests, examples, documentation/site assets, configuration, binary assets and
other files outside the three production roots remain outside the registered
measurement population. The full2,046-path inventory remains available in the
unchanged Phase5.2.1 source inventory. The new evidence records outside-root
extension counts per state. Known extra languages in documentation/examples do
not expand the production scope or establish analyzer coverage. Changing those
roots/suffixes would require a separately approved contract version.

Actual language NCLOC, native analysis completeness and analyzer compatibility
were not measured. Browser Reload remains a **Python+JS mixed development
candidate**, not a JS-dominant project; native programming-family shares≥10%
still need verification in a future authorized analysis.

## Source licensing and attribution

All18 states have their actual root license inspected as immutable Git blobs;
CLI also has its NOTICE inspected. This gives24 state/license-or-notice records,
representing only **four unique license/notice blobs**. Paths, Git IDs and SHA256
are recorded per state. License identity is established; ownership warranties,
institutional approval and publication acceptance are not.

| Source | Verified declared code license | Conditions to address before source/derivative redistribution |
| --- | --- | --- |
| Commons CLI | Apache-2.0, plus `NOTICE.txt` | Retain applicable notices, provide the license, preserve required NOTICE attribution and mark modified distributed files. No trademark endorsement is inferred. |
| Click | BSD-3-Clause | Retain copyright/conditions/disclaimer in source; reproduce required notices in binary materials; respect the non-endorsement condition. |
| Browser Reload | MIT | Include the copyright and permission notice with copies or substantial source portions. |

These findings come from the pinned repository files, not today's repository
badge. No project code was modified or redistributed here. A later dataset
containing code snippets or substantial source portions needs an attribution
plan tied to the exact contributing source/version. Numeric-only data, raw
issues, rule text, source excerpts and analyzer binaries require separate
publication decisions rather than a blanket code-license label.
[Apache's license text](https://www.apache.org/licenses/LICENSE-2.0).

## Analyzer and tool licensing

The committed Phase5.2.1 artifact inventory binds these analyzer JAR identities:

| Analyzer | Version | Embedded license evidence |
| --- | --- | --- |
| Java |8.37.0.45887|SSAL v1.0, `licenses/LICENSE.txt`|
| Python |5.27.0.35548|SSAL v1.0, `licenses/LICENSE.txt`|
| JavaScript |13.4.0.43982|SSAL v1.0, `licenses/LICENSE.txt`|

The saved extraction was produced by a read-only offline inspection during the
interrupted earlier phase. Task A rehashed its license text and linked each
record to the JAR hash in the committed inventory. **No container was accessed
and no fresh extraction was performed in Task A.** All three embedded license
texts have SHA256:
`b93b383060f0b26e95538455d8a92b0c9bc5bf61c3a1fd42583fc3d535330a03`.
The cached extraction's own hash and provenance limitations are in the checklist.

The embedded SSAL grant is conditioned on its defined noncompetitive purpose.
That definition excludes specified competing/substitute uses and external AI
interaction with program-provided data or the program. Therefore, installation,
public availability and academic-project intent do not establish permission for
the proposed AI workflow. Qualified human review and, where needed, written
licensor permission must determine the allowed collection/use/publication plan.
This report issues no legal opinion, exception, permission or acceptance.

The publisher's current website displays SSAL **v1.0.1** dated2025-11-20. It
supports identifying the type of restriction but **does not replace the actual
v1.0 terms embedded in the pinned artifacts**. The scanner project publishes
LGPLv3 terms; that does not relicense its separately licensed analyzers or establish
all notices in the pinned image. No scanner/server/analyzer redistribution occurs
here. [Current SSAL text](https://www.sonarsource.com/license/ssal/),
[scanner project license](https://github.com/SonarSource/sonar-scanner-cli/blob/master/LICENSE.txt).

## Objective findings versus human decisions

| Item | Objective result | Unresolved human decision |
| --- | --- | --- |
| Source states/scopes | Exact18-state inventory verified; all identifiers retained | None needed merely to record these existing facts |
| Static content signals | All recorded signals dispositioned; no unknown in-root file or flagged vendor marker | Accept review limitations; investigate any later provenance dispute |
| Source license identity | Apache-2.0/BSD-3-Clause/MIT and CLI NOTICE verified | Accept and implement the release-specific attribution plan |
| Analyzer license identity | Pinned cached SSAL v1.0 text/hash verified | Determine intended AI/competitive-use permission; obtain written clarification/permission if necessary |
| Derived data | No new measurements or dataset release | Approve exact fields, intended recipients/use, retention and publication terms; do not assume raw rule text or numeric labels are unrestricted |
| Runtime permissions | Latest task authorizes source/rights review only | A separately authorized task must establish any runtime credentials and execution permissions |

The checklist explicitly leaves every human-approval item `NOT_APPROVED`, records
no approval evidence and keeps `legal_acceptance=false`. Existing registrations
retain `reserved_role=quarantine` and unresolved data-reuse terms. No promotion,
contract weakening or collection-ready PASS was issued.

A viable next decision is qualified review of the actual embedded terms and the
intended workflow, followed by written permission if required. If that route is
unavailable, a different analyzer/data source would need its own explicit rights
review and separately authorized study decision. Task A does not choose or
implement that change and does not begin Task B.

## Verification, resource limits and preservation

The audit and tests run sequentially under a **1GiB address-space ceiling**, with
180-second operation timeouts and120-second CPU ceilings. Individual Git blobs
are size-checked before reading (≤1MiB); aggregate unique source reads are capped
at8MiB; JSON/decompressed inventory inputs are capped at4MiB. No parallel workers
were launched. Audit peak RSS was about25MiB; actual measurements and test
results are recorded in `verification.json`. **187 tests passed in each checkout**,
including11 new audit cases. There were no failed or skipped cases.

Preservation checks passed for all377 pre-existing central files,288 existing
working-project files,56 frozen experiment bundles /322 artifacts, both
Phase5.1 bundles, the source database and the pinned checkpoint. The four
unfinished untracked remediation files were also preserved byte-for-byte.

The source/rights audit was reproduced twice; its normalized evidence is identical
apart from process-memory telemetry. Appropriate regression checks cover the
new audit, existing production scopes, preflight and schema-v2 foundation. No
Maven, model or container command was used. Verification includes streamed hashes
of previous files, frozen bundles, the source SQLite and checkpoint, without
loading large binaries into memory.

Only new Task A documentation, audit/test code and small metadata are committed.
The unfinished `forecasting_multilanguage/remediation/` files from the interrupted
broader phase remain unchanged and uncommitted. Existing downloaded dependencies
remain outside Git and were not accessed or extended by Task A.

Reproduction, using the existing interpreter and saved local inspection inputs:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
TD522A_PY="$PWD/.venv-forecast/bin/python"
PYTHONDONTWRITEBYTECODE=1 timeout 180s prlimit \
  --as=1073741824 --cpu=120 --fsize=16777216 -- \
  "$TD522A_PY" -m tools.review_phase5_2_2_a \
  --content-cache /home/hp/tst/research/forecasting_mvp/phase5_2_2/2026-10-15/content-review-raw.json \
  --analyzer-license-cache /home/hp/tst/research/forecasting_mvp/phase5_2_2/2026-10-15/embedded_license_evidence.private.json \
  --output /path/outside/git/to/new-task-a-review.json
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s prlimit --as=1073741824 --cpu=120 --fsize=16777216 -- \
  "$TD522A_PY" -m pytest -q -p no:cacheprovider \
  tests/test_phase5_2_2_a_review.py tests/test_production_scope_readiness.py \
  tests/test_multilanguage_preflight.py tests/test_multilanguage_foundation.py
```

Saved private inspection inputs are not distributed. Their absence blocks exact
local reproduction; do not synthesize replacements or claim fresh binary
inspection. Public scope/source identity evidence remains in the committed
metadata bundle. Publication uses a normal descendant commit on central `main`,
explicit working-project sync and GitHub byte verification. The unrelated working
`main` history and every earlier experimental artifact remain preserved.

**STOP after Task A verification and publication. Task B is not authorized.**
