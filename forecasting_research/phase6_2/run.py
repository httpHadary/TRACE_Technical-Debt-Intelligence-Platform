"""Bounded sequential synthetic worker, no pretrained imports or acquisition."""
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time
from forecasting_research.phase6_0.artifacts import write, sha
from .study import safe, verify, LIMITS


def limit_failure(elapsed, rss, log_bytes, output_bytes):
    if elapsed > LIMITS['wall_seconds']:
        return 'TIMEOUT'
    if rss > LIMITS['rss_bytes']:
        return 'RSS_LIMIT'
    if log_bytes > LIMITS['log_bytes']:
        return 'LOG_LIMIT'
    if output_bytes > LIMITS['output_bytes']:
        return 'OUTPUT_LIMIT'
    return None


def concurrent_workers():
    found = []
    for path in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            argv = path.read_bytes().decode(errors='replace').strip('\0').split('\0')
        except (OSError, ProcessLookupError):
            continue
        if any(v.startswith('forecasting_research.phase6_') and v.endswith('.worker') for v in argv):
            found.append(int(path.parent.name))
    return found


def run(path):
    root = safe(path)
    verify(root)
    mem = {s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')}
    disk = os.statvfs(root)
    concurrent = concurrent_workers()
    admitted = mem['MemAvailable'] >= 4*1024**3 and disk.f_bavail*disk.f_frsize >= 256*1024**2 and not concurrent
    write(root/'admission.json',dict(available_ram_bytes=mem['MemAvailable'],free_disk_bytes=disk.f_bavail*disk.f_frsize,
                                  eligible=admitted,concurrent_model_workers=concurrent,limits=LIMITS))
    if not admitted:
        write(root/'supervisor.json',dict(status='BLOCKED_RESOURCE',reason='RAM/disk admission; no worker started'))
        return
    write(root/'attempt.json',dict(owner='phase6_2.synthetic.numpy.v1',attempts=1,registration_sha256=sha(root/'registration.json')))
    env = {**os.environ, 'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2',
           'NUMEXPR_NUM_THREADS':'2','CUDA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1',
           'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'}
    cpus = sorted(os.sched_getaffinity(0))[:2]
    command = ['taskset','-c',','.join(map(str,cpus)),sys.executable,'-m','forecasting_research.phase6_2.worker',str(root)]
    peak, hwm, reason = 0, 0, None
    start = time.monotonic()
    with (root/'worker.stdout').open('xb') as out, (root/'worker.stderr').open('xb') as err:
        process = subprocess.Popen(command,env=env,stdout=out,stderr=err,start_new_session=True,close_fds=True)
        while process.poll() is None:
            try:
                values = {s.split(':')[0]:int(s.split()[1])*1024 for s in Path(f'/proc/{process.pid}/status').read_text().splitlines() if s.startswith(('VmRSS:','VmHWM:'))}
                peak = max(peak,values.get('VmRSS',0))
                hwm = max(hwm,values.get('VmHWM',0))
            except OSError:
                pass
            logs = out.tell()+err.tell()
            total = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
            reason = limit_failure(time.monotonic()-start,max(peak,hwm),logs,total)
            if reason:
                try:
                    os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
                break
            time.sleep(.01)
        code = process.wait()
    final = json.loads((root/'worker_resources.json').read_text()) if (root/'worker_resources.json').exists() else None
    if final and final['peak_rss_bytes'] > LIMITS['rss_bytes']:
        reason = reason or 'RSS_LIMIT'
    receipt = dict(status='PASS' if code==0 and not reason else 'BLOCKED_RESOURCE' if reason else 'FAILED',
                   reason=reason,exit_code=code,command=command,wall_seconds=time.monotonic()-start,
                   sampled_peak_rss_bytes=peak or None,kernel_sampled_hwm_bytes=hwm or None,
                   worker_finally_receipt=final,limits=LIMITS,
                   monitoring='10ms RSS/HWM + kernel final ru_maxrss; process supervisor, not cgroup enforcement',
                   no_native_model_process=True,network='No network calls; worker Python socket connections denied; not network namespace isolation')
    write(root/'supervisor.json',receipt)
    write(root/'artifact_manifest.json',dict(status='SYNTHETIC_ENGINEERING_TEST',artifacts={p.name:sha(p) for p in sorted(root.iterdir()) if p.is_file()}))
    return receipt
