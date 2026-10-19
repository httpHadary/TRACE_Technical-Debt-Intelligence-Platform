"""Synthetic truth is accessed only after complete prediction sealing."""
import csv,json,math,statistics,random
from datetime import timedelta
from collections import defaultdict
from forecasting_research.phase6_0.contracts import Request,validate_response,utc,iso,finite
from forecasting_research.phase6_0.evaluation import metrics
from forecasting_research.phase6_0.artifacts import write,sha
from .population import specs,future,history,short,population
from .study import MODELS


def denominator(request):
    values=request.values[-90:]
    return statistics.mean(abs(b-a) for a,b in zip(values,values[1:]))


def validate_crossing(request,result):
    if set(result)!={'failure','request_id','crossing_steps','invalid_raw_path'} or result['failure']!='NATIVE_QUANTILE_CROSSING' or result['request_id']!=request.identity:
        raise ValueError('Only identity-bound native crossing is recoverable')
    path=result['invalid_raw_path'];crossed=[]
    if len(path)!=90:raise ValueError('Complete rejected raw path required')
    for day,p in enumerate(path,1):
        if set(p)!={'timestamp_utc','raw_point','raw_q10','raw_q50','raw_q90'}:raise ValueError('Invalid raw path shape')
        if p['timestamp_utc']!=iso(utc(request.origin_utc)+timedelta(days=day)):
            raise ValueError('Invalid path time')
        q=[finite(p[k]) for k in ('raw_q10','raw_q50','raw_q90')]
        if finite(p['raw_point'])!=q[1]:raise ValueError('Invalid native median')
        if not q[0]<=q[1]<=q[2]:crossed.append(day)
    if not crossed or crossed!=result['crossing_steps']:raise ValueError('Crossing evidence mismatch')


def endpoint_rows(reg,requests,predictions):
    ids={r['case_id'] for r in reg['population'] if r['eligible']}
    if set(predictions)!=set(MODELS) or any(set(predictions[m])!=ids for m in MODELS):
        raise ValueError('Complete attempted model/case population required')
    spec_by_id={s.case_id:s for s in specs()};rows=[]
    for cid in sorted(ids):
        a,b=(Request.from_dict(requests[cid][k]) for k in ('90','512'))
        if a!=short(b):raise ValueError('Common origin and suffix mismatch')
        targets=future(spec_by_id[cid]);d=denominator(a)
        for model in MODELS:
            request=b if model=='chronos512' else a;result=predictions[model][cid]
            failed=bool(result.get('failure'))
            if failed:validate_crossing(request,result)
            else:validate_response(request,result,model)
            for h in (30,60,90):
                p=None if failed else result['path'][h-1]
                rows.append(dict(case_id=cid,scenario=spec_by_id[cid].scenario,model=model,horizon_days=h,
                      origin_utc=a.origin_utc,endpoint_utc=a.endpoint(h),status='NATIVE_FAILURE' if failed else 'SUCCESS',
                      failure=result['failure'] if failed else None,unit=a.unit,experiment_status=a.status,
                      current=a.values[-1],actual=targets[h]['value'],scale_denominator=d,
                      prediction=p['point'] if p else None,raw_prediction=p['raw_point'] if p else None,
                      q10=p['q10'] if p else None,q90=p['q90'] if p else None,
                      raw_q10=p['raw_q10'] if p else None,raw_q90=p['raw_q90'] if p else None))
    return rows


def augmented(rows):
    if not rows:return None
    translated=[dict(repository_id=r['case_id'],current=r['current'],actual=r['actual'],prediction=r['prediction'],q10=r['q10'],q90=r['q90']) for r in rows]
    result=metrics(translated)
    normalized=[abs(r['prediction']-r['actual'])/r['scale_denominator'] for r in rows if r['scale_denominator']>0]
    result.update(scale_normalized_mae=statistics.mean(normalized) if normalized else None,
                  normalization_defined=len(normalized),normalization_undefined=len(rows)-len(normalized),
                  raw_collapsed_intervals=sum(r['raw_q10'] is not None and r['raw_q10']==r['raw_q90'] for r in rows),
                  clipped_points=sum(r['prediction']!=r['raw_prediction'] for r in rows))
    return result


def tables(rows,ids):
    result={}
    for model in MODELS:
        successful=[r for r in rows if r['model']==model and r['case_id'] in ids and r['status']=='SUCCESS']
        result[model]={}
        for h in (30,60,90):
            at=[r for r in successful if r['horizon_days']==h]
            result[model][str(h)]={
                'all':augmented(at),'unchanged':augmented([r for r in at if r['actual']==r['current']]),
                'changing':augmented([r for r in at if r['actual']!=r['current']]),
                'scenarios':{s:augmented([r for r in at if r['scenario']==s]) for s in sorted({r['scenario'] for r in at})}}
    return result


def summarize(rows,reg):
    if reg['population']!=population() or reg['models']!=list(MODELS):raise ValueError('Registered synthetic population required')
    ids={r['case_id'] for r in reg['population'] if r['eligible']}
    expected={(c,m,h) for c in ids for m in MODELS for h in (30,60,90)}
    if len(rows)!=len(expected) or {(r['case_id'],r['model'],r['horizon_days']) for r in rows}!=expected:
        raise ValueError('Missing/duplicate/unregistered endpoint identity')
    lookup={(r['case_id'],r['model'],r['horizon_days']):r for r in rows}
    expected_by_id={s.case_id:(short(history(s)),future(s)) for s in specs() if s.case_id in ids}
    for r in rows:
        request,targets=expected_by_id[r['case_id']];h=r['horizon_days']
        if (r['origin_utc']!=request.origin_utc or r['endpoint_utc']!=request.endpoint(h) or r['actual']!=targets[h]['value']
                or r['current']!=request.values[-1] or r['scale_denominator']!=denominator(request)
                or r['unit']!=request.unit or r['experiment_status']!=request.status):
            raise ValueError('Generated truth/unit/paired denominator mismatch')
        if r['status']=='NATIVE_FAILURE':
            if r['model'] not in ('chronos90','chronos512') or r['failure']!='NATIVE_QUANTILE_CROSSING' or any(r[k] is not None for k in ('prediction','raw_prediction','q10','q90','raw_q10','raw_q90')):
                raise ValueError('Failure cannot contain fallback or fabricated interval')
        elif r['status']!='SUCCESS' or r['failure'] is not None or finite(r['prediction'])!=max(0,finite(r['raw_prediction'])):
            raise ValueError('Invalid prediction status or stock policy')
        elif r['model'].startswith('chronos'):
            if not finite(r['raw_q10'])<=r['raw_prediction']<=finite(r['raw_q90']) or r['q10']!=max(0,r['raw_q10']) or r['q90']!=max(0,r['raw_q90']):
                raise ValueError('Native interval ordering/clipping invalid')
    for cid in ids:
        for h in (30,60,90):
            for key in ('actual','current','origin_utc','endpoint_utc','scale_denominator'):
                if len({lookup[cid,m,h][key] for m in MODELS})!=1:raise ValueError('Mismatched paired inputs/targets')
    success={m:{cid for cid in ids if all(lookup[cid,m,h]['status']=='SUCCESS' for h in (30,60,90))} for m in MODELS}
    matched=set.intersection(*success.values());paired=success['chronos90']&success['chronos512']
    paired_stats={}
    for h in (30,60,90):
        values={cid:abs(lookup[cid,'chronos512',h]['prediction']-lookup[cid,'chronos512',h]['actual'])-
                    abs(lookup[cid,'chronos90',h]['prediction']-lookup[cid,'chronos90',h]['actual']) for cid in sorted(paired)}
        rng=random.Random(42);keys=list(values);draws=sorted(statistics.mean(values[rng.choice(keys)] for _ in keys) for _ in range(500)) if keys else []
        normalized=[values[cid]/lookup[cid,'chronos90',h]['scale_denominator'] for cid in keys if lookup[cid,'chronos90',h]['scale_denominator']>0]
        paired_stats[str(h)]=dict(n=len(values),mean_absolute_error_512_minus_90=statistics.mean(values.values()) if values else None,
             paired_case_bootstrap_ci95=[draws[12],draws[487]] if draws else None,
             scale_normalized_difference=statistics.mean(normalized) if normalized else None,
             normalization_defined=len(normalized),normalization_undefined=len(values)-len(normalized),
             scenarios={s:statistics.mean(v for cid,v in values.items() if lookup[cid,'chronos90',h]['scenario']==s)
                        for s in sorted({lookup[cid,'chronos90',h]['scenario'] for cid in values})})
    return dict(status='SYNTHETIC_ENGINEERING_TEST',registered_cases=len(reg['population']),eligible_cases=len(ids),
         excluded_cases=len(reg['population'])-len(ids),attempted_contexts={m:len(ids) for m in MODELS},
         successful_contexts={m:len(v) for m,v in success.items()},failure_rate={m:(len(ids)-len(v))/len(ids) for m,v in success.items()},
         failed_ids={m:sorted(ids-v) for m,v in success.items()},all_method_matched_ids=sorted(matched),native_pair_ids=sorted(paired),
         all_method_matched=tables(rows,matched),native_available_conditional=tables(rows,ids),paired=paired_stats,
         full_assigned_native_mae='Unavailable for any method with failures; conditional tables identify exact retained IDs',
         uncertainty='Synthetic case bootstrap only; not independent real repository evidence')


def evaluate(study,reg,requests):
    sealed=json.loads((study/'prediction_seal.json').read_text())
    if sha(study/'predictions.json')!=sealed['sha256'] or sealed['labels_scored'] is not False:
        raise ValueError('Prediction seal must precede numerical truth access')
    if sealed.get('registration_sha256')!=sha(study/'registration.json'):
        raise ValueError('Predictions must bind to exact frozen registration')
    predictions=json.loads((study/'predictions.json').read_text());rows=endpoint_rows(reg,requests,predictions)
    with (study/'endpoints.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result=summarize(rows,reg);write(study/'metrics.json',result)
    write(study/'synthetic_targets.json',{s.case_id:future(s) for s in specs()})
    if sha(study/'predictions.json')!=sealed['sha256']:raise ValueError('Sealed predictions changed')
    return result


def read_endpoints(path):
    with path.open() as f:rows=list(csv.DictReader(f))
    numeric=('current','actual','scale_denominator','prediction','raw_prediction','q10','q90','raw_q10','raw_q90')
    for r in rows:
        r['horizon_days']=int(r['horizon_days'])
        for k in numeric:r[k]=None if r[k]=='' else finite(float(r[k]))
        r['failure']=r['failure'] or None
    return rows
