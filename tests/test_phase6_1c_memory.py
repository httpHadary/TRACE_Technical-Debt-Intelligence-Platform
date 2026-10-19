"""Static engineering checks only; never construct or forecast with TimesFM."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,struct
import pytest
from forecasting_research.phase6_1c.integrity import entry,literal_config,expected_parameters,inspect_checkpoint,unique_json
from forecasting_research.phase6_1c.loader import require_approval
from forecasting_research.phase6_1c.study import LIMITS,CONFIG,safe
from forecasting_research.phase6_1c.run import limit_failure


def test_exact_model_code_and_weight_identities():
    data=entry()
    assert data['revision']=='1d952420fba87f3c6dee4f240de0f1a0fbc790e3'
    assert data['code_revision']=='e51928e27119cb17bebc005be2696b75e0a9e688'
    assert data['weight_bytes']==925181104 and data['tensor_count']==232


def test_symbolic_pinned_parameter_inventory_without_model_execution():
    data=entry();root=Path(data['private_root'])/'code/timesfm/src/timesfm'
    cfg=literal_config((root/'timesfm_2p5/timesfm_2p5_base.py').read_text())
    parameters=expected_parameters(cfg)
    assert len(parameters)==232
    assert parameters['stacked_xf.19.attn.qkv_proj.weight']['shape']==[3840,1280]
    assert parameters['output_projection_quantiles.output_layer.weight']['shape']==[10240,1280]
    assert parameters['tokenizer.hidden_layer.bias']['shape']==[1280]
    assert CONFIG['fix_quantile_crossing'] is False and CONFIG['infer_is_positive'] is False


def test_symbolic_config_rejects_code_execution():
    text='class TimesFM_2p5_200M_Definition:\n x: int = __import__("os").system("false")\n'
    with pytest.raises(ValueError):literal_config(text)
    with pytest.raises(ValueError):unique_json([('x',1),('x',2)])


def make_checkpoint(tmp_path,*,dtype='F32',shape=None,values=None,offset=None):
    values=values if values is not None else (1.,-2.)
    data=struct.pack('<'+'f'*len(values),*values)
    info={'x':dict(dtype=dtype,shape=[2] if shape is None else shape,data_offsets=[0,len(data)] if offset is None else offset)}
    header=json.dumps(info).encode();path=tmp_path/'toy.safetensors';path.write_bytes(struct.pack('<Q',len(header))+header+data)
    return path,hashlib.sha256(path.read_bytes()).hexdigest()


def test_bounded_static_header_value_and_per_tensor_hashes(tmp_path):
    path,digest=make_checkpoint(tmp_path)
    result=inspect_checkpoint(path,{'x':dict(dtype='F32',shape=[2])},require_hash=digest,require_size=path.stat().st_size)
    assert result['tensor_count']==1 and result['all_finite']
    assert result['tensors']['x']['sha256']==hashlib.sha256(struct.pack('<ff',1.,-2.)).hexdigest()


@pytest.mark.parametrize('mutation',('dtype','shape','nan','gap','missing','hash','size','symlink'))
def test_static_checkpoint_failure_modes(tmp_path,mutation):
    kwargs={'dtype':'F16'} if mutation=='dtype' else {'shape':[1]} if mutation=='shape' else {'values':(float('nan'),2.)} if mutation=='nan' else {'offset':[4,12]} if mutation=='gap' else {}
    path,digest=make_checkpoint(tmp_path,**kwargs);expected={'x':dict(dtype='F32',shape=[2])}
    if mutation=='missing':expected['y']=dict(dtype='F32',shape=[1])
    if mutation=='hash':digest='0'*64
    size=path.stat().st_size+(1 if mutation=='size' else 0)
    if mutation=='symlink':
        alias=tmp_path/'alias';alias.symlink_to(path);path=alias
    with pytest.raises(ValueError):inspect_checkpoint(path,expected,require_hash=digest,require_size=size)


def approval_fixture():
    # Protocol unit fixture only, never a real authorization receipt.
    return dict(status='EXPLICIT_OPERATOR_APPROVAL',registration_sha256='a'*64,scope='SMOKE_ONLY',
        operator_evidence='UNIT_TEST_ONLY_NOT_OPERATOR_EVIDENCE',rss_ceiling_bytes=2*1024**3,
        guard_bytes=7*1024**3//4,seconds=900,attempts=1)


@pytest.mark.parametrize('field,value', [('status','NOT_APPROVED'),('scope','UNRESTRICTED'),('operator_evidence',''),
    ('rss_ceiling_bytes',3*1024**3),('guard_bytes',2*1024**3),('seconds',901),('attempts',2),('attempts',True),('registration_sha256','b'*64)])
def test_approval_rejects_missing_scope_changed_identity_or_relaxed_limits(field,value):
    value_ = approval_fixture();value_[field]=value
    with pytest.raises(PermissionError):require_approval(value_,'a'*64)


def test_no_native_action_without_approval(tmp_path,monkeypatch):
    import forecasting_research.phase6_1c.run as control
    marker=[]
    monkeypatch.setattr(control,'safe',lambda x:tmp_path)
    monkeypatch.setattr(control,'verify',lambda x:({},{}))
    monkeypatch.setattr(control,'sha',lambda x:'a'*64)
    monkeypatch.setattr(control,'supervise',lambda *a:marker.append('NATIVE_EXECUTION_FORBIDDEN'))
    approval=tmp_path/'pending.json';approval.write_text(json.dumps(dict(status='NOT_APPROVED')))
    with pytest.raises(PermissionError):control.run(tmp_path,approval)
    assert marker==[] and not (tmp_path/'attempt.json').exists() and not (tmp_path/'approval.json').exists()


@pytest.mark.parametrize('elapsed,rss,logs,total,reason', [(901,0,0,0,'TIMEOUT'),(0,7*1024**3//4+1,0,0,'RSS_LIMIT'),
    (0,0,16*1024**2+1,0,'LOG_LIMIT'),(0,0,0,64*1024**2+1,'OUTPUT_LIMIT'),(0,0,0,0,None)])
def test_resource_failure_policy(elapsed,rss,logs,total,reason):
    assert limit_failure(elapsed,rss,logs,total)==reason
    assert LIMITS['rss_ceiling_bytes']==2*1024**3 and LIMITS['guard_bytes']==7*1024**3//4


@pytest.mark.parametrize('path',('/tmp/phase6_1c','/home/hp/tst/research/forecasting_mvp/phase6_1c/x/../old','/home/hp/tst/research/forecasting_mvp/phase6_1b/x'))
def test_output_ownership(path):
    with pytest.raises(ValueError):safe(path)


def test_static_inspector_has_no_timesfm_or_torch_import():
    import ast,forecasting_research.phase6_1c.integrity as module
    tree=ast.parse(Path(module.__file__).read_text())
    imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
    assert not any(n and n.startswith(('torch','timesfm')) for n in imports)


def test_supervisor_retains_immediate_nonzero_exit_and_stderr(tmp_path):
    import sys
    from forecasting_research.phase6_1c.run import supervise
    result=supervise([sys.executable,'-c','import sys;print("fixture-stderr",file=sys.stderr);sys.exit(23)'],tmp_path)
    assert result['exit_code']==23 and result['status']=='BLOCKED_RUNTIME'
    assert 'fixture-stderr' in (tmp_path/'worker.log').read_text()


def test_supervisor_limit_stops_owned_child_without_retry(tmp_path,monkeypatch):
    import sys
    import forecasting_research.phase6_1c.run as control
    monkeypatch.setattr(control,'limit_failure',lambda *args:'TIMEOUT')
    result=control.supervise([sys.executable,'-c','import time;time.sleep(2)'],tmp_path)
    assert result['failure']=='TIMEOUT' and result['exit_code']!=0


def test_resource_admission_failure_never_starts_native_worker(tmp_path,monkeypatch):
    import forecasting_research.phase6_1c.run as control
    from forecasting_research.phase6_1c.integrity import entry
    monkeypatch.setattr(control,'safe',lambda x:tmp_path)
    monkeypatch.setattr(control,'verify',lambda x:({},{}))
    monkeypatch.setattr(control,'sha',lambda x:'a'*64)
    monkeypatch.setattr(control,'admission',lambda x:dict(eligible=False))
    monkeypatch.setattr(control,'concurrent_workloads',lambda:[])
    def forbidden(*args):raise AssertionError('Worker launch forbidden')
    monkeypatch.setattr(control,'supervise',forbidden)
    (tmp_path/'static_audit.json').write_text(json.dumps({'model':entry()}))
    approval=tmp_path/'unit-approval.json';approval.write_text(json.dumps(approval_fixture()))
    result=control.run(tmp_path,approval)
    assert result['status']=='BLOCKED_RESOURCE'
    with pytest.raises(FileExistsError):control.run(tmp_path,approval)
