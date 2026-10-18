# E.0.3 verified static test-dependency recovery

Status: **STATIC_TEST_DEPENDENCY_CLOSURE_COMPLETE** for the exact E.0.2 missing
roots in the frozen T0 consumer context. All ten paths are recovered. The complete
candidate cache has 679 hash-verified files: 653 unchanged seed files plus 26 new
files (12 JARs and 14 POMs). It is not proof of Maven lifecycle or compiler success.

`dependency_manifest.json` is the full reusable cache inventory with exact
coordinates, URLs, hashes, same-origin checksums, origins and independent request
accounting. `recovered_artifacts.json` isolates the 26 additions. The cache identity
uses the sorted path/hash/byte-size recipe in `cache_identity.json`.

`closure_evidence.json` records the actual required declaration paths, parent/BOM
metadata, managed versions, exclusions and omitted test/provided/optional paths.
`frontier_comparison.json` reconciles the original ten missing paths.
`remaining_uncertainties.json` keeps old profile/plugin/SCM/rights questions visible.

Sixteen new files reused approved local bytes only after fresh Maven Central
checksums and structural/coordinate validation. Ten files were downloaded from
Maven Central. This uses 56 of 200 requests; no continuation batch ran. No Maven,
JAR execution, build retry, scanner, server, model or dataset admission ran.

Only metadata, independently authored code/tests and reports are published. No
POM/JAR payload, user credentials, caches or historical binary outputs are in Git.
See `E_0_4_HANDOFF.md`; the next compile requires separate explicit authorization.
