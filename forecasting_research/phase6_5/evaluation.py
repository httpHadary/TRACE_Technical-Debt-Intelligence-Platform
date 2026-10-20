"""Paired, equal-family scoring; no future access in predictors."""
import math
import random
import statistics as st
from collections import defaultdict


def mean(xs):return st.mean(xs) if xs else None

def aggregate(rows):
    if not rows:raise ValueError('Empty comparison')
    if len({r['case_id'] for r in rows})!=len(rows):raise ValueError('Duplicate case identity')
    if any(not all(math.isfinite(r[k]) for k in ('point','actual','current','scale')) or r['scale']<=0 for r in rows):
        raise ValueError('Nonfinite comparison')
    errors=[r['point']-r['actual'] for r in rows];base=[abs(r['current']-r['actual']) for r in rows]
    by_family=defaultdict(list);bf=defaultdict(list)
    for r in rows:
        by_family[r['family']].append(abs(r['point']-r['actual'])/r['scale'])
        bf[r['family']].append(abs(r['current']-r['actual'])/r['scale'])
    norm=mean([mean(v) for v in by_family.values()]);bn=mean([mean(v) for v in bf.values()]);mae=mean([abs(v) for v in errors]);b=mean(base)
    return dict(n=len(rows),families=len(by_family),mae=mae,persistence_mae=b,raw_skill=None if b==0 else 1-mae/b,
                rmse=math.sqrt(mean([e*e for e in errors])),bias=mean(errors),median_absolute_error=st.median(map(abs,errors)),
                normalized_mae=norm,normalized_skill=None if bn==0 else 1-norm/bn,
                unfloored_normalized_mae=mean([abs(r['point']-r['actual'])/r['current'] for r in rows if r['current']>0]),
                zero_denominators=sum(r['current']==0 for r in rows),
                false_movements=sum(r['point']!=r['current'] and r['actual']==r['current'] for r in rows),
                missed_changes=sum(r['point']==r['current'] and r['actual']!=r['current'] for r in rows))

def summaries(rows):
    groups={'all':rows,'changed':[r for r in rows if r['actual']!=r['current']],
            'unchanged':[r for r in rows if r['actual']==r['current']],
            'large_up':[r for r in rows if r['actual']-r['current']>=max(1.,.1*r['current'])],
            'large_down':[r for r in rows if r['actual']-r['current']<=-max(1.,.1*r['current'])],
            'excluding_extreme':[r for r in rows if not r['extreme_scale']]}
    return {k:aggregate(v) if v else None for k,v in groups.items()}

def interval_metrics(rows):
    for r in rows:
        if not all(math.isfinite(r[k]) for k in ('lo','hi','actual')) or not 0<=r['lo']<=r['hi']:
            raise ValueError('Invalid interval; never sort')
    if not rows:return None
    return dict(n=len(rows),coverage=mean([r['lo']<=r['actual']<=r['hi'] for r in rows]),
                mean_width=mean([r['hi']-r['lo'] for r in rows]),
                normalized_mean_width=mean([(r['hi']-r['lo'])/r['scale'] for r in rows]),
                interval_score=mean([r['hi']-r['lo']+10*max(0,r['lo']-r['actual'])+10*max(0,r['actual']-r['hi']) for r in rows]),
                collapsed=sum(r['lo']==r['hi'] for r in rows))

def paired_family_interval(rows,seed=658):
    # Case siblings/paired shifted futures are not independently resampled.
    groups=defaultdict(list)
    for r in rows:groups[r['family']].append((abs(r['point']-r['actual'])-abs(r['current']-r['actual']))/r['scale'])
    means=[mean(v) for v in groups.values()]
    if len(means)<4:return dict(status='UNAVAILABLE',families=len(means))
    rng=random.Random(seed);draws=sorted(mean(rng.choices(means,k=len(means))) for _ in range(500))
    return dict(status='EXPLORATORY_SYNTHETIC_FAMILY_BOOTSTRAP',families=len(means),draws=500,
                normalized_error_difference=mean(means),lower=draws[12],upper=draws[487])
