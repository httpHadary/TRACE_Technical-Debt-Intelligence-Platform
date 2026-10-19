"""New deterministic synthetic mechanisms. Predictor never imports this module."""
from datetime import datetime, timedelta, timezone
import math
import random
from forecasting_research.phase6_0.contracts import Request, digest, iso
from . import HORIZONS, VERSION, STATUS

FAMILIES = ('constant', 'long_plateaus', 'gradual_increase', 'gradual_decrease',
            'upward_jump', 'downward_jump', 'multiple_changes', 'stationary_noise',
            'changing_volatility', 'irregular', 'sparse', 'near_zero', 'mixed_scale',
            'hidden_future_change', 'distribution_shift', 'nonlinear_reversal')
OOD = ('damped_oscillation', 'saturating_recovery')
COUNTS = {'train': 24, 'validation': 8, 'calibration': 8, 'test': 12, 'ood': 24}
ROOT_SEED = 62020261020


def specs():
    result = []
    for partition, count in COUNTS.items():
        for family in OOD if partition == 'ood' else FAMILIES:
            for index in range(count):
                key = dict(version=VERSION, root_seed=ROOT_SEED, partition=partition,
                           family=family, index=index)
                identity = digest(key)
                result.append(dict(key, seed=int(identity[:16], 16),
                                   case_id='synthetic-'+identity[:32]))
    return result


def generate(spec):
    rng = random.Random(spec['seed'])
    family = spec['family']
    base = rng.uniform(15, 600)
    scale = 10**rng.uniform(1.7, 3.7) if family == 'mixed_scale' else 1.
    rate = rng.uniform(.025, .7)
    jump = rng.uniform(.1, .65)*base
    period = rng.randint(22, 65)
    phase = rng.randint(1, period)
    origin = datetime(2040, 1, 1, tzinfo=timezone.utc)+timedelta(days=spec['seed'] % 10000)
    hist_rng = random.Random(spec['seed'] ^ 0x13579)
    future_rng = random.Random(spec['seed'] ^ 0x24680)
    params = dict(base=base, scale=scale, rate=rate, jump=jump, period=period, phase=phase)

    def value(t, noise):
        if family == 'constant':
            v = base
        elif family == 'long_plateaus':
            v = base+jump*math.floor((t+phase)/(period*2))
        elif family == 'gradual_increase':
            v = base+rate*(t+180)
        elif family == 'gradual_decrease':
            v = base+rate*(90-t)
        elif family == 'upward_jump':
            v = base+jump*(t >= -period)+jump*(t >= period)
        elif family == 'downward_jump':
            v = base-jump*(t >= -period)-.4*jump*(t >= period)
        elif family == 'multiple_changes':
            v = base+.5*jump*math.floor((t+phase)/period)+jump*math.sin(t/period)
        elif family == 'stationary_noise':
            v = base+noise.gauss(0, base*.025)
        elif family == 'changing_volatility':
            v = base+noise.gauss(0, base*(.015 if t < -30 else .12))
        elif family in ('irregular', 'sparse'):
            v = base+rate*(t+180)+jump*math.floor((t+phase)/period)
        elif family == 'near_zero':
            v = 0. if spec['partition'] == 'test' and spec['index'] == 0 else max(0, base/1000+rate/30*math.sin(t/13))
        elif family == 'mixed_scale':
            v = base+rate*(t+180)+.2*jump*math.floor((t+phase)/period)
        elif family == 'hidden_future_change':
            v = base+(jump if spec['seed'] % 2 else -jump)*(t >= rng_jump)
        elif family == 'distribution_shift':
            v = base+rate*(t+180) if t <= 0 else base+180*rate-(rate+1)*(t)+jump*(t >= 45)
        elif family == 'nonlinear_reversal':
            v = base+rate*abs(t+phase)+jump*math.sin(t/(period/2))
        elif family == 'damped_oscillation':
            v = base+jump*math.exp(-max(0,t+180)/200)*math.sin(t/9)
        elif family == 'saturating_recovery':
            v = base/(1+math.exp(-(t+phase)/30))
        else:
            raise ValueError('Unknown generating mechanism')
        return round(max(0., v*scale), 8)

    rng_jump = rng.randint(1, 90)
    params['unobservable_future_jump_day'] = rng_jump
    stamps, values, reasons = [], [], []
    for t in range(-179, 1):
        v = value(t, hist_rng)
        if family == 'irregular' and t != 0 and hist_rng.random() < .65:
            continue  # No invented daily observations.
        missing = family == 'sparse' and t != 0 and hist_rng.random() < .85
        stamps.append(iso(origin+timedelta(days=t)))
        values.append(None if missing else v)
        reasons.append('SYNTHETIC_UNOBSERVED' if missing else None)
    request = Request(spec['case_id'], iso(origin), tuple(stamps), tuple(values), tuple(reasons))
    # Separate future random stream, never used in Request construction/features.
    future = {h: dict(timestamp_utc=request.endpoint(h), value=value(h, future_rng)) for h in HORIZONS}
    return request, future, params


def population():
    cases, identities, parameters = [], set(), set()
    for spec in specs():
        request, future, params = generate(spec)
        history_id = digest(dict(timestamps=[i for i in range(len(request.values))], values=list(request.values),
                                 offsets=[(datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ')-datetime.strptime(request.origin_utc, '%Y-%m-%dT%H:%M:%SZ')).days for t in request.timestamps]))
        parameter_id = digest(dict(family=spec['family'], parameters=params))
        if history_id in identities or parameter_id in parameters:
            raise ValueError('Duplicate numeric histories or generator parameters across population')
        identities.add(history_id)
        parameters.add(parameter_id)
        cases.append(dict(spec=spec, request=request.as_dict(), targets=future,
                          parameters=params, history_sha256=history_id, parameters_sha256=parameter_id))
    return cases
