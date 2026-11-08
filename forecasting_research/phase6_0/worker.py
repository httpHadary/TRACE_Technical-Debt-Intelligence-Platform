"""Only registered synthetic cases; no input dataset path or real-data mode."""
from pathlib import Path
import importlib.metadata,json,os,resource,sys,time
from .runtime import deny_network,MAX_RSS
from .artifacts import write,seal,sha,TASK_ROOT,source_identity
from .synthetic import generate,CHRONOS_CASES
from .contracts import canonical
from .chronos import predict
from .evaluation import score

CHECKPOINT=Path('/home/hp/tst/research/forecasting_mvp/model_cache/chronos-2-small/ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a')
PINS={'chronos-forecasting':'2.3.2','torch':'2.11.0+cpu','transformers':'4.57.6','numpy':'2.4.4','pandas':'3.0.2'}


def execute(output):
    output=Path(output).absolute()
    if ('..' in output.parts or not output.is_relative_to(TASK_ROOT) or any(p.is_symlink() for p in (output,*output.parents))
            or json.loads((output/'attempt.json').read_text()) != dict(owner='phase6_0.synthetic.cpu',attempts=1,
                command='forecasting_research.phase6_0.worker',output=str(output))):
        raise ValueError('Exclusive task-owned synthetic worker directory required')
    # Exclusive execution claim; this directory cannot be used to retry a worker.
    write(output/'worker_claim.json',dict(status='CONSUMED',pid=os.getpid()))
    start=time.monotonic();network=deny_network()
    sources=source_identity();write(output/'source_identity.json',sources)
    resource.setrlimit(resource.RLIMIT_CPU,(900,900));resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
    allowed=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,allowed[:2])
    versions={p:importlib.metadata.version(p) for p in PINS}
    if versions!=PINS:raise RuntimeError('BLOCKED_RUNTIME: pinned dependency drift')
    from forecasting_mvp.chronos_adapter import ChronosSmallAdapter,verify_checkpoint
    admission=verify_checkpoint(CHECKPOINT)
    if json.loads((CHECKPOINT/'checkpoint_admission.json').read_text())!=admission:raise RuntimeError('Admission changed')
    cases=[generate(s,r) for s,r in CHRONOS_CASES]
    from .registry import compatible
    for case in cases:compatible('chronos_small',case.request,execute=True)
    write(output/'registration.json',dict(status='SYNTHETIC_ENGINEERING_TEST',checkpoint=admission,runtime=versions,
          network=network,case_ids=[c.request.case_id for c in cases],context_length=90,native_future_steps=90,
          quantiles=[.1,.5,.9],seed=42,repeat_count=2,threads=2,interop_threads=1,fallback='NONE',selection='fixed synthetic.CHRONOS_CASES before outcomes'))
    write(output/'requests.json',[c.request.as_dict() for c in cases])
    load=time.monotonic();adapter=ChronosSmallAdapter.load_cpu(CHECKPOINT);load_seconds=time.monotonic()-load
    import torch
    assert torch.get_num_threads()==2 and torch.get_num_interop_threads()==1 and not torch.cuda.is_available() and torch.version.cuda is None
    predictions={};timings=[];repeat_receipts=[]
    for case in cases:
        pair=[]
        for repeat in range(2):
            tick=time.monotonic();pair.append(predict(adapter,case.request));timings.append(dict(case_id=case.request.case_id,repeat=repeat,seconds=time.monotonic()-tick))
        equal=canonical(pair[0])==canonical(pair[1])
        repeat_receipts.append(dict(case_id=case.request.case_id,identical=equal))
        if not equal:raise RuntimeError('Native repeatability failed; no reselection')
        predictions[case.request.case_id]=pair[0]
    prediction_sha=write(output/'predictions.json',predictions)
    write(output/'prediction_seal.json',dict(sha256=prediction_sha,labels_scored=False))
    assert sha(output/'predictions.json')==prediction_sha
    sealed=json.loads((output/'predictions.json').read_text())
    result=score(cases,sealed,'chronos_small')
    from .predictors import baseline
    good=[c for c in cases if not sealed[c.request.case_id].get('failure')]
    result['matched_persistence']=score(good,{c.request.case_id:baseline(c.request) for c in good},'persistence') if good else None
    write(output/'evaluation.json',result)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    if peak>MAX_RSS:raise RuntimeError('RSS_LIMIT')
    if verify_checkpoint(CHECKPOINT)!=admission:raise RuntimeError('Checkpoint changed')
    if source_identity()!=sources:raise RuntimeError('Worker source changed during inference')
    write(output/'resources.json',dict(network=network,model_load_seconds=load_seconds,elapsed_seconds=time.monotonic()-start,
          peak_rss_bytes=peak,timings=timings,repeatability=repeat_receipts,cpu_affinity=sorted(os.sched_getaffinity(0)),
          torch_threads=torch.get_num_threads(),torch_interop_threads=torch.get_num_interop_threads(),gpu_used=False,
          active_threads_observation='Numerical thread pools capped; background runtime housekeeping threads may exist'))


if __name__=='__main__':
    output=Path(sys.argv[1]);execute(output)
