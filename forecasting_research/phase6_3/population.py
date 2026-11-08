"""Independent mechanisms and seeds, with explicit stable/return OOD branches."""
from datetime import datetime, timedelta, timezone
import math
import random
from forecasting_research.phase6_0.contracts import Request, digest, iso
from . import VERSION, HORIZONS

FAMILIES = ('constant', 'stair_plateaus', 'sudden_decrease', 'gradual_decrease',
            'increase_recovery', 'decrease_regression', 'return_origin',
            'alternating_steps', 'abrupt_reversal', 'hidden_jump', 'irregular',
            'sparse', 'near_zero', 'mixed_scale', 'stationary_noise', 'variable_hazard')
OOD = ('hidden_pulse', 'sticky_renewal', 'delayed_reversal', 'saturating_reset',
       'burst_freeze', 'bounded_cycle', 'rare_relapse', 'reset_plateau')
COUNTS = dict(train=24, validation=12, calibration=12, test=16, ood=20)
ROOT_SEED = 63020261020


def specs():
    result = []
    for partition,count in COUNTS.items():
        for family in OOD if partition=='ood' else FAMILIES:
            for index in range(count):
                item = dict(version=VERSION,root_seed=ROOT_SEED,partition=partition,family=family,index=index)
                key = digest(item)
                result.append(dict(item,seed=int(key[:16],16),case_id='synthetic-'+key[:32]))
    return result


def pulse(t, period=30):
    position = t % period
    return min(position,period-position)/(period/2)


def trajectory(spec):
    rng = random.Random(spec['seed'])
    family = spec['family']
    base, rate = rng.uniform(30,800), rng.uniform(.03,.6)
    amplitude = base*rng.uniform(.2,.75)
    period, phase = rng.randint(25,85), rng.randint(1,24)
    scale = 10**rng.uniform(-2,3.5) if family=='mixed_scale' else 1.
    if family=='near_zero':
        scale = rng.uniform(.00001,.001)
    params = dict(base=base,rate=rate,amplitude=amplitude,period=period,phase=phase,scale=scale)
    hist_rng = random.Random(spec['seed'] ^ 0x6321)
    future_rng = random.Random(spec['seed'] ^ 0x6352)
    direction = -1 if spec['index']%2 else 1
    event_day = rng.randint(1,110)
    params.update(direction=direction,event_day=event_day)

    def path(t, noise):
        if family=='constant': v=base
        elif family=='stair_plateaus': v=base+.15*amplitude*math.floor((t+180)/period)
        elif family=='sudden_decrease': v=base+amplitude*(t < -phase)+amplitude*(t < period)
        elif family=='gradual_decrease': v=base+rate*(90-t)
        elif family=='increase_recovery': v=base+amplitude*max(0,1-abs(t+phase)/70)
        elif family=='decrease_regression': v=base-amplitude*max(0,1-abs(t+phase)/70)
        elif family=='return_origin': v=base+amplitude*pulse(t)
        elif family=='alternating_steps': v=base+amplitude*(math.floor((t+phase)/period)%2)
        elif family=='abrupt_reversal': v=base+rate*min(t+180,180)-2*rate*max(0,t)
        elif family=='hidden_jump': v=base+direction*amplitude*(t>=event_day)
        elif family in ('irregular','sparse'): v=base+direction*rate*t+.1*amplitude*math.floor((t+phase)/period)
        elif family=='near_zero': v=base+.1*amplitude*pulse(t,40)
        elif family=='mixed_scale': v=base+direction*rate*t+.1*amplitude*(math.floor((t+phase)/period)%2)
        elif family=='stationary_noise': v=base+noise.gauss(0,.03*base)
        elif family=='variable_hazard': v=base+.2*direction*amplitude*math.floor((t+180)/period)
        elif family in OOD:
            # Genuinely new historical patterns, not training-family aliases.
            offset = OOD.index(family)
            v=base+.15*amplitude*math.sin((t+phase)/(7+offset))+.01*rate*t*t/180
            if family=='sticky_renewal': v=base+.2*amplitude*(math.floor((t+180)/(period+11))%3)
            if family=='burst_freeze': v=base+.2*amplitude*(t>=-100)+.1*amplitude*(t>=-70)
            if family=='reset_plateau': v=base+.3*amplitude*max(0,(t+phase)/100)**2
        else: raise ValueError('Unknown registered mechanism')
        return round(max(0.,v*scale),8)

    history = [path(t,hist_rng) for t in range(-179,1)]
    current = history[-1]
    future = []
    for t in range(1,91):
        value = path(t,future_rng)
        if family=='variable_hazard' and spec['index']%3==0:
            value=current  # Unobservable cessation, explicitly part of generator.
        if family in OOD:
            branch=spec['index']%4
            if branch==0: value=current
            elif branch==1: value=current+direction*amplitude*pulse(t)
            else:
                if family=='hidden_pulse': d=amplitude*(1 if t<45 else .35)
                elif family=='sticky_renewal': d=amplitude*(.4+math.floor(t/40)*.2)
                elif family=='delayed_reversal': d=amplitude*(t/90 if t<45 else 1.1-t/90)
                elif family=='saturating_reset': d=amplitude*(1-math.exp(-t/35))
                elif family=='burst_freeze': d=amplitude*min(t,25)/25
                elif family=='bounded_cycle': d=amplitude*(.4+.2*math.sin(t/8))
                elif family=='rare_relapse': d=amplitude*(.7 if t<70 else .2)
                else: d=amplitude*(.8 if t<50 else .5)
                value=current+(d if branch==2 else -d)
        future.append(round(max(0.,value),8))
    # One genuinely zero test history, with its own non-daily observation mask.
    zero = family=='near_zero' and spec['partition']=='test' and spec['index']==0
    if zero:
        history=[0.]*180
        future=[0.]*90
    return history,future,dict(params,zero_case=zero)


def generate(spec):
    history,future,params = trajectory(spec)
    rng=random.Random(spec['seed'] ^ 0x6373)
    origin=datetime(2050,1,1,tzinfo=timezone.utc)+timedelta(days=spec['seed']%15000)
    stamps,values,reasons=[],[],[]
    for index,value in enumerate(history):
        t=index-179
        if spec['family']=='irregular' and t!=0 and rng.random()<.65:
            continue
        missing=(spec['family']=='sparse' and t!=0 and rng.random()<.82
                 or params['zero_case'] and t!=0 and index%5!=0)
        stamps.append(iso(origin+timedelta(days=t)))
        values.append(None if missing else value)
        reasons.append('SYNTHETIC_UNOBSERVED' if missing else None)
    request=Request(spec['case_id'],iso(origin),tuple(stamps),tuple(values),tuple(reasons))
    targets={str(h):dict(timestamp_utc=request.endpoint(h),value=future[h-1]) for h in HORIZONS}
    offsets=[(datetime.strptime(t,'%Y-%m-%dT%H:%M:%SZ')-datetime.strptime(request.origin_utc,'%Y-%m-%dT%H:%M:%SZ')).days for t in request.timestamps]
    history_id=digest(dict(timestamps=list(range(len(values))),values=values,offsets=offsets))
    return dict(request=request.as_dict(),targets=targets,spec=spec,
                history_sha256=history_id,parameters_sha256=digest(dict(family=spec['family'],params=params)),
                future_path_sha256=digest(future),endpoint_return_with_interim_change=any(v!=history[-1] for v in future) and all(future[h-1]==history[-1] for h in HORIZONS))


def population():
    cases=[generate(s) for s in specs()]
    for field in ('history_sha256','parameters_sha256'):
        if len({c[field] for c in cases})!=len(cases):
            raise ValueError('Duplicate synthetic history/parameters; no post-outcome deduplication')
    return cases
