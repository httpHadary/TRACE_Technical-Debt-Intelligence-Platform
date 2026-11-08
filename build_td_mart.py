#!/usr/bin/env python3
"""
Builds the file-level weekly Technical Debt regression mart (td_mart.csv).

    ONE ROW = ONE FILE AT ONE WEEKLY T0.

FEATURES  everything describing the file at or before T0.
TARGETS   future Technical Debt Principal, in remediation-effort minutes:

    TD_Principal = bug_remediation_effort
                 + vulnerability_remediation_effort
                 + code_smell_remediation_effort
      (= sum of remediation effort over every ACTIVE SonarQube issue on the file)

    TD_3w = TD_Principal at T0 + 3 weeks
    TD_1m = TD_Principal at T0 + 4 weeks
    TD_3m = TD_Principal at T0 + 12 weeks

T0 technical debt is a FEATURE (technical_debt_minutes_t0 = TD_Principal at T0).
Future debt is a TARGET. Nothing after T0 is used in any feature column; the
horizon snapshots are read ONLY to build the TD_* / *_remediation_effort_<h>
target columns. Each horizon is gated independently (status OBSERVED /
UNKNOWN_OBSERVATION / UNKNOWN_LINEAGE / EXCLUDED); never impute a missing target.

ROWS KEPT: only T0 weeks HISTORY_WEEKS+1 .. last-HORIZON_WEEKS (full 26w history behind, full 12w
horizon ahead), production Java files only, with all three targets OBSERVED (see config.py
DROP_INELIGIBLE_ROWS / REQUIRE_ALL_TARGETS_OBSERVED). Result: no blank cells.

Split: chronological 60/20/20 over T0 weeks with a 12-week purge after train and
validation, so a train row's 12-week target window cannot overlap later splits.
NOTE: with 12-week purges, VALIDATION/TEST only get rows once the run has
roughly >= 100 T0 weeks (a warning is printed if either ends up empty).

Run after scan_weekly_snapshots.py, pipeline_total_line.py,
add_weekly_commits_churn.py, pipeline_g3.py, compute_git_window_features.py,
compute_lineage.py, compute_sonar_trend_features.py and
compute_finding_lifecycle.py, all with the same start_date/branch/weeks.

Usage:
    python3 build_td_mart.py <start_date> [branch] [weeks] [g3_dir]
"""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import config
from td_utils import parse_minutes
from weekly_commits import resolve_weekly_commits

DATA_DIR = Path("data")

ACTIVE_STATUSES = {"OPEN", "CONFIRMED", "REOPENED"}
HORIZONS = [("3w", 3), ("1m", 4), ("3m", 12)]
SEVERITY_COLS = {
    "BLOCKER": "blocker_finding_count_t0", "CRITICAL": "critical_finding_count_t0",
    "MAJOR": "major_finding_count_t0", "MINOR": "minor_finding_count_t0",
    "INFO": "info_finding_count_t0",
}
TYPE_COLS = {
    "CODE_SMELL": "code_smell_count_t0", "BUG": "bug_count_t0",
    "VULNERABILITY": "vulnerability_count_t0",
}
GIT_FEATURE_COLUMNS = [
    "commits_t0", "lines_added_t0", "lines_deleted_t0", "churn_t0", "authors_t0",
    "file_age_days_t0", "days_since_last_change_t0", "churn_acceleration_t0",
    "commit_burstiness_t0", "churn_burstiness_t0",
    "last_change_missing_t0", "git_history_missing_t0",
]
TREND_PREFIXES = [
    "finding_density_slope", "finding_density_volatility",
    "technical_debt_density_slope", "technical_debt_density_volatility",
    "complexity_slope", "cognitive_complexity_slope", "duplication_slope",
    "td_history_points", "td_history_missing",
]
WINDOW_SUFFIXES = ("3w", "1m", "3m", "6m")
EMPTY_DEBT = {"bug": 0, "vulnerability": 0, "code_smell": 0, "total": 0}

_COMMIT_DATE_CACHE = {}


def get_commit_date(repo_path, commit_hash):
    """Real git commit timestamp (NOT Sonar's analysis date, which is when the scan ran)."""
    if commit_hash not in _COMMIT_DATE_CACHE:
        r = subprocess.run(["git", "-C", str(repo_path), "show", "-s", "--format=%cI", commit_hash],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError(f"Could not get commit date for {commit_hash}:\n{r.stderr}")
        _COMMIT_DATE_CACHE[commit_hash] = r.stdout.strip()
    return _COMMIT_DATE_CACHE[commit_hash]


def to_bool(v):
    return str(v).strip().lower() == "true"


def safe_int(v, default=0):
    try:
        return int(float(v)) if v not in (None, "") else default
    except (TypeError, ValueError):
        return default


def load_csv_dict(path, key_col):
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        return {r[key_col]: r for r in csv.DictReader(f) if r.get(key_col)}


def component_path(component):
    component = str(component or "").strip()
    return component.split(":", 1)[1] if ":" in component else component


def load_active_issues(label):
    path = DATA_DIR / f"issues_{label}.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [i for i in json.load(f) if i.get("status") in ACTIVE_STATUSES]


def debt_breakdown_by_file(issues):
    """{path: {bug, vulnerability, code_smell, total}} in minutes."""
    key_by_type = {"BUG": "bug", "VULNERABILITY": "vulnerability", "CODE_SMELL": "code_smell"}
    out = {}
    for issue in issues:
        fp = component_path(issue.get("component"))
        if not fp:
            continue
        minutes = parse_minutes(issue.get("effort_minutes"))
        d = out.setdefault(fp, dict(EMPTY_DEBT))
        d["total"] += minutes
        t = key_by_type.get(issue.get("type"))
        if t:
            d[t] += minutes
    return out


def build_issue_state(issues):
    findings, severity, itype = {}, {}, {}
    for issue in issues:
        fp = component_path(issue.get("component"))
        if not fp:
            continue
        findings[fp] = findings.get(fp, 0) + 1
        s, t = issue.get("severity"), issue.get("type")
        if s in SEVERITY_COLS:
            severity.setdefault(fp, {})[s] = severity.get(fp, {}).get(s, 0) + 1
        if t in TYPE_COLS:
            itype.setdefault(fp, {})[t] = itype.get(fp, {}).get(t, 0) + 1
    return findings, severity, itype


def build_future_lineage_map(lineage_rows):
    """lineage_id -> artifact_id, keeping only UNIQUE mappings (ambiguous ones are dropped)."""
    cand = {}
    for artifact_id, row in lineage_rows.items():
        lid = row.get("lineage_id")
        if lid:
            cand.setdefault(lid, set()).add(artifact_id)
    return {lid: next(iter(a)) for lid, a in cand.items() if len(a) == 1}


def analyzers_compatible(meta_t0, snap_t0, meta_h, snap_h):
    pairs = [
        (meta_t0.get("sonarqube_version"), meta_h.get("sonarqube_version")),
        (meta_t0.get("java_analyzer_version"), meta_h.get("java_analyzer_version")),
        (meta_t0.get("quality_profile_hash"), meta_h.get("quality_profile_hash")),
        (snap_t0.get("analysis_mode"), snap_h.get("analysis_mode")),
    ]
    return all(a and b and a == b for a, b in pairs)


def is_production_file(file_path):
    """.java, outside test/generated/build/vendor/example/sample/benchmark/template paths."""
    return (file_path.endswith(".java")
            and not any(p in f"/{file_path}" for p in config.NON_PRODUCTION_PATH_PATTERNS)
            and not config.NON_PRODUCTION_FILENAME_REGEX.search(file_path))


def main():
    if len(sys.argv) not in (2, 3, 4, 5):
        print(__doc__)
        sys.exit(1)
    start_date = sys.argv[1]
    branch = sys.argv[2] if len(sys.argv) >= 3 else config.BRANCH
    max_weeks = int(sys.argv[3]) if len(sys.argv) >= 4 else config.DEFAULT_WEEKS
    g3_dir = Path(sys.argv[4]) if len(sys.argv) == 5 else Path("weekly_g3_features")

    weeks = resolve_weekly_commits(config.REPO_PATH, start_date, branch, max_weeks=max_weeks)
    weeks = {w: b for w, b in weeks.items() if b["commit"]}
    week_numbers = sorted(weeks)
    if not week_numbers:
        print("No weekly commits found.")
        return
    print(f">>> Found {len(week_numbers)} weekly snapshots")

    # T0 weeks that have a FULL trailing history behind them and a FULL horizon ahead:
    #   first = HISTORY_WEEKS + 1 (starts at the repo midpoint when start_date = origin_start_date)
    #   last  = latest week - HORIZON_WEEKS
    first_t0 = config.HISTORY_WEEKS + 1
    last_t0 = week_numbers[-1] - config.HORIZON_WEEKS
    t0_weeks = [w for w in week_numbers if first_t0 <= w <= last_t0]
    if not t0_weeks:
        print(f"!!! No usable T0 weeks: need weeks {first_t0}..{last_t0} but only "
              f"{week_numbers[0]}..{week_numbers[-1]} exist. Scan at least "
              f"{config.HISTORY_WEEKS + config.HORIZON_WEEKS + 1} weeks.")
        return
    print(f">>> T0 weeks: {t0_weeks[0]}..{t0_weeks[-1]} ({len(t0_weeks)} weeks; "
          f"weeks 1..{first_t0 - 1} are history warm-up, last {config.HORIZON_WEEKS} are target horizon)")

    snapshots = load_csv_dict(DATA_DIR / "snapshots.csv", "label")
    analysis_metadata = {}
    meta_path = DATA_DIR / "analysis_metadata.csv"
    if meta_path.exists():
        with open(meta_path, newline="", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                analysis_metadata[r["label"]] = r  # last row per label wins

    all_rows = []
    for t0_week in t0_weeks:
        t0_label = f"week_{t0_week:02d}"
        snap_t0 = snapshots.get(t0_label)
        if not snap_t0:
            print(f">>> Skipping {t0_label}: missing snapshot metadata.")
            continue
        meta_t0 = analysis_metadata.get(t0_label, {})
        t0_commit_date = get_commit_date(config.REPO_PATH, snap_t0["commit_hash"])

        measures_t0 = load_csv_dict(DATA_DIR / f"measures_{t0_label}.csv", "file_path")
        lineage_t0 = load_csv_dict(Path("lineage") / f"{t0_label}.csv", "artifact_id")
        git_t0 = load_csv_dict(Path("git_window_features") / f"{t0_label}.csv", "artifact_id")
        sonar_t0 = load_csv_dict(Path("sonar_trends") / f"{t0_label}.csv", "artifact_id")
        lifecycle_t0 = load_csv_dict(Path("finding_lifecycle") / f"{t0_label}.csv", "artifact_id")
        g3_t0 = load_csv_dict(g3_dir / f"{t0_label}.csv", "artifact_id")

        t0_issues = load_active_issues(t0_label)
        debt_t0 = debt_breakdown_by_file(t0_issues)
        findings_by_file, severity_by_file, type_by_file = build_issue_state(t0_issues)

        # ---- horizon snapshots: used ONLY to build target columns -----------
        horizon_data = {}
        for name, offset in HORIZONS:
            fw = t0_week + offset
            h_label = f"week_{fw:02d}"
            snap_h = snapshots.get(h_label) if fw in weeks else None
            if not snap_h:
                horizon_data[name] = None
                continue
            meta_h = analysis_metadata.get(h_label, {})
            horizon_data[name] = {
                "measures": load_csv_dict(DATA_DIR / f"measures_{h_label}.csv", "file_path"),
                "lineage_by_id": build_future_lineage_map(
                    load_csv_dict(Path("lineage") / f"{h_label}.csv", "artifact_id")),
                "debt": debt_breakdown_by_file(load_active_issues(h_label)),
                "analyzer_compatible": analyzers_compatible(meta_t0, snap_t0, meta_h, snap_h),
            }

        n_built = 0
        for file_path, measure in measures_t0.items():
            if config.DROP_INELIGIBLE_ROWS and not is_production_file(file_path):
                continue  # xml/config/test files: no lineage, no targets -> never usable rows
            row = {}
            ncloc = safe_int(measure.get("ncloc"))

            # ---- identity ---------------------------------------------------
            lin = lineage_t0.get(file_path)
            if lin:
                lineage_id = lin.get("lineage_id", "")
                lineage_confidence = lin.get("lineage_confidence", "UNSUPPORTED")
            else:
                lineage_id = hashlib.sha1(file_path.encode()).hexdigest()[:16]
                lineage_confidence = "UNSUPPORTED"

            row["origin_id"] = hashlib.sha1(
                f"{config.REPOSITORY_ID}:{file_path}:{t0_week}".encode()).hexdigest()[:20]
            row["repository_id"] = config.REPOSITORY_ID
            row["artifact_id"] = file_path
            row["lineage_id"] = lineage_id
            row["language"] = measure.get("language") or config.LANGUAGE
            row["path_at_t0"] = file_path
            row["t0"] = t0_commit_date
            row["week"] = t0_label
            row["commit_hash_t0"] = snap_t0["commit_hash"]
            row["sonar_analysis_key_t0"] = snap_t0["analysis_key"]
            row["lineage_confidence"] = lineage_confidence

            # ---- analyzer contract ---------------------------------------------
            row["sonarqube_version"] = meta_t0.get("sonarqube_version", "")
            row["java_analyzer_version"] = meta_t0.get("java_analyzer_version", "")
            row["quality_profile_id"] = meta_t0.get("quality_profile_id", "")
            row["quality_profile_hash"] = meta_t0.get("quality_profile_hash", "")
            row["analysis_mode"] = snap_t0.get("analysis_mode", "")
            row["compatible_rule_domain_version"] = meta_t0.get(
                "compatible_rule_domain_version", config.COMPATIBLE_RULE_DOMAIN_VERSION)

            # ---- T0 eligibility ---------------------------------------------------
            production_source_file = is_production_file(file_path)
            git_row = git_t0.get(file_path, {})
            sonar_row = sonar_t0.get(file_path, {})
            git_history_missing = to_bool(git_row.get("git_history_missing_t0", "True"))
            td_history_missing = to_bool(sonar_row.get("td_history_missing_6m", "True"))
            history_complete = (not git_history_missing) and (not td_history_missing) and bool(git_row)

            reasons_t0 = []
            if not production_source_file:
                reasons_t0.append("not_production_source_file")
            if not history_complete:
                reasons_t0.append("history_incomplete")
            eligible_t0 = not reasons_t0

            row["production_source_file"] = production_source_file
            row["sonar_available_t0"] = True
            row["history_complete"] = history_complete
            row["eligible_t0"] = eligible_t0
            row["exclusion_reason_t0"] = ";".join(reasons_t0)

            # ---- git features (all <= T0) -------------------------------------------
            row["ncloc_t0"] = ncloc
            for col in GIT_FEATURE_COLUMNS:
                row[col] = git_row.get(col, "")
            g3 = g3_t0.get(file_path, {})
            row["total_lines_g3"] = g3.get("total_lines", "")
            row["commits_g3"] = g3.get("commits", "")
            row["churn_g3"] = g3.get("churn", "")
            row["churn_rate_g3"] = g3.get("churn_rate", "")

            # ---- Sonar state at T0 ---------------------------------------------------
            cur = debt_t0.get(file_path, EMPTY_DEBT)
            n_find = findings_by_file.get(file_path, 0)
            row["finding_count_t0"] = n_find
            row["finding_density_t0"] = round(1000 * n_find / ncloc, 4) if ncloc > 0 else ""
            row["bug_remediation_effort_t0"] = cur["bug"]
            row["vulnerability_remediation_effort_t0"] = cur["vulnerability"]
            row["code_smell_remediation_effort_t0"] = cur["code_smell"]
            row["technical_debt_minutes_t0"] = cur["total"]          # TD_Principal at T0
            row["technical_debt_density_t0"] = round(1000 * cur["total"] / ncloc, 4) if ncloc > 0 else ""
            for sev, col in SEVERITY_COLS.items():
                row[col] = severity_by_file.get(file_path, {}).get(sev, 0)
            for typ, col in TYPE_COLS.items():
                row[col] = type_by_file.get(file_path, {}).get(typ, 0)
            row["complexity_t0"] = measure.get("complexity", "")
            row["cognitive_complexity_t0"] = measure.get("cognitive_complexity", "")
            row["duplicated_lines_density_t0"] = measure.get("duplicated_lines_density", "")
            row["comment_lines_density_t0"] = measure.get("comment_lines_density", "")

            # ---- backward-looking Sonar trends + finding lifecycle ----------------
            for suf in WINDOW_SUFFIXES:
                for prefix in TREND_PREFIXES:
                    col = f"{prefix}_{suf}"
                    row[col] = sonar_row.get(col, "")
            lc = lifecycle_t0.get(file_path, {})
            for suf in WINDOW_SUFFIXES:
                row[f"finding_arrivals_{suf}"] = lc.get(f"finding_arrivals_{suf}", 0)
                row[f"finding_closures_{suf}"] = lc.get(f"finding_closures_{suf}", 0)

            # ---- TARGETS: the only place future snapshots are read -----------------
            lineage_ok = lineage_confidence in {"HIGH", "MEDIUM"}
            for name, _offset in HORIZONS:
                # fixed column order regardless of branch taken below
                for col in (f"TD_{name}", f"TD_{name}_status", f"TD_{name}_exclusion_reason",
                            f"bug_remediation_effort_{name}",
                            f"vulnerability_remediation_effort_{name}",
                            f"code_smell_remediation_effort_{name}"):
                    row[col] = ""
                hd = horizon_data.get(name)
                if hd is None:
                    row[f"TD_{name}_status"] = "UNKNOWN_OBSERVATION"
                    row[f"TD_{name}_exclusion_reason"] = "horizon_not_scanned_yet"
                    continue

                future_path = hd["lineage_by_id"].get(lineage_id, "")
                sonar_available_future = bool(future_path) and future_path in hd["measures"]

                reasons = []
                if not eligible_t0:
                    reasons.append("t0_not_eligible")
                if not lineage_ok:
                    reasons.append("lineage_unsupported_or_ambiguous")
                if not sonar_available_future:
                    reasons.append("sonar_unavailable_at_horizon")
                if not hd["analyzer_compatible"]:
                    reasons.append("analyzer_incompatible_t0_horizon")

                if reasons:
                    if "sonar_unavailable_at_horizon" in reasons:
                        status = "UNKNOWN_OBSERVATION"
                    elif "lineage_unsupported_or_ambiguous" in reasons:
                        status = "UNKNOWN_LINEAGE"
                    else:
                        status = "EXCLUDED"
                    row[f"TD_{name}_status"] = status
                    row[f"TD_{name}_exclusion_reason"] = ";".join(reasons)
                    continue

                fut = hd["debt"].get(future_path, EMPTY_DEBT)
                row[f"bug_remediation_effort_{name}"] = fut["bug"]
                row[f"vulnerability_remediation_effort_{name}"] = fut["vulnerability"]
                row[f"code_smell_remediation_effort_{name}"] = fut["code_smell"]
                row[f"TD_{name}"] = fut["total"]
                row[f"TD_{name}_status"] = "OBSERVED"

            # ---- row filters: keep only fully-populated rows -------------------------
            if config.DROP_INELIGIBLE_ROWS and not eligible_t0:
                continue  # production file but < 26 weeks of history (file too new)
            if config.REQUIRE_ALL_TARGETS_OBSERVED and any(
                    row[f"TD_{n}_status"] != "OBSERVED" for n, _ in HORIZONS):
                continue  # file deleted/renamed within the horizon -> no target to learn from

            # Empty reason columns mean "nothing wrong"; say so instead of leaving them blank.
            for col in ["exclusion_reason_t0"] + [f"TD_{n}_exclusion_reason" for n, _ in HORIZONS]:
                if row[col] == "":
                    row[col] = "NONE"

            # ---- leakage metadata + split bookkeeping --------------------------------
            row["max_feature_ts"] = t0_commit_date
            row["split_family"] = "CHRONOLOGICAL"
            row["_t0_week"] = t0_week
            all_rows.append(row)
            n_built += 1

        print(f">>> {t0_label}: {n_built} of {len(measures_t0)} file rows kept")

    if not all_rows:
        print("No rows produced.")
        return

    # ---- chronological split: 60/20/20 by week, 12-week purge ------------------
    valid_weeks = sorted({r["_t0_week"] for r in all_rows})
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

    for row in all_rows:
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
        row["partition"] = part
        row["fold_id"] = f"chrono_{part.lower()}"

    # ---- consistency guard: Sonar's non-comment lines can never exceed the file's physical lines
    impossible = [r for r in all_rows
                  if str(r.get("ncloc_t0", "")) != "" and str(r.get("total_lines_g3", "")) != ""
                  and float(r["ncloc_t0"]) > float(r["total_lines_g3"])]
    if impossible:
        bad_weeks = sorted({r["week"] for r in impossible})
        print(f"!!! {len(impossible)} row(s) have ncloc_t0 > total_lines_g3 (impossible) in {bad_weeks[:10]} -- "
              f"stale Sonar snapshot. Run validate_snapshots.py --fix and re-scan before using this mart.")

    fieldnames = list(all_rows[0].keys())
    with open("td_mart.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n>>> Wrote {len(all_rows)} rows ({len(fieldnames)} columns) to td_mart.csv")
    print(">>> PARTITIONS")
    for part in ("TRAIN", "VALIDATION", "TEST", "PURGED", "UNASSIGNED"):
        print(f">>>   {part}: {sum(1 for r in all_rows if r['partition'] == part)}")
    for part in ("VALIDATION", "TEST"):
        if not any(r["partition"] == part for r in all_rows):
            print(f"!!! WARNING: no {part} rows. With a {purge}-week purge you need more weeks "
                  f"(currently {n} T0 weeks; ~100+ recommended). Re-run with a larger --weeks.")
    for name, _ in HORIZONS:
        obs = sum(1 for r in all_rows if r[f"TD_{name}_status"] == "OBSERVED")
        print(f">>> TD_{name}: {obs} observed / {len(all_rows)} rows")
    blanks = {c: sum(1 for r in all_rows if r.get(c, "") == "") for c in fieldnames}
    blanks = {c: n for c, n in blanks.items() if n}
    if blanks:
        print(f"!!! {len(blanks)} column(s) still contain blanks:")
        for c, n in sorted(blanks.items(), key=lambda kv: -kv[1]):
            print(f"!!!   {c}: {n}/{len(all_rows)} blank")
    else:
        print(f">>> No blank cells in any of the {len(fieldnames)} columns.")
    print(">>> Targets (TD_*, *_status, *_exclusion_reason, *_remediation_effort_<3w|1m|3m>) are "
          "label-only: never put them in X. Filter each target on its own TD_*_status == 'OBSERVED'.")


if __name__ == "__main__":
    main()
