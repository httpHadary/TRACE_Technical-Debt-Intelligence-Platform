# Phase 5.2.2-E.0.1 — Build sandbox setup and failure-capture repair

Date: **2026-10-18**, Africa/Cairo. Starting main: `8e73a0a050fc3f411087666aae1057b66fa3282f`.

**SETUP_AND_CAPTURE_PASS.** One real disposable container, using the pinned image,
prepared and verified the exact117-file source population and653-artifact cache,
then deliberately exited73 before Maven. Its exact failure stage/category,
setup stdout/stderr, terminal Docker exit/OOM state, cgroup measurements and
owned daemon events were retained, and the container was removed. No smoke retry,
Maven, Java compiler, scanner, historical lifecycle, model or dataset operation ran.

**E.0 remains BLOCKED_BUILD_OR_RESOURCE.** Its report, receipt, controller recipe,
failure evidence and exhausted attempt claim remain byte-identical. This phase
proves infrastructure setup/capture only, not Java compilation or plugin-classpath
readiness. E.0.2 has not started.

## Root cause and scoped repair

E.0 mounted root-owned tmpfs directories and recursively chmodded their roots as
UID1000. Its setup exited123 before Maven, and its monitor's next Docker exec raced
termination. Cleanup discarded logs/tmpfs evidence. The exact old failed command's
stderr was unavailable; this phase does not invent or rewrite it.

The new reusable sandbox is isolated in `tools/build_sandbox.py` and
`tools/build_sandbox_setup.sh`. The archived E.0 recipe stays unchanged for audit.
The controller fixes:

- Explicit `uid=1000,gid=1000` tmpfs ownership for `/source` and
  `/runtime-repository`, retaining size/mode/nosuid/nodev/noexec. The shell verifies
  actual UID/GID, ownership and writability **before copying**. `/tmp` and `/output`
  also have explicit task ownership. No root container, extra capabilities,
  privileged mode or writable host bind was introduced.
- `find -mindepth1 -type f` changes permissions only on copied owned files;
  no recursive chmod targets mount roots. All117 source/653 artifact byte hashes
  remain exact, with unchanged coordinates and historical POM identity.
- An EXIT trap is registered before setup/redirects. `run_stage` records stage,
  command category, native stdout/stderr and real exit code. The trap snapshots
  cgroup evidence when readable and records an unavailable marker otherwise.
- Setup stdout/stderr are distinct files, independent from any future Maven
  streams. This version has **no Maven command path** and only accepts
  `--no-maven-smoke`. The deliberately injected failure is clearly identified.
- The trap relays setup output to Docker logs and holds for at most15seconds
  awaiting collection. Live namespace tar export is bounded and validated before
  extraction; no Docker archive API assumption is used for tmpfs contents.
- Exec failures are recorded as capture races. Independent host capture paths
  retain Docker stdout/stderr, terminal state including OOMKilled and filtered
  task-owned daemon events before ownership-checked removal. Failed inspect does
  not suppress log retention. Abrupt kill/OOM cannot run an EXIT trap; available
  host evidence is retained and missing tmpfs/cgroup measurements stay unavailable.
- An exclusive persistent attempt claim prevents a second container. Resource
  admission is repeated immediately before startup. Cleanup asserts name/label
  ownership and targets only this task's disposable container.

Archive admission rejects traversal, absolute/unregistered paths, symlinks/hard
links, canonical duplicates, overwritten outputs, oversized members, excessive
member counts and total expansion. It validates all members before writing.
Limits are32MiB archive/expansion,8MiB per file and128 members. This smoke captured
21 small allowed files. No binary/source/dependency artifact is admitted to Git.

## Frozen inputs and real smoke observations

| Evidence | Actual |
| --- | --- |
| Repository |Apache Commons CLI, T0 only|
| Commit |`4ff0d4adbc2161677e71050ba23c152831f6ad83`|
| Tree |`ac7521be84b2820a83f7b960d329a15521408214`|
| Historical POM SHA256 |`b75fb9813e3c06121caa7d84c31a471b646465966079cf10ec4c7a2e4aba55f2`|
| Seed input origin |Exact verified E.0117-source/653-artifact seeds|
| Independent byte-verified copies |117 source files;653 artifacts; no hard links|
| Production Java files |26; no fabricated source/Git metadata|
| Actual pre-copy ownership |`/source 1000:1000:1777`, `/runtime-repository 1000:1000:1777`|
| Intended/actual working directory |`/source`|
| Expected/actual injected exit |73 /73|
| Exact stage |`INJECTED_PRE_MAVEN_FAILURE`|
| Exact command category |`deliberate_exit_73`|
| Source/cache populations |117/653 exact unique paths; every SHA256 equal|
| Setup completion |true, before injected failure|
| Unavailable required evidence |none|
| Container startups / retries |1 /0|
| Cleanup |complete; no task container remains|

The fixture injection printed:

```text
stdout: TD_SMOKE_INJECTED_STDOUT
stderr: TD_SMOKE_INJECTED_STDERR
```

The native setup stderr also retains the wrapper's exact failure line:

```text
STAGE_FAILED INJECTED_PRE_MAVEN_FAILURE deliberate_exit_73 exit=73
```

Docker's terminal state is exit73, OOMKilled=false. Its logs contain both captured
streams; retained sizes are1586stdout bytes and134stderr bytes. The process snapshot
contains no Java/Maven/compiler/scanner process. The wrapper has no Maven launcher,
accepts only smoke mode and records `maven.state=NOT_STARTED`. No empty Maven log or
fabricated historical build result substitutes for actual execution evidence.

Exact expected/observed SHA256 manifests, capture-completeness checks, stage output
and terminal metadata are under [examples/phase5_2_2_e_0_1](examples/phase5_2_2_e_0_1/README.md).
The source/cache verification uses published E.0/D.3 provenance and Git blob
identities. No POM/JAR was downloaded or executed; only native setup tools ran.

### Read-only verifier correction after capture

The first reader compared GNU-sort display order against Python lexical order.
The pinned image locale orders some filenames differently. The117/653 raw path
lists had **zero set differences and zero duplicates**, and every byte hash already
matched. The reader was corrected to canonicalize ordering while requiring exact
unique populations, counts and SHA256 equality. No captured file, scope or admission
identity changed, and the container was not rerun. The initial checker receipt
remains private, with its SHA256 and the correction recorded in
[verification_manifest.json](examples/phase5_2_2_e_0_1/verification_manifest.json).

Additional strict isolation assertions were checked against the saved real
pre-start inspection, without starting another container. Final source/test hashes
bind the corrected reader and those assertions; the executed shell wrapper hash
matches the published shell byte-for-byte.

## Actual resources and isolation

Image: `sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`. No image pull, install or runtime upgrade occurred.

| Evidence | Actual |
| --- | ---: |
| Actual cgroup memory.max |1,073,741,824 bytes|
| Actual cgroup memory.swap.max |0|
| Actual cpu.max |100000 /100000: one CPU|
| Actual pids.max |64|
| EXIT-trap memory.peak |84,742,144 bytes (~80.82MiB)|
| EXIT-trap CPU usage |473,064µs|
| Host available RAM immediately before start |6,401,507,328bytes (~5.96GiB)|
| Minimum sampled host available RAM |6,305,783,808bytes (~5.87GiB)|
| Free disk immediately before start |21,337,673,728bytes|
| OOM / OOM-kill counters |0 /0|

The memory/CPU readings are actual EXIT-trap snapshots through that point. They do
not retrospectively include later evidence-export helpers/cleanup. Full-lifetime
memory remained cgroup-capped at1GiB; no peak beyond the observed snapshot is
invented. The real container ran about1.61seconds according to terminal timestamps.
Raw UTC timestamps are retained; this report's date follows the Africa/Cairo client.

No other container or prohibited Java/Maven/Sonar/model workload was running at
admission. Minimum host headroom stayed above2GiB. Controls remained user1000:1000,
all capabilities dropped, no-new-privileges, network `none`, image root read-only,
read-only task inputs/inspection binds, no host credentials/socket/user Maven cache.

Source/repository/tmp each retained128MiB tmpfs caps, output32MiB:416MiB total,
plus8MiB shared memory. File-size cap8MiB;1024file descriptors;110second monitor threshold and
180second hard outer controller timeout; EXIT-trap collection grace at most15seconds. Task-owned logs were capped1MiB.
The smoke started no JVM, so no heap tuning or native-console workaround was used.

## Regression and preservation

**368 tests passed in each checkout**, including35 new sandbox cases; zero failures,
errors or skips. Central: 22.165s; original project:
18.836s. Tests cover UID/GID/mount/security tampering, source/cache
copy and permission failures, actual shell EXIT-trap stderr/exit preservation,
early exit, exec/inspect races, independent Docker-log retention, simulated OOM,
missing cgroup measurements, archive traversal/links/duplicates/size caps,
exclusive attempt claims, cleanup ownership, no-Maven mode and locale-independent
exact file identities. Unit fixtures do not claim extra real smoke runs.

Preservation PASS:465 prior central files,376 working files,4 unrelated unfinished
files;1378/615/630 D/D.1/D.2 cache files,842 D.3 private files and790 E.0 private
files, all byte-identical. Prior request ledgers remain2000/400/52/112. E.0's status
stays BLOCKED. All56 frozen bundles/322 artifacts,2 Phase5.1 bundles, source SQLite,
pinned model checkpoint, original sources/POMs and old Sonar container state/mounts
remain verified. No task-owned container remains. Original working `main` remains
`2e7999ea436d49449652e6c52e9066ef2e514419`.

The historical user Maven-cache metadata snapshot predates this task. The current
user cache contains384 additional files and4 `_remote.repositories` metadata updates
from2026-10-16, all before task start; none of the historical entries was removed.
These pre-existing changes were **not** overwritten or rolled back. All current
file ctimes predate task start;75 prior artifact hashes match. There are6262 current
entries across both user caches. The smoke never mounted or wrote either cache.
[User-cache drift receipt](examples/phase5_2_2_e_0_1/user_cache_drift.json) keeps this
distinct from byte-for-byte preservation of the frozen research caches. The old
snapshot/ledgers remain unchanged; no historical accounting was reset.

[Verification receipt](examples/phase5_2_2_e_0_1/verification.json) records source,
JUnit/log hashes and preservation. Exact inputs and raw private inspections remain
outside Git:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_1/2026-10-18/
```

New files: `tools/build_sandbox.py`, `tools/build_sandbox_setup.sh`,
`tests/test_build_sandbox.py`, this report and the metadata/text evidence bundle.
No existing source, report, cache, configuration, experimental dataset or model
was edited. Only safe new source/tests/text/metadata are published.

## Reproduction and E.0.2 handoff

Read-only checking of the existing capture requires no Docker/Maven execution:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 timeout 60s taskset -c 0 \
  prlimit --as=1073741824 --cpu=45 --fsize=33554432 -- \
  .venv-forecast/bin/python - <<'PY_READONLY'
from pathlib import Path
from tools.build_sandbox import completeness
r = Path('/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_1/2026-10-18')
print(completeness(r)['status'])
PY_READONLY
```

Regression command (no real container or Maven):

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 prlimit --as=1073741824 --cpu=120 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_build_sandbox.py tests/test_phase5_2_2_e_0_compilation.py \
  tests/test_phase5_2_2_d_3_inspection.py tests/test_phase5_2_2_d_2_recovery.py \
  tests/test_phase5_2_2_d_1_continuation.py tests/test_phase5_2_2_d_recovery.py \
  tests/test_phase5_2_2_b_probes.py tests/test_phase5_2_2_a_review.py \
  tests/test_production_scope_readiness.py tests/test_multilanguage_preflight.py \
  tests/test_multilanguage_foundation.py
```

[E.0.2 handoff](examples/phase5_2_2_e_0_1/E_0_2_HANDOFF.md) specifies a separately
authorized one-container offline T0 compilation, expected2GiB/768MiB heap/240second
limits, immutable inputs and original lifecycle. This phase implements **no compile
adapter**. The smoke entry point rejects compilation commands. Do not call the
archived E.0 recipe or reset the consumed E.0/E.0.1 claims.

**STOP after verified E.0.1 publication. No E.0.2, Maven lifecycle, other revision,
Sonar, scan, dataset admission or model work started.**
