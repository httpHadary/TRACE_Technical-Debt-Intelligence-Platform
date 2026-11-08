"""Single resource-admitted existing-model worker. No acquisition or retry path."""
from pathlib import Path
import json
import os
from forecasting_research.phase6_0.artifacts import write, seal, sha
from forecasting_research.phase6_1a.run import admission, supervise
from .study import safe, verify, verify_prior
from .evaluate import evaluate


def concurrent_workloads():
    """Read-only process observation; never kills unrelated workloads."""
    found=[]
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name)==os.getpid():
            continue
        try:
            args=(entry/'cmdline').read_bytes().split(b'\0')
            exe=Path(os.fsdecode(args[0])).name if args and args[0] else ''
            # Inspect actual executable/arguments, not shell command text.
            active=exe in ('java','javac','mvn','sonar-scanner') or any(
                a.decode(errors='replace').startswith('forecasting_research.') and a.endswith(b'.worker') for a in args)
            if active:
                found.append(dict(pid=int(entry.name),executable=exe))
        except (OSError,ValueError):
            continue
    return found


def run(path):
    study = safe(path)
    reg,requests=verify(study)
    write(study/'attempt.json',dict(owner='phase6_1b.comparison',attempts=1,study=str(study)))
    predictions={m:{} for m in reg['models']};execution={}
    planned=('chronos512','ttm512','timesfm512')
    if reg.get('reuse'):
        prior=verify_prior(reg['reuse']['prior'])
        if (sha(prior/'predictions.json')!=reg['reuse']['prediction_sha256'] or sha(prior/'registration.json')!=reg['reuse']['registration_sha256']):
            raise ValueError('Prior prediction identity drift')
        previous=json.loads((prior/'predictions.json').read_text())
        predictions.update({m:previous[m] for m in reg['reuse']['models']})
        old=json.loads((prior/'execution_status.json').read_text())
        execution={m:dict(old[m],reused_from=str(prior/m)) for m in ('chronos512','timesfm512')}
        planned=('ttm512',)
    for model in planned:
        out=study/model;out.mkdir(exist_ok=False)
        write(out/'attempt.json',dict(owner='phase6_1b.'+model+'.cpu',attempts=1,study=str(study)))
        resources=admission(study)
        resources['concurrent_prohibited_processes']=concurrent_workloads()
        resources['eligible']=resources['eligible'] and not resources['concurrent_prohibited_processes']
        write(out/'host_admission.json',resources)
        executable=Path(reg['registry'][model]['python'])
        if not resources['eligible'] or not executable.is_file():
            receipt=dict(status='BLOCKED_RESOURCE',failure='RESOURCE_OR_ENVIRONMENT_ADMISSION',worker_started=False)
        else:
            # A conservative stop threshold leaves 256 MiB below the approved
            # 2 GiB RSS ceiling for monitoring latency. Never increase ceilings.
            receipt=supervise([str(executable),'-m','forecasting_research.phase6_1b.worker',str(study),model],out,
                              max_rss=7*1024**3//4)
            receipt['approved_rss_ceiling_bytes']=2*1024**3
            receipt['worker_started']=True
            if receipt['failure']=='RSS_LIMIT':receipt['status']='BLOCKED_RESOURCE'
        execution[model]=receipt
        if receipt['status']=='PASS':
            data=json.loads((out/'predictions.json').read_text())
            expected=dict(sha256=sha(out/'predictions.json'),registration_sha256=sha(study/'registration.json'),labels_scored=False)
            if json.loads((out/'prediction_seal.json').read_text())!=expected:
                raise ValueError('Per-model prediction seal required')
            predictions.update(data)
        else:
            for cid,data in requests.items():
                from forecasting_research.phase6_0.contracts import Request
                predictions[model][cid]=dict(failure=receipt['status'],request_id=Request.from_dict(data).identity)
        write(out/'terminal_receipt.json',receipt)
    if not predictions['persistence']:
        raise RuntimeError('Baseline/Chronos worker failed; preserve receipt, do not score')
    write(study/'execution_status.json',execution)
    digest=write(study/'predictions.json',predictions)
    write(study/'prediction_seal.json',dict(sha256=digest,registration_sha256=sha(study/'registration.json'),labels_scored=False))
    metrics=evaluate(study,reg,requests)
    good=[m for m in ('chronos512','ttm512','timesfm512') if execution[m]['status']=='PASS']
    result=dict(status='PASS' if len(good)==3 else 'PARTIAL' if any(m!='chronos512' for m in good) else 'BLOCKED',
                completed_native_workers=good,scope='SYNTHETIC_ENGINEERING_TEST; not real-world forecasting evidence')
    write(study/'outcome.json',result)
    seal(study)
    return result
