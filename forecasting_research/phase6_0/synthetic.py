"""Explicit daily latent ground truth; observation masks are separate and never filled."""
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
import math
import random
from .contracts import Request,iso,digest

SCENARIOS=('constant','long_plateaus','slow_increase','slow_decrease','up_jump','down_jump',
           'multiple_steps','stationary_noise','sparse','irregular','quiet_then_change','near_zero',
           'mixed_scale','distribution_shift')
ORIGIN=datetime(2026,1,1,tzinfo=timezone.utc)


@dataclass(frozen=True)
class Case:
    request: Request
    scenario: str
    seed: int
    mechanism: str
    future_daily_truth: tuple
    future_timestamps: tuple

    def targets(self):
        return {h:self.future_daily_truth[h-1] for h in self.request.horizons}


def generate(scenario, replicate=0):
    if scenario not in SCENARIOS or type(replicate) is not int or not 0<=replicate<100:
        raise ValueError('Registered scenario/replicate required')
    seed=6000+SCENARIOS.index(scenario)*100+replicate
    rng=random.Random(seed)
    scale=(.01,1,1000)[replicate%3] if scenario=='mixed_scale' else (1+.1*replicate)
    base=100*scale;all_values=[]
    for day in range(-89,91):
        if scenario=='constant':v=base
        elif scenario=='long_plateaus':v=base+(10*scale if day>=-60 else 0)+(15*scale if day>=60 else 0)
        elif scenario=='slow_increase':v=base+.25*scale*day
        elif scenario=='slow_decrease':v=base-.25*scale*day
        elif scenario=='up_jump':v=base+(40*scale if day>=-10 else 0)+(30*scale if day>=45 else 0)
        elif scenario=='down_jump':v=base-(30*scale if day>=-10 else 0)-(25*scale if day>=45 else 0)
        elif scenario=='multiple_steps':v=base+15*scale*math.floor((day+89)/25)
        elif scenario=='stationary_noise':v=base+rng.gauss(0,3*scale)
        elif scenario in ('sparse','irregular'):v=base+.1*scale*day+rng.gauss(0,scale)
        elif scenario=='quiet_then_change':v=base+(60*scale if day>=15 else 0)
        elif scenario=='near_zero':v=0 if replicate%2==0 else max(0,.01+.001*math.sin(day))
        elif scenario=='mixed_scale':v=base+.15*scale*day+rng.gauss(0,scale)
        else:v=base+.05*day if day<=0 else base+1.5*day
        all_values.append(max(0,float(v)))
    times=[iso(ORIGIN+timedelta(days=d)) for d in range(-89,1)]
    values=all_values[:90];reasons=[None]*90
    if scenario=='sparse':
        for i in range(90):
            if i%14 and i!=89:values[i]=None;reasons[i]='SYNTHETIC_UNOBSERVED'
    if scenario=='irregular':
        keep=[i for i in range(90) if i in (0,89) or rng.random()<.3]
        times=[times[i] for i in keep];values=[values[i] for i in keep];reasons=[None]*len(keep)
    # Routing identity carries no explicit generating-process/scenario hint.
    case_id='synthetic-'+digest(['phase6.synthetic.case.v1',seed,scenario,replicate])[:32]
    req=Request(case_id,iso(ORIGIN),tuple(times),tuple(values),tuple(reasons))
    mechanism={'constant':'fixed stock','quiet_then_change':'constant past; unobservable future jump at +15d',
               'distribution_shift':'past slope .05; future slope 1.5','sparse':'daily latent slope/noise; observed every 14d and origin',
               'irregular':'daily latent slope/noise; stochastic observation timestamps',
               'near_zero':'even replicas identically zero; odd replicas small nonnegative sinusoid'}.get(scenario,scenario+'; see versioned generator equation')
    return Case(req,scenario,seed,mechanism,tuple(all_values[90:]),tuple(iso(ORIGIN+timedelta(days=d)) for d in range(1,91)))


def population():
    return [generate(s,r) for s in SCENARIOS for r in range(3)]

# Fixed before outcomes: 10 cases, 20 calls with repeatability check. No reselection.
CHRONOS_CASES=(('constant',0),('slow_increase',0),('slow_decrease',0),('up_jump',0),('down_jump',0),
               ('near_zero',0),('near_zero',1),('mixed_scale',0),('mixed_scale',2),('stationary_noise',0))
