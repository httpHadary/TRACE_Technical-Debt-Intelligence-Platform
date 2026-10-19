"""Approval-gated single worker. No retry, acquisition or limit override."""
from pathlib import Path
import json
import os
import signal
import subprocess
import time
from forecasting_research.phase6_0.artifacts import write,sha,seal
from forecasting_research.phase6_1a.run import admission
from forecasting_research.phase6_1b.run import concurrent_workloads
from forecasting_research.phase6_1b.evaluate import evaluate
from .study import safe,verify,LIMITS,PRIOR
from .loader import require_approval


def limit_failure(elapsed,rss,log_bytes,total_bytes,limits=LIMITS):
    if limits!=LIMITS:raise ValueError('No resource-policy override')
    if elapsed>limits['wall_seconds']:return 'TIMEOUT'
    if rss>limits['guard_bytes']:return 'RSS_LIMIT'
    if log_bytes>limits['log_bytes']:return 'LOG_LIMIT'
    if total_bytes>limits['total_bytes']:return 'OUTPUT_LIMIT'
    return None


def supervise(command,out):
    start=time.monotonic();peak=0;hwm=0;failure=None
    env={**os.environ,'CUDA_VISIBLE_DEVICES':'','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
        'HF_DATASETS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2',
        'OPENBLAS_NUM_THREADS':'2','NUMEXPR_NUM_THREADS':'2','PYTHONDONTWRITEBYTECODE':'1','TOKENIZERS_PARALLELISM':'false'}
    with (out/'worker.log').open('xb') as log:
        process=subprocess.Popen(command,env=env,stdout=log,stderr=log,start_new_session=True,close_fds=True)
        while process.poll() is None:
            try:
                lines=Path(f'/proc/{process.pid}/status').read_text().splitlines()
                values={s.split(':')[0]:int(s.split()[1])*1024 for s in lines if s.startswith(('VmRSS:','VmHWM:'))}
                peak=max(peak,values.get('VmRSS',0));hwm=max(hwm,values.get('VmHWM',0))
            except OSError:pass
            failure=limit_failure(time.monotonic()-start,max(peak,hwm),log.tell(),sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
            if failure:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                break
            time.sleep(.005)
        code=process.wait()
    receipt=dict(status='PASS' if code==0 and not failure else 'BLOCKED_RESOURCE' if failure else 'BLOCKED_RUNTIME',
        failure=failure or ('WORKER_FAILED' if code else None),exit_code=code,wall_seconds=time.monotonic()-start,
        sampled_peak_rss_bytes=peak or None,sampled_kernel_highwater_bytes=hwm or None,
        limits=LIMITS,guard='5ms sampled RSS/HWM plus final kernel ru_maxrss, not hard cgroup enforcement')
    write(out/'supervisor.json',receipt)
    return receipt


def run(path,approval_file):
    out=safe(path);reg,requests=verify(out)
    approval=json.loads(Path(approval_file).read_text())
    scope=require_approval(approval,sha(out/'registration.json'))
    # No claim, native import or subprocess occurs for an unapproved request.
    write(out/'approval.json',approval)
    write(out/'attempt.json',dict(owner='phase6_1c.timesfm.cpu',attempts=1,registration_sha256=sha(out/'registration.json')))
    gate=admission(out);gate['concurrent_prohibited_processes']=concurrent_workloads()
    gate['eligible']=gate['eligible'] and not gate['concurrent_prohibited_processes']
    write(out/'host_admission.json',gate)
    audit=json.loads((out/'static_audit.json').read_text());executable=Path(audit['model']['python'])
    if not gate['eligible'] or not executable.is_file():
        result=dict(status='BLOCKED_RESOURCE',reason='Host/resource/runtime admission failed; worker not started')
    else:
        receipt=supervise([str(executable),'-m','forecasting_research.phase6_1c.worker',str(out)],out)
        if receipt['status']!='PASS':
            result=dict(status=receipt['status'],reason=receipt['failure'],native_outputs_verified=False)
        else:
            metrics=None
            if scope=='SMOKE_AND_REGISTERED_36':
                native=json.loads((out/'native_predictions.json').read_text())
                expected=dict(sha256=sha(out/'native_predictions.json'),registration_sha256=sha(out/'registration.json'),labels_scored=False)
                if json.loads((out/'native_prediction_seal.json').read_text())!=expected or set(native)!=set(requests):
                    raise ValueError('Complete sealed native population required before labels')
                predictions=json.loads((PRIOR/'predictions.json').read_text());predictions['timesfm512']=native
                original=json.loads((PRIOR/'execution_status.json').read_text());original['timesfm512']=receipt
                write(out/'execution_status.json',original)
                digest=write(out/'predictions.json',predictions)
                write(out/'prediction_seal.json',dict(sha256=digest,registration_sha256=sha(out/'registration.json'),labels_scored=False))
                metrics=evaluate(out,reg,requests)
            result=dict(status='PASS' if metrics is None or metrics['accounting']['timesfm512']['native_invalid']==0 else 'PARTIAL',
                scope=scope,native_outputs_verified=True,comparison_completed=metrics is not None,
                interpretation='Synthetic engineering feasibility only; previously exposed cohort')
    write(out/'outcome.json',result);seal(out)
    return result
