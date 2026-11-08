"""Matched synthetic scoring, family-cluster diagnostics, no model selection."""
from collections import defaultdict
from itertools import combinations
import math
import random
import statistics as st
import numpy as np
from forecasting_research.phase6_0.contracts import finite, digest


def mean(values):
    values = list(values)
    return st.mean(values) if values else None


def group_mean(rows, fn):
    groups = defaultdict(list)
    for row in rows:
        groups[row['family']].append(row)
    return mean(fn(group) for group in groups.values())


def forecast_metrics(rows):
    if not rows:
        return dict(n=0, families=0, mae=None, synthetic_case_macro_mae=None,
                    equal_family_macro_mae=None, rmse=None, median_absolute_error=None,
                    bias=None, persistence_skill=None, normalized_mae=None,
                    normalized_persistence_skill=None, zero_denominators=0,
                    false_movement_count=0, missed_movement_count=0)
    errors = [r['prediction']-r['actual'] for r in rows]
    base = mean(abs(r['current']-r['actual']) for r in rows)
    mae = mean(abs(e) for e in errors)
    scaled = [r for r in rows if r['metric_scale'] > 0]
    ne = group_mean(scaled, lambda group: mean(abs(r['prediction']-r['actual'])/r['metric_scale'] for r in group))
    nb = group_mean(scaled, lambda group: mean(abs(r['current']-r['actual'])/r['metric_scale'] for r in group))
    return dict(n=len(rows), families=len({r['family'] for r in rows}), mae=mae,
                synthetic_case_macro_mae=mae,  # Exactly one origin per synthetic case.
                equal_family_macro_mae=group_mean(rows, lambda g: mean(abs(r['prediction']-r['actual']) for r in g)),
                rmse=math.sqrt(mean(e*e for e in errors)), median_absolute_error=st.median(abs(e) for e in errors),
                bias=mean(errors), persistence_skill=1-mae/base if base else None,
                normalized_mae=ne, normalized_persistence_skill=1-ne/nb if nb else None,
                zero_denominators=len(rows)-len(scaled),
                false_movement_count=sum(r['actual']==r['current'] and r['prediction']!=r['current'] for r in rows),
                missed_movement_count=sum(r['actual']!=r['current'] and r['prediction']==r['current'] for r in rows))


def classification_metrics(rows, threshold):
    if not 0 <= finite(threshold) <= 1:
        raise ValueError('Registered validation-selected threshold required')
    y = [int(r['actual'] != r['current']) for r in rows]
    p = [finite(r['probability']) for r in rows]
    if not y or any(not 0 <= v <= 1 for v in p):
        raise ValueError('Nonempty probabilities in [0,1] required')
    z = [int(v >= threshold) for v in p]
    tp = sum(a==b==1 for a, b in zip(y, z))
    fp = sum(a==0 and b==1 for a, b in zip(y, z))
    fn = sum(a==1 and b==0 for a, b in zip(y, z))
    tn = len(y)-tp-fp-fn
    pos, neg = sum(y), len(y)-sum(y)
    roc = mean((a>b)+.5*(a==b) for a, ya in zip(p,y) if ya for b, yb in zip(p,y) if not yb) if pos and neg else None
    # Stepwise area under precision-recall = average precision; ties grouped.
    ap, count_tp, count_all = 0., 0, 0
    if pos:
        for prob in sorted(set(p), reverse=True):
            group = [v for v, pv in zip(y,p) if pv == prob]
            count_tp += sum(group)
            count_all += len(group)
            ap += sum(group)/pos*count_tp/count_all
    bins = []
    for i in range(5):
        indices = [j for j, v in enumerate(p) if i/5 <= v < (i+1)/5 or i==4 and v==1]
        bins.append(dict(lower=i/5, upper=(i+1)/5, n=len(indices),
                         mean_probability=mean(p[j] for j in indices), prevalence=mean(y[j] for j in indices)))
    return dict(n=len(y), positive_prevalence=pos/len(y), threshold=threshold,
                precision=tp/(tp+fp) if tp+fp else None, recall=tp/pos if pos else None,
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
                pr_auc_average_precision=ap if pos and neg else None,
                roc_auc=roc, undefined_reason='SINGLE_CLASS' if not pos or not neg else None,
                brier_score=mean((v-a)**2 for a,v in zip(y,p)),
                true_positive=tp, false_positive=fp, false_negative=fn, true_negative=tn,
                calibration=bins)


def interval_metrics(rows, kind):
    values = [r for r in rows if r.get(kind) is not None]
    if not values:
        return dict(n=0, coverage80=None, width80=None, interval_score80=None,
                    pinball10=None, pinball50=None, pinball90=None, collapsed=0, invalid=0)
    invalid = sum(not r[kind][0] <= r[kind][1] <= r[kind][2] for r in values)
    if invalid:
        raise ValueError('Invalid derived quantile order; no sorting repair')
    def loss(q, actual, predicted):
        d = actual-predicted
        return max(q*d, (q-1)*d)
    return dict(n=len(values), coverage80=mean(r[kind][0] <= r['actual'] <= r[kind][2] for r in values),
                width80=mean(r[kind][2]-r[kind][0] for r in values),
                interval_score80=mean(r[kind][2]-r[kind][0]+10*max(0,r[kind][0]-r['actual'])+10*max(0,r['actual']-r[kind][2]) for r in values),
                pinball10=mean(loss(.1,r['actual'],r[kind][0]) for r in values),
                pinball50=mean(loss(.5,r['actual'],r[kind][1]) for r in values),
                pinball90=mean(loss(.9,r['actual'],r[kind][2]) for r in values),
                collapsed=sum(r[kind][0]==r[kind][2] for r in values), invalid=0)


def paired(rows, left, right, horizon, partition):
    a = {r['case_id']:r for r in rows if r['method']==left and r['horizon']==horizon and r['partition']==partition}
    b = {r['case_id']:r for r in rows if r['method']==right and r['horizon']==horizon and r['partition']==partition}
    if set(a) != set(b):
        raise ValueError('Paired comparisons require identical attempted IDs')
    groups = defaultdict(list)
    normalized = defaultdict(list)
    for cid, r in a.items():
        if r['actual'] != b[cid]['actual'] or r['request_id'] != b[cid]['request_id']:
            raise ValueError('Paired target/request mismatch')
        d = abs(b[cid]['prediction']-r['actual'])-abs(r['prediction']-r['actual'])
        groups[r['family']].append(d)
        if r['metric_scale']:
            normalized[r['family']].append(d/r['metric_scale'])
    keys = sorted(groups)
    rng = random.Random(620)
    means = {g:mean(v) for g,v in groups.items()}
    draws = sorted(mean(means[rng.choice(keys)] for _ in keys) for _ in range(500))
    ci = [float(v) for v in np.quantile(draws, [.025,.975])]
    return dict(left=left, right=right, horizon=horizon, partition=partition, n=len(a), family_clusters=len(keys),
                case_ids_sha256=digest(sorted(a)),
                mean_error_difference_right_minus_left=mean(d for group in groups.values() for d in group),
                equal_family_difference=mean(means.values()), normalized_family_difference=mean(mean(v) for v in normalized.values()),
                family_bootstrap_ci95=ci, replicates=500, seed=620,
                limitation='Synthetic mechanism families, not independent real software repositories')


def summarize(rows, classification):
    aggregates, scenarios, intervals, pairs = [], [], [], []
    methods = list(dict.fromkeys(r['method'] for r in rows))
    for partition in ('test','ood'):
        for h in (30,60,90):
            for method in methods:
                selected = [r for r in rows if r['partition']==partition and r['horizon']==h and r['method']==method]
                for scale in ('all','excluding_mixed_scale'):
                    rs = [r for r in selected if scale=='all' or r['family']!='mixed_scale']
                    for stratum in ('all','unchanged','changed','large_increase','large_decrease'):
                        def admitted(r):
                            delta = r['actual']-r['current']
                            large = max(10,.2*r['current'])
                            return (stratum=='all' or stratum=='unchanged' and delta==0
                                    or stratum=='changed' and delta!=0 or stratum=='large_increase' and delta>=large
                                    or stratum=='large_decrease' and delta<=-large)
                        subset = [r for r in rs if admitted(r)]
                        aggregates.append(dict(partition=partition,horizon=h,method=method,scale=scale,stratum=stratum,**forecast_metrics(subset)))
                for family in sorted({r['family'] for r in selected}):
                    scenarios.append(dict(partition=partition,horizon=h,method=method,family=family,
                                          **forecast_metrics([r for r in selected if r['family']==family])))
                for kind in ('calibrated_quantiles','mixture_quantiles'):
                    for stratum in ('all','unchanged','changed'):
                        subset = [r for r in selected if stratum=='all' or (r['actual']==r['current'])==(stratum=='unchanged')]
                        intervals.append(dict(partition=partition,horizon=h,method=method,kind=kind,stratum=stratum,**interval_metrics(subset,kind)))
            for left,right in combinations(methods,2):
                pairs.append(paired(rows,left,right,h,partition))
    return dict(status='SYNTHETIC_ENGINEERING_TEST', aggregate=aggregates, per_family=scenarios,
                intervals=intervals, paired=pairs, classification=classification,
                attempted={p:len({r['case_id'] for r in rows if r['partition']==p}) for p in ('test','ood')},
                failures=[], failure_rate=0., aggregation='one origin per synthetic case; family macro separate; pooled case RMSE')
