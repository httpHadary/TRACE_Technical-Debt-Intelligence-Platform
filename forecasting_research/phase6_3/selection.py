"""Validation-only safety constrained selection; primary AP never replaced by champion."""
from collections import defaultdict
import statistics as st
from forecasting_research.phase6_0.contracts import digest
from .models import METHODS,configs,predict,features
from . import HORIZONS,STATUS


def family_mean(records,fn):
    groups=defaultdict(list)
    for row in records: groups[row['family']].append(fn(row))
    return st.mean(st.mean(v) for v in groups.values()) if groups else None


def records(requests,targets,metadata,state,config,horizon):
    result=[]
    if set(requests)!=set(targets): raise ValueError('Exact matching label/request population required')
    for cid,request in requests.items():
        forecast=predict(request,state,config,horizon);f=features(request)
        target=targets[cid][str(horizon)]
        if target['timestamp_utc']!=request.endpoint(horizon): raise ValueError('Wrong target timestamp')
        result.append(dict(case_id=cid,request_id=request.identity,family=metadata[cid]['family'],
                           current=f['current'],model_scale=f['model_scale'],metric_scale=f['metric_scale'],
                           actual=target['value'],prediction=forecast['point']))
    return result


def risk(rows):
    score=family_mean(rows,lambda r:abs(r['prediction']-r['actual'])/r['model_scale'])
    unchanged=[r for r in rows if r['actual']==r['current']]
    down=[r for r in rows if r['actual']-r['current']<=-max(10,.2*r['current'])]
    unchanged_error=family_mean(unchanged,lambda r:abs(r['prediction']-r['actual'])/r['model_scale'])
    down_error=family_mean(down,lambda r:abs(r['prediction']-r['actual'])/r['model_scale'])
    down_base=family_mean(down,lambda r:abs(r['current']-r['actual'])/r['model_scale'])
    raw_down=st.mean(abs(r['prediction']-r['actual']) for r in down) if down else None
    raw_base=st.mean(abs(r['current']-r['actual']) for r in down) if down else None
    enough=len(unchanged)>=8 and len(down)>=8
    safe=enough and unchanged_error<=.02 and down_error<=1.05*down_base and raw_down<=1.05*raw_base
    return dict(normalized_family_error=score,raw_mae=st.mean(abs(r['prediction']-r['actual']) for r in rows),
                unchanged_n=len(unchanged),large_decrease_n=len(down),unchanged_normalized_error=unchanged_error,
                large_decrease_normalized_error=down_error,large_decrease_normalized_base=down_base,
                raw_large_decrease_mae=raw_down,raw_large_decrease_base=raw_base,
                safety_eligible=bool(safe),safety_sample_adequate=enough)


def choose(candidates):
    eligible=[r for r in candidates if r['risk']['safety_eligible']]
    available=eligible or candidates
    minimum=min(r['risk']['normalized_family_error'] for r in available)
    chosen=next(r for r in available if r['risk']['normalized_family_error']<=minimum*1.01)
    return dict(chosen,any_safe=bool(eligible))


def select(state,requests,targets,metadata,partition='validation'):
    if partition!='validation': raise ValueError('Validation-only model selection')
    all_scores=[];heads={}
    for h in HORIZONS:
        selections={}
        for method in METHODS[:-1]:
            scores=[]
            for c in configs(method):
                scores.append(dict(config=c,risk=risk(records(requests,targets,metadata,state,c,h))))
            choice=choose(scores)
            selections[method]=choice
            all_scores += [dict(horizon=h,method=method,**r) for r in scores]
        eligible=[(method,r) for method,r in selections.items() if r['any_safe']]
        if eligible:
            minimum=min(r['risk']['normalized_family_error'] for _,r in eligible)
            champion=next(method for method,r in eligible if r['risk']['normalized_family_error']<=minimum*1.01)
        else: champion='persistence'  # Explicit lack-of-safety-evidence fallback.
        heads[str(h)]=dict(configs={m:r['config'] for m,r in selections.items()},
                           champion_comparison_only=champion,primary_candidate='adaptive_persistence',
                           method_safety={m:r['any_safe'] for m,r in selections.items()},risks={m:r['risk'] for m,r in selections.items()})
        heads[str(h)]['configs']['comparison_champion']=heads[str(h)]['configs'][champion]
    return dict(status=STATUS,horizons=heads,search_scores=all_scores,state_sha256=digest(state),
                training_partition='train',selection_partition='validation',test_accessed=False,frozen=True,
                primary_rule='Adaptive Persistence remains primary regardless of comparison champion')
