"""Linux bounded CPU worker with kernel-denied networking, no new dependencies."""
import ctypes,errno,json,os,platform,resource,signal,subprocess,sys,time
from pathlib import Path
from .artifacts import fresh,write,seal

MAX_RSS=2*1024**3


def deny_network():
    # Linux x86_64 seccomp data: nr @0, arch @4. Deny socket/connect/sendto/sendmsg.
    if sys.platform!='linux' or platform.machine()!='x86_64':raise RuntimeError('Unsupported network sandbox platform')
    class Filter(ctypes.Structure):_fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint32)]
    class Program(ctypes.Structure):_fields_=[('len',ctypes.c_ushort),('filter',ctypes.POINTER(Filter))]
    instructions=[(0x20,0,0,4),(0x15,1,0,0xc000003e),(0x06,0,0,0x80000000),(0x20,0,0,0)]
    for number in (41,42,44,46):instructions.extend([(0x15,0,1,number),(0x06,0,0,0x00050000|errno.EPERM)])
    instructions.append((0x06,0,0,0x7fff0000))
    array=(Filter*len(instructions))(*(Filter(*v) for v in instructions));program=Program(len(array),array)
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(38,1,0,0,0)!=0 or libc.prctl(22,2,ctypes.byref(program),0,0)!=0:
        raise OSError(ctypes.get_errno(),'Network sandbox unavailable')
    import socket
    try:socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    except PermissionError:return 'SECCOMP_SOCKET_DENIED'
    raise RuntimeError('Network sandbox failed verification')


def supervise(command,output,*,timeout=900,max_rss=MAX_RSS):
    if not 0<timeout<=900 or not 0<max_rss<=MAX_RSS:raise ValueError('Cannot increase approved resource ceilings')
    start=time.monotonic();peak=0;failure=None
    environment={**os.environ,'CUDA_VISIBLE_DEVICES':'','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
                 'HF_DATASETS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1','OMP_NUM_THREADS':'2',
                 'MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','NUMEXPR_NUM_THREADS':'2',
                 'PYTHONDONTWRITEBYTECODE':'1','TOKENIZERS_PARALLELISM':'false'}
    with (output/'worker.log').open('xb') as log:
        p=subprocess.Popen(command,env=environment,stdout=log,stderr=log,start_new_session=True,close_fds=True)
        while p.poll() is None:
            try:
                status=Path(f'/proc/{p.pid}/status').read_text()
                peak=max(peak,next(int(line.split()[1])*1024 for line in status.splitlines() if line.startswith('VmRSS:')))
            except (OSError,StopIteration):pass
            if time.monotonic()-start>timeout:failure='TIMEOUT'
            elif peak>max_rss:failure='RSS_LIMIT'
            elif log.tell()>16*1024**2:failure='LOG_LIMIT'
            if failure:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                break
            time.sleep(.02)
        code=p.wait()
    receipt=dict(status='PASS' if code==0 and failure is None else 'BLOCKED_RUNTIME',failure=failure or ('WORKER_FAILED' if code else None),
                 exit_code=code,elapsed_seconds=time.monotonic()-start,sampled_peak_rss_bytes=peak,
                 max_rss_bytes=max_rss,timeout_seconds=timeout,rss_guard='20ms sampled worker RSS plus final ru_maxrss; not cgroup quota')
    write(output/'supervisor.json',receipt)
    return receipt


def run_chronos(output):
    out=fresh(output)
    write(out/'attempt.json',dict(owner='phase6_0.synthetic.cpu',attempts=1,
          command='forecasting_research.phase6_0.worker',output=str(out)))
    executable=Path(__file__).resolve().parents[2]/'.venv-chronos-cpu/bin/python'
    if not executable.is_file():
        receipt=dict(status='BLOCKED_RUNTIME',failure='PINNED_ENVIRONMENT_MISSING')
        write(out/'supervisor.json',receipt);seal(out);return receipt
    return supervise([str(executable),'-m','forecasting_research.phase6_0.worker',str(out)],out)
