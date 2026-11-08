"""Immutable registration and explicit acquisition gates; no downloader/installer."""
from pathlib import Path
import json
from forecasting_research.phase6_0.artifacts import sha, write
from forecasting_research.phase6_0.contracts import Request
from forecasting_research.phase6_0.worker import CHECKPOINT, PINS
from forecasting_research.phase6_1a.study import sources as prior_sources
from . import VERSION
from .population import population, history, specs
from .adapters import BASELINES, MODEL

ROOT = Path('/home/hp/tst/research/forecasting_mvp/phase6_1b')
MODELS = (*BASELINES, MODEL, 'ttm512', 'timesfm512')
CANDIDATES = MODELS
LIMITS = dict(rss_bytes=2*1024**3, seconds=900, numerical_threads=2, log_bytes=16*1024**2, total_bytes=64*1024**2)


def safe(path):
    p = Path(path).absolute()
    if '..' in p.parts or p == ROOT or not p.is_relative_to(ROOT) or any(x.is_symlink() for x in (p, *p.parents)):
        raise ValueError('Exclusive phase6_1b path without traversal/symlinks required')
    return p


def sources():
    project = Path(__file__).resolve().parents[2]
    return {**prior_sources(), **{str(p.relative_to(project)): sha(p) for p in sorted((project / 'forecasting_research/phase6_1b').glob('*.py'))},
            'forecasting_research/phase6_0/model_eligibility.json': sha(project / 'forecasting_research/phase6_0/model_eligibility.json'),
            'forecasting_research/phase6_1b/model_admission.json': sha(project / 'forecasting_research/phase6_1b/model_admission.json')}


def registry():
    project = Path(__file__).resolve().parents[2]
    return json.loads((project/'forecasting_research/phase6_1b/model_admission.json').read_text())['models']


def verify_prior(path):
    prior=safe(path)
    if not (prior/'manifest.json').is_file():raise ValueError('Sealed prior attempt required')
    manifest=json.loads((prior/'manifest.json').read_text())['artifacts']
    for name,digest in manifest.items():
        if '..' in Path(name).parts or Path(name).is_absolute() or sha(prior/name)!=digest:
            raise ValueError('Prior attempt preservation failure')
    return prior


def prepare(path, prior=None):
    out = safe(path)
    out.mkdir(parents=True, exist_ok=False)
    from forecasting_mvp.chronos_adapter import verify_checkpoint
    checkpoint = verify_checkpoint(CHECKPOINT)
    project = Path(__file__).resolve().parents[2]
    if checkpoint != json.loads((project / 'examples/phase4_1/checkpoint_admission.json').read_text()):
        raise ValueError('Independent checkpoint/license admission mismatch')
    requests = {s.case_id: history(s).as_dict() for s in specs() if history(s).complete_daily(512)}
    write(out / 'requests.json', requests)
    reuse=None
    if prior is not None:
        previous=verify_prior(prior)
        if sha(previous/'requests.json')!=sha(out/'requests.json'):
            raise ValueError('Reused predictions must have identical requests')
        reuse=dict(prior=str(previous),registration_sha256=sha(previous/'registration.json'),
                   prediction_sha256=sha(previous/'predictions.json'),
                   models=['persistence','rolling_mean','linear_trend','chronos512','timesfm512'],
                   reason='TTM import setup failed before model load/native calls; exact model-module loading repair only; no Chronos/TimesFM replay')
    reg = dict(version=VERSION, status='SYNTHETIC_ENGINEERING_TEST', population=population(), models=list(MODELS),reuse=reuse,
        candidates=list(CANDIDATES), registry=registry(), checkpoint=checkpoint, runtime=PINS,
        context=512, native_chronos_steps=90, horizons=[30, 60, 90], repeats=2, seed=42,
        baseline_windows=dict(persistence=1, rolling_mean=7, linear_trend=90), trend='OLS slope anchored at origin',
        normalization='abs_error / mean(abs(history[512])); zero => null, count explicitly; not MASE',
        macro='Equal scenario weight; equal case weight within each scenario; synthetic cases are not repositories',
        pairs='Every pair on identical successful IDs per horizon; all-admitted intersection separately; blocked candidates never imputed',
        scales='Report all scenarios and excluding mixed_scale; no outcome-selected model/default',
        quantiles='Native q10/q50/q90 strict entire-path ordering; no repair/fallback; absent intervals null',
        stock='max(0, raw); retain raw point/quantiles',
        development_reference='Phase6.1A exposed development only; new seeds/origin/equations, not a real confirmatory cohort',
        limits=LIMITS,
        input_sha256=sha(out / 'requests.json'), sources=sources(), fitting=False, tuning=False)
    write(out / 'registration.json', reg)
    write(out / 'registration_seal.json', {'sha256': sha(out / 'registration.json')})
    return reg


def verify(path):
    out = safe(path)
    reg = json.loads((out / 'registration.json').read_text())
    if sha(out / 'registration.json') != json.loads((out / 'registration_seal.json').read_text())['sha256']:
        raise ValueError('Registration seal mismatch')
    if reg['sources'] != sources() or reg['population'] != population() or reg['registry'] != registry() or reg['models'] != list(MODELS) or reg['version'] != VERSION:
        raise ValueError('Frozen code/population/admission changed')
    if (reg['limits'] != LIMITS or reg['context'] != 512 or reg['native_chronos_steps'] != 90
            or reg['horizons'] != [30,60,90] or reg['runtime'] != PINS or reg['repeats'] != 2
            or reg['baseline_windows'] != dict(persistence=1,rolling_mean=7,linear_trend=90)
            or reg['fitting'] is not False or reg['tuning'] is not False):
        raise ValueError('Registered policy changed')
    if sha(out / 'requests.json') != reg['input_sha256']:
        raise ValueError('Input seal mismatch')
    data = json.loads((out / 'requests.json').read_text())
    expected = {s.case_id: history(s).as_dict() for s in specs() if history(s).complete_daily(512)}
    if data != expected:
        raise ValueError('Only preregistered synthetic histories admitted')
    for value in data.values():
        if not Request.from_dict(value).complete_daily(512):
            raise ValueError('No sparse/irregular inference')
    return reg, data
