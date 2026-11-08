"""Development-only interval choice; independent final calibration, no test residuals."""
import numpy as np
from forecasting_research.phase6_0.contracts import finite
from .models import features

KINDS=('shared_symmetric','signed_global','direction_stratified')
MIN_BIN=12


def bucket(prediction,current):
    return 'stable' if prediction==current else 'increase' if prediction>current else 'decrease'


def build(records,kind,partition):
    if partition not in ('train_interval_prototype','calibration') or kind not in KINDS:
        raise ValueError('Only training prototypes or separate calibration labels permitted')
    residuals=[(r['actual']-r['prediction'])/r['model_scale'] for r in records]
    if len(residuals)<MIN_BIN or not np.isfinite(residuals).all():
        raise ValueError('INSUFFICIENT_CALIBRATION_SUPPORT')
    def qs(values):
        if kind=='shared_symmetric':
            radius=float(np.quantile(np.abs(values),.8,method='higher'))
            return [-radius,0.,radius]
        return [float(v) for v in np.quantile(values,[.1,.5,.9],method='linear')]
    global_q=qs(residuals)
    groups={}
    for label in ('stable','increase','decrease'):
        values=[v for r,v in zip(records,residuals) if bucket(r['prediction'],r['current'])==label]
        groups[label]=dict(n=len(values),quantiles=qs(values) if len(values)>=MIN_BIN else global_q,
                           fallback_to_global=len(values)<MIN_BIN)
    return dict(kind=kind,partition=partition,n=len(records),global_quantiles=global_q,bins=groups,
                bin_policy='Predicted direction only, never true future direction',min_bin=MIN_BIN)


def apply(prediction,current,scale,state,widen=1.):
    prediction,current,scale,widen=map(finite,(prediction,current,scale,widen))
    if widen not in (1.,1.25) or scale<1:
        raise ValueError('Registered finite scale and bounded widening required')
    q=state['bins'][bucket(prediction,current)]['quantiles'] if state['kind']=='direction_stratified' else state['global_quantiles']
    if len(q)!=3 or not np.isfinite(q).all() or not q[0]<=q[1]<=q[2]:
        raise ValueError('Invalid interval; no sorting repair')
    center=q[1]
    adjusted=[center+widen*(q[0]-center),center,center+widen*(q[2]-center)]
    raw=[prediction+v*scale for v in adjusted]
    return dict(raw=raw,quantiles=[max(0.,v) for v in raw],widen=widen,
                bin=bucket(prediction,current),kind=state['kind'])


def interval_objective(records,state,widen):
    scores,widths,covered=[],[],[]
    for row in records:
        q=apply(row['prediction'],row['current'],row['model_scale'],state,widen)['quantiles']
        width=q[2]-q[0]
        score=width+10*max(0,q[0]-row['actual'])+10*max(0,row['actual']-q[2])
        scores.append(score/row['model_scale']);widths.append(width/row['model_scale'])
        covered.append(q[0]<=row['actual']<=q[2])
    # Family balance is handled explicitly, not pooled scale-weighted scores.
    families=sorted({r['family'] for r in records})
    macro=lambda values:float(np.mean([np.mean([v for r,v in zip(records,values) if r['family']==f]) for f in families]))
    return dict(normalized_interval_score=macro(scores),normalized_mean_width=macro(widths),
                coverage=float(np.mean(covered)),quality_eligible=.75<=float(np.mean(covered))<=.85 and macro(widths)<=2.)


def choose(train_records,validation_records,partition='validation'):
    if partition!='validation': raise ValueError('Interval selection requires validation only')
    candidates=[]
    for kind in KINDS:
        prototype=build(train_records,kind,'train_interval_prototype')
        for widen in (1.,1.25):
            candidates.append(dict(kind=kind,widen=widen,**interval_objective(validation_records,prototype,widen)))
    eligible=[r for r in candidates if r['quality_eligible']]
    chosen=min(eligible or candidates,key=lambda r:r['normalized_interval_score'])
    return dict(chosen=chosen,candidates=candidates,quality_gate_passed=bool(eligible),
                selection_partition='validation',prototype_partition='train_interval_prototype',
                limitation='In-sample training residual prototypes for validation choice; final independent calibration, no coverage guarantee')
