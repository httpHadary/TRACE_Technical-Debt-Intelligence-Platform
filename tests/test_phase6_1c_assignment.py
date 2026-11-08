"""Tiny torch fixtures test documented mechanics. Never load/execute TimesFM."""
import hashlib
import torch
import pytest
from safetensors.torch import save_file,load_file
from forecasting_research.phase6_1c.loader import bind_meta


def fixture(tmp_path):
    cpu=torch.nn.Linear(3,2)
    with torch.no_grad():
        cpu.weight.copy_(torch.arange(6,dtype=torch.float32).reshape(2,3));cpu.bias.copy_(torch.tensor([1.,2.]))
    path=tmp_path/'toy.safetensors';save_file(cpu.state_dict(),str(path))
    state=load_file(str(path),device='cpu',backend='mmap')
    inventory={k:dict(shape=list(v.shape),dtype='F32',sha256=hashlib.sha256(memoryview(v.numpy()).cast('B')).hexdigest()) for k,v in state.items()}
    return cpu,state,inventory


def test_meta_assignment_shares_storage_preserves_values_and_toy_outputs(tmp_path):
    cpu,state,inventory=fixture(tmp_path)
    with torch.device('meta'):meta=torch.nn.Linear(3,2)
    assert all(p.is_meta for p in meta.parameters())
    result=bind_meta(meta,state,inventory)
    assert result['zero_copy_storage_verified'] and result['all_cpu_float32']
    for k,v in meta.state_dict().items():assert v.data_ptr()==state[k].data_ptr()
    x=torch.tensor([[1.,2.,3.]])
    with torch.inference_mode():assert torch.equal(cpu(x),meta(x))


@pytest.mark.parametrize('mutation',('missing','extra','shape','dtype','hash','not_meta','buffer'))
def test_assignment_fails_closed(tmp_path,mutation):
    cpu,state,inventory=fixture(tmp_path)
    with torch.device('meta'):meta=torch.nn.Linear(3,2)
    if mutation=='missing':del state['bias']
    if mutation=='extra':state['unknown']=torch.ones(1)
    if mutation=='shape':state['weight']=torch.ones(1,3)
    if mutation=='dtype':state['weight']=state['weight'].double()
    if mutation=='hash':inventory['weight']['sha256']='0'*64
    if mutation=='not_meta':meta=cpu
    if mutation=='buffer':meta.register_buffer('scratch',torch.ones(1),persistent=False)
    with pytest.raises(ValueError):bind_meta(meta,state,inventory)
