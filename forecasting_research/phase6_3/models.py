"""Interpretable synthetic fits and immutable frozen transfer; no target at prediction."""
from functools import lru_cache
from types import MappingProxyType
import numpy as np
from forecasting_research.phase6_0.contracts import Request, finite, digest
from forecasting_research.phase6_2 import models as old
from forecasting_research.phase6_2.features import extract, NAMES
from . import VERSION, STATUS, HORIZONS

METHODS = ('persistence','rolling_mean','anchored_trend','trend_shrink','direct_delta',
           'residual_blend','binary_adaptive','direction_gate','asymmetric_weighted',
           'adaptive_persistence','frozen_phase6_2','comparison_champion')
ALPHAS = (1.,10.)


@lru_cache(maxsize=4096)
def features(request):
    if not isinstance(request,Request):
        raise ValueError('Typed past-only request required')
    f=extract(request)
    f['vector']=tuple(f['vector'])
    return MappingProxyType(f)


def configs(method):
    if method in ('persistence','rolling_mean','anchored_trend','frozen_phase6_2'):
        return [dict(method=method)]
    if method=='trend_shrink':
        return [dict(method=method,shrink=w) for w in (0.,.25,.5,1.)]
    result=[dict(method=method,alpha=1.,balance='none',threshold=.9,minimum=.02,shrink=0.)] if method=='adaptive_persistence' else []
    for alpha in ALPHAS:
        if method=='direct_delta':
            result.append(dict(method=method,alpha=alpha))
        elif method=='binary_adaptive':
            result += [dict(method=method,alpha=alpha,threshold=t) for t in (.5,.75,.9)]
        elif method=='residual_blend':
            result += [dict(method=method,alpha=alpha,shrink=w) for w in (0.,.25,.5,1.)]
        elif method in ('direction_gate','asymmetric_weighted','adaptive_persistence'):
            for balance in ('none','balanced'):
                for threshold in (.5,.75,.9) if method=='direction_gate' else (.75,.9) if method=='adaptive_persistence' else (None,):
                    for minimum in (.02,.1) if method=='adaptive_persistence' else (None,):
                        for shrink in (.25,.5) if method=='adaptive_persistence' else (None,):
                            c=dict(method=method,alpha=alpha,balance=balance)
                            if threshold is not None: c['threshold']=threshold
                            if minimum is not None: c['minimum']=minimum
                            if shrink is not None: c['shrink']=shrink
                            result.append(c)
        else: raise ValueError('Unregistered method')
    return result


@lru_cache(maxsize=16)
def config_hashes(method):
    return frozenset(digest(c) for c in configs(method))


def weighted_logistic(x,y,weights,alpha):
    y=np.asarray(y,dtype=float);weights=np.asarray(weights,dtype=float)
    if len(y)!=len(x) or weights.shape!=y.shape or not np.isfinite(weights).all() or (weights<=0).any():
        raise ValueError('Aligned positive class weights required')
    if len(set(y))<2:
        return dict(kind='single_class',probability=float(y[0]),eligible=False,
                    reason='INSUFFICIENT_CLASS_DIVERSITY; no logistic fit')
    beta=np.zeros(x.shape[1]);penalty=np.eye(x.shape[1])*alpha;penalty[0,0]=0
    for _ in range(40):
        p=old.sigmoid(x@beta)
        gradient=x.T@(weights*(p-y))+penalty@beta
        hessian=x.T@((weights*p*(1-p))[:,None]*x)+penalty
        beta-=.5*np.linalg.solve(hessian,gradient)
    if not np.isfinite(beta).all(): raise ValueError('Nonfinite direction coefficients')
    return dict(kind='logistic',coefficients=beta.tolist(),eligible=True,iterations=40)


def direction_probabilities(head,x):
    values=np.array([old.change_probability(c,x) for c in head['ovr']])
    if not np.isfinite(values).all() or values.sum()<=0:
        raise ValueError('Invalid OVR probability vector')
    values=values/values.sum()
    return [old.probability(float(p)) for p in values]


def fit(rows,transfer):
    if not rows or any(r['partition']!='train' for r in rows):
        raise ValueError('New synthetic training only')
    binary=old.fit(rows)  # Same algorithm on NEW training, never old data/state.
    requests=[Request.from_dict(r['request']) for r in rows]
    fs=[features(r) for r in requests]
    x=old.transform(binary['preprocessor'],[f['vector'] for f in fs])
    heads={}
    for h in HORIZONS:
        y=np.array([(r['targets'][str(h)]['value']-f['current'])/f['model_scale'] for r,f in zip(rows,fs)])
        classes=np.where(y==0,0,np.where(y>0,1,2))
        counts=[int((classes==c).sum()) for c in range(3)]
        options={}
        for alpha in ALPHAS:
            sides={}
            for name,mask in [('increase',y>0),('decrease',y<0)]:
                sides[name]=old.ridge(x[mask],y[mask],alpha) if mask.sum()>=2 else None
            for balance in ('none','balanced'):
                weights=np.ones(len(y)) if balance=='none' else np.array([len(y)/(3*counts[c]) for c in classes])
                ovr=[weighted_logistic(x,(classes==c).astype(int),weights,alpha) for c in range(3)]
                options[str(alpha)+'/'+balance]=dict(ovr=ovr,**sides,counts=counts,eligible=all(c>=2 for c in counts),
                    class_weight=balance,probability_semantics='normalized one-vs-rest estimates; not calibrated posteriors')
        heads[str(h)]=options
    return dict(version=VERSION,status=STATUS,feature_names=list(NAMES),binary_new_fit=binary,
                direction_heads=heads,transfer=transfer,train_n=len(rows),
                training_requests_sha256=digest([r.as_dict() for r in requests]),
                transfer_refitted=False)


def predict(request,state,config,horizon):
    if (not isinstance(request,Request) or not isinstance(config,dict) or type(horizon) is not int
            or horizon not in HORIZONS or digest(config) not in config_hashes(config.get('method')) or state['version']!=VERSION):
        raise ValueError('Registered request/config/version/horizon required')
    f=features(request);method=config['method'];probs=None;p=None
    direct=None;up_raw=down_raw=None;action=0.;shrink=None
    if method=='frozen_phase6_2':
        transfer=state['transfer'];conf=transfer['selection']['horizons'][str(horizon)]['configs']['selected']
        result=old.predict(request,transfer['model'],conf,horizon)
        raw=result['raw_stock'];p=result['p_change'];action=result['raw_signed_delta']/f['model_scale']
    elif method=='persistence': raw=f['current']
    elif method=='rolling_mean':
        observed=[v for v in request.values if v is not None];raw=float(np.mean(observed[-7:]))
    elif method in ('anchored_trend','trend_shrink'):
        if f['vector'][9] is None: raise ValueError('INSUFFICIENT_OBSERVATIONS for fixed trend')
        shrink=config.get('shrink',1.)
        direct=horizon*f['vector'][9];action=shrink*direct
        raw=f['current']+action*f['model_scale']
    else:
        binary=state['binary_new_fit']
        x=old.transform(binary['preprocessor'],[f['vector']])
        head=binary['heads'][str(horizon)][str(config['alpha'])]
        p=old.change_probability(head['classifier'],x)
        if method in ('direct_delta','residual_blend'):
            direct=float((x@np.array(head['direct']))[0]);shrink=config.get('shrink',1.);action=direct*shrink
        elif method=='binary_adaptive':
            if head['conditional'] is None: raise ValueError('INELIGIBLE_CONDITIONAL_CHANGE')
            direct=float((x@np.array(head['conditional']))[0]);action=direct if p>=config['threshold'] else 0.
        else:
            direction=state['direction_heads'][str(horizon)][str(config['alpha'])+'/'+config['balance']]
            if not direction['eligible']: raise ValueError('INELIGIBLE_THREE_CLASS_TRAINING_SUPPORT')
            probs=direction_probabilities(direction,x);p=1-probs[0]
            if direction['increase'] is None or direction['decrease'] is None:
                raise ValueError('INELIGIBLE_DIRECTION_MAGNITUDE')
            up_raw=float((x@np.array(direction['increase']))[0]);down_raw=float((x@np.array(direction['decrease']))[0])
            up,down=max(0.,up_raw),min(0.,down_raw)
            chosen=max(range(3),key=lambda i:probs[i])
            direct=(0.,up,down)[chosen]
            if method=='asymmetric_weighted': action=probs[1]*up+probs[2]*down
            elif method=='direction_gate': action=direct if probs[chosen]>=config['threshold'] else 0.
            else:
                minimum=max(config['minimum'],.25*f['vector'][5])
                reliability=1/(1+f['vector'][20]*180/30)
                shrink=config['shrink']*reliability
                action=direct*shrink if probs[chosen]>=config['threshold'] and abs(direct)>=minimum else 0.
        raw=f['current']+action*f['model_scale']
    finite(raw)
    return dict(version=VERSION,status=STATUS,unit=request.unit,case_id=request.case_id,request_id=request.identity,
                horizon=horizon,timestamp_utc=request.endpoint(horizon),config_sha256=digest(config),
                point=max(0.,raw),raw_stock=raw,raw_signed_delta=raw-f['current'],
                binary_change_probability=p,direction_probabilities=probs,raw_component_delta=direct,
                raw_upward_component=up_raw,raw_downward_component=down_raw,
                intentional_shrinkage=shrink,action_delta_normalized=(raw-f['current'])/f['model_scale'],
                is_frozen_transfer=method=='frozen_phase6_2')
