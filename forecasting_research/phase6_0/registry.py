"""Documented eligibility is separate from execution permission and local availability."""
from pathlib import Path
import json
from .contracts import Request


def registry():
    doc=json.loads(Path(__file__).with_name('model_eligibility.json').read_text())
    return {r['key']:r for r in doc['models']}


def compatible(key,request,*,execute=False):
    if not isinstance(request,Request) or key not in registry():raise ValueError('Registered model and typed input required')
    model=registry()[key]
    if execute and key!='chronos_small':raise ValueError('No new candidate runtime is authorized in Phase 6.0')
    if key not in ('chronos_small','ttm_daily','timesfm_2_5'):
        raise ValueError('Not eligible for direct full 30/60/90 experiment')
    length=512 if key=='ttm_daily' else len(request.values)
    if key=='chronos_small':length=90
    if not request.complete_daily(length) or length>model['context_capacity'] or model['native_horizon_capacity']<90:
        raise ValueError('Unsupported daily context/horizon; no synthetic padding or recursion')
    return dict(api_compatible=True,runtime_verified=key=='chronos_small',real_data_admitted=False)
