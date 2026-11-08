import argparse
import json
from pathlib import Path
from .study import prepare
from .run import run
from .evaluate import summarize, read_rows

p = argparse.ArgumentParser(description='Phase6.1B synthetic-only comparison; no acquisition')
p.add_argument('command',choices=['prepare','run','reproduce'])
p.add_argument('--study')
p.add_argument('--out')
p.add_argument('--reuse-prior')
a = p.parse_args()
if a.command=='prepare':
    if not a.out or a.study:
        p.error('prepare requires --out only')
    reg = prepare(a.out,a.reuse_prior)
    print(json.dumps(dict(status='REGISTERED',cases=len(reg['population']))))
elif a.command=='run':
    if not a.study or a.out:
        p.error('run requires --study only')
    print(json.dumps(run(a.study)))
else:
    if a.out or a.study:
        p.error('reproduce uses published synthetic summaries only')
    root=Path(__file__).resolve().parents[2]/'examples/phase6_1b'
    result=summarize(read_rows(root/'endpoints.csv'),json.loads((root/'registration.json').read_text()),json.loads((root/'execution_status.json').read_text()))
    if result!=json.loads((root/'metrics.json').read_text()):
        raise ValueError('Published numerical reproduction mismatch')
    print(json.dumps(dict(status='REPRODUCED',eligible_cases=result['eligible_cases'])))
