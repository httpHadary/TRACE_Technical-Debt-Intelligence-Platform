import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import copy
import os
import subprocess
import pytest
import config
from contracts import write_json


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import requests
    def forbidden(*args, **kwargs):
        raise AssertionError('Offline tests must not use network')
    monkeypatch.setattr(requests.sessions.Session, 'request', forbidden)


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    import scan_snapshot
    import sonar_evidence
    repo = tmp_path/'repo'
    repo.mkdir()
    real_run = subprocess.run
    def git(*args, date=None):
        env = dict(os.environ)
        if date:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        return real_run(['git','-C',str(repo),*args], env=env, check=True, capture_output=True, text=True).stdout.strip()
    git('init','-b','main')
    git('config','user.email','test@example.invalid')
    git('config','user.name','Offline Fixture')
    paths = ['src/main/java/com/acme/core/A.java', 'src/main/java/com/acme/core/B.java']
    for path in paths:
        p = repo/path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('package com.acme.core;\npublic class '+p.stem+' {}\n')
    (repo/'pom.xml').write_text('<project/>')
    git('add','.')
    git('commit','-m','root',date='2020-01-01T00:00:00Z')
    commit = git('rev-parse','HEAD')
    git('commit','--allow-empty','-m','calendar cap',date='2023-01-01T00:00:00Z')
    work = tmp_path/'sample'
    work.mkdir()
    monkeypatch.chdir(work)
    for name, value in {'REPO_PATH':str(repo),'KAFKA_REPO_PATH':str(repo),'REPOSITORY_ID':'sample',
                        'PROJECT_KEY':'p:sample','BRANCH':'main','SCANNER_IMAGE':'scanner@sha256:'+'a'*64,
                        'JAVA_BINARIES_PATH':None,'MODULE_STRATEGY':'auto','MODULE_PACKAGE_EXTRA_DEPTH':1,
                        'EXTRA_PRODUCTION_ROOTS':(),'SONAR_TOKEN':'SECRET_TEST_TOKEN'}.items():
        monkeypatch.setattr(config,name,value)
    state = {'repo':repo,'work':work,'paths':paths,'commit':commit,'git':git,'docker_calls':0,
             'ce_status':'SUCCESS','analysis':'analysis1','profile_parameter':'1','issues':[],
             'measures':{},'fail_endpoint':None,'returncode':0}

    class FakeClient:
        def __init__(self, directory):
            self.directory = directory
            self.sequence = 0
        def get(self, endpoint, params=None, text=False):
            if endpoint == state['fail_endpoint']:
                raise OSError('Simulated transport failure')
            params = params or {}
            if endpoint == '/api/server/version':
                data = '10.0.0'
            elif endpoint == '/api/plugins/installed':
                data = {'plugins':[{'key':'java','version':'7.0.0'}]}
            elif endpoint == '/api/qualityprofiles/search':
                data = {'profiles':[{'key':'profile','language':'java'}]}
            elif endpoint == '/api/rules/search':
                data = {'total':1,'rules':[{'key':'java:S1','name':'Synthetic rule'}],
                        'actives':{'java:S1':[{'qProfile':'profile','severity':'MAJOR','params':[{'key':'limit','value':state['profile_parameter']}]}]}}
            elif endpoint == '/api/ce/task':
                data = {'task':{'id':'task1','componentKey':config.PROJECT_KEY,'status':state['ce_status'],
                                'analysisId':state['analysis'],'executedAt':'2024-01-01T00:00:00Z'}}
            elif endpoint == '/api/project_analyses/search':
                data = {'analyses':[{'key':state['analysis'],'revision':state.get('revision',commit)}]}
            elif endpoint == '/api/measures/component_tree':
                import build_module_mart as mart
                components = []
                for path in paths:
                    values = {k:'0' for k in ['ncloc',*mart.SUM_MEASURES]}
                    values.update(ncloc='100',lines='120',complexity='10')
                    values.update(state['measures'].get(path,{}))
                    components.append({'key':config.PROJECT_KEY+':'+path,'path':path,'language':'java',
                        'measures':[{'metric':k,'value':v} for k,v in values.items() if v is not None]})
                data = {'paging':{'total':len(components),'pageIndex':1,'pageSize':500},'components':components}
            elif endpoint == '/api/issues/search':
                data = {'total':len(state['issues']),'issues':state['issues']}
            else:
                raise AssertionError(endpoint)
            self.sequence += 1
            write_json(self.directory/f'{self.sequence:04d}.json',{'endpoint':endpoint,'params':params,'response':data})
            return copy.deepcopy(data)

    def fake_run(cmd, *args, **kwargs):
        if cmd[0] != 'docker':
            return real_run(cmd,*args,**kwargs)
        state['docker_calls'] += 1
        evidence = next(a.removesuffix(':/td-evidence') for a in cmd if a.endswith(':/td-evidence'))
        report = Path(evidence)/'work/report-task.txt'
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(f'ceTaskId=task1\nprojectKey={config.PROJECT_KEY}\nserverUrl={config.SONAR_URL_FROM_SCANNER}\n')
        return subprocess.CompletedProcess(cmd,state['returncode'],'scanner output SECRET_TEST_TOKEN','')
    monkeypatch.setattr(subprocess,'run',fake_run)
    state['client'] = FakeClient
    def collect(label='week_01'):
        scan_snapshot.scan_snapshot(commit,label,client_factory=FakeClient)
        return sonar_evidence.collect_snapshot(label,client_factory=FakeClient)
    state['collect'] = collect
    return state
