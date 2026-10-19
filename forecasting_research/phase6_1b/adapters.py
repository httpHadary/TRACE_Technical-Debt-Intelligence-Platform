"""Past-only adapters. Unadmitted models fail before importing executable code."""
from statistics import mean, linear_regression
from datetime import timedelta
from forecasting_research.phase6_0.contracts import Request, response, iso, utc, finite
from forecasting_research.phase6_1a.adapter import ContextAdapter

BASELINES = ('persistence', 'rolling_mean', 'linear_trend')
MODEL = 'chronos512'


class BlockedAcquisition(RuntimeError):
    pass


def require_daily(request):
    if not isinstance(request, Request) or not request.complete_daily(512):
        raise ValueError('512 genuinely observed daily synthetic positions required; no fill')


def baseline(request, model):
    require_daily(request)
    if model not in BASELINES:
        raise ValueError('Unregistered baseline')
    current = request.values[-1]
    # Fixed before outcomes. All methods receive the same history; these baselines
    # intentionally select fixed past windows, without validation/test tuning.
    slope = linear_regression(range(-89, 1), request.values[-90:]).slope if model == 'linear_trend' else 0
    level = mean(request.values[-7:]) if model == 'rolling_mean' else current
    return response(request, model, [dict(timestamp_utc=iso(utc(request.origin_utc) + timedelta(days=h)),
        raw_point=level + h * slope, raw_q10=None, raw_q50=None, raw_q90=None) for h in range(1, 91)])


class Chronos512:
    """Read-only composition of the independently observed native API adapter."""
    def __init__(self, pipeline):
        self.native = ContextAdapter(pipeline)

    def predict(self, request):
        require_daily(request)
        return self.native.predict_observed(request, 512)

    @property
    def forward_receipt(self):
        return self.native.forward_receipt


class UnadmittedModel:
    """Explicit gate adapter, NOT a claim of a working TTM/TimesFM integration.

    Pinned code licensing, hashed dependency closure, exact daily API routing and
    resource admission must be verified before a separate native implementation.
    There is deliberately no generic remote-code/from_pretrained fallback.
    """
    def __init__(self, model):
        if model not in ('ttm512', 'timesfm512'):
            raise ValueError('Only registered blocked candidates')
        self.model = model

    def predict(self, request):
        require_daily(request)
        raise BlockedAcquisition(f'{self.model}: BLOCKED_ACQUISITION; no approval or admitted runtime')


def native_path(request, model, points, quantiles=None):
    require_daily(request)
    if len(points)!=90 or (quantiles is not None and len(quantiles)!=90):
        raise ValueError('Native horizon shape mismatch')
    raw=[]
    crossings=[]
    for step,point in enumerate(points,1):
        p=finite(point)
        qs=[None]*3 if quantiles is None else list(map(finite,quantiles[step-1]))
        if len(qs)!=3:
            raise ValueError('q10/q50/q90 required')
        if quantiles is not None and (not qs[0]<=qs[1]<=qs[2]):
            crossings.append(step)
        raw.append(dict(timestamp_utc=iso(utc(request.origin_utc)+timedelta(days=step)),raw_point=p,
                        raw_q10=qs[0],raw_q50=qs[1],raw_q90=qs[2]))
    if crossings:
        return dict(failure='NATIVE_QUANTILE_CROSSING',request_id=request.identity,
                    crossing_steps=crossings,invalid_raw_path=raw)
    return response(request,model,raw,quantiles=quantiles is not None)


class TTM512:
    def __init__(self, model, daily_token):
        if (model.config.context_length,model.config.prediction_length,daily_token)!=(512,96,8):
            raise ValueError('Pinned daily512→96 configuration required')
        if not model.config.resolution_prefix_tuning or model.config.loss!='mse' or model.config.multi_quantile_head:
            raise ValueError('Pinned point-regression semantics required')
        self.model=model
        self.daily_token=daily_token

    def predict(self, request):
        require_daily(request)
        import torch
        import hashlib
        x=torch.tensor(request.values,dtype=torch.float32).reshape(1,512,1)
        traces=[]
        def observe(module,args,kwargs):
            actual=kwargs['past_values']
            if not torch.equal(actual,x) or kwargs.get('future_values') is not None or not kwargs['past_observed_mask'].all() or kwargs['freq_token'].tolist()!=[8]:
                raise RuntimeError('TTM past-only tensor/frequency identity violated')
            traces.append(dict(shape=list(actual.shape),finite_positions=int(torch.isfinite(actual).sum()),
                               matches_requested_float32=True,daily_token=8,context_sha256=hashlib.sha256(actual.numpy().tobytes()).hexdigest()))
        hook=self.model.register_forward_pre_hook(observe,with_kwargs=True)
        try:
            with torch.inference_mode():
                y=self.model(past_values=x,past_observed_mask=torch.ones_like(x,dtype=torch.bool),
                             freq_token=torch.tensor([self.daily_token]),return_loss=False).prediction_outputs
        finally:
            hook.remove()
        if list(y.shape)!=[1,96,1] or not torch.isfinite(y).all() or len(traces)!=1:
            raise ValueError('TTM native output/forward contract violated')
        points=y.detach().cpu().reshape(-1).tolist()
        self.forward_receipt=dict(trace=traces,native_steps=96,raw_native_point_path=points,quantiles=None)
        return native_path(request,'ttm512',points[:90])


class TimesFM512:
    def __init__(self, model):
        fc=model.forecast_config
        if fc.max_context!=512 or fc.fix_quantile_crossing or fc.infer_is_positive or fc.force_flip_invariance:
            raise ValueError('Pinned native audit configuration required')
        self.model=model

    def predict(self, request):
        require_daily(request)
        import numpy as np
        import torch
        import hashlib
        x=np.asarray(request.values,dtype=np.float32)
        trace=[]
        original=self.model.compiled_decode
        def observed(horizon,inputs,masks):
            values=np.asarray(inputs)
            if horizon!=90 or values.shape!=(1,512) or not np.array_equal(values[0],x) or np.asarray(masks).any():
                raise RuntimeError('TimesFM complete past tensor identity violated; no fill')
            trace.append(dict(shape=list(values.shape),matches_requested_float32=True,
                              masked_positions=0,context_sha256=hashlib.sha256(values.astype(np.float32).tobytes()).hexdigest()))
            return original(horizon,inputs,masks)
        self.model.compiled_decode=observed
        try:
            with torch.inference_mode():
                point,full=self.model.forecast(horizon=90,inputs=[x])
        finally:
            self.model.compiled_decode=original
        if point.shape!=(1,90) or full.shape!=(1,90,10) or not np.isfinite(point).all() or not np.isfinite(full).all() or len(trace)!=1:
            raise ValueError('TimesFM native shape/finiteness contract violated')
        if not np.array_equal(point,full[:,:,5]):
            raise ValueError('Pinned API point must equal native q50')
        crossings=(np.diff(full[0,:,1:],axis=1)<0).any(axis=1)
        self.forward_receipt=dict(trace=trace,native_steps=90,raw_mean_head=full[0,:,0].tolist(),
            raw_all_deciles=full[0,:,1:].tolist(),fix_quantile_crossing=False,
            configured_max_horizon=self.model.forecast_config.max_horizon)
        result=native_path(request,'timesfm512',point[0].tolist(),full[0][:,[1,5,9]].tolist())
        if crossings.any():
            result=dict(failure='NATIVE_QUANTILE_CROSSING',request_id=request.identity,
                        crossing_steps=(np.nonzero(crossings)[0]+1).tolist(),invalid_native_quantiles=full[0].tolist())
        return result
