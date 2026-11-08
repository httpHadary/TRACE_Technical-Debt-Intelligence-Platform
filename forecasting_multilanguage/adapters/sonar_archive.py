"""Import explicitly registered native Sonar archives; no live API/scanner calls."""
import json
import hashlib
from ..contracts import Observation, raw_measure, digest, metric_unit
from ..io import artifact_path, file_sha256
from ..registry import language_distribution


def verified_json(root, relative, expected):
    data = artifact_path(root, relative).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Archived payload digest mismatch")
    return json.loads(data)


def read_archive(root, index):
    """Index carries per-payload hashes and separately archived coverage provenance.

    No incomplete/partial coverage is promoted. Caller binds the returned candidates
    to a validated analyzer domain and actual Git lineage using PastStore.
    """
    output = []
    for entry in index:
        payload = verified_json(root, entry["payload"], entry["raw_payload_sha256"])
        coverage = verified_json(root, entry["coverage_payload"], entry["coverage_sha256"])
        inventory_record = verified_json(root, entry["inventory_payload"], entry["inventory_sha256"])
        if inventory_record["commit_sha"] != entry["commit_sha"]:
            raise ValueError("Inventory revision mismatch")
        if (coverage["status"] != "COMPLETE" or coverage["failed_files"] != 0 or coverage["unsupported_files"] != 0
                or type(coverage["expected_source_files"]) is not int or coverage["expected_source_files"] <= 0
                or coverage["analyzed_files"] != coverage["expected_source_files"]
                or coverage["commit_sha"] != entry["commit_sha"]
                or coverage["analysis_id"] != entry["analysis_id"]):
            raise ValueError("Whole-repository coverage not proved")
        if (payload["analysis_id"] != entry["analysis_id"] or payload["revision"] != entry["commit_sha"]
                or payload["component"]["key"] != entry["native_project_key"]):
            raise ValueError("Native payload analysis/revision/project mismatch")
        raw = {}
        for metric in payload["component"]["measures"]:
            if metric["metric"] in raw:
                raise ValueError("Duplicate native metric")
            raw[metric["metric"]] = metric.get("value")
        languages, errors = language_distribution(raw.pop("ncloc_language_distribution", None))
        if errors:
            raise ValueError("Invalid measured language coverage")
        measures = {}
        for key, value in raw.items():
            # Sonar REST serializes metrics as text; invalid tokens stay invalid/null.
            try:
                value = float(value) if isinstance(value, str) else value
            except (TypeError, ValueError):
                pass
            measures[key] = raw_measure(value, metric_unit(key))
        output.append(Observation(**{k: entry[k] for k in (
            "repository_id", "family_id", "commit_sha", "source_tree_sha", "state_utc", "analysis_id",
            "executed_utc", "available_utc", "retrieved_utc", "domain_id", "scope_id", "raw_payload_sha256", "inventory_sha256", "coverage_sha256")},
            **{k: coverage[k] for k in ("expected_source_files", "analyzed_files", "failed_files", "unsupported_files")},
            production_paths=tuple(sorted(inventory_record["production_paths"])),
            measures=measures, languages=languages,
            source_id=digest({"entry": entry, "coverage": coverage})))
    return output
