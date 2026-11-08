"""New 512-day observed histories; independent future and observation-mask streams."""
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
import random,math
from forecasting_research.phase6_0.contracts import Request,digest,iso
from forecasting_research.phase6_0.synthetic import SCENARIOS
from . import VERSION

ORIGIN=datetime(2026,6,1,tzinfo=timezone.utc)


@dataclass(frozen=True)
class Spec:
    scenario: str
    replicate: int

    def __post_init__(self):
        if self.scenario not in SCENARIOS or type(self.replicate) is not int or self.replicate not in (0,1,2):
            raise ValueError('Only preregistered scenarios/replicates')

    @property
    def seed(self):return 61000+100*SCENARIOS.index(self.scenario)+self.replicate
    @property
    def case_id(self):return 'synthetic-'+digest([VERSION,self.seed])[:32]
    @property
    def scale(self):return (.01,1,1000)[self.replicate] if self.scenario=='mixed_scale' else 1+.1*self.replicate


def value(spec,day,rng):
    s=spec.scenario;k=spec.scale
    if s=='constant':v=100
    elif s=='long_plateaus':v=100+sum(15 for change in (-400,-200,-30,60) if day>=change)
    elif s=='slow_increase':v=300+.25*day
    elif s=='slow_decrease':v=100-.15*day
    elif s=='up_jump':v=100+40*(day>=-150)+30*(day>=45)
    elif s=='down_jump':v=150-30*(day>=-150)-25*(day>=45)
    elif s=='multiple_steps':v=100+15*math.floor((day+511)/25)
    elif s=='stationary_noise':v=100+rng.gauss(0,3)
    elif s in ('sparse','irregular'):v=100+.05*day+rng.gauss(0,1)
    elif s=='quiet_then_change':v=100+60*(day>=15)
    elif s=='near_zero':v=0 if spec.replicate%2==0 else max(0,.01+.001*math.sin(day))
    elif s=='mixed_scale':v=300+.15*day+rng.gauss(0,1)
    else:v=100+(.05*day if day<=0 else 1.5*day)
    return max(0.,float(v*k))


def history(spec):
    rng=random.Random(spec.seed);mask=random.Random(spec.seed+200000)
    times=[];values=[];reasons=[]
    for day in range(-511,1):
        v=value(spec,day,rng)
        if spec.scenario=='irregular' and day not in (-511,0) and mask.random()>.3:continue
        missing=spec.scenario=='sparse' and (day+511)%14!=0 and day!=0
        times.append(iso(ORIGIN+timedelta(days=day)))
        values.append(None if missing else v);reasons.append('SYNTHETIC_UNOBSERVED' if missing else None)
    return Request(spec.case_id,iso(ORIGIN),tuple(times),tuple(values),tuple(reasons))


def future(spec):
    # Independent future noise. No future RNG calls affect history or observation mask.
    rng=random.Random(spec.seed+100000)
    return {h:dict(timestamp_utc=iso(ORIGIN+timedelta(days=h)),value=value_) for h,value_ in
            ((d,value(spec,d,rng)) for d in range(1,91)) if h in (30,60,90)}


def short(long):
    if not isinstance(long,Request) or not long.complete_daily(512):
        raise ValueError('Full 512 genuine generated daily observations required')
    return Request(long.case_id,long.origin_utc,long.timestamps[-90:],long.values[-90:],long.reasons[-90:])


def specs():return [Spec(s,r) for s in SCENARIOS for r in range(3)]


def population():
    result=[]
    for spec in specs():
        long=history(spec);eligible=long.complete_daily(512)
        result.append(dict(case_id=spec.case_id,scenario=spec.scenario,replicate=spec.replicate,
                      history_seed=spec.seed,future_seed=spec.seed+100000,mask_seed=spec.seed+200000,scale=spec.scale,
                      origin_utc=long.origin_utc,eligible=eligible,exclusion=None if eligible else 'INELIGIBLE_SPARSE_OR_IRREGULAR_NO_FILL',
                      history_positions=len(long.values),known=sum(v is not None for v in long.values),
                      long_request_sha256=long.identity,short_request_sha256=short(long).identity if eligible else None))
    return result
