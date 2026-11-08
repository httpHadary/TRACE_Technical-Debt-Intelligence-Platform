"""Resource-admitted single-attempt controller. Network allowed only for later Git publication."""
from pathlib import Path
import json,os,time,signal,subprocess
from forecasting_research.phase6_0.artifacts import write,seal
from .study import safe,verify
from .evaluate import evaluate


def supervise(command,study,*,timeout=900,max_rss=2*1024**3):
    if not 0<timeout<=900 or not 0<max_rss<=2*1024**3:raise ValueError('Cannot increase ceilings')
    start=time.monotonic();peak=0;failure=None
    env={**os.environ,'CUDA_VISIBLE_DEVICES':'','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_DATASETS_OFFLINE':'1',
         'HF_HUB_DISABLE_TELEMETRY':'1','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2',
         'NUMEXPR_NUM_THREADS':'2','PYTHONDONTWRITEBYTECODE':'1','TOKENIZERS_PARALLELISM':'false'}
    with (study/'worker.log').open('xb') as log:
        process=subprocess.Popen(command,env=env,stdout=log,stderr=log,start_new_session=True,close_fds=True)
        while process.poll() is None:
            try:
                info=Path(f'/proc/{process.pid}/status').read_text()
                peak=max(peak,next(int(s.split()[1])*1024 for s in info.splitlines() if s.startswith('VmRSS:')))
            except (OSError,StopIteration):pass
            if time.monotonic()-start>timeout:failure='TIMEOUT'
            elif peak>max_rss:failure='RSS_LIMIT'
            elif log.tell()>16*1024**2:failure='LOG_LIMIT'
            elif sum(p.stat().st_size for p in study.rglob('*') if p.is_file())>64*1024**2:failure='OUTPUT_LIMIT'
            if failure:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                break
            time.sleep(.02)
        code=process.wait()
    receipt=dict(status='PASS' if code==0 and failure is None else 'BLOCKED_RUNTIME',failure=failure or ('WORKER_FAILED' if code else None),
         exit_code=code,wall_seconds=time.monotonic()-start,sampled_peak_rss_bytes=peak,
         rss_limit_bytes=max_rss,timeout_seconds=timeout,rss_policy='20ms sampled guard plus worker kernel ru_maxrss check, not cgroup quota')
    write(study/'supervisor.json',receipt);return receipt


def admission(study):
    import shutil
    available=next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
    free=shutil.disk_usage(study).free
    return dict(available_host_ram_bytes=available,free_disk_bytes=free,host_ram_minimum_bytes=4*1024**3,
                disk_minimum_bytes=512*1024**2,eligible=available>=4*1024**3 and free>=512*1024**2)


def run(path):
    study=safe(path);verify(study)
    # Claim even an admission failure, so resource changes cannot trigger automatic retries.
    write(study/'attempt.json',dict(owner='phase6_1a.context.cpu',attempts=1,study=str(study)))
    resources=admission(study);write(study/'host_admission.json',resources)
    executable=Path(__file__).resolve().parents[2]/'.venv-chronos-cpu/bin/python'
    if not resources['eligible'] or not executable.is_file():
        result=dict(status='BLOCKED_RESOURCES' if not resources['eligible'] else 'BLOCKED_RUNTIME',failure='ADMISSION_FAILED' if not resources['eligible'] else 'PINNED_ENVIRONMENT_MISSING')
        write(study/'outcome.json',result);seal(study);return result
    result=supervise([str(executable),'-m','forecasting_research.phase6_1a.worker',str(study)],study)
    if result['status']=='PASS':
        reg,requests=verify(study);metrics=evaluate(study,reg,requests)
        result=dict(status='PASS',eligible_cases=metrics['eligible_cases'],native_failures={k:v for k,v in metrics['failure_rate'].items() if k.startswith('chronos')},
                    scope='SYNTHETIC_ENGINEERING_TEST; not real-world improvement evidence')
    write(study/'outcome.json',result);seal(study);return result
