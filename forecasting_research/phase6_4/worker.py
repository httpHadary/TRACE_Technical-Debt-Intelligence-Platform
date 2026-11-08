"""One bounded worker: fit -> validate -> calibrate -> seal -> score, no retuning."""
import json
import resource
import socket
import sys
import time
from pathlib import Path
import numpy as np
from forecasting_research.phase6_0.contracts import Request,digest
from forecasting_research.phase6_0.artifacts import write,sha
from forecasting_research.phase6_3.models import predict as transfer_predict
from . import HORIZONS,STATUS
from .model import fit,Predictor,CONFIGS,METHODS,features,quantile
from .selection import risk,choose
from .evaluation import summarize
from .study import safe,verify,open_targets,seal_predictions,PROJECT
from .population import REPLICAS


def deny(*args,**kwargs):raise RuntimeError('NETWORK_DISABLED')


def execute(root):
    verify(root)
    transfer=json.loads((PROJECT/'examples/phase6_3/models.json').read_text())
    transfer_selection=json.loads((PROJECT/'examples/phase6_3/selection.json').read_text())
    all_rows=[];events=[];repeat=0
    def inputs(rep,part):
        raw=json.loads((root/f'{rep}.{part}.requests.json').read_text())
        metadata=json.loads((root/f'{rep}.{part}.metadata.json').read_text())
        return {cid:Request.from_dict(r) for cid,r in raw.items()},metadata
    def record(req,meta,forecast,target=None):
        f=features(req)
        r=dict(forecast,**meta,current=f['current'],model_scale=f['model_scale'],metric_scale=f['metric_scale'])
        if target is not None:
            if target['timestamp_utc']!=forecast['timestamp_utc']:raise ValueError('Exact target timestamp mismatch')
            r['actual']=target['value']
        return r
    for rep in REPLICAS:
        requests,meta=inputs(rep,'train');labels=open_targets(root,rep,'train')
        train=[dict(request=r.as_dict(),targets=labels[cid],metadata=meta[cid]) for cid,r in requests.items()]
        state=fit(train);write(root/f'{rep}.model.json',state);predictor=Predictor(state)
        events.append(dict(replica=rep,event='TRAIN_FIT',requests_sha256=digest([r.as_dict() for r in requests.values()])))
        requests,meta=inputs(rep,'validation');labels=open_targets(root,rep,'validation')
        selection={};search={}
        for h in HORIZONS:
            scores=[]
            for config in CONFIGS:
                rows=[record(r,meta[cid],predictor.predict(r,h,config=config),labels[cid][str(h)]) for cid,r in requests.items()]
                scores.append(dict(config=config,risk=risk(rows)))
            search[str(h)]=scores;selection[str(h)]=choose(scores)
            # Mechanical fallback invariant, independent of numerical preference.
            if not selection[str(h)]['admitted_adjustment'] and selection[str(h)]['config']['shrink']!=0:raise AssertionError('Unsafe fallback')
        write(root/f'{rep}.selection.json',selection);write(root/f'{rep}.search.json',search)
        events.append(dict(replica=rep,event='VALIDATION_SELECTION_FROZEN',sha256=sha(root/f'{rep}.selection.json')))
        requests,meta=inputs(rep,'calibration');labels=open_targets(root,rep,'calibration')
        calibration={}
        for h in HORIZONS:
            residuals=[abs(labels[cid][str(h)]['value']-predictor.predict(r,h,config=selection[str(h)]['config'])['point'])/features(r)['model_scale'] for cid,r in requests.items()]
            calibration[str(h)]=dict(radius=quantile(residuals,.8),n=len(residuals),role='calibration',nominal=.8)
        write(root/f'{rep}.calibration.json',calibration)
        events.append(dict(replica=rep,event='CALIBRATION_FROZEN',sha256=sha(root/f'{rep}.calibration.json')))
        for part in ('test','ood','identifiability'):
            requests,meta=inputs(rep,part);predictions=[];same_history={}
            for cid,req in requests.items():
                for h in HORIZONS:
                    config=selection[str(h)]['config']
                    for method in METHODS:
                        if method=='frozen_phase6_3':
                            oldconfig=transfer_selection['horizons'][str(h)]['configs']['adaptive_persistence']
                            result=transfer_predict(req,transfer,oldconfig,h)
                            forecast=dict(case_id=cid,request_id=req.identity,horizon=h,timestamp_utc=req.endpoint(h),
                                point=result['point'],raw_stock=result['raw_stock'],direction_probabilities=result['direction_probabilities'],
                                reason='ARCHIVED_30D_POLICY_DEVIATION' if h==30 else 'FROZEN_TRANSFER')
                        else:forecast=predictor.predict(req,h,method,config if method=='adaptive_persistence' else dict(k=48,confidence=.6,shrink=1.))
                        if method=='adaptive_persistence':
                            again=predictor.predict(req,h,method,config)
                            if again!=forecast:raise AssertionError('Nondeterministic inference')
                            repeat+=1
                            key=(meta[cid]['history_sha256'],h)
                            pure={k:v for k,v in forecast.items() if k not in ('case_id','request_id')}
                            if key in same_history and same_history[key]!=pure:raise AssertionError('Hidden branch leaked')
                            same_history[key]=pure
                            f=features(req);radius=calibration[str(h)]['radius']*f['model_scale']
                            forecast['calibrated_interval']=[max(0.,forecast['point']-radius),forecast['point']+radius]
                            _,_,_,order=predictor.context(req);values=predictor.y[str(h)][order[:config['k']]]
                            forecast['local_interval']=[max(0.,f['current']+quantile(values,q)*f['model_scale']) for q in (.1,.9)]
                        predictions.append(dict(record(req,meta[cid],forecast),method=method))
            write(root/f'{rep}.{part}.predictions.json',predictions)
        seal_predictions(root,rep,[f'{rep}.{name}.json' for name in ('model','selection','calibration')])
        events.append(dict(replica=rep,event='ALL_TEST_OOD_PREDICTIONS_SEALED',sha256=sha(root/f'{rep}.prediction_seal.json')))
        for part in ('test','ood','identifiability'):
            labels=open_targets(root,rep,part)
            rows=json.loads((root/f'{rep}.{part}.predictions.json').read_text())
            for row in rows:
                target=labels[row['case_id']][str(row['horizon'])]
                if target['timestamp_utc']!=row['timestamp_utc']:raise ValueError('Target mapping failed')
                all_rows.append(dict(row,actual=target['value']))
        events.append(dict(replica=rep,event='TEST_OOD_LABELS_OPENED_AFTER_SEAL'))
    write(root/'events.json',events)
    write(root/'metrics.json',summarize(all_rows))
    write(root/'repeatability.json',dict(exact_repeated_predictions=repeat,identical_history_hidden_branch_predictions_equal=True))
    write(root/'completion.json',dict(scope=STATUS,execution='PASS',scientific_success='SEE_METRICS_NO_ASSUMED_IMPROVEMENT',forecasts=len(all_rows)))


def main():
    root=safe(sys.argv[1]);start=time.monotonic();code=0;failure=None
    socket.socket.connect=deny;socket.create_connection=deny
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
    try:execute(root)
    except Exception as exc:
        code=1;failure=dict(type=type(exc).__name__,message=str(exc))
        write(root/'failure.json',failure)
        raise
    finally:
        usage=resource.getrusage(resource.RUSAGE_SELF)
        write(root/'worker_resources.json',dict(exit_code=code,failure=failure,wall_seconds=time.monotonic()-start,
            peak_rss_bytes=usage.ru_maxrss*1024,user_cpu_seconds=usage.ru_utime,system_cpu_seconds=usage.ru_stime,
            numpy=np.__version__,python=sys.version,thread_environment={k:__import__('os').environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}))

if __name__=='__main__':main()
