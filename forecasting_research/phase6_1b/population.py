"""Preregistered generated daily histories; future noise has an independent stream."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import random
from forecasting_research.phase6_0.contracts import Request, digest, iso
from forecasting_research.phase6_0.synthetic import SCENARIOS
from . import VERSION

ORIGIN = datetime(2026, 10, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class Spec:
    scenario: str
    replicate: int

    def __post_init__(self):
        if self.scenario not in SCENARIOS or type(self.replicate) is not int or self.replicate not in (0, 1, 2):
            raise ValueError('Registered synthetic family and replicate required')

    @property
    def seed(self):
        return 6101000 + 100 * SCENARIOS.index(self.scenario) + self.replicate

    @property
    def case_id(self):
        return 'synthetic-' + digest([VERSION, self.seed])[:32]

    @property
    def scale(self):
        return (.02, 2., 500.)[self.replicate] if self.scenario == 'mixed_scale' else (1., 1.3, 1.6)[self.replicate]


def value(spec, day, rng):
    s = spec.scenario
    if s == 'constant':
        v = 85
    elif s == 'long_plateaus':
        v = 90 + sum(12 for change in (-420, -210, -40, 50) if day >= change)
    elif s == 'slow_increase':
        v = 240 + .2 * day
    elif s == 'slow_decrease':
        v = 95 - .12 * day
    elif s == 'up_jump':
        v = 80 + 35 * (day >= -120) + 25 * (day >= 35)
    elif s == 'down_jump':
        v = 160 - 45 * (day >= -120) - 35 * (day >= 35)
    elif s == 'multiple_steps':
        v = 95 + 9 * math.floor((day + 511) / 31)
    elif s == 'stationary_noise':
        v = 110 + rng.gauss(0, 4)
    elif s in ('sparse', 'irregular'):
        v = 110 + .08 * day + rng.gauss(0, 2)
    elif s == 'quiet_then_change':
        v = 85 + 45 * (day >= 20)
    elif s == 'near_zero':
        v = 0 if spec.replicate != 1 else max(0, .02 + .003 * math.sin(day / 3))
    elif s == 'mixed_scale':
        v = 240 + .2 * day + rng.gauss(0, 2)
    else:  # intentionally unobservable future slope shift
        v = 130 + (.04 * day if day <= 0 else 1.1 * day)
    return max(0., float(v * spec.scale))


def specs():
    return [Spec(s, r) for s in SCENARIOS for r in range(3)]


def history(spec):
    rng, mask = random.Random(spec.seed), random.Random(spec.seed + 200000)
    times, values, reasons = [], [], []
    for day in range(-511, 1):
        v = value(spec, day, rng)
        if spec.scenario == 'irregular' and day not in (-511, 0) and mask.random() > .35:
            continue
        missing = spec.scenario == 'sparse' and (day + 511) % 17 != 0 and day != 0
        times.append(iso(ORIGIN + timedelta(days=day)))
        values.append(None if missing else v)
        reasons.append('SYNTHETIC_UNOBSERVED' if missing else None)
    return Request(spec.case_id, iso(ORIGIN), tuple(times), tuple(values), tuple(reasons))


def future(spec):
    rng = random.Random(spec.seed + 100000)
    points = {d: value(spec, d, rng) for d in range(1, 91)}
    return {h: {'timestamp_utc': iso(ORIGIN + timedelta(days=h)), 'value': points[h]} for h in (30, 60, 90)}


def population():
    rows = []
    for spec in specs():
        req = history(spec)
        rows.append(dict(case_id=spec.case_id, scenario=spec.scenario, replicate=spec.replicate,
                         seed=spec.seed, future_seed=spec.seed + 100000, mask_seed=spec.seed + 200000,
                         scale=spec.scale, origin_utc=req.origin_utc, request_id=req.identity,
                         eligible=req.complete_daily(512), history_positions=len(req.values),
                         exclusion=None if req.complete_daily(512) else 'SPARSE_OR_IRREGULAR_NO_FILL'))
    return rows
