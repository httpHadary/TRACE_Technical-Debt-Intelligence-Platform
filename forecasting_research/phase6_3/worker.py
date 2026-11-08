"""One bounded synthetic fit, validation freeze, calibrated/sealed final evaluation."""
from pathlib import Path
import json
import os
import resource
import socket
import sys
import time
import traceback
from forecasting_research.phase6_0.artifacts import write,sha
from forecasting_research.phase6_0.contracts import Request,digest,finite
from . import STATUS,HORIZONS
from .models import fit,predict,features,METHODS
from .selection import select,records
from .calibration import KINDS,build,choose,apply
from .study import safe,verify,Labels,prediction_seal,verify_prediction_seal
from .evaluation import summarize


def validate_predictions(root,requests,metadata,selection):
    verify_prediction_seal(root)
    predictions=json.loads((root/'predictions.json').read_text())
    expected={(m,c,h) for c,r in metadata.items() if r['partition'] in ('test','ood') for m in METHODS for h in HORIZONS}
    seen=set()
    for p in predictions:
        key=(p['method'],p['case_id'],p['horizon'])
        if key in seen or key not in expected: raise ValueError('Duplicate/unregistered forecast')
        seen.add(key);r=requests[p['case_id']]
        finite(p['point']);finite(p['raw_stock']);finite(p['raw_signed_delta'])
        conf=selection['horizons'][str(p['horizon'])]['configs'][p['method']]
        if (p['request_id']!=r.identity or p['config_sha256']!=digest(conf) or p['timestamp_utc']!=r.endpoint(p['horizon'])
                or p['point']!=max(0.,p['raw_stock']) or p['raw_signed_delta']!=p['raw_stock']-r.values[-1]
                or p['family']!=metadata[r.case_id]['family'] or p['partition']!=metadata[r.case_id]['partition'] or p['status']!=STATUS):
            raise ValueError('Forecast identity/stock mismatch')
        for q in p['intervals'].values():
            a,b,c=map(finite,q)
            if not 0<=a<=b<=c: raise ValueError('Invalid derived interval; no repair')
    if seen!=expected: raise ValueError('Missing forecast population')
    return predictions


def execute(root):
    root=safe(root);verify(root)
    events=[dict(event='registration_verified',sha256=sha(root/'registration.json'))]
    labels=Labels(root,events)
    requests={c:Request.from_dict(r) for c,r in json.loads((root/'requests.json').read_text()).items()}
    metadata={r['case_id']:r for r in json.loads((root/'population.json').read_text())}
    inputs=lambda p:{c:r for c,r in requests.items() if metadata[c]['partition']==p}
    train_truth=labels.read('train','fit')
    state=fit([dict(partition='train',request=r.as_dict(),targets=train_truth[c]) for c,r in inputs('train').items()],
              json.loads((root/'transfer.json').read_text()))
    write(root/'models.json',state)
    events.append(dict(event='training_complete',sha256=sha(root/'models.json'),frozen_transfer_refitted=False))
    validation=labels.read('validation','select')
    selected=select(state,inputs('validation'),validation,metadata)
    interval_choices={}
    for h in HORIZONS:
        conf=selected['horizons'][str(h)]['configs']['adaptive_persistence']
        train_rows=records(inputs('train'),train_truth,metadata,state,conf,h)
        validation_rows=records(inputs('validation'),validation,metadata,state,conf,h)
        interval_choices[str(h)]=choose(train_rows,validation_rows)
    selected['interval_choices']=interval_choices
    write(root/'selection.json',selected)
    events.append(dict(event='point_and_interval_selection_frozen',sha256=sha(root/'selection.json')))
    calibration_truth=labels.read('calibration','calibrate')
    calibration={}
    for h in HORIZONS:
        conf=selected['horizons'][str(h)]['configs']['adaptive_persistence']
        rs=records(inputs('calibration'),calibration_truth,metadata,state,conf,h)
        calibration[str(h)]={kind:build(rs,kind,'calibration') for kind in KINDS}
    write(root/'calibration.json',dict(status=STATUS,horizons=calibration,selection_partition='validation',calibration_partition='calibration'))
    events.append(dict(event='calibration_frozen',sha256=sha(root/'calibration.json')))
    predictions=[]
    for part in ('test','ood'):
        for cid,r in inputs(part).items():
            f=features(r)
            for h in HORIZONS:
                for method in METHODS:
                    conf=selected['horizons'][str(h)]['configs'][method]
                    p=predict(r,state,conf,h);intervals={};raw_intervals={}
                    if method=='adaptive_persistence':
                        for kind in KINDS:
                            q=apply(p['point'],f['current'],f['model_scale'],calibration[str(h)][kind])
                            intervals[kind]=q['quantiles'];raw_intervals[kind]=q['raw']
                        chosen=interval_choices[str(h)]['chosen']
                        q=apply(p['point'],f['current'],f['model_scale'],calibration[str(h)][chosen['kind']],chosen['widen'])
                        intervals['selected_calibration']=q['quantiles'];raw_intervals['selected_calibration']=q['raw']
                    if method=='frozen_phase6_2':
                        radius=state['transfer']['calibration']['normalized_absolute_radius']['selected/'+str(h)]*f['model_scale']
                        raw=[p['point']-radius,p['point'],p['point']+radius]
                        intervals['frozen_phase6_2_interval']=[max(0.,v) for v in raw];raw_intervals['frozen_phase6_2_interval']=raw
                    p.update(method=method,partition=part,family=metadata[cid]['family'],intervals=intervals,raw_intervals=raw_intervals)
                    predictions.append(p)
    write(root/'predictions.json',predictions);prediction_seal(root)
    events.append(dict(event='test_predictions_sealed',sha256=sha(root/'prediction_seal.json'),test_targets_opened=False))
    predictions=validate_predictions(root,requests,metadata,selected)
    truth={**labels.read('test','score'),**labels.read('ood','score')}
    diagnostics=labels.read('diagnostics','score')
    rows=[];interval_rows=[]
    for p in predictions:
        cid,h=p['case_id'],p['horizon'];f=features(requests[cid]);target=truth[cid][str(h)]
        if target['timestamp_utc']!=requests[cid].endpoint(h): raise ValueError('Wrong exact target')
        row=dict(method=p['method'],partition=p['partition'],family=p['family'],case_id=cid,request_id=p['request_id'],
                 horizon=h,current=f['current'],actual=target['value'],prediction=p['point'],raw_stock=p['raw_stock'],
                 metric_scale=f['metric_scale'],model_scale=f['model_scale'],
                 binary_change_probability=p['binary_change_probability'],direction_probabilities=p['direction_probabilities'],
                 return_to_origin=diagnostics[cid]['endpoint_return_with_interim_change'])
        rows.append(row)
        for kind,q in p['intervals'].items():
            interval_rows.append(dict(row,kind=kind,quantiles=q))
    write(root/'scored_rows.json',rows);write(root/'interval_rows.json',interval_rows)
    result=summarize(rows,interval_rows,selected);write(root/'metrics.json',result)
    repeated=[predict(requests[p['case_id']],state,selected['horizons'][str(p['horizon'])]['configs'][p['method']],p['horizon']) for p in predictions]
    keys=set(repeated[0]);identical=all(q=={k:p[k] for k in keys} for q,p in zip(repeated,predictions))
    if not identical: raise ValueError('Nonrepeatable lightweight forecasts')
    write(root/'repeatability.json',dict(status='PASS',scope=STATUS,predictions=len(repeated),sha256=digest(repeated),frozen_state_unchanged=True))
    verify(root);verify_prediction_seal(root);write(root/'events.json',events)
    return dict(status='PASS',scope=STATUS,forecasts=len(predictions),failures=0,
                native_pretrained_calls=0,old_experiment_runs=0,old_state_refits=0,metrics_sha256=sha(root/'metrics.json'))


def main(path):
    root=safe(path);start=time.monotonic();failure=None;outcome=None
    def deny(*args,**kwargs): raise RuntimeError('NETWORK_DISABLED_PHASE6_3')
    socket.socket.connect=deny;socket.create_connection=deny
    try:
        outcome=execute(root)
    except BaseException as exc:
        failure=dict(type=type(exc).__name__,message=str(exc)[:2000]);traceback.print_exc();raise
    finally:
        usage=resource.getrusage(resource.RUSAGE_SELF)
        write(root/'worker_resources.json',dict(status='FAIL' if failure else 'PASS',failure=failure,
              wall_seconds=time.monotonic()-start,peak_rss_bytes=usage.ru_maxrss*1024,
              cpu_user_seconds=usage.ru_utime,cpu_system_seconds=usage.ru_stime,
              affinity=sorted(os.sched_getaffinity(0)),threads=Path('/proc/self/status').read_text().split('Threads:')[1].splitlines()[0].strip(),
              env={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','CUDA_VISIBLE_DEVICES')},
              observability='finally on ordinary exceptions; supervisor evidence only on abrupt kill'))
        if outcome: write(root/'outcome.json',outcome)


if __name__=='__main__': main(sys.argv[1])
