# Real development pilot candidates — Phase 5.2

Date: 2026-10-15. **Metadata/source selection only; collection is blocked.**
No debt measurements or forecast outcomes were used to nominate, rank or replace
repositories. The pilot remains exactly three development families, with one
genuinely mixed Python+JS/TS family rather than a fourth JS/TS-dominant project.

## Selection policy and result

Start with a small existing Java library and small publicly licensed Python/web
libraries. Fix the common origin/grid from historical coverage, inspect complete
source objects and production roots, then prefer: passing frozen lineage gates;
fewer unsupported/ancillary production languages; smaller source/build footprint.
Use immutable source identities, not popularity/error/debt outcomes. Record every
screened alternative. This is an engineering feasibility screen, not a random or
representative research sample.

| Target | Selected development source | Code license at selected historical states | Reason |
| --- | --- | --- | --- |
| Java-dominant | [Apache Commons CLI](https://github.com/apache/commons-cli) | Apache-2.0; NOTICE retained as a separate obligation | Existing complete local lineage; small Maven/JDK8-targeted library; source scope can be enumerated |
| Python-dominant | [Pallets Click](https://github.com/pallets/click) | BSD-3-Clause | Small pure-Python library, no application build needed for native source analysis |
| Mixed Python+JS | [Django Browser Reload](https://github.com/adamchainz/django-browser-reload) | MIT | Small real runtime package with server-side Python and two browser JS modules; no production CSS/templates/TS compiler dependency in the selected roots |

Licenses were checked as pinned historical Git objects, not inferred solely from
today's GitHub badge. Hashes of all six state licenses/build files are in
[`historical_build_provenance.json`](examples/phase5_2/historical_build_provenance.json).
Later source redistribution must retain the applicable license/NOTICE material.
New dataset/rule-export publication terms are a separate future gate; this phase
publishes file/hash/count metadata, not source archives or proprietary rule text.

## Immutable source identities

| Source | Provider/family identity | Frozen lineage tip |
| --- | --- | --- |
| Commons CLI | GitHub212343 / `github:212343` | `c99cb283fbf631a589cf7c41d5884992d94c7741` |
| Click | GitHub19103692 / `github:19103692` | `2247b35ea1c47c727d7a06e51fa280e12a863ff6` |
| Browser Reload | GitHub438426152 / `github:438426152` | `9e07824fe16e413fccf4078bd8d5e68b75a553c7` |

The source plans bind each tip to its recorded UTC ref-observation clock and a
complete, nonshallow first-parent history. Connectivity checks use existing Git
objects; no state is picked by nearest measurement. Full commit/tree IDs for each
of the18 selected cutoffs and their inventories are in
[`selected_source_plans.json`](examples/phase5_2/selected_source_plans.json).

Commons CLI has1,956 first-parent commits, Click1,384 and Browser Reload424,
with zero timestamp inversions in each chain. These are counts on the selected
lineages, not independent temporal measurements. The histories use committer UTC
as the registered retrospective state clock; they do not establish historical
online branch availability.

Commons CLI is known exposed in V2/prior registries. Exact canonical URL/name
checks found no prior match for Click or Browser Reload in the bounded Phase5.1
inventory; unresolved names/forks mean this is **not a certificate of complete
non-exposure**. All candidates become exposed development sources through this
preflight anyway. Current GitHub metadata marks them non-forks and gives distinct
provider IDs; no family is reserved for confirmation or promoted to held-out.

## Actual production inventory and provisional language mix

The common origin is 2024-10-01T00:00:00Z; six cutoffs cover July3–December30,
2024. The planner enumerates every tracked entry, including symlink/submodule
checks, instead of treating a known suffix list as the entire repository.

| Source at T0 | Proposed production root | Actual proposed source files | Nonblank source-text proxy | Frozen-policy differences |
| --- | --- | --- | --- | ---: |
| Commons CLI | `src/main` | 26 Java | 6,166 Java lines | 2 site JS paths outside root |
| Click | `src/click` | 16 Python | 8,199 Python lines | 15 docs/example Python paths |
| Browser Reload | `src/django_browser_reload` | 8 Python +2 JS | 257 Python +116 JS lines | 7 example Python paths |

Browser Reload's source-text programming shares are68.9% Python /31.1% JS at
T0, making it a strong **provisional genuine mix** under the mixed-first screen.
Nonblank lines include comments/docstrings and are not native NCLOC. Only a
complete future analysis can confirm the two ≥10% programming-family NCLOC
shares. Do not relabel it JS-dominant, apportion debt by line share, or count
example CSS/HTML as production coverage.

All selected production extensions are `.java`, `.py` or `.js`; there are no
unrecognized production extensions at T0. The tracked inventory nevertheless
retains outside-scope `.vm`, `.cgi`, `.xcf`, `.jacoco`, `.file`, `.bat`, `.in`,
HTML/CSS, config, docs and binary asset paths. Java `overview.html` is Javadoc
documentation; Python `py.typed` is package metadata. Test/fixture/example and
generated/vendor/minified dispositions are explicit. File-header/provenance
review must confirm the path heuristics before dispatch; absence of a `vendor`
directory does not prove every file is first-party.

Current frozen schema2 scope cannot express this root-aware study. A **new
versioned scope/contract dispatch** is required, as documented in
[`scope_extension_proposal.json`](examples/phase5_2/scope_extension_proposal.json).
The original policy and all prior measurements remain untouched. Do not simply
omit files at scan time and reuse the frozen scope hash.

## Historical build feasibility

- **Commons CLI:** the inspected POMs use Java8 source/target settings and varying
  Apache parent versions. A Maven3.9.11/JDK17 image is already present; use a
  fixed Java8 release/SDK policy across the new retrospective study. Parent/POM
  and compiler/enforcer/resources plugin caches exist, but the complete
  transitive effective-POM/classpath graph is unverified. No compilation ran.
  Missing dependency, class or SDK evidence blocks Java collection rather than
  permitting source-only analysis.
- **Click:** T0 `pyproject.toml` requires Python≥3.8 and declares a Flit backend.
  Native source scanning does not require installing or importing the library,
  running its tests or resolving Flit/dev dependencies. Freeze the supported
  Python-version property from each historical declaration, or split the domain
  if it changes measurement semantics. The proposed six-state policy uses the
  common supported source baseline after declaration verification.
- **Browser Reload:** source-only Python/JS acquisition, without Django startup,
  database, browser, npm install or transpilation. Historical dependency/build
  declarations are hashed. Existing JS13.4 embeds Node24.11.0, but actual isolated
  runtime deployment and analyzer completion remain untested.

The execution plan specifies the no-network/cache-only first build attempt and
the required future failure evidence. Build feasibility is a metadata conclusion,
not a successful build/scan benchmark.

## Recorded alternatives and exclusions

| Candidate | Screening performed | Disposition |
| --- | --- | --- |
| [Django Debug Toolbar](https://github.com/django-commons/django-debug-toolbar), provider46939, BSD-3-Clause | Complete local bare history/source inventory and six metadata states;2,038 first-parent commits | Three historical first-parent timestamp inversions fail frozen admission. Production CSS and Django templates require additional scope/coverage work. Keep as a documented alternative, not a fourth pilot |
| [Pallets Flask](https://github.com/pallets/flask), provider596892, BSD-3-Clause | Publisher/API metadata and language summary only | Larger repository metadata footprint than Click. No mirror/build/complete-history claim; not an extra Python target |

Debug Toolbar's2024 source-text mix also supports a provisional mixed family,
but that does not erase its lineage/scope blockers. We did not alter its tips,
discard old commits, sort the graph by timestamp or choose an easier debt outcome.
Browser Reload's selection was based on passing metadata gates and its smaller
production scope. No new fourth JS/TS-dominant repository was introduced.

## Decision boundary

**Select these three sources for planning; do not admit measurements yet.**
No project/analysis was created and no Sonar metric was read for selection. Before
future collection, resolve the versioned scope, live Standard mode/profile/rule
hashes, license/data-policy acceptance, Java build proof, sandbox runtime and RAM
headroom gates. If a candidate later fails, preserve the failed attempt and plan;
do not swap in an unregistered family based on model outcomes.
