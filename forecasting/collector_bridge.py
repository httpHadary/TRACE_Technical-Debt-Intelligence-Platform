"""Isolated adapter for the repaired collector's workspace-local configuration.

Invoked in a child process with cwd=workspace; no collector globals in the parent
are changed. All inputs are verified before being exported to the new layer.
"""
from dataclasses import asdict
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import argparse
import re

from contracts import read_csv, read_json, sha256, write_json
from forecasting.schema import Snapshot, iso, timestamp

ENDPOINT_DATA = Path("forecast_endpoints/data")


@contextmanager
def evidence_namespace(directory):
    """Redirect only this isolated adapter's collector imports; restore on exit.

    Supplemental endpoints must never enter legacy weekly CSV registries. Raw
    proof paths remain in their original namespace; existing evidence is not moved
    or rewritten to pretend it came from another scanner work directory.
    """
    import sonar_evidence
    import scan_snapshot
    import scan_weekly_snapshots
    import build_module_mart
    targets = [(sonar_evidence, "DATA"), (scan_snapshot, "DATA"),
               (scan_weekly_snapshots, "DATA"), (build_module_mart, "DATA_DIR")]
    original = [(module, name, getattr(module, name)) for module, name in targets]
    try:
        for module, name in targets:
            setattr(module, name, Path(directory))
        yield
    finally:
        for module, name, value in original:
            setattr(module, name, value)


def _load_current(data, recovery_cutoffs=None):
    import config
    import build_module_mart as mart
    from sonar_evidence import verify_snapshot
    from forecasting.git import GitRepository

    context = read_json("repo_context.json")
    for name, key in (("REPO_PATH", "repo_path"), ("REPOSITORY_ID", "repository_id"),
                      ("PROJECT_KEY", "project_key"), ("BRANCH", "branch")):
        if not context.get(key):
            raise ValueError(f"Missing workspace context: {key}")
        setattr(config, name, context[key])
    scope = (tuple(read_json("module_strategy.json").get("scope", ())) if Path("module_strategy.json").exists()
             else tuple(config.EXTRA_PRODUCTION_ROOTS))
    config.EXTRA_PRODUCTION_ROOTS = scope
    repo = GitRepository(context["repo_path"], scope)
    _, rows = read_csv(data / "snapshots.csv", required=["label", "commit_hash"], key="label")
    if not rows:
        raise ValueError("No verified snapshots")
    endpoints = {}
    if (data / "forecast_endpoint_cutoffs.json").exists():
        endpoints = read_json(data / "forecast_endpoint_cutoffs.json")
    for label, cutoff in (recovery_cutoffs or {}).items():
        if label in endpoints and endpoints[label] != cutoff:
            raise ValueError("Recovery cutoff conflicts with recorded endpoint")
        endpoints[label] = cutoff
    first = read_json(data / f"complete_{rows[0]['label']}.json")
    # These are the recorded server identities, used for read-only verification.
    config.SONAR_URL, config.SONAR_URL_FROM_SCANNER = first["sonar_url"], first["scanner_sonar_url"]
    result, inputs, seen = [], {}, set()

    class FileMapper:
        def module_of(self, path):
            return path

    start = timestamp(context["start_date"] + "T00:00:00+00:00")
    for row in rows:
        label, commit = row["label"], row["commit_hash"]
        match = re.fullmatch(r"week_(\d+)", label)
        if match:
            cutoff = iso(start + timedelta(days=7 * int(match.group(1))))
            weekly = True
        elif label in endpoints:
            cutoff, weekly = iso(endpoints[label]), False
        else:
            raise ValueError(f"No explicit calendar cutoff for snapshot {label}")
        if cutoff in seen:
            raise ValueError("Duplicate repository cutoff")
        seen.add(cutoff)
        if repo.resolve(context["branch"], cutoff) != commit:
            raise ValueError(f"{label}: commit differs from exact cutoff resolver")
        proof = verify_snapshot(label, context["repo_path"], commit)
        states, _ = mart.aggregate_week(label, FileMapper(), proof["eligible_paths"])
        files = {p: {"sqale_minutes": s["sqale_index"], "combined_effort_minutes": s["td"],
                     "ncloc": s["ncloc"], "complexity": s["complexity"],
                     "cognitive_complexity": s["cognitive_complexity"], "finding_count": s["findings"]}
                 for p, s in states.items()}
        result.append(Snapshot(context["repository_id"], cutoff, commit, files,
                               proof["metadata"], label, weekly, scope))
        for path in (data / f"complete_{label}.json", data / f"measures_{label}.csv", data / f"issues_{label}.json"):
            inputs[str(Path(path).resolve())] = sha256(path)
        for path in proof["artifacts"]:
            raw = data / path
            inputs[str(raw.resolve())] = sha256(raw)
    for path in ("repo_context.json", "module_strategy.json", data / "forecast_endpoint_cutoffs.json",
                 data / "snapshots.csv", data / "analysis_metadata.csv"):
        if Path(path).exists():
            inputs[str(Path(path).resolve())] = sha256(path)
    source_root = Path(__file__).resolve().parents[1]
    for name in ("config.py", "contracts.py", "modules.py", "build_module_mart.py", "sonar_evidence.py",
                 "scan_snapshot.py", "weekly_commits.py", "td_utils.py"):
        inputs[str(source_root / name)] = sha256(source_root / name)
    result.sort(key=lambda s: timestamp(s.cutoff))
    return {"repo_path": context["repo_path"], "branch": context["branch"],
            "snapshots": [asdict(s) for s in result], "input_hashes": inputs,
            "collector_contract": "repaired_snapshot_v1"}


def load_verified(recovery_cutoffs=None):
    with evidence_namespace(Path("data")):
        result = _load_current(Path("data"))
    if (ENDPOINT_DATA / "snapshots.csv").exists():
        with evidence_namespace(ENDPOINT_DATA):
            supplemental = _load_current(ENDPOINT_DATA, recovery_cutoffs)
        if supplemental["repo_path"] != result["repo_path"] or supplemental["branch"] != result["branch"]:
            raise ValueError("Supplemental endpoint repository differs")
        known = {s["cutoff"] for s in result["snapshots"]}
        if any(s["weekly"] or s["cutoff"] in known for s in supplemental["snapshots"]):
            raise ValueError("Supplemental endpoints conflict with weekly origins")
        result["snapshots"].extend(supplemental["snapshots"])
        result["snapshots"].sort(key=lambda s: timestamp(s["cutoff"]))
        result["input_hashes"].update(supplemental["input_hashes"])
    return result


def collect_endpoints(requests):
    from scan_snapshot import scan_snapshot
    from sonar_evidence import collect_snapshot, verify_snapshot, workspace_lock
    from scan_weekly_snapshots import fill_week_from
    from forecasting.git import GitRepository
    records = read_json(requests)
    if not isinstance(records, list):
        raise ValueError("Endpoint requests must be a list")
    if len({r["label"] for r in records}) != len(records) or len({iso(r["cutoff"]) for r in records}) != len(records):
        raise ValueError("Duplicate endpoint request identity/cutoff")
    context = read_json("repo_context.json")
    if any(r["repository_id"] != context["repository_id"] for r in records):
        raise ValueError("Endpoint request belongs to another repository")
    # Parent lock also prevents simultaneous weekly collection against this project.
    with workspace_lock():
        verified = load_verified({r["label"]: iso(r["cutoff"]) for r in records})
        repo = GitRepository(verified["repo_path"])
        repository_id = verified["snapshots"][0]["repository_id"]
        # Validate all requests before submitting any scanner work.
        for request in records:
            if request["repository_id"] != repository_id:
                raise ValueError("Endpoint request belongs to another repository")
            cutoff, label = iso(request["cutoff"]), request["label"]
            if timestamp(cutoff) > datetime.now(timezone.utc):
                raise ValueError("Cannot collect a future endpoint cutoff")
            if timestamp(cutoff) != timestamp(request["origin_cutoff"]) + timedelta(days=90):
                raise ValueError("Endpoint request is not exactly 90 days")
            if not any(s["weekly"] and s["cutoff"] == iso(request["origin_cutoff"]) for s in verified["snapshots"]):
                raise ValueError("Endpoint request has no verified weekly origin")
            commit = repo.resolve(verified["branch"], cutoff)
            if not commit or commit != request["commit"]:
                raise ValueError("Endpoint request commit changed")
        with evidence_namespace(ENDPOINT_DATA):
            index_path = ENDPOINT_DATA / "forecast_endpoint_cutoffs.json"
            index = read_json(index_path) if index_path.exists() else {}
            with workspace_lock():
                reusable = [s for s in verified["snapshots"] if not s["weekly"]]
                for request in records:
                    cutoff, label, commit = iso(request["cutoff"]), request["label"], request["commit"]
                    if label in index and index[label] != cutoff:
                        raise ValueError("Endpoint cutoff conflict")
                    if (ENDPOINT_DATA / f"complete_{label}.json").exists():
                        verify_snapshot(label, repo.path, commit)
                    elif (ENDPOINT_DATA / f"pending_{label}.json").exists():
                        if read_json(ENDPOINT_DATA / f"pending_{label}.json")["commit"] != commit:
                            raise ValueError("Pending endpoint mismatch")
                        collect_snapshot(label)
                    else:
                        same = next((s["label"] for s in reusable if s["commit"] == commit), None)
                        if same:
                            fill_week_from(same, label)
                        else:
                            scan_snapshot(commit, label)
                            collect_snapshot(label)
                    index[label] = cutoff
                    write_json(index_path, index)
                    reusable.append({"label": label, "commit": commit})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    parser.add_argument("--collect-endpoints")
    args = parser.parse_args()
    if args.collect_endpoints:
        collect_endpoints(args.collect_endpoints)
    elif args.output:
        from sonar_evidence import workspace_lock
        with workspace_lock():
            write_json(args.output, load_verified())
    else:
        parser.error("--output or --collect-endpoints required")


if __name__ == "__main__":
    main()
