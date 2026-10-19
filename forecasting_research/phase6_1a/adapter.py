"""New context-length adapter. Original Phase 4/6.0 adapters are never modified."""
from datetime import timedelta
import inspect
from forecasting_research.phase6_0.contracts import Request,utc,iso,finite,response


class NativePathCrossing(ValueError):
    def __init__(self,path,steps):
        super().__init__('NATIVE_QUANTILE_CROSSING');self.path=path;self.steps=steps


class ContextAdapter:
    def __init__(self,pipeline):
        self.pipeline=pipeline
        parameters=inspect.signature(pipeline.predict_df).parameters
        if not {'context_length','prediction_length','quantile_levels','freq'}<=set(parameters):
            raise ValueError('Pinned documented API required')
        if pipeline.model_context_length<512 or pipeline.model_prediction_length<90:
            raise ValueError('Insufficient native context/output capacity')
        self.forward_receipt=[]

    def predict(self,request,context_days):
        if type(context_days) is not int or context_days not in (90,512) or not isinstance(request,Request) or not request.complete_daily(context_days):
            raise ValueError('Unsupported context: complete 90/512 daily synthetic observations only')
        import pandas as pd
        times=pd.to_datetime(request.timestamps,utc=True).tz_localize(None).as_unit('ns')
        frame=pd.DataFrame(dict(item_id=['series']*context_days,timestamp=times,debt_minutes=request.values))
        result=self.pipeline.predict_df(frame,prediction_length=90,quantile_levels=[.1,.5,.9],id_column='item_id',
            timestamp_column='timestamp',target='debt_minutes',context_length=context_days,batch_size=1,
            cross_learning=False,validate_inputs=True,freq='D')
        required={'item_id','timestamp','target_name','predictions','0.1','0.5','0.9'}
        if set(result.columns)!=required or len(result)!=90:raise ValueError('Output shape/columns mismatch')
        raw=[];crossings=[]
        for step,row in enumerate(result.to_dict('records'),1):
            expected=iso(utc(request.origin_utc)+timedelta(days=step))
            stamp=pd.Timestamp(row['timestamp']);stamp=stamp.tz_localize('UTC') if stamp.tzinfo is None else stamp.tz_convert('UTC')
            if row['item_id']!='series' or row['target_name']!='debt_minutes' or stamp.isoformat().replace('+00:00','Z')!=expected:
                raise ValueError('Native output daily timestamp/identity mismatch')
            q10,q50,q90=(finite(row[k]) for k in ('0.1','0.5','0.9'));finite(row['predictions'])
            raw.append(dict(timestamp_utc=expected,raw_point=q50,raw_q10=q10,raw_q50=q50,raw_q90=q90))
            if not q10<=q50<=q90:crossings.append(step)
        # Full identity/finiteness checks precede the only recoverable failure.
        if crossings:raise NativePathCrossing(raw,crossings)
        return response(request,'chronos'+str(context_days),raw,quantiles=True)

    def predict_observed(self,request,context_days):
        """Prove the actual model forward consumed every requested float32 observation."""
        if not isinstance(request,Request) or context_days not in (90,512) or not request.complete_daily(context_days):
            raise ValueError('Admitted complete context required before forward hook')
        import torch,hashlib
        receipts=[]
        def before(module,args,kwargs):
            context=kwargs.get('context',args[0] if args else None)
            expected=torch.tensor(request.values,dtype=torch.float32,device='cpu').reshape(1,-1)
            if (context is None or context.device.type!='cpu' or context.dtype!=torch.float32 or context.shape!=expected.shape
                    or not torch.equal(context,expected) or not torch.isfinite(context).all()):
                raise RuntimeError('Actual model did not receive exact registered float32 context')
            if kwargs.get('future_target') is not None:raise RuntimeError('Future targets forbidden')
            receipts.append(dict(context_shape=list(context.shape),finite_positions=int(torch.isfinite(context).sum()),
                                 matches_requested_float32=True,context_sha256=hashlib.sha256(context.detach().numpy().tobytes()).hexdigest()))
        handle=self.pipeline.model.register_forward_pre_hook(before,with_kwargs=True)
        def norm_observer(module,args,kwargs,output):
            # Native per-context statistics, not an additional fitted transform.
            if receipts and kwargs.get('loc_scale') is None:
                loc,scale=output[1]
                receipts[-1]['native_location']=loc.detach().reshape(-1).tolist()
                receipts[-1]['native_scale']=scale.detach().reshape(-1).tolist()
        normalization=self.pipeline.model.instance_norm.register_forward_hook(norm_observer,with_kwargs=True)
        try:
            try:result=self.predict(request,context_days)
            except NativePathCrossing as exc:
                result=dict(failure='NATIVE_QUANTILE_CROSSING',request_id=request.identity,
                            crossing_steps=exc.steps,invalid_raw_path=exc.path)
        finally:
            handle.remove();normalization.remove()
        if len(receipts)!=1:raise RuntimeError('Exactly one native forward expected; no unrolling/fallback')
        self.forward_receipt=receipts
        return result
