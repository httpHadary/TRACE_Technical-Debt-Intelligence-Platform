"""Phase 0 study configuration. No model imports or execution on load."""
from dataclasses import asdict, dataclass
from pathlib import Path
import re

from contracts import digest, read_json, safe_id

from .contracts import TargetContract


@dataclass(frozen=True)
class ModelCandidate:
    name: str
    model_id: str
    revision: str
    license: str
    role: str
    context_days: int
    native_horizon_steps: int

    def __post_init__(self):
        safe_id(self.name)
        if not isinstance(self.model_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.model_id):
            raise ValueError("Explicit model repository required")
        if not re.fullmatch(r"[0-9a-f]{40}", self.revision):
            raise ValueError("Immutable checkpoint revision required")
        if self.license not in ("Apache-2.0", "UNRESOLVED"):
            raise ValueError("Explicit license decision required")
        if self.role not in ("primary_pretrained", "conditional_comparator"):
            raise ValueError("Unknown candidate role")
        if type(self.context_days) is not int or self.context_days <= 0 or type(self.native_horizon_steps) is not int or self.native_horizon_steps <= 0:
            raise ValueError("Positive native context/horizon required")


@dataclass(frozen=True)
class StudyConfig:
    study_id: str
    dataset_path: str
    dataset_source: str
    dataset_license: str
    output_root: str
    horizons_days: tuple[int, ...]
    models: tuple[ModelCandidate, ...]
    smoke_timeout_seconds: int = 900
    pilot_budget_seconds: int = 28800
    phase: int = 0
    mvp_schema_version: int = 1

    def __post_init__(self):
        safe_id(self.study_id)
        if type(self.phase) is not int or self.phase != 0 or type(self.mvp_schema_version) is not int or self.mvp_schema_version != 1:
            raise ValueError("Only Phase 0 / MVP schema 1 is implemented")
        if self.horizons_days != (30, 60, 90) or any(type(h) is not int for h in self.horizons_days):
            raise ValueError("Register exact horizons (30, 60, 90); no weekly substitution")
        for h in self.horizons_days:
            TargetContract(h)
        for path in (self.dataset_path, self.output_root):
            if not isinstance(path, str) or not Path(path).is_absolute():
                raise ValueError("Explicit absolute dataset/output paths required")
        dataset = Path(self.dataset_path).resolve()
        output = Path(self.output_root).resolve()
        if dataset == output or dataset.is_relative_to(output):
            raise ValueError("Dataset must remain outside output root")
        if not self.dataset_source.startswith("https://") or self.dataset_license != "CC-BY-NC-SA-4.0":
            raise ValueError("V2 source and research-use license required")
        if not self.models or len({m.name for m in self.models}) != len(self.models):
            raise ValueError("Unique model candidates required")
        for limit in (self.smoke_timeout_seconds, self.pilot_budget_seconds):
            if type(limit) is not int or limit <= 0:
                raise ValueError("Positive resource budgets required")

    @classmethod
    def load(cls, path):
        raw = read_json(path)
        raw["horizons_days"] = tuple(raw["horizons_days"])
        raw["models"] = tuple(ModelCandidate(**m) for m in raw["models"])
        return cls(**raw)

    def record(self):
        return asdict(self)

    @property
    def config_id(self):
        return digest(self.record())
