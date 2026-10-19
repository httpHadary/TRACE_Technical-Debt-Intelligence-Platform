"""Preregistered synthetic protocol, independent transfer identity, role-bound truth."""
from pathlib import Path
import json
import os
from forecasting_research.phase6_0.artifacts import write, sha
from forecasting_research.phase6_0.contracts import Request, digest, utc
from forecasting_research.phase6_2.runtime import identity as runtime_identity
from . import VERSION, STATUS, HORIZONS
from .population import population, ROOT_SEED, COUNTS, FAMILIES, OOD
from .models import METHODS, configs

ROOT=Path('/home/hp/tst/research/forecasting_mvp/phase6_3')
OLD=Path('/home/hp/tst/research/forecasting_mvp/phase6_2/2026-10-20/study-001')
TRANSFER_HASHES={'models.json':'d77a32b321e0d4b8d08041f6829387decefa34e50c8276bad4e597d8b981052f',
                 'selection.json':'257ad269baea63d9bb91c0bebbb3c2d756eeae33fb4f66089384c85c6c339fce',
                 'calibration.json':'82e19536bfed4d4553ba9dbaadaf210e005bcfa46312c213bf26247d2958913c'}
LIMITS=dict(rss_bytes=2*1024**3,wall_seconds=900,numerical_threads=2,log_bytes=8*1024**2,output_bytes=64*1024**2)
POLICY=dict(version=VERSION,status=STATUS,primary_candidate='adaptive_persistence',
 formulation='origin stock + conservatively gated signed adjustment, then max(0, raw stock)',
 root_seed=ROOT_SEED,counts=COUNTS,families=list(FAMILIES),ood_families=list(OOD),
 history_calendar_days=180,horizons=list(HORIZONS),
 grids={m:configs(m) for m in METHODS[:-1]},
 target='endpoint sign/equality, not any interim excursion; observed history never filled',
 eligibility='common all-method admission: known origin, >=2 observed values including >=2 in final90 calendar days; fail registration if violated',
 features='unchanged past-only 24 Phase6.2 features + null indicators; cached immutable copies',
 classifier='40 damped Newton iterations, L2 1/10, normalized 3-way OVR, none/balanced train class weights',
 magnitude='separate positive/negative signed ridge on training only; sign projections and raw components retained',
 training_scale='max(1 minute, mean absolute observed past); not an epsilon metric denominator',
 metrics_scale='unfloored mean absolute observed past; zero denominators excluded/count reported',
 primary_selection='minimum equal-family model-scale-normalized validation MAE subject to registered safety; no OOD selection',
 large_decrease_validation_safety='Both raw MAE and equal-family model-scale-normalized MAE <=1.05 times persistence; n>=8',
 ood_objective='nonnegative unfloored normalized OOD skill at each horizon, independent eight-family final score only; never used for selection',
 point_safety=dict(unchanged_model_scale_mae_max=.02,large_decrease_relative_deterioration_max=.05,min_safety_n=8),
 tie_policy='within 1% of minimum validation error, first registered grid/order; protected zero-adjustment AP first',
 adaptive_gate='direction argmax incl stable; confidence .75/.9, abs normalized magnitude >=max(.02/.1, .25*past normalized volatility)',
 adaptive_shrink='0 protected option, or .25/.5 times 1/(1+maximum observed gap days/30); no future reliability inputs',
 large_change='abs(delta)>=max(10 minutes,.2*current)',
 interval_selection='train-residual prototypes, validation-only score/coverage/width choice, then independent calibration refit',
 interval_candidates=['shared_symmetric','signed_global','direction_stratified'],widening=[1.,1.25],minimum_calibration_bin=12,
 interval_quality=dict(coverage_low=.75,coverage_high=.85,mean_model_scale_width_max=2.,interval_score_must_not_exceed_shared=True),
 forecasting_targets=dict(main_normalized_skill_positive=True,ood_normalized_skill_nonnegative=True,
                         changed_normalized_skill_nonnegative=True,unchanged_model_scale_mae_max=.02,
                         raw_and_normalized_large_decrease_skill_min=-.05),
 default_if_no_safe_advance='protected zero-adjustment Adaptive Persistence; comparison champion may be ordinary persistence',
 limitations='engineering tolerances, not universal safety or conformal guarantees; mechanism clusters are not real repositories',
 bootstrap='500 whole-family paired draws, seed620; main16 and OOD8 mechanism families; subgroup intervals exploratory',
 transfer='exact original Phase6.2 state/preprocessing/selected configs/calibration, read-only new-input transfer only',
 ood_construction='8 unseen mechanisms; each has stable, interim-return, upward-change, downward-change branches; no outcome-based filtering',
 counterexamples='post-score largest model-scale-normalized excess per family, up to12 families; not used for fitting/selection',
 exclusion='no test-driven population/seed/threshold/width changes; no native pretrained, real labels, network or installation',
 rights='24 NOT_APPROVED unchanged',limits=LIMITS)


def safe(path,fresh=False):
    p=Path(path).absolute()
    if '..' in p.parts or p==ROOT or not p.is_relative_to(ROOT) or any(v.is_symlink() for v in (p,*p.parents)):
        raise ValueError('New exclusive Phase6.3 directory outside Git, no aliases')
    if fresh: p.mkdir(parents=True,exist_ok=False)
    elif not p.is_dir(): raise ValueError('Registered directory required')
    return p


def sources():
    project=Path(__file__).resolve().parents[2]
    paths=list((project/'forecasting_research/phase6_3').glob('*.py'))
    paths+=list((project/'forecasting_research/phase6_2').glob('*.py'))
    paths+=[project/'forecasting_research/phase6_0'/n for n in ('contracts.py','predictors.py','artifacts.py')]
    return {str(p.relative_to(project)):sha(p) for p in sorted(paths)}


def transfer():
    for name,expected in TRANSFER_HASHES.items():
        if sha(OLD/name)!=expected: raise ValueError('Frozen transfer identity mismatch: '+name)
    return dict(model=json.loads((OLD/'models.json').read_text()),
                selection=json.loads((OLD/'selection.json').read_text()),
                calibration=json.loads((OLD/'calibration.json').read_text()),
                identities=TRANSFER_HASHES,refitted=False)


def prepare(path):
    root=safe(path,fresh=True)
    cases=population();requests={};meta=[];labels={p:{} for p in COUNTS};diagnostics={}
    old_registration=json.loads((OLD/'registration.json').read_text())
    if sha(OLD/'population.json')!=old_registration['inputs']['population.json']:
        raise ValueError('Prior history metadata identity mismatch')
    prior={r['history_sha256'] for r in json.loads((OLD/'population.json').read_text())}
    if any(c['history_sha256'] in prior for c in cases):
        raise ValueError('Old synthetic history reused; stop, no post-hoc deduplication')
    for c in cases:
        spec=c['spec'];req=Request.from_dict(c['request']);cid=req.case_id
        recent=[v for t,v in zip(req.timestamps,req.values) if v is not None and (utc(req.origin_utc)-utc(t)).days<90]
        if req.values[-1] is None or len(recent)<2:
            raise ValueError('Common all-method past-only eligibility failed; no selective population')
        requests[cid]=req.as_dict();labels[spec['partition']][cid]=c['targets']
        meta.append(dict(case_id=cid,partition=spec['partition'],family=spec['family'],seed=spec['seed'],
                         request_sha256=req.identity,history_sha256=c['history_sha256'],parameters_sha256=c['parameters_sha256']))
        if spec['partition'] in ('test','ood'):
            diagnostics[cid]=dict(endpoint_return_with_interim_change=c['endpoint_return_with_interim_change'],future_path_sha256=c['future_path_sha256'])
    write(root/'requests.json',requests);write(root/'population.json',meta)
    for p,data in labels.items(): write(root/(p+'_targets.json'),data)
    write(root/'diagnostics_targets.json',diagnostics)
    write(root/'transfer.json',transfer());write(root/'runtime_identity.json',runtime_identity())
    reg=dict(policy=POLICY,inputs={p.name:sha(p) for p in sorted(root.iterdir()) if p.is_file()},source_sha256=sources(),
             counts={p:len(v) for p,v in labels.items()},total=len(cases),prior_history_hashes=len(prior),
             history_overlap_with_phase6_2=0,python=os.sys.version,
             isolation='logical role/file/pure prediction interfaces, not hostile-code OS target isolation')
    value=write(root/'registration.json',reg)
    write(root/'registration_seal.json',dict(registration_sha256=value,models_fitted=False))
    return reg


def verify(root):
    root=safe(root);reg=json.loads((root/'registration.json').read_text())
    if reg['policy']!=POLICY or reg['source_sha256']!=sources(): raise ValueError('Changed study policy/source')
    if json.loads((root/'registration_seal.json').read_text())!=dict(registration_sha256=sha(root/'registration.json'),models_fitted=False):
        raise ValueError('Registration seal mismatch')
    for name,expected in reg['inputs'].items():
        if sha(root/name)!=expected: raise ValueError('Input identity mismatch: '+name)
    if runtime_identity()!=json.loads((root/'runtime_identity.json').read_text()): raise ValueError('Runtime changed')
    if transfer()!=json.loads((root/'transfer.json').read_text()): raise ValueError('Frozen transfer changed')
    return reg


SEALED=('registration.json','requests.json','population.json','transfer.json','models.json','selection.json','calibration.json','predictions.json')


def prediction_seal(root):
    value=dict(status=STATUS,artifacts={n:sha(root/n) for n in SEALED},labels_scored=False)
    write(root/'prediction_seal.json',value)
    return value


def verify_prediction_seal(root):
    expected=dict(status=STATUS,artifacts={n:sha(root/n) for n in SEALED},labels_scored=False)
    if json.loads((root/'prediction_seal.json').read_text())!=expected: raise ValueError('Prediction seal mismatch')
    return expected


class Labels:
    def __init__(self,root,events): self.root,self.events=safe(root),events

    def read(self,partition,purpose):
        roles=dict(train='fit',validation='select',calibration='calibrate',test='score',ood='score',diagnostics='score')
        if partition not in roles or roles[partition]!=purpose: raise ValueError('Partition/role mismatch')
        if purpose=='score': verify_prediction_seal(self.root)
        path=self.root/(partition+'_targets.json')
        reg=json.loads((self.root/'registration.json').read_text())
        if sha(path)!=reg['inputs'][path.name]: raise ValueError('Target identity mismatch')
        self.events.append(dict(event='labels_read',partition=partition,purpose=purpose,prediction_seal_verified=purpose=='score'))
        return json.loads(path.read_text())
