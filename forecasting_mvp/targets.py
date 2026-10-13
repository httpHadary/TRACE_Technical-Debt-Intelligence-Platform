"""Exact calendar state construction, with missingness and past-only contexts."""
from bisect import bisect_right
from datetime import timedelta
import json
import math

from contracts import digest, number

from .contracts import utc_iso, utc_timestamp, TargetContract

DAY = timedelta(days=1)
TRACKS = {"core90": (90, (30, 60, 90)), "masked90": (90, (30, 60, 90)),
          "ttm60": (180, (60,)), "ttm90": (512, (90,))}


class RepositoryStates:
    """Archive-only monotonic first-parent chain; no nearest measurement lookup."""
    def __init__(self, git_rows, observations):
        self.chain = sorted(git_rows, key=lambda r: int(r["first_parent_index"]))
        if not self.chain or [int(r["first_parent_index"]) for r in self.chain] != list(range(len(self.chain))):
            raise ValueError("Contiguous first-parent ancestry required")
        self.times = [utc_timestamp(r["committer_timestamp"]) for r in self.chain]
        if any(b < a for a, b in zip(self.times, self.times[1:])):
            raise ValueError("Nonmonotonic first-parent time")
        for a, b in zip(self.chain, self.chain[1:]):
            parents = json.loads(b["parents_json"])
            if not parents or parents[0] != a["commit_sha"]:
                raise ValueError("Broken first-parent ancestry")
        self.observed = {}
        self._state_cache = {}
        for row in observations:
            if row["commit_sha"] in self.observed:
                raise ValueError("Ambiguous measured revision")
            self.observed[row["commit_sha"]] = row
        # Known profile changes/missing metadata are barriers even if no daily cutoff lands on them.
        self.segments = []
        segment = 0
        prior_profile = None
        for commit in self.chain:
            row = self.observed.get(commit["commit_sha"])
            if row is not None:
                profile = row["profile_hash"] if row["profile_status"] == "KNOWN_METADATA_ONLY" else None
                if profile != prior_profile or profile is None:
                    segment += 1
                prior_profile = profile
            self.segments.append((segment, prior_profile))

    def state(self, cutoff):
        cutoff = utc_timestamp(cutoff)
        if cutoff in self._state_cache:
            return self._state_cache[cutoff]
        if cutoff < self.times[0] or cutoff > self.times[-1]:
            return None, "OUTSIDE_ARCHIVED_HISTORY"
        i = bisect_right(self.times, cutoff) - 1
        commit = self.chain[i]
        row = self.observed.get(commit["commit_sha"])
        if row is None:
            return {"index": i, "commit_sha": commit["commit_sha"]}, "UNMEASURED_SELECTED_REVISION"
        if row["provenance_status"] != "AUDITED_IMPORTED" or row["metric"] != "SQALE_INDEX" or row["scope_id"] != "native_project":
            return None, "INCOMPATIBLE_OBSERVATION_CONTRACT"
        value = number(row["sqale_index_minutes"])
        if value is None:
            return None, "MISSING_SQALE"
        if row["profile_status"] != "KNOWN_METADATA_ONLY" or not row["profile_hash"]:
            return None, "UNKNOWN_PROFILE_METADATA"
        if utc_timestamp(row["committer_timestamp"]) != self.times[i] or utc_timestamp(row["historical_timestamp"]) != self.times[i]:
            raise ValueError("Observation/commit time mismatch")
        result = {"index": i, "commit_sha": commit["commit_sha"], "observation_id": row["observation_id"],
                "value": value, "profile_hash": row["profile_hash"], "segment": self.segments[i][0],
                "committer_timestamp": row["committer_timestamp"]}, None
        self._state_cache[cutoff] = result
        return result

    def context(self, origin, length, masked=False):
        origin = utc_timestamp(origin)
        origin_state, reason = self.state(origin)
        if reason:
            return None, "ORIGIN_" + reason
        start = origin - (length - 1) * DAY
        if start < self.times[0]:
            return None, "INSUFFICIENT_CONTEXT_SPAN"
        values, references, stamps = [], [], []
        reasons = []
        indices = []
        for d in range(length):
            stamp = start + d * DAY
            state, missing = self.state(stamp)
            if state is not None and "segment" in state and state["segment"] != origin_state["segment"]:
                return None, "CONTEXT_PROFILE_SEGMENT_CROSSING"
            if missing not in (None, "UNMEASURED_SELECTED_REVISION", "MISSING_SQALE"):
                return None, "CONTEXT_" + missing
            if state and "index" in state:
                indices.append(state["index"])
            stamps.append(utc_iso(stamp))
            values.append(state["value"] if missing is None else None)
            references.append(state["observation_id"] if missing is None else None)
            reasons.append(missing)
        # Detect known profile barriers between grid selections, including sub-day transitions.
        first_index = bisect_right(self.times, start) - 1
        if any(s[0] != origin_state["segment"] for s in self.segments[first_index:origin_state["index"] + 1]):
            return None, "CONTEXT_PROFILE_SEGMENT_CROSSING"
        known = sum(v is not None for v in values)
        if known < length and not masked:
            return None, "MISSING_CONTEXT_STATE"
        if masked and known < math.ceil(0.8 * length):
            return None, "MASKED_CONTEXT_BELOW_80_PERCENT"
        record = {"origin_utc": utc_iso(origin), "context_start_utc": utc_iso(start), "context_days": length,
                  "timestamps": stamps, "values": values, "observation_ids": references,
                  "known_fraction": known / length, "missing_count": length - known,
                  "distinct_observation_ids": len(set(r for r in references if r)),
                  "missing_reasons": reasons, "profile_hash": origin_state["profile_hash"],
                  "metadata_segment": origin_state["segment"], "max_feature_utc": stamps[-1]}
        return record, None

    def endpoint(self, origin, horizon):
        target = TargetContract(horizon)
        first, reason = self.state(origin)
        if reason:
            return None, "ORIGIN_" + reason
        last, reason = self.state(target.endpoint(origin))
        if reason:
            return None, "ENDPOINT_" + reason
        if any(s[0] != first["segment"] for s in self.segments[first["index"]:last["index"] + 1]):
            return None, "TARGET_PROFILE_SEGMENT_CROSSING"
        # Identical SHA means identical archived branch state, not a carried older measurement.
        return {"endpoint_utc": target.endpoint(origin), "endpoint_revision": last["commit_sha"],
                "endpoint_observation_id": last["observation_id"], "actual_minutes": last["value"],
                "actual_delta_minutes": last["value"] - first["value"],
                "endpoint_state_kind": "UNCHANGED_VERIFIED_STATE" if first["commit_sha"] == last["commit_sha"] else "MEASURED_CHANGED_STATE"}, None


def next_monday(value):
    dt = utc_timestamp(value)
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if midnight < dt:
        midnight += DAY
    return midnight + timedelta(days=(-midnight.weekday()) % 7)


def context_features(context):
    values = context["values"]
    features = {"current_minutes": values[-1], "known_fraction": context["known_fraction"],
                "distinct_observation_ids": context["distinct_observation_ids"], "max_feature_utc": context["max_feature_utc"]}
    for lag in (7, 30, 60):
        features[f"lag{lag}"] = values[-1 - lag]
    for window in (30, 90):
        known = [(i, v) for i, v in enumerate(values[-window:]) if v is not None]
        if len(known) < math.ceil(0.8 * window):
            mean = slope = std = None
        else:
            mean = sum(v for _, v in known) / len(known)
            avg_x = sum(i for i, _ in known) / len(known)
            denominator = sum((i - avg_x) ** 2 for i, _ in known)
            slope = sum((i - avg_x) * (v - mean) for i, v in known) / denominator if denominator else 0.0
            std = (sum((v - mean) ** 2 for _, v in known) / len(known)) ** 0.5
        features.update({f"mean{window}": mean, f"slope{window}": slope, f"std{window}": std})
    return features
