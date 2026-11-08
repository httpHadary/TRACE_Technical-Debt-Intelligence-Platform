"""Read-only independent arithmetic, selection and population audit; no forecasting."""
from pathlib import Path
from collections import defaultdict
import json
import math
import statistics as st
import sys
from forecasting_research.phase6_0.artifacts import sha
from forecasting_research.phase6_0.contracts import Request,digest
from forecasting_research.phase6_4.study import verify,open_targets,LIMITS


def close(a,b):
    if a is None or b is None:
        if a is not b:raise ValueError('Null metric mismatch')
    elif not math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-9):raise ValueError(f'Arithmetic mismatch {a} != {b}')


def macro(rows,fn):
    groups=defaultdict(list)
    for r in rows:groups[r['family']].append(fn(r))
    return st.mean(st.mean(v) for v in groups.values()) if groups else None


def filter_rows(rows,stratum):
    out=[]
    for r in rows:
        d=r['actual']-r['current'];threshold=max(10,.2*r['current'])
        if (stratum=='all' or stratum=='unchanged' and d==0 or stratum=='changed' and d!=0
            or stratum=='large_decrease' and d<=-threshold or stratum=='large_increase' and d>=threshold
            or stratum=='excluding_extreme_scale' and r['scale_band']!=3):out.append(r)
    return out


def audit(root):
    root=Path(root);reg=verify(root)
    load=lambda name:json.loads((root/name).read_text())
    manifest=load('artifact_manifest.json')
    for name,h in manifest['artifacts'].items():
        if Path(name).name!=name or sha(root/name)!=h:raise ValueError('Artifact modified')
    methods=('persistence','rolling_mean','anchored_trend','direct_delta','local_median','adaptive_persistence','frozen_phase6_3')
    groups=defaultdict(list);events=load('events.json');checks=0;selections=[]
    for rep in reg['replicas']:
        state=load(f'{rep}.model.json');selected=load(f'{rep}.selection.json');search=load(f'{rep}.search.json')
        train=load(f'{rep}.train.requests.json')
        if state['train_requests_sha256']!=digest(list(train.values())) or set(state['training_ids'])!=set(train) or state['training_n']!=576:raise ValueError('Training identity mismatch')
        e=[r['event'] for r in events if r['replica']==rep]
        if e!=['TRAIN_FIT','VALIDATION_SELECTION_FROZEN','CALIBRATION_FROZEN','ALL_TEST_OOD_PREDICTIONS_SEALED','TEST_OOD_LABELS_OPENED_AFTER_SEAL']:raise ValueError('Invalid role chronology')
        for h in (30,60,90):
            scores=search[str(h)]
            if [r['config'] for r in scores]!=reg['configs']:raise ValueError('Search population changed')
            eligible=[r for r in scores[1:] if r['risk']['safe'] and r['risk']['score']<.98*r['risk']['base']]
            if eligible:
                best=min(r['risk']['score'] for r in eligible)
                expected=next(r for r in eligible if r['risk']['score']<=1.01*best)
            else:expected=scores[0]
            actual=selected[str(h)]
            if actual['config']!=expected['config'] or actual['admitted_adjustment']!=bool(eligible):raise ValueError('Unsafe or test-selected configuration')
            if not eligible and actual['config']['shrink']!=0:raise ValueError('Unprotected fallback')
            selections.append(dict(replica=rep,horizon=h,**actual))
        calibration=load(f'{rep}.calibration.json')
        for part in ('test','ood','identifiability'):
            truth=open_targets(root,rep,part)
            requests={k:Request.from_dict(v) for k,v in load(f'{rep}.{part}.requests.json').items()}
            metadata=load(f'{rep}.{part}.metadata.json');rows=load(f'{rep}.{part}.predictions.json')
            expected={(cid,h,m) for cid in requests for h in (30,60,90) for m in methods}
            got={(r['case_id'],r['horizon'],r['method']) for r in rows}
            if got!=expected or len(got)!=len(rows):raise ValueError('Dropped, duplicate or mismatched forecasts')
            request_info={cid:(r.identity,st.mean(v for v in r.values if v is not None)) for cid,r in requests.items()}
            identical={}
            for r in rows:
                cid=r['case_id'];h=r['horizon'];req=requests[cid];identity,scale=request_info[cid]
                if r['request_id']!=identity or r['timestamp_utc']!=req.endpoint(h) or truth[cid][str(h)]['timestamp_utc']!=req.endpoint(h):raise ValueError('Forecast identity or endpoint mismatch')
                if r['point']!=max(0.,r['raw_stock']) or not math.isfinite(r['point']) or r['current']!=req.values[-1]:raise ValueError('Invalid stock')
                if any(r[k]!=v for k,v in metadata[cid].items()):raise ValueError('Metadata changed')
                close(r['model_scale'],max(1.,scale));close(r['metric_scale'],scale)
                if r['method']=='adaptive_persistence':
                    p=r['direction_probabilities']
                    if len(p)!=3 or any(not math.isfinite(v) or v<0 or v>1 for v in p):raise ValueError('Invalid direction probabilities')
                    close(sum(p),1)
                    if selected[str(h)]['config']['shrink']==0 and r['point']!=r['current']:raise ValueError('Protected action moved')
                    radius=calibration[str(h)]['radius']*r['model_scale']
                    if r['calibrated_interval']!=[max(0,r['point']-radius),r['point']+radius]:raise ValueError('Calibration mapping changed')
                    for key in ('calibrated_interval','local_interval'):
                        lo,hi=r[key]
                        if not 0<=lo<=hi or not math.isfinite(hi):raise ValueError('Invalid interval')
                    if part=='identifiability':
                        key=(r['group'],h)
                        same=(r['point'],p,r['calibrated_interval'])
                        if key in identical and identical[key]!=same:raise ValueError('Hidden future leaked into predictions')
                        identical[key]=same
                row=dict(r,actual=truth[cid][str(h)]['value'])
                groups[(rep,part,h,r['method'])].append(row)
            checks+=len(rows)
    metric=load('metrics.json');arithmetic=0;targets=[]
    for m in metric['aggregate']:
        rs=filter_rows(groups[(m['replica'],m['partition'],m['horizon'],m['method'])],m['stratum'])
        if m['n']!=len(rs):raise ValueError('Stratum count mismatch')
        if not rs:close(m['mae'],None);continue
        errors=[r['point']-r['actual'] for r in rs]
        mae=st.mean(abs(x) for x in errors);base=st.mean(abs(r['current']-r['actual']) for r in rs)
        norm=macro(rs,lambda r:abs(r['point']-r['actual'])/r['model_scale'])
        normbase=macro(rs,lambda r:abs(r['current']-r['actual'])/r['model_scale'])
        close(m['mae'],mae);close(m['persistence_mae'],base);close(m['rmse'],math.sqrt(st.mean(x*x for x in errors)))
        close(m['bias'],st.mean(errors));close(m['median_absolute_error'],st.median(abs(x) for x in errors))
        close(m['normalized_mae'],norm);close(m['raw_skill'],1-mae/base if base else None)
        close(m['normalized_skill'],1-norm/normbase if normbase else None)
        pos=[r for r in rs if r['metric_scale']>0]
        un=macro(pos,lambda r:abs(r['point']-r['actual'])/r['metric_scale']);ub=macro(pos,lambda r:abs(r['current']-r['actual'])/r['metric_scale'])
        close(m['unfloored_normalized_skill'],1-un/ub if ub else None)
        if m['zero_denominator_count']!=len(rs)-len(pos):raise ValueError('Hidden denominator policy')
        arithmetic+=9
    for m in metric['intervals']:
        rs=filter_rows(groups[(m['replica'],m['partition'],m['horizon'],m['method'])],m['stratum'])
        if len(rs)!=m['n']:raise ValueError('Interval population mismatch')
        if not rs:continue
        qs=[r[m['kind']] for r in rs];width=[q[1]-q[0] for q in qs]
        close(m['coverage'],st.mean(q[0]<=r['actual']<=q[1] for r,q in zip(rs,qs)))
        close(m['mean_width'],st.mean(width));close(m['median_width'],st.median(width))
        close(m['mean_normalized_width'],st.mean(w/r['model_scale'] for r,w in zip(rs,width)))
        close(m['interval_score'],st.mean(q[1]-q[0]+10*max(0,q[0]-r['actual'])+10*max(0,r['actual']-q[1]) for r,q in zip(rs,qs)))
        arithmetic+=5
    for rep in reg['replicas']:
        for part in ('test','ood','identifiability'):
            for h in (30,60,90):
                rs=groups[(rep,part,h,'adaptive_persistence')]
                get=lambda s:next(m for m in metric['aggregate'] if (m['replica'],m['partition'],m['horizon'],m['method'],m['stratum'])==(rep,part,h,'adaptive_persistence',s))
                overall=get('all');unch=get('unchanged');down=get('large_decrease');up=get('large_increase')
                support=all(x['n']>=24 and x.get('families',0)>=2 for x in (unch,down,up))
                quality=support and unch.get('normalized_mae',math.inf)<=.01 and all(x.get('raw_skill',-math.inf) is not None and x.get('normalized_skill',-math.inf) is not None and x['raw_skill']>=-.02 and x['normalized_skill']>=-.02 for x in (down,up))
                better=overall['raw_skill']>0 and overall['normalized_skill']>0
                if part=='identifiability':better=overall['raw_skill']>=-.01 and overall['normalized_skill']>=-.01
                targets.append(dict(replica=rep,partition=part,horizon=h,adequate_support=support,
                    raw_skill=overall['raw_skill'],normalized_skill=overall['normalized_skill'],
                    performance_target=bool(quality and better),safety_quality=bool(quality)))
    supervisor=load('supervisor.json');resources=load('worker_resources.json')
    if supervisor['status']!='PASS' or resources['exit_code']!=0 or max(resources['peak_rss_bytes'],supervisor['sampled_peak_rss_bytes'])>LIMITS['rss_bytes'] or supervisor['wall_seconds']>900:raise ValueError('Runtime failed approved limits')
    return dict(status='PASS',scope='SYNTHETIC_ENGINEERING_TEST',predictions_verified=checks,
        independent_arithmetic_checks=arithmetic,files_rehashed=len(manifest['artifacts']),
        protected_fallback_verified=True,seals_before_label_access=True,selection=selections,
        research_targets=targets,consistent_forecasting_improvement=all(t['performance_target'] for t in targets if t['partition']!='identifiability'),
        identifiability_reliability=all(t['performance_target'] for t in targets if t['partition']=='identifiability'),
        complete_subgroup_support=all(t['adequate_support'] for t in targets),
        real_world_improvement='NOT_ESTABLISHED',new_real_data_used=False)


if __name__=='__main__':print(json.dumps(audit(sys.argv[1]),sort_keys=True,allow_nan=False))
