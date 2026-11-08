"""Phase 1 read-only history ingestion. No grid, future labels or models."""
import ast
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import statistics

from contracts import digest, number, read_json, write_csv, write_json

from .contracts import utc_iso, utc_timestamp
from .io import file_sha256, publish_manifest
from .verification import REQUIRED_COLUMNS


SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
FIELDS = (
    "observation_id", "repository_id", "source_project_id", "commit_sha", "committer_timestamp",
    "historical_timestamp", "analysis_id", "sqale_index_minutes", "metric", "unit", "scope_id",
    "profile_hash", "domain_id", "domain_segment_id", "profile_status", "mainline_status",
    "first_parent_index", "chronology_status", "provenance_status", "source_sha256", "limitations",
)
GIT_FIELDS = ("repository_id", "source_project_id", "commit_sha", "committer_timestamp", "parents_json",
              "in_main_branch", "parent_status", "mainline_status", "first_parent_index", "has_measurement")
SOURCE_URL = "https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1"


@dataclass(frozen=True)
class HistoryConfig:
    dataset_path: str
    output_root: str
    expected_source_sha256: str | None = None
    dataset_source: str = SOURCE_URL
    dataset_license: str = "CC-BY-NC-SA-4.0"
    phase: int = 1
    mvp_schema_version: int = 1

    def __post_init__(self):
        if type(self.phase) is not int or self.phase != 1 or type(self.mvp_schema_version) is not int or self.mvp_schema_version != 1:
            raise ValueError("Only Phase 1 / schema 1 history ingestion supported")
        if self.dataset_source != SOURCE_URL or self.dataset_license != "CC-BY-NC-SA-4.0":
            raise ValueError("Explicit V2 release and dataset license required")
        for value in (self.dataset_path, self.output_root):
            if not isinstance(value, str) or not Path(value).is_absolute():
                raise ValueError("Absolute dataset/output paths required")
        if Path(self.dataset_path).resolve().is_relative_to(Path(self.output_root).resolve()):
            raise ValueError("Source must be outside output root")
        if self.expected_source_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", self.expected_source_sha256):
            raise ValueError("Expected source SHA-256 must be immutable or null")

    @classmethod
    def load(cls, path):
        return cls(**read_json(path))


def imported_time(value, allow_naive=False):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Missing timestamp")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    naive = dt.tzinfo is None
    if naive:
        if not allow_naive:
            raise ValueError("Naive Git time cannot establish UTC chronology")
        dt = dt.replace(tzinfo=timezone.utc)
    return utc_iso(dt), naive


def parse_parents(value):
    parsed = ast.literal_eval(value) if isinstance(value, str) else value
    if not isinstance(parsed, (list, tuple)) or any(not isinstance(v, str) or not SHA.fullmatch(v) for v in parsed):
        raise ValueError("Invalid parent list")
    if len(set(parsed)) != len(parsed):
        raise ValueError("Duplicate parent identities")
    return tuple(parsed)


def profile_record(value):
    """Normalize dataset semicolon separators without modifying quoted values."""
    if value is None or not str(value).strip():
        return None, "MISSING"
    text = str(value)
    normalized = []
    quoted = escaped = False
    for char in text:
        if escaped:
            escaped = False
        elif char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        normalized.append("," if char == ";" and not quoted else char)
    try:
        profiles = json.loads("".join(normalized))
        if not isinstance(profiles, list) or not profiles or any(
                not isinstance(p, dict) or not p.get("key") or not p.get("language") for p in profiles):
            raise ValueError("Missing profile identities")
        profiles = sorted(profiles, key=lambda p: json.dumps(p, sort_keys=True, separators=(",", ":")))
        if len({p["language"] for p in profiles}) != len(profiles):
            raise ValueError("Ambiguous language profile")
        return profiles, "KNOWN_METADATA_ONLY"
    except (ValueError, TypeError, KeyError):
        return None, "INVALID"


def mainline_audit(commits):
    """Use a unique graph tip, never the latest measured timestamp; no branch oracle."""
    referenced = {parent for c in commits.values() for parent in c["parents"] if parent in commits}
    tips = sorted(set(commits) - referenced)
    missing_edges = sorted((sha, parent) for sha, c in commits.items() for parent in c["parents"] if parent not in commits)
    inverted = sorted((sha, parent) for sha, c in commits.items() for parent in c["parents"]
                      if parent in commits and utc_timestamp(commits[parent]["time"]) > utc_timestamp(c["time"]))
    chain = []
    boundary = None
    children = defaultdict(list)
    degree = {}
    for sha, commit in commits.items():
        degree[sha] = sum(p in commits for p in commit["parents"])
        for parent in commit["parents"]:
            if parent in commits:
                children[parent].append(sha)
    ready = deque(sha for sha, n in degree.items() if n == 0)
    visited = 0
    while ready:
        sha = ready.popleft()
        visited += 1
        for child in children[sha]:
            degree[child] -= 1
            if degree[child] == 0:
                ready.append(child)
    cyclic = len(commits) - visited
    if cyclic:
        boundary = "NO_TIP_OR_CYCLE" if not tips else "CYCLIC_GRAPH"
    elif len(tips) == 1:
        current = tips[0]
        seen = set()
        while current in commits and current not in seen:
            seen.add(current)
            chain.append(current)
            parents = commits[current]["parents"]
            if not parents:
                break
            current = parents[0]
        if current in seen and commits[current]["parents"] and commits[current]["parents"][0] in seen:
            boundary = "CYCLE"
        elif current not in commits:
            boundary = "MISSING_FIRST_PARENT"
    else:
        boundary = "AMBIGUOUS_TIPS" if tips else "NO_TIP_OR_CYCLE"
    chain.reverse()
    indices = {sha: i for i, sha in enumerate(chain)}
    first_parent_inversions = [i for i in range(1, len(chain))
                               if utc_timestamp(commits[chain[i]]["time"]) < utc_timestamp(commits[chain[i - 1]]["time"])]
    return {"candidate_tips": tips, "selected_tip": tips[0] if len(tips) == 1 and not cyclic else None,
            "boundary": boundary, "missing_parent_edges": len(missing_edges),
            "cyclic_or_cycle_dependent_nodes": cyclic,
            "missing_parent_examples": missing_edges[:10], "parent_timestamp_inversions": len(inverted),
            "first_parent_timestamp_inversions": len(first_parent_inversions),
            "first_parent_inversion_indices": first_parent_inversions,
            "first_parent_commits": len(chain), "non_first_parent_commits": len(commits) - len(chain)}, indices


def gap_summary(times):
    dates = sorted({utc_timestamp(t) for t in times})
    gaps = [(b - a).total_seconds() / 86400 for a, b in zip(dates, dates[1:])]
    return {"distinct_timestamps": len(dates), "median_gap_days": statistics.median(gaps) if gaps else None,
            "max_gap_days": max(gaps) if gaps else None,
            "p90_gap_days": sorted(gaps)[max(0, int(0.9 * len(gaps)) - 1)] if gaps else None,
            "span_days": (dates[-1] - dates[0]).total_seconds() / 86400 if dates else 0,
            "first_timestamp": utc_iso(dates[0]) if dates else None,
            "last_timestamp": utc_iso(dates[-1]) if dates else None}


def ingest_history(config, output):
    source = Path(config.dataset_path).resolve(strict=True)
    output = Path(output).resolve()
    if output.exists() or not output.is_relative_to(Path(config.output_root).resolve()):
        raise ValueError("New output directory inside configured root required")
    source_hash = file_sha256(source)
    if config.expected_source_sha256 and source_hash != config.expected_source_sha256:
        raise ValueError("Source hash differs from registered release")
    # All publication happens after validation; a source/schema failure creates no valid bundle.
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA temp_store=MEMORY")
        integrity = [r[0] for r in db.execute("PRAGMA integrity_check")]
        if integrity != ["ok"]:
            raise ValueError("SQLite integrity check failed")
        required = {name: set(cols) for name, cols in REQUIRED_COLUMNS.items()}
        schema = {name: [r[1] for r in db.execute(f'PRAGMA table_info("{name}")')] for name in required}
        if any(not cols.issubset(schema[name]) for name, cols in required.items()):
            raise ValueError("Required source schema missing")
        raw_git = defaultdict(list)
        for row in db.execute("SELECT PROJECT_ID,COMMIT_HASH,COMMITTER_DATE,PARENTS,IN_MAIN_BRANCH FROM GIT_COMMITS ORDER BY PROJECT_ID,COMMIT_HASH"):
            raw_git[(row[0], row[1])].append(row)
        raw_measures = defaultdict(list)
        for row in db.execute("SELECT PROJECT_ID,ANALYSIS_KEY,SQALE_INDEX,QUALITY_PROFILES FROM SONAR_MEASURES ORDER BY PROJECT_ID,ANALYSIS_KEY"):
            raw_measures[(row[0], row[1])].append(row)
        analyses = list(db.execute("SELECT PROJECT_ID,ANALYSIS_KEY,DATE,REVISION FROM SONAR_ANALYSIS ORDER BY PROJECT_ID,DATE,ANALYSIS_KEY,REVISION"))
    git_by_project = defaultdict(dict)
    exclusions = []
    git_excluded = Counter()
    for (project, sha), group in raw_git.items():
        try:
            if len(group) != 1:
                raise ValueError("DUPLICATE_GIT_KEY")
            if not isinstance(project, str) or not project or not isinstance(sha, str) or not SHA.fullmatch(sha):
                raise ValueError("INVALID_GIT_IDENTITY")
            _, _, timestamp, parents, main = group[0]
            stamp, _ = imported_time(timestamp)
            parsed = parse_parents(parents)
            is_main = str(main).strip().lower() in ("true", "1")
            if not is_main:
                raise ValueError("NOT_MAIN_BRANCH_FLAG")
            git_by_project[project][sha] = {"time": stamp, "parents": parsed}
        except (ValueError, TypeError, SyntaxError) as exc:
            reason = str(exc)
            git_excluded[reason] += 1
            exclusions.append({"kind": "git", "source_project_id": project, "revision": sha, "reason": reason})
    graphs = {}
    indices = {}
    for project in sorted(git_by_project):
        graphs[project], indices[project] = mainline_audit(git_by_project[project])
    analysis_keys = Counter((p, k) for p, k, _, _ in analyses if k and str(k).strip())
    revision_keys = Counter((p, s) for p, k, _, s in analyses if k and str(k).strip())
    rows = []
    rejected = Counter()
    naively_imported = 0
    for project, key, date, revision in analyses:
        try:
            if not key or not str(key).strip():
                raise ValueError("BLANK_ANALYSIS_KEY")
            if analysis_keys[(project, key)] != 1:
                raise ValueError("DUPLICATE_ANALYSIS_KEY")
            if revision_keys[(project, revision)] != 1:
                raise ValueError("AMBIGUOUS_REVISION_ANALYSES")
            measures = raw_measures.get((project, key), [])
            if len(measures) != 1:
                raise ValueError("MISSING_MEASUREMENT" if not measures else "DUPLICATE_MEASURE_KEY")
            commit = git_by_project.get(project, {}).get(revision)
            if commit is None:
                raise ValueError("UNADMITTED_GIT_REVISION")
            stamp, naive = imported_time(date, allow_naive=True)
            if stamp != commit["time"]:
                raise ValueError("ANALYSIS_COMMIT_TIMESTAMP_MISMATCH")
            value = number(measures[0][2])
            profiles, profile_status = profile_record(measures[0][3])
            profile_hash = digest(profiles) if profiles is not None else None
            repo_id = "v2-" + digest(project)[:24]
            index = indices[project].get(revision)
            on_chain = index is not None
            graph = graphs[project]
            main_status = "FIRST_PARENT" if on_chain else "NON_FIRST_PARENT" if graph["selected_tip"] else "UNRESOLVED_MAINLINE"
            inverted = on_chain and index in graph["first_parent_inversion_indices"]
            limitations = ["IMPORTED_ANALYZER_RULES_SCANNER_BUILD_SCOPE_DETAILS_UNKNOWN",
                           "RETROSPECTIVE_MAINLINE_NOT_ONLINE_AVAILABILITY"]
            if value is None:
                limitations.append("MISSING_SQALE")
            if profile_status != "KNOWN_METADATA_ONLY":
                limitations.append("PROFILE_" + profile_status)
            if naive:
                limitations.append("NAIVE_ANALYSIS_ASSIGNED_UTC_AFTER_GIT_MATCH")
            if graph["boundary"]:
                limitations.append(graph["boundary"])
            if not on_chain:
                limitations.append(main_status)
            if inverted:
                limitations.append("FIRST_PARENT_TIME_INVERSION")
            rows.append({"observation_id": digest([source_hash, project, key, revision]),
                         "repository_id": repo_id, "source_project_id": project, "commit_sha": revision,
                         "committer_timestamp": commit["time"], "historical_timestamp": stamp,
                         "analysis_id": key, "sqale_index_minutes": value, "metric": "SQALE_INDEX",
                         "unit": "estimated_remediation_minutes", "scope_id": "native_project",
                         "profile_hash": profile_hash, "domain_id": digest([source_hash, project, "native_project", profile_hash]) if profile_hash else None,
                         "domain_segment_id": None, "profile_status": profile_status,
                         "mainline_status": main_status, "first_parent_index": index,
                         "chronology_status": "INVERTED_FIRST_PARENT_EDGE" if inverted else "TIMESTAMP_LINK_VERIFIED",
                         "provenance_status": "AUDITED_IMPORTED", "source_sha256": source_hash,
                         "limitations": "|".join(limitations)})
            naively_imported += naive
        except (ValueError, TypeError) as exc:
            reason = str(exc)
            rejected[reason] += 1
            exclusions.append({"kind": "analysis", "source_project_id": project, "analysis_id": key,
                               "revision": revision, "reason": reason})
    rows.sort(key=lambda r: (r["source_project_id"], r["historical_timestamp"], r["commit_sha"], r["analysis_id"]))
    projects = sorted(set(git_by_project) | {r[0] for r in analyses})
    diagnostics = []
    measured = defaultdict(set)
    for r in rows:
        measured[r["source_project_id"]].add(r["commit_sha"])
    for project in projects:
        project_rows = [r for r in rows if r["source_project_id"] == project]
        # Segment only observed metadata, not an assertion about unknown intervening scans.
        segment = 0
        prior = object()
        previous_index = None
        ordered = sorted(project_rows, key=lambda r: (r["first_parent_index"] is None,
                          r["first_parent_index"] if r["first_parent_index"] is not None else 0,
                          r["historical_timestamp"], r["analysis_id"]))
        for row in ordered:
            index = row["first_parent_index"]
            crossing_inversion = index is not None and previous_index is not None and any(
                previous_index < i <= index for i in graphs[project]["first_parent_inversion_indices"])
            if row["profile_hash"] != prior or crossing_inversion:
                segment += 1
            if row["profile_hash"]:
                row["domain_segment_id"] = digest([row["domain_id"], segment])
            prior = row["profile_hash"]
            previous_index = index
        summary = gap_summary([r["historical_timestamp"] for r in project_rows])
        commits = git_by_project.get(project, {})
        lo = summary["first_timestamp"]
        hi = summary["last_timestamp"]
        in_span = [sha for sha, c in commits.items() if lo is not None and lo <= c["time"] <= hi]
        graph = graphs.get(project, {"selected_tip": None, "boundary": "NO_ADMITTED_COMMITS"})
        hints = {}
        for h in (30, 60, 90):
            hints[str(h)] = {"span_covers_90_context_plus_horizon": summary["span_days"] >= 89 + h,
                             "endpoint_pair_count": None, "eligible_origins": None,
                             "status": "NOT_EVALUATED_NO_FUTURE_LABELS"}
        diagnostics.append({"source_project_id": project, "repository_id": "v2-" + digest(project)[:24],
                            "measurements": len(project_rows), "valid_debt_values": sum(r["sqale_index_minutes"] is not None for r in project_rows),
                            "missing_debt_values": sum(r["sqale_index_minutes"] is None for r in project_rows),
                            "git_commits": len(commits), "unmeasured_revisions": len(set(commits) - measured[project]),
                            "in_measured_span_commits": len(in_span),
                            "in_measured_span_unmeasured_revisions": sum(s not in measured[project] for s in in_span),
                            "profile_status_counts": dict(sorted(Counter(r["profile_status"] for r in project_rows).items())),
                            "observed_domain_chronology_segments": segment, "distinct_profile_hashes": len({r["profile_hash"] for r in project_rows if r["profile_hash"]}),
                            "mainline_status_counts": dict(sorted(Counter(r["mainline_status"] for r in project_rows).items())),
                            "history": summary, "ancestry": graph, "horizon_screening": hints})
    git_rows = []
    for project in sorted(git_by_project):
        for sha, commit in sorted(git_by_project[project].items()):
            index = indices[project].get(sha)
            git_rows.append({"repository_id": "v2-" + digest(project)[:24], "source_project_id": project,
                             "commit_sha": sha, "committer_timestamp": commit["time"],
                             "parents_json": json.dumps(commit["parents"], separators=(",", ":")), "in_main_branch": True,
                             "parent_status": "MISSING_PARENT" if any(p not in git_by_project[project] for p in commit["parents"]) else "PRESENT",
                             "mainline_status": "FIRST_PARENT" if index is not None else "NON_FIRST_PARENT" if graphs[project]["selected_tip"] else "UNRESOLVED_MAINLINE",
                             "first_parent_index": index, "has_measurement": sha in measured[project]})
    after_hash = file_sha256(source)
    if source_hash != after_hash:
        raise ValueError("Source changed during ingestion; publication rejected")
    implementation = {p.name: file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
    implementation["legacy_contracts.py"] = file_sha256(Path(__file__).parent.parent / "contracts.py")
    audit = {"phase": 1, "mvp_schema_version": 1, "implementation_sha256": implementation, "status": "PARTIAL" if rejected or git_excluded or any(
             d["ancestry"].get("boundary") or d["ancestry"].get("first_parent_timestamp_inversions") or
             d["profile_status_counts"].get("MISSING") or d["profile_status_counts"].get("INVALID") for d in diagnostics) else "PASS",
             "source": {"sha256": source_hash, "sha256_after": after_hash, "unchanged": True,
                        "bytes": source.stat().st_size, "release": config.dataset_source, "license": config.dataset_license},
             "config": asdict(config), "schema": schema, "sqlite_integrity_check": integrity,
             "counts": {"source_analysis_rows": len(analyses), "source_git_rows": sum(len(v) for v in raw_git.values()),
                        "source_measure_rows": sum(len(v) for v in raw_measures.values()), "historical_debt_rows": len(rows),
                        "git_history_rows": len(git_rows), "repositories": len(diagnostics),
                        "missing_debt_values": sum(r["sqale_index_minutes"] is None for r in rows),
                        "observed_zero_debt": sum(r["sqale_index_minutes"] == 0 for r in rows),
                        "naive_analysis_dates_assigned_utc_after_exact_git_match": naively_imported,
                        "excluded_analyses": sum(rejected.values()), "excluded_git_records": sum(git_excluded.values()),
                        "orphan_measure_keys": sum(k not in analysis_keys for k in raw_measures),
                        "unmeasured_revisions": sum(d["unmeasured_revisions"] for d in diagnostics),
                        "in_span_unmeasured_revisions": sum(d["in_measured_span_unmeasured_revisions"] for d in diagnostics)},
             "exclusion_reason_counts": dict(sorted(rejected.items())), "git_exclusion_reason_counts": dict(sorted(git_excluded.items())),
             "repositories": diagnostics, "forecasting_readiness": "REQUIRES_PHASE_2_CONTEXT_AND_ENDPOINT_AUDIT",
             "future_labels_constructed": False, "models_executed": False,
             "limitations": ["AUDITED_IMPORTED verifies joins, numeric values and timestamp provenance only",
                             "Profile metadata is not an immutable complete analyzer/rule/build-mode domain",
                             "Graph-tip inference from archived main-flag ancestry is not historical online availability",
                             "Span and gaps do not prove regularly measured inputs or exact future outcomes"]}
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "historical_debt.csv", rows, FIELDS)
    write_csv(output / "git_history.csv", git_rows, GIT_FIELDS)
    write_json(output / "historical_data_audit.json", audit)
    write_json(output / "excluded_records.json", exclusions)
    sample = [next(r for r in rows if r["source_project_id"] == p) for p in sorted({r["source_project_id"] for r in rows})[:12]]
    write_csv(output / "historical_debt_sample.csv", sample, FIELDS)
    publish_manifest(output, ["historical_debt.csv", "git_history.csv", "historical_data_audit.json", "excluded_records.json", "historical_debt_sample.csv"],
                     {"phase": 1, "status": audit["status"], "source_sha256": source_hash,
                      "future_labels_constructed": False, "models_executed": False})
    return audit
