"""Source-only readiness evidence; no measurements, labels, builds or scans."""
import argparse
import json
from pathlib import Path
from ..contracts import digest
from ..git_events import GitArchive
from ..io import publish
from .scope import VERSION, REPOSITORIES, ScopedGit, policy
from .registry import contract_ids, validate_registration


def inspect_sources(configs, pinned_jobs):
    if (len(configs) != 3 or {c["repository_id"] for c in configs} != set(REPOSITORIES)
            or len(pinned_jobs) != 18):
        raise ValueError("Exactly three families and eighteen pinned jobs required")
    allowed = {"build_paths", "canonical_url", "expected_target", "family_id", "license_paths", "path",
               "production_roots", "provider_repository_id", "ref_observed_utc", "repository_id", "t0_utc", "tip_sha"}
    if any(set(c) != allowed for c in configs):
        raise ValueError("Exact source-only config fields required; outcome fields forbidden")
    records, registrations = [], []
    for config in sorted(configs, key=lambda r: r["repository_id"]):
        repo = config["repository_id"]
        pol = policy(repo)
        if (config["production_roots"] != [pol["root"]] or config["expected_target"] != pol["target"]
                or config["family_id"] != "github:" + pol["provider_repository_id"]
                or config["provider_repository_id"] != pol["provider_repository_id"]
                or config["canonical_url"] != "https://github.com/" + repo):
            raise ValueError("Pinned repository/root identity mismatch")
        lineage = ScopedGit(GitArchive(config["path"], config["tip_sha"], config["ref_observed_utc"]), repo)
        registration = dict(schema_version=2, contract_version=VERSION, study_id="phase5-production-root-development-v1",
            repository_id=repo, canonical_url=config["canonical_url"], provider_repository_id=pol["provider_repository_id"],
            family_id=config["family_id"], source_license_spdx={"java_dominant":"Apache-2.0", "python_dominant":"BSD-3-Clause", "mixed_python_jsts":"MIT"}[pol["target"]],
            data_reuse_terms="UNRESOLVED", source_reference="phase5_2_pinned_sources", source_digest=digest({k:v for k,v in config.items() if k != "path"}),
            exposure_status="EXPOSED", exposure_evidence_refs=["examples/phase5_2/source_candidates.json"], reserved_role="quarantine",
            branch_reference="pinned-first-parent-tip", branch_reference_observed_at=config["ref_observed_utc"],
            tip_sha=config["tip_sha"], lineage_policy="COMPLETE_FIRST_PARENT", declared_languages=pol["languages"],
            study_mode="RETROSPECTIVE_FIXED_ANALYZER", **contract_ids(repo))
        validate_registration(registration)
        registrations.append(registration)
        jobs = [j for j in pinned_jobs if j["repository_id"] == repo]
        if (len(jobs) != 6 or sorted(j["offset_days"] for j in jobs) != [-90, -30, 0, 30, 60, 90]
                or len({j["cutoff_utc"] for j in jobs}) != 6):
            raise ValueError("Pinned cutoff grid required")
        from datetime import timedelta
        from ..contracts import utc
        for job in jobs:
            if utc(job["cutoff_utc"]) != utc(config["t0_utc"]) + timedelta(days=job["offset_days"]):
                raise ValueError("Exact cutoff offset mismatch")
            state = lineage.state(job["cutoff_utc"])
            if state is None or state.sha != job["commit_sha"] or state.tree != job["tree_sha"]:
                raise ValueError("Pinned commit/tree differs from exact active state")
            inv = lineage.inventory(state.sha)
            counts = {k: sum(r["language"] == k for r in inv["entries"]) for k in pol["languages"]}
            if counts != job["expected_language_files"] or len(inv["production_paths"]) != job["expected_source_files"]:
                raise ValueError("Source coverage differs from original pinned plan")
            records.append(dict(repository_id=repo, family_id=config["family_id"], cutoff_utc=job["cutoff_utc"],
                offset_days=job["offset_days"], commit_sha=state.sha, tree_sha=state.tree,
                native_project_key_plan=job["native_project_key_plan"], expected_language_files=counts,
                inventory=inv, **contract_ids(repo)))
    return dict(version=VERSION, registrations=registrations, source_states=records,
                actual_measurements=0, actual_targets=0, collection_authorized=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--pinned-readiness", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = inspect_sources(json.loads(Path(args.config).read_text()),
                             json.loads(Path(args.pinned_readiness).read_text())["planned_jobs"])
    publish(Path(args.output), {"source_readiness.json":result}, {"phase":"5.2.1", "contract_version":VERSION})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
