"""Evaluator-only future truth; identical-population pairs and scale diagnostics."""
from pathlib import Path
from itertools import combinations
import csv
import json
import math
import statistics as st
from forecasting_research.phase6_0.artifacts import write, sha
from forecasting_research.phase6_0.contracts import Request, validate_response, finite
from .population import specs, history, future, population
from .study import MODELS, CANDIDATES


def denominator(request):
    # Level normalization avoids the plateau MASE=0 problem; genuine all-zero
    # histories remain undefined instead of using an arbitrary epsilon.
    return st.mean(abs(v) for v in request.values)


def score(rows):
    if not rows:
        return dict(n=0, mae=None, rmse=None, median_absolute_error=None, bias=None,
                    equal_scenario_macro_mae=None, normalized_mae=None, zero_denominators=0,
                    persistence_skill=None, intervals_available=0, coverage=None, interval_width=None,
                    collapsed_intervals=None, raw_mae=None, clipped_points=0)
    errors = [r['prediction'] - r['actual'] for r in rows]
    mae = st.mean(abs(e) for e in errors)
    scenarios = sorted({r['scenario'] for r in rows})
    macro = st.mean(st.mean(abs(r['prediction']-r['actual']) for r in rows if r['scenario']==s) for s in scenarios)
    pm = st.mean(abs(r['current']-r['actual']) for r in rows)
    normalized = [abs(r['prediction']-r['actual']) / r['denominator'] for r in rows if r['denominator'] > 0]
    intervals = [r for r in rows if r['q10'] is not None]
    return dict(n=len(rows), mae=mae, rmse=math.sqrt(st.mean(e*e for e in errors)),
        median_absolute_error=st.median(abs(e) for e in errors), bias=st.mean(errors),
        equal_scenario_macro_mae=macro, normalized_mae=st.mean(normalized) if normalized else None,
        zero_denominators=sum(r['denominator']==0 for r in rows), persistence_skill=1-mae/pm if pm else None,
        raw_mae=st.mean(abs(r['raw_point']-r['actual']) for r in rows),
        clipped_points=sum(r['raw_point']<0 for r in rows), intervals_available=len(intervals),
        coverage=st.mean(r['q10']<=r['actual']<=r['q90'] for r in intervals) if intervals else None,
        interval_width=st.mean(r['q90']-r['q10'] for r in intervals) if intervals else None,
        collapsed_intervals=sum(r['q10']==r['q90'] for r in intervals) if intervals else None)


def validate_rows(rows, reg):
    allowed = {s.case_id: s for s in specs() if history(s).complete_daily(512)}
    seen = set()
    for r in rows:
        key = (r['model'], r['case_id'], r['horizon'])
        if key in seen or r['model'] not in MODELS or r['case_id'] not in allowed or r['horizon'] not in (30,60,90):
            raise ValueError('Duplicate/unregistered forecast identity')
        seen.add(key)
        spec = allowed[r['case_id']]
        req = history(spec)
        truth = future(spec)[r['horizon']]
        if (r['scenario'] != spec.scenario or r['actual'] != truth['value'] or r['timestamp_utc'] != truth['timestamp_utc']
                or r['current'] != req.values[-1] or r['denominator'] != denominator(req) or r['request_id'] != req.identity):
            raise ValueError('Synthetic truth/denominator/input identity mismatch')
        for name in ('prediction', 'raw_point', 'actual', 'current', 'denominator'):
            finite(r[name])
        if r['prediction'] != max(0., r['raw_point']):
            raise ValueError('Stock clipping mismatch')
        qs = [r[k] for k in ('q10','q50','q90')]
        if r['model'] in ('chronos512','timesfm512'):
            a,b,c = map(finite, qs)
            raw = [finite(r[k]) for k in ('raw_q10','raw_q50','raw_q90')]
            if not raw[0]<=raw[1]<=raw[2] or qs != [max(0.,q) for q in raw] or not 0<=a<=b<=c or b != r['prediction'] or raw[1]!=r['raw_point']:
                raise ValueError('Invalid interval/point')
        elif any(r[k] is not None for k in ('q10','q50','q90','raw_q10','raw_q50','raw_q90')):
            raise ValueError('No invented baseline intervals')
    if reg['population'] != population():
        raise ValueError('Population identity mismatch')


def summarize(rows, reg, execution=None):
    validate_rows(rows, reg)
    eligible = {r['case_id'] for r in reg['population'] if r['eligible']}
    by_model = {m: {r['case_id'] for r in rows if r['model']==m} for m in MODELS}
    # A success requires all three exact endpoints; partial paths do not become
    # selectively successful horizons in a matched comparison.
    for model, ids in by_model.items():
        for cid in ids:
            if {r['horizon'] for r in rows if r['model']==model and r['case_id']==cid} != {30,60,90}:
                raise ValueError('Partial success path')
    available=[m for m in MODELS if execution is None or m not in execution or execution[m]['status']=='PASS']
    common = set.intersection(*(by_model[m] for m in available))
    summaries = []
    for m in MODELS:
        for h in (30,60,90):
            for population_name, ids in (('all_successful', by_model[m]), ('all_admitted_matched', common)):
                for scale in ('including_mixed_scale','excluding_mixed_scale'):
                    subset = [r for r in rows if r['model']==m and r['horizon']==h and r['case_id'] in ids
                              and (scale=='including_mixed_scale' or r['scenario']!='mixed_scale')]
                    for stratum in ('all','unchanged','changing'):
                        selected = [r for r in subset if stratum=='all' or (r['actual']==r['current'])==(stratum=='unchanged')]
                        summaries.append(dict(model=m,horizon=h,population=population_name,scale=scale,stratum=stratum,**score(selected)))
    per_scenario = [dict(model=m,horizon=h,scenario=s,**score([r for r in rows if r['model']==m and r['horizon']==h and r['scenario']==s]))
                    for m in MODELS for h in (30,60,90) for s in sorted({r['scenario'] for r in rows})]
    pairs = []
    for a,b in combinations(MODELS,2):
        ids = by_model[a] & by_model[b]
        for h in (30,60,90):
            for scale in ('including_mixed_scale','excluding_mixed_scale'):
                left = {r['case_id']:r for r in rows if r['model']==a and r['horizon']==h and r['case_id'] in ids
                        and (scale=='including_mixed_scale' or r['scenario']!='mixed_scale')}
                right = {r['case_id']:r for r in rows if r['model']==b and r['horizon']==h and r['case_id'] in left}
                diffs = {cid:abs(right[cid]['prediction']-right[cid]['actual'])-abs(r['prediction']-r['actual']) for cid,r in left.items()}
                scenarios = sorted({r['scenario'] for r in left.values()})
                norm = [d/left[cid]['denominator'] for cid,d in diffs.items() if left[cid]['denominator']>0]
                pairs.append(dict(left=a,right=b,horizon=h,scale=scale,n=len(left),case_ids=sorted(left),
                    mean_error_difference_right_minus_left=st.mean(diffs.values()) if diffs else None,
                    equal_scenario_difference=st.mean(st.mean(diffs[c] for c in diffs if left[c]['scenario']==s) for s in scenarios) if scenarios else None,
                    normalized_difference=st.mean(norm) if norm else None,zero_denominators=len(left)-len(norm)))
    return dict(status='SYNTHETIC_ENGINEERING_TEST',registered_cases=len(reg['population']),eligible_cases=len(eligible),
        ineligible_cases=len(reg['population'])-len(eligible),all_admitted_common_ids=sorted(common),
        all_candidate_common_ids=sorted(set.intersection(*by_model.values())),comparison_gate='COMPLETE' if len(available)==len(MODELS) else 'PARTIAL_RUNTIME',
        available_models=available,
        accounting={m:dict(eligible=len(eligible),registered_forecasts=len(eligible),
                    successful=len(by_model[m]),native_invalid=len(eligible)-len(by_model[m]) if m in available else 0,
                    runtime_blocked=len(eligible) if m not in available else 0,
                    native_failure_rate=(len(eligible)-len(by_model[m]))/len(eligible) if m in available else None) for m in CANDIDATES},
        aggregate=summaries,scenarios=per_scenario,paired=pairs,
        distinct_numeric_histories=len({tuple(history(s).values) for s in specs() if history(s).complete_daily(512)}))


def csv_write(path, rows):
    with Path(path).open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def evaluate(study, reg, requests):
    receipt = json.loads((study/'prediction_seal.json').read_text())
    if receipt != dict(sha256=sha(study/'predictions.json'), registration_sha256=sha(study/'registration.json'), labels_scored=False):
        raise ValueError('Predictions must be sealed against registration before target access')
    predictions = json.loads((study/'predictions.json').read_text())
    if set(predictions)!=set(MODELS) or any(set(v)!=set(requests) for v in predictions.values()):
        raise ValueError('All attempted identities required, including failures')
    rows, failures = [], []
    cases = {s.case_id:s for s in specs()}
    for m in MODELS:
        for cid,pred in predictions[m].items():
            req = Request.from_dict(requests[cid])
            if 'failure' in pred:
                if (m not in ('chronos512','timesfm512','ttm512') or pred['request_id']!=req.identity or pred['failure'] not in ('NATIVE_QUANTILE_CROSSING','BLOCKED_RESOURCE','BLOCKED_RUNTIME')):
                    raise ValueError('Only identity-bound native crossing is recoverable')
                failures.append(dict(model=m,case_id=cid,reason=pred['failure'],steps=pred.get('crossing_steps')))
                continue
            validate_response(req,pred,m)
            for h in (30,60,90):
                truth = future(cases[cid])[h]
                endpoint = pred['path'][h-1]
                rows.append(dict(model=m,case_id=cid,request_id=req.identity,scenario=cases[cid].scenario,horizon=h,
                    timestamp_utc=truth['timestamp_utc'],current=req.values[-1],actual=truth['value'],
                    denominator=denominator(req),prediction=endpoint['point'],raw_point=endpoint['raw_point'],
                    q10=endpoint['q10'],q50=endpoint['q50'],q90=endpoint['q90'],
                    raw_q10=endpoint['raw_q10'],raw_q50=endpoint['raw_q50'],raw_q90=endpoint['raw_q90']))
    metrics = summarize(rows,reg,json.loads((study/'execution_status.json').read_text()))
    write(study/'metrics.json',metrics)
    write(study/'native_failures.json',failures)
    csv_write(study/'endpoints.csv',rows)
    for name,key in (('aggregate','aggregate'),('scenario','scenarios')):
        csv_write(study/(name+'_metrics.csv'),metrics[key])
    csv_write(study/'paired_metrics.csv',[{k:v for k,v in r.items() if k!='case_ids'} for r in metrics['paired']])
    return metrics


def read_rows(path):
    rows = []
    with Path(path).open(newline='') as f:
        for raw in csv.DictReader(f):
            row = dict(raw)
            row['horizon']=int(row['horizon'])
            for k in ('current','actual','denominator','prediction','raw_point','q10','q50','q90','raw_q10','raw_q50','raw_q90'):
                row[k] = None if row[k]=='' else float(row[k])
            rows.append(row)
    return rows
