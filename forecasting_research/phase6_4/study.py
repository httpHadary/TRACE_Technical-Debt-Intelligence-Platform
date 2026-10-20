"""Exclusive registration and test-label access only after sealed prediction files."""
from pathlib import Path
import json
import sys
import hashlib
from forecasting_research.phase6_0.artifacts import write,sha
from forecasting_research.phase6_0.contracts import digest
from . import VERSION,STATUS
from .population import population,REPLICAS,COUNTS,FAMILIES,OOD
from .model import CONFIGS
from .integrity import runtime_identity

ROOT=Path('/home/hp/tst/research/forecasting_mvp/phase6_4')
PROJECT=Path(__file__).resolve().parents[2]
LIMITS=dict(rss_bytes=2*1024**3,wall_seconds=900,threads=2,log_bytes=8*1024**2,output_bytes=128*1024**2)


def safe(path):
    p=Path(path).absolute()
    if '..' in p.parts or not p.is_relative_to(ROOT) or p==ROOT or any(a.is_symlink() for a in (p,*p.parents)):
        raise ValueError('Exclusive phase6_4 nonsymlink private path required')
    return p


def sources():
    return {str(p.relative_to(PROJECT)):sha(p) for p in sorted((PROJECT/'forecasting_research').rglob('*.py'))}


def prepare(path):
    root=safe(path);root.mkdir(parents=True,exist_ok=False)
    runtime=runtime_identity();write(root/'runtime_identity.json',runtime)
    files={};split=[];old_histories=set()
    # Read only opaque history identifiers from the old population metadata.
    old=Path('/home/hp/tst/research/forecasting_mvp/phase6_3/2026-10-20/study-001/population.json')
    published=json.loads((PROJECT/'examples/phase6_3/split_manifest.json').read_text())
    if sha(old)!=published['full_private_population_sha256']:raise ValueError('Old history registry changed')
    old_histories={r['history_sha256'] for r in json.loads(old.read_text())}
    history_roles={};ids=set()
    for rep in REPLICAS:
        for part in COUNTS:
            rows=population(rep,part)
            for r in rows:
                cid=r['request']['case_id'];meta=r['metadata'];hs=meta['history_sha256']
                if cid in ids or hs in old_histories:raise ValueError('Duplicate or exposed history')
                ids.add(cid)
                role=(rep,part,meta['group'])
                if hs in history_roles and (part!='identifiability' or history_roles[hs]!=role):raise ValueError('Cross-role duplicate history')
                history_roles[hs]=role
            stem=f'{rep}.{part}'
            payloads={'requests':{r['request']['case_id']:r['request'] for r in rows},
                      'targets':{r['request']['case_id']:r['targets'] for r in rows},
                      'metadata':{r['request']['case_id']:r['metadata'] for r in rows}}
            for kind,data in payloads.items():
                name=f'{stem}.{kind}.json';files[name]=write(root/name,data)
            split.append(dict(replica=rep,partition=part,n=len(rows),families=list(OOD if part in ('ood','identifiability') else FAMILIES)))
    transfer={n:sha(PROJECT/'examples/phase6_3'/n) for n in ('models.json','selection.json')}
    write(root/'registration.json',dict(version=VERSION,status=STATUS,files=files,source_hashes=sources(),
        replicas=list(REPLICAS),splits=split,configs=CONFIGS,limits=LIMITS,transfer_hashes=transfer,
        old_history_hashes_checked=len(old_histories),prior_phase_scope='Frozen published states only, no old cohort execution',
        primary='adaptive_persistence',selection='fail closed; >=24 examples and >=2 families per safety stratum',
        runtime_identity_sha256=sha(root/'runtime_identity.json'),
        protocol_sha256=sha(PROJECT/'PHASE_6_4_PREREGISTRATION.md'),python_sha256=sha(Path(sys.executable).resolve())))
    return root


def verify(root):
    root=safe(root);reg=json.loads((root/'registration.json').read_text())
    if reg['version']!=VERSION or reg['source_hashes']!=sources():raise ValueError('Registered source changed')
    if reg['protocol_sha256']!=sha(PROJECT/'PHASE_6_4_PREREGISTRATION.md'):raise ValueError('Protocol changed')
    if reg['python_sha256']!=sha(Path(sys.executable).resolve()):raise ValueError('Runtime changed')
    if sha(root/'runtime_identity.json')!=reg['runtime_identity_sha256'] or runtime_identity()!=json.loads((root/'runtime_identity.json').read_text()):raise ValueError('Numerical runtime changed')
    for name,h in reg['files'].items():
        if Path(name).name!=name or sha(root/name)!=h:raise ValueError('Input identity changed')
    for name,h in reg['transfer_hashes'].items():
        if sha(PROJECT/'examples/phase6_3'/name)!=h:raise ValueError('Frozen transfer changed')
    return reg


def seal_predictions(root,replica,prerequisites):
    names=[f'{replica}.{part}.predictions.json' for part in ('test','ood','identifiability')]
    payload=dict(files={n:sha(root/n) for n in names+prerequisites},registration_sha256=sha(root/'registration.json'))
    write(root/f'{replica}.prediction_seal.json',payload)
    return payload


def open_targets(root,replica,partition):
    if partition in ('test','ood','identifiability'):
        seal=json.loads((root/f'{replica}.prediction_seal.json').read_text())
        if seal['registration_sha256']!=sha(root/'registration.json'):raise ValueError('Registration seal mismatch')
        expected={f'{replica}.{p}.predictions.json' for p in ('test','ood','identifiability')}
        if not expected.issubset(seal['files']):raise ValueError('Incomplete prediction seal')
        for name,h in seal['files'].items():
            if sha(root/name)!=h:raise ValueError('Prediction/state tampering')
    elif partition not in ('train','validation','calibration'):raise ValueError('Invalid label role')
    return json.loads((root/f'{replica}.{partition}.targets.json').read_text())
