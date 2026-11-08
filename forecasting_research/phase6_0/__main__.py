import argparse
from .benchmark import run
from .runtime import run_chronos
from .artifacts import seal

parser=argparse.ArgumentParser(description='Phase 6.0 synthetic-only engineering tests; no real data')
parser.add_argument('command',choices=['baselines','chronos-synthetic'])
parser.add_argument('--out',required=True)
args=parser.parse_args()
if args.command=='baselines':
    result=run(args.out);print('SYNTHETIC_ENGINEERING_TEST: baseline artifacts sealed')
else:
    result=run_chronos(args.out)
    from pathlib import Path
    if not (Path(args.out)/'manifest.json').exists():seal(Path(args.out))
    print(result)
    if result['status']!='PASS':raise SystemExit(3)
