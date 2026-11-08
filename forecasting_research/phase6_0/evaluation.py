"""Label access happens only here, after sealed prediction generation."""
from collections import defaultdict
import math,statistics,random
from .contracts import finite,validate_response


def metrics(rows):
    if not rows:return None
    groups=defaultdict(list)
    for r in rows:groups[r['repository_id']].append(r)
    def mae(rs):return statistics.mean(abs(finite(r['prediction'])-finite(r['actual'])) for r in rs)
    def rmse(rs):return math.sqrt(statistics.mean((r['prediction']-r['actual'])**2 for r in rs))
    model=statistics.mean(mae(rs) for rs in groups.values())
    base=statistics.mean(statistics.mean(abs(r['current']-r['actual']) for r in rs) for rs in groups.values())
    rng=random.Random(42);keys=sorted(groups);draws=[]
    if len(keys)>=2:
        gains={k:statistics.mean(abs(r['current']-r['actual'])-abs(r['prediction']-r['actual']) for r in v) for k,v in groups.items()}
        draws=sorted(statistics.mean(gains[rng.choice(keys)] for _ in keys) for _ in range(500))
    intervals=[r for r in rows if r['q10'] is not None and r['q90'] is not None]
    igroups=defaultdict(list)
    for r in intervals:igroups[r['repository_id']].append(r)
    return dict(n=len(rows),repository_clusters=len(groups),macro_mae=model,macro_rmse=statistics.mean(rmse(rs) for rs in groups.values()),
                pooled_mae=mae(rows),pooled_rmse=rmse(rows),median_absolute_error=statistics.median(abs(r['prediction']-r['actual']) for r in rows),
                signed_bias=statistics.mean(r['prediction']-r['actual'] for r in rows),persistence_macro_mae=base,
                skill=None if base==0 else 1-model/base,
                paired_gain_ci95=[draws[int(.025*len(draws))],draws[int(.975*len(draws))]] if draws else None,
                bootstrap_scope='synthetic case clusters; not real repositories',interval_n=len(intervals),
                macro_coverage80=statistics.mean(statistics.mean(r['q10']<=r['actual']<=r['q90'] for r in rs) for rs in igroups.values()) if igroups else None,
                macro_width80=statistics.mean(statistics.mean(r['q90']-r['q10'] for r in rs) for rs in igroups.values()) if igroups else None,
                collapsed_intervals=sum(r['q10']==r['q90'] for r in intervals))


def score(cases, predictions, model):
    if len({c.request.case_id for c in cases})!=len(cases):raise ValueError('Duplicate synthetic identities')
    expected={c.request.case_id for c in cases}
    if set(predictions)!=expected:raise ValueError('Complete declared attempt population required, including failures')
    rows=[];failures=[]
    for case in cases:
        req=case.request;result=predictions[req.case_id]
        if result.get('failure'):
            if (result.get('request_id')!=req.identity or not isinstance(result['failure'],str)
                    or not result['failure'].startswith(('NATIVE_QUANTILE_CROSSING','INSUFFICIENT','MISSING_ORIGIN'))
                    or set(result)-{'failure','request_id','crossings'}):
                raise ValueError('Unregistered failure or wrong request identity')
            failures.append(dict(case_id=req.case_id,reason=result['failure']));continue
        validate_response(req,result,model)
        # Labels accessed only after validation of identity-bound sealed predictions.
        for h,actual in case.targets().items():
            p=result['path'][h-1];current=req.values[-1]
            rows.append(dict(repository_id=req.case_id,scenario=case.scenario,horizon=h,current=current,actual=actual,
                             prediction=p['point'],q10=p['q10'],q90=p['q90']))
    output={}
    for h in (30,60,90):
        for subset in ('all','unchanged','changing','large_change'):
            rs=[r for r in rows if r['horizon']==h and (subset=='all' or
                subset=='unchanged' and r['actual']==r['current'] or subset=='changing' and r['actual']!=r['current'] or
                subset=='large_change' and abs(r['actual']-r['current'])>=max(10,.2*r['current']))]
            output[str(h)+'/'+subset]=metrics(rs)
    return dict(model=model,attempted_cases=len(cases),successful_cases=len(cases)-len(failures),failures=failures,
                failure_rate=len(failures)/len(cases),metrics=output,rows=rows,
                context_diversity=dict(cases=len(cases),distinct_value_sequences=len({tuple(c.request.values) for c in cases}),
                                       distinct_request_ids=len({c.request.identity for c in cases})))
