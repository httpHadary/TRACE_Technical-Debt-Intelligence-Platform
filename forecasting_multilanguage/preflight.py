"""Phase5.2 planning only: immutable Git inventory, never build/scan/model jobs.

This module deliberately does not change or relax the frozen schema2 scope or
admission policy. A failed gate remains failed in its proposed replay records.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath, Path
import hashlib
import argparse
import json

from .contracts import digest, iso, utc, revision
from .git_events import git, GitArchive
from .io import publish
from .registry import SCOPE_ID, source_language, EXCLUDE

OFFSETS = (-90, -30, 0, 30, 60, 90)
SOURCE_EXTENSIONS = {".java": "java", ".py": "py", ".pyi": "py",
                     ".js": "js", ".mjs": "js", ".cjs": "js", ".jsx": "js",
                     ".ts": "ts", ".tsx": "ts", ".css": "css", ".html": "web", ".htm": "web",
                     ".xml": "xml", ".jsp": "jsp", ".vue": "vue", ".svelte": "svelte",
                     ".c": "cpp", ".cpp": "cpp", ".h": "cpp", ".cs": "cs", ".go": "go",
                     ".kt": "kotlin", ".sh": "shell", ".bash": "shell", ".sql": "sql"}
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2", ".ttf", ".eot"}
DATA_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".properties", ".txt", ".md", ".rst", ".po", ".pot", ".mo"}
EXTRA_TEST_PARTS = {"testing", "testdata", "fixtures", "__mocks__", "example", "examples", "docs", "doc", "benchmarks"}


def six_cutoffs(t0):
    origin = utc(t0)
    return [{"offset_days": d, "cutoff_utc": iso(origin + timedelta(seconds=d * 86400))} for d in OFFSETS]


def classify_path(path, production_roots):
    p = PurePosixPath(path)
    if not path or p.is_absolute() or ".." in p.parts or "\\" in path:
        raise ValueError("Unsafe repository path")
    under_root = any(path == root or path.startswith(root.rstrip("/") + "/") for root in production_roots)
    parts = {v.lower() for v in p.parts[:-1]}
    if (parts & (set(EXCLUDE) | EXTRA_TEST_PARTS) or p.name.startswith(("test_", "conftest."))
            or ".test." in p.name or ".spec." in p.name
            or (p.name in ("package.html", "overview.html") and "java" in parts)):
        role = "TEST_VENDOR_GENERATED_DOC_OR_EXAMPLE"
    elif not under_root:
        role = "OUTSIDE_DECLARED_PRODUCTION_ROOTS"
    elif p.name.endswith((".min.js", ".min.css", ".map")):
        role = "GENERATED_OR_VENDOR_REVIEW_REQUIRED"
    elif p.suffix.lower() in SOURCE_EXTENSIONS:
        role = "PROPOSED_PRODUCTION_SOURCE"
    elif p.suffix.lower() in ASSET_EXTENSIONS:
        role = "PRODUCTION_ASSET_NOT_NATIVE_DEBT_SOURCE"
    elif p.suffix.lower() in DATA_EXTENSIONS or p.name in ("LICENSE", "NOTICE", "MANIFEST.in", "Makefile", "py.typed"):
        role = "PRODUCTION_RESOURCE_OR_METADATA_REVIEW_REQUIRED"
    else:
        role = "UNRECOGNIZED_PRODUCTION_EXTENSION_REVIEW_REQUIRED"
    return {"role": role, "extension": p.suffix.lower() or "<none>",
            "proposed_language": SOURCE_EXTENSIONS.get(p.suffix.lower()) if role == "PROPOSED_PRODUCTION_SOURCE" else None,
            "frozen_schema2_language": source_language(path)}


def tree_inventory(path, commit_sha, production_roots):
    """Enumerate every tracked entry, not merely a suffix-filtered subset.

    Line counts are nonblank source-text proxies, NOT Sonar NCLOC. Real language
    strata must be confirmed later from admitted analyzer coverage.
    """
    rows = []
    listing = git(path, "ls-tree", "-r", "-z", "--full-tree", revision(commit_sha))
    for line in listing.split(b"\0"):
        if not line:
            continue
        metadata, raw_path = line.split(b"\t", 1)
        mode, kind, object_id = metadata.decode().split()
        name = raw_path.decode("utf-8", errors="strict")
        record = dict(path=name, mode=mode, object_type=kind, git_object_id=object_id,
                      **classify_path(name, production_roots))
        if mode in ("120000", "160000"):
            record["role"] = "SYMLINK_OR_SUBMODULE_REQUIRES_SEPARATE_PROOF"
            record["proposed_language"] = None
        if record["role"] == "PROPOSED_PRODUCTION_SOURCE":
            data = git(path, "cat-file", "blob", object_id)
            if b"\0" in data:
                record["role"] = "BINARY_SOURCE_REQUIRES_REVIEW"
                record["proposed_language"] = None
            else:
                record["nonblank_lines_proxy"] = sum(bool(v.strip()) for v in data.splitlines())
        rows.append(record)
    return sorted(rows, key=lambda r: r["path"])


def first_parent_evidence(path, tip, observed_at):
    revision(tip)
    utc(observed_at)
    if git(path, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise ValueError("Shallow source cannot establish complete historical states")
    # Connectivity check does not write lost+found, rewrite refs or fetch objects.
    git(path, "fsck", "--connectivity-only", "--no-dangling", tip)
    raw = git(path, "log", "--first-parent", "--reverse", "--format=%H%x09%P%x09%ct%x09%T", tip)
    commits, inversions = [], []
    for line in raw.decode().splitlines():
        sha, parents, seconds, tree = line.split("\t")
        row = {"commit_sha": revision(sha), "parents": parents.split(), "tree_sha": revision(tree),
               "committer_utc": iso(datetime.fromtimestamp(int(seconds), timezone.utc))}
        if utc(row["committer_utc"]) > utc(observed_at):
            raise ValueError("Future-dated commit beyond ref observation")
        if commits:
            if not row["parents"] or row["parents"][0] != commits[-1]["commit_sha"]:
                raise ValueError("Missing first-parent ancestry")
            if utc(row["committer_utc"]) < utc(commits[-1]["committer_utc"]):
                inversions.append({"previous": commits[-1], "next": row})
        elif row["parents"]:
            raise ValueError("Unresolved root")
        commits.append(row)
    if not commits or commits[-1]["commit_sha"] != tip:
        raise ValueError("Tip mismatch")
    strict_error = None
    try:
        GitArchive(path, tip, observed_at)
    except ValueError as exc:
        strict_error = str(exc)
    return commits, {"complete_first_parent_objects": True, "connectivity_check": "PASS",
                     "first_parent_commit_count": len(commits), "lineage_sha256": digest(commits),
                     "timestamp_inversions": inversions,
                     "frozen_schema2_lineage_status": "BLOCKED" if strict_error else "PASS",
                     "frozen_schema2_error": strict_error}


def metadata_stratum(lines):
    groups = Counter()
    for key, count in lines.items():
        if key in ("java", "py", "js", "ts", "cpp", "cs", "go", "kotlin"):
            groups["jsts" if key in ("js", "ts") else key] += count
    total = sum(groups.values())
    shares = {k: v / total for k, v in sorted(groups.items())} if total else {}
    significant = sorted(k for k, share in shares.items() if share >= .1)
    if len(significant) >= 2:
        stratum = "mixed_python_jsts" if significant == ["jsts", "py"] else "mixed_other"
    elif shares and max(shares.values()) >= .8:
        stratum = {"java": "java_dominant", "py": "python_dominant", "jsts": "jsts_dominant"}.get(max(shares, key=shares.get), "other")
    else:
        stratum = "other"
    return {"proxy_programming_shares": shares, "proxy_stratum": stratum,
            "confirmed_sonar_ncloc_stratum": None, "status": "PROVISIONAL_SOURCE_TEXT_NOT_MEASURED_NCLOC"}


def plan_repository(config):
    """Config identifies sources/cutoffs, never carries debt outcomes or job commands."""
    required = {"repository_id", "family_id", "canonical_url", "provider_repository_id", "path", "tip_sha",
                "ref_observed_utc", "t0_utc", "production_roots", "expected_target", "license_paths", "build_paths"}
    if set(config) != required:
        raise ValueError("Exact metadata-only preflight config fields required")
    if config["expected_target"] not in ("java_dominant", "python_dominant", "mixed_python_jsts"):
        raise ValueError("Only the three registered development target families")
    for root in config["production_roots"]:
        if not root or root.startswith("/") or ".." in PurePosixPath(root).parts or root == "." or "\\" in root:
            raise ValueError("Explicit repository-relative production roots required")
    commits, lineage = first_parent_evidence(config["path"], config["tip_sha"], config["ref_observed_utc"])
    inventories, cutoffs = {}, []
    for cutoff in six_cutoffs(config["t0_utc"]):
        instant = utc(cutoff["cutoff_utc"])
        if instant > utc(config["ref_observed_utc"]):
            raise ValueError("Cutoff beyond observed ref")
        active = [c for c in commits if utc(c["committer_utc"]) <= instant]
        if not active:
            raise ValueError("No code state at registered cutoff")
        state = active[-1]
        # Historical inversions outside this window remain strict-schema2 blockers;
        # do not certify a local sorted-timestamp workaround as an admitted lineage.
        key = state["commit_sha"]
        if key not in inventories:
            inventories[key] = tree_inventory(config["path"], key, config["production_roots"])
        inventory = inventories[key]
        roles, languages, lines, omitted = Counter(), Counter(), Counter(), []
        for record in inventory:
            roles[record["role"]] += 1
            if record["proposed_language"]:
                languages[record["proposed_language"]] += 1
                lines[record["proposed_language"]] += record.get("nonblank_lines_proxy", 0)
            if bool(record["frozen_schema2_language"]) != (record["role"] == "PROPOSED_PRODUCTION_SOURCE"):
                omitted.append(record["path"])
        files = {v["path"]: v for v in inventory}
        evidence = {}
        for name in config["license_paths"] + config["build_paths"]:
            evidence[name] = {"status": "FOUND", "git_blob": files[name]["git_object_id"]} if name in files else {"status": "ABSENT_AT_REVISION"}
        cutoffs.append(dict(cutoff, **state, inventory_sha256=digest(inventory),
                            production_source_inventory_sha256=digest([r for r in inventory if r["role"] == "PROPOSED_PRODUCTION_SOURCE"]),
                            tracked_entries=len(inventory), role_counts=dict(sorted(roles.items())),
                            proposed_source_files_by_language=dict(sorted(languages.items())),
                            source_nonblank_lines_proxy=dict(sorted(lines.items())),
                            scope_vs_frozen_schema2_differences=omitted, source_evidence=evidence,
                            **metadata_stratum(lines)))
    window_start = utc(cutoffs[0]["cutoff_utc"])
    relevant = [v for v in lineage["timestamp_inversions"] if max(utc(v[k]["committer_utc"]) for k in ("previous", "next")) >= window_start]
    output = {k: v for k, v in config.items() if k != "path"}
    return {"preflight_version": 1, "schema_version": 2, "purpose": "DEVELOPMENT_REPLAY_PLAN_ONLY_NOT_ADMISSION",
            "source": output, "lineage": lineage, "window_inversion_count": len(relevant),
            "cutoffs": cutoffs, "distinct_cutoff_commits": len({c["commit_sha"] for c in cutoffs}),
            "frozen_scope_policy_hash": SCOPE_ID, "proposed_scope_status": "REQUIRES_NEW_VERSION_NOT_APPLIED",
            "actual_analysis_ids": [], "native_debt_values": None,
            "collection_authorized": False, "readiness": "BLOCKED_PENDING_CAPABILITY_DOMAIN_SCOPE_AND_RESOURCE_GATES"}, inventories


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    raw = Path(args.config).read_bytes()
    configs = json.loads(raw)
    if not isinstance(configs, list) or not configs or len({c["repository_id"] for c in configs}) != len(configs) or len({c["family_id"] for c in configs}) != len(configs):
        raise ValueError("Unique metadata-only repository/family records required")
    plans, artifacts = [], {}
    output = Path(args.output).resolve()
    for config in configs:
        if output.is_relative_to(Path(config["path"]).resolve()):
            raise ValueError("Output cannot be inside immutable Git source")
        plan, inventories = plan_repository(config)
        plans.append(plan)
        for sha, inventory in inventories.items():
            artifacts["inventory/" + digest([config["repository_id"], sha]) + ".json"] = inventory
    artifacts["source_replay_plans.json"] = sorted(plans, key=lambda p: p["source"]["repository_id"])
    return publish(args.output, artifacts, {"phase": "5.2", "config_sha256": hashlib.sha256(raw).hexdigest(),
                "scope": "METADATA_AND_SOURCE_INVENTORY_ONLY_NO_REPLAY", "schema2_scope_unchanged": SCOPE_ID})


if __name__ == "__main__":
    main()
