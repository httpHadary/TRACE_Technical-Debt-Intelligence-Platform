"""Independent exact-duration endpoint status construction; no predictions."""
from .contracts import digest, horizon_endpoint, iso, utc
from .features import FEATURE_CONTRACT, build_features
from .admission import UnmeasuredOrigin
from .git_events import OutsideRefEvidence

TARGET_CONTRACT = digest({"schema_version": 2, "metric": "sqale_index", "mode": "STANDARD",
                          "unit": "estimated_remediation_minutes", "horizons_days": [30, 60, 90],
                          "endpoint": "independent_exact_active_state_same_domain_scope"})
ORIGIN_FIELDS = ("schema_version", "repository_id", "family_id", "origin_utc", "origin_observation_id",
                 "domain_id", "scope_id", "horizon_days", "endpoint_utc", "context_id", "feature_contract_id", "target_contract_id", "forecast_id")
LABEL_FIELDS = ("forecast_id", "endpoint_utc", "actual_minutes", "actual_delta_minutes", "endpoint_state_sha",
                "endpoint_observation_id", "endpoint_state_proof_id", "label_status", "missing_reason")


def origin_identity(store, cutoff, horizon):
    cutoff = iso(utc(cutoff))
    endpoint = horizon_endpoint(cutoff, horizon)
    observation = store.at(cutoff)
    if observation is None:
        raise UnmeasuredOrigin("Measured origin required")
    record = {"schema_version": 2, "repository_id": store.registration["repository_id"],
              "family_id": store.registration["family_id"], "origin_utc": cutoff,
              "origin_observation_id": observation.observation_id, "domain_id": observation.domain_id,
              "scope_id": observation.scope_id, "horizon_days": horizon, "endpoint_utc": endpoint,
              "context_id": build_features(store, cutoff)["context_id"],
              "feature_contract_id": FEATURE_CONTRACT, "target_contract_id": TARGET_CONTRACT}
    return dict(record, forecast_id=digest(record))


def target_status(origin, endpoint_store):
    required = {"schema_version", "repository_id", "family_id", "origin_utc", "origin_observation_id",
                "domain_id", "scope_id", "horizon_days", "endpoint_utc", "context_id", "feature_contract_id", "target_contract_id", "forecast_id"}
    if (set(origin) != required or digest({k: v for k, v in origin.items() if k != "forecast_id"}) != origin["forecast_id"]
            or origin["endpoint_utc"] != horizon_endpoint(origin["origin_utc"], origin["horizon_days"])
            or origin["schema_version"] != 2 or origin["target_contract_id"] != TARGET_CONTRACT
            or origin["feature_contract_id"] != FEATURE_CONTRACT):
        raise ValueError("Origin/target identity mismatch")
    if origin["repository_id"] != endpoint_store.registration["repository_id"] or origin["family_id"] != endpoint_store.registration["family_id"]:
        raise ValueError("Endpoint repository/family identity mismatch")
    label = {"forecast_id": origin["forecast_id"], "endpoint_utc": origin["endpoint_utc"],
             "actual_minutes": None, "actual_delta_minutes": None, "endpoint_state_sha": None,
             "endpoint_observation_id": None, "endpoint_state_proof_id": None,
             "label_status": "UNKNOWN", "missing_reason": None}
    if origin["domain_id"] != endpoint_store.domain["domain_id"] or origin["scope_id"] != endpoint_store.registration["scope_policy_hash"]:
        return dict(label, label_status="DOMAIN_INCOMPATIBLE", missing_reason="DOMAIN_OR_SCOPE_CHANGED")
    previous = endpoint_store.at(origin["origin_utc"])
    if previous is None or previous.observation_id != origin["origin_observation_id"]:
        raise ValueError("Origin measurement identity changed")
    try:
        endpoint = endpoint_store.at(origin["endpoint_utc"])
        label["endpoint_state_proof_id"] = endpoint_store.proof_id(origin["endpoint_utc"])
    except OutsideRefEvidence:
        return dict(label, missing_reason="ENDPOINT_REF_EVIDENCE_UNAVAILABLE")
    if endpoint is None or endpoint.measures["sqale_index"].value is None:
        return dict(label, missing_reason="EXACT_ENDPOINT_STATE_UNMEASURED")
    current = previous.measures["sqale_index"].value
    if current is None:
        return dict(label, missing_reason="ORIGIN_DEBT_UNMEASURED")
    actual = endpoint.measures["sqale_index"].value
    return dict(label, actual_minutes=actual, actual_delta_minutes=actual - current,
                endpoint_state_sha=endpoint.commit_sha, endpoint_observation_id=endpoint.observation_id,
                label_status="OBSERVED", missing_reason=None)
