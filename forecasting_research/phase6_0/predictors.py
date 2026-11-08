"""No labels, filesystem access or model fitting. Frozen adapters remain unchanged."""
from datetime import timedelta
import statistics
from .contracts import Request,finite,iso,utc,response


def bridge(request):
    if not isinstance(request,Request) or not request.complete_daily():
        raise ValueError('Complete 90 daily observed synthetic values required; no fill/padding')
    from forecasting_mvp.prediction_input import PredictionInput
    # Typed synthetic bridge only. Never a historical measurement/admission proof.
    return PredictionInput(request.identity,request.case_id,'core90',request.origin_utc,90,request.timestamps,request.values)


def baseline(request, model='persistence'):
    if not isinstance(request,Request) or model not in ('persistence','rolling_mean','linear_trend'):
        raise ValueError('Registered baseline and typed past-only request required')
    if request.values[-1] is None:
        raise ValueError('MISSING_ORIGIN; persistence cannot carry unknown stock')
    current=finite(request.values[-1]);origin=utc(request.origin_utc)
    raw=[]
    if request.complete_daily():
        from forecasting_mvp.baselines import baseline_predict
        historical=bridge(request)
    else:historical=None
    observed=[((utc(t)-origin).total_seconds()/86400,finite(v)) for t,v in zip(request.timestamps,request.values) if v is not None]
    for h in range(1,91):
        if historical is not None and h in (30,60,90):
            from dataclasses import replace
            v=baseline_predict(replace(historical,horizon_days=h),model,{'persistence':0,'rolling_mean':7,'linear_trend':90}[model])[0]
        elif model=='persistence':v=current
        elif model=='rolling_mean':
            recent=[v for d,v in observed if d>-7]
            if len(recent)<6:raise ValueError('INSUFFICIENT_WINDOW; no sparse-history fill')
            v=statistics.mean(recent)
        else:
            if len(observed)<3:raise ValueError('INSUFFICIENT_DISTINCT_TIMES')
            slope=statistics.linear_regression([d for d,v in observed],[v for d,v in observed]).slope
            v=current+h*slope
        raw.append(dict(timestamp_utc=iso(origin+timedelta(days=h)),raw_point=v,raw_q10=None,raw_q50=None,raw_q90=None))
    return response(request,model,raw)


def change_features(request):
    if not isinstance(request,Request):raise ValueError('Typed request required')
    observed=[(utc(t),v) for t,v in zip(request.timestamps,request.values) if v is not None]
    pairs=list(zip(observed,observed[1:]))
    changes=[(b[0],b[1]-a[1]) for a,b in pairs if b[1]!=a[1]]
    contiguous=all((b[0]-a[0])==timedelta(days=1) for a,b in pairs)
    return dict(current=request.values[-1],distinct_observed_values=len({v for t,v in observed}),
                observed_transition_count=len(changes),observed_transition_fraction=len(changes)/len(pairs) if pairs else None,
                days_since_last_observed_transition=(utc(request.origin_utc)-changes[-1][0]).total_seconds()/86400 if changes else None,
                volatility=statistics.pstdev([v for t,v in observed]) if len(observed)>1 else None,
                measurement_gaps=not contiguous,unobserved_changes_possible=not contiguous)


def reconstruct(current, signed_delta):
    current=finite(current)
    if current<0:raise ValueError('Stock cannot be negative')
    return max(0.0,current+finite(signed_delta))


def blend(current, candidate, weight):
    w=finite(weight)
    if not 0<=w<=1:raise ValueError('Validation-frozen weight in [0,1] required')
    return reconstruct(current,w*(finite(candidate)-finite(current)))


def gate(current, signed_delta, probability, threshold):
    p,t=finite(probability),finite(threshold)
    if not 0<=p<=1 or not 0<=t<=1:raise ValueError('Registered probabilities/threshold required')
    return reconstruct(current,signed_delta if p>=t else 0)
