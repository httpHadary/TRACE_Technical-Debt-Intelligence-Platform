"""Frozen F0/F1 feature computation and the explicit past-only model boundary."""
from datetime import timedelta
import math
import statistics
from .contracts import digest, utc, iso, MODES
from .registry import language_family
from .admission import UnmeasuredOrigin

F0 = ("debt_minutes_t0", "debt_observation_age_days", "distinct_debt_states_90d",
      "distinct_debt_analyses_90d", "debt_change_30d", "debt_ols_slope_90d", "debt_std_90d")
SNAPSHOT = {"ncloc_t0": "ncloc", "files_t0": "files", "complexity_t0": "complexity",
            "cognitive_complexity_t0": "cognitive_complexity", "code_smells_t0": "code_smells",
            "bugs_t0": "bugs", "vulnerabilities_t0": "vulnerabilities",
            "duplicated_lines_density_t0": "duplicated_lines_density"}
F1 = tuple(SNAPSHOT) + ("commits_30d", "commits_90d", "active_commit_days_30d",
                       "changed_source_paths_30d", "days_since_last_commit_in_90d",
                       "no_commit_in_complete_90d", "scope_language_family")
FEATURES = F0 + F1
FEATURE_CONTRACT = digest({"version": 2, "F0": F0, "F1": F1, "window": "(t0-L,t0]",
                           "trend": "distinct_state_analysis_utc_elapsed_days_min3", "F2": "DISABLED"})


def build_features(store, cutoff):
    origin = utc(cutoff)
    cutoff = iso(origin)
    start90, start30 = iso(origin - timedelta(days=90)), iso(origin - timedelta(days=30))
    current = store.at(cutoff)
    if current is None or current.measures["sqale_index"].value is None:
        raise UnmeasuredOrigin("An admitted measured origin state is required")
    past = store.history(start90, cutoff)
    debt_history = [o for o in past if o.measures["sqale_index"].value is not None]
    output = {}

    def put(name, value, reason=None, observations=(), events=(), complete=None):
        times = [o.state_utc for o in observations] + [e["state_utc"] for e in events]
        availability = [o.available_utc for o in observations] + [e["available_utc"] for e in events]
        if any(utc(t) > origin for t in times):
            raise ValueError("Future feature source rejected")
        output[name] = {"value": value, "status": "OBSERVED" if value is not None else "MISSING",
                        "reason": None if value is not None else reason,
                        "source_refs": sorted([o.observation_id for o in observations] + [e["event_id"] for e in events]),
                        "max_source_state_utc": max(times, key=utc) if times else None,
                        "max_available_utc": max(availability, key=utc) if availability and all(availability) else None,
                        "window_complete": complete}

    put("debt_minutes_t0", current.measures["sqale_index"].value, observations=[current])
    put("debt_observation_age_days", (origin - utc(current.state_utc)).total_seconds() / 86400, observations=[current])
    put("distinct_debt_states_90d", len({o.commit_sha for o in debt_history}), observations=debt_history)
    put("distinct_debt_analyses_90d", len({o.analysis_id for o in debt_history}), observations=debt_history)
    lag = store.at(start30)
    lag_value = lag.measures["sqale_index"].value if lag else None
    put("debt_change_30d", current.measures["sqale_index"].value - lag_value if lag_value is not None else None,
        "EXACT_PAST_STATE_UNMEASURED", observations=[current, lag] if lag_value is not None else [current])
    diverse = len({o.commit_sha for o in debt_history}) >= 3 and len({o.state_utc for o in debt_history}) >= 3
    x = [(utc(o.state_utc) - origin).total_seconds() / 86400 for o in debt_history]
    y = [o.measures["sqale_index"].value for o in debt_history]
    slope = statistics.linear_regression(x, y).slope if diverse else None
    put("debt_ols_slope_90d", slope, "INSUFFICIENT_DISTINCT_STATES", observations=debt_history)
    put("debt_std_90d", statistics.pstdev(y) if diverse else None,
        "INSUFFICIENT_DISTINCT_STATES", observations=debt_history)
    for name, key in SNAPSHOT.items():
        metric = current.measures.get(key)
        put(name, metric.value if metric else None, metric.reason if metric else "SOURCE_MISSING", observations=[current])
    put("scope_language_family", language_family(current.languages), observations=[current])
    # Git objects do not prove historical online availability. Retrospective mode
    # permits source-state reconstruction, but never an online-availability claim.
    if store.mode == "OPERATIONAL_ASOF":
        for name in F1:
            if name not in output:
                put(name, None, "GIT_AVAILABILITY_UNVERIFIED", complete=False)
    else:
        events90 = store.lineage.events(start90, cutoff)
        events30 = [e for e in events90 if utc(e["state_utc"]) > utc(start30)]
        put("commits_30d", len(events30), events=events30, complete=True)
        put("commits_90d", len(events90), events=events90, complete=True)
        put("active_commit_days_30d", len({utc(e["state_utc"]).date() for e in events30}), events=events30, complete=True)
        put("changed_source_paths_30d", len({p for e in events30 for p in e["paths"]}), events=events30, complete=True)
        put("days_since_last_commit_in_90d", (origin - max(utc(e["state_utc"]) for e in events90)).total_seconds() / 86400 if events90 else None,
            "CENSORED_NO_EVENT_IN_90D", events=events90, complete=True)
        put("no_commit_in_complete_90d", int(not events90), events=events90, complete=True)
    record = {"schema_version": 2, "feature_contract_id": FEATURE_CONTRACT,
              "repository_id": store.registration["repository_id"], "family_id": store.registration["family_id"],
              "origin_utc": cutoff, "origin_observation_id": current.observation_id,
              "domain_id": current.domain_id, "scope_id": current.scope_id,
              "study_mode": store.mode, "state_proof_id": store.proof_id(cutoff), "features": output}
    return dict(record, context_id=digest(record))


def prediction_input(record, *, expected_cutoff):
    """No labels, evaluation metadata, source-store handles or open-ended columns.

    This boundary validates data contracts; it is not a sandbox for arbitrary code.
    Routing IDs/horizons belong outside the returned numerical/categorical X.
    """
    fields = {"schema_version", "feature_contract_id", "repository_id", "family_id", "origin_utc",
              "origin_observation_id", "domain_id", "scope_id", "study_mode", "state_proof_id", "features", "context_id"}
    if set(record) != fields or set(record["features"]) != set(FEATURES):
        raise ValueError("Only frozen feature fields admitted; target/evaluation fields forbidden")
    if record["feature_contract_id"] != FEATURE_CONTRACT or record["schema_version"] != 2 or record["study_mode"] not in MODES:
        raise ValueError("Unregistered feature contract/mode")
    if digest({k: v for k, v in record.items() if k != "context_id"}) != record["context_id"]:
        raise ValueError("Feature identity mismatch")
    cutoff = utc(expected_cutoff)
    if utc(record["origin_utc"]) != cutoff:
        raise ValueError("Externally bound prediction cutoff required")
    result = {}
    for name in FEATURES:
        item = record["features"][name]
        if set(item) != {"value", "status", "reason", "source_refs", "max_source_state_utc", "max_available_utc", "window_complete"}:
            raise ValueError("Unexpected feature evidence/label field")
        if item["max_source_state_utc"] is not None and utc(item["max_source_state_utc"]) > cutoff:
            raise ValueError("Future source evidence forbidden")
        value = item["value"]
        if value is None:
            if item["status"] != "MISSING" or not item["reason"]:
                raise ValueError("Missing feature must retain status/reason")
        else:
            if item["status"] != "OBSERVED" or item["reason"] is not None:
                raise ValueError("Observed feature status mismatch")
            if record["study_mode"] == "OPERATIONAL_ASOF" and (item["max_available_utc"] is None or utc(item["max_available_utc"]) > cutoff):
                raise ValueError("Future/unknown online availability forbidden")
            if name == "scope_language_family":
                if value not in {"java_dominant", "python_dominant", "jsts_dominant", "cpp_dominant", "cs_dominant", "go_dominant", "mixed_python_jsts", "mixed_other", "unknown", "other"}:
                    raise ValueError("Unknown language category")
            elif type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("Finite feature value required")
        result[name] = value
        result[name + "__missing"] = int(value is None)
    return result
