import argparse
import json
from pathlib import Path
from forecasting_research.phase6_0.artifacts import write
from .integrity import audit
from .study import safe,prepare

p=argparse.ArgumentParser(description='TimesFM static feasibility; native run requires separate explicit approval')
p.add_argument('command',choices=['audit','prepare','run'])
p.add_argument('--out');p.add_argument('--audit');p.add_argument('--study');p.add_argument('--approval')
a=p.parse_args()
if a.command=='audit':
    if not a.out or a.audit or a.study or a.approval:p.error('audit requires --out only')
    target=safe(a.out)
    if target.exists():p.error('Fresh audit file required')
    target.parent.mkdir(parents=True,exist_ok=True)
    result=audit();write(target,result)
    print(json.dumps(dict(status=result['status'],tensors=result['checkpoint']['tensor_count'],native_forecasts=0)))
elif a.command=='prepare':
    if not a.out or not a.audit or a.study or a.approval:p.error('prepare requires --out and --audit only')
    result=prepare(a.out,json.loads(Path(a.audit).read_text()))
    print(json.dumps(dict(status='REGISTERED_PENDING_APPROVAL',smoke=result['smoke_case_id'])))
else:
    if not a.study or not a.approval or a.out or a.audit:p.error('run requires --study and --approval only')
    from .run import run
    print(json.dumps(run(a.study,a.approval)))
