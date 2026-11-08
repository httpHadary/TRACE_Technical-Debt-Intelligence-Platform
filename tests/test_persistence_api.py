"""Loopback HTTP checks: no framework, external network or model execution."""
import http.client
import json
from pathlib import Path
import shutil
import subprocess
from threading import Thread

import pytest

from contracts import read_json, write_json
from forecasting_mvp.api import create_server
from forecasting_mvp.persistence_flow import build
from test_persistence_flow import EXAMPLES


@pytest.fixture
def local_api(tmp_path):
    registry = tmp_path/'registry'
    registry.mkdir()
    manifest = build(EXAMPLES/'observations.json',registry/'example',EXAMPLES/'actuals.json')
    server = create_server(registry,port=0)
    thread = Thread(target=server.serve_forever,daemon=True)
    thread.start()
    def request(path, method='GET', host=None):
        conn = http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
        headers = {'Host':host} if host else {}
        conn.request(method,path,headers=headers)
        response = conn.getresponse()
        body = response.read()
        result = (response.status,dict(response.getheaders()),json.loads(body) if body and response.getheader('Content-Type','').startswith('application/json') else body.decode())
        conn.close()
        return result
    yield registry,manifest,request
    server.shutdown();server.server_close();thread.join(timeout=5)


def base(manifest):
    return '/api/mvp/v1/bundles/'+manifest['bundle_id']


def test_read_routes_static_and_reports(local_api):
    _,manifest,get = local_api
    assert get('/api/mvp/v1/health')[2]['current_accuracy'] == 'UNVALIDATED'
    assert get('/api/mvp/v1/bundles')[2] == [manifest]
    prefix=base(manifest)
    assert get(prefix)[2] == manifest
    assert get(prefix+'/repositories')[2] == ['synthetic-demo','synthetic-missing']
    route=prefix+'/repositories/synthetic-demo'
    assert len(get(route+'/history')[2]) == 6
    query='?horizon=3&horizon_unit=revision_step&model=persistence'
    f=get(route+'/forecasts'+query)[2][0]
    e=get(route+'/evaluations'+query)[2][0]
    assert f['prediction_minutes']==10 and e['actual_minutes']==12 and e['error_minutes']==-2
    s=get(route+'/evaluations'+query+'&summary=true')[2][0]
    assert s['measured_actuals']==1 and s['unavailable']==1
    assert s['subsets']['all']['macro_mae_minutes']==2
    for path in ['/','/app.js','/style.css']:
        status,headers,body=get(path)
        assert status==200 and body
        assert headers['X-Content-Type-Options']=='nosniff'
        assert "default-src 'self'" in headers['Content-Security-Policy']
    js=get('/app.js')[2]
    assert 'textContent' in js and 'innerHTML' not in js
    assert 'Array.isArray(rows)' in js
    html=get('/')[2]
    assert '<select id="horizon">' in html and 'model-selector' not in html
    assert 'https://' not in html and 'http://' not in html


@pytest.mark.parametrize('suffix', [
    '/forecasts', '/forecasts?horizon=3', '/forecasts?horizon=30&horizon_unit=revision_step',
    '/forecasts?horizon=3&horizon_unit=elapsed_day', '/forecasts?horizon=3&horizon_unit=revision_step&model=chronos',
    '/forecasts?horizon=3&horizon=4&horizon_unit=revision_step',
    '/forecasts?horizon=03&horizon_unit=revision_step', '/history?unexpected=1',
    '/evaluations?horizon=3&horizon_unit=revision_step&summary=false',
])
def test_invalid_queries_are_422(local_api,suffix):
    _,manifest,get=local_api
    assert get(base(manifest)+'/repositories/synthetic-demo'+suffix)[0]==422


@pytest.mark.parametrize('path', ['/missing','/api/mvp/v1/unknown','/api/mvp/v1/bundles/unknown','/api/mvp/v1/bundles/unknown/repositories','/../contracts.py','/%2e%2e/contracts.py'])
def test_unknown_routes_and_containment(local_api,path):
    assert local_api[2](path)[0]==404


@pytest.mark.parametrize('method',['POST','PUT','PATCH','DELETE','HEAD','OPTIONS','TRACE','CONNECT'])
def test_mutation_methods_rejected(local_api,method):
    assert local_api[2]('/api/mvp/v1/bundles',method)[0]==405


def test_localhost_binding_host_and_corruption(local_api):
    registry,manifest,get=local_api
    with pytest.raises(ValueError,match='127.0.0.1'): create_server(registry,host='0.0.0.0',port=0)
    assert get('/api/mvp/v1/bundles',host='attacker.example')[0]==403
    (registry/'example/history.json').write_text('[]')
    assert get('/api/mvp/v1/bundles')[0]==409
    assert get(base(manifest)+'/repositories')[0]==409
    (registry/'example/manifest.json').unlink()
    assert get('/api/mvp/v1/bundles')[0]==409


def test_registered_absent_clock_is_truthful_unsupported_data(local_api,tmp_path):
    registry,_,get=local_api
    source=read_json(EXAMPLES/'observations.json')
    source['horizons']={'elapsed_day':[30,60,90]}
    path=tmp_path/'elapsed-only.json';write_json(path,source)
    m=build(path,registry/'elapsed-only')
    route=base(m)+'/repositories/synthetic-demo/forecasts'
    status,_,result=get(route+'?horizon_unit=revision_step&horizon=3')
    assert status==200 and result['status']=='UNSUPPORTED_DATA' and result['data'] is None
    assert result['reason']
    assert isinstance(get(route+'?horizon_unit=elapsed_day&horizon=30')[2],list)


def test_symlink_registry_entries_rejected(local_api,tmp_path):
    registry,_,get=local_api
    (registry/'escape').symlink_to(tmp_path,target_is_directory=True)
    assert get('/api/mvp/v1/bundles')[0]==409


def test_dashboard_javascript_parses():
    node=shutil.which('node')
    if not node: pytest.skip('Node unavailable; HTTP/static checks still apply')
    js=Path(__file__).resolve().parents[1]/'forecasting_mvp/static/app.js'
    result=subprocess.run([node,'--check',str(js)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
