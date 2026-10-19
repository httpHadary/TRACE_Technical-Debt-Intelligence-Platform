"""Read-only adapter bridge. No real contexts, training, remote loading or fallback."""
from .contracts import response,iso,utc
from .predictors import bridge
from datetime import timedelta


class Recorder:
    def __init__(self,pipeline):self.pipeline=pipeline;self.rows=None
    def predict_df(self,*args,**kwargs):
        frame=self.pipeline.predict_df(*args,**kwargs)
        self.rows=frame.to_dict('records')
        return frame


def predict(adapter,request):
    from forecasting_mvp.chronos_adapter import ChronosSmallAdapter, NativeQuantileCrossingError
    observed=Recorder(adapter.pipeline)
    guarded=ChronosSmallAdapter(observed)
    try:
        native=guarded.predict_path(bridge(request))
    except NativeQuantileCrossingError:
        # Entire path still invalid; expose diagnostic positions, never repair/sort.
        rows=observed.rows
        crossings=[dict(step=i+1,raw_q10=float(r['0.1']),raw_q50=float(r['0.5']),raw_q90=float(r['0.9']))
                   for i,r in enumerate(rows) if not float(r['0.1'])<=float(r['0.5'])<=float(r['0.9'])]
        return dict(failure='NATIVE_QUANTILE_CROSSING',crossings=crossings,request_id=request.identity)
    raw=[dict(timestamp_utc=r['timestamp'],raw_point=r['raw_q50'],raw_q10=r['raw_q10'],raw_q50=r['raw_q50'],raw_q90=r['raw_q90']) for r in native]
    return response(request,'chronos_small',raw,quantiles=True)
