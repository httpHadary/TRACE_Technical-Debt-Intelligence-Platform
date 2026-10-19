"""Bounded static inspection. Never imports or instantiates TimesFM."""
from pathlib import Path
import ast
import hashlib
import json
import math
import struct
from forecasting_research.phase6_0.artifacts import sha

MODEL = 'google/timesfm-2.5-200m-pytorch'
REVISION = '1d952420fba87f3c6dee4f240de0f1a0fbc790e3'
CODE_REVISION = 'e51928e27119cb17bebc005be2696b75e0a9e688'
WEIGHT_SHA = '2f776efe6245e42b24bc4153ffdf61810140210e4bd3b01fb21f7aa779ab6ce8'
ADMISSION_SHA = 'a3f225383c7ef182c9fff67149220adee6a450033c6e23ebcf83c3064b0269c9'
WEIGHT_BYTES = 925181104


def entry():
    project=Path(__file__).resolve().parents[2]
    path=project/'forecasting_research/phase6_1b/model_admission.json'
    if sha(path)!=ADMISSION_SHA:
        raise ValueError('Frozen Phase6.1B admission changed')
    data=json.loads(path.read_text())['models']['timesfm512']
    if (data['model_id'],data['revision'],data['code_revision'],data['weight_sha256'])!=(MODEL,REVISION,CODE_REVISION,WEIGHT_SHA):
        raise ValueError('Exact TimesFM2.5 identity required')
    return data


def verify_sources(data):
    root=Path(data['private_root'])
    for name,digest in {**data['code_files'],**data['checkpoint_files']}.items():
        path=root/name
        if path.is_symlink() or sha(path)!=digest:
            raise ValueError('Pinned code/checkpoint identity mismatch: '+name)
    base=Path(data['base_dependency_root'])
    lock=root/'base_environment_before.json'
    if sha(lock)!=data['base_manifest_sha256']:
        raise ValueError('Existing dependency lock changed')
    locked=json.loads(lock.read_text())
    for name,digest in locked.items():
        if sha(base/name)!=digest:
            raise ValueError('Read-only runtime dependency changed: '+name)
    return dict(pinned_code_files=len(data['code_files']),dependency_files=len(locked),
                torch_module_sha256=sha(base/'torch/nn/modules/module.py'),
                safetensors_torch_sha256=sha(base/'safetensors/torch.py'))


def literal_config(source):
    """Read only constants and allowlisted config constructors; no eval/import."""
    tree=ast.parse(source)
    definition=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='TimesFM_2p5_200M_Definition')
    allowed={'ResidualBlockConfig','StackedTransformersConfig','TransformerConfig'}
    def read(node):
        if isinstance(node,ast.Constant):return node.value
        if isinstance(node,ast.List):return [read(x) for x in node.elts]
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in allowed and not node.args:
            return {k.arg:read(k.value) for k in node.keywords if k.arg is not None}
        if (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name)
                and node.func.value.id=='dataclasses' and node.func.attr=='field' and len(node.keywords)==1
                and node.keywords[0].arg=='default_factory' and isinstance(node.keywords[0].value,ast.Lambda)):
            return read(node.keywords[0].value.body)
        raise ValueError('Unsupported symbolic configuration expression')
    return {n.target.id:read(n.value) for n in definition.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name)}


def expected_parameters(config):
    """Independent shape inventory derived from pinned dense/transformer source."""
    expected={}
    def add(name,*shape):expected[name]=dict(dtype='F32',shape=list(shape))
    def linear(name,inputs,outputs,bias=False):
        add(name+'.weight',outputs,inputs)
        if bias:add(name+'.bias',outputs)
    for prefix in ('tokenizer','output_projection_point','output_projection_quantiles'):
        cfg=config[prefix]
        linear(prefix+'.hidden_layer',cfg['input_dims'],cfg['hidden_dims'],cfg['use_bias'])
        linear(prefix+'.output_layer',cfg['hidden_dims'],cfg['output_dims'],cfg['use_bias'])
        linear(prefix+'.residual_layer',cfg['input_dims'],cfg['output_dims'],cfg['use_bias'])
    stack=config['stacked_transformers'];cfg=stack['transformer']
    if (cfg['attention_norm'],cfg['feedforward_norm'],cfg['qk_norm'],cfg['use_bias'],cfg['fuse_qkv'])!=('rms','rms','rms',False,True):
        raise ValueError('Unsupported architecture; do not guess alternate shapes')
    d,h=cfg['model_dims'],cfg['model_dims']//cfg['num_heads']
    for i in range(stack['num_layers']):
        prefix=f'stacked_xf.{i}.'
        for name in ('pre_attn_ln','post_attn_ln','pre_ff_ln','post_ff_ln'):add(prefix+name+'.scale',d)
        linear(prefix+'attn.qkv_proj',d,3*d)
        linear(prefix+'attn.out',d,d)
        for name in ('query_ln','key_ln'):add(prefix+'attn.'+name+'.scale',h)
        add(prefix+'attn.per_dim_scale.per_dim_scale',h)
        linear(prefix+'ff0',d,cfg['hidden_dims'])
        linear(prefix+'ff1',cfg['hidden_dims'],d)
    return expected


def unique_json(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON key')
        result[key]=value
    return result


def inspect_checkpoint(path,expected,*,require_hash=WEIGHT_SHA,require_size=WEIGHT_BYTES):
    """Stream hashes and finite F32 checks in 1 MiB chunks; no model/tensor load."""
    path=Path(path)
    if path.is_symlink() or path.stat().st_size!=require_size:
        raise ValueError('Checkpoint path/size mismatch')
    import numpy as np
    with path.open('rb') as stream:
        raw=stream.read(8)
        if len(raw)!=8:raise ValueError('Incomplete safetensors header')
        length=struct.unpack('<Q',raw)[0]
        if not 0<length<=1024**2:raise ValueError('Bounded header required')
        header_raw=stream.read(length)
        header=json.loads(header_raw,object_pairs_hook=unique_json)
        header.pop('__metadata__',None)
        if set(header)!=set(expected):raise ValueError('Missing/unexpected parameter keys')
        digest=hashlib.sha256(raw+header_raw);position=0;tensors={}
        for key,info in sorted(header.items(),key=lambda item:item[1]['data_offsets'][0]):
            if set(info)!= {'dtype','shape','data_offsets'} or {k:info[k] for k in ('dtype','shape')}!=expected[key]:
                raise ValueError('Parameter shape/dtype mismatch: '+key)
            begin,end=info['data_offsets']
            size=4*math.prod(info['shape'])
            if type(begin) is not int or type(end) is not int or begin!=position or end-begin!=size:
                raise ValueError('Overlapping/gapped/invalid tensor storage')
            per=hashlib.sha256();remaining=size
            while remaining:
                chunk=stream.read(min(1024**2,remaining))
                if not chunk or len(chunk)%4:raise ValueError('Truncated F32 tensor')
                if not np.isfinite(np.frombuffer(chunk,dtype='<f4')).all():raise ValueError('Nonfinite checkpoint tensor')
                per.update(chunk);digest.update(chunk);remaining-=len(chunk)
            tensors[key]=dict(info,sha256=per.hexdigest(),bytes=size)
            position=end
        if stream.read(1) or 8+length+position!=require_size or digest.hexdigest()!=require_hash:
            raise ValueError('Checkpoint content/hash/extent mismatch')
    return dict(checkpoint_sha256=digest.hexdigest(),header_bytes=length,tensor_count=len(tensors),
                parameter_bytes=position,elements=position//4,all_finite=True,tensors=tensors)


def audit():
    data=entry();identities=verify_sources(data)
    root=Path(data['private_root'])/'code/timesfm/src/timesfm'
    config=literal_config((root/'timesfm_2p5/timesfm_2p5_base.py').read_text())
    expected=expected_parameters(config)
    if len(expected)!=232:raise ValueError('Unexpected pinned architecture population')
    result=inspect_checkpoint(Path(data['checkpoint_root'])/'model.safetensors',expected)
    return dict(status='STATIC_PARAMETER_MAPPING_VERIFIED',identities=identities,model=data,
                symbolic_config=config,checkpoint=result,native_model_constructed=False,native_forecasts=0)
