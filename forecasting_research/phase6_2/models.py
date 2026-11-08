"""Small NumPy models; fit accepts synthetic TRAIN rows, predict accepts Request only."""
import math
import statistics as st
import numpy as np
from forecasting_research.phase6_0.contracts import Request, finite, digest
from forecasting_research.phase6_0.predictors import reconstruct, gate, blend
from . import HORIZONS, VERSION, STATUS
from .features import extract, baseline, NAMES

ALPHAS = (1., 10.)
THRESHOLDS = (.1, .25, .5, .75, .9)
WEIGHTS = (0., .25, .5, .75, 1.)
METHODS = ('persistence', 'rolling_mean', 'anchored_trend', 'direct_delta',
           'hard_gate', 'probability_weighted', 'mixture_median', 'blend', 'selected')


def probability(value):
    value = finite(value)
    if not 0 <= value <= 1:
        raise ValueError('Probability must lie in [0,1]')
    return value


def transform_fit(vectors):
    a = np.array([[np.nan if v is None else v for v in row] for row in vectors], dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != len(NAMES) or not len(a):
        raise ValueError('Registered feature shape required')
    med = np.array([float(np.median(c[np.isfinite(c)])) if np.isfinite(c).any() else 0. for c in a.T])
    missing = np.isnan(a).astype(float)
    a = np.where(np.isnan(a), med, a)
    a = np.concatenate([a, missing], axis=1)
    mean, sd = a.mean(axis=0), a.std(axis=0)
    sd = np.where(sd == 0, 1., sd)
    state = dict(medians=med.tolist(), mean=mean.tolist(), sd=sd.tolist(),
                 fit_partition='train', null_policy='training median + explicit missing indicator',
                 constant_column_policy='unit scale; no metric denominator change')
    return state, np.column_stack([np.ones(len(a)), (a-mean)/sd])


def transform(state, vectors):
    a = np.array([[np.nan if v is None else v for v in row] for row in vectors], dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != len(NAMES):
        raise ValueError('Registered features required')
    missing = np.isnan(a).astype(float)
    a = np.where(np.isnan(a), state['medians'], a)
    a = np.concatenate([a, missing], axis=1)
    out = np.column_stack([np.ones(len(a)), (a-state['mean'])/state['sd']])
    if not np.isfinite(out).all():
        raise ValueError('Nonfinite transformed input')
    return out


def ridge(x, y, alpha):
    if alpha not in ALPHAS or len(x) == 0 or len(x) != len(y):
        raise ValueError('Registered positive regularization and observations required')
    penalty = np.eye(x.shape[1])*alpha
    penalty[0, 0] = 0
    beta = np.linalg.solve(x.T@x+penalty, x.T@np.asarray(y))
    if not np.isfinite(beta).all():
        raise ValueError('Nonfinite ridge coefficients')
    return beta.tolist()


def sigmoid(x):
    return 1/(1+np.exp(-np.clip(x, -40, 40)))


def logistic(x, y, alpha):
    if alpha not in ALPHAS or len(y) != len(x) or not set(y) <= {0, 1}:
        raise ValueError('Binary labels and registered penalty required')
    if len(set(y)) < 2:
        return dict(kind='single_class', probability=float(st.mean(y)),
                    reason='INSUFFICIENT_CLASS_DIVERSITY; no logistic fit', eligible=False)
    y = np.asarray(y)
    beta = np.zeros(x.shape[1])
    penalty = np.eye(x.shape[1])*alpha
    penalty[0, 0] = 0
    # Fixed damped Newton iterations; deterministic, no test-selected stopping.
    for _ in range(40):
        p = sigmoid(x@beta)
        hessian = x.T@((p*(1-p))[:, None]*x)+penalty
        gradient = x.T@(p-y)+penalty@beta
        step = np.linalg.solve(hessian, gradient)
        beta -= .5*step
    if not np.isfinite(beta).all():
        raise ValueError('Invalid classifier coefficients')
    return dict(kind='logistic', coefficients=beta.tolist(), eligible=True,
                training_prevalence=float(y.mean()), iterations=40,
                class_weight='none; each synthetic training case equal')


def change_probability(state, x):
    if state['kind'] == 'single_class':
        return probability(state['probability'])
    return probability(float(sigmoid(x@np.array(state['coefficients']))[0]))


def fit(rows):
    if not rows or any(set(r) != {'partition', 'request', 'targets'} or r['partition'] != 'train' for r in rows):
        raise ValueError('Training partition only; validation/test labels forbidden in fit')
    requests = [Request.from_dict(r['request']) for r in rows]
    for req, row in zip(requests, rows):
        if set(row['targets']) != {str(h) for h in HORIZONS}:
            raise ValueError('All exact training endpoints required')
        for h in HORIZONS:
            target = row['targets'][str(h)]
            if set(target) != {'timestamp_utc','value'} or target['timestamp_utc'] != req.endpoint(h):
                raise ValueError('Training endpoint identity mismatch')
    features = [extract(r) for r in requests]
    preprocessor, x = transform_fit([f['vector'] for f in features])
    heads = {}
    for h in HORIZONS:
        actual = [finite(r['targets'][str(h)]['value']) for r in rows]
        if any(v < 0 for v in actual):
            raise ValueError('Nonnegative synthetic stock labels required')
        y = np.array([(v-f['current'])/f['model_scale'] for f, v in zip(features, actual)])
        changed = (y != 0).astype(int)
        candidates = {}
        for alpha in ALPHAS:
            direct = ridge(x, y, alpha)
            positive = changed.astype(bool)
            if positive.sum() < 2:
                conditional, residuals = None, []
            else:
                conditional = ridge(x[positive], y[positive], alpha)
                residuals = sorted((y[positive]-x[positive]@np.array(conditional)).tolist())
            candidates[str(alpha)] = dict(direct=direct, conditional=conditional,
                classifier=logistic(x, changed.tolist(), alpha),
                conditional_residuals=residuals, changed_training_count=int(positive.sum()))
        heads[str(h)] = candidates
    return dict(version=VERSION, status=STATUS, feature_names=list(NAMES), preprocessor=preprocessor,
                heads=heads, train_requests_sha256=digest([r['request'] for r in rows]),
                train_n=len(rows), training_only=True)


def weighted_quantile(support, q):
    probability(q)
    if not support or any(not math.isfinite(v) or not math.isfinite(w) or w < 0 for v, w in support):
        raise ValueError('Finite nonnegative probability mass required')
    total = sum(w for _, w in support)
    if abs(total-1) > 1e-9:
        raise ValueError('Probability mass must sum to one')
    mass = 0.
    ordered = sorted(support, key=lambda v: v[0])  # Distribution support, not forecast quantile repair.
    for value, weight in ordered:
        mass += weight
        if mass >= q:
            return value
    return ordered[-1][0]


def mixture(p, conditional_delta, residuals):
    p = probability(p)
    if not residuals:
        raise ValueError('INELIGIBLE_DISTRIBUTION: no changed-training residual support')
    support = [(0., 1-p)]+[(finite(conditional_delta)+finite(r), p/len(residuals)) for r in residuals]
    return [weighted_quantile(support, q) for q in (.1, .5, .9)]


def configs(method):
    if method in METHODS[:3]:
        return [dict(method=method)]
    if method not in METHODS[3:-1]:
        raise ValueError('Unregistered method')
    grid = []
    for alpha in ALPHAS:
        for param in THRESHOLDS if method == 'hard_gate' else WEIGHTS if method == 'blend' else (None,):
            config = dict(method=method, alpha=alpha)
            if method == 'hard_gate':
                config['threshold'] = param
            if method == 'blend':
                config['weight'] = param
            grid.append(config)
    return grid


def predict(request, state, config, horizon):
    """No label/split/scenario/generator parameter argument; pure inference."""
    if (not isinstance(request, Request) or not isinstance(config, dict) or type(horizon) is not int or horizon not in HORIZONS
            or config not in configs(config.get('method')) or state['version'] != VERSION
            or state['feature_names'] != list(NAMES)):
        raise ValueError('Registered request/model/config identity required')
    f = extract(request)
    method = config['method']
    p, qs = None, None
    if method in METHODS[:3]:
        raw = baseline(request, method, horizon)
    else:
        x = transform(state['preprocessor'], [f['vector']])
        head = state['heads'][str(horizon)][str(config['alpha'])]
        p = change_probability(head['classifier'], x)
        direct = float((x@np.array(head['direct']))[0])
        if method in ('direct_delta', 'blend'):
            delta = direct
        else:
            if head['conditional'] is None:
                raise ValueError('INELIGIBLE_CONDITIONAL_MODEL')
            conditional = float((x@np.array(head['conditional']))[0])
            if method == 'hard_gate':
                delta = conditional if p >= config['threshold'] else 0.
            elif method == 'probability_weighted':
                delta = p*conditional
            else:
                qs = mixture(p, conditional, head['conditional_residuals'])
                delta = qs[1]
        if method == 'blend':
            delta *= config['weight']
        raw = f['current']+delta*f['model_scale']
    finite(raw)
    signed = raw-f['current']
    output = dict(version=VERSION, status=STATUS, unit=request.unit, case_id=request.case_id,
                  request_id=request.identity, horizon=horizon, timestamp_utc=request.endpoint(horizon),
                  config_sha256=digest(config), raw_signed_delta=signed, raw_stock=raw,
                  point=reconstruct(f['current'], signed), p_change=p,
                  mixture_raw_quantiles=[f['current']+q*f['model_scale'] for q in qs] if qs else None,
                  mixture_quantiles=[max(0., f['current']+q*f['model_scale']) for q in qs] if qs else None)
    if method == 'hard_gate' and output['point'] != gate(f['current'], signed, p, config['threshold']):
        raise ValueError('Gate reconstruction invariant')
    if method == 'blend' and output['point'] != blend(f['current'], f['current']+direct*f['model_scale'], config['weight']):
        # Roundoff may differ under algebraically equivalent operations.
        if not math.isclose(output['point'], blend(f['current'], f['current']+direct*f['model_scale'], config['weight']), abs_tol=1e-8):
            raise ValueError('Blend reconstruction invariant')
    return output
