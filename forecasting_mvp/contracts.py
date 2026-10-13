"""Small repository contracts, separate from legacy module forecasting schemas."""
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import math

from contracts import digest, number, safe_id

from . import MVP_SCHEMA_VERSION


def utc_timestamp(value):
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("Timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def utc_iso(value):
    return utc_timestamp(value).isoformat().replace("+00:00", "Z")


def finite_delta(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Delta must be finite or null")
    return float(value)


@dataclass(frozen=True)
class TargetContract:
    horizon_days: int
    metric: str = "SQALE_INDEX"
    unit: str = "estimated_remediation_minutes"
    scope_id: str = "native_project"
    domain_policy: str = "same_known_metadata_segment"
    context_policy: str = "daily90_complete_first"
    endpoint_policy: str = "exact_measured_first_parent_state_at_utc_cutoff"
    cadence_seconds: int = 86400
    population: str = "whole_repository_stock"

    def __post_init__(self):
        if type(self.horizon_days) is not int or self.horizon_days not in (30, 60, 90):
            raise ValueError("MVP horizons are exact 30/60/90 days; 91 is a separate target")
        if self.metric != "SQALE_INDEX" or self.unit != "estimated_remediation_minutes":
            raise ValueError("Maintainability estimate required, not combined effort or actual labor")
        if type(self.cadence_seconds) is not int or self.cadence_seconds != 86400:
            raise ValueError("Daily UTC cadence required")
        for name in ("scope_id", "domain_policy", "context_policy", "endpoint_policy", "population"):
            safe_id(getattr(self, name))
        if self.scope_id != "native_project" or self.population != "whole_repository_stock":
            raise ValueError("Phase 0 config supports the native repository stock target")

    @property
    def duration_seconds(self):
        return self.horizon_days * 86400

    def endpoint(self, origin):
        return utc_iso(utc_timestamp(origin) + timedelta(seconds=self.duration_seconds))

    def record(self):
        return {"mvp_schema_version": MVP_SCHEMA_VERSION, **asdict(self),
                "duration_seconds": self.duration_seconds}

    @property
    def target_id(self):
        return digest(self.record())


@dataclass(frozen=True)
class Observation:
    repository_id: str
    revision: str
    analysis_id: str
    domain_id: str
    historical_time: str
    source_hash: str
    value_minutes: float | None
    scope_id: str = "native_project"
    provenance_status: str = "IMPORTED_UNAUDITED"
    metric: str = "SQALE_INDEX"
    execution_time: str | None = None

    def __post_init__(self):
        for name in ("repository_id", "analysis_id", "domain_id", "scope_id"):
            safe_id(getattr(self, name))
        if len(self.revision) not in (40, 64) or any(c not in "0123456789abcdef" for c in self.revision):
            raise ValueError("Full immutable Git revision required")
        if len(self.source_hash) != 64 or any(c not in "0123456789abcdef" for c in self.source_hash):
            raise ValueError("Source SHA-256 required")
        if self.metric != "SQALE_INDEX":
            raise ValueError("SQALE estimate required")
        if self.provenance_status not in ("IMPORTED_UNAUDITED", "AUDITED_IMPORTED", "VERIFIED_SCAN"):
            raise ValueError("Unknown provenance")
        object.__setattr__(self, "value_minutes", number(self.value_minutes))
        object.__setattr__(self, "historical_time", utc_iso(self.historical_time))
        if self.execution_time is not None:
            object.__setattr__(self, "execution_time", utc_iso(self.execution_time))
        if self.provenance_status == "VERIFIED_SCAN":
            raise ValueError("Own-scan proof admission is deferred; Phase 0 cannot certify scans")

    def record(self):
        return {"mvp_schema_version": MVP_SCHEMA_VERSION, **asdict(self)}

    @property
    def observation_id(self):
        return digest(self.record())
