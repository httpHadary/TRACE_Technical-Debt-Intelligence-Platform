"""Focused validation only: reuse existing SYNTHETIC fixture builder and MVP CLI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from threading import Thread
from urllib.request import urlopen

REPO=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',required=True,help='Fresh output directory, separate from this evidence package')
parser.add_argument('--browser-python',required=True,help='Existing Python with Playwright and cached Chromium; no installation is attempted')
args=parser.parse_args()
ROOT=Path(args.out).resolve()
if ROOT.is_relative_to(Path(__file__).resolve().parent):
    raise ValueError('Output must be outside this published evidence package')
ROOT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(REPO))
from contracts import read_json,write_json
from forecasting_mvp.persistence_flow import load_presentation
from forecasting_mvp.api import create_server

tracked=subprocess.run(['git','ls-files','-z'],cwd=REPO,capture_output=True,check=True).stdout.decode().split('\0')
before={name:hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in tracked if name and (REPO/name).is_file()}
write_json(ROOT/'tracked_before.json',before)
helpers=runpy.run_path(str(REPO/'tests/test_native_project_persistence.py'))
registry=ROOT/'registry';registry.mkdir()
results=[]
for name,languages,missing in [('python',('py',),False),('jsts',('js','ts'),False),('python-missing-security',('py',),True)]:
    case=ROOT/name;case.mkdir()
    fixture=helpers['fixture_archive'](case,languages,missing=missing)
    index,archive,git,record=fixture
    record['entries']=record['entries'][:3]
    write_json(index,record)
    for target in ('native_sqale_index_minutes','native_total_principal_minutes'):
        target_short='sqale' if target=='native_sqale_index_minutes' else 'principal'
        destination=registry/(name+'-'+target_short)
        cmd=[sys.executable,'-m','forecasting_mvp','persistence-ingest-native','--index',str(index),'--archive',str(archive),'--git',str(git),'--target',target,'--out',str(destination)]
        proc=subprocess.run(cmd,cwd=REPO,capture_output=True,text=True,timeout=30,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        (case/(target_short+'-cli.stdout.json')).write_text(proc.stdout)
        (case/(target_short+'-cli.stderr.txt')).write_text(proc.stderr)
        assert proc.returncode==0,(proc.returncode,proc.stderr,proc.stdout)
        bundle=load_presentation(destination)
        expected=None if missing and target_short=='principal' else 12 if target_short=='sqale' else 16
        f=bundle['forecasts'][0]
        assert f['prediction_minutes']==expected
        assert all(x['prediction_minutes']==expected and x['predicted_change_minutes']==(None if expected is None else 0) and x['interval_lower'] is None and x['interval_upper'] is None for x in bundle['forecasts'])
        assert bundle['manifest']['metadata']['evidence']=='SOFTWARE_VALIDATION_ONLY'
        history=bundle['history'];assert len(history)==3
        assert history[-1]['stock_minutes']==expected
        assert history[-1]['components']['security']==(None if missing else 2)
        results.append(dict(case=name,target=target,bundle_id=bundle['manifest']['bundle_id'],repository_id=f['repository_id'],languages=f['native']['languages'],expected_minutes=expected,expected_status='UNAVAILABLE' if expected is None else 'AVAILABLE',forecast_count=len(bundle['forecasts']),forecast_ids=[x['forecast_id'] for x in bundle['forecasts']],bundle_path=str(destination)))
for name in ('python','jsts','python-missing-security'):
    pair=[r for r in results if r['case']==name]
    assert set(pair[0]['forecast_ids']).isdisjoint(pair[1]['forecast_ids'])
write_json(ROOT/'cases.json',results)
server=create_server(registry,port=0);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    base=f'http://127.0.0.1:{server.server_port}'
    api=[]
    for case in results:
        route=base+'/api/mvp/v1/bundles/'+case['bundle_id']+'/repositories/'+case['repository_id']
        for resource in ('history','forecasts?horizon_unit=revision_step&horizon=3','evaluations?horizon_unit=revision_step&horizon=3'):
            with urlopen(route+'/'+resource,timeout=15) as response:
                rows=json.load(response)
                assert response.status==200 and rows[0]['target']==case['target']
                assert rows[0]['native']['languages']==case['languages']
                if resource.startswith('forecasts'):assert rows[0]['prediction_minutes']==case['expected_minutes']
                if resource.startswith('history'):assert rows[-1]['stock_minutes']==case['expected_minutes']
                if resource.startswith('evaluations'):assert rows[0]['status']==('UNAVAILABLE' if case['expected_minutes'] is None else 'PENDING')
                api.append(dict(case=case['case'],target=case['target'],resource=resource,status=200))
    write_json(ROOT/'api_receipt.json',dict(status='PASS',requests=api))
    browser_python=args.browser_python
    proc=subprocess.run([browser_python,str(Path(__file__).with_name('browser_check.py')),base,str(ROOT)],cwd=REPO,capture_output=True,text=True,timeout=120,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    (ROOT/'browser.stdout.txt').write_text(proc.stdout);(ROOT/'browser.stderr.txt').write_text(proc.stderr)
    assert proc.returncode==0,(proc.returncode,proc.stdout,proc.stderr)
finally:
    server.shutdown();server.server_close();thread.join()
assert all(hashlib.sha256((REPO/name).read_bytes()).hexdigest()==value for name,value in before.items())
write_json(ROOT/'result.json',dict(status='PASS_OFFLINE_FIXTURE_E2E',evidence='SYNTHETIC_SOFTWARE_VALIDATION_ONLY',repository_commit=subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,text=True,check=True).stdout.strip(),cases=results,api_requests=len(api),dashboard=read_json(ROOT/'browser_receipt.json'),product_files_unchanged=True,new_scans=0,new_model_runs=0,authentic_export_validated=False))
print(json.dumps(dict(status='PASS_OFFLINE_FIXTURE_E2E',bundles=len(results),api_requests=len(api),browser=read_json(ROOT/'browser_receipt.json')['status'],product_files_unchanged=True)))
