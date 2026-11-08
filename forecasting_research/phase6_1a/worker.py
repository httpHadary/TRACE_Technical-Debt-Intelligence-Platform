"""One offline label-free paired-context worker. No scoring/future generation."""
from pathlib import Path
import json,os,resource,sys,time,importlib.metadata
from forecasting_research.phase6_0.runtime import deny_network,MAX_RSS
from forecasting_research.phase6_0.worker import CHECKPOINT,PINS
from forecasting_research.phase6_0.artifacts import write,sha
from forecasting_research.phase6_0.contracts import Request,canonical
from forecasting_research.phase6_0.predictors import baseline
from .study import safe,verify,MODELS
from .adapter import ContextAdapter


def execute(path):
    study=safe(path)
    if json.loads((study/'attempt.json').read_text())!={'owner':'phase6_1a.context.cpu','attempts':1,'study':str(study)}:
        raise ValueError('Exclusive attempt ownership required')
    write(study/'worker_claim.json',{'pid':os.getpid(),'status':'CONSUMED'})
    start=time.monotonic();network=deny_network();resource.setrlimit(resource.RLIMIT_CPU,(900,900))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    reg,requests=verify(study)
    versions={k:importlib.metadata.version(k) for k in PINS}
    if versions!=PINS:raise RuntimeError('BLOCKED_RUNTIME: pinned package drift')
    from forecasting_mvp.chronos_adapter import ChronosSmallAdapter,verify_checkpoint
    admission=verify_checkpoint(CHECKPOINT)
    if admission!=reg['checkpoint'] or versions!=reg['runtime'] or sys.version_info[:3]!=(3,12,3):
        raise RuntimeError('BLOCKED_RUNTIME: registration/checkpoint/Python identity mismatch')
    config=json.loads((CHECKPOINT/'config.json').read_text())['chronos_config']
    if config['context_length']<512 or config['output_patch_size']*config['max_output_patches']<90:
        raise RuntimeError('BLOCKED_CHECKPOINT: insufficient native capacities')
    write(study/'runtime_admission.json',dict(status='SYNTHETIC_ENGINEERING_TEST',checkpoint=admission,runtime=versions,network=network,
        context_capacity=config['context_length'],native_horizon_capacity=config['output_patch_size']*config['max_output_patches']))
    load=time.monotonic();loaded=ChronosSmallAdapter.load_cpu(CHECKPOINT);adapter=ContextAdapter(loaded.pipeline);load_seconds=time.monotonic()-load
    import torch
    if torch.get_num_threads()!=2 or torch.get_num_interop_threads()!=1 or torch.version.cuda is not None or torch.cuda.is_available():
        raise RuntimeError('BLOCKED_RUNTIME: CPU/thread policy failed')
    predictions={m:{} for m in MODELS};timings=[];forwards=[];repeats=[]
    for cid,pair in requests.items():
        short,long=(Request.from_dict(pair[k]) for k in ('90','512'))
        for model in MODELS[:3]:predictions[model][cid]=baseline(short,model)
        for length,request in ((90,short),(512,long)):
            outputs=[]
            for repeat in range(2):
                tick=time.monotonic();outputs.append(adapter.predict_observed(request,length))
                timings.append(dict(case_id=cid,context_days=length,repeat=repeat,seconds=time.monotonic()-tick))
                forwards.append(dict(case_id=cid,context_days=length,repeat=repeat,forward=adapter.forward_receipt))
            if canonical(outputs[0])!=canonical(outputs[1]):raise RuntimeError('NONDETERMINISTIC_NATIVE_OUTPUT; no retry')
            repeats.append(dict(case_id=cid,context_days=length,identical=True))
            predictions['chronos'+str(length)][cid]=outputs[0]
    prediction_hash=write(study/'predictions.json',predictions)
    write(study/'prediction_seal.json',dict(sha256=prediction_hash,labels_scored=False,registration_sha256=sha(study/'registration.json')))
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    if peak>MAX_RSS:raise RuntimeError('RSS_LIMIT')
    verify(study)
    if verify_checkpoint(CHECKPOINT)!=admission:raise RuntimeError('Checkpoint changed')
    write(study/'forward_evidence.json',forwards)
    write(study/'resources.json',dict(network=network,model_load_seconds=load_seconds,worker_elapsed_seconds=time.monotonic()-start,
        peak_rss_bytes=peak,cpu_affinity=sorted(os.sched_getaffinity(0)),torch_threads=2,torch_interop_threads=1,
        repeats=repeats,timings=timings,native_calls=len(timings),gpu_used=False,successful_worker=True))


if __name__=='__main__':
    out=Path(sys.argv[1])
    try:execute(out)
    except Exception as exc:
        # A fatal error remains a failed worker; never turn it into fallback predictions.
        try:
            owned=safe(out)
            if (owned/'attempt.json').is_file():
                write(owned/'worker_failure.json',dict(status='BLOCKED_RUNTIME',exception_type=type(exc).__name__,message=str(exc)))
        except (ValueError,OSError):pass
        raise
