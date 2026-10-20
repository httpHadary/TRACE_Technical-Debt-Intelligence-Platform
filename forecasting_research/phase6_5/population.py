"""Controlled information interventions, not simulation of real feature utility.

Causal order: generate history and declared plans at origin, generate imperfect
records of plans, then draw realizations/delays/directions and future magnitudes.
A record is not copied from a realized future. Hidden/reversed are paired changes
to future mechanisms with EXACTLY the same observable request.
"""
import math
import random
from datetime import datetime, timedelta, timezone
from forecasting_research.phase6_0.contracts import Request, digest, iso
from .contracts import InformationRequest, Signal
from . import HORIZONS

FAMILIES = ('plateau', 'growth', 'decline', 'cycle', 'sparse', 'noise')
UNSEEN = ('reversal_history', 'damped_history', 'irregular_history', 'burst_history')
COUNTS = dict(train=60, validation=30, calibration=30, test=40, unseen=60)
ROLES = tuple(COUNTS)

def rng_for(*parts): return random.Random(int(digest(list(parts))[:16], 16))

def generate(seed, role, family, index):
    if role not in ROLES or family not in (UNSEEN if role == 'unseen' else FAMILIES):
        raise ValueError('Unregistered generation role or mechanism')
    r = rng_for(seed, role, family, index)
    origin = datetime(2040, 1, 1, tzinfo=timezone.utc) + timedelta(days=r.randrange(3000))
    scale = (0., 10., 100., 10000.)[index % 4]
    current = scale * r.uniform(.8, 1.2)
    vals=[];times=[];reasons=[]
    phase=r.uniform(0, 6); slope=r.uniform(.001, .003)
    for i in range(96):
        t=i-95
        factor = {'growth': 1+slope*t, 'decline': 1-slope*t,
                  'cycle': 1+.1*math.sin(t/8+phase),
                  'reversal_history': 1+.15*abs(t+35)/95,
                  'damped_history': 1+.1*math.sin(t/5)*math.exp(t/50),
                  'burst_history': 1+.12*(t < -40)}.get(family, 1.)
        if family in ('noise', 'irregular_history'): factor += r.uniform(-.04,.04)
        value=current if i==95 else max(0., current*factor)
        if family=='irregular_history' and i not in (0,95) and i%4: continue
        missing=family=='sparse' and i not in (0,95) and i%5!=0
        times.append(iso(origin+timedelta(days=t)));vals.append(None if missing else value)
        reasons.append('SYNTHETIC_UNOBSERVED' if missing else None)
    debt=Request('synthetic-info-'+digest([seed,role,family,index])[:20],iso(origin),tuple(times),tuple(vals),tuple(reasons))
    # Planned intent is generated BEFORE all future realizations. It is a hypothetical
    # ordinal record, NOT mined refactoring, actual future churn or debt direction.
    plan=r.choice((-1,0,1))
    recorded=plan if r.random()<.9 else r.choice((-1,0,1))
    activity=(8 if plan else 1)+r.randrange(3)
    signals=[]
    for h in HORIZONS:
        for name,value,unit in [('declared_intent',recorded,'ordinal_intent'),('observed_activity',activity,'count')]:
            signals.append(Signal(name,h,value,unit,iso(origin-timedelta(days=1)),iso(origin),
                                  iso(origin-timedelta(days=30)),True,digest(['synthetic_record',seed,role,family,index,name,h,value])))
    req=InformationRequest(debt,tuple(signals))
    # One realization draw makes horizon changes nested; return-to-origin is
    # allowed in hidden controls. No request contains the following variables.
    u=r.random(); reverse=r.random()<.07
    magnitude=r.uniform(.12,.30)
    targets={}; hidden={}; reversed_targets={}
    for h,prob in zip(HORIZONS,(.7,.82,.9)):
        direction=plan if u<prob else 0
        if reverse: direction=-direction
        # Exactly zero histories have no directional decreases available; retained
        # and counted in normalized-zero and sign-support diagnostics.
        delta=current*magnitude*(h/30)**.6*direction
        targets[str(h)]=dict(timestamp_utc=debt.endpoint(h),value=max(0.,current+delta))
        # Independent unobservable event: signal loses its relation to the future.
        hr=rng_for(seed,role,family,index,h,'hidden')
        hd=hr.choice((-1,0,1)); hm=hr.uniform(.12,.30)
        hidden[str(h)]=dict(timestamp_utc=debt.endpoint(h),value=max(0.,current+current*hm*(h/30)**.6*hd))
        reversed_targets[str(h)]=dict(timestamp_utc=debt.endpoint(h),value=max(0.,current-delta))
    return dict(request=req.as_dict(),targets=targets,hidden_targets=hidden,reversed_targets=reversed_targets,
                metadata=dict(role=role,family=family,seed=seed,index=index,extreme_scale=scale==10000.,
                              history_sha256=digest([debt.timestamps,debt.values,debt.reasons])))

def population(seed,role):
    return [generate(seed,role,f,i) for f in (UNSEEN if role=='unseen' else FAMILIES) for i in range(COUNTS[role])]

def delayed(request):
    from .contracts import InformationRequest, Signal
    from forecasting_research.phase6_0.contracts import utc
    signals=[]
    for s in request.signals:
        obj=s.as_dict(); obj['available_utc']=iso(utc(request.debt.origin_utc)+timedelta(days=1))
        signals.append(Signal.from_dict(obj))
    return InformationRequest(request.debt,tuple(signals))
