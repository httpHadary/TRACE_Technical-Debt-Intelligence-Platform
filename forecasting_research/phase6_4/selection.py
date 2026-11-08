"""Fail-closed validation admission; never fall back to an unsafe adjustment."""
import math
import statistics as st
from collections import defaultdict
from .model import CONFIGS


def family_mean(rows,key):
    groups=defaultdict(list)
    for r in rows:groups[r['family']].append(key(r))
    return st.mean(st.mean(v) for v in groups.values()) if groups else None


def risk(rows):
    if not rows or any(r['partition']!='validation' for r in rows):raise ValueError('Validation only')
    if any(not all(math.isfinite(r[k]) for k in ('actual','point','current','model_scale')) or r['model_scale']<=0 for r in rows):raise ValueError('Invalid risk data')
    unchanged=[r for r in rows if r['actual']==r['current']]
    down=[r for r in rows if r['actual']-r['current']<=-max(10,.2*r['current'])]
    up=[r for r in rows if r['actual']-r['current']>=max(10,.2*r['current'])]
    enough=all(len(rs)>=24 and len({r['family'] for r in rs})>=2 for rs in (unchanged,down,up))
    mean=lambda rs,field: st.mean(abs(r[field]-r['actual']) for r in rs) if rs else None
    norm=lambda rs,field:family_mean(rs,lambda r:abs(r[field]-r['actual'])/r['model_scale'])
    score=norm(rows,'point');base=norm(rows,'current');raw=mean(rows,'point');rawbase=mean(rows,'current')
    safe=enough and norm(unchanged,'point')<=.01 and raw<=rawbase*1.01
    if enough:
        safe=safe and all(norm(rs,'point')<=1.02*norm(rs,'current') and mean(rs,'point')<=1.02*mean(rs,'current') for rs in (down,up))
    return dict(score=score,base=base,raw_mae=raw,raw_base=rawbase,adequate=enough,safe=bool(safe),
        unchanged_n=len(unchanged),large_decrease_n=len(down),large_increase_n=len(up),
        unchanged_error=norm(unchanged,'point'),safety_counts={name:dict(n=len(rs),families=len({r['family'] for r in rs})) for name,rs in [('unchanged',unchanged),('decrease',down),('increase',up)]})


def choose(scores):
    if len(scores)!=len(CONFIGS) or [r['config'] for r in scores]!=CONFIGS:raise ValueError('Complete registered search required')
    # Explicit protected fallback regardless of evidence availability; no eligible-or-all.
    protected=scores[0]
    if protected['config']['shrink']!=0:raise ValueError('Missing protected action')
    eligible=[r for r in scores[1:] if r['risk']['safe'] and r['risk']['score']<.98*r['risk']['base']]
    if not eligible:
        return dict(config=protected['config'],risk=protected['risk'],reason='PROTECTED_FALLBACK',admitted_adjustment=False)
    best=min(r['risk']['score'] for r in eligible)
    chosen=next(r for r in eligible if r['risk']['score']<=best*1.01)
    return dict(chosen,reason='VALIDATION_ADMITTED',admitted_adjustment=True)
