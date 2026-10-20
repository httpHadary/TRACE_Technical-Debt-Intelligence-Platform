"""Arithmetic evaluation only; no fitting or model selection."""
import statistics as st
from collections import defaultdict
import numpy as np
from .selection import family_mean
from forecasting_research.phase6_3.evaluation import direction_metrics


def ratio_skill(model,base):return 1-model/base if base is not None and base>0 else None


def metrics(rows):
    if not rows:return dict(n=0,mae=None,raw_skill=None,normalized_skill=None)
    error=[abs(r['point']-r['actual']) for r in rows]
    base=[abs(r['current']-r['actual']) for r in rows]
    norm=family_mean(rows,lambda r:abs(r['point']-r['actual'])/r['model_scale'])
    normbase=family_mean(rows,lambda r:abs(r['current']-r['actual'])/r['model_scale'])
    positive=[r for r in rows if r['metric_scale']>0]
    uf=family_mean(positive,lambda r:abs(r['point']-r['actual'])/r['metric_scale'])
    ub=family_mean(positive,lambda r:abs(r['current']-r['actual'])/r['metric_scale'])
    return dict(n=len(rows),families=len({r['family'] for r in rows}),mae=st.mean(error),persistence_mae=st.mean(base),
        raw_skill=ratio_skill(st.mean(error),st.mean(base)),rmse=float(np.sqrt(np.mean(np.square(error)))),
        median_absolute_error=st.median(error),bias=st.mean(r['point']-r['actual'] for r in rows),
        family_mae=family_mean(rows,lambda r:abs(r['point']-r['actual'])),normalized_mae=norm,
        normalized_skill=ratio_skill(norm,normbase),unfloored_normalized_skill=ratio_skill(uf,ub),
        zero_denominator_count=len(rows)-len(positive),
        false_changes=sum(r['point']!=r['current'] and r['actual']==r['current'] for r in rows),
        missed_changes=sum(r['point']==r['current'] and r['actual']!=r['current'] for r in rows))


def subset(rows,name):
    def keep(r):
        d=r['actual']-r['current'];large=max(10,.2*r['current'])
        return (name=='all' or name=='unchanged' and d==0 or name=='changed' and d!=0
                or name=='large_increase' and d>=large or name=='large_decrease' and d<=-large
                or name=='excluding_extreme_scale' and r['scale_band']!=3)
    return [r for r in rows if keep(r)]


def interval_metrics(rows,field):
    if not rows:return dict(n=0)
    qs=[r[field] for r in rows]
    if any(len(q)!=2 or not np.isfinite(q).all() or q[0]<0 or q[0]>q[1] for q in qs):raise ValueError('Invalid interval; no sorting repair')
    scores=[q[1]-q[0]+10*max(0,q[0]-r['actual'])+10*max(0,r['actual']-q[1]) for r,q in zip(rows,qs)]
    return dict(n=len(rows),coverage=st.mean(q[0]<=r['actual']<=q[1] for r,q in zip(rows,qs)),
        mean_width=st.mean(q[1]-q[0] for q in qs),median_width=st.median(q[1]-q[0] for q in qs),
        mean_normalized_width=st.mean((q[1]-q[0])/r['model_scale'] for r,q in zip(rows,qs)),
        interval_score=st.mean(scores),normalized_interval_score=st.mean(s/r['model_scale'] for s,r in zip(scores,rows)),
        collapsed=sum(q[0]==q[1] for q in qs),invalid=0)


def summarize(rows):
    groups=defaultdict(list)
    for r in rows:groups[(r['replica'],r['partition'],r['horizon'],r['method'])].append(r)
    aggregate=[];families=[];classifiers=[];intervals=[];paired=[]
    for (rep,part,h,method),rs in sorted(groups.items()):
        key=dict(replica=rep,partition=part,horizon=h,method=method)
        for name in ('all','unchanged','changed','large_increase','large_decrease','excluding_extreme_scale'):
            subset_rows=subset(rs,name)
            aggregate.append(dict(key,stratum=name,**metrics(subset_rows)))
            if method=='adaptive_persistence':
                for field in ('calibrated_interval','local_interval'):
                    intervals.append(dict(key,stratum=name,kind=field,**interval_metrics(subset_rows,field)))
        for fam in sorted({r['family'] for r in rs}):families.append(dict(key,family=fam,**metrics([r for r in rs if r['family']==fam])))
        if method=='adaptive_persistence':
            diagnostic=direction_metrics(rs)
            diagnostic['probability_semantics']='Empirical local-neighbor direction proportions; not certified calibrated probabilities'
            y=[r['actual']!=r['current'] for r in rs];a=[r['point']!=r['current'] for r in rs]
            tp=sum(x and z for x,z in zip(y,a));fp=sum(not x and z for x,z in zip(y,a));fn=sum(x and not z for x,z in zip(y,a))
            classifiers.append(dict(key,direction=diagnostic,action=dict(precision=tp/(tp+fp) if tp+fp else None,
                recall=tp/(tp+fn) if tp+fn else None,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)))
            # Paired whole-family bootstrap; synthetic family dependence retained.
            diffs=[family_mean([r for r in rs if r['family']==fam],lambda r:(abs(r['point']-r['actual'])-abs(r['current']-r['actual']))/r['model_scale']) for fam in sorted({r['family'] for r in rs})]
            rng=np.random.default_rng(640)
            draws=np.mean(rng.choice(diffs,(500,len(diffs)),replace=True),axis=1)
            paired.append(dict(key,family_count=len(diffs),normalized_paired_difference=st.mean(diffs),
                exploratory_family_bootstrap95=np.quantile(draws,[.025,.975]).tolist()))
    return dict(scope='SYNTHETIC_ENGINEERING_TEST',aggregate=aggregate,per_family=families,
                classifiers=classifiers,intervals=intervals,paired=paired,total_forecasts=len(rows))
