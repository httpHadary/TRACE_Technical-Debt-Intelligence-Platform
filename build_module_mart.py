#!/usr/bin/env python3
"""
Module-level weekly Technical Debt dataset.

    ONE ROW = ONE MODULE AT ONE WEEKLY T0      (replaces: one file at one weekly T0)

A module is defined in modules.py / config.MODULE_STRATEGY:
    build    nearest ancestor directory with pom.xml / build.gradle(.kts)   (multi-module repos)
    package  Java package one level below the repo's base package           (single-module repos)
Decided once per repo and frozen in module_strategy.json.

Inputs (must include the new complete provenance contract; no automatic re-scan):
    data/measures_week_NN.csv   per-file Sonar measures (incl. sqale_index)
    data/issues_week_NN.json    every issue
    data/snapshots.csv, data/analysis_metadata.csv
    data/complete_week_NN.json and retained attempt evidence
    git history of the repo

Outputs (written to the current working directory):
    module_weekly_state.csv       EVERY scanned week x module: size, SQALE index, debt, findings, git
                                  activity, backward-looking trends. No targets. This is the file
                                  to read for the weekly time series ("collect data weekly").
    module_latest_snapshot.csv    just the newest week of the above (current state per module).
    module_td_mart.csv            ML mart: T0 weeks with full 26w history and full 12w horizon, plus
                                  targets TD_3w/1m/3m and SQALE_3w/1m/3m, plus the chronological split.

SQALE index
    sqale_index_t0 = SonarQube's `sqale_index` (remediation effort of the module's code smells, in
    minutes) = sum of its production-Java files' sqale_index. Also: sqale_debt_ratio_t0 (%),
    sqale_rating_t0 (A-E), sqale_index_per_kloc_t0.
    NOTE: sqale_index counts CODE SMELLS only. technical_debt_minutes_t0 (= TD_Principal, the original
    target) also adds bug + vulnerability effort, so TD >= sqale_index.

No future data in any feature: git windows, trends and lifecycle only look back from T0. Future weeks
are read only to build the target columns.

Usage:
    python3 build_module_mart.py <start_date> [branch] [weeks]
"""
import bisect
import csv
import hashlib
import json
import subprocess
import sys
import uuid
import shutil
from collections import defaultdict
from pathlib import Path

import pandas as pd

import config
import modules
from contracts import number, ratio, read_csv, read_json, write_json, digest, sha256
from contracts import write_csv as atomic_csv
from compute_git_window_features import burstiness, clean_numstat_path
from compute_sonar_trend_features import ols_slope, population_stdev
from td_utils import assert_contiguous_weeks, parse_minutes
from weekly_commits import resolve_weekly_commits

DATA_DIR = Path("data")
OUTPUT_DIR = Path('.')
ACTIVE_STATUSES = {"OPEN", "CONFIRMED", "REOPENED"}
HORIZONS = [("3w", 3), ("1m", 4), ("3m", 12)]
WINDOWS = {"3w": 3, "1m": 4, "3m": 12, "6m": 26}
SEVERITIES = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]
TYPES = ["CODE_SMELL", "BUG", "VULNERABILITY"]
TYPE_KEY = {"BUG": "bug", "VULNERABILITY": "vulnerability", "CODE_SMELL": "code_smell"}
SUM_MEASURES = ["lines", "statements", "functions", "classes", "complexity",
                "cognitive_complexity", "duplicated_lines", "comment_lines", "sqale_index"]

ID_COLS = ["repository_id", "module_id", "module_strategy", "week", "week_end_utc", "t0",
           "commit_hash_t0", "sonar_analysis_key_t0", "sonarqube_version", "java_analyzer_version",
           "quality_profile_id", "quality_profile_hash", "analysis_mode",
           "compatible_rule_domain_version"]
SIZE_COLS = ["file_count_t0", "ncloc_t0", "lines_t0", "statements_t0", "functions_t0", "classes_t0",
             "complexity_t0", "cognitive_complexity_t0", "duplicated_lines_t0",
             "duplicated_lines_density_t0", "comment_lines_t0", "comment_lines_density_t0"]
SQALE_COLS = ["sqale_index_t0", "sqale_debt_ratio_t0", "sqale_rating_t0", "sqale_index_per_kloc_t0"]
DEBT_COLS = (["finding_count_t0", "finding_density_t0", "bug_remediation_effort_t0",
              "vulnerability_remediation_effort_t0", "code_smell_remediation_effort_t0",
              "technical_debt_minutes_t0", "technical_debt_density_t0"]
             + [f"{s.lower()}_finding_count_t0" for s in SEVERITIES]
             + [f"{t.lower()}_count_t0" for t in TYPES]
             + ["files_with_findings_t0", "max_file_td_t0"])
GIT_COLS = ["commits_t0", "files_changed_t0", "lines_added_t0", "lines_deleted_t0", "churn_t0",
            "authors_t0", "module_age_days_t0", "days_since_last_change_t0",
            "churn_acceleration_t0", "commit_burstiness_t0", "churn_burstiness_t0",
            "git_history_missing_t0"]
TREND_PREFIXES = ["finding_density_slope", "finding_density_volatility",
                  "technical_debt_density_slope", "technical_debt_density_volatility",
                  "sqale_density_slope", "sqale_density_volatility",
                  "sqale_index_slope", "ncloc_slope",
                  "complexity_slope", "cognitive_complexity_slope", "duplication_slope",
                  "td_history_points", "td_history_missing"]
TREND_COLS = [f"{p}_{s}" for s in WINDOWS for p in TREND_PREFIXES]
LIFECYCLE_COLS = [f"{k}_{s}" for s in WINDOWS for k in ("finding_arrivals", "finding_closures")]
STATE_COLS = ID_COLS + SIZE_COLS + SQALE_COLS + DEBT_COLS + GIT_COLS + TREND_COLS + LIFECYCLE_COLS
OBS_COLS = [f'{metric}_{suffix}' for metric in ['ncloc', *SUM_MEASURES]
            for suffix in ('status', 'observed_files', 'missing_files', 'partial_sum')]
STATE_COLS += OBS_COLS + ['issues_status', 'effort_status', 'missing_effort_findings',
                        'observed_effort_minutes_partial', 'membership_hash', 'commit_timestamp', 'mapping_id']


# ------------------------------------------------------------------ small helpers
def fnum(v):
    return number(v)


def component_path(component):
    component = str(component or "").strip()
    if config.PROJECT_KEY:
        prefix = config.PROJECT_KEY + ':'
        if not component.startswith(prefix):
            raise ValueError('Issue component belongs to another project')
        return component[len(prefix):]
    return component.rsplit(':', 1)[-1]


def sqale_rating(ratio):
    if ratio is None:
        return None
    for bound, letter in config.SQALE_RATING_BOUNDS:
        if ratio <= bound:
            return letter
    return "E"


def load_csv_by(path, key):
    path = Path(path)
    _, rows = read_csv(path, required=[key], key=key)
    return {r[key]: r for r in rows}


def analyzers_compatible(meta_t0, snap_t0, meta_h, snap_h):
    pairs = [(meta_t0.get("sonarqube_version"), meta_h.get("sonarqube_version")),
             (meta_t0.get("java_analyzer_version"), meta_h.get("java_analyzer_version")),
             (meta_t0.get("quality_profile_hash"), meta_h.get("quality_profile_hash")),
             (meta_t0.get("compatible_rule_domain_version"), meta_h.get("compatible_rule_domain_version")),
             (meta_t0.get("scanner_image"), meta_h.get("scanner_image")),
             (snap_t0.get("analysis_mode"), snap_h.get("analysis_mode"))]
    if any(meta.get('analysis_mode') != snap.get('analysis_mode') for meta, snap in ((meta_t0, snap_t0), (meta_h, snap_h))):
        return False
    return all(a and b and a == b for a, b in pairs)


# ------------------------------------------------------------------ Sonar aggregation
def aggregate_week(label, mapper, expected_paths=None):
    """-> ({module: state}, {module: set(active issue keys)}) for one weekly snapshot."""
    states, keys = {}, defaultdict(set)

    def state(m):
        if m not in states:
            states[m] = {"file_count": 0, "ncloc": 0.0, "findings": 0, "td": 0.0,
                         "bug": 0.0, "vulnerability": 0.0, "code_smell": 0.0,
                         "sev": defaultdict(int), "typ": defaultdict(int),
                         "file_td": defaultdict(float), 'paths': set(), 'issues_observed': True,
                         'missing': defaultdict(int), 'partial': defaultdict(float),
                         'missing_effort': 0, 'partial_effort': 0.0,
                         **{k: 0.0 for k in SUM_MEASURES}}
        return states[m]

    mpath = DATA_DIR / f"measures_{label}.csv"
    _, rows = read_csv(mpath, required=['file_path', 'ncloc', *SUM_MEASURES], key='file_path')
    measured = {r['file_path'] for r in rows if modules.is_production_file(r['file_path'])}
    if expected_paths is not None and measured != set(expected_paths):
        raise ValueError(f'{label}: measured production population differs from Git/source inventory')
    for r in rows:
            fp = r.get("file_path", "")
            if not modules.is_production_file(fp):
                continue
            s = state(mapper.module_of(fp))
            s["file_count"] += 1
            s['paths'].add(fp)
            for k in ['ncloc', *SUM_MEASURES]:
                value = fnum(r[k])
                if value is None:
                    s['missing'][k] += 1
                    s[k] = None
                else:
                    s['partial'][k] += value
                    if s[k] is not None:
                        s[k] += value

    ipath = DATA_DIR / f"issues_{label}.json"
    if ipath.exists():
        issues = read_json(ipath)
        if not isinstance(issues, list):
            raise ValueError('Issue export must be a list')
        seen = set()
        for i in issues:
            if not i.get('key') or i['key'] in seen:
                raise ValueError('Missing/duplicate issue key')
            seen.add(i['key'])
            if i.get('status') not in ACTIVE_STATUSES | {'RESOLVED', 'CLOSED'}:
                raise ValueError('Unsupported issue status')
            if i.get("status") not in ACTIVE_STATUSES:
                continue
            fp = component_path(i.get("component"))
            if not modules.is_production_file(fp):
                continue
            m = mapper.module_of(fp)
            if fp not in measured:
                raise ValueError(f'{label}: issue on unmeasured production file {fp}')
            if i.get('type') not in TYPES or i.get('severity') not in SEVERITIES:
                raise ValueError('Unsupported issue type/severity')
            s = states[m]
            minutes = parse_minutes(i.get("effort_minutes"))
            if minutes is None:
                s['missing_effort'] += 1
            else:
                s['partial_effort'] += minutes
            s["findings"] += 1
            t = TYPE_KEY.get(i.get("type"))
            for field in ('td', t):
                s[field] = None if minutes is None or s[field] is None else s[field] + minutes
            s['file_td'][fp] = None if minutes is None or s['file_td'][fp] is None else s['file_td'][fp] + minutes
            s["sev"][i.get("severity")] += 1
            s["typ"][i.get("type")] += 1
            keys[m].add(i["key"])

    else:
        for s in states.values():
            s['issues_observed'] = False
            for field in ('td', 'bug', 'vulnerability', 'code_smell', 'findings'):
                s[field] = None
    for s in states.values():
        sq, smell = s['sqale_index'], s['code_smell']
        if sq is not None and smell is not None and abs(sq - smell) > 0.02 * max(sq, smell):
            raise ValueError(f'{label}: SQALE and code-smell effort disagree')
    return states, keys


def state_to_columns(s):
    """Flatten an aggregated module state into the *_t0 columns (no git, no trends)."""
    ncloc, lines = s["ncloc"], s["lines"]
    kloc = ncloc / 1000 if ncloc is not None else None
    dup_density = ratio(s['duplicated_lines'], lines, 100)
    cl = s["comment_lines"]
    cdens = ratio(cl, ncloc + cl if ncloc is not None and cl is not None else None, 100)
    sq = s["sqale_index"]
    debt_ratio = ratio(sq, ncloc * config.DEV_COST_PER_LINE_MIN if ncloc is not None else None, 100)
    out = {
        "file_count_t0": s["file_count"], "ncloc_t0": ncloc, "lines_t0": lines,
        **{f'{k}_t0': s[k] for k in ('statements', 'functions', 'classes', 'complexity',
                                   'cognitive_complexity', 'duplicated_lines', 'comment_lines')},
        "duplicated_lines_density_t0": dup_density, "comment_lines_density_t0": cdens,
        "sqale_index_t0": sq, "sqale_debt_ratio_t0": debt_ratio,
        "sqale_rating_t0": sqale_rating(debt_ratio), "sqale_index_per_kloc_t0": ratio(sq, kloc),
        "finding_count_t0": s["findings"], "finding_density_t0": ratio(s["findings"], kloc),
        "bug_remediation_effort_t0": s["bug"],
        "vulnerability_remediation_effort_t0": s["vulnerability"],
        "code_smell_remediation_effort_t0": s["code_smell"],
        "technical_debt_minutes_t0": s["td"],
        "technical_debt_density_t0": ratio(s["td"], kloc),
        "files_with_findings_t0": len(s["file_td"]) if s['issues_observed'] else None,
        "max_file_td_t0": (max(s['file_td'].values(), default=0) if s['issues_observed']
                           and all(v is not None for v in s['file_td'].values()) else None),
        'issues_status': 'OBSERVED' if s['issues_observed'] else 'UNKNOWN_OBSERVATION',
        'effort_status': 'OBSERVED' if s['issues_observed'] and not s['missing_effort'] else 'UNKNOWN_OBSERVATION',
        'missing_effort_findings': s['missing_effort'] if s['issues_observed'] else None,
        'observed_effort_minutes_partial': s['partial_effort'] if s['issues_observed'] else None,
        'membership_hash': digest(sorted(s['paths'])),
    }
    for sev in SEVERITIES:
        out[f"{sev.lower()}_finding_count_t0"] = s["sev"].get(sev, 0) if s['issues_observed'] else None
    for t in TYPES:
        out[f"{t.lower()}_count_t0"] = s["typ"].get(t, 0) if s['issues_observed'] else None
    for k in ['ncloc', *SUM_MEASURES]:
        missing = s['missing'][k]
        out.update({f'{k}_status': 'UNKNOWN_OBSERVATION' if missing else 'OBSERVED',
                    f'{k}_observed_files': s['file_count'] - missing,
                    f'{k}_missing_files': missing, f'{k}_partial_sum': s['partial'][k]})
    return out


def trend_series(s):
    """Per-week values used by the rolling windows (None when ncloc == 0 / not available)."""
    kloc = s["ncloc"] / 1000 if s['ncloc'] is not None else None
    return {
        "DD": ratio(s['findings'], kloc), 'TDD': ratio(s['td'], kloc, 1/60),
        'SQD': ratio(s['sqale_index'], kloc, 1/60),
        'CC': ratio(s['complexity'], kloc), 'CogC': ratio(s['cognitive_complexity'], kloc),
        'DP': ratio(s['duplicated_lines'], s['lines'], 100),
        "SQ": s["sqale_index"], "NCLOC": s["ncloc"],
    }


# ------------------------------------------------------------------ git aggregation
def collect_history(repo_path, end_commit):
    """[(committer_ts_utc, commit, author, path, added, deleted)] for the whole history (no merges)."""
    out = subprocess.run(
        ["git", "-C", str(repo_path), "log", end_commit, "--no-merges",
         "--format=COMMIT|%H|%cI|%ae", "--numstat", '-z', '--no-renames'],
        capture_output=True, text=True, encoding="utf-8", errors="strict")
    if out.returncode != 0:
        raise RuntimeError(f"git log failed:\n{out.stderr}")
    events, commit, ts, author = [], None, None, None
    for line in out.stdout.split('\0'):
        line = line.lstrip('\n')
        if line.startswith("COMMIT|"):
            _, commit, iso, author = line.split("|", 3)
            ts = pd.Timestamp(iso)
            ts = ts.tz_convert(None) if ts.tzinfo is not None else ts
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a, d, path = parts
        events.append((ts, commit, author.lower(), path,
                       int(a) if a.isdigit() else None, int(d) if d.isdigit() else None))
    return events


def build_git_buckets(events, weeks, mapper_by_week, ancestors=None):
    """-> (per_week[module][week] -> bucket, times[module] -> sorted [ts], history_floor)."""
    wnums = sorted(weeks)
    ends = [weeks[w]["end"] for w in wnums]
    first_start, last_end = weeks[wnums[0]]["start"], ends[-1]
    per_week = defaultdict(dict)
    times = defaultdict(list)
    floor = None
    for ts, commit, author, path, a, d in events:
        if not modules.is_production_file(path) or ts > last_end:
            continue
        if a is None or d is None:
            raise ValueError('Production Java file has unmeasurable binary churn')
        floor = ts if floor is None or ts < floor else floor
        if ts <= first_start:
            w = None
            mapper = mapper_by_week[wnums[0]]
            if ancestors is not None and commit not in ancestors[wnums[0]]:
                continue
        else:
            i = bisect.bisect_left(ends, ts)
            w = wnums[i]
            mapper = mapper_by_week[w]
            if ancestors is not None and commit not in ancestors[w]:
                continue
        m = mapper.module_of(path, source_commit=commit)
        times[m].append(ts)
        if w is None:
            continue
        b = per_week[m].setdefault(w, {"commits": set(), "files": set(), "added": 0,
                                       "deleted": 0, "authors": set()})
        b["commits"].add(commit)
        b["files"].add(path)
        b["added"] += a
        b["deleted"] += d
        b["authors"].add(author)
    for m in times:
        times[m].sort()
    return per_week, times, floor


# ------------------------------------------------------------------ split
def assign_partitions(rows):
    # A fixed calendar, independent of surviving rows and future weekly extensions.
    valid_weeks = list(range(config.HISTORY_WEEKS + 1, config.HISTORY_WEEKS + config.T0_WEEKS + 1))
    n = len(valid_weeks)
    train_count = max(1, int(n * 0.60))
    validation_count = max(1, int(n * 0.20))
    train_weeks = valid_weeks[:train_count]
    validation_weeks = valid_weeks[train_count:train_count + validation_count]
    test_weeks = valid_weeks[train_count + validation_count:]
    purge = max(off for _, off in HORIZONS)
    train_end = max(train_weeks)
    val_start = min(validation_weeks) if validation_weeks else None
    val_end = max(validation_weeks) if validation_weeks else None
    test_start = min(test_weeks) if test_weeks else None
    for row in rows:
        w = row.pop("_t0_week")
        if w <= train_end:
            part = "TRAIN"
        elif val_start is not None and w < val_start + purge:
            part = "PURGED"
        elif val_start is not None and val_end is not None and val_start + purge <= w <= val_end:
            part = "VALIDATION"
        elif test_start is not None and w < test_start + purge:
            part = "PURGED"
        elif test_start is not None:
            part = "TEST"
        else:
            part = "UNASSIGNED"
        if w > valid_weeks[-1]:
            part = 'UNASSIGNED'
        row["partition"] = part
        row["fold_id"] = f"chrono_{part.lower()}"
    return n, purge


def write_csv(path, rows, fieldnames):
    atomic_csv(OUTPUT_DIR / path, rows, fieldnames)


# ------------------------------------------------------------------ main
def build():
    if len(sys.argv) not in (2, 3, 4):
        print(__doc__)
        sys.exit(1)
    start_date = sys.argv[1]
    branch = sys.argv[2] if len(sys.argv) >= 3 else config.BRANCH
    max_weeks = int(sys.argv[3]) if len(sys.argv) == 4 else config.DEFAULT_WEEKS
    if max_weeks <= 0:
        raise ValueError('A positive week count is required')
    if modules._git(config.REPO_PATH, ['rev-parse', '--is-shallow-repository']).strip() != 'false':
        raise ValueError('Complete Git history is required')

    weeks = resolve_weekly_commits(config.REPO_PATH, start_date, branch, max_weeks=max_weeks)
    if any(not b['commit'] for b in weeks.values()):
        raise ValueError('A calendar week has no historical commit; weeks cannot be silently removed')
    snapshots = load_csv_by(DATA_DIR / "snapshots.csv", "label")
    meta = load_csv_by(DATA_DIR / 'analysis_metadata.csv', 'label')
    wnums = sorted(weeks)
    if not wnums:
        raise ValueError('No complete calendar weeks')
    assert_contiguous_weeks([f"week_{w:02d}" for w in wnums])
    weeks = {w: weeks[w] for w in wnums}
    from sonar_evidence import verify_snapshot
    inventories = {}
    for w in wnums:
        label = f'week_{w:02d}'
        if label not in snapshots or label not in meta or snapshots[label]['commit_hash'] != weeks[w]['commit']:
            raise ValueError(f'{label}: missing/mismatched snapshot commit or metadata')
        inventories[w] = verify_snapshot(label, config.REPO_PATH, weeks[w]['commit'])['eligible_paths']
    print(f">>> {len(wnums)} scanned weeks ({wnums[0]}..{wnums[-1]})")

    # ---- module definition (frozen) + one mapper per week -------------------------------------
    decision = modules.load_or_decide_strategy(config.REPO_PATH, weeks[wnums[0]]["commit"])
    strategy = decision["strategy"]
    mapper_by_week = {w: modules.mapper_for_commit(config.REPO_PATH, weeks[w]["commit"], decision)
                      for w in wnums}

    # ---- Sonar state per week x module ----------------------------------------------------------
    states, keys = {}, {}
    for w in wnums:
        states[w], keys[w] = aggregate_week(f"week_{w:02d}", mapper_by_week[w], inventories[w])
    n_mod = len({m for w in wnums for m in states[w]})
    print(f">>> {n_mod} distinct modules across all weeks (strategy: {strategy})")

    # consistency check: sqale_index (Sonar) should equal the code-smell effort we sum from issues
    diffs = []  # aggregate_week enforces reconciliation whenever both totals are observed.
    total_mw = sum(len(states[w]) for w in wnums)
    print(f">>> sqale_index vs issue-derived code-smell effort differ by >2% in {len(diffs)}/{total_mw} "
          f"module-weeks" + (f" (e.g. week {diffs[0][0]}, {diffs[0][1]})" if diffs else " -- consistent"))

    # ---- git history, bucketed by module ---------------------------------------------------------
    print(f">>> Walking git history once (up to {weeks[wnums[-1]]['commit'][:8]})")
    events = collect_history(config.REPO_PATH, weeks[wnums[-1]]["commit"])
    ancestor_cache = {}
    ancestors = {}
    for w in wnums:
        commit = weeks[w]['commit']
        if commit not in ancestor_cache:
            ancestor_cache[commit] = set(modules._git(config.REPO_PATH, ['rev-list', commit]).split())
        ancestors[w] = ancestor_cache[commit]
    first_start = weeks[wnums[0]]["start"]
    zero = {"commits": set(), "files": set(), "added": 0, "deleted": 0, "authors": set()}

    # ---- per week x module feature rows -------------------------------------------------------------
    series = {w: {m: trend_series(s) for m, s in states[w].items()} for w in wnums}
    rows_by_wm = {}
    for i, w in enumerate(wnums):
        # Reconstruct only history reachable at this T0. Backdated commits merged later
        # may enter later T0 features, but can never leak into earlier observations.
        visible = [event for event in events if event[1] in ancestors[w]]
        per_week, times, floor = build_git_buckets(visible, {k: weeks[k] for k in wnums if k <= w}, mapper_by_week)
        repo_history_missing = floor is None or floor > first_start
        snap = snapshots[f"week_{w:02d}"]
        m_t0 = meta.get(f"week_{w:02d}", {})
        t0 = weeks[w]["end"]
        commit_ts = modules._git(config.REPO_PATH, ['show', '-s', '--format=%cI', snap['commit_hash']]).strip()
        if pd.Timestamp(commit_ts).tz_convert(None) > t0:
            raise ValueError('Snapshot commit is after observation cutoff')
        for m, s in states[w].items():
            row = {
                "repository_id": config.REPOSITORY_ID, "module_id": m, "module_strategy": strategy,
                "week": f"week_{w:02d}", "week_end_utc": t0.isoformat() + 'Z', 't0': t0.isoformat() + 'Z',
                'commit_timestamp': commit_ts, 'mapping_id': decision['mapping_id'],
                "commit_hash_t0": snap["commit_hash"], "sonar_analysis_key_t0": snap["analysis_key"],
                "sonarqube_version": m_t0.get("sonarqube_version", ""),
                "java_analyzer_version": m_t0.get("java_analyzer_version", ""),
                "quality_profile_id": m_t0.get("quality_profile_id", ""),
                "quality_profile_hash": m_t0.get("quality_profile_hash", ""),
                "analysis_mode": snap.get("analysis_mode", ""),
                "compatible_rule_domain_version": m_t0.get(
                    "compatible_rule_domain_version", config.COMPATIBLE_RULE_DOMAIN_VERSION),
            }
            row.update(state_to_columns(s))

            # git (committer dates <= T0, merges excluded)
            ev_times = times.get(m, [])
            n_t0 = bisect.bisect_right(ev_times, t0)
            pw = per_week.get(m, {})
            cur = pw.get(w, zero)
            commit_series = [len(pw.get(x, zero)["commits"]) for x in range(wnums[0], w + 1)]
            churn_series = [pw.get(x, zero)["added"] + pw.get(x, zero)["deleted"]
                            for x in range(wnums[0], w + 1)]
            prev_churn = (pw.get(w - 1, zero)["added"] + pw.get(w - 1, zero)["deleted"]) if w > wnums[0] else None
            churn = cur["added"] + cur["deleted"]
            row.update({
                "commits_t0": len(cur["commits"]), "files_changed_t0": len(cur["files"]),
                "lines_added_t0": cur["added"], "lines_deleted_t0": cur["deleted"], "churn_t0": churn,
                "authors_t0": len(cur["authors"]),
                "module_age_days_t0": (t0 - ev_times[0]).days if n_t0 else "",
                "days_since_last_change_t0": (t0 - ev_times[n_t0 - 1]).days if n_t0 else "",
                "churn_acceleration_t0": (churn - prev_churn) if prev_churn is not None else "",
                "commit_burstiness_t0": round(burstiness(commit_series), 6),
                "churn_burstiness_t0": round(burstiness(churn_series), 6),
                "git_history_missing_t0": bool(repo_history_missing or n_t0 == 0),
            })

            # backward-looking Sonar trends
            for suf, win in WINDOWS.items():
                def vals(metric):
                    if i - win + 1 < 0:
                        return None
                    if not all(analyzers_compatible(meta[f'week_{wnums[j]:02d}'], snapshots[f'week_{wnums[j]:02d}'], m_t0, snap)
                               for j in range(i - win + 1, i + 1)):
                        return None
                    return [series[wnums[j]].get(m, {}).get(metric) for j in range(i - win + 1, i + 1)]
                for prefix, metric in (("finding_density", "DD"), ("technical_debt_density", "TDD"),
                                       ("sqale_density", "SQD")):
                    v = vals(metric)
                    row[f"{prefix}_slope_{suf}"] = ols_slope(v)
                    row[f"{prefix}_volatility_{suf}"] = population_stdev(v)
                row[f"sqale_index_slope_{suf}"] = ols_slope(vals("SQ"))
                row[f"ncloc_slope_{suf}"] = ols_slope(vals("NCLOC"))
                row[f"complexity_slope_{suf}"] = ols_slope(vals("CC"))
                row[f"cognitive_complexity_slope_{suf}"] = ols_slope(vals("CogC"))
                row[f"duplication_slope_{suf}"] = ols_slope(vals("DP"))
                dd = vals("DD")
                n_pts = 0 if dd is None else sum(1 for x in dd if x is not None)
                row[f"td_history_points_{suf}"] = n_pts
                row[f"td_history_missing_{suf}"] = dd is None or n_pts < win

                # finding lifecycle: active issue keys now vs `win` weeks ago (module present both times)
                if (i - win >= 0 and all(m in states[wnums[j]] and states[wnums[j]][m]['issues_observed']
                    and analyzers_compatible(meta[f'week_{wnums[j]:02d}'], snapshots[f'week_{wnums[j]:02d}'], m_t0, snap)
                    for j in range(i - win, i + 1))):
                    now, past = keys[w].get(m, set()), keys[wnums[i - win]].get(m, set())
                    row[f"finding_arrivals_{suf}"] = len(now - past)
                    row[f"finding_closures_{suf}"] = len(past - now)
                else:
                    row[f"finding_arrivals_{suf}"] = ""
                    row[f"finding_closures_{suf}"] = ""
            rows_by_wm[(w, m)] = row

    # ---- output 1: weekly state (every week, no targets) --------------------------------------------
    state_rows = [rows_by_wm[(w, m)] for w in wnums for m in sorted(states[w])]
    write_csv("module_weekly_state.csv", state_rows, STATE_COLS)
    latest = [r for r in state_rows if r["week"] == f"week_{wnums[-1]:02d}"]
    write_csv("module_latest_snapshot.csv", latest, STATE_COLS)
    print(f">>> module_weekly_state.csv: {len(state_rows)} rows ({len(STATE_COLS)} columns), "
          f"{len(wnums)} weeks x up to {n_mod} modules")
    print(f">>> module_latest_snapshot.csv: {len(latest)} modules at week_{wnums[-1]:02d}")

    # ---- output 2: ML mart -----------------------------------------------------------------------------
    first_t0 = config.HISTORY_WEEKS + 1
    last_t0 = wnums[-1] - config.HORIZON_WEEKS
    t0_weeks = [w for w in wnums if first_t0 <= w <= last_t0]
    if not t0_weeks:
        print(f"!!! No usable T0 weeks for the mart yet: need weeks {first_t0}..{last_t0}, scanned "
              f"{wnums[0]}..{wnums[-1]}. (module_weekly_state.csv is still complete.)")
        write_csv('module_td_mart.csv', [], MART_COLS)
        return {'rows': 0, 'status': 'COMPLETE', 'training_ready': False}
    print(f">>> Mart T0 weeks: {t0_weeks[0]}..{t0_weeks[-1]} ({len(t0_weeks)} weeks)")

    mart = []
    for w in t0_weeks:
        label = f"week_{w:02d}"
        snap_t0, meta_t0 = snapshots[label], meta.get(label, {})
        for m in sorted(states[w]):
            base = rows_by_wm[(w, m)]
            # lifecycle compares T0 with the snapshot 26 weeks back (one week earlier than the trend window
            # starts), so a module must exist then too -- otherwise finding_arrivals_6m would be blank.
            # Missing numeric predictors do not erase an otherwise observed origin/target.
            # Lifecycle availability independently proves the complete historical window.
            history_complete = (not base['git_history_missing_t0']) and base['finding_arrivals_6m'] != ''
            eligible = history_complete
            reasons_t0 = [] if history_complete else ["history_incomplete"]
            row = {"origin_id": hashlib.sha1(
                f"{config.REPOSITORY_ID}:{decision['mapping_id']}:{m}:{base['t0']}:{snap_t0['commit_hash']}".encode()).hexdigest()[:20]}
            row.update(base)
            row.update({"production_source_file": True, "history_complete": history_complete,
                        "eligible_t0": eligible, "exclusion_reason_t0": ";".join(reasons_t0)})
            s_now = states[w][m]
            for name, offset in HORIZONS:
                cols = {f"TD_{name}": "", f"TD_{name}_status": "", f"TD_{name}_exclusion_reason": "",
                        f"bug_remediation_effort_{name}": "", f"vulnerability_remediation_effort_{name}": "",
                        f"code_smell_remediation_effort_{name}": "", f"SQALE_{name}": "",
                        f"TD_{name}_delta": None, f"SQALE_{name}_delta": None,
                        f'SQALE_{name}_status': 'UNKNOWN_OBSERVATION',
                        f'membership_added_{name}': None, f'membership_removed_{name}': None}
                hw = w + offset
                h_label = f"week_{hw:02d}"
                if hw not in states or h_label not in snapshots:
                    cols[f"TD_{name}_status"] = "UNKNOWN_OBSERVATION"
                    cols[f"TD_{name}_exclusion_reason"] = "horizon_not_scanned_yet"
                else:
                    reasons = []
                    if not eligible:
                        reasons.append("t0_not_eligible")
                    fut = states[hw].get(m)
                    if fut is None:
                        reasons.append("module_missing_at_horizon")
                    elif not fut['paths'] & s_now['paths']:
                        reasons.append('module_lineage_unresolved')
                    if fut is not None:
                        cols[f'membership_added_{name}'] = len(fut['paths'] - s_now['paths'])
                        cols[f'membership_removed_{name}'] = len(s_now['paths'] - fut['paths'])
                    if not analyzers_compatible(meta_t0, snap_t0, meta.get(h_label, {}), snapshots[h_label]):
                        reasons.append("analyzer_incompatible_t0_horizon")
                    if not reasons and fut['sqale_index'] is not None:
                        cols[f'SQALE_{name}'] = fut['sqale_index']
                        cols[f'SQALE_{name}_status'] = 'OBSERVED'
                        cols[f'SQALE_{name}_delta'] = (fut['sqale_index'] - s_now['sqale_index']
                            if s_now['sqale_index'] is not None else None)
                    if fut is not None and fut['td'] is None:
                        reasons.append('future_debt_unobserved')
                    if reasons:
                        cols[f"TD_{name}_status"] = ("UNKNOWN_OBSERVATION" if any(r in reasons for r in ('module_missing_at_horizon', 'module_lineage_unresolved', 'future_debt_unobserved'))
                                                     else "EXCLUDED")
                        cols[f"TD_{name}_exclusion_reason"] = ";".join(reasons)
                    else:
                        cols[f"bug_remediation_effort_{name}"] = fut["bug"]
                        cols[f"vulnerability_remediation_effort_{name}"] = fut["vulnerability"]
                        cols[f"code_smell_remediation_effort_{name}"] = fut["code_smell"]
                        cols[f"TD_{name}"] = fut["td"]
                        cols[f"SQALE_{name}"] = fut["sqale_index"]
                        cols[f"TD_{name}_delta"] = fut['td'] - s_now['td'] if s_now['td'] is not None else None
                        cols[f"SQALE_{name}_delta"] = (fut['sqale_index'] - s_now['sqale_index']
                            if fut['sqale_index'] is not None and s_now['sqale_index'] is not None else None)
                        cols[f'SQALE_{name}_status'] = 'OBSERVED' if fut['sqale_index'] is not None else 'UNKNOWN_OBSERVATION'
                        cols[f"TD_{name}_status"] = "OBSERVED"
                row.update(cols)

            if config.DROP_INELIGIBLE_ROWS and not eligible:
                continue
            if config.REQUIRE_ALL_TARGETS_OBSERVED and any(
                    row[f"TD_{n}_status"] != "OBSERVED" for n, _ in HORIZONS):
                continue
            for c in ["exclusion_reason_t0"] + [f"TD_{n}_exclusion_reason" for n, _ in HORIZONS]:
                if row[c] == "":
                    row[c] = "NONE"
            row["max_feature_ts"] = base["t0"]
            row["split_family"] = "CHRONOLOGICAL"
            row["_t0_week"] = w
            mart.append(row)

    if not mart:
        print("No mart rows produced (no module has 26 weeks of history and an observed 12-week future yet).")
        write_csv('module_td_mart.csv', [], MART_COLS)
        return {'status': 'COMPLETE', 'rows': 0, 'training_ready': False}
    n_weeks, purge = assign_partitions(mart)
    fieldnames = MART_COLS
    write_csv("module_td_mart.csv", mart, fieldnames)
    print(f"\n>>> Wrote module_td_mart.csv: {len(mart)} rows ({len(fieldnames)} columns), "
          f"{len({r['module_id'] for r in mart})} modules")
    for part in ("TRAIN", "VALIDATION", "TEST", "PURGED", "UNASSIGNED"):
        print(f">>>   {part}: {sum(1 for r in mart if r['partition'] == part)}")
    for part in ("VALIDATION", "TEST"):
        if not any(r["partition"] == part for r in mart):
            print(f"!!! WARNING: no {part} rows ({n_weeks} T0 weeks, {purge}-week purge; ~100+ weeks recommended).")
    if len(mart) < 1000:
        print(f"!!! NOTE: only {len(mart)} module-level rows ({n_mod} modules x ~{n_weeks} T0 weeks) -- far fewer than "
              f"a file-level mart. Pool several repositories (combined_module_td_mart.csv) before fitting big models.")
    blanks = {c: sum(1 for r in mart if r.get(c) in (None, "")) for c in fieldnames}
    blanks = {c: n for c, n in blanks.items() if n}
    if blanks:
        print(f"!!! {len(blanks)} column(s) still contain blanks:")
        for c, n in sorted(blanks.items(), key=lambda kv: -kv[1])[:15]:
            print(f"!!!   {c}: {n}/{len(mart)} blank")
    else:
        print(f">>> No blank cells in any of the {len(fieldnames)} columns.")
    print(">>> Targets (TD_*, SQALE_*, *_status, *_delta, *_remediation_effort_<3w|1m|3m>) are label-only: "
          "never put them in X.")
    return {'status': 'COMPLETE', 'rows': len(mart), 'training_ready': all(any(r['partition'] == p for r in mart)
            for p in ('TRAIN', 'VALIDATION', 'TEST')), 'mapping_id': decision['mapping_id']}


MART_COLS = ['origin_id', *STATE_COLS, 'production_source_file', 'history_complete', 'eligible_t0', 'exclusion_reason_t0']
for _h, _ in HORIZONS:
    MART_COLS += [f'TD_{_h}', f'TD_{_h}_status', f'TD_{_h}_exclusion_reason',
                  *[f'{k}_remediation_effort_{_h}' for k in ('bug', 'vulnerability', 'code_smell')],
                  f'SQALE_{_h}', f'TD_{_h}_delta', f'SQALE_{_h}_delta', f'SQALE_{_h}_status',
                  f'membership_added_{_h}', f'membership_removed_{_h}']
MART_COLS += ['max_feature_ts', 'split_family', 'partition', 'fold_id']


def feature_policy():
    """Bind configurable metric/split definitions; do not mix differently defined marts."""
    return {'history_weeks': config.HISTORY_WEEKS, 'horizon_weeks': config.HORIZON_WEEKS,
            't0_weeks': config.T0_WEEKS, 'target_horizons': HORIZONS, 'history_windows': WINDOWS,
            'development_cost_minutes_per_line': config.DEV_COST_PER_LINE_MIN,
            'rating_bounds': config.SQALE_RATING_BOUNDS, 'active_statuses': sorted(ACTIVE_STATUSES),
            'drop_ineligible': config.DROP_INELIGIBLE_ROWS,
            'require_all_targets_observed': config.REQUIRE_ALL_TARGETS_OBSERVED,
            'extra_production_roots': config.EXTRA_PRODUCTION_ROOTS,
            'module_strategy': config.MODULE_STRATEGY, 'package_extra_depth': config.MODULE_PACKAGE_EXTRA_DEPTH,
            'implementation': {name:sha256(Path(__file__).parent/name) for name in
                ('build_module_mart.py','modules.py','contracts.py','weekly_commits.py','sonar_evidence.py','td_utils.py')}}


def publish_generation():
    global OUTPUT_DIR
    generation = uuid.uuid4().hex
    OUTPUT_DIR = Path('.generations') / generation
    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    record = {'generation': generation, 'status': 'RUNNING', 'repository_id': config.REPOSITORY_ID}
    record.update(feature_policy=feature_policy(), feature_policy_hash=digest(feature_policy()))
    write_json('module_generation.json', record)
    try:
        record.update(build())
        outputs = {p.name: sha256(p) for p in OUTPUT_DIR.glob('*.csv')}
        inputs = {str(p): sha256(p) for p in DATA_DIR.rglob('*') if p.is_file() and p.name != 'run.lock'}
        for name in ('repo_context.json', 'module_strategy.json'):
            if Path(name).is_file():
                inputs[name] = sha256(name)
        record.update(outputs=outputs, inputs=inputs)
        for name in outputs:
            from contracts import atomic_bytes
            atomic_bytes(name, (OUTPUT_DIR / name).read_bytes())
        write_json(OUTPUT_DIR / 'module_generation.json', record)
        write_json('module_generation.json', record)
    except BaseException as exc:
        record.update(status='FAILED', reason=f'{type(exc).__name__}: {exc}')
        write_json(OUTPUT_DIR / 'module_generation.json', record)
        write_json('module_generation.json', record)
        raise
    finally:
        OUTPUT_DIR = Path('.')


def main():
    from sonar_evidence import workspace_lock
    with workspace_lock():
        publish_generation()


if __name__ == "__main__":
    main()
