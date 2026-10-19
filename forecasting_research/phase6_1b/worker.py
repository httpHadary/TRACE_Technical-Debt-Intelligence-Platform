"""One separately admitted CPU model worker. Future labels never enter execution."""
from pathlib import Path
import importlib.metadata
import json, os, resource, sys, time
from forecasting_research.phase6_0.artifacts import write, sha
from forecasting_research.phase6_0.contracts import Request, canonical
from forecasting_research.phase6_0.runtime import deny_network, MAX_RSS
from forecasting_research.phase6_0.worker import CHECKPOINT, PINS
from .study import safe, verify
from .adapters import baseline, Chronos512, TTM512, TimesFM512, BASELINES


def verify_installation(entry):
    root=Path(entry['private_root'])
    if sha(root/'base_environment_before.json')!=entry['base_manifest_sha256']:
        raise ValueError('Base dependency lock changed')
    manifest=json.loads((root/'base_environment_before.json').read_text())
    base=Path(entry['base_dependency_root'])
    for name,digest in manifest.items():
        if sha(base/name)!=digest:
            raise ValueError('Shared read-only dependency identity drift')
    for name,digest in entry['code_files'].items():
        if sha(root/name)!=digest:
            raise ValueError('Pinned executable source drift')
    for name,expected in entry['checkpoint_files'].items():
        if sha(root/name)!=expected:
            raise ValueError('Checkpoint/license identity drift')


def execute(path, name):
    study=safe(path)
    if name not in ('chronos512','ttm512','timesfm512'):
        raise ValueError('Registered model required')
    out=study/name
    if json.loads((out/'attempt.json').read_text())!={'owner':'phase6_1b.'+name+'.cpu','attempts':1,'study':str(study)}:
        raise ValueError('Exclusive owned attempt required')
    write(out/'worker_claim.json',dict(pid=os.getpid(),status='CONSUMED'))
    start=time.monotonic();network=deny_network()
    resource.setrlimit(resource.RLIMIT_CPU,(900,900))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    reg,requests=verify(study)
    versions={k:importlib.metadata.version(k) for k in PINS}
    if versions!=PINS or sys.version_info[:3]!=(3,12,3):
        raise RuntimeError('BLOCKED_RUNTIME: exact Python/package lock mismatch')
    entry=reg['registry'][name]
    verify_installation(entry)
    import torch
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.manual_seed(42);torch.use_deterministic_algorithms(True)
    if torch.version.cuda is not None or torch.cuda.is_available():
        raise RuntimeError('CPU-only runtime required')
    tick=time.monotonic()
    write(out/'loading.json',dict(model=name,stage='MODEL_LOADING',native_calls_started=0))
    if name=='chronos512':
        from forecasting_mvp.chronos_adapter import ChronosSmallAdapter, verify_checkpoint
        if verify_checkpoint(CHECKPOINT)!=reg['checkpoint']:
            raise ValueError('Chronos published checkpoint drift')
        # Original loader sets inter-op count itself, so load pipeline with the
        # same documented local flags after our one-time worker thread setup.
        from chronos import Chronos2Pipeline
        pipeline=Chronos2Pipeline.from_pretrained(str(CHECKPOINT),device_map='cpu',dtype=torch.float32,
                     local_files_only=True,trust_remote_code=False,use_safetensors=True)
        pipeline.model.eval();adapter=Chronos512(pipeline)
    elif name=='ttm512':
        # Load the unmodified upstream model/config modules in a task namespace.
        # Upstream package __init__ eagerly imports the entire data/training
        # toolkit; none is required by these two model modules. This does not
        # replace model classes, weights, forward code or native preprocessing.
        import types
        import importlib as module_importer
        package=types.ModuleType('td360_pinned_ttm')
        package.__path__=[str(Path(entry['private_root'])/'code/ttm/tsfm_public/models/tinytimemixer')]
        sys.modules[package.__name__]=package
        native=module_importer.import_module(package.__name__+'.modeling_tinytimemixer')
        TinyTimeMixerForPrediction=native.TinyTimeMixerForPrediction
        model,loading=TinyTimeMixerForPrediction.from_pretrained(entry['checkpoint_root'],local_files_only=True,
                    use_safetensors=True,trust_remote_code=False,output_loading_info=True)
        if any(loading.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs')):
            raise RuntimeError('TTM checkpoint/code state mismatch: '+str(loading))
        model=model.to('cpu').eval()
        adapter=TTM512(model,entry['daily_token'])
    else:
        import timesfm
        model=timesfm.TimesFM_2p5_200M_torch.from_pretrained(entry['checkpoint_root'],local_files_only=True,torch_compile=False)
        model.compile(timesfm.ForecastConfig(max_context=512,max_horizon=90,per_core_batch_size=1,
            normalize_inputs=True,use_continuous_quantile_head=True,force_flip_invariance=False,
            infer_is_positive=False,fix_quantile_crossing=False,return_backcast=False))
        adapter=TimesFM512(model)
    module=pipeline.model if name=='chronos512' else model if name=='ttm512' else model.model
    if any(p.device.type!='cpu' or p.dtype!=torch.float32 for p in module.parameters()):
        raise RuntimeError('CPU float32 parameters required')
    load_seconds=time.monotonic()-tick
    write(out/'runtime_admission.json',dict(model=name,runtime=versions,network=network,
        torch_threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),gpu=False,
        load_seconds=load_seconds,checkpoint=entry['weight_sha256']))
    predictions={name:{}}
    if name=='chronos512':predictions.update({b:{} for b in BASELINES})
    timings=[];repeats=[];forwards=[]
    for cid,data in requests.items():
        req=Request.from_dict(data)
        if name=='chronos512':
            for b in BASELINES:predictions[b][cid]=baseline(req,b)
        outputs=[];native=[]
        for repeat in range(2):
            print(json.dumps(dict(event='native_call_started',case_id=cid,repeat=repeat,model=name)),flush=True)
            tick=time.monotonic();outputs.append(adapter.predict(req))
            timings.append(dict(case_id=cid,repeat=repeat,seconds=time.monotonic()-tick))
            native.append(adapter.forward_receipt)
            forwards.append(dict(case_id=cid,repeat=repeat,trace=adapter.forward_receipt))
        if canonical(outputs[0])!=canonical(outputs[1]) or canonical(native[0])!=canonical(native[1]):
            raise RuntimeError('NATIVE_NONREPEATABILITY; no retry')
        repeats.append(dict(case_id=cid,identical=True))
        predictions[name][cid]=outputs[0]
    prediction_hash=write(out/'predictions.json',predictions)
    write(out/'prediction_seal.json',dict(sha256=prediction_hash,registration_sha256=sha(study/'registration.json'),labels_scored=False))
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    if peak>MAX_RSS:raise RuntimeError('RSS_LIMIT')
    verify(study);verify_installation(entry)
    write(out/'forward_evidence.json',forwards)
    write(out/'resources.json',dict(native_calls=len(timings),attempted_cases=len(requests),timings=timings,
        repeats=repeats,model_load_seconds=load_seconds,worker_seconds=time.monotonic()-start,
        kernel_peak_rss_bytes=peak,cpu_affinity=sorted(os.sched_getaffinity(0)),numerical_threads=2,
        interop_threads=1,gpu=False,network=network,workers=1,automatic_retries=0))


if __name__=='__main__':
    try:execute(sys.argv[1],sys.argv[2])
    except Exception as exc:
        try:
            out=safe(sys.argv[1])/sys.argv[2]
            if (out/'attempt.json').is_file():
                write(out/'worker_failure.json',dict(status='BLOCKED_RUNTIME',type=type(exc).__name__,message=str(exc)))
        except (ValueError,OSError):pass
        raise
