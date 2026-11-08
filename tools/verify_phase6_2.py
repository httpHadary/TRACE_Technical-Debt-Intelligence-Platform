"""Read-only audit of Phase6.2 synthetic outputs; no fitting or inference."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import math
import statistics as st
import sys
from forecasting_research.phase6_0.artifacts import sha
from forecasting_research.phase6_0.contracts import Request, digest
from forecasting_research.phase6_2.study import verify, verify_prediction_seal, LIMITS
from forecasting_research.phase6_2.features import extract
from forecasting_research.phase6_2.models import METHODS
from forecasting_research.phase6_2 import HORIZONS, STATUS, VERSION


def close(a, b):
    if a is None or b is None:
        if a is not b:
            raise ValueError('Undefined metric mismatch')
    elif not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10):
        raise ValueError(f'Metric mismatch {a} vs {b}')


def audit(root):
    root = Path(root)
    registration = verify(root)
    verify_prediction_seal(root)
    manifest = json.loads((root/'artifact_manifest.json').read_text())
    for name, expected in manifest['artifacts'].items():
        if sha(root/name) != expected:
            raise ValueError('Artifact changed: '+name)
    load = lambda name:json.loads((root/name).read_text())
    requests = {cid:Request.from_dict(r) for cid,r in load('requests.json').items()}
    population = {r['case_id']:r for r in load('population.json')}
    predictions, rows = load('predictions.json'),load('scored_rows.json')
    metrics, selection, models = load('metrics.json'),load('selection.json'),load('models.json')
    if digest(models) != selection['model_sha256']:
        raise ValueError('Selected model semantic hash mismatch')
    train = [req.as_dict() for cid,req in requests.items() if population[cid]['partition']=='train']
    if models['train_requests_sha256'] != digest(train) or models['train_n'] != 384:
        raise ValueError('Training request membership mismatch')
    expected = {(m,c,h) for c,meta in population.items() if meta['partition'] in ('test','ood') for m in METHODS for h in HORIZONS}
    def index(data):
        indexed = {(r['method'],r['case_id'],r['horizon']):r for r in data}
        if len(indexed) != len(data) or set(indexed) != expected:
            raise ValueError('Complete matched population required')
        return indexed
    prediction_index, scored_index = index(predictions),index(rows)
    schema = {'version','status','unit','case_id','request_id','horizon','timestamp_utc','config_sha256',
              'raw_signed_delta','raw_stock','point','p_change','mixture_raw_quantiles','mixture_quantiles',
              'method','partition','family','calibrated_quantiles'}
    test_truth = {**load('test_targets.json'),**load('ood_targets.json')}
    for key,pred in prediction_index.items():
        method,cid,h = key
        req,row = requests[cid],scored_index[key]
        actual = test_truth[cid][str(h)]
        if (set(pred) != schema or pred['request_id'] != req.identity or row['request_id'] != req.identity
                or pred['timestamp_utc'] != req.endpoint(h) or actual['timestamp_utc'] != req.endpoint(h)
                or row['actual'] != actual['value'] or row['prediction'] != pred['point']
                or row['metric_scale'] != extract(req)['metric_scale'] or row['current'] != req.values[-1]
                or pred['config_sha256'] != digest(selection['horizons'][str(h)]['configs'][method])
                or pred['raw_signed_delta'] != pred['raw_stock']-req.values[-1]
                or pred['point'] != max(0.,pred['raw_stock']) or pred['status'] != STATUS or pred['version'] != VERSION):
            raise ValueError('Prediction/target/source/config identity mismatch')
    checks = 0
    for metric in metrics['aggregate']:
        subset = [r for r in rows if r['method']==metric['method'] and r['partition']==metric['partition'] and r['horizon']==metric['horizon']
                  and (metric['scale']=='all' or r['family']!='mixed_scale')]
        stratum = metric['stratum']
        def keep(r):
            delta=r['actual']-r['current'];large=max(10,.2*r['current'])
            return (stratum=='all' or stratum=='unchanged' and delta==0 or stratum=='changed' and delta!=0
                    or stratum=='large_increase' and delta>=large or stratum=='large_decrease' and delta<=-large)
        subset = [r for r in subset if keep(r)]
        if len(subset) != metric['n']:
            raise ValueError('Stratum population mismatch')
        if not subset:
            close(None,metric['mae']);continue
        errors = [r['prediction']-r['actual'] for r in subset]
        mae=st.mean(abs(e) for e in errors)
        close(mae,metric['mae'])
        close(math.sqrt(st.mean(e*e for e in errors)),metric['rmse'])
        close(st.median(abs(e) for e in errors),metric['median_absolute_error'])
        close(st.mean(errors),metric['bias'])
        persistence=st.mean(abs(r['current']-r['actual']) for r in subset)
        close(1-mae/persistence if persistence else None,metric['persistence_skill'])
        families=defaultdict(list);scaled=defaultdict(list)
        for r in subset:
            families[r['family']].append(abs(r['prediction']-r['actual']))
            if r['metric_scale']:
                scaled[r['family']].append(abs(r['prediction']-r['actual'])/r['metric_scale'])
        close(st.mean(st.mean(v) for v in families.values()),metric['equal_family_macro_mae'])
        close(st.mean(st.mean(v) for v in scaled.values()) if scaled else None,metric['normalized_mae'])
        if metric['zero_denominators'] != sum(r['metric_scale']==0 for r in subset):
            raise ValueError('Zero denominator accounting mismatch')
        checks += 7
    events = load('events.json')
    names = [e['event'] for e in events]
    seal_index = names.index('test_predictions_sealed')
    for i,e in enumerate(events):
        if e.get('partition') in ('test','ood') and e['event']=='labels_read':
            if i <= seal_index or not e['prediction_seal_verified']:
                raise ValueError('Test label access before prediction seal')
    if not names.index('training_complete') < names.index('selection_frozen') < seal_index:
        raise ValueError('Fitting/selection/sealing chronology mismatch')
    receipt = load('supervisor.json')
    worker = load('worker_resources.json')
    if (receipt['status'] != 'PASS' or receipt['exit_code'] != 0 or worker['failure'] is not None
            or worker['peak_rss_bytes'] > LIMITS['rss_bytes'] or worker['wall_seconds'] > LIMITS['wall_seconds']
            or int(worker['threads']) > 2 or receipt['sampled_peak_rss_bytes'] > LIMITS['rss_bytes']):
        raise ValueError('Worker/resource receipt failed')
    return dict(status='PASS',scope=STATUS,registration_sha256=sha(root/'registration.json'),
                artifact_files_verified=len(manifest['artifacts']),prediction_rows=len(predictions),
                scored_rows=len(rows),independent_metric_arithmetic_checks=checks,
                forecast_counts=dict(Counter(r['partition'] for r in predictions)),
                seal_before_test_labels=True,model_training_partition_verified=True,
                full_matching_population=True,native_pretrained_calls=0,raw_historical_labels_opened=0)


if __name__ == '__main__':
    print(json.dumps(audit(sys.argv[1]),sort_keys=True))
