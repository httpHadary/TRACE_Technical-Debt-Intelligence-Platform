"""Register once, separate labels, seal predictions, then score only those seals."""
import json
import hashlib
import math
import os
import sys
import statistics as st
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from forecasting_research.phase6_0.contracts import digest, canonical
from . import VERSION, SCOPE, HORIZONS, REPLICAS
from .contracts import InformationRequest
from .population import population, delayed, FAMILIES, UNSEEN, COUNTS
from .model import Predictor, fit, past, select, quantile, SHRINKS, METHODS
from .evaluation import summaries, interval_metrics, paired_family_interval

ROOT=Path('/home/hp/tst/research/forecasting_mvp/phase6_5')
LIMITS=dict(rss_bytes=2*1024**3,wall_seconds=900,threads=2,output_bytes=128*1024**2,
            file_bytes=16*1024**2,log_bytes=8*1024**2)
FINAL=('test','unseen','hidden','reversed','delayed')

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def safe(path):
    p=Path(path)
    if not p.is_absolute() or '..' in p.parts or not p.is_relative_to(ROOT) or p==ROOT:
        raise ValueError('Exclusive phase6_5 outside-Git path required')
    for q in (p,*p.parents):
        if q.is_symlink():raise ValueError('Symlink output boundary')
    return p

def write(path,obj):
    raw=canonical(obj)+b'\n'
    if len(raw)>LIMITS['file_bytes']:raise ValueError('Bounded artifact exceeded')
    with Path(path).open('xb') as f:
        f.write(raw);f.flush();os.fsync(f.fileno())

def read(path):
    path=Path(path)
    if path.is_symlink() or path.stat().st_size>LIMITS['file_bytes']:raise ValueError('Invalid bounded artifact')
    return json.loads(path.read_bytes())

def source_identity():
    root=Path(__file__).parent
    return {p.name:sha(p) for p in sorted(root.glob('*.py'))}

def prepare(path):
    root=safe(path);root.mkdir(exist_ok=False)
    manifest={};history_roles={};ids=set()
    for seed in REPLICAS:
        for role in ('train','validation','calibration','test','unseen'):
            rows=population(seed,role)
            for r in rows:
                identity=r['request']['debt']['case_id'];hist=r['metadata']['history_sha256']
                if identity in ids:raise ValueError('Duplicate immutable case ID')
                ids.add(identity)
                # All-zero histories intentionally repeat; retain explicit counts,
                # disallow nonzero identical history crossing partition boundaries.
                if any(v not in (None,0) for v in r['request']['debt']['values']):
                    if hist in history_roles:raise ValueError('Cross-case duplicate nonzero history')
                    history_roles[hist]=[seed,role]
            versions=[(role,rows,'targets')]
            if role=='validation':versions += [('validation_hidden',rows,'hidden_targets'),('validation_reversed',rows,'reversed_targets')]
            if role=='test':versions += [('hidden',rows,'hidden_targets'),('reversed',rows,'reversed_targets'),('delayed',rows,'targets')]
            for name,rs,target_key in versions:
                requests=[];targets={};metadata={}
                for r in rs:
                    req=InformationRequest.from_dict(r['request'])
                    if name=='delayed':req=delayed(req)
                    requests.append(req.as_dict());key=req.debt.case_id
                    targets[key]=r[target_key];metadata[key]=r['metadata']
                for suffix,obj in [('requests',requests),('targets',targets),('metadata',metadata)]:
                    filename=f'{seed}.{name}.{suffix}.json';write(root/filename,obj);manifest[filename]=sha(root/filename)
    registration=dict(version=VERSION,status=SCOPE,replicas=REPLICAS,horizons=HORIZONS,
        methods=METHODS,shrinks=SHRINKS,families=FAMILIES,unseen_history_families=UNSEEN,counts_per_family=COUNTS,
        final_populations=FINAL,paired_future_interventions=['hidden','reversed','delayed'],
        case_entries_per_test=240,source_sha256=source_identity(),artifacts=manifest,limits=LIMITS,
        history_policy='Nonzero histories unique; all-zero histories intentionally repeated, not independent histories',
        normalization='max(1 minute,current observed stock); zero unfloored denominators counted/excluded',
        selection='validation equal-family normalized MAE >2% skill, <=.05 unchanged error, >=24 each sign, raw<=1.02 persistence; shrinks 0/.5/1',
        robust_selection='same rule plus no regret on paired validation hidden and reversed mechanisms',
        calibration='independent calibration absolute residual normalized 80th percentile; no guarantee under shift',
        hypotheses=dict(information='Synthetic origin intent can reduce error only under a declared predictive relationship',
                        unsigned='Activity can change risk without identifying direction',
                        hidden='Identical requests cannot distinguish different conditional future mechanisms'),
        forecasting_performance_claim='No real-data or universal improvement claim',
        protocol_sha256=sha(Path(__file__).parents[2]/'PHASE_6_5_PREREGISTRATION.md'),
        audit_tool_sha256=sha(Path(__file__).parents[2]/'tools/verify_phase6_5.py'),
        tests_sha256=sha(Path(__file__).parents[2]/'tests/test_phase6_5_information.py'),
        created_utc=datetime.now(timezone.utc).isoformat())
    write(root/'registration.json',registration)
    return read(root/'registration.json')

def verify(root):
    root=safe(root);reg=read(root/'registration.json')
    if reg['version']!=VERSION or reg['limits']!=LIMITS or reg['source_sha256']!=source_identity():raise ValueError('Registration/source identity changed')
    base=Path(__file__).parents[2]
    for key,name in [('protocol_sha256','PHASE_6_5_PREREGISTRATION.md'),('audit_tool_sha256','tools/verify_phase6_5.py'),('tests_sha256','tests/test_phase6_5_information.py')]:
        if sha(base/name)!=reg[key]:raise ValueError('Registered protocol/auditor/test changed')
    for name,expected in reg['artifacts'].items():
        if Path(name).name!=name or sha(root/name)!=expected:raise ValueError('Input identity changed')
    return reg

def open_labels(root,seed,role):
    if role in FINAL:
        seal=read(root/f'{seed}.prediction_seal.json')
        expected_names={f'{seed}.{r}.predictions.json' for r in FINAL}|{f'{seed}.{s}.json' for s in ('model','selection','calibration')}
        if set(seal['files'])!=expected_names:raise ValueError('Incomplete prediction seal')
        if seal['registration_sha256']!=sha(root/'registration.json'):raise ValueError('Registration seal mismatch')
        for name,expected in seal['files'].items():
            if Path(name).name!=name or sha(root/name)!=expected:raise ValueError('Prediction seal mismatch')
    return read(root/f'{seed}.{role}.targets.json')

def classify(rows):
    valid=[r for r in rows if r['direction_probabilities'] is not None]
    if not valid:return dict(n=0,status='UNAVAILABLE')
    confusion=[[0]*3 for _ in range(3)];brier=[]
    for r in valid:
        actual=0 if r['actual']==r['current'] else 1 if r['actual']>r['current'] else 2
        p=r['direction_probabilities'];pred=max(range(3),key=lambda i:p[i]);confusion[actual][pred]+=1
        brier.append(sum((v-(i==actual))**2 for i,v in enumerate(p)))
    f1=[]
    for c in range(3):
        tp=confusion[c][c];fp=sum(confusion[i][c] for i in range(3) if i!=c);fn=sum(confusion[c][i] for i in range(3) if i!=c)
        f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)
    return dict(n=len(valid),confusion=confusion,order=['stable','increase','decrease'],
                macro_f1=st.mean(v for v in f1 if v is not None),brier=st.mean(brier),
                probabilities='Empirical training frequencies, not certified posterior probabilities')

def execute(root):
    root=safe(root);verify(root);events=[]
    def event(name,**kw):events.append(dict(sequence=len(events),event=name,**kw))
    metrics=[];intervals=[];classification=[];paired=[];repeated=0
    for seed in REPLICAS:
        def requests(role):return [InformationRequest.from_dict(v) for v in read(root/f'{seed}.{role}.requests.json')]
        train=requests('train');labs=open_labels(root,seed,'train');meta=read(root/f'{seed}.train.metadata.json')
        rows=[dict(request=r.as_dict(),targets=labs[r.debt.case_id],metadata=meta[r.debt.case_id]) for r in train]
        state=fit(rows);write(root/f'{seed}.model.json',state);predictor=Predictor(state);event('TRAINED',seed=seed)
        vr=requests('validation');vl=open_labels(root,seed,'validation');vm=read(root/f'{seed}.validation.metadata.json')
        selections={}
        for h in HORIZONS:
            candidates={};hidden={};reverse={}
            for a in SHRINKS:
                cr=[];hr=[];rr=[]
                # Paired validation perturbations come from registered metadata
                # generation, not final labels. Saved separately during preparation.
                hlabels=read(root/f'{seed}.validation_hidden.targets.json')
                rlabels=read(root/f'{seed}.validation_reversed.targets.json')
                for req in vr:
                    pred=predictor.predict(req,h,'adaptive_local',a);f=past(req);cid=req.debt.case_id
                    base=dict(role='validation',point=pred['point'],current=f['current'],scale=f['scale'],family=vm[cid]['family'])
                    cr.append(dict(base,actual=vl[cid][str(h)]['value']))
                    hr.append(dict(base,actual=hlabels[cid][str(h)]['value']))
                    rr.append(dict(base,actual=rlabels[cid][str(h)]['value']))
                candidates[a]=cr;hidden[a]=hr;reverse[a]=rr
            selections[str(h)]=dict(local=select(candidates),stress=select(candidates,[hidden,reverse]))
        write(root/f'{seed}.selection.json',selections);event('SELECTION_FROZEN',seed=seed)
        # Calibration targets are read only after point state and selection freeze.
        cal=requests('calibration');cl=open_labels(root,seed,'calibration');radii={}
        def prediction(req,h,method):
            policy='local' if method=='adaptive_local' else 'stress'
            a=selections[str(h)][policy]['shrink'] if method.startswith('adaptive_') else 0.
            return predictor.predict(req,h,method,a)
        for method in METHODS:
            for h in HORIZONS:
                residual=[abs(prediction(req,h,method)['point']-cl[req.debt.case_id][str(h)]['value'])/past(req)['scale'] for req in cal]
                radii[f'{method}:{h}']=quantile(residual,.8)
        write(root/f'{seed}.calibration.json',radii);event('CALIBRATION_FROZEN',seed=seed)
        all_predictions={}
        for role in FINAL:
            out=[]
            for req in requests(role):
                for h in HORIZONS:
                    for method in METHODS:
                        pred=prediction(req,h,method);again=prediction(req,h,method)
                        if pred!=again:raise ValueError('Nondeterministic prediction')
                        repeated+=1;f=past(req);radius=radii[f'{method}:{h}']*f['scale']
                        out.append(dict(pred,lo=max(0.,pred['point']-radius),hi=pred['point']+radius))
            name=f'{seed}.{role}.predictions.json';write(root/name,out);all_predictions[role]=out
        protected={f'{seed}.{r}.predictions.json':sha(root/f'{seed}.{r}.predictions.json') for r in FINAL}
        for suffix in ('model','selection','calibration'):protected[f'{seed}.{suffix}.json']=sha(root/f'{seed}.{suffix}.json')
        write(root/f'{seed}.prediction_seal.json',dict(registration_sha256=sha(root/'registration.json'),files=protected))
        event('FINAL_PREDICTIONS_SEALED',seed=seed)
        for role in FINAL:
            labs=open_labels(root,seed,role);event('FINAL_LABELS_OPENED',seed=seed,role=role)
            reqs={r.debt.case_id:r for r in requests(role)};md=read(root/f'{seed}.{role}.metadata.json')
            grouped=defaultdict(list)
            for p in all_predictions[role]:
                cid=p['case_id'];req=reqs[cid];f=past(req);target=labs[cid][str(p['horizon'])]
                if p['request_id']!=req.identity or target['timestamp_utc']!=p['timestamp_utc']:raise ValueError('Scoring identity mismatch')
                row=dict(p,actual=target['value'],current=f['current'],scale=f['scale'],family=md[cid]['family'],extreme_scale=md[cid]['extreme_scale'])
                grouped[(p['method'],p['horizon'])].append(row)
            for (method,h),rs in grouped.items():
                identity=dict(replica=seed,partition=role,method=method,horizon=h)
                metrics.append(dict(identity,strata=summaries(rs),per_family={fam:summaries([r for r in rs if r['family']==fam])['all'] for fam in sorted({r['family'] for r in rs})}))
                intervals.append(dict(identity,overall=interval_metrics(rs),changed=interval_metrics([r for r in rs if r['actual']!=r['current']]),unchanged=interval_metrics([r for r in rs if r['actual']==r['current']])))
                classification.append(dict(identity,result=classify(rs)))
                paired.append(dict(identity,result=paired_family_interval(rs)))
    write(root/'metrics.json',metrics);write(root/'intervals.json',intervals)
    write(root/'classification.json',classification);write(root/'paired.json',paired)
    write(root/'events.json',events);write(root/'repeatability.json',dict(exact_predictions=repeated,status='PASS'))
    return dict(scope=SCOPE,status='COMPLETED',replicas=len(REPLICAS),predictions=repeated)
