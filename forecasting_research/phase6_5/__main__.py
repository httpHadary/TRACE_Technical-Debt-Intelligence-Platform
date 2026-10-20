import argparse
from .experiment import prepare
from .runner import run, worker
p=argparse.ArgumentParser(description='Isolated synthetic information adequacy study')
g=p.add_mutually_exclusive_group(required=True)
g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true');g.add_argument('--worker',action='store_true')
p.add_argument('path');a=p.parse_args()
(prepare if a.prepare else worker if a.worker else run)(a.path)
