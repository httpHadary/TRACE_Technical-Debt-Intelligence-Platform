"""Data-only commands. There is intentionally no model or scanner command."""
import argparse
from dataclasses import asdict, fields
import csv
from io import StringIO
import json
import hashlib
from pathlib import Path
from .adapters.v2 import read_only_database, source_audit, churn_audit, candidate_identity_audit
from .adapters.sonar_archive import read_archive
from .admission import PastStore, UnmeasuredOrigin
from .contracts import analyzer_domain, canonical, digest, utc, iso, Observation
from .features import build_features, prediction_input, FEATURE_CONTRACT, FEATURES
from .git_events import GitArchive, OutsideRefEvidence
from .inventory import discover_local_sources, exposure_inventory
from .io import publish, file_sha256
from .registry import PILOT_TARGETS
from .targets import origin_identity, target_status, TARGET_CONTRACT, ORIGIN_FIELDS, LABEL_FIELDS


def csv_bytes(rows, fields):
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build_archive(study_path, domain_path, index_path, archive, git_path, cutoffs_path, output):
    paths = list(map(Path, (study_path, domain_path, index_path, cutoffs_path)))
    raw_configs = [p.read_bytes() for p in paths]
    registration, manifest, index, cutoffs = [json.loads(data) for data in raw_configs]
    cutoffs = [iso(utc(c)) for c in cutoffs]
    if not cutoffs or len(cutoffs) != len(set(cutoffs)):
        raise ValueError("Unique preregistered origins required")
    if registration["reserved_role"] != "development":
        raise ValueError("Phase5.1 archive pilot is development-only")
    output_path = Path(output).resolve()
    if any(output_path.is_relative_to(Path(p).resolve()) for p in (archive, git_path)):
        raise ValueError("New artifacts must be outside immutable source archives/Git")
    source_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in zip(("study", "domain", "index", "cutoffs"), raw_configs)}
    domain = analyzer_domain(manifest)
    lineage = GitArchive(git_path, registration["tip_sha"], registration["branch_reference_observed_at"])
    observations = read_archive(archive, index)
    store = PastStore(registration, domain, lineage, observations)
    features, origins, labels, attempts = [], [], [], []
    # Features are completed before the independent endpoint builder is called.
    for cutoff in sorted(cutoffs):
        try:
            record = build_features(store, cutoff)
        except (UnmeasuredOrigin, OutsideRefEvidence) as exc:
            attempts.append({"origin_utc": cutoff, "status": "EXCLUDED", "reason": type(exc).__name__})
            continue
        prediction_input(record, expected_cutoff=cutoff)
        attempts.append({"origin_utc": cutoff, "status": "ADMITTED", "reason": None})
        features.append(record)
        origins.extend(origin_identity(store, cutoff, h) for h in (30, 60, 90))
    for origin in origins:
        labels.append(target_status(origin, store))
    snapshots, measures, languages = [], [], []
    for obs in observations:
        snapshot = asdict(obs)
        del snapshot["measures"], snapshot["languages"], snapshot["production_paths"]
        snapshot["observation_id"] = obs.observation_id
        snapshots.append(snapshot)
        for key, measure in sorted(obs.measures.items()):
            measures.append(dict(observation_id=obs.observation_id, metric_key=key,
                                 metric_semantics=manifest["metric_semantics"] if key == "sqale_index" else "native_" + key,
                                 scope_id=obs.scope_id, language_key="all", raw_metric_key=key,
                                 source_ref=obs.source_id, **asdict(measure)))
        for key, value in sorted(obs.languages.items()):
            languages.append(dict(observation_id=obs.observation_id, language_key=key, analyzed_ncloc=value,
                                  analyzer_plugin_key=next((p["key"] for p in manifest["plugins"] if p["language"] == key), "UNVERIFIED"),
                                  coverage_status="MEASURED_NCLOC_NOT_DEBT_SHARE"))
    feature_rows = [dict(context_id=f["context_id"], origin_utc=f["origin_utc"],
                         **prediction_input(f, expected_cutoff=f["origin_utc"])) for f in features]
    from datetime import timedelta
    admitted_cutoffs = [f["origin_utc"] for f in features]
    events = lineage.events(iso(min(map(utc, admitted_cutoffs)) - timedelta(days=90)), iso(max(map(utc, admitted_cutoffs)))) if admitted_cutoffs else []
    event_rows = []
    positions = {c.sha: i for i, c in enumerate(lineage.commits)}
    for event in events:
        commit = lineage.by_sha[event["commit_sha"]]
        row = dict(event, paths=canonical(event["paths"]).decode(), repository_id=registration["repository_id"],
                   family_id=registration["family_id"], first_parent_sha=commit.parents[0] if commit.parents else None,
                   ancestry_index=positions[commit.sha], is_merge=len(commit.parents) > 1,
                   additions=None, removals=None, delta_status="F2_DISABLED", raw_source_ref=lineage.identity)
        event_rows.append(row)
    artifacts = {"feature_evidence.jsonl": b"".join(canonical(r) + b"\n" for r in features),
                 "origin_admission.json": attempts,
                 "features.csv": csv_bytes(feature_rows, ["context_id", "origin_utc"] + [k for n in FEATURES for k in (n, n + "__missing")]),
                 "analysis_snapshots.csv": csv_bytes(snapshots, [f.name for f in fields(Observation) if f.name not in ("measures", "languages", "production_paths")] + ["observation_id"]),
                 "measurements.csv": csv_bytes(measures, ("observation_id", "metric_key", "metric_semantics", "scope_id", "language_key", "raw_metric_key", "source_ref", "value", "status", "reason", "unit")),
                 "language_coverage.csv": csv_bytes(languages, ("observation_id", "language_key", "analyzed_ncloc", "analyzer_plugin_key", "coverage_status")),
                 "source_provenance.json": {"payloads": index, "lineage_identity": lineage.identity},
                 "git_events.csv": csv_bytes(event_rows, ("commit_sha", "state_utc", "available_utc", "paths", "event_id",
                    "repository_id", "family_id", "first_parent_sha", "ancestry_index", "is_merge", "additions", "removals", "delta_status", "raw_source_ref")),
                 "cohorts.json": {"role": registration["reserved_role"], "family_id": registration["family_id"],
                                  "forecast_ids": sorted(o["forecast_id"] for o in origins), "confirmatory_enrollment": False},
                 "forecast_origins.csv": csv_bytes(origins, ORIGIN_FIELDS),
                 "forecast_labels.csv": csv_bytes(labels, LABEL_FIELDS),
                 "repository_registry.json": registration, "analyzer_domains.json": domain,
                 "readiness.json": {"schema_version": 2, "feature_contexts": len(features), "excluded_origins": len(cutoffs) - len(features),
                                    "status": "DATA_CONTRACTS_READY" if features else "BLOCKED_NO_MEASURED_ORIGINS",
                                    "distinct_states": len({o.commit_sha for o in observations}),
                                    "distinct_analyses": len(observations),
                                    "label_statuses": {s: sum(l["label_status"] == s for l in labels) for s in sorted({l["label_status"] for l in labels})},
                                    "F2_enabled": False}}
    return publish(output, artifacts, {"source_hashes": source_hashes, "lineage_identity": lineage.identity,
                                      "feature_contract_id": FEATURE_CONTRACT, "target_contract_id": TARGET_CONTRACT})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit-legacy")
    audit.add_argument("--db", required=True)
    audit.add_argument("--sha256", required=True)
    audit.add_argument("--git-sources", required=True, help="JSON PROJECT_ID -> existing Git checkout")
    audit.add_argument("--output", required=True)
    local = sub.add_parser("inventory-local")
    local.add_argument("--root", action="append", required=True)
    local.add_argument("--output", required=True)
    local.add_argument("--exposure-records", help="Additional metadata-only prior-family identities and source refs")
    local.add_argument("--exclude", action="append", default=[], help="Exclude model/frozen/output roots from metadata search")
    archive = sub.add_parser("build-archive")
    for name in ("study", "domain", "index", "archive", "git", "cutoffs", "output"):
        archive.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    if args.command == "audit-legacy":
        sources = json.loads(Path(args.git_sources).read_text())
        with read_only_database(args.db, args.sha256) as con:
            evidence = source_audit(con)
            churn = churn_audit(con, sources)
            identities = candidate_identity_audit(con, args.sha256)
        publish(args.output, {"legacy_source_audit.json": evidence, "churn_diagnostics.json": churn,
                             "legacy_identity_audit.json": identities},
                {"source_sha256": args.sha256, "source_license": "CC-BY-NC-SA-4.0",
                 "source_url": "https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1",
                 "git_sources_sha256": file_sha256(args.git_sources)})
    elif args.command == "inventory-local":
        out = Path(args.output).resolve()
        if any(out.is_relative_to(Path(r).resolve()) for r in args.root) and not any(out.is_relative_to(Path(r).resolve()) for r in args.exclude):
            raise ValueError("Inventory output inside search roots must have an explicit excluded ancestor")
        evidence = discover_local_sources(args.root, excluded_roots=args.exclude)
        records = json.loads(Path(args.exposure_records).read_text()) if args.exposure_records else []
        for repo in evidence["git_repositories"]:
            records.append({"identity": repo["canonical_url"], "source_ref": "local_git_metadata"})
        for registry in evidence["exposure_registries"]:
            for row in registry["identities"]:
                for key in ("repository", "repository_id", "repo", "url"):
                    if row.get(key):
                        records.append({"identity": row[key], "source_ref": registry["sha256"]})
                        break
        publish(args.output, {"local_inventory.json": evidence,
                             "exposure_inventory.json": exposure_inventory(records),
                             "pilot_readiness.json": {"targets": list(PILOT_TARGETS), "admitted": [],
                                                      "status": "PARTIAL/BLOCKED_NONJAVA_DATA"}},
                {"search": "explicit_local_roots_only_no_network_no_scans"})
    else:
        build_archive(args.study, args.domain, args.index, args.archive, args.git, args.cutoffs, args.output)
    return 0
