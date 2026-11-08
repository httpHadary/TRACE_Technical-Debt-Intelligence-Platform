import copy
import sys
from pathlib import Path
import pandas as pd
import pytest

import build_module_mart as mart
import config
import modules
import sonar_evidence
import scan_weekly_snapshots
from contracts import read_csv, read_json, sha256, write_csv, write_json
from run_all_repos import combine_marts, verify_generation


def prepare(sandbox, weeks):
    sandbox['collect']()
    for w in range(2,weeks+1):
        scan_weekly_snapshots.fill_week_from('week_01',f'week_{w:02d}')


def build(monkeypatch, weeks):
    monkeypatch.setattr(sys,'argv',['build_module_mart.py','2020-01-02','main',str(weeks)])
    mart.main()


def test_full_offline_export_git_features_targets_and_combination(sandbox,monkeypatch):
    # Real temporary Git + real collection/validation/aggregation; only Docker/HTTP are simulated.
    sandbox['measures'][sandbox['paths'][1]]={'complexity':None}
    prepare(sandbox,138)
    build(monkeypatch,138)
    record=verify_generation(sandbox['work'])
    assert record['status']=='COMPLETE' and record['rows']==100
    assert sandbox['docker_calls']==1  # unchanged commit is reused, not scanned 138 times
    header,rows=read_csv('module_td_mart.csv',key='origin_id')
    assert set(header)==set(mart.MART_COLS)
    first=rows[0]
    assert first['week']=='week_27'
    assert first['commit_hash_t0']==sandbox['commit']
    assert first['t0']!=first['commit_timestamp']
    assert first['max_feature_ts']==first['t0']
    assert first['complexity_t0']=='' and first['complexity_missing_files']=='1'
    assert first['complexity_partial_sum']=='10.0'
    assert first['TD_3m_status']=='OBSERVED' and float(first['TD_3m'])==0
    assert first['finding_count_t0']=='0' and float(first['sqale_index_t0'])==0
    assert first['partition']=='TRAIN'
    assert {r['partition'] for r in rows}=={'TRAIN','VALIDATION','TEST','PURGED'}
    original={r['origin_id']:r['partition'] for r in rows}
    # Shorter and longer collections must not rename existing origins or move split boundaries.
    build(monkeypatch,39)
    smaller=read_csv('module_td_mart.csv')[1]
    assert len(smaller)==1 and smaller[0]['origin_id'] in original
    assert smaller[0]['partition']==original[smaller[0]['origin_id']]
    combine_marts(['sample'],set(),sandbox['work'].parent,'module_td_mart.csv','combined.csv')
    assert len(read_csv(sandbox['work'].parent/'combined.csv')[1])==1
    # Too little history replaces old mart with an explicit empty, stable-schema result.
    build(monkeypatch,2)
    empty_header,empty=read_csv('module_td_mart.csv')
    assert not empty and empty_header==mart.MART_COLS
    combine_marts(['sample'],set(),sandbox['work'].parent,'module_td_mart.csv','combined.csv')
    assert read_csv(sandbox['work'].parent/'combined.csv')[1]==[]


def test_stale_generation_rejected_after_failure(sandbox,monkeypatch):
    prepare(sandbox,2)
    build(monkeypatch,2)
    old=sha256('module_weekly_state.csv')
    Path('data/issues_week_02.json').write_text('[{}]')
    with pytest.raises(ValueError):
        build(monkeypatch,2)
    assert sha256('module_weekly_state.csv')==old  # previous generation preserved, not accepted
    assert read_json('module_generation.json')['status']=='FAILED'
    with pytest.raises(ValueError):
        verify_generation(sandbox['work'])


def test_missing_predictor_preserves_observed_debt_target(sandbox,monkeypatch):
    sandbox['measures'][sandbox['paths'][0]]={'ncloc':None}
    prepare(sandbox,39)
    build(monkeypatch,39)
    rows=read_csv('module_td_mart.csv')[1]
    assert len(rows)==1
    assert rows[0]['ncloc_t0']=='' and rows[0]['finding_density_t0']==''
    assert rows[0]['TD_3m_status']=='OBSERVED'


def test_sqale_target_independent_of_missing_issue_effort(sandbox,monkeypatch):
    sandbox['issues']=[{'key':'issue1','component':config.PROJECT_KEY+':'+sandbox['paths'][0],
                      'status':'OPEN','type':'CODE_SMELL','severity':'MAJOR','rule':'java:S1'}]
    sandbox['measures'][sandbox['paths'][0]]={'sqale_index':'25'}
    prepare(sandbox,39)
    build(monkeypatch,39)
    row=read_csv('module_td_mart.csv')[1][0]
    assert row['TD_3m_status']=='UNKNOWN_OBSERVATION' and row['TD_3m']==''
    assert row['SQALE_3m_status']=='OBSERVED' and float(row['SQALE_3m'])==25


def test_deleted_file_uses_historical_package(sandbox):
    repo=sandbox['repo']; git=sandbox['git']
    path=repo/sandbox['paths'][0]
    path.write_text('package alternate.core;\nclass A {}\n')
    git('add','.')
    git('commit','-m','package',date='2023-01-02T00:00:00Z')
    decision=modules.detect_strategy(repo,'HEAD')
    git('rm',str(path))
    git('commit','-m','delete',date='2023-01-03T00:00:00Z')
    commit=git('rev-parse','HEAD')
    mapper=modules.mapper_for_commit(repo,commit,decision)
    assert mapper.module_of(sandbox['paths'][0],source_commit=commit)=='alternate'


@pytest.mark.parametrize('defect',['wrong_repo','duplicate','modified_input'])
def test_combination_rejects_invalid_generation(sandbox,monkeypatch,defect):
    prepare(sandbox,2)
    build(monkeypatch,2)
    header,rows=read_csv('module_weekly_state.csv')
    record=read_json('module_generation.json')
    if defect=='wrong_repo':
        rows[0]['repository_id']='other'
    elif defect=='duplicate':
        rows.append(copy.deepcopy(rows[0]))
    else:
        Path('data/issues_week_01.json').write_text('[{}]')
    if defect!='modified_input':
        write_csv('module_weekly_state.csv',rows,header)
        record['outputs']['module_weekly_state.csv']=sha256('module_weekly_state.csv')
        write_json('module_generation.json',record)
    with pytest.raises(ValueError):
        combine_marts(['sample'],set(),sandbox['work'].parent,'module_weekly_state.csv','combined.csv',False)


def test_bad_commit_rejected_even_when_csv_and_proof_agree(sandbox,monkeypatch):
    prepare(sandbox,2)
    # Recorded evidence is internally intact, but resolver selects another commit.
    real=mart.resolve_weekly_commits
    def wrong(*args,**kwargs):
        result=real(*args,**kwargs)
        result[1]['commit']='e'*40
        return result
    monkeypatch.setattr(mart,'resolve_weekly_commits',wrong)
    with pytest.raises(ValueError,match='snapshot commit'):
        build(monkeypatch,2)


def test_git_history_preserves_spaces_unicode_and_rename(sandbox):
    repo=sandbox['repo']; git=sandbox['git']
    original=repo/sandbox['paths'][0]
    renamed=original.with_name('Space É.java')
    git('mv',str(original),str(renamed))
    git('commit','-m','rename',date='2023-01-02T00:00:00Z')
    events=mart.collect_history(repo,'HEAD')
    assert any(e[3].endswith('Space É.java') and e[4]>0 for e in events)
    assert any(e[3]==sandbox['paths'][0] and e[5]>0 for e in events)
    assert all(e[1] and e[0] is not None for e in events)


def test_backdated_future_branch_not_visible_at_earlier_t0(sandbox):
    git=sandbox['git']; repo=sandbox['repo']
    git('checkout','-b','side',sandbox['commit'])
    p=repo/sandbox['paths'][0]
    p.write_text(p.read_text()+'// future branch change\n')
    git('add','.')
    git('commit','-m','backdated',date='2020-01-03T00:00:00Z')
    side=git('rev-parse','HEAD')
    git('checkout','main')
    git('merge','--no-ff','side','-m','merge later',date='2023-01-02T00:00:00Z')
    from weekly_commits import resolve_weekly_commits
    resolved=resolve_weekly_commits(repo,'2020-01-02','main',2)
    assert all(v['commit']==sandbox['commit'] for v in resolved.values())
    events=mart.collect_history(repo,'HEAD')
    assert any(e[1]==side for e in events)
    ancestors=set(git('rev-list',resolved[1]['commit']).split())
    assert not any(e[1]==side for e in events if e[1] in ancestors)


def test_module_mapping_uses_earliest_structure_and_configuration(sandbox,monkeypatch):
    git=sandbox['git']; repo=sandbox['repo']
    decision=modules.load_or_decide_strategy(repo,sandbox['commit'])
    assert decision['decided_at_commit']==sandbox['commit']
    monkeypatch.setattr(config,'MODULE_PACKAGE_EXTRA_DEPTH',2)
    with pytest.raises(ValueError):
        modules.load_or_decide_strategy(repo,sandbox['commit'])


def test_real_declared_package_not_path_guess(sandbox):
    repo=sandbox['repo']; git=sandbox['git']
    p=repo/sandbox['paths'][0]
    p.write_text('package actual.other;\nclass A {}\n')
    git('add','.')
    git('commit','-m','different declaration',date='2023-01-02T00:00:00Z')
    commit=git('rev-parse','HEAD')
    decision=modules.detect_strategy(repo,commit)
    mapper=modules.mapper_for_commit(repo,commit,decision)
    assert mapper.module_of(sandbox['paths'][0])=='actual'


def test_orphan_files_do_not_fake_second_build_module(sandbox):
    files=['mod/pom.xml','mod/src/main/java/A.java','src/main/java/B.java']
    roots=modules.build_dirs_of(files)
    actual={modules.nearest_build_dir(p,roots) for p in files if modules.is_production_file(p)}-{None}
    assert actual=={'mod'}
