"""Hash-verified archive extension: exact files, native identities and content review."""
from ..adapters.sonar_archive import verified_json, read_archive as native_archive
from ..contracts import digest, hash_id
from .scope import VERSION


def verify_coverage(lineage, obs, proof):
    if set(proof) != {"coverage", "inventory", "review"}:
        raise ValueError("Exact verified coverage/inventory/review proof required")
    coverage, archived, review = (proof[k] for k in ("coverage", "inventory", "review"))
    # Proof must be the identical parsed artifacts bound into the Observation.
    # Raw-byte hashes are checked by read_archive; also bind canonical representations
    # to source_id below, so changing a parsed proof cannot bypass those hashes.
    if obs.source_id != digest({"version": VERSION, "native_source_id": coverage.get("native_source_id"),
                               "proof": proof}):
        raise ValueError("Coverage proof identity mismatch")
    actual = lineage.inventory(obs.commit_sha)
    if archived != actual or actual["blockers"]:
        raise ValueError("Archive differs from exact Git tree inventory")
    identities = {"version": VERSION, "repository_id": obs.repository_id, "scope_id": obs.scope_id,
                  "commit_sha": obs.commit_sha, "source_tree_sha": obs.source_tree_sha,
                  "analysis_id": obs.analysis_id, "inventory_id": actual["inventory_id"]}
    if any(coverage.get(k) != v for k, v in identities.items()):
        raise ValueError("Native coverage revision/tree/analysis/scope mismatch")
    if (coverage.get("status") != "COMPLETE" or coverage.get("failed_files") != 0
            or coverage.get("unsupported_files") != 0
            or coverage.get("expected_source_files") != len(actual["production_paths"])
            or coverage.get("analyzed_files") != len(actual["production_paths"])):
        raise ValueError("Partial coverage forbidden")
    expected = [{"path": r["path"], "language": r["language"]} for r in actual["entries"] if r["role"] == "PRODUCTION"]
    files = coverage.get("analyzed_source_files", [])
    if (any(set(r) != {"path", "language"} for r in files)
            or sorted(files, key=lambda r: r["path"]) != expected
            or tuple(obs.production_paths) != tuple(actual["production_paths"])):
        raise ValueError("Exact native production-file/language equality required")
    if (review.get("version") != VERSION or review.get("inventory_id") != actual["inventory_id"]
            or review.get("status") != "REVIEWED_NO_UNRESOLVED_GENERATED_VENDOR_OR_NONCODE"
            or not isinstance(review.get("reviewer"), str) or not review["reviewer"]
            or review.get("reviewed_paths") != [r["path"] for r in actual["entries"] if r["role"] != "OUTSIDE_ROOT"]):
        raise ValueError("Bound full-root content/exclusion review required")
    for key in ("raw_file_components_sha256", "scanner_completion_sha256", "ce_success_sha256"):
        hash_id(coverage.get(key))


def read_archive(root, index, lineage):
    """Import only existing archives. Additional raw evidence stays hash-addressed.

    Completion/file exports are verified bytes, not an assertion inferred from
    aggregate file counts. No new observations are collected by this function.
    """
    from dataclasses import replace
    output, proofs = [], {}
    for entry in index:
        obs = native_archive(root, [entry])[0]
        inventory = verified_json(root, entry["inventory_payload"], entry["inventory_sha256"])
        coverage = verified_json(root, entry["coverage_payload"], entry["coverage_sha256"])
        review = verified_json(root, entry["review_payload"], entry["review_sha256"])
        if coverage.get("native_project_key") != entry["native_project_key"]:
            raise ValueError("Coverage native project mismatch")
        components = verified_json(root, entry["file_components_payload"], coverage["raw_file_components_sha256"])
        scanner = verified_json(root, entry["scanner_completion_payload"], coverage["scanner_completion_sha256"])
        ce = verified_json(root, entry["ce_success_payload"], coverage["ce_success_sha256"])
        # Export envelope is assembled from fully paginated native responses. Retain
        # raw response page hashes alongside it; equality and completion are mandatory.
        if (components.get("analysis_id") != obs.analysis_id or components.get("revision") != obs.commit_sha
                or components.get("project_key") != entry["native_project_key"]
                or components.get("pagination_complete") is not True
                or components.get("files") != coverage.get("analyzed_source_files")
                or scanner.get("exit_code") != 0 or scanner.get("sensors_complete") is not True
                or scanner.get("analysis_id") != obs.analysis_id
                or scanner.get("revision") != obs.commit_sha
                or scanner.get("project_key") != entry["native_project_key"]
                or not scanner.get("ce_task_id")
                or scanner.get("ce_task_id") != ce.get("task", {}).get("id")
                or ce.get("task", {}).get("status") != "SUCCESS"
                or ce["task"].get("analysisId") != obs.analysis_id
                or ce["task"].get("componentKey") != entry["native_project_key"]):
            raise ValueError("Native completion/file evidence mismatch")
        proof = dict(coverage=dict(coverage, native_source_id=obs.source_id), inventory=inventory, review=review)
        obs = replace(obs, source_id=digest({"version": VERSION, "native_source_id": obs.source_id, "proof": proof}))
        verify_coverage(lineage, obs, proof)
        output.append(obs)
        proofs[obs.observation_id] = proof
    return output, proofs
