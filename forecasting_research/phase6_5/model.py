"""Adaptive Persistence conditioned on admitted origin information, not identities."""
import math
import statistics as st
from collections import defaultdict
from functools import lru_cache
from forecasting_research.phase6_0.contracts import finite, utc, digest
from forecasting_research.phase6_2.features import slope
from .contracts import InformationRequest
from . import VERSION, HORIZONS

SHRINKS=(0.,.5,1.)
METHODS=('persistence','rolling_mean','anchored_trend','history_median','activity_median',
         'intent_median','adaptive_local','adaptive_stress')

@lru_cache(maxsize=8192)
def past(request):
    d=request.debt;origin=utc(d.origin_utc)
    obs=[((utc(t)-origin).total_seconds()/86400,float(v)) for t,v in zip(d.timestamps,d.values) if v is not None]
    scale=max(1.,d.values[-1]); gradient=slope([(t,v) for t,v in obs if t>=-30])
    history=0 if gradient is None or abs(gradient)/scale<.0002 else 1 if gradient>0 else -1
    return dict(current=float(d.values[-1]),scale=scale,history=history,
                gradient=slope([(t,v) for t,v in obs if t>=-90]) or 0.,
                mean=st.mean(v for _,v in obs[-7:]))

def quantile(xs,q):
    if not xs or not 0<q<=1 or not all(math.isfinite(v) for v in xs): raise ValueError('Invalid distribution')
    return sorted(xs)[max(0, math.ceil(q*len(xs))-1)]

def key(request,h,channel):
    if channel=='history':return str(past(request)['history'])
    name='observed_activity' if channel=='activity' else 'declared_intent'
    v,reason=request.signal(name,h)
    return None if v is None else str(int(v>=5) if channel=='activity' else v)

def fit(rows):
    if not rows or any(r['metadata']['role']!='train' for r in rows):raise ValueError('New synthetic train only')
    cells={};zero=0
    for channel in ('history','activity','intent'):
        for h in HORIZONS:
            groups=defaultdict(list)
            for r in rows:
                request=InformationRequest.from_dict(r['request']); f=past(request)
                target=r['targets'][str(h)]
                if target['timestamp_utc']!=request.debt.endpoint(h) or finite(target['value'])<0:
                    raise ValueError('Wrong training endpoint')
                if f['current']==0:continue
                k=key(request,h,channel)
                if k is not None:groups[k].append((target['value']-f['current'])/f['scale'])
            cells[f'{channel}:{h}']=dict(groups)
    zero=sum(InformationRequest.from_dict(r['request']).debt.values[-1]==0 for r in rows)
    return dict(version=VERSION,training_ids=[r['request']['debt']['case_id'] for r in rows],
                train_requests_sha256=digest([r['request'] for r in rows]),fit_role='train',
                zero_origins_kept_as_protected_cases=zero,cells=cells)

class Predictor:
    def __init__(self,state):
        if state.get('version')!=VERSION or state.get('fit_role')!='train':raise ValueError('Invalid fitted state')
        self.state=state

    def predict(self,request,h,method,shrink=0.):
        if not isinstance(request,InformationRequest):raise ValueError('Past-only typed input required')
        if type(h) is not int or h not in HORIZONS or method not in METHODS or type(shrink) not in (int,float) or shrink not in SHRINKS:
            raise ValueError('Unregistered forecast policy')
        f=past(request);delta=0.;probs=None;support=0;reason='PERSISTENCE';native=None
        if method=='rolling_mean':delta=f['mean']-f['current']
        elif method=='anchored_trend':delta=f['gradient']*h
        elif method not in ('persistence',):
            channel='history' if method=='history_median' else 'activity' if method=='activity_median' else 'intent'
            k=key(request,h,channel)
            values=[] if k is None else self.state['cells'].get(f'{channel}:{h}',{}).get(k,[])
            support=len(values)
            if f['current']==0:reason='ZERO_ORIGIN_PROTECTED'
            elif k is None:reason=request.signal('observed_activity' if channel=='activity' else 'declared_intent',h)[1]
            elif support<30:reason='INSUFFICIENT_TRAIN_SUPPORT'
            else:
                probs=[st.mean(v==0 for v in values),st.mean(v>0 for v in values),st.mean(v<0 for v in values)]
                native=[f['current']+f['scale']*quantile(values,q) for q in (.1,.5,.9)]
                factor=shrink if method.startswith('adaptive_') else 1.
                delta=factor*f['scale']*quantile(values,.5)
                reason='VALIDATION_PROTECTED' if factor==0 else 'EMPIRICAL_MEDIAN_ADJUSTMENT'
        raw=finite(f['current']+delta)
        return dict(request_id=request.identity,case_id=request.debt.case_id,horizon=h,
                    timestamp_utc=request.debt.endpoint(h),method=method,point=max(0.,raw),raw_stock=raw,
                    raw_delta=delta,reason=reason,support=support,direction_probabilities=probs,
                    local_q10_q50_q90=native)

def risk(rows):
    if not rows or any(r['role']!='validation' for r in rows):raise ValueError('Validation only')
    for r in rows:
        if not all(math.isfinite(r[k]) for k in ('point','actual','current','scale')) or r['scale']<=0:
            raise ValueError('Invalid risk inputs')
    families=defaultdict(list);base=defaultdict(list)
    unchanged=[r for r in rows if r['actual']==r['current']]
    counts={s:sum((r['actual']==r['current'] if s=='stable' else r['actual']>r['current'] if s=='up' else r['actual']<r['current']) for r in rows) for s in ('stable','up','down')}
    for r in rows:
        families[r['family']].append(abs(r['point']-r['actual'])/r['scale'])
        base[r['family']].append(abs(r['current']-r['actual'])/r['scale'])
    score=st.mean(st.mean(v) for v in families.values());b=st.mean(st.mean(v) for v in base.values())
    stable=st.mean(abs(r['point']-r['current'])/r['scale'] for r in unchanged) if unchanged else None
    enough=all(v>=24 for v in counts.values())
    raw=st.mean(abs(r['point']-r['actual']) for r in rows);rb=st.mean(abs(r['current']-r['actual']) for r in rows)
    return dict(score=score,base=b,skill=None if b==0 else 1-score/b,raw_mae=raw,raw_base=rb,
                unchanged_normalized_error=stable,counts=counts,adequate=enough,
                safe=enough and stable<=.05 and raw<=rb*1.02)

def select(candidate_rows,stress_rows=None):
    if set(candidate_rows)!=set(SHRINKS):raise ValueError('Complete fixed validation search required')
    scores=[]
    for a in SHRINKS:
        r=risk(candidate_rows[a]); stresses=[risk(rs[a]) for rs in (stress_rows or [])]
        eligible=a>0 and r['safe'] and r['skill'] is not None and r['skill']>.02
        if stresses:eligible=eligible and all(s['safe'] and s['score']<=s['base'] for s in stresses)
        scores.append(dict(shrink=a,risk=r,stress_risks=stresses,eligible=eligible))
    eligible=[r for r in scores if r['eligible']]
    chosen=min(eligible,key=lambda r:(r['risk']['score'],r['shrink'])) if eligible else scores[0]
    return dict(shrink=chosen['shrink'],reason='VALIDATION_ADMITTED' if eligible else 'PROTECTED_FALLBACK',search=scores)
