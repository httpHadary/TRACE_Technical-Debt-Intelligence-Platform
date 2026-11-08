"""Independent stdlib arithmetic auditor. Reads new synthetic artifacts only."""
import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics as st


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(p):
    if p.is_symlink() or p.stat().st_size>16*1024**2:raise ValueError('Invalid bounded artifact')
    return json.loads(p.read_bytes())
def close(a,b):
    if not math.isclose(a,b,abs_tol=1e-9,rel_tol=1e-11):raise ValueError(f'Numerical mismatch: {a} versus {b}')
def dt(t):return datetime.strptime(t,'%Y-%m-%dT%H:%M:%SZ')
def ols(points):
    if len(points)<2:return 0.
    x=st.mean(a for a,b in points);y=st.mean(b for a,b in points);den=sum((a-x)**2 for a,b in points)
    return sum((a-x)*(b-y) for a,b in points)/den if den else 0.


def audit(path):
    root=Path(path)
    if root.is_symlink() or not root.is_dir():raise ValueError('Real task directory required')
    reg=load(root/'registration.json');checks=0;files=0;predictions=0;pairchecks=0
    for name,expected in reg['artifacts'].items():
        if Path(name).name!=name or sha(root/name)!=expected:raise ValueError('Input artifact mismatch')
        files+=1
    repository=Path(__file__).resolve().parents[1]
    for name,expected in reg['source_sha256'].items():
        if Path(name).name!=name or sha(repository/'forecasting_research/phase6_5'/name)!=expected:raise ValueError('Code changed')
    for key,name in [('protocol_sha256','PHASE_6_5_PREREGISTRATION.md'),('audit_tool_sha256','tools/verify_phase6_5.py'),('tests_sha256','tests/test_phase6_5_information.py')]:
        if sha(repository/name)!=reg[key]:raise ValueError('Protocol/test/auditor changed')
    metrics=load(root/'metrics.json');events=load(root/'events.json')
    for seed in reg['replicas']:
        es=[v for v in events if v.get('seed')==seed]
        seal_event=next(v['sequence'] for v in es if v['event']=='FINAL_PREDICTIONS_SEALED')
        if not all(v['sequence']>seal_event for v in es if v['event']=='FINAL_LABELS_OPENED'):raise ValueError('Labels opened prematurely')
        seal=load(root/f'{seed}.prediction_seal.json')
        if seal['registration_sha256']!=sha(root/'registration.json'):raise ValueError('Registration mismatch')
        required={f'{seed}.{r}.predictions.json' for r in reg['final_populations']}|{f'{seed}.{s}.json' for s in ('model','selection','calibration')}
        if set(seal['files'])!=required:raise ValueError('Incomplete seal')
        for name,expected in seal['files'].items():
            if Path(name).name!=name or sha(root/name)!=expected:raise ValueError('State/prediction tampering')
            files+=1
        state=load(root/f'{seed}.model.json');selection=load(root/f'{seed}.selection.json');calibration=load(root/f'{seed}.calibration.json')
        if state['fit_role']!='train':raise ValueError('Training role wrong')
        training=load(root/f'{seed}.train.requests.json')
        if state['train_requests_sha256']!=digest(training):raise ValueError('Training identity changed')
        for h in reg['horizons']:
            for policy in ('local','stress'):
                s=selection[str(h)][policy];choices=[]
                for c in s['search']:
                    r=c['risk'];eligible=c['shrink']>0 and r['safe'] and r['skill'] is not None and r['skill']>.02
                    if policy=='stress':eligible=eligible and all(z['safe'] and z['score']<=z['base'] for z in c['stress_risks'])
                    if bool(c['eligible'])!=bool(eligible):raise ValueError('Selection eligibility mismatch')
                    if eligible:choices.append(c)
                expected=min(choices,key=lambda c:(c['risk']['score'],c['shrink']))['shrink'] if choices else 0.
                if expected!=s['shrink']:raise ValueError('Unsafe fallback/selection')
        references={}
        for role in reg['final_populations']:
            reqs=load(root/f'{seed}.{role}.requests.json');lookup={r['debt']['case_id']:r for r in reqs}
            labels=load(root/f'{seed}.{role}.targets.json');meta=load(root/f'{seed}.{role}.metadata.json')
            ps=load(root/f'{seed}.{role}.predictions.json');keys=set();grouped=defaultdict(list)
            features={}
            for cid,req in lookup.items():
                d=req['debt'];origin=dt(d['origin_utc']);current=d['values'][-1];scale=max(1.,current)
                obs=[((dt(t)-origin).total_seconds()/86400,v) for t,v in zip(d['timestamps'],d['values']) if v is not None]
                gradient=ols([(t,v) for t,v in obs if t>=-30]);sgn=0 if abs(gradient)/scale<.0002 else 1 if gradient>0 else -1
                features[cid]=(current,scale,obs,sgn)
            for p in ps:
                cid=p['case_id'];h=p['horizon'];method=p['method'];k=(cid,h,method)
                if k in keys:raise ValueError('Duplicate prediction')
                keys.add(k);req=lookup[cid];current,scale,obs,sgn=features[cid]
                if p['request_id']!=digest(req) or p['timestamp_utc']!=labels[cid][str(h)]['timestamp_utc']:raise ValueError('Wrong forecast identity')
                channel='history' if method=='history_median' else 'activity' if method=='activity_median' else 'intent'
                a=selection[str(h)]['local' if method=='adaptive_local' else 'stress']['shrink'] if method.startswith('adaptive_') else 1.
                delta=0.
                if method=='rolling_mean':delta=st.mean(v for t,v in obs[-7:])-current
                elif method=='anchored_trend':delta=h*ols([(t,v) for t,v in obs if t>=-90])
                elif method!='persistence' and current!=0:
                    value=None
                    if channel=='history':value=str(sgn)
                    else:
                        name='observed_activity' if channel=='activity' else 'declared_intent'
                        for signal in req['signals']:
                            if signal['name']==name and signal['horizon']==h and signal['complete'] and signal['value'] is not None and signal['available_utc']<=req['debt']['origin_utc']:
                                value=str(int(signal['value']>=5) if channel=='activity' else signal['value'])
                    values=state['cells'].get(f'{channel}:{h}',{}).get(value,[])
                    if len(values)>=30:delta=a*scale*sorted(values)[math.ceil(len(values)/2)-1]
                close(p['raw_delta'],delta);close(p['point'],max(0.,current+delta));checks+=2
                radius=calibration[f'{method}:{h}']*scale
                close(p['lo'],max(0.,p['point']-radius));close(p['hi'],p['point']+radius);checks+=2
                if role in ('test','hidden','reversed'):
                    if role=='test':references[k]=p['point']
                    elif p['point']!=references[k]:raise ValueError('Hidden future leaked into predictions')
                    else:pairchecks+=1
                actual=labels[cid][str(h)]['value'];grouped[(method,h)].append((p['point'],actual,current,scale,meta[cid]['family']))
                predictions+=1
            if len(keys)!=len(reqs)*len(reg['methods'])*len(reg['horizons']):raise ValueError('Incomplete population')
            for (method,h),rows in grouped.items():
                reported=next(m['strata']['all'] for m in metrics if (m['replica'],m['partition'],m['method'],m['horizon'])==(seed,role,method,h))
                if reported['n']!=len(rows):raise ValueError('Metric population mismatch')
                close(reported['mae'],st.mean(abs(a-y) for a,y,c,s,f in rows));checks+=1
                fam=defaultdict(list)
                for a,y,c,s,f in rows:fam[f].append(abs(a-y)/s)
                close(reported['normalized_mae'],st.mean(st.mean(v) for v in fam.values()));checks+=1
    return dict(status='PASS',scope=reg['status'],predictions_verified=predictions,independent_arithmetic_checks=checks,
                paired_hidden_world_equalities=pairchecks,input_state_prediction_files_rehashed=files,
                real_world_predictive_value='NOT_ESTABLISHED',source_and_protocol_verified=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path');a=p.parse_args();print(json.dumps(audit(a.path),sort_keys=True))
