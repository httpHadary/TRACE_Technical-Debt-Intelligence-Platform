"""Static registration and separately approved execution boundary."""
from pathlib import Path
import json
from forecasting_research.phase6_0.artifacts import sha,write
from forecasting_research.phase6_0.contracts import Request
from forecasting_research.phase6_1b.population import Spec
from . import VERSION

ROOT=Path('/home/hp/tst/research/forecasting_mvp/phase6_1c')
PRIOR=Path('/home/hp/tst/research/forecasting_mvp/phase6_1b/2026-10-19/study-003')
LIMITS=dict(rss_ceiling_bytes=2*1024**3,guard_bytes=7*1024**3//4,wall_seconds=900,threads=2,
            log_bytes=16*1024**2,total_bytes=64*1024**2)
CONFIG=dict(max_context=512,max_horizon=90,per_core_batch_size=1,normalize_inputs=True,
            use_continuous_quantile_head=True,force_flip_invariance=False,infer_is_positive=False,
            fix_quantile_crossing=False,return_backcast=False)


def safe(path):
    p=Path(path).absolute()
    if '..' in p.parts or p==ROOT or not p.is_relative_to(ROOT) or any(x.is_symlink() for x in (p,*p.parents)):
        raise ValueError('Fresh owned Phase6.1C path without traversal/symlinks required')
    return p


def sources():
    project=Path(__file__).resolve().parents[2]
    files=sorted((project/'forecasting_research/phase6_1c').glob('*.py'))
    files += [project/'forecasting_research/phase6_1b'/n for n in ('adapters.py','evaluate.py','population.py','model_admission.json')]
    files += [project/'forecasting_research/phase6_1a/run.py',project/'forecasting_research/phase6_0/runtime.py']
    return {str(p.relative_to(project)):sha(p) for p in files}


def prepare(path,audit):
    from .integrity import audit as inspect
    evidence=inspect()
    if evidence!=audit:raise ValueError('Fresh static audit must reproduce exactly')
    out=safe(path);out.mkdir(parents=True,exist_ok=False)
    prior=json.loads((PRIOR/'registration.json').read_text())
    requests=json.loads((PRIOR/'requests.json').read_text())
    if sha(PRIOR/'requests.json')!=prior['input_sha256'] or len(requests)!=36:
        raise ValueError('Frozen synthetic request identity mismatch')
    for data in requests.values():
        if not Request.from_dict(data).complete_daily(512):raise ValueError('Complete original512 histories required')
    write(out/'requests.json',requests);write(out/'static_audit.json',audit)
    reg=dict(version=VERSION,status='SYNTHETIC_ENGINEERING_TEST',population=prior['population'],
        models=prior['models'],source_hashes=sources(),limits=LIMITS,forecast_config=CONFIG,
        smoke_case_id=Spec('slow_increase',0).case_id,native_horizon=90,horizons=[30,60,90],
        repeats=0,loader='meta constructor + mmap safetensors + strict assign=True; no source/weight modification',
        input_sha256=sha(out/'requests.json'),audit_sha256=sha(out/'static_audit.json'),
        prior=dict(path=str(PRIOR),registration_sha256=sha(PRIOR/'registration.json'),
                   predictions_sha256=sha(PRIOR/'predictions.json'),manifest_sha256=sha(PRIOR/'manifest.json')),
        authorization='NOT_GRANTED_BY_REGISTRATION',scope='One separately approved worker; smoke first; optional conditional36 within same load/time budget',
        labels='Unavailable to predictor; score only sealed outputs',
        cohort='Previously exposed Phase6.1B synthetic development population; never fresh confirmatory',
        failure='No fallback, quantile sorting, retry, alternative loader or raised limits')
    write(out/'registration.json',reg);write(out/'registration_seal.json',dict(sha256=sha(out/'registration.json')))
    return reg


def verify(path):
    out=safe(path);reg=json.loads((out/'registration.json').read_text())
    if sha(out/'registration.json')!=json.loads((out/'registration_seal.json').read_text())['sha256']:
        raise ValueError('Frozen registration changed')
    if (reg['version']!=VERSION or reg['source_hashes']!=sources() or reg['limits']!=LIMITS
            or reg['forecast_config']!=CONFIG or reg['authorization']!='NOT_GRANTED_BY_REGISTRATION'
            or reg['smoke_case_id']!=Spec('slow_increase',0).case_id or reg['native_horizon']!=90
            or reg['horizons']!=[30,60,90]):raise ValueError('Static policy/source drift')
    for name,key in [('requests.json','input_sha256'),('static_audit.json','audit_sha256')]:
        if sha(out/name)!=reg[key]:raise ValueError('Registered artifact changed')
    for name,key in [('registration.json','registration_sha256'),('predictions.json','predictions_sha256'),('manifest.json','manifest_sha256')]:
        if sha(PRIOR/name)!=reg['prior'][key]:raise ValueError('Frozen Phase6.1B evidence changed')
    return reg,json.loads((out/'requests.json').read_text())
