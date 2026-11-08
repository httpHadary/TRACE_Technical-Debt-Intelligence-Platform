"""Fresh claimed statistical worker with measured RSS/wall/output bounds."""
import json
import os
from pathlib import Path
import resource
import signal
import socket
import subprocess
import sys
import time
from .experiment import safe, verify, write, read, sha, LIMITS, execute


def limit_failure(seconds,rss,logs,output):
    for actual,maximum,reason in [(seconds,LIMITS['wall_seconds'],'TIMEOUT'),(rss,LIMITS['rss_bytes'],'RSS_LIMIT'),
            (logs,LIMITS['log_bytes'],'LOG_LIMIT'),(output,LIMITS['output_bytes'],'OUTPUT_LIMIT')]:
        if actual>maximum:return reason
    return None


def prohibited_processes():
    found=[]
    for p in Path('/proc').glob('[0-9]*/cmdline'):
        try:args=p.read_bytes().decode(errors='replace').strip('\0').split('\0')
        except OSError:continue
        if not args:continue
        binary=Path(args[0]).name
        model_worker=any(a.startswith('forecasting_research.phase6_') and a.endswith('.worker') for a in args)
        this_worker='forecasting_research.phase6_5' in args and '--worker' in args
        if binary in ('java','mvn','sonar-scanner') or model_worker or this_worker:
            found.append(dict(pid=int(p.parent.name),category='JAVA_OR_MODEL_WORKER'))
    return found


def run(path):
    root=safe(path);verify(root)
    mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
    disk=os.statvfs(root);conflicts=prohibited_processes();size=sum(p.stat().st_size for p in root.iterdir() if p.is_file())
    admitted=mem>=4*1024**3 and disk.f_bavail*disk.f_frsize>=256*1024**2 and not conflicts and size<LIMITS['output_bytes']
    write(root/'admission.json',dict(eligible=admitted,host_available_ram_bytes=mem,free_disk_bytes=disk.f_bavail*disk.f_frsize,
            prohibited_processes=conflicts,input_payload_bytes=size,limits=LIMITS))
    if not admitted:
        write(root/'supervisor.json',dict(status='BLOCKED_RESOURCE',reason='LIVE_ADMISSION_FAILED',worker_started=False));return
    write(root/'attempt.json',dict(owner='phase6_5.information.v1',attempts=1,registration_sha256=sha(root/'registration.json')))
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','CUDA_VISIBLE_DEVICES':'',
         'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'}
    cpus=sorted(os.sched_getaffinity(0))[:2]
    cmd=['taskset','-c',','.join(map(str,cpus)),sys.executable,'-m','forecasting_research.phase6_5','--worker',str(root)]
    start=time.monotonic();peak=0;reason=None;code=None;proc=None
    try:
        with (root/'worker.stdout').open('xb') as out,(root/'worker.stderr').open('xb') as err:
            proc=subprocess.Popen(cmd,env=env,stdout=out,stderr=err,close_fds=True,start_new_session=True)
            while proc.poll() is None:
                try:
                    usage=[int(s.split()[1])*1024 for s in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if s.startswith(('VmRSS:','VmHWM:'))]
                    peak=max([peak,*usage])
                except OSError:pass
                total=sum(p.stat().st_size for p in root.iterdir() if p.is_file())
                reason=limit_failure(time.monotonic()-start,peak,out.tell()+err.tell(),total)
                if reason:os.killpg(proc.pid,signal.SIGKILL);break
                time.sleep(.01)
            code=proc.wait()
    finally:
        if proc and proc.poll() is None:
            os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        final=read(root/'worker_resources.json') if (root/'worker_resources.json').exists() else None
        if final:
            peak=max(peak,final['peak_rss_bytes'])
            reason=reason or limit_failure(time.monotonic()-start,peak,0,sum(p.stat().st_size for p in root.iterdir() if p.is_file()))
        receipt=dict(status='PASS' if code==0 and not reason else 'BLOCKED_RESOURCE' if reason else 'FAILED',exit_code=code,reason=reason,
                command=cmd,wall_seconds=time.monotonic()-start,peak_observed_rss_or_hwm_bytes=peak or None,
                worker=final,limits=LIMITS,monitoring='10ms /proc RSS/HWM plus final ru_maxrss; not a dedicated cgroup',
                cgroup_oom_events='UNAVAILABLE',network='Python socket connections denied, no namespace claim',
                dependency_acquisition=0,pretrained_runs=0)
        write(root/'supervisor.json',receipt)
    return receipt


def worker(path):
    root=safe(path);start=time.monotonic();failure=None;code=1
    try:
        resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
        resource.setrlimit(resource.RLIMIT_CPU,(900,900))
        resource.setrlimit(resource.RLIMIT_FSIZE,(LIMITS['file_bytes'],LIMITS['file_bytes']))
        def denied(*args,**kwargs):raise RuntimeError('NETWORK_NOT_ADMITTED')
        socket.socket.connect=denied;socket.create_connection=denied
        claim=read(root/'attempt.json')
        if claim['owner']!='phase6_5.information.v1' or claim['registration_sha256']!=sha(root/'registration.json'):
            raise ValueError('Attempt identity mismatch')
        result=execute(root);write(root/'completion.json',result);code=0
    except BaseException as exc:
        failure=dict(type=type(exc).__name__,message=str(exc));raise
    finally:
        u=resource.getrusage(resource.RUSAGE_SELF)
        write(root/'worker_resources.json',dict(exit_code=code,failure=failure,wall_seconds=time.monotonic()-start,
              peak_rss_bytes=u.ru_maxrss*1024,user_cpu_seconds=u.ru_utime,system_cpu_seconds=u.ru_stime,
              numerical_threads_max=2,runtime='stdlib only',python=sys.version,network_connections='DENIED'))
