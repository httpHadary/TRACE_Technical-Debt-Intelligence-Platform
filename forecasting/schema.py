"""Prediction, availability and feature contracts shared by every model."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
import re

from contracts import digest

CURRENT_FEATURES = (
    "sqale_minutes", "combined_effort_minutes", "ncloc", "complexity",
    "cognitive_complexity", "finding_count", "file_count", "history_points",
    "history_fraction", "membership_changed", "commits_26w", "churn_26w", "authors_26w",
)
ROLLING_FEATURES = tuple(f"{name}_{stat}_26w" for name in
                         ("sqale_minutes", "ncloc", "complexity", "finding_count")
                         for stat in ("mean", "slope", "observed"))
BASE_FEATURES = CURRENT_FEATURES + ROLLING_FEATURES
GRAPH_FEATURES = (
    "dependency_in_degree", "dependency_out_degree", "dependency_coupling",
    "dependency_cycle", "dependency_pagerank", "cochange_degree", "cochange_weight",
    "contributor_degree", "contributor_weight", "source_coverage", "unresolved_imports",
    "unresolved_build_dependencies", "dependency_available", "history_graph_available",
    "build_coverage",
)
SEQUENCE_FEATURES = ("sqale_minutes", "combined_effort_minutes", "ncloc", "complexity",
                     "cognitive_complexity", "finding_count", "file_count") + GRAPH_FEATURES
COMPATIBILITY_FIELDS = ("sonarqube_version", "java_analyzer_version", "quality_profile_hash",
                        "compatible_rule_domain_version", "scanner_image", "analysis_mode")


def timestamp(value):
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timezone-aware cutoff required")
    return dt.astimezone(timezone.utc)


def iso(value):
    return timestamp(value).isoformat() if not isinstance(value, datetime) else value.astimezone(timezone.utc).isoformat()


def finite(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("Boolean numeric observation")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Nonfinite observation")
    return value


@dataclass(frozen=True)
class ForecastConfig:
    horizon: str = "approx91"
    growth_threshold_minutes: float = 30.0
    strategy: str = "auto"
    package_extra_depth: int = 1
    history_weeks: int = 26

    def __post_init__(self):
        if self.horizon not in ("exact90", "approx91"):
            raise ValueError("Choose exact90 or explicit approx91; 84 days is not supported")
        if self.strategy not in ("auto", "build", "package"):
            raise ValueError("Invalid module strategy")
        if self.package_extra_depth < 0 or self.history_weeks != 26:
            raise ValueError("Invalid history/package depth")
        if finite(self.growth_threshold_minutes) is None or self.growth_threshold_minutes < 0:
            raise ValueError("Invalid predefined growth threshold")

    @property
    def days(self):
        return 90 if self.horizon == "exact90" else 91

    def contract(self):
        return {**asdict(self), "horizon_days": self.days, "growth_rule": "delta > threshold",
                "target": "future_sqale_minutes - current_sqale_minutes"}


@dataclass
class Snapshot:
    repository_id: str
    cutoff: str
    commit: str
    files: dict
    metadata: dict
    label: str = ""
    weekly: bool = True
    scope: tuple = ()

    def __post_init__(self):
        self.cutoff = iso(self.cutoff)
        if not self.repository_id or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", self.commit):
            raise ValueError("Missing snapshot identity")
        for values in self.files.values():
            for name, value in values.items():
                observed = finite(value)
                if observed is not None and observed < 0:
                    raise ValueError(f"Negative source measurement: {name}")
        if any(not self.metadata.get(k) for k in COMPATIBILITY_FIELDS):
            raise ValueError("Incomplete analyzer compatibility metadata")


def compatible(snapshots):
    return len({tuple(s.metadata[k] for k in COMPATIBILITY_FIELDS) for s in snapshots}) == 1


def observation_id(repository_id, stable_module_id, cutoff):
    return digest([repository_id, stable_module_id, iso(cutoff)])


def assert_available(cutoff, feature_cutoffs):
    if any(timestamp(v) > timestamp(cutoff) for v in feature_cutoffs):
        raise ValueError("Future information in predictors")


def predictor_names(model):
    if model == "M1":
        return BASE_FEATURES
    if model == "M2":
        return BASE_FEATURES + GRAPH_FEATURES
    raise ValueError("Unsupported predictor model")
