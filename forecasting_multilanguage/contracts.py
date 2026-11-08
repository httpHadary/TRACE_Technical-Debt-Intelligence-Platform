"""Strict, dependency-free contracts for a new, independently registered study."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import re

HORIZONS = (30, 60, 90)
MODES = ("RETROSPECTIVE_FIXED_ANALYZER", "OPERATIONAL_ASOF")
MISSING_WORDS = {"", "unknown", "unverified", "missing", "none", "n/a"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def utc(value):
    if not isinstance(value, str):
        raise ValueError("Explicit timezone-aware UTC timestamp required")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ValueError("UTC timestamp required; no naive/local conversion")
    return stamp.astimezone(timezone.utc)


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def hash_id(value, length=64):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{%d}" % length, value):
        raise ValueError("Invalid immutable digest")
    return value


def revision(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
        raise ValueError("Full Git object identity required")
    return value


def horizon_endpoint(cutoff, days):
    if type(days) is not int or days not in HORIZONS:
        raise ValueError("Only exact 30/60/90-day horizons admitted")
    return iso(utc(cutoff) + timedelta(seconds=days * 86400))


@dataclass(frozen=True)
class Measure:
    value: float | None
    status: str
    reason: str | None = None
    unit: str = "count"

    def __post_init__(self):
        if self.status == "OBSERVED":
            if (isinstance(self.value, bool) or not isinstance(self.value, (int, float))
                    or not math.isfinite(self.value) or self.value < 0 or self.reason is not None):
                raise ValueError("Observed measures must be finite nonnegative numbers")
        elif self.status not in ("MISSING", "INVALID", "UNSUPPORTED") or self.value is not None or not self.reason:
            raise ValueError("Missing measure needs null plus explicit status/reason")


def raw_measure(value, unit="count"):
    if value is None or value == "":
        return Measure(None, "MISSING", "SOURCE_MISSING", unit)
    if type(value) not in (int, float):
        return Measure(None, "INVALID", "NONNUMERIC_SOURCE", unit)
    if not math.isfinite(value) or value < 0:
        return Measure(None, "INVALID", "INVALID_NUMBER", unit)
    return Measure(float(value), "OBSERVED", unit=unit)


def metric_unit(key):
    key = key.lower()
    if key == "sqale_index":
        return "estimated_remediation_minutes"
    if key == "development_cost":
        return "estimated_development_minutes"
    if key.endswith(("density", "ratio")) or key == "coverage":
        return "percent"
    if key in ("ncloc", "lines", "duplicated_lines", "comment_lines"):
        return "lines"
    return "ordinal_rating" if key.endswith("rating") else "count"


DOMAIN_FIELDS = ("server_version", "edition", "scanner_version", "scanner_image_sha256",
                 "plugins", "rules_sha256", "scope_policy_sha256", "build_mode",
                 "runtime_manifest_sha256", "dependency_policy_sha256",
                 "suppression_policy_sha256", "metric_mode", "metric_semantics")


def analyzer_domain(manifest):
    """Hash incomplete manifests too, but never equate them with a known domain."""
    missing = []
    for key in DOMAIN_FIELDS:
        value = manifest.get(key)
        if value is not None and key != "plugins" and not isinstance(value, str):
            raise ValueError("Analyzer manifest scalar fields must be explicit strings")
        if value is None or (isinstance(value, str) and value.strip().lower() in MISSING_WORDS) or value == []:
            missing.append(key)
    for key in DOMAIN_FIELDS:
        if key.endswith("sha256") and key not in missing:
            hash_id(manifest[key])
    plugins = manifest.get("plugins", [])
    if not isinstance(plugins, list):
        raise ValueError("Plugin manifest must be a list")
    keys = []
    for plugin in plugins:
        if set(plugin) != {"key", "language", "version", "binary_sha256"}:
            raise ValueError("Complete plugin identity required")
        if any(not isinstance(plugin[k], str) or plugin[k].lower() in MISSING_WORDS for k in plugin):
            missing.append("plugins.identity")
        hash_id(plugin["binary_sha256"])
        keys.append((plugin["key"], plugin["language"]))
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate plugin identity")
    normalized = dict(manifest, plugins=sorted(plugins, key=lambda p: (p["key"], p["language"])))
    return {"domain_id": digest(normalized), "status": "INCOMPLETE" if missing else "COMPLETE",
            "missing_fields": sorted(set(missing)), "manifest": normalized}


@dataclass(frozen=True)
class Observation:
    repository_id: str
    family_id: str
    commit_sha: str
    source_tree_sha: str
    state_utc: str
    analysis_id: str
    executed_utc: str
    available_utc: str | None
    retrieved_utc: str
    domain_id: str
    scope_id: str
    raw_payload_sha256: str
    inventory_sha256: str
    coverage_sha256: str
    expected_source_files: int
    analyzed_files: int
    failed_files: int
    unsupported_files: int
    production_paths: tuple
    measures: dict
    languages: dict
    source_id: str

    def __post_init__(self):
        revision(self.commit_sha)
        revision(self.source_tree_sha)
        for value in (self.state_utc, self.executed_utc, self.retrieved_utc):
            utc(value)
        if utc(self.state_utc) > utc(self.executed_utc) or utc(self.executed_utc) > utc(self.retrieved_utc):
            raise ValueError("Impossible source/execution/retrieval chronology")
        if self.available_utc is not None:
            if not utc(self.executed_utc) <= utc(self.available_utc) <= utc(self.retrieved_utc):
                raise ValueError("Impossible availability clock")
        for value in (self.domain_id, self.scope_id, self.raw_payload_sha256, self.inventory_sha256, self.coverage_sha256, self.source_id):
            hash_id(value)
        if (any(type(v) is not int or v < 0 for v in (self.expected_source_files, self.analyzed_files, self.failed_files, self.unsupported_files))
                or self.expected_source_files <= 0 or self.analyzed_files != self.expected_source_files
                or self.failed_files or self.unsupported_files):
            raise ValueError("Complete measured production scope required")
        if len(self.production_paths) != len(set(self.production_paths)) or len(self.production_paths) != self.expected_source_files:
            raise ValueError("Unique complete production inventory required")
        if not self.repository_id or not self.family_id or not self.analysis_id:
            raise ValueError("Repository/family/analysis identity required")
        if not self.measures or any(not isinstance(v, Measure) for v in self.measures.values()):
            raise ValueError("Typed measures required")
        if any(type(v) is not int or v < 0 for v in self.languages.values()):
            raise ValueError("Language NCLOC must be nonnegative integer")

    @property
    def observation_id(self):
        return digest(asdict(self))
