"""Standalone synthetic-only benchmark; sealing precedes all numerical scoring."""
from pathlib import Path
import json,time
from .artifacts import fresh,write,seal,sha,source_identity
from .synthetic import population
from .predictors import baseline
from .evaluation import score
from .contracts import canonical


def run(output):
    out=fresh(output);cases=population();predictions={};latencies={};sources=source_identity()
    write(out/'source_identity.json',sources)
    write(out/'registration.json',dict(status='SYNTHETIC_ENGINEERING_TEST',seed_policy='6000+scenario_index*100+replicate',
          cases=[dict(case_id=c.request.case_id,scenario=c.scenario,seed=c.seed,mechanism=c.mechanism,
                      request_id=c.request.identity) for c in cases],models=['persistence','rolling_mean','linear_trend'],
          fixed_windows=dict(rolling_mean=7,linear_trend=90),large_change='abs(delta)>=max(10, .2*current)',tuning=False))
    write(out/'requests.json',[c.request.as_dict() for c in cases])
    for model in ('persistence','rolling_mean','linear_trend'):
        predictions[model]={};start=time.monotonic()
        for case in cases:
            try:result=baseline(case.request,model)
            except ValueError as exc:
                if not str(exc).startswith(('INSUFFICIENT','MISSING_ORIGIN')):raise
                result=dict(failure=str(exc),request_id=case.request.identity)
            predictions[model][case.request.case_id]=result
        latencies[model]=time.monotonic()-start
    digest=write(out/'predictions.json',predictions)
    write(out/'prediction_seal.json',dict(sha256=digest,labels_scored=False))
    assert sha(out/'predictions.json')==digest
    sealed=json.loads((out/'predictions.json').read_text())
    reports={m:score(cases,rows,m) for m,rows in sealed.items()}
    # Matched successful populations are explicit, not a silent failure exclusion.
    eligible=[c for c in cases if all(not sealed[m][c.request.case_id].get('failure') for m in sealed)]
    reports['matched_all_baselines']={m:score(eligible,{c.request.case_id:rows[c.request.case_id] for c in eligible},m) for m,rows in sealed.items()}
    write(out/'evaluation.json',reports)
    write(out/'timings.json',latencies)
    write(out/'targets.json',[dict(case_id=c.request.case_id,status='SYNTHETIC_ENGINEERING_TEST',
          generating_mechanism=c.mechanism,seed=c.seed,truth_basis='explicit daily latent generator',
          timestamps=list(c.future_timestamps),values=list(c.future_daily_truth)) for c in cases])
    assert sha(out/'predictions.json')==digest
    assert source_identity()==sources
    seal(out)
    return reports
