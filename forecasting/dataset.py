"""Deterministic transformations from verified snapshots to model-ready artifacts."""
from collections import Counter
from datetime import timedelta
from importlib.metadata import version
from pathlib import Path
import io
import json

import numpy as np

from contracts import atomic_bytes, digest, read_json, sha256, write_csv, write_json
from . import SCHEMA_VERSION
from .git import GitRepository
from .graphs import extract_graph
from .identity import IdentityTracker, ModuleDefinition
from .schema import (BASE_FEATURES, GRAPH_FEATURES, SEQUENCE_FEATURES, Snapshot, ForecastConfig,
                     COMPATIBILITY_FIELDS, assert_available, compatible, finite, iso, observation_id, timestamp)

KEYS = ("repository_id", "stable_module_id", "prediction_timestamp", "observation_id")
LABEL_FIELDS = (*KEYS, "horizon", "horizon_days", "label_end_timestamp", "target_status", "exclusion_reason",
                "debt_delta_minutes", "growth_label", "growth_threshold_minutes", "future_sqale_minutes",
                "membership_changed", "added_files", "removed_files", "retained_files",
                "retained_debt_delta_minutes", "added_debt_minutes", "removed_debt_minutes")
STATE_FIELDS = (*KEYS, "module_path", "module_strategy", "module_config_id", "birth_timestamp", "lineage_status",
                "membership_hash", "commit", "snapshot_label", "analyzer_signature", "max_feature_timestamp", *BASE_FEATURES)
GRAPH_FIELDS = (*KEYS, "max_feature_timestamp", "analyzer_signature", "graph_status", *GRAPH_FEATURES,
                "parsed_files", "total_files", "imports", "build_total", "build_parsed")
MEMBERSHIP_FIELDS = (*KEYS, "module_path", "module_strategy", "module_config_id", "file_path", "stable_file_id",
                     "blob", "sqale_minutes", "combined_effort_minutes", "ncloc")


def observed_sum(values):
    values = [finite(v) for v in values]
    return sum(values) if all(v is not None for v in values) else None


def source_hashes():
    base = Path(__file__).parent
    return {p.name: sha256(p) for p in sorted(base.glob("*.py"))} | {
        p.name: sha256(p) for p in (base.parent / "requirements-forecast.txt", base.parent / "requirements-forecast-lock.txt")}


def package_versions():
    import platform
    return {"python": platform.python_version(), **{name: version(name) for name in
            ("numpy", "networkx", "pandas", "scikit-learn", "catboost", "scipy", "requests", "openpyxl")}}


def temporal_features(history, current, weeks):
    available = [h for h in history if compatible([h["snapshot"], current["snapshot"]])]
    result = {"history_points": len(available), "history_fraction": len(available) / weeks}
    for feature in ("sqale_minutes", "ncloc", "complexity", "finding_count"):
        points = [(timestamp(h["snapshot"].cutoff), h[feature]) for h in available if h[feature] is not None]
        result[feature + "_observed_26w"] = len(points)
        result[feature + "_mean_26w"] = float(np.mean([v for _, v in points])) if points else None
        slope = None
        if len(points) > 1:
            x = np.array([(d - points[0][0]).total_seconds() / (7 * 86400) for d, _ in points])
            y = np.array([v for _, v in points])
            slope = float(np.dot(x - x.mean(), y - y.mean()) / np.dot(x - x.mean(), x - x.mean()))
        result[feature + "_slope_26w"] = slope
    return result


def make_label(origin, records, snapshots, config):
    cutoff = origin["snapshot"].cutoff
    end = iso(timestamp(cutoff) + timedelta(days=config.days))
    row = {k: origin[k] for k in KEYS}
    row.update(horizon=config.horizon, horizon_days=config.days, label_end_timestamp=end,
               target_status="UNKNOWN_OBSERVATION", exclusion_reason="endpoint_snapshot_unavailable",
               debt_delta_minutes=None, growth_label=None, growth_threshold_minutes=config.growth_threshold_minutes,
               future_sqale_minutes=None, membership_changed=None, added_files=None, removed_files=None,
               retained_files=None, retained_debt_delta_minutes=None, added_debt_minutes=None, removed_debt_minutes=None)
    endpoint = snapshots.get(end)
    if endpoint is None:
        return row
    future = records.get((origin["stable_module_id"], end))
    if future is None:
        row["exclusion_reason"] = "module_deleted_or_lineage_unresolved"
        return row
    window = [s for d, s in snapshots.items() if timestamp(cutoff) <= timestamp(d) <= timestamp(end)]
    if not compatible(window):
        row.update(target_status="INCOMPATIBLE", exclusion_reason="analyzer_incompatible_in_target_window")
        return row
    lineage = [r for (sid, date), r in records.items() if sid == origin["stable_module_id"]
               and timestamp(cutoff) <= timestamp(date) <= timestamp(end)]
    if any(r["lineage_status"].startswith("AMBIGUOUS") for r in lineage):
        row["exclusion_reason"] = "ambiguous_module_lineage"
        return row
    before, after = origin["file_debt"], future["file_debt"]
    common, added, removed = before.keys() & after.keys(), after.keys() - before.keys(), before.keys() - after.keys()
    a, r = observed_sum(after[p] for p in added), observed_sum(before[p] for p in removed)
    c0, c1 = observed_sum(before[p] for p in common), observed_sum(after[p] for p in common)
    row.update(membership_changed=int(bool(added or removed)), added_files=len(added), removed_files=len(removed),
               retained_files=len(common), retained_debt_delta_minutes=c1 - c0 if c0 is not None and c1 is not None else None,
               added_debt_minutes=a, removed_debt_minutes=r, future_sqale_minutes=future["sqale_minutes"])
    if origin["sqale_minutes"] is None or future["sqale_minutes"] is None:
        row["exclusion_reason"] = "current_or_future_sqale_unobserved"
        return row
    delta = future["sqale_minutes"] - origin["sqale_minutes"]
    row.update(target_status="OBSERVED", exclusion_reason="", debt_delta_minutes=delta,
               growth_label=int(delta > config.growth_threshold_minutes))
    return row


def describe(rows, labels):
    observed = [r for r in labels if r["target_status"] == "OBSERVED"]
    values = np.array([r["debt_delta_minutes"] for r in observed], dtype=float)
    return {"observations": len(rows), "repositories": len({r["repository_id"] for r in rows}),
            "modules": len({(r["repository_id"], r["stable_module_id"]) for r in rows}),
            "repository_snapshot_blocks": len({(r["repository_id"], r["prediction_timestamp"]) for r in rows}),
            "target_status_counts": dict(Counter(r["target_status"] for r in labels)),
            "exclusion_reason_counts": dict(Counter(r["exclusion_reason"] for r in labels if r["exclusion_reason"])),
            "eligible_labels": len(observed), "growth_events": sum(r["growth_label"] for r in observed),
            "changed_debt_observations": sum(r["debt_delta_minutes"] != 0 for r in observed),
            "membership_changed_targets": sum(r["membership_changed"] for r in observed),
            "incomplete_history_observations": sum(r["history_fraction"] < 1 for r in rows),
            "predictor_missing_counts": {k: sum(r.get(k) is None for r in rows) for k in BASE_FEATURES + GRAPH_FEATURES},
            "target_distribution_minutes": dict(zip(("min", "p25", "median", "p75", "max"),
                map(float, np.quantile(values, [0, .25, .5, .75, 1])))) if len(values) else None}


def transform(sources, config):
    states, memberships, identities_out, edges_out, graph_rows, unresolved_out, lineage_out, labels = [], [], [], [], [], [], [], []
    sequences, masks, snapshot_masks, sequence_times, sequence_ids = [], [], [], [], []
    definitions, input_hashes, seen_repositories = [], {}, set()
    for source in sources:
        snapshots = sorted([Snapshot(**s) if isinstance(s, dict) else s for s in source["snapshots"]],
                           key=lambda s: timestamp(s.cutoff))
        if not snapshots:
            raise ValueError("Empty repository snapshots")
        repository_id = snapshots[0].repository_id
        if repository_id in seen_repositories or any(s.repository_id != repository_id for s in snapshots):
            raise ValueError("Duplicate or mixed repository identities")
        seen_repositories.add(repository_id)
        if len({s.cutoff for s in snapshots}) != len(snapshots):
            raise ValueError("Duplicate repository cutoffs")
        if any(tuple(s.scope) != tuple(snapshots[0].scope) for s in snapshots):
            raise ValueError("Production scope changed within repository history")
        repo = GitRepository(source["repo_path"], snapshots[0].scope)
        definition = ModuleDefinition.create(repo, snapshots[0], config)
        definitions.append({**definition.__dict__, "config_id": definition.config_id})
        input_hashes.update(source.get("input_hashes", {}))
        tracker, previous_file_ids, previous_commit = IdentityTracker(definition), {}, None
        records, by_time = {}, {s.cutoff: s for s in snapshots}
        weekly_records = []
        for snapshot in snapshots:
            expected = {p for p in repo.tree(snapshot.commit) if repo.production(p)}
            if set(snapshot.files) != expected:
                raise ValueError("Snapshot file population differs from historical production tree")
            if repo.resolve(source["branch"], snapshot.cutoff) != snapshot.commit:
                raise ValueError("Snapshot commit differs from cutoff resolver")
            rename_pairs = repo.rename_pairs(previous_commit, snapshot.commit) if previous_commit else {}
            inherited = {rename_pairs.get(p, p): fid for p, fid in previous_file_ids.items()}
            file_ids = {p: inherited.get(p, digest([repository_id, p, snapshot.cutoff])) for p in expected}
            previous_file_ids, previous_commit = file_ids, snapshot.commit
            identities, packages, events = tracker.update(repo, snapshot)
            graph_edges, statistics, unresolved = extract_graph(repo, snapshot, identities, packages,
                                                                 definition, config.history_weeks * 7)
            graph_key = {"repository_id": repository_id, "prediction_timestamp": snapshot.cutoff,
                         "max_feature_timestamp": snapshot.cutoff}
            edges_out.extend({**graph_key, **e} for e in graph_edges)
            unresolved_out.extend({**graph_key, **e} for e in unresolved)
            lineage_out.extend({**graph_key, **e} for e in events)
            for name, identity in sorted(identities.items()):
                sid = identity["stable_module_id"]
                keys = {"repository_id": repository_id, "stable_module_id": sid,
                        "prediction_timestamp": snapshot.cutoff,
                        "observation_id": observation_id(repository_id, sid, snapshot.cutoff)}
                current = {**keys, **{k: v for k, v in identity.items() if k not in ("paths", "parent_ids")},
                           "module_strategy": definition.strategy, "module_config_id": definition.config_id,
                           "commit": snapshot.commit, "snapshot_label": snapshot.label,
                           "analyzer_signature": digest([snapshot.metadata[k] for k in COMPATIBILITY_FIELDS]),
                           "max_feature_timestamp": snapshot.cutoff, "snapshot": snapshot,
                           "file_count": len(identity["paths"]), "membership_changed": int(identity["lineage_status"] != "CONTINUING"),
                           "file_debt": {file_ids[p]: snapshot.files[p]["sqale_minutes"] for p in identity["paths"]}}
                for metric in SEQUENCE_FEATURES[:6]:
                    current[metric] = observed_sum(snapshot.files[p].get(metric) for p in identity["paths"])
                current.update({k: statistics[name][k] for k in GRAPH_FEATURES})
                records[(sid, snapshot.cutoff)] = current
                history = [records[(sid, iso(timestamp(snapshot.cutoff) - timedelta(weeks=i)))]
                           for i in reversed(range(config.history_weeks))
                           if (sid, iso(timestamp(snapshot.cutoff) - timedelta(weeks=i))) in records
                           and records[(sid, iso(timestamp(snapshot.cutoff) - timedelta(weeks=i)))]["snapshot"].weekly]
                assert_available(snapshot.cutoff, [h["snapshot"].cutoff for h in history])
                current.update(temporal_features(history, current, config.history_weeks))
                # Activity is read from the snapshot ancestry. Historical group names are
                # resolved at their commit by the graph extractor; no future paths are used.
                current.update(commits_26w=statistics[name].get("commits_26w", 0),
                               churn_26w=statistics[name].get("churn_26w", 0),
                               authors_26w=statistics[name].get("authors_26w", 0))
                identities_out.append({**keys, "module_path": name, "module_strategy": definition.strategy,
                    "module_config_id": definition.config_id, "birth_timestamp": identity["birth_timestamp"],
                    "lineage_status": identity["lineage_status"], "membership_hash": identity["membership_hash"],
                    "parent_ids": json.dumps(identity["parent_ids"]), "active": 1})
                graph_rows.append({**keys, "max_feature_timestamp": snapshot.cutoff,
                                   "analyzer_signature": current["analyzer_signature"],
                                   **{k: statistics[name][k] for k in GRAPH_FIELDS if k in statistics[name]}})
                for path in sorted(identity["paths"]):
                    memberships.append({**keys, "module_path": name, "module_strategy": definition.strategy,
                        "module_config_id": definition.config_id, "file_path": path, "stable_file_id": file_ids[path],
                        "blob": repo.tree(snapshot.commit)[path],
                        **{k: snapshot.files[path].get(k) for k in ("sqale_minutes", "combined_effort_minutes", "ncloc")}})
                if not snapshot.weekly:
                    continue
                states.append({k: current[k] for k in STATE_FIELDS})
                weekly_records.append(current)
                sequence = np.zeros((config.history_weeks, len(SEQUENCE_FEATURES)), dtype=np.float64)
                mask = np.zeros_like(sequence, dtype=bool)
                present = np.zeros(config.history_weeks, dtype=bool)
                dates = []
                for index, i in enumerate(reversed(range(config.history_weeks))):
                    date = iso(timestamp(snapshot.cutoff) - timedelta(weeks=i))
                    dates.append(date)
                    h = records.get((sid, date))
                    if h and h["snapshot"].weekly and compatible([h["snapshot"], snapshot]):
                        present[index] = True
                        for j, feature in enumerate(SEQUENCE_FEATURES):
                            value = finite(h.get(feature))
                            if value is not None:
                                sequence[index, j], mask[index, j] = value, True
                sequences.append(sequence); masks.append(mask); snapshot_masks.append(present)
                sequence_times.append(dates); sequence_ids.append(keys["observation_id"])
        labels.extend(make_label(r, records, by_time, config) for r in weekly_records)
    shape = (len(sequences), config.history_weeks, len(SEQUENCE_FEATURES))
    arrays = {"values": np.array(sequences).reshape(shape), "feature_mask": np.array(masks, dtype=bool).reshape(shape),
              "snapshot_mask": np.array(snapshot_masks, dtype=bool).reshape((len(sequences), config.history_weeks)),
              "timestamps": np.array(sequence_times, dtype="U32").reshape((len(sequences), config.history_weeks)),
              "observation_ids": np.array(sequence_ids, dtype="U64"),
              "feature_names": np.array(SEQUENCE_FEATURES, dtype="U64")}
    return {"states": states, "memberships": memberships, "identities": identities_out,
            "edges": edges_out, "graphs": graph_rows, "unresolved": unresolved_out, "lineage": lineage_out,
            "labels": labels, "arrays": arrays, "definitions": definitions, "input_hashes": input_hashes}


def build_dataset(sources, config, output, data_kind="historical_sonar"):
    if data_kind not in ("synthetic", "historical_sonar"):
        raise ValueError("Unknown data kind")
    if data_kind == "historical_sonar" and any(s.get("collector_contract") != "repaired_snapshot_v1" or
                                              not s.get("input_hashes") for s in sources):
        raise ValueError("Historical Sonar datasets require verified collector inputs")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)  # Immutable generation, never overwrite old data.
    manifest = {"schema_version": SCHEMA_VERSION, "status": "RUNNING", "data_kind": data_kind,
                "prediction_contract": config.contract(), "implementation": source_hashes(),
                "environment": package_versions()}
    write_json(output / "manifest.json", manifest)
    try:
        input_hashes = {p: checksum for source in sources for p, checksum in source.get("input_hashes", {}).items()}
        if any(sha256(p) != checksum for p, checksum in input_hashes.items()):
            raise ValueError("Collector inputs changed after verification")
        data = transform(sources, config)
        if any(sha256(p) != checksum for p, checksum in input_hashes.items()):
            raise ValueError("Collector inputs changed during transformation")
        tables = {
            "module_weekly_state.csv": (data["states"], STATE_FIELDS),
            "module_membership.csv": (data["memberships"], MEMBERSHIP_FIELDS),
            "module_identity.csv": (data["identities"], (*KEYS, "module_path", "module_strategy", "module_config_id",
                "birth_timestamp", "lineage_status", "membership_hash", "parent_ids", "active")),
            "module_edges_weekly.csv": (data["edges"], ("repository_id", "prediction_timestamp", "max_feature_timestamp",
                "source", "target", "edge_type", "weight", "directed")),
            "module_graph_features.csv": (data["graphs"], GRAPH_FIELDS),
            "module_labels.csv": (data["labels"], LABEL_FIELDS),
        }
        for name, (rows, fields) in tables.items():
            write_csv(output / name, rows, fields)
        for name, rows in (("module_lineage.json", data["lineage"]), ("unresolved_dependencies.json", data["unresolved"])):
            write_json(output / name, rows)
        buffer = io.BytesIO()
        np.savez_compressed(buffer, **data["arrays"])
        atomic_bytes(output / "module_sequences.npz", buffer.getvalue())
        graph_by_id = {r["observation_id"]: r for r in data["graphs"]}
        joined = [{**r, **{k: graph_by_id[r["observation_id"]][k] for k in GRAPH_FEATURES}} for r in data["states"]]
        write_json(output / "dataset_audit.json", describe(joined, data["labels"]))
        hashes = {p.name: sha256(p) for p in sorted(output.iterdir()) if p.name != "manifest.json"}
        manifest.update(status="COMPLETE", outputs=hashes, input_hashes=data["input_hashes"],
            module_definitions=data["definitions"], predictor_allowlist={"M1": list(BASE_FEATURES), "M2": list(BASE_FEATURES + GRAPH_FEATURES)},
            sequence_features=list(SEQUENCE_FEATURES), sequence_weeks=config.history_weeks,
            feature_cutoff_rule="every feature source cutoff <= prediction_timestamp",
            identity_policy="causal full-membership rename; ambiguous split/merge excluded",
            graph_policy="source imports/build literals + ancestral 26-week cochange/contributor overlap",
            data_version=digest({"outputs": hashes, "inputs": data["input_hashes"], "contract": config.contract(),
                                 "implementation": manifest["implementation"]}))
        write_json(output / "manifest.json", manifest)
        return manifest
    except BaseException as exc:
        manifest.update(status="FAILED", reason=f"{type(exc).__name__}: {exc}")
        write_json(output / "manifest.json", manifest)
        raise


def verify_dataset(path):
    path = Path(path)
    manifest = read_json(path / "manifest.json")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("status") != "COMPLETE":
        raise ValueError("Incomplete/unsupported forecasting generation")
    contract = manifest.get("prediction_contract", {})
    configuration = ForecastConfig(**{k: contract[k] for k in
        ("horizon", "growth_threshold_minutes", "strategy", "package_extra_depth", "history_weeks")})
    if configuration.contract() != contract:
        raise ValueError("Invalid prediction contract")
    required = {"module_weekly_state.csv", "module_membership.csv", "module_identity.csv", "module_labels.csv",
                "module_graph_features.csv", "module_edges_weekly.csv", "module_sequences.npz", "dataset_audit.json",
                "module_lineage.json", "unresolved_dependencies.json"}
    if set(manifest.get("outputs", {})) != required:
        raise ValueError("Missing/unexpected dataset artifacts")
    for name, expected in manifest["outputs"].items():
        if (path / name).is_symlink() or sha256(path / name) != expected:
            raise ValueError("Dataset artifact checksum mismatch")
    expected = digest({"outputs": manifest["outputs"], "inputs": manifest["input_hashes"],
                       "contract": manifest["prediction_contract"], "implementation": manifest["implementation"]})
    if expected != manifest["data_version"]:
        raise ValueError("Dataset version mismatch")
    if manifest["predictor_allowlist"] != {"M1": list(BASE_FEATURES), "M2": list(BASE_FEATURES + GRAPH_FEATURES)}:
        raise ValueError("Predictor allowlist changed")
    return manifest
