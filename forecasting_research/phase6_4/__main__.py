import argparse
from .study import prepare
from .run import run

parser=argparse.ArgumentParser(description='Synthetic Adaptive Persistence: exclusive registration and bounded run')
parser.add_argument('action',choices=('prepare','run'))
parser.add_argument('path')
args=parser.parse_args()
if args.action=='prepare':prepare(args.path)
else:run(args.path)
