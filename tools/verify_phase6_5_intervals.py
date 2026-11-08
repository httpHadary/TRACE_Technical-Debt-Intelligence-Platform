"""Post-scoring independent interval arithmetic, no model execution."""
import argparse
import json
import math
from pathlib import Path
import statistics as st
from tools.verify_phase6_5 import load


def calculate(rows):
    if not rows:return None
    for lo,hi,y,current in rows:
        if not all(math.isfinite(v) for v in (lo,hi,y,current)) or not 0<=lo<=hi or current<0:
            raise ValueError('Invalid interval; never sort or repair')
    return dict(n=len(rows),coverage=st.mean(lo<=y<=hi for lo,hi,y,c in rows),
                mean_width=st.mean(hi-lo for lo,hi,y,c in rows),
                normalized_mean_width=st.mean((hi-lo)/max(1.,c) for lo,hi,y,c in rows),
                interval_score=st.mean(hi-lo+10*max(0,lo-y)+10*max(0,y-hi) for lo,hi,y,c in rows),
                collapsed=sum(lo==hi for lo,hi,y,c in rows))


def audit(path):
    root=Path(path);reg=load(root/'registration.json');metrics=load(root/'intervals.json');checks=0
    # Point audit must pass separately; this read-only supplement checks coverage,
    # width and scoring arithmetic against those sealed prediction endpoints.
    for seed in reg['replicas']:
        for role in reg['final_populations']:
            reqs={v['debt']['case_id']:v for v in load(root/f'{seed}.{role}.requests.json')}
            labs=load(root/f'{seed}.{role}.targets.json');ps=load(root/f'{seed}.{role}.predictions.json')
            for m in [v for v in metrics if (v['replica'],v['partition'])==(seed,role)]:
                preds=[v for v in ps if (v['method'],v['horizon'])==(m['method'],m['horizon'])]
                for kind in ('overall','changed','unchanged'):
                    rows=[(v['lo'],v['hi'],labs[v['case_id']][str(v['horizon'])]['value'],reqs[v['case_id']]['debt']['values'][-1]) for v in preds]
                    if kind!='overall':rows=[(lo,hi,y,c) for lo,hi,y,c in rows if (y!=c)==(kind=='changed')]
                    actual=calculate(rows);expected=m[kind]
                    if actual is None:
                        if expected is not None:raise ValueError('Missing group mismatch')
                    else:
                        for key,value in actual.items():
                            if not math.isclose(value,expected[key],rel_tol=1e-11,abs_tol=1e-9):raise ValueError('Interval arithmetic mismatch')
                            checks+=1
    return dict(status='PASS',independent_interval_checks=checks,scope=reg['status'],no_fitting_or_new_forecasts=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('path');a=parser.parse_args()
    print(json.dumps(audit(a.path),sort_keys=True))
