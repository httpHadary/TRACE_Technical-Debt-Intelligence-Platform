"""Versioned meta + mmap + assign loader. No TimesFM import before approval."""
from pathlib import Path
import hashlib
import inspect
from forecasting_research.phase6_0.artifacts import sha
from .integrity import entry, MODEL, REVISION, WEIGHT_SHA


def require_approval(approval, registration_sha256):
    required={'status','registration_sha256','scope','operator_evidence','rss_ceiling_bytes','guard_bytes','seconds','attempts'}
    if (not isinstance(approval,dict) or set(approval)!=required or approval['status']!='EXPLICIT_OPERATOR_APPROVAL'
            or approval['registration_sha256']!=registration_sha256
            or approval['scope'] not in ('SMOKE_ONLY','SMOKE_AND_REGISTERED_36')
            or not isinstance(approval['operator_evidence'],str) or not approval['operator_evidence'].strip()
            or any(type(approval[k]) is not int for k in ('rss_ceiling_bytes','guard_bytes','seconds','attempts'))
            or approval['rss_ceiling_bytes']!=2*1024**3 or approval['guard_bytes']!=7*1024**3//4
            or approval['seconds']!=900 or approval['attempts']!=1):
        raise PermissionError('Separate explicit operator approval for this sealed registration required')
    return approval['scope']


def bind_meta(module, state, inventory):
    """Generic tested primitive; no TimesFM construction or forecast here."""
    import torch
    if 'assign' not in inspect.signature(module.load_state_dict).parameters:
        raise RuntimeError('Installed Torch lacks documented assignment API')
    current=module.state_dict()
    if set(current)!=set(inventory) or set(state)!=set(inventory):
        raise ValueError('Complete exact state mapping required')
    if list(module.named_buffers()):
        raise ValueError('Unexpected persistent/nonpersistent buffers; do not invent materialization')
    for key,expected in inventory.items():
        old,new=current[key],state[key]
        if (old.device.type!='meta' or old.dtype!=torch.float32 or list(old.shape)!=expected['shape']
                or new.device.type!='cpu' or new.dtype!=torch.float32 or list(new.shape)!=expected['shape']
                or not new.is_contiguous()):
            raise ValueError('Meta mapping or checkpoint tensor properties mismatch: '+key)
    result=module.load_state_dict(state,strict=True,assign=True)
    if result.missing_keys or result.unexpected_keys:raise ValueError('Incomplete assignment')
    assigned=module.state_dict()
    hashes={}
    for key,param in assigned.items():
        source=state[key]
        if (param.device.type!='cpu' or param.dtype!=torch.float32 or not param.is_contiguous()
                or param.data_ptr()!=source.data_ptr() or param.storage_offset()!=source.storage_offset()
                or list(param.shape)!=inventory[key]['shape']):
            raise ValueError('Assignment allocated/reinterpreted tensor storage')
        view=param.detach().numpy()
        if view.__array_interface__['data'][0]!=param.data_ptr():raise ValueError('Hashing must share tensor storage')
        digest=hashlib.sha256(memoryview(view).cast('B')).hexdigest()
        if digest!=inventory[key]['sha256']:raise ValueError('Assigned tensor bytes changed: '+key)
        hashes[key]=digest
    return dict(exact_keys=True,all_cpu_float32=True,zero_copy_storage_verified=True,tensor_sha256=hashes)


def load_timesfm(audit,approval,registration_sha256):
    require_approval(approval,registration_sha256)
    data=entry()
    if audit['model']!=data or audit['checkpoint']['checkpoint_sha256']!=WEIGHT_SHA:
        raise ValueError('Static admission identity mismatch')
    path=Path(data['checkpoint_root'])/'model.safetensors'
    if sha(path)!=WEIGHT_SHA:raise ValueError('Checkpoint drift before loading')
    import torch
    from safetensors.torch import load_file
    import timesfm
    if torch.__version__!='2.11.0+cpu' or torch.version.cuda is not None or torch.cuda.is_available():
        raise RuntimeError('Exact CPU Torch required')
    if 'backend' not in inspect.signature(load_file).parameters:
        raise RuntimeError('Installed safetensors mmap API unavailable')
    with torch.device('meta'):
        model=timesfm.TimesFM_2p5_200M_torch(torch_compile=False)
    # No original load_checkpoint()/from_pretrained(), .to_empty(), random CPU
    # parameter bank, dtype conversion or post-assignment copy is involved.
    if model.model.device.type!='cpu':raise ValueError('CPU model routing required')
    state=load_file(str(path),device='cpu',backend='mmap')
    receipt=bind_meta(model.model,state,audit['checkpoint']['tensors'])
    del state
    model.model.eval()
    return model,receipt
