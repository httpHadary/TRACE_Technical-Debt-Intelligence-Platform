import argparse
from .study import prepare
from .run import run

parser = argparse.ArgumentParser(description='Phase6.2 synthetic-only lightweight study; no pretrained run')
parser.add_argument('action',choices=('prepare','run'))
parser.add_argument('directory')
args = parser.parse_args()
result = prepare(args.directory) if args.action=='prepare' else run(args.directory)
print(result.get('status', 'REGISTERED') if result else 'BLOCKED_RESOURCE')
