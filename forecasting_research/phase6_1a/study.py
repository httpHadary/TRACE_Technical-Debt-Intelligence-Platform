"""Frozen study registration, fresh paths and hash-verified publication."""
from pathlib import Path
import json,os
from forecasting_research.phase6_0.artifacts import write,sha,seal
from forecasting_research.phase6_0.contracts import Request,digest
from .population import population,history,short,specs
from . import VERSION

ROOT=Path('/home/hp/tst/research/forecasting_mvp/phase6_1a')
ENV=Path('/home/hp/tst/td_pipeline_module_level/td_pipeline/.venv-chronos-cpu')
MODELS=('persistence','rolling_mean','linear_trend','chronos90','chronos512')


def safe(path):
    p=Path(path).absolute()
    if '..' in p.parts or p==ROOT or not p.is_relative_to(ROOT) or any(x.is_symlink() for x in (p,*p.parents)):
        raise ValueError('Owned phase6_1a path required; no symlinks/traversal')
    return p


def sources():
    project=Path(__file__).resolve().parents[2]
    files=sorted((project/'forecasting_research/phase6_1a').glob('*.py'))
    files+=sorted((project/'forecasting_research/phase6_0').glob('*.py'))
    files += [project/'forecasting_mvp/chronos_adapter.py',project/'forecasting_mvp/baselines.py',project/'requirements-chronos-cpu-lock.txt']
    files.append(project/'examples/phase4_1/checkpoint_admission.json')
    result={str(p.relative_to(project)):sha(p) for p in files}
    for name in ('pipeline.py','model.py','layers.py','dataset.py'):
        result['installed_chronos2/'+name]=sha(ENV/'lib/python3.12/site-packages/chronos/chronos2'/name)
    result['installed_chronos/chronos_bolt.py']=sha(ENV/'lib/python3.12/site-packages/chronos/chronos_bolt.py')
    return result


def prepare(path):
    out=safe(path);out.mkdir(parents=True,exist_ok=False)
    rows=population();requests={}
    for spec in specs():
        long=history(spec)
        if long.complete_daily(512):requests[spec.case_id]={'90':short(long).as_dict(),'512':long.as_dict()}
    write(out/'requests.json',requests)
    from forecasting_research.phase6_0.worker import CHECKPOINT,PINS
    from forecasting_mvp.chronos_adapter import verify_checkpoint
    checkpoint=verify_checkpoint(CHECKPOINT)
    published=json.loads((Path(__file__).resolve().parents[2]/'examples/phase4_1/checkpoint_admission.json').read_text())
    if checkpoint!=published:raise ValueError('Independent published checkpoint/license admission mismatch')
    registration=dict(version=VERSION,status='SYNTHETIC_ENGINEERING_TEST',checkpoint=checkpoint,runtime=PINS,population=rows,models=list(MODELS),
        context_days=[90,512],native_future_steps=90,horizons_days=[30,60,90],repeats=2,seed=42,
        quantiles=[.1,.5,.9],stock_policy='max(0, raw); preserve raw values',fallback='NONE',
        baseline_policy={'persistence':'origin','rolling_mean':'fixed final 7 observations','linear_trend':'fixed final 90, anchored OLS'},
        paired_policy='identical origins/targets; primary all-five-success matched; report full attempted coverage and native-pair overlap',
        normalization='absolute error divided by mean abs first-difference of common final90 past; zero denominator => null, count excluded',
        preprocessing='Same native float32 InstanceNorm/arcsinh and inverse; location/scale recomputed on each full supplied context; internal patch masks are not new observations',
        bootstrap='500 paired synthetic-case draws seed42; conditional engineering diagnostic, not real-repository inference',
        input_sha256=sha(out/'requests.json'),source_sha256=sources(),
        limits=dict(rss_bytes=2*1024**3,wall_seconds=900,numerical_threads=2,log_bytes=16*1024**2,artifact_bytes=16*1024**2,total_output_bytes=64*1024**2),
        fitting=False,tuning=False,original_phase6_0_comparison=False)
    write(out/'registration.json',registration)
    write(out/'registration_seal.json',{'sha256':sha(out/'registration.json')})
    return registration


def verify(path):
    out=safe(path);reg=json.loads((out/'registration.json').read_text())
    if sha(out/'registration.json')!=json.loads((out/'registration_seal.json').read_text())['sha256']:
        raise ValueError('Frozen registration changed')
    if reg['version']!=VERSION or reg['source_sha256']!=sources() or reg['population']!=population() or reg['models']!=list(MODELS):
        raise ValueError('Study/source/population identity mismatch')
    if sha(out/'requests.json')!=reg['input_sha256']:raise ValueError('Request bytes changed')
    data=json.loads((out/'requests.json').read_text());expected={}
    for spec in specs():
        long=history(spec)
        if long.complete_daily(512):expected[spec.case_id]={'90':short(long).as_dict(),'512':long.as_dict()}
    if data!=expected:raise ValueError('Only exactly generated synthetic requests admitted')
    for pair in data.values():
        a,b=(Request.from_dict(pair[k]) for k in ('90','512'))
        if a!=short(b):raise ValueError('Paired context mismatch')
    return reg,data
