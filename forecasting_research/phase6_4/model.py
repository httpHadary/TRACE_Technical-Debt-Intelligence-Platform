"""Past-only local change distributions with an explicit persistence action."""
from functools import lru_cache
import numpy as np
from forecasting_research.phase6_0.contracts import Request, digest, finite
from forecasting_research.phase6_2.features import extract, baseline
from forecasting_research.phase6_2.models import transform_fit, transform, ridge
from . import VERSION, HORIZONS

# Exclude absolute log-scale, counts redundant with coverage, and unbounded past age.
FEATURES=(0,2,4,5,6,7,8,9,10,11,12,13,14,18,19,20,21,22,23)
CONFIGS=[dict(k=16,confidence=1.,shrink=0.)]+[
    dict(k=k,confidence=c,shrink=s) for k in (16,48,96) for c in (.6,.8) for s in (.25,.5,1.)]
METHODS=('persistence','rolling_mean','anchored_trend','direct_delta','local_median',
         'adaptive_persistence','frozen_phase6_3')


@lru_cache(maxsize=8192)
def features(request):
    f=extract(request)
    # New inference semantics: gaps do not imply continuous no-change observations.
    vector=list(f['vector']);vector[15]=0.
    return dict(f,vector=tuple(vector))


def fit(rows):
    if not rows or any(r['metadata']['partition']!='train' for r in rows):
        raise ValueError('Only new synthetic training may fit state')
    requests=[Request.from_dict(r['request']) for r in rows]
    fs=[features(r) for r in requests]
    pre,x=transform_fit([f['vector'] for f in fs])
    columns=[i+1 for i in FEATURES]+[i+25 for i in FEATURES]
    z=x[:,columns]
    distance=np.mean((z[:,None,:]-z[None,:,:])**2,axis=2)
    np.fill_diagonal(distance,np.inf)
    support={str(k):float(np.quantile(np.sort(distance,axis=1)[:,k-1],.95)) for k in (16,48,96)}
    ys={};reg={}
    for h in HORIZONS:
        y=[]
        for r,req,f in zip(rows,requests,fs):
            target=r['targets'][str(h)]
            if target['timestamp_utc']!=req.endpoint(h) or finite(target['value'])<0:raise ValueError('Invalid training target')
            y.append((target['value']-f['current'])/f['model_scale'])
        ys[str(h)]=y;reg[str(h)]=ridge(x,y,10.)
    return dict(version=VERSION,preprocessor=pre,columns=columns,neighbors=z.tolist(),
        deltas=ys,direct=reg,support=support,training_ids=[r.case_id for r in requests],
        train_requests_sha256=digest([r.as_dict() for r in requests]),training_n=len(rows))


def quantile(values,q):
    if not 0<=q<=1 or not len(values) or not np.isfinite(values).all():raise ValueError('Finite empirical distribution required')
    # Inverse empirical CDF; preserves zero mass, no fabricated continuous median.
    ordered=np.sort(values)
    return float(ordered[max(0,int(np.ceil(q*len(ordered)))-1)])


class Predictor:
    def __init__(self,state):
        if state['version']!=VERSION:raise ValueError('Wrong model version')
        self.state=state;self.z=np.asarray(state['neighbors']);self.y={h:np.array(v) for h,v in state['deltas'].items()}
        self.cache={}

    def context(self,request):
        if not isinstance(request,Request):raise ValueError('Typed past-only Request required')
        if request.identity not in self.cache:
            f=features(request);x=transform(self.state['preprocessor'],[f['vector']])
            d=np.mean((self.z-x[0,self.state['columns']])**2,axis=1)
            order=np.argsort(d,kind='stable')
            self.cache[request.identity]=(f,x,d,order)
        return self.cache[request.identity]

    def predict(self,request,horizon,method='adaptive_persistence',config=None):
        if type(horizon) is not int or horizon not in HORIZONS or method not in METHODS[:-1]:raise ValueError('Unregistered forecast')
        config=CONFIGS[0] if config is None else config
        if config not in CONFIGS:raise ValueError('Unregistered adaptive configuration')
        f,x,d,order=self.context(request);k=config['k'];values=self.y[str(horizon)][order[:k]]
        p=[float(np.mean(values==0)),float(np.mean(values>0)),float(np.mean(values<0))]
        median=quantile(values,.5);direction=0 if median==0 else 1 if median>0 else 2
        expected_benefit=float(np.mean(abs(values))-np.mean(abs(values-median)))
        in_support=bool(d[order[k-1]]<=self.state['support'][str(k)])
        reason='BASELINE';delta=0.
        if method in ('persistence','rolling_mean','anchored_trend'):
            delta=baseline(request,method,horizon)-f['current']
        elif method=='direct_delta':delta=float((x@np.array(self.state['direct'][str(horizon)]))[0])*f['model_scale']
        elif method=='local_median':delta=median*f['model_scale'];reason='UNGATED_ABLATION'
        else:
            reason=('PROTECTED_PERSISTENCE' if config['shrink']==0 else 'NOVEL_HISTORY' if not in_support
                    else 'WEAK_DIRECTION' if direction==0 or p[direction]<config['confidence']
                    else 'INSUFFICIENT_LOCAL_BENEFIT' if expected_benefit<.01 else 'ADJUST')
            if reason=='ADJUST':
                reliability=1/(1+f['vector'][20]*180/30)
                delta=config['shrink']*reliability*median*f['model_scale']
        raw=finite(f['current']+delta)
        return dict(case_id=request.case_id,request_id=request.identity,horizon=horizon,timestamp_utc=request.endpoint(horizon),
            point=max(0.,raw),raw_stock=raw,raw_delta=delta,direction_probabilities=p,
            signed_median=median,upward_median=quantile(values[values>0],.5) if (values>0).any() else None,
            downward_median=quantile(values[values<0],.5) if (values<0).any() else None,
            neighborhood_distance=float(d[order[k-1]]),in_support=in_support,reason=reason,
            expected_local_mae_reduction=expected_benefit)
