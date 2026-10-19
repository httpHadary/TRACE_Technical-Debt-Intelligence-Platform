"""Immutable registration, role-bound labels and prediction-before-test seals."""
from pathlib import Path
import json
import os
from importlib.metadata import version
from forecasting_research.phase6_0.artifacts import write, sha
from forecasting_research.phase6_0.contracts import digest, Request
from . import VERSION, STATUS, HORIZONS
from .population import population, ROOT_SEED, COUNTS, FAMILIES, OOD
from .models import METHODS, ALPHAS, THRESHOLDS, WEIGHTS
from .runtime import identity as runtime_identity

ROOT = Path('/home/hp/tst/research/forecasting_mvp/phase6_2')
LIMITS = dict(rss_bytes=2*1024**3, wall_seconds=900, numerical_threads=2,
              log_bytes=8*1024**2, output_bytes=64*1024**2)
POLICY = dict(version=VERSION, status=STATUS, history_days=180, horizons=list(HORIZONS),
    root_seed=ROOT_SEED, counts=COUNTS, families=list(FAMILIES), ood_families=list(OOD),
    alpha_grid=list(ALPHAS), hard_gate_thresholds=list(THRESHOLDS), blend_weights=list(WEIGHTS),
    methods=list(METHODS), selection='minimum equal-family normalized validation MAE; denominator=max(1, mean observed history); exact ties use grid order',
    reported_normalization='mean absolute observed history; zero denominator null/excluded with count; no epsilon',
    target='endpoint difference != 0, not any interim event; current + raw signed delta clipped at zero',
    magnitude='ridge conditional mean on changed training cases; mixture adds empirical changed-training normalized residuals',
    uncertainty='80% absolute normalized residual radius, higher empirical 0.8 quantile, calibration only; descriptive, no conformal guarantee',
    fixed_baselines='persistence; mean of last 7 observed values; origin-anchored OLS slope from last 90 calendar days',
    large_change='abs(delta)>=max(10 minutes, 0.2*current)', class_weight='none',
    seed_policy='distinct SHA256-derived random streams; hidden future noise separate from observed history',
    bootstrap='500 paired resamples of mechanism families; seed 620; descriptive synthetic uncertainty',
    fitting='synthetic training only; no model refit after validation/calibration/test',
    pretrained={'chronos':'NOT_EXECUTED_NO_SEPARATE_APPROVAL','ttm':'NOT_EXECUTED','timesfm':'NOT_EXECUTED'},
    rights='24 decisions NOT_APPROVED; no analyzer measurements', limits=LIMITS)


def safe(path, fresh=False):
    p = Path(path).absolute()
    if ('..' in p.parts or p == ROOT or not p.is_relative_to(ROOT)
            or any(x.is_symlink() for x in (p, *p.parents))):
        raise ValueError('Exclusive new Phase6.2 output outside Git required, no aliases/symlinks')
    if fresh:
        p.mkdir(parents=True, exist_ok=False)
    elif not p.is_dir():
        raise ValueError('Registered task directory required')
    return p


def sources():
    project = Path(__file__).resolve().parents[2]
    files = list((project/'forecasting_research/phase6_2').glob('*.py'))
    files += [project/'forecasting_research/phase6_0'/n for n in ('contracts.py','predictors.py','artifacts.py')]
    return {str(p.relative_to(project)):sha(p) for p in sorted(files)}


def prepare(path):
    root = safe(path, fresh=True)
    cases = population()
    inputs, metadata, labels = {}, [], {p:{} for p in COUNTS}
    for c in cases:
        req = Request.from_dict(c['request'])
        spec = c['spec']
        inputs[req.case_id] = req.as_dict()
        labels[spec['partition']][req.case_id] = c['targets']
        metadata.append(dict(case_id=req.case_id, partition=spec['partition'], family=spec['family'],
                             request_sha256=req.identity, history_sha256=c['history_sha256'],
                             parameters_sha256=c['parameters_sha256'], seed=spec['seed']))
    write(root/'requests.json', inputs)
    write(root/'population.json', metadata)
    for partition, targets in labels.items():
        write(root/(partition+'_targets.json'), targets)
    write(root/'runtime_identity.json', runtime_identity())
    files = {p.name:sha(p) for p in sorted(root.iterdir()) if p.is_file()}
    reg = dict(policy=POLICY, inputs=files, source_sha256=sources(),
               environment={'python':os.sys.version, 'numpy':version('numpy')},
               counts={p:len(labels[p]) for p in COUNTS}, total=len(cases),
               isolation='logical file/role/prediction contracts, not hostile-code OS label isolation')
    reg_hash = write(root/'registration.json', reg)
    write(root/'registration_seal.json', dict(registration_sha256=reg_hash, models_fitted=False))
    return reg


def verify(root):
    root = safe(root)
    reg = json.loads((root/'registration.json').read_text())
    if (reg['policy'] != POLICY or reg['source_sha256'] != sources()
            or json.loads((root/'registration_seal.json').read_text()) != dict(registration_sha256=sha(root/'registration.json'), models_fitted=False)):
        raise ValueError('Registration/source/policy mismatch')
    for name, expected in reg['inputs'].items():
        if sha(root/name) != expected:
            raise ValueError('Input identity mismatch: '+name)
    if runtime_identity() != json.loads((root/'runtime_identity.json').read_text()):
        raise ValueError('Installed runtime bytes changed')
    return reg


def prediction_seal(root):
    root = safe(root)
    names = ('registration.json','requests.json','population.json','models.json','selection.json',
             'calibration.json','predictions.json')
    receipt = dict(artifacts={n:sha(root/n) for n in names}, labels_scored=False,
                   populations=['test','ood'], status=STATUS)
    write(root/'prediction_seal.json', receipt)
    return receipt


def verify_prediction_seal(root):
    receipt = json.loads((root/'prediction_seal.json').read_text())
    expected = ('registration.json','requests.json','population.json','models.json','selection.json','calibration.json','predictions.json')
    if (receipt != dict(artifacts={n:sha(root/n) for n in expected}, labels_scored=False,
                        populations=['test','ood'], status=STATUS)):
        raise ValueError('Complete prediction/model/config/input seal required before test targets')
    return receipt


class Labels:
    """Capability checks are audited logical boundaries, not an adversarial sandbox."""
    def __init__(self, root, events):
        self.root, self.events = safe(root), events

    def read(self, partition, purpose):
        allowed = {'train':'fit', 'validation':'select', 'calibration':'calibrate', 'test':'score', 'ood':'score'}
        if partition not in allowed or purpose != allowed[partition]:
            raise ValueError('Label partition/purpose mismatch')
        if purpose == 'score':
            verify_prediction_seal(self.root)
        path = self.root/(partition+'_targets.json')
        reg = json.loads((self.root/'registration.json').read_text())
        if sha(path) != reg['inputs'][path.name]:
            raise ValueError('Target identity mismatch')
        self.events.append(dict(event='labels_read', partition=partition, purpose=purpose,
                                prediction_seal_verified=purpose == 'score'))
        return json.loads(path.read_text())
