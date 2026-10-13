import sys
from pathlib import Path
import subprocess
import pytest
import config
import run_all_repos as multi
import run_pipeline as single
import validate_snapshots as validator
import scan_weekly_snapshots as weekly
from contracts import sha256, write_json


def test_validation_empty_is_failure(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys,'argv',['validate_snapshots.py'])
    assert validator.main()!=0


def test_validation_fix_never_deletes(sandbox,monkeypatch):
    sandbox['collect']()
    before=sha256('data/issues_week_01.json')
    monkeypatch.setattr(sys,'argv',['validate_snapshots.py','--fix'])
    assert validator.main()!=0
    assert sha256('data/issues_week_01.json')==before


def test_each_reused_week_is_checked(sandbox,monkeypatch):
    sandbox['collect']()
    weekly.fill_week_from('week_01','week_02')
    Path('data/issues_week_02.json').write_text('[{}]')
    monkeypatch.setattr(sys,'argv',['validate_snapshots.py'])
    assert validator.main()!=0


def test_zero_error_validator_passes_valid(sandbox,monkeypatch):
    sandbox['collect']()
    monkeypatch.setattr(sys,'argv',['validate_snapshots.py'])
    assert validator.main()==0


def test_force_rescan_disabled(monkeypatch):
    monkeypatch.setattr(sys,'argv',['scan_weekly_snapshots.py','--force'])
    with pytest.raises(SystemExit):
        weekly.main()


@pytest.mark.parametrize('row',[
    'repository_id,git_url\n../escape,https://example.invalid/repo\n',
    'repository_id,git_url\na,https://example.invalid/a\na,https://example.invalid/b\n',
    'repository_id,git_url\na,https://user:password@example.invalid/a\n',
    'repository_id,repository_id,git_url\na,b,https://example.invalid/a\n',
    'repository_id,git_url\n'])
def test_registry_invalid(tmp_path,row):
    path=tmp_path/'repos.csv'; path.write_text(row)
    with pytest.raises(ValueError):
        multi.load_repos(path)


def test_workbook_valid_and_duplicate_identity_rejected(tmp_path):
    openpyxl=pytest.importorskip('openpyxl')
    book=openpyxl.Workbook(); sheet=book.active
    sheet.append(['repository_id','git_url','weeks'])
    sheet.append(['sample','https://example.invalid/repo',138])
    path=tmp_path/'repos.xlsx'; book.save(path)
    assert multi.load_repos(path)[0]['weeks']=='138'
    sheet.append(['sample','https://example.invalid/other',138]); book.save(path)
    with pytest.raises(ValueError):
        multi.load_repos(path)


def test_requested_missing_branch_is_not_substituted(sandbox):
    with pytest.raises(ValueError):
        multi.detect_branch(sandbox['repo'],'missing')


def test_corrupt_pinned_context_not_silently_reset(tmp_path):
    (tmp_path/'repo_context.json').write_text('{')
    with pytest.raises(ValueError):
        multi.pinned_start_date(tmp_path)


def test_pipeline_stops_on_validation_error(monkeypatch):
    def failure(*args,**kwargs):
        return subprocess.CompletedProcess(args[0],2)
    monkeypatch.setattr(subprocess,'run',failure)
    with pytest.raises(SystemExit) as exc:
        single.run([sys.executable,'validate_snapshots.py'])
    assert exc.value.code==2


def test_multi_repo_failure_nonzero_and_no_combination(tmp_path,monkeypatch):
    registry=tmp_path/'repos.csv'
    registry.write_text('repository_id,git_url\na,https://example.invalid/a\n')
    def fail(*args):
        raise RuntimeError('synthetic failure')
    monkeypatch.setattr(multi,'run_one_repo',fail)
    monkeypatch.setattr(multi,'combine_marts',lambda *a,**k:pytest.fail('combined a failed run'))
    monkeypatch.setattr(sys,'argv',['run_all_repos.py',str(registry),'--output-dir',str(tmp_path/'runs'),
                                   '--repos-dir',str(tmp_path/'repos')])
    with pytest.raises(SystemExit) as exc:
        multi.main()
    assert exc.value.code==1


def test_skip_scan_does_not_clone_fetch_or_auto_repair(sandbox,monkeypatch):
    from argparse import Namespace
    args=Namespace(branch='main',start_date='2020-01-02',weeks=2,repos_dir=str(sandbox['repo'].parent),
                   output_dir=str(sandbox['work'].parent/'runs'),skip_scan=True,weekly_update=True,
                   refresh_start=False,level='module')
    monkeypatch.setattr(multi,'clone_or_update',lambda *a:pytest.fail('unexpected clone/fetch'))
    monkeypatch.setattr(multi,'fast_forward_branch',lambda *a:pytest.fail('unexpected fetch'))
    commands=[]
    def stop(cmd,**kwargs):
        commands.append(cmd)
        raise RuntimeError('validation intentionally stops test')
    monkeypatch.setattr(multi,'run',stop)
    with pytest.raises(RuntimeError):
        multi.run_one_repo({'repository_id':'repo','git_url':'https://example.invalid/repo'},args)
    assert commands[0][1].endswith('validate_snapshots.py')
    assert '--fix' not in commands[0]
