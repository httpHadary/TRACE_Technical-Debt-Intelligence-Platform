"""Independent read-only arithmetic/identity audit; never fit or forecast a model."""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import math
import statistics as st
import sys
from forecasting_research.phase6_0.artifacts import sha
from forecasting_research.phase6_0.contracts import Request,digest,canonical
from forecasting_research.phase6_3.study import verify,verify_prediction_seal,TRANSFER_HASHES,LIMITS
from forecasting_research.phase6_3.models import METHODS,configs


def close(a,b):
    if a is None or b is None:
        if a is not b: raise ValueError('Undefined metric mismatch')
    elif not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10): raise ValueError('Metric mismatch')


def audit(root):
    root=Path(root);registration=verify(root);verify_prediction_seal(root)
    load=lambda n:json.loads((root/n).read_text())
    manifest=load('artifact_manifest.json')
    for name,expected in manifest['artifacts'].items():
        if sha(root/name)!=expected: raise ValueError('Changed artifact: '+name)
    reqs={c:Request.from_dict(r) for c,r in load('requests.json').items()}
    meta={r['case_id']:r for r in load('population.json')}
    state,selection=load('models.json'),load('selection.json')
    if digest(state)!=selection['state_sha256']: raise ValueError('Changed selected state')
    train=[r.as_dict() for c,r in reqs.items() if meta[c]['partition']=='train']
    if state['training_requests_sha256']!=digest(train) or state['train_n']!=384:
        raise ValueError('Incorrect new training population')
    for key,name in [('model','models.json'),('selection','selection.json'),('calibration','calibration.json')]:
        raw=canonical(state['transfer'][key])+b'\n'
        if hashlib.sha256(raw).hexdigest()!=TRANSFER_HASHES[name]: raise ValueError('Altered frozen transfer component')
    if state['binary_new_fit']['train_requests_sha256']==state['transfer']['model']['train_requests_sha256']:
        raise ValueError('New fit silently substituted for frozen state')
    predicted,scored=load('predictions.json'),load('scored_rows.json')
    expected={(m,c,h) for c,r in meta.items() if r['partition'] in ('test','ood') for m in METHODS for h in (30,60,90)}
    index=lambda rows:{(r['method'],r['case_id'],r['horizon']):r for r in rows}
    pindex,sindex=index(predicted),index(scored)
    if len(pindex)!=len(predicted) or len(sindex)!=len(scored) or set(pindex)!=expected or set(sindex)!=expected:
        raise ValueError('Nonmatching case/horizon populations')
    truth={**load('test_targets.json'),**load('ood_targets.json')}
    history_scale={c:st.mean(v for v in r.values if v is not None) for c,r in reqs.items()}
    for key,p in pindex.items():
        method,c,h=key;r=reqs[c];z=sindex[key];target=truth[c][str(h)]
        conf=selection['horizons'][str(h)]['configs'][method]
        if (p['request_id']!=r.identity or z['request_id']!=r.identity or p['timestamp_utc']!=r.endpoint(h)
                or target['timestamp_utc']!=r.endpoint(h) or z['actual']!=target['value'] or z['prediction']!=p['point']
                or z['current']!=r.values[-1] or p['config_sha256']!=digest(conf)
                or z['metric_scale']!=history_scale[c] or z['model_scale']!=max(1.,history_scale[c])
                or p['raw_signed_delta']!=p['raw_stock']-r.values[-1] or p['point']!=max(0.,p['raw_stock'])):
            raise ValueError('Prediction/source/target/config mismatch')
    metrics=load('metrics.json');checks=0
    for metric in metrics['aggregate']:
        rows=[r for r in scored if r['method']==metric['method'] and r['partition']==metric['partition'] and r['horizon']==metric['horizon']
              and (metric['scale']=='all' or r['family']!='mixed_scale')]
        def keep(r):
            d=r['actual']-r['current'];large=max(10,.2*r['current']);s=metric['stratum']
            return (s=='all' or s=='unchanged' and d==0 or s=='changed' and d!=0 or s=='increase' and d>0 or s=='decrease' and d<0
                    or s=='large_increase' and d>=large or s=='large_decrease' and d<=-large or s=='return_to_origin' and r['return_to_origin'])
        rows=[r for r in rows if keep(r)]
        if len(rows)!=metric['n']: raise ValueError('Stratum count mismatch')
        if not rows:
            close(metric['mae'],None);continue
        errors=[r['prediction']-r['actual'] for r in rows]
        mae=st.mean(abs(e) for e in errors);base=st.mean(abs(r['current']-r['actual']) for r in rows)
        close(metric['mae'],mae);close(metric['rmse'],math.sqrt(st.mean(e*e for e in errors)))
        close(metric['bias'],st.mean(errors));close(metric['median_absolute_error'],st.median(abs(e) for e in errors))
        close(metric['persistence_skill'],1-mae/base if base else None)
        groups=defaultdict(list);scaled=defaultdict(list);normbase=defaultdict(list);floored=defaultdict(list)
        for r in rows:
            error=abs(r['prediction']-r['actual']);f=r['family'];groups[f].append(error)
            floored[f].append(error/r['model_scale'])
            if r['metric_scale']:
                scaled[f].append(error/r['metric_scale']);normbase[f].append(abs(r['current']-r['actual'])/r['metric_scale'])
        macro=lambda g:st.mean(st.mean(v) for v in g.values()) if g else None
        close(metric['equal_family_macro_mae'],macro(groups));close(metric['normalized_mae'],macro(scaled))
        close(metric['model_scale_normalized_mae'],macro(floored))
        b=macro(normbase);close(metric['normalized_persistence_skill'],1-macro(scaled)/b if b else None)
        if metric['zero_denominators']!=sum(r['metric_scale']==0 for r in rows): raise ValueError('Zero denominator mismatch')
        checks+=9
    events=load('events.json');names=[r['event'] for r in events];sealed=names.index('test_predictions_sealed')
    if not names.index('training_complete')<names.index('point_and_interval_selection_frozen')<names.index('calibration_frozen')<sealed:
        raise ValueError('Training/selection/calibration/seal chronology mismatch')
    for i,event in enumerate(events):
        if event.get('partition') in ('test','ood','diagnostics') and (i<=sealed or not event['prediction_seal_verified']):
            raise ValueError('Future access before seal')
    for family in registration['policy']['ood_families']:
        for h in (30,60,90):
            rows=[r for r in scored if r['method']=='persistence' and r['partition']=='ood' and r['horizon']==h and r['family']==family]
            counts=[sum(r['actual']==r['current'] for r in rows),sum(r['actual']>r['current'] for r in rows),sum(r['actual']<r['current'] for r in rows)]
            if counts!=[10,5,5]: raise ValueError('OOD missing registered endpoint classes')
    resource=load('worker_resources.json');supervisor=load('supervisor.json')
    if (supervisor['status']!='PASS' or supervisor['exit_code']!=0 or resource['failure'] is not None
            or max(resource['peak_rss_bytes'],supervisor['sampled_peak_rss_bytes'])>LIMITS['rss_bytes']
            or resource['wall_seconds']>900 or int(resource['threads'])>2): raise ValueError('Resource/result gate failed')
    targets=[]
    for part in ('test','ood'):
        for h in (30,60,90):
            get=lambda method,stratum='all':next(r for r in metrics['aggregate'] if r['method']==method and r['horizon']==h and r['partition']==part and r['scale']=='all' and r['stratum']==stratum)
            ap=get('adaptive_persistence');unch=get('adaptive_persistence','unchanged');down=get('adaptive_persistence','large_decrease');changed=get('adaptive_persistence','changed')
            interval=next(r for r in metrics['intervals'] if r['kind']=='selected_calibration' and r['horizon']==h and r['partition']==part and r['stratum']=='all')
            shared=next(r for r in metrics['intervals'] if r['kind']=='shared_symmetric' and r['horizon']==h and r['partition']==part and r['stratum']=='all')
            targets.append(dict(partition=part,horizon=h,
                full_normalized_skill=ap['normalized_persistence_skill'],positive_normalized_skill=(ap['normalized_persistence_skill']>0 if part=='test' else ap['normalized_persistence_skill']>=0),
                unchanged_model_scale_mae=unch['model_scale_normalized_mae'],unchanged_protection_pass=unch['n']>=8 and unch['model_scale_normalized_mae']<=.02,
                changed_normalized_skill=changed['normalized_persistence_skill'],changed_skill_pass=changed['normalized_persistence_skill']>=0,
                large_decrease_raw_skill=down['persistence_skill'],large_decrease_normalized_skill=down['normalized_persistence_skill'],
                large_decrease_safety_pass=down['n']>=8 and down['persistence_skill']>=-.05 and down['normalized_persistence_skill']>=-.05,
                interval_coverage=interval['coverage80'],interval_normalized_width=interval['normalized_width'],
                interval_quality_pass=.75<=interval['coverage80']<=.85 and interval['normalized_width']<=2 and interval['normalized_interval_score']<=shared['normalized_interval_score']))
    return dict(status='PASS',scope='SYNTHETIC_ENGINEERING_TEST',registration_sha256=sha(root/'registration.json'),
                predictions=len(predicted),independent_arithmetic_checks=checks,files_rehashed=len(manifest['artifacts']),
                seal_before_test_labels=True,frozen_transfer_identity_verified=True,old_experiment_runs=0,native_pretrained_calls=0,
                research_targets=targets,experiment_validity_is_distinct_from_performance=True)


if __name__=='__main__': print(json.dumps(audit(sys.argv[1]),sort_keys=True))
