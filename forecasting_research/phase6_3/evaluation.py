"""Same-case synthetic forecasting, direction and interval diagnostics; no tuning."""
from itertools import combinations
import statistics as st
import numpy as np
from forecasting_research.phase6_2.evaluation import forecast_metrics,classification_metrics,interval_metrics,paired
from .models import METHODS
from .selection import family_mean


def direction_metrics(rows):
    labels=[0 if r['actual']==r['current'] else 1 if r['actual']>r['current'] else 2 for r in rows]
    probabilities=[r['direction_probabilities'] for r in rows]
    if any(p is None or len(p)!=3 or not np.isfinite(p).all() or min(p)<0 or abs(sum(p)-1)>1e-9 for p in probabilities):
        raise ValueError('Valid three-way probabilities required')
    guesses=[max(range(3),key=lambda i:p[i]) for p in probabilities]
    confusion=[[sum(y==a and z==b for y,z in zip(labels,guesses)) for b in range(3)] for a in range(3)]
    per_class=[]
    for c in range(3):
        tp=confusion[c][c];fp=sum(confusion[j][c] for j in range(3) if j!=c);fn=sum(confusion[c][j] for j in range(3) if j!=c)
        binary=[dict(actual=int(y==c),current=0,probability=p[c]) for y,p in zip(labels,probabilities)]
        diagnostic=classification_metrics(binary,.5)  # Fixed OVR diagnostic, not a forecasting gate.
        per_class.append(dict(class_name=('unchanged','increase','decrease')[c],support=sum(y==c for y in labels),
                              precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,
                              f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
                              roc_auc=diagnostic['roc_auc'],pr_auc=diagnostic['pr_auc_average_precision']))
    return dict(n=len(rows),confusion=confusion,per_class=per_class,
                macro_f1=st.mean(r['f1'] for r in per_class if r['f1'] is not None),
                multiclass_brier=st.mean(sum((p[c]-int(y==c))**2 for c in range(3)) for y,p in zip(labels,probabilities)),
                probability_semantics='Normalized OVR, no post-hoc probability calibration',
                diagnostic_threshold_policy='0.5 only for auxiliary OVR AUC helper; direction decisions use argmax, AP actions use validation confidence gates')


def summarize(rows,interval_rows,selection):
    aggregate=[];per_family=[];intervals=[];paired_results=[];classifiers=[]
    for part in ('test','ood'):
        for h in (30,60,90):
            for method in METHODS:
                selected=[r for r in rows if r['partition']==part and r['horizon']==h and r['method']==method]
                for scale in ('all','excluding_mixed_scale'):
                    rs=[r for r in selected if scale=='all' or r['family']!='mixed_scale']
                    for stratum in ('all','unchanged','changed','increase','decrease','large_increase','large_decrease','return_to_origin'):
                        def keep(r):
                            d=r['actual']-r['current'];large=max(10,.2*r['current'])
                            return (stratum=='all' or stratum=='unchanged' and d==0 or stratum=='changed' and d!=0
                                    or stratum=='increase' and d>0 or stratum=='decrease' and d<0
                                    or stratum=='large_increase' and d>=large or stratum=='large_decrease' and d<=-large
                                    or stratum=='return_to_origin' and r['return_to_origin'])
                        subset=[r for r in rs if keep(r)]
                        aggregate.append(dict(partition=part,horizon=h,method=method,scale=scale,stratum=stratum,
                            model_scale_normalized_mae=family_mean(subset,lambda r:abs(r['prediction']-r['actual'])/r['model_scale']),
                            **forecast_metrics(subset)))
                for family in sorted({r['family'] for r in selected}):
                    per_family.append(dict(partition=part,horizon=h,method=method,family=family,
                                          **forecast_metrics([r for r in selected if r['family']==family])))
            for a,b in combinations(METHODS,2): paired_results.append(paired(rows,a,b,h,part))
            for method in ('binary_adaptive','adaptive_persistence'):
                selected=[r for r in rows if r['method']==method and r['partition']==part and r['horizon']==h]
                threshold=selection['horizons'][str(h)]['configs'][method]['threshold']
                diagnostic=classification_metrics([dict(r,probability=r['binary_change_probability']) for r in selected],threshold)
                y=[r['actual']!=r['current'] for r in selected];z=[r['prediction']!=r['current'] for r in selected]
                tp=sum(a and b for a,b in zip(y,z));fp=sum(not a and b for a,b in zip(y,z));fn=sum(a and not b for a,b in zip(y,z))
                classifiers.append(dict(partition=part,horizon=h,method=method,probability_threshold_diagnostic=diagnostic,
                    actual_forecast_action=dict(precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,
                                               f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,false_movements=fp,missed_changes=fn),
                    direction=direction_metrics(selected) if method=='adaptive_persistence' else None))
            for kind in sorted({r['kind'] for r in interval_rows}):
                selected=[r for r in interval_rows if r['partition']==part and r['horizon']==h and r['kind']==kind]
                for stratum in ('all','unchanged','changed','large_increase','large_decrease'):
                    def keep(r):
                        d=r['actual']-r['current'];large=max(10,.2*r['current'])
                        return (stratum=='all' or stratum=='unchanged' and d==0 or stratum=='changed' and d!=0
                                or stratum=='large_increase' and d>=large or stratum=='large_decrease' and d<=-large)
                    subset=[r for r in selected if keep(r)]
                    stat=interval_metrics(subset,'quantiles')
                    widths=[r['quantiles'][2]-r['quantiles'][0] for r in subset]
                    def score(r):
                        a,b,c=r['quantiles'];return c-a+10*max(0,a-r['actual'])+10*max(0,r['actual']-c)
                    intervals.append(dict(partition=part,horizon=h,kind=kind,stratum=stratum,**stat,
                        median_width80=st.median(widths) if widths else None,
                        normalized_width=family_mean(subset,lambda r:(r['quantiles'][2]-r['quantiles'][0])/r['model_scale']),
                        normalized_interval_score=family_mean(subset,lambda r:score(r)/r['model_scale'])))
    # Select illustrative counterexamples by largest excess error, only after scoring.
    candidates=[dict(partition=r['partition'],family=r['family'],case_id=r['case_id'],horizon=r['horizon'],
                         actual=r['actual'],current=r['current'],adaptive=r['prediction'],
                         excess_error=abs(r['prediction']-r['actual'])-abs(r['current']-r['actual']),
                         normalized_excess=(abs(r['prediction']-r['actual'])-abs(r['current']-r['actual']))/r['model_scale'])
                     for r in rows if r['method']=='adaptive_persistence' and abs(r['prediction']-r['actual'])>abs(r['current']-r['actual'])]
    # One counterexample per family, ranked by registered model-scale excess.
    ranked=sorted(candidates,key=lambda r:-r['normalized_excess'])
    seen=set();failures=[]
    for r in ranked:
        if r['family'] not in seen:
            failures.append(r);seen.add(r['family'])
        if len(failures)==12: break
    return dict(status='SYNTHETIC_ENGINEERING_TEST',aggregate=aggregate,per_family=per_family,intervals=intervals,
                paired=paired_results,classifiers=classifiers,counterexamples=failures,
                attempted={p:len({r['case_id'] for r in rows if r['partition']==p}) for p in ('test','ood')},
                failures=[],ineligible_cases=[],matched_populations=True)
