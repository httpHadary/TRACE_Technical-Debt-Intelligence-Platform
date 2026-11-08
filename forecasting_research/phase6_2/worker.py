"""One synthetic-only numerical worker; finally receipts survive ordinary errors."""
from pathlib import Path
import json
import os
import resource
import socket
import sys
import time
import traceback
import numpy as np
from forecasting_research.phase6_0.artifacts import write, sha
from forecasting_research.phase6_0.contracts import Request, digest
from . import HORIZONS, STATUS
from .features import extract
from .models import fit, configs, predict, METHODS
from .study import verify, Labels, prediction_seal, verify_prediction_seal, safe
from .evaluation import summarize, classification_metrics, mean


def selection_score(requests, predictions, actuals, metadata):
    groups = {}
    for cid, pred in predictions.items():
        scale = extract(requests[cid])['model_scale']
        family = metadata[cid]['family']
        groups.setdefault(family, []).append(abs(pred['point']-actuals[cid])/scale)
    return mean(mean(values) for values in groups.values())


def select(state, requests, targets, metadata, partition='validation'):
    if partition != 'validation':
        raise ValueError('Selection requires validation, never test/calibration labels')
    selection, scores = {}, []
    for horizon in HORIZONS:
        actuals = {cid:row[str(horizon)]['value'] for cid,row in targets.items()}
        heads, method_scores = {}, {}
        for method in METHODS[:-1]:
            best = None
            for config in configs(method):
                predictions = {cid:predict(req,state,config,horizon) for cid,req in requests.items()}
                score = selection_score(requests,predictions,actuals,metadata)
                scores.append(dict(horizon=horizon, config=config, validation_score=score))
                if best is None or score < best[0]:
                    best = (score,config)
            method_scores[method], heads[method] = best
        champion = min(METHODS[:-1], key=lambda name:method_scores[name])
        heads['selected'] = heads[champion]
        selection[str(horizon)] = dict(configs=heads, champion=champion, validation_scores=method_scores)
    return dict(status=STATUS, fit_partition='train', selection_partition='validation',
                horizons=selection, search_scores=scores, test_accessed=False,
                model_sha256=digest(state), frozen=True)


def calibrate(state, selected, requests, targets, partition='calibration'):
    if partition != 'calibration':
        raise ValueError('Separate calibration partition required')
    output = {}
    for horizon in HORIZONS:
        for method in METHODS:
            conf = selected['horizons'][str(horizon)]['configs'][method]
            residuals = [abs(predict(req,state,conf,horizon)['point']-targets[cid][str(horizon)]['value'])/extract(req)['model_scale']
                         for cid,req in requests.items()]
            output[method+'/'+str(horizon)] = float(np.quantile(residuals,.8,method='higher'))
    return dict(partition='calibration', nominal=.8, normalized_absolute_radius=output,
                method='empirical higher 0.8 quantile, no conformal coverage guarantee', test_accessed=False)


def validate_predictions(root, requests, metadata, selected):
    verify_prediction_seal(root)
    predictions = json.loads((root/'predictions.json').read_text())
    expected = {(m,c,h) for c,v in metadata.items() if v['partition'] in ('test','ood') for m in METHODS for h in HORIZONS}
    actual = set()
    for pred in predictions:
        key = (pred['method'],pred['case_id'],pred['horizon'])
        if key in actual or key not in expected:
            raise ValueError('Incomplete, duplicate or unregistered prediction population')
        actual.add(key)
        req = requests[pred['case_id']]
        conf = selected['horizons'][str(pred['horizon'])]['configs'][pred['method']]
        if (pred['request_id'] != req.identity or pred['config_sha256'] != digest(conf)
                or pred['timestamp_utc'] != req.endpoint(pred['horizon']) or pred['status'] != STATUS
                or pred['partition'] != metadata[pred['case_id']]['partition']
                or pred['family'] != metadata[pred['case_id']]['family']
                or pred['point'] != max(0.,pred['raw_stock'])
                or pred['raw_signed_delta'] != pred['raw_stock']-req.values[-1]):
            raise ValueError('Prediction/input/config/stock identity mismatch')
        for kind in ('mixture_quantiles','calibrated_quantiles'):
            qs = pred[kind]
            if qs is not None and (len(qs)!=3 or not all(np.isfinite(qs)) or not 0<=qs[0]<=qs[1]<=qs[2]):
                raise ValueError('Invalid derived interval; no repair')
    if actual != expected:
        raise ValueError('Missing predictions, no selective-success scoring')
    return predictions


def execute(root):
    root = safe(root)
    reg = verify(root)
    events = [dict(event='registration_verified', sha256=sha(root/'registration.json'))]
    labels = Labels(root,events)
    requests = {c:Request.from_dict(r) for c,r in json.loads((root/'requests.json').read_text()).items()}
    metadata = {r['case_id']:r for r in json.loads((root/'population.json').read_text())}
    def inputs(partition):
        return {c:r for c,r in requests.items() if metadata[c]['partition']==partition}
    train_labels = labels.read('train','fit')
    state = fit([dict(partition='train',request=req.as_dict(),targets=train_labels[cid]) for cid,req in inputs('train').items()])
    write(root/'models.json',state)
    events.append(dict(event='training_complete',model_sha256=sha(root/'models.json')))
    selection = select(state,inputs('validation'),labels.read('validation','select'),metadata)
    write(root/'selection.json',selection)
    events.append(dict(event='selection_frozen',sha256=sha(root/'selection.json')))
    calibration = calibrate(state,selection,inputs('calibration'),labels.read('calibration','calibrate'))
    write(root/'calibration.json',calibration)
    forecasts = []
    for partition in ('test','ood'):
        for cid,req in inputs(partition).items():
            f = extract(req)
            for horizon in HORIZONS:
                for method in METHODS:
                    config = selection['horizons'][str(horizon)]['configs'][method]
                    pred = predict(req,state,config,horizon)
                    radius = calibration['normalized_absolute_radius'][method+'/'+str(horizon)]*f['model_scale']
                    pred.update(method=method,partition=partition,family=metadata[cid]['family'],
                                calibrated_quantiles=[max(0.,pred['point']-radius),pred['point'],pred['point']+radius])
                    forecasts.append(pred)
    write(root/'predictions.json',forecasts)
    prediction_seal(root)
    events.append(dict(event='test_predictions_sealed',sha256=sha(root/'prediction_seal.json'),test_targets_opened=False))
    predictions = validate_predictions(root,requests,metadata,selection)
    test_labels = {**labels.read('test','score'),**labels.read('ood','score')}
    rows, classified = [], []
    for pred in predictions:
        cid,h = pred['case_id'],pred['horizon']
        actual = test_labels[cid][str(h)]
        req = requests[cid]
        if actual['timestamp_utc'] != req.endpoint(h):
            raise ValueError('Exact target timestamp mismatch')
        f = extract(req)
        rows.append(dict(method=pred['method'],case_id=cid,request_id=req.identity,partition=pred['partition'],
                         family=pred['family'],horizon=h,actual=actual['value'],current=f['current'],
                         prediction=pred['point'],raw_stock=pred['raw_stock'],metric_scale=f['metric_scale'],
                         probability=pred['p_change'],calibrated_quantiles=pred['calibrated_quantiles'],
                         mixture_quantiles=pred['mixture_quantiles']))
    for partition in ('test','ood'):
        for h in HORIZONS:
            rs = [r for r in rows if r['method']=='hard_gate' and r['partition']==partition and r['horizon']==h]
            config = selection['horizons'][str(h)]['configs']['hard_gate']
            classified.append(dict(partition=partition,horizon=h,**classification_metrics(rs,config['threshold'])))
    write(root/'scored_rows.json',rows)
    result = summarize(rows,classified)
    write(root/'metrics.json',result)
    # Repeat inference over all frozen requests using the same state; no refit,
    # no future arguments, and no additional model/parameter selection.
    repeated = [predict(requests[p['case_id']],state,selection['horizons'][str(p['horizon'])]['configs'][p['method']],p['horizon']) for p in predictions]
    keys = set(repeated[0])
    identical = all(a == {k:p[k] for k in keys} for a,p in zip(repeated,predictions))
    if not identical:
        raise ValueError('Deterministic lightweight prediction repeat failed')
    write(root/'repeatability.json',dict(status='PASS',predictions_checked=len(repeated),models_refitted=False,
                                      prediction_digest=digest(repeated)))
    verify(root)
    verify_prediction_seal(root)
    write(root/'events.json',events)
    return dict(status='PASS',interpretation=STATUS,attempted=len(forecasts),failures=0,
                pretrained='NOT_EXECUTED',rights='24 NOT_APPROVED; unchanged',
                metrics_sha256=sha(root/'metrics.json'),reg=sha(root/'registration.json'))


def main(path):
    root = safe(path)
    start = time.monotonic()
    failure, outcome = None, None
    def deny(*args, **kwargs):
        raise RuntimeError('NETWORK_DISABLED_PHASE6_2')
    socket.socket.connect = deny
    socket.create_connection = deny
    try:
        outcome = execute(root)
    except BaseException as exc:
        failure = dict(type=type(exc).__name__, message=str(exc)[:2000])
        traceback.print_exc()
        raise
    finally:
        write(root/'worker_resources.json',dict(status='FAIL' if failure else 'PASS',failure=failure,
              wall_seconds=time.monotonic()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
              cpu_user_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime,
              cpu_system_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_stime,
              affinity=sorted(os.sched_getaffinity(0)),threads=Path('/proc/self/status').read_text().split('Threads:')[1].splitlines()[0].strip(),
              env={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','CUDA_VISIBLE_DEVICES')},
              observability='finally on ordinary exceptions; SIGKILL cannot execute Python finally; supervisor retains host observations'))
        if outcome:
            write(root/'outcome.json',outcome)


if __name__ == '__main__':
    main(sys.argv[1])
