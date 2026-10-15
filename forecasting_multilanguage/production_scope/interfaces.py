"""Scope-bound identities around unchanged F0/F1 and exact-duration algorithms.

The validation projections below reuse pure frozen algorithms; they never enter
legacy admission/publication. New public records always carry new contract IDs.
"""
from ..contracts import digest, horizon_endpoint
from .. import features as algorithm
from .. import targets as endpoints
from .registry import contract_ids, validate_registration


def build_features(store, cutoff):
    validate_registration(store.registration)
    record = algorithm.build_features(store, cutoff)
    record["feature_contract_id"] = store.registration["feature_contract_id"]
    record["context_id"] = digest({k: v for k, v in record.items() if k != "context_id"})
    return record


def prediction_input(record, *, expected_cutoff):
    ids = contract_ids(record["repository_id"])
    if (record["scope_id"] != ids["scope_policy_hash"]
            or record["feature_contract_id"] != ids["feature_contract_id"]
            or digest({k: v for k, v in record.items() if k != "context_id"}) != record["context_id"]):
        raise ValueError("Versioned prediction identity mismatch")
    view = dict(record, feature_contract_id=algorithm.FEATURE_CONTRACT)
    view["context_id"] = digest({k: v for k, v in view.items() if k != "context_id"})
    return algorithm.prediction_input(view, expected_cutoff=expected_cutoff)


def origin_identity(store, cutoff, horizon):
    # Exact horizon validation precedes any source lookup.
    horizon_endpoint(cutoff, horizon)
    record = endpoints.origin_identity(store, cutoff, horizon)
    record.update(feature_contract_id=store.registration["feature_contract_id"],
                  target_contract_id=store.registration["target_contract_id"],
                  context_id=build_features(store, cutoff)["context_id"])
    record["forecast_id"] = digest({k: v for k, v in record.items() if k != "forecast_id"})
    return record


def target_status(origin, endpoint_store):
    ids = contract_ids(origin["repository_id"])
    if (origin["scope_id"] != ids["scope_policy_hash"]
            or origin["feature_contract_id"] != ids["feature_contract_id"]
            or origin["target_contract_id"] != ids["target_contract_id"]
            or digest({k: v for k, v in origin.items() if k != "forecast_id"}) != origin["forecast_id"]):
        raise ValueError("Versioned target identity mismatch")
    view = dict(origin, feature_contract_id=algorithm.FEATURE_CONTRACT, target_contract_id=endpoints.TARGET_CONTRACT)
    view["forecast_id"] = digest({k: v for k, v in view.items() if k != "forecast_id"})
    return dict(endpoints.target_status(view, endpoint_store), forecast_id=origin["forecast_id"])
