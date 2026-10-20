"""Two-clock, provenance-bound synthetic covariates. No approval mechanism."""
from dataclasses import dataclass
import re
from forecasting_research.phase6_0.contracts import Request, exact, digest, utc, finite
from . import VERSION, HORIZONS, SCOPE

FIELDS = ('name', 'horizon', 'value', 'unit', 'event_utc', 'available_utc',
          'window_start_utc', 'complete', 'provenance_sha256', 'status', 'purpose')

@dataclass(frozen=True)
class Signal:
    name: str
    horizon: int
    value: float | None
    unit: str
    event_utc: str
    available_utc: str
    window_start_utc: str
    complete: bool
    provenance_sha256: str
    status: str = SCOPE
    purpose: str = 'SYNTHETIC_INFORMATION_TEST_ONLY'

    def __post_init__(self):
        if self.status != SCOPE or self.purpose != 'SYNTHETIC_INFORMATION_TEST_ONLY':
            raise ValueError('REAL_DATA_NOT_ADMITTED')
        if self.name not in ('observed_activity', 'declared_intent'):
            raise ValueError('Signal not allowlisted; future outcomes prohibited')
        if type(self.horizon) is not int or self.horizon not in HORIZONS:
            raise ValueError('Exact horizon required')
        if type(self.complete) is not bool or not re.fullmatch('[0-9a-f]{64}', self.provenance_sha256):
            raise ValueError('Invalid completeness or provenance identity')
        if not utc(self.window_start_utc) <= utc(self.event_utc) <= utc(self.available_utc):
            raise ValueError('Invalid two-clock ordering')
        if self.name == 'observed_activity':
            if self.unit != 'count' or self.value is not None and (type(self.value) is not int or self.value < 0):
                raise ValueError('Activity is an integer count, never debt minutes')
            if not self.complete and self.value is not None:
                raise ValueError('Incomplete window must remain missing')
        else:
            if self.unit != 'ordinal_intent' or self.value is not None and (type(self.value) is not int or self.value not in (-1, 0, 1)):
                raise ValueError('Intent is an ordinal declaration, not realized direction')

    @classmethod
    def from_dict(cls, value):
        exact(value, FIELDS)
        return cls(**value)

    def as_dict(self):
        return vars(self).copy()

    def usable(self, origin):
        # Unavailable covariate does not exclude a case or erase the observed debt.
        if utc(self.available_utc) > utc(origin) or utc(self.event_utc) > utc(origin):
            return False, 'NOT_AVAILABLE_AT_ORIGIN'
        if not self.complete:
            return False, 'INCOMPLETE_WINDOW'
        if self.value is None:
            return False, 'EXPLICIT_MISSING'
        return True, 'AVAILABLE_NOT_PROVEN_PREDICTIVE'

@dataclass(frozen=True)
class InformationRequest:
    debt: Request
    signals: tuple
    version: str = VERSION

    def __post_init__(self):
        if self.version != VERSION or not isinstance(self.debt, Request) or type(self.signals) is not tuple:
            raise ValueError('Versioned immutable request required')
        if self.debt.values[-1] is None or len([v for v in self.debt.values if v is not None]) < 2:
            raise ValueError('Measured origin and historical support required')
        keys = []
        for s in self.signals:
            if not isinstance(s, Signal): raise ValueError('Typed signal required')
            keys.append((s.name, s.horizon))
        if len(keys) != len(set(keys)) or len(keys) > 6:
            raise ValueError('Duplicate or oversized signal population')

    @classmethod
    def from_dict(cls, obj):
        exact(obj, ('debt', 'signals', 'version'))
        if not isinstance(obj['signals'], list): raise ValueError('Signal array required')
        return cls(Request.from_dict(obj['debt']), tuple(Signal.from_dict(s) for s in obj['signals']), obj['version'])

    def as_dict(self):
        return dict(debt=self.debt.as_dict(), signals=[s.as_dict() for s in self.signals], version=self.version)

    @property
    def identity(self): return digest(self.as_dict())

    def signal(self, name, horizon):
        if type(horizon) is not int or horizon not in HORIZONS: raise ValueError('Unregistered horizon')
        for s in self.signals:
            if (s.name, s.horizon) == (name, horizon):
                ok, reason = s.usable(self.debt.origin_utc)
                return s.value if ok else None, reason
        return None, 'ABSENT_SIGNAL'
