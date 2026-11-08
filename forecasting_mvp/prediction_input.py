"""Past-only admission boundary. No model loading, prediction or label access."""
from dataclasses import dataclass
from datetime import timedelta
import math

from contracts import digest
from .contracts import TargetContract, utc_iso, utc_timestamp
from .targets import TRACKS

CONTEXT_FIELDS = frozenset(("context_id", "repository_id", "track", "origin_utc",
    "context_start_utc", "context_days", "timestamps", "values", "observation_ids",
    "known_fraction", "missing_count", "distinct_observation_ids", "missing_reasons",
    "profile_hash", "metadata_segment", "max_feature_utc"))


@dataclass(frozen=True)
class PredictionInput:
    context_id: str
    repository_id: str
    track: str
    origin_utc: str
    horizon_days: int
    timestamps: tuple
    values: tuple

    def model_payload(self):
        """Copies contain only past observations and the requested horizon."""
        return {"horizon_days": self.horizon_days,
                "timestamps": list(self.timestamps), "past_values": list(self.values)}


def admit_prediction_input(context, horizon_days, *, expected_origin_utc, measurement_times):
    """Require ONE context, externally bound cutoff, and referenced measurement times.

    measurement_times maps past observation IDs to their imported historical times.
    The returned immutable object exposes no IDs, measurement store, split labels,
    endpoint values or evaluation metadata to a model. A later runner must use this
    boundary; arbitrary Python code is not sandboxed by this contract.
    """
    if not isinstance(context, dict) or set(context) != CONTEXT_FIELDS:
        raise ValueError("Only allowlisted context fields admitted; targets/evaluation labels forbidden")
    TargetContract(horizon_days)
    track = context["track"]
    if track not in TRACKS or horizon_days not in TRACKS[track][1]:
        raise ValueError("Unregistered track/horizon")
    length = TRACKS[track][0]
    origin = utc_timestamp(expected_origin_utc)
    if utc_timestamp(context["origin_utc"]) != origin or utc_timestamp(context["max_feature_utc"]) != origin:
        raise ValueError("Context must match externally bound prediction cutoff")
    if type(context["context_days"]) is not int or context["context_days"] != length:
        raise ValueError("Wrong context length")
    arrays = [context[k] for k in ("timestamps", "values", "observation_ids", "missing_reasons")]
    if any(not isinstance(v, list) or len(v) != length for v in arrays):
        raise ValueError("Aligned context arrays required")
    start = origin - timedelta(days=length - 1)
    if utc_timestamp(context["context_start_utc"]) != start:
        raise ValueError("Context start mismatch")
    known, refs = 0, set()
    for i, (stamp, value, ref, reason) in enumerate(zip(*arrays)):
        timestamp = utc_timestamp(stamp)
        if timestamp != start + timedelta(days=i) or timestamp > origin:
            raise ValueError("Past-only exact daily context required; future measurement forbidden")
        if value is None:
            if ref is not None or reason not in ("UNMEASURED_SELECTED_REVISION", "MISSING_SQALE"):
                raise ValueError("Missing observations require null references and an explicit reason")
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("Finite nonnegative observed stock required")
            if not ref or reason is not None or ref not in measurement_times:
                raise ValueError("Past measurement provenance required")
            if utc_timestamp(measurement_times[ref]) > timestamp:
                raise ValueError("Future measurement reference forbidden")
            known += 1
            refs.add(ref)
    if context["values"][-1] is None or known < (math.ceil(.8 * length) if track == "masked90" else length):
        raise ValueError("Insufficient admitted past observations")
    if (context["missing_count"] != length - known or context["known_fraction"] != known / length
            or context["distinct_observation_ids"] != len(refs)):
        raise ValueError("Context summary mismatch")
    content = {k: v for k, v in context.items() if k not in ("context_id", "repository_id", "track")}
    if context["context_id"] != digest([context["repository_id"], track, content]):
        raise ValueError("Context identity mismatch")
    return PredictionInput(context["context_id"], context["repository_id"], track,
                           utc_iso(origin), horizon_days, tuple(context["timestamps"]), tuple(context["values"]))
