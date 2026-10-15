"""New-study registry dispatch; never changes the legacy scope validator."""
from ..contracts import digest
from ..registry import SCOPE_ID, validate_registration as legacy_shape
from ..features import FEATURE_CONTRACT
from ..targets import TARGET_CONTRACT
from .scope import VERSION, policy, scope_id


def contract_ids(repository_id):
    scope = scope_id(repository_id)
    return dict(scope_policy_hash=scope,
                feature_contract_id=digest([VERSION, scope, FEATURE_CONTRACT, "scoped-git-events-v1"]),
                target_contract_id=digest([VERSION, scope, TARGET_CONTRACT, "exact-full-production-state-v1"]))


def validate_registration(record):
    extension = {"contract_version", "feature_contract_id", "target_contract_id"}
    if not extension <= set(record) or record["contract_version"] != VERSION:
        raise ValueError("Explicit new-study contract version required")
    pol = policy(record["repository_id"])
    ids = contract_ids(record["repository_id"])
    if any(record[k] != v for k, v in ids.items()):
        raise ValueError("Scope/feature/target contract mismatch")
    if (record["provider_repository_id"] != pol["provider_repository_id"]
            or record["family_id"] != "github:" + pol["provider_repository_id"]
            or record["canonical_url"] != "https://github.com/" + pol["repository_id"]
            or set(record["declared_languages"]) != set(pol["languages"])
            or record["reserved_role"] not in ("development", "quarantine")):
        raise ValueError("Pinned development family/language identity required")
    # Reuse common schema-v2 shape/rights/time checks on an explicit validation-only
    # projection. It is NOT an admitted legacy registration, and is never published.
    common = {k: v for k, v in record.items() if k not in extension}
    common["scope_policy_hash"] = SCOPE_ID
    legacy_shape(common)
    return digest(record)
