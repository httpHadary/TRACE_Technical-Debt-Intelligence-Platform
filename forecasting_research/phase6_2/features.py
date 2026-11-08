"""Pure past-only features. Nulls are explicit; gaps never prove persistence."""
import math
import statistics as st
from forecasting_research.phase6_0.contracts import Request, finite, utc
from . import HORIZONS


NAMES = ('current', 'observed_changes', 'observed_transition_fraction',
         'days_since_observed_change', 'distinct_values', 'volatility',
         'recent_signed_change', 'recent_absolute_change', 'short_slope',
         'long_slope', 'short_average', 'long_average', 'contiguous_plateau_days',
         'minimum', 'maximum', 'log_scale', 'relative_variability',
         'observed_count', 'missing_fraction', 'mean_gap_days', 'max_gap_days',
         'contiguous_transition_fraction', 'gaps_present', 'scale_zero')


def slope(points):
    if len(points) < 2:
        return None
    mx = st.mean(x for x, _ in points)
    my = st.mean(y for _, y in points)
    denominator = sum((x-mx)**2 for x, _ in points)
    return sum((x-mx)*(y-my) for x, y in points)/denominator if denominator else None


def extract(request):
    if not isinstance(request, Request) or request.values[-1] is None:
        raise ValueError('Typed past-only request with measured origin required')
    origin = utc(request.origin_utc)
    obs = [((utc(t)-origin).total_seconds()/86400, finite(v))
           for t, v in zip(request.timestamps, request.values) if v is not None]
    if len(obs) < 2:
        raise ValueError('At least two actually observed values required')
    values = [v for _, v in obs]
    denominator = st.mean(abs(v) for v in values)
    # Training/reconstruction scale is distinct from the reported metric scale.
    # One minute is an explicit model unit for zero/sub-minute series, no epsilon.
    model_scale = max(1., denominator)
    pairs = [(b[0], b[1]-a[1], b[0]-a[0]) for a, b in zip(obs, obs[1:])]
    changed = [t for t, d, _ in pairs if d != 0]
    recent = [(t, d, gap) for t, d, gap in pairs if t > -30]
    contiguous = [(t, d) for t, d, gap in pairs if gap == 1]
    plateau = 0.
    for _, d, gap in reversed(pairs):
        if gap != 1 or d != 0:
            break
        plateau += 1
    short = [(t, v) for t, v in obs if t > -30]
    long = [(t, v) for t, v in obs if t > -90]
    calendar_span = int((origin-utc(request.timestamps[0])).total_seconds()/86400)+1
    sd = st.pstdev(values)
    features = [values[-1]/model_scale, len(changed)/len(pairs),
                len(changed)/len(pairs), -changed[-1]/180 if changed else None,
                len(set(values))/len(values), sd/model_scale,
                st.mean(d for _, d, _ in recent)/model_scale if recent else None,
                st.mean(abs(d) for _, d, _ in recent)/model_scale if recent else None,
                slope(short), slope(long),
                st.mean(v for _, v in short)/model_scale,
                st.mean(v for _, v in long)/model_scale,
                plateau/180, min(values)/model_scale, max(values)/model_scale,
                math.log1p(denominator)/10, sd/denominator if denominator else None,
                len(obs)/180, 1-len(obs)/calendar_span,
                st.mean(gap for _, _, gap in pairs)/180,
                max(gap for _, _, gap in pairs)/180,
                st.mean(d != 0 for _, d in contiguous) if contiguous else None,
                float(any(gap > 1 for _, _, gap in pairs)), float(denominator == 0)]
    # Counts are scaled for regression; descriptive audit preserves actual counts.
    features[1] = len(changed)/180
    features[8] = features[8]/model_scale if features[8] is not None else None
    features[9] = features[9]/model_scale if features[9] is not None else None
    if any(v is not None and not math.isfinite(v) for v in features):
        raise ValueError('Nonfinite historical feature')
    return dict(vector=features, metric_scale=denominator, model_scale=model_scale,
                current=values[-1], observed_count=len(obs), observed_changes=len(changed),
                observed_transition_fraction=len(changed)/len(pairs),
                gap_censored=any(gap > 1 for _, _, gap in pairs),
                plateau_lower_bound_days=plateau,
                days_since_observed_change=-changed[-1] if changed else None,
                missing_records=sum(v is None for v in request.values))


def baseline(request, method, horizon):
    if horizon not in HORIZONS or type(horizon) is not int:
        raise ValueError('Exact registered endpoint required')
    f = extract(request)
    origin = utc(request.origin_utc)
    observed = [((utc(t)-origin).total_seconds()/86400, v)
                for t, v in zip(request.timestamps, request.values) if v is not None]
    if method == 'persistence':
        return f['current']
    if method == 'rolling_mean':
        # Fixed last seven actual observations, not seven fabricated daily states.
        return st.mean(v for _, v in observed[-7:])
    if method == 'anchored_trend':
        gradient = slope([(t, v) for t, v in observed if t > -90])
        if gradient is None:
            raise ValueError('INSUFFICIENT_OBSERVATIONS for fixed 90-calendar-day slope')
        return f['current']+horizon*gradient
    raise ValueError('Unregistered baseline')
