"""Fresh task-owned publication, canonical JSON, and content integrity seals."""
from pathlib import Path
import hashlib
import os
from .contracts import canonical

TASK_ROOT=Path('/home/hp/tst/research/forecasting_mvp/phase6_0')


def fresh(output):
    path=Path(output).absolute()
    if '..' in path.parts or any(p.is_symlink() for p in (path,*path.parents)) or not path.is_relative_to(TASK_ROOT) or path==TASK_ROOT:
        raise ValueError('Fresh task output must be outside Git under phase6_0, without symlinks')
    path.mkdir(parents=True,exist_ok=False)
    return path


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def source_identity():
    project=Path(__file__).resolve().parents[2]
    files=sorted((project/'forecasting_research').rglob('*.py'))
    files += [project/name for name in ('forecasting_mvp/chronos_adapter.py','forecasting_mvp/baselines.py',
              'forecasting_mvp/prediction_input.py','requirements-chronos-cpu-lock.txt')]
    files.append(project/'forecasting_research/phase6_0/model_eligibility.json')
    return {str(p.relative_to(project)):sha(p) for p in files}


def write(path, data):
    raw=canonical(data)+b'\n'
    if len(raw)>16*1024*1024:raise ValueError('Bounded artifact required')
    with Path(path).open('xb') as f:
        f.write(raw);f.flush();os.fsync(f.fileno())
    return hashlib.sha256(raw).hexdigest()


def seal(root):
    files={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
    if 'manifest.json' in files:raise ValueError('Cannot replace sealed evidence')
    write(root/'manifest.json',dict(status='SYNTHETIC_ENGINEERING_TEST',artifacts=files))
    return files
