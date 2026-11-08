"""Conditional native worker. No TimesFM construction before explicit approval."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import resource
import sys
import time
from forecasting_research.phase6_0.artifacts import write,sha
from forecasting_research.phase6_0.contracts import Request
from forecasting_research.phase6_0.runtime import deny_network
from forecasting_research.phase6_1b.adapters import TimesFM512
from .study import safe,verify,CONFIG,LIMITS
from .loader import require_approval,load_timesfm
from .integrity import verify_sources


def execute(path):
    out=safe(path);reg,requests=verify(out)
    approval=json.loads((out/'approval.json').read_text())
    scope=require_approval(approval,sha(out/'registration.json'))
    expected=dict(owner='phase6_1c.timesfm.cpu',attempts=1,registration_sha256=sha(out/'registration.json'))
    if json.loads((out/'attempt.json').read_text())!=expected:raise PermissionError('Exclusive owned claim required')
    write(out/'worker_claim.json',dict(pid=os.getpid(),status='CONSUMED'))
    start=time.monotonic();network=deny_network()
    resource.setrlimit(resource.RLIMIT_CPU,(900,900));resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    expected_versions={'torch':'2.11.0+cpu','safetensors':'0.8.0','numpy':'2.4.4','huggingface_hub':'0.36.2'}
    versions={k:importlib.metadata.version(k) for k in expected_versions}
    if versions!=expected_versions or sys.version_info[:3]!=(3,12,3):raise RuntimeError('Pinned runtime drift')
    audit=json.loads((out/'static_audit.json').read_text());verify_sources(audit['model'])
    import torch
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.manual_seed(42);torch.use_deterministic_algorithms(True)
    write(out/'loading.json',dict(stage='META_MMAP_ASSIGN_LOADING',native_calls_started=0))
    tick=time.monotonic();model,assignment=load_timesfm(audit,approval,sha(out/'registration.json'));load_seconds=time.monotonic()-tick
    write(out/'assignment_verification.json',assignment)
    model.compile(__import__('timesfm').ForecastConfig(**CONFIG))
    adapter=TimesFM512(model)
    write(out/'load_receipt.json',dict(status='MODEL_LOADED_NO_FORECAST_YET',load_seconds=load_seconds,
        parameters=audit['checkpoint']['tensor_count'],cpu=True,float32=True,
        configured_horizon=model.forecast_config.max_horizon,fix_quantile_crossing=model.forecast_config.fix_quantile_crossing))
    predictions={};traces=[];timings=[]
    order=[reg['smoke_case_id']]
    if scope=='SMOKE_AND_REGISTERED_36':order += [c for c in requests if c!=reg['smoke_case_id']]
    for index,cid in enumerate(order):
        req=Request.from_dict(requests[cid])
        print(json.dumps(dict(event='native_call_started',case_id=cid,stage='SMOKE' if index==0 else 'REGISTERED_COMPARISON')),flush=True)
        tick=time.monotonic();result=adapter.predict(req)
        timings.append(dict(case_id=cid,seconds=time.monotonic()-tick));traces.append(dict(case_id=cid,trace=adapter.forward_receipt))
        predictions[cid]=result
        if index==0:
            smoke_hash=write(out/'smoke_prediction.json',result)
            write(out/'smoke_seal.json',dict(sha256=smoke_hash,registration_sha256=sha(out/'registration.json'),labels_scored=False))
            if 'failure' in result:raise RuntimeError('NATIVE_SMOKE_INVALID; no further calls')
    prediction_hash=write(out/'native_predictions.json',predictions)
    write(out/'native_prediction_seal.json',dict(sha256=prediction_hash,registration_sha256=sha(out/'registration.json'),labels_scored=False))
    # Verify every assigned parameter after inference without allocating copies.
    for key,param in model.model.state_dict().items():
        digest=hashlib.sha256(memoryview(param.detach().numpy()).cast('B')).hexdigest()
        if digest!=audit['checkpoint']['tensors'][key]['sha256']:raise RuntimeError('Pretrained parameter mutation')
    verify(out);verify_sources(audit['model'])
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    if peak>LIMITS['guard_bytes']:raise RuntimeError('RSS_GUARD_EXCEEDED')
    write(out/'forward_evidence.json',traces)
    write(out/'resources.json',dict(status='PASS',scope=scope,network=network,runtime=versions,
        worker_seconds=time.monotonic()-start,load_seconds=load_seconds,timings=timings,
        native_calls=len(timings),native_invalid_cases=sum('failure' in v for v in predictions.values()),
        kernel_peak_rss_bytes=peak,threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),
        cpu_affinity=sorted(os.sched_getaffinity(0)),gpu=False,automatic_retries=0,parameters_unchanged=True))


if __name__=='__main__':
    try:execute(sys.argv[1])
    except Exception as exc:
        try:
            out=safe(sys.argv[1])
            if (out/'attempt.json').is_file():write(out/'worker_failure.json',dict(type=type(exc).__name__,message=str(exc)))
        except (ValueError,OSError):pass
        raise
