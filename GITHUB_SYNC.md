# Central version-control destination

Repository: https://github.com/FadyYosry77/TechDebt360-MVP
Target branch: `main`. Completed phases are pushed only after their tests and
artifact verification pass. No force pushes, automatic phase advancement or bulk
dataset/model uploads.

## This machine's two checkouts

- Working project: `/home/hp/tst/td_pipeline_module_level/td_pipeline`.
- Central GitHub checkout: `/home/hp/tst/TechDebt360-MVP`.

The working project's original two-commit history and GitHub's starter/upload
history are unrelated. Both were inspected and preserved. The working project
now has `origin` pointing to the central repository and a `github-main` branch
tracking `origin/main`; its existing `main` and pre-existing changes were not
reset, rebased or checked out. Do not push the unrelated local `main` over remote
`main`. Publication uses the clean central checkout and fast-forward commits
based on its existing history.

For each future authorized phase:

1. Inspect both checkout statuses, local history, and remote `main`.
2. Update a clean central checkout with `git pull --ff-only origin main`.
3. Copy only the verified phase's explicit source/config/test/document and small
   evidence files from the working project. Compare target files before copying
   so unrelated remote changes are not overwritten. Never use a whole-directory
   recursive sync that includes caches, private config or generated data.
4. Run the relevant compatibility checks using the same verified code, inspect
   the staged diff, file sizes and secret patterns, then commit descriptively.
5. Push normally to `main`; if it cannot fast-forward, stop and reconcile or use
   a feature branch/PR. Never force-push. Verify remote SHA and key file contents.
6. Fetch the working project's `origin` and fast-forward only its `github-main`
   tracking reference. Do not move the original working `main` or its changes.

Dataset binaries, full generated history, checkpoints, environments and secrets
are excluded. Reproduce data locally from the source hash and configuration
template; phase-specific `examples/` folders contain attributed samples and useful
audit evidence. Absolute paths in historical records describe the original host,
not portable installation defaults. Copy the example config to an ignored
`study.phase1.local.json` and adjust paths for another machine.

Current authorization ends after Phase 4.2 frozen-cohort Chronos evaluation, verification and its GitHub push.
Further model tuning, retraining, CatBoost, Granite, dashboards and later phases require new authorization.
