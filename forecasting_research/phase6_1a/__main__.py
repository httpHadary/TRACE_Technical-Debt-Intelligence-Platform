import argparse,json
from pathlib import Path
from .study import prepare
from .run import run
from .evaluate import read_endpoints,summarize
p=argparse.ArgumentParser(description='Phase6.1A synthetic-only paired context study')
p.add_argument('command',choices=['prepare','run','reproduce'])
p.add_argument('--out');p.add_argument('--study');a=p.parse_args()
if a.command=='prepare':
    if not a.out or a.study:p.error('prepare requires --out only')
    r=prepare(a.out);print(json.dumps(dict(status='REGISTERED',population=len(r['population']))))
elif a.command=='run':
    if not a.study or a.out:p.error('run requires --study only')
    r=run(a.study);print(json.dumps(r))
    if r['status']!='PASS':raise SystemExit(3)
else:
    if a.study or a.out:p.error('reproduce uses only packaged synthetic summaries')
    root=Path(__file__).resolve().parents[2]/'examples/phase6_1a'
    result=summarize(read_endpoints(root/'endpoints.csv'),json.loads((root/'registration.json').read_text()))
    expected=json.loads((root/'metrics.json').read_text())
    if result!=expected:raise ValueError('Published endpoint summary reproduction mismatch')
    print(json.dumps({'status':'REPRODUCED','eligible_cases':result['eligible_cases']}))
