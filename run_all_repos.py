#!/usr/bin/env python3
"""
Runs the full TD-regression pipeline across MULTIPLE repos, each given
as a git URL, and combines the results into one dataset.

Give it a CSV of repos (one row per repo):

    repository_id,git_url,branch,start_date,weeks
    commons-cli,https://github.com/apache/commons-cli.git,master,,120
    slf4j,https://github.com/qos-ch/slf4j.git,master,,120

branch/start_date/weeks columns are optional per-row.
  * start_date blank (or "midpoint")  -> the code computes the repo MIDPOINT (halfway between
    first and latest commit) and starts week 1 config.HISTORY_WEEKS (26) weeks earlier, so the
    first T0 week starts exactly at the midpoint with a full 6-month past behind it.
  * branch blank -> explicit --branch, otherwise the clone's default branch. A missing explicit branch fails.
  * weeks blank  -> --weeks (default 138), capped at the weeks that actually exist
    after start_date.

For each repo, this:
  1. unless --skip-scan, clones it (or fetches latest if already cloned) into
     <repos-dir>/<repository_id>/
  2. writes <output-dir>/<repository_id>/repo_context.json so the SAME
     config.py picks up this repo's KAFKA_REPO_PATH/PROJECT_KEY/
     REPOSITORY_ID without editing config.py per repo
  3. runs the whole pipeline with <output-dir>/<repository_id>/ as the
     working directory (scan -> git features -> Sonar features -> td_mart.csv)
  4. moves on to the next repo -- one repo failing does NOT stop the
     others (logged and skipped; see the summary at the end)

If any repository fails, the command exits nonzero without combining. Otherwise, verified
module generations are combined. Pass --holdout-repos to
mark entire repos as a held-out test set (REPOSITORY_HELD_OUT split)
instead of pooling their rows into the per-repo chronological split.

MODULE LEVEL (default): after scanning, build_module_mart.py aggregates the weekly Sonar snapshots +
git history per MODULE (see modules.py / config.MODULE_STRATEGY) and writes module_weekly_state.csv
(every week x module, with sqale_index), module_latest_snapshot.csv and module_td_mart.csv.
Use --level file for the old file-level mart, or --level both.

WEEKLY COLLECTION: run the same command once a week with --weekly-update. It fast-forwards each clone
to origin, REUSES the start_date pinned in the repo's repo_context.json (so week numbers never shift),
scans only the weeks that are new since the last run, and rebuilds the module outputs.

Usage:
    python3 run_all_repos.py <repos_csv> [--branch trunk] [--start-date 2015-01-01]
                              [--weeks 60] [--holdout-repos repoA,repoB]
                              [--skip-scan] [--resume-from <repository_id>]
                              [--repos-dir C:/repo_clones] [--output-dir G:/MyDrive/td_runs]

--repos-dir is where repos actually get git-cloned. KEEP THIS ON LOCAL
DISK, not a Drive-synced folder -- a git clone is tens of thousands of
small .git object files; syncing that continuously is slow, burns
Drive quota, and git itself gets slower inside a sync-shadowed folder.

--output-dir is where every repo's working directory (all the CSVs
this pipeline writes, and the final td_mart.csv / combined_td_mart.csv)
gets written. THIS is the one safe to point at a Drive-synced folder,
e.g. "G:/My Drive/td_runs" -- it's a modest number of CSV files, and
having them land directly in Drive is exactly what you want for backup
or sharing. Defaults to ./runs if not given.

Requires: config.py + every pipeline script (scan_weekly_snapshots.py,
pipeline_total_line.py, add_weekly_commits_churn.py, pipeline_g3.py,
compute_git_window_features.py, compute_ownership_entropy.py,
compute_lineage.py, compute_sonar_trend_features.py,
compute_finding_lifecycle.py, build_td_mart.py) sitting in the SAME
directory as this script -- they get invoked by absolute path so Python
resolves `import config` against THIS directory regardless of which
repo's working directory a given call runs in.
"""
import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import config
from contracts import digest, read_csv, read_json, safe_id, sha256, write_csv, write_json
from weekly_commits import available_weeks, midpoint_start_date, origin_start_date

PYTHON = sys.executable
SCRIPT_DIR = Path(__file__).resolve().parent

TOTAL_LINES_DIR = "weekly_total_lines"
G3_DIR = "weekly_g3_features"


def here(script_name):
    return str(SCRIPT_DIR / script_name)


def step(title):
    print()
    print("=" * 70)
    print(f">>> {title}")
    print("=" * 70)


def run(cmd, cwd, allow_fail=False):
    print(f"$ (cwd={cwd}) {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0 and not allow_fail:
        raise RuntimeError(f"Step failed (exit {result.returncode}): {' '.join(cmd)}")
    return result.returncode


def normalize_git_url(url):
    """Strips tracking query strings/fragments (e.g. ?utm_source=...) that
    break git's smart-HTTP handshake, and adds .git for GitHub URLs that
    are missing it. Leaves local filesystem paths (no ://) untouched."""
    url = url.strip()
    if "://" not in url:
        return url
    parts = urlsplit(url)
    if parts.username or parts.password:
        raise ValueError('Do not put credentials in repository URLs')
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    if "github.com" in url and not url.endswith(".git"):
        url = url.rstrip("/") + ".git"
    return url


def clone_or_update(git_url, repo_path):
    # Resolve to an ABSOLUTE path first. Previously this stayed relative
    # (e.g. "repo_clones/OFBiz") while also being cloned with cwd set to
    # its own parent ("repo_clones") -- that applies the relative segment
    # TWICE, so the repo actually lands at repo_clones/repo_clones/OFBiz
    # while repo_context.json (and every later step) looks for it one
    # level up and fails with "No such file or directory". Resolving to
    # an absolute path here makes the cwd argument irrelevant and fixes
    # that double-nesting for good.
    repo_path = Path(repo_path).resolve()
    if (repo_path / ".git").exists():
        remote = subprocess.run(['git', '-C', str(repo_path), 'remote', 'get-url', 'origin'],
                                check=True, capture_output=True, text=True).stdout.strip()
        if normalize_git_url(remote) != git_url:
            raise ValueError('Existing clone belongs to another repository')
        print(f">>> {repo_path} already cloned -- fetching latest.")
        run(["git", "fetch", "--all"], cwd=str(repo_path))
    else:
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        print(f">>> Cloning {git_url} -> {repo_path}")
        run(["git", "clone", git_url, str(repo_path)], cwd=str(repo_path.parent))


def fast_forward_branch(repo_path, branch):
    """Move the LOCAL branch to origin/<branch>. (`git fetch` alone does not: the pipeline resolves
    weekly commits from the local branch, so without this a weekly re-run would never see new commits.)"""
    run(["git", "fetch", "--all", "--prune"], cwd=str(repo_path))
    if _git_ok(repo_path, "rev-parse", "--verify", "--quiet", f"origin/{branch}"):
        run(["git", "checkout", "-q", branch], cwd=str(repo_path))
        run(["git", "merge", "--ff-only", "-q", f"origin/{branch}"], cwd=str(repo_path))


def pinned_start_date(workdir):
    """start_date saved by the first run (blank/midpoint start only). Re-computing the midpoint on every
    run would move it as the repo grows and silently shift every week_NN label."""
    p = Path(workdir) / "repo_context.json"
    if p.exists():
        return read_json(p)['start_date']
    return None


def _git_ok(repo_path, *args):
    return subprocess.run(["git", "-C", str(repo_path), *args],
                          capture_output=True, text=True).returncode == 0


def detect_branch(repo_path, requested):
    """Use `requested` if it exists in the clone; otherwise the clone's default branch."""
    if requested and _git_ok(repo_path, "rev-parse", "--verify", "--quiet", requested):
        return requested
    if requested:
        raise ValueError(f'Requested branch does not exist: {requested}')
    r = subprocess.run(["git", "-C", str(repo_path), "symbolic-ref", "--short",
                        "refs/remotes/origin/HEAD"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        found = r.stdout.strip().split("/", 1)[-1]
        print(f">>> Branch '{requested}' not found; using default branch '{found}'.")
        return found
    for cand in ("main", "master", "trunk"):
        if _git_ok(repo_path, "rev-parse", "--verify", "--quiet", cand):
            print(f">>> Branch '{requested}' not found; using '{cand}'.")
            return cand
    raise RuntimeError(f"Could not determine a branch for {repo_path}")


def load_repos(path):
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        try:
            import openpyxl
        except ImportError:
            print("!!! Reading .xlsx requires openpyxl: pip install openpyxl")
            sys.exit(1)
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        header = [str(h).strip() for h in rows[0]]
        if len(header) != len(set(header)) or not {'repository_id', 'git_url'} <= set(header):
            raise ValueError('Invalid repository workbook header')
        out = []
        for r in rows[1:]:
            if all(c is None for c in r):
                continue
            d = {k: ("" if v is None else v) for k, v in zip(header, r)}
            for k in ("branch", "start_date", "weeks"):
                if k in d and hasattr(d[k], "strftime"):
                    d[k] = d[k].strftime("%Y-%m-%d")
                elif k in d:
                    d[k] = str(d[k]).strip()
            d["git_url"] = str(d.get("git_url", "")).strip()
            out.append(d)
        return validate_repos(out)
    return validate_repos(read_csv(path, required=['repository_id', 'git_url'], key='repository_id')[1])


def validate_repos(rows):
    seen = set()
    for row in rows:
        rid = safe_id(row['repository_id'])
        if rid in seen or not row['git_url']:
            raise ValueError('Duplicate/empty repository identity')
        normalize_git_url(row['git_url'])
        seen.add(rid)
    if not rows:
        raise ValueError('Empty repository registry')
    return rows


def run_one_repo(repo_row, args):
    repository_id = safe_id(repo_row['repository_id'])
    git_url = normalize_git_url(repo_row["git_url"].strip())
    branch_req = (repo_row.get("branch") or "").strip() or args.branch
    start_req = (repo_row.get("start_date") or "").strip() or args.start_date or "midpoint"
    weeks_req = int(str(repo_row.get("weeks") or "").strip() or args.weeks)

    repo_path = Path(args.repos_dir) / repository_id
    workdir = Path(args.output_dir) / repository_id
    workdir.mkdir(parents=True, exist_ok=True)

    step(f"{repository_id}: clone/update (local: {repo_path})")
    if args.skip_scan:
        if not (repo_path / '.git').exists():
            raise ValueError('--skip-scan requires an existing local repository')
    else:
        clone_or_update(git_url, repo_path)

    branch = detect_branch(repo_path.resolve(), branch_req)
    if args.weekly_update:
        if not args.skip_scan:
            fast_forward_branch(repo_path.resolve(), branch)
        weeks_req = 10 ** 6          # no cap: follow the repo up to its latest commit
    if start_req.lower() in ("midpoint", "auto", ""):
        pinned = None if args.refresh_start else pinned_start_date(workdir)
        if pinned:
            start_date = pinned
            print(f">>> {repository_id}: reusing pinned start_date {start_date} from repo_context.json")
        else:
            midpoint = midpoint_start_date(repo_path.resolve(), branch)
            start_date = origin_start_date(repo_path.resolve(), branch, config.HISTORY_WEEKS)
            print(f">>> {repository_id}: repo midpoint = {midpoint} (first T0 week); "
                  f"week 1 starts {config.HISTORY_WEEKS} weeks earlier = {start_date}")
    else:
        start_date = start_req
    weeks = min(weeks_req, available_weeks(repo_path.resolve(), start_date, branch))
    if weeks < weeks_req:
        print(f">>> {repository_id}: only {weeks} weeks exist after {start_date} (asked for {weeks_req}).")
    if weeks <= 0:
        raise RuntimeError(f"{repository_id}: no weeks available after {start_date} on '{branch}'")

    step(f"{repository_id}: write repo_context.json")
    context = {
        "repository_id": repository_id,
        "repo_path": str(repo_path.resolve()),
        "project_key": f"{repository_id}-td",
        "branch": branch,
        "start_date": start_date,
        "weeks": weeks,
    }
    context['git_url'] = git_url
    context_path = workdir / 'repo_context.json'
    if context_path.exists():
        old = read_json(context_path)
        if args.refresh_start or any(old.get(k) != context[k] for k in ('repository_id', 'repo_path', 'project_key', 'branch', 'start_date', 'git_url')):
            raise ValueError('Existing workspace identity/calendar differs; use a fresh workspace')
    write_json(context_path, context)
    print(json.dumps(context, indent=2))

    date_args = [start_date, branch, str(weeks)]
    wd = str(workdir)

    step(f"{repository_id}: Sonar scanning (one snapshot per week)")
    if args.skip_scan:
        print("SKIPPED (--skip-scan)")
    else:
        run([PYTHON, here("scan_weekly_snapshots.py"), *date_args], cwd=wd)

    step(f"{repository_id}: validate Sonar snapshots against Git (stale-scan check)")
    run([PYTHON, here('validate_snapshots.py')], cwd=wd)

    if args.level in ("file", "both"):
        run([PYTHON, here('pipeline_total_line.py'), context['repo_path'], TOTAL_LINES_DIR, *date_args], cwd=wd)
        step(f"{repository_id}: git feature sources (file level)")
        run([PYTHON, here("add_weekly_commits_churn.py"), start_date, branch, str(weeks),
             TOTAL_LINES_DIR], cwd=wd)
        run([PYTHON, here("pipeline_g3.py"), TOTAL_LINES_DIR, G3_DIR], cwd=wd)
        run([PYTHON, here("compute_git_window_features.py"), *date_args], cwd=wd)
        run([PYTHON, here("compute_ownership_entropy.py"), *date_args], cwd=wd)
        run([PYTHON, here("compute_lineage.py"), *date_args], cwd=wd)

        step(f"{repository_id}: Sonar trend + lifecycle features (file level)")
        run([PYTHON, here("compute_sonar_trend_features.py")], cwd=wd)
        run([PYTHON, here("compute_finding_lifecycle.py")], cwd=wd)

        step(f"{repository_id}: build td_mart.csv (file level)")
        run([PYTHON, here("build_td_mart.py"), start_date, branch, str(weeks), G3_DIR], cwd=wd)
        if not (workdir / "td_mart.csv").exists():
            raise RuntimeError(f"{repository_id}: build_td_mart.py did not produce td_mart.csv")

    if args.level in ("module", "both"):
        step(f"{repository_id}: build module-level dataset (module_weekly_state.csv, module_td_mart.csv)")
        run([PYTHON, here("build_module_mart.py"), *date_args], cwd=wd)
        if not (workdir / "module_weekly_state.csv").exists():
            raise RuntimeError(f"{repository_id}: build_module_mart.py did not produce module_weekly_state.csv")

    return workdir


def combine_marts(repo_ids, holdout_ids, output_dir, mart_name="td_mart.csv",
                  combined_name="combined_td_mart.csv", holdout_aware=True):
    output_dir = Path(output_dir)
    all_rows, fieldnames, seen = [], None, set()
    for repository_id in repo_ids:
        safe_id(repository_id)
        mart_path = output_dir / repository_id / mart_name
        if mart_name.startswith('module_'):
            verify_generation(mart_path.parent)
        header, rows = read_csv(mart_path, required=['repository_id'])
        if fieldnames is not None and header != [k for k in fieldnames if k != 'held_repository']:
            if header != fieldnames:
                raise ValueError('Incompatible mart schemas')
        if fieldnames is None:
            fieldnames = header + (['held_repository'] if holdout_aware and 'held_repository' not in header else [])
        for row in rows:
            if row['repository_id'] != repository_id:
                raise ValueError('Wrong repository in combined dataset')
            unit = (repository_id, row.get('module_id', row.get('artifact_id')), row.get('week', row.get('origin_id')))
            if not all(unit) or unit in seen:
                raise ValueError('Missing/duplicate scientific unit in combined dataset')
            seen.add(unit)
            if holdout_aware:
                row.setdefault('held_repository', 'NONE')
            if holdout_aware and repository_id in holdout_ids:
                row.update(held_repository=repository_id, split_family='REPOSITORY_HELD_OUT', partition='TEST', fold_id='repo_holdout')
            all_rows.append(row)
    combined_path = output_dir / combined_name
    if fieldnames is None:
        raise ValueError('No repositories to combine')
    write_csv(combined_path, all_rows, fieldnames)
    print(f">>> Wrote {combined_path}: {len(all_rows)} rows across "
          f"{len({r['repository_id'] for r in all_rows})} repo(s).")


def verify_generation(workdir):
    workdir = Path(workdir)
    record = read_json(workdir / 'module_generation.json')
    from build_module_mart import feature_policy
    if record.get('feature_policy_hash') != digest(record.get('feature_policy')) or record['feature_policy_hash'] != digest(feature_policy()):
        raise ValueError('Generation feature definitions/implementation differ')
    if record.get('status') != 'COMPLETE' or record.get('repository_id') != workdir.name:
        raise ValueError('Incomplete/wrong module generation')
    if not record.get('outputs') or not record.get('inputs'):
        raise ValueError('Missing generation integrity record')
    for name, checksum in {**record['inputs'], **record['outputs']}.items():
        path = workdir / name
        if not path.resolve().is_relative_to(workdir.resolve()) or sha256(path) != checksum:
            raise ValueError('Stale or modified generation input/output')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repos_csv")
    parser.add_argument('--branch', default=None, help='Explicit branch; otherwise use repository default')
    parser.add_argument("--start-date", default=None, help="fallback if a repo row omits start_date (default: repo midpoint)")
    parser.add_argument("--weeks", type=int, default=config.DEFAULT_WEEKS, help="fallback if a repo row omits weeks (default: HISTORY + T0 + HORIZON = 138)")
    parser.add_argument("--holdout-repos", default="", help="comma-separated repository_ids to hold out entirely")
    parser.add_argument("--skip-scan", action="store_true")
    parser.add_argument("--level", choices=["module", "file", "both"], default="module",
                         help="module (default): module-level dataset; file: the original file-level mart; both.")
    parser.add_argument("--weekly-update", action="store_true",
                         help="Weekly collection mode: fast-forward each clone to origin, reuse the pinned start_date, "
                              "scan only the new weeks, rebuild outputs. Schedule this once a week.")
    parser.add_argument('--refresh-start', action='store_true',
                         help='Only accepted for a brand-new workspace; existing calendars cannot be reset')
    parser.add_argument("--resume-from", default=None,
                         help="repository_id to start at, skipping every repo before it in the CSV "
                              "(e.g. after a crash partway through a long multi-repo run)")
    parser.add_argument("--repos-dir", default="repo_clones",
                         help="Where repos get git-cloned. Keep this on LOCAL disk -- not a Drive-synced folder.")
    parser.add_argument("--output-dir", default="runs",
                         help="Where every repo's CSV outputs + td_mart.csv + combined_td_mart.csv get "
                              "written. Safe to point at a Drive-synced folder, e.g. 'G:/My Drive/td_runs'.")
    args = parser.parse_args()

    repos = load_repos(args.repos_csv)
    if args.resume_from:
        idx = next((i for i, r in enumerate(repos) if r["repository_id"] == args.resume_from), None)
        if idx is None:
            print(f"!!! --resume-from {args.resume_from} not found in {args.repos_csv}")
            sys.exit(1)
        repos = repos[idx:]

    Path(args.repos_dir).mkdir(parents=True, exist_ok=True)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    holdout_ids = {r.strip() for r in args.holdout_repos.split(",") if r.strip()}

    succeeded, failed = [], []
    write_json(Path(args.output_dir) / 'combined_generation.json', {'status': 'RUNNING'})
    for repo_row in repos:
        repository_id = repo_row["repository_id"].strip()
        try:
            run_one_repo(repo_row, args)
            succeeded.append(repository_id)
        except Exception as e:
            print(f"\n!!! {repository_id} FAILED: {e}")
            print(f"!!! Continuing with the next repo. Re-run later with "
                  f"--resume-from {repository_id} to retry from here.")
            failed.append(repository_id)

    step("Combining all repos' outputs")
    if failed:
        write_json(Path(args.output_dir) / 'combined_generation.json', {'status': 'FAILED', 'failed': failed, 'succeeded': succeeded})
        raise SystemExit(1)
    # Deliberately combine from EVERY repo listed in repos.csv, not just
    # `succeeded` (this run's list). Otherwise a targeted --resume-from
    # run that only touches 1-2 repos would rebuild combined_td_mart.csv
    # from just those repos, silently dropping every other repo's rows
    # that were already sitting on disk from an earlier run.
    all_repo_ids = [r["repository_id"].strip() for r in load_repos(args.repos_csv)]
    try:
        if args.level in ('file', 'both'):
            combine_marts(all_repo_ids, holdout_ids, args.output_dir)
        if args.level in ('module', 'both'):
            combine_marts(all_repo_ids, holdout_ids, args.output_dir, 'module_td_mart.csv', 'combined_module_td_mart.csv')
            combine_marts(all_repo_ids, set(), args.output_dir, 'module_weekly_state.csv', 'combined_module_weekly_state.csv', holdout_aware=False)
        write_json(Path(args.output_dir) / 'combined_generation.json', {'status': 'COMPLETE', 'repositories': all_repo_ids,
            'outputs': {p.name: sha256(p) for p in Path(args.output_dir).glob('combined_*.csv')}})
    except BaseException as exc:
        write_json(Path(args.output_dir) / 'combined_generation.json', {'status': 'FAILED', 'reason': str(exc)})
        raise

    print()
    print(f">>> Succeeded: {succeeded}")
    if failed:
        print(f">>> FAILED (skipped): {failed}")


if __name__ == "__main__":
    main()
