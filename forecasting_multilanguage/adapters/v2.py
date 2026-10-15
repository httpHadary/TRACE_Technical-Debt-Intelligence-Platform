"""Reproducible legacy audit, raw-reference candidates and churn reconciliation.

V2 has no complete immutable analyzer bundle. It is never a strict schema2
observation source merely because a join or metric is valid.
"""
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
import re
import sqlite3
from ..contracts import digest, raw_measure, metric_unit
from ..git_events import legacy_path_proof, MissingGitObject
from ..io import file_sha256
from ..registry import language_distribution

METRICS = ("SQALE_INDEX", "NCLOC", "LINES", "FILES", "CLASSES", "FUNCTIONS", "STATEMENTS",
           "COMPLEXITY", "COGNITIVE_COMPLEXITY", "CODE_SMELLS", "BUGS", "VULNERABILITIES",
           "VIOLATIONS", "SQALE_DEBT_RATIO", "SQALE_RATING", "DUPLICATED_LINES",
           "DUPLICATED_LINES_DENSITY", "COMMENT_LINES", "DEVELOPMENT_COST", "COVERAGE", "TEAM_SIZE", "BUSINESS_VALUE")


@contextmanager
def read_only_database(path, expected_sha256):
    path = Path(path).resolve(strict=True)
    if file_sha256(path) != expected_sha256:
        raise ValueError("Source database identity mismatch")
    con = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        con.execute("PRAGMA temp_store=MEMORY")
        con.row_factory = sqlite3.Row
        yield con
    finally:
        con.close()
    if file_sha256(path) != expected_sha256:
        raise ValueError("Source database changed during audit")


def numstat(value):
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        return int(value)
    raise ValueError("Invalid nonnegative integer numstat")


def source_audit(con):
    tables = ("PROJECTS", "GIT_COMMITS", "GIT_COMMITS_CHANGES", "SONAR_MEASURES", "SONAR_ANALYSIS",
              "SONAR_ISSUES", "SONAR_RULES", "JIRA_ISSUES", "REFACTORING_MINER", "SZZ_FAULT_INDUCING_COMMITS")
    result = {"schema_version": 2, "lane": "LEGACY_DOMAIN_UNVERIFIED",
              "table_counts": {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}}
    result["metric_coverage"] = {}
    for metric in METRICS:
        counts = Counter()
        for row in con.execute(f'SELECT "{metric}" FROM SONAR_MEASURES'):
            value = row[0]
            measure = raw_measure(value)
            counts[measure.status] += 1
            counts["sql_nulls"] += value is None
            counts["observed_zeros"] += measure.value == 0 if measure.value is not None else False
        result["metric_coverage"][metric] = {k: counts[k] for k in ("OBSERVED", "MISSING", "INVALID", "sql_nulls", "observed_zeros")}
    languages, projects, invalid, missing = Counter(), defaultdict(set), Counter(), 0
    for row in con.execute("SELECT PROJECT_ID,NCLOC_LANGUAGE_DISTRIBUTION FROM SONAR_MEASURES"):
        values, errors = language_distribution(row[1])
        missing += row[1] in (None, "")
        invalid.update(errors if row[1] not in (None, "") else [])
        for key, value in values.items():
            if value > 0:
                languages[key] += 1
                projects[key].add(row[0])
    result["language_coverage"] = {"positive_observations": dict(sorted(languages.items())),
                                   "projects": {k: len(v) for k, v in sorted(projects.items())},
                                   "missing_distributions": missing, "invalid_tokens": dict(invalid)}
    invalid = 0
    for row in con.execute("SELECT LINES_ADDED,LINES_REMOVED FROM GIT_COMMITS_CHANGES"):
        try:
            numstat(row[0]); numstat(row[1])
        except ValueError:
            invalid += 1
    result["invalid_numstat_rows"] = invalid
    # Avoid a correlated scan over an unindexed source; use distinct keys in memory.
    keys = {(r[0], r[1]) for r in con.execute("SELECT PROJECT_ID,COMMIT_HASH FROM GIT_COMMITS")}
    result["orphan_change_keys"] = sum((r[0], r[1]) not in keys for r in con.execute("SELECT DISTINCT PROJECT_ID,COMMIT_HASH FROM GIT_COMMITS_CHANGES"))
    result["analyzer_domain_status"] = "INCOMPLETE"
    result["F2_enabled"] = False
    return result


def churn_audit(con, git_sources):
    """Hash-ordered, per-project round-robin sample: >=10 conflict +10 clean.

    git_sources maps native PROJECT_ID to an already available local Git checkout.
    All groups are audited before choosing a sample. No source repair or aggregate
    promotion follows from a small sample; every future included window needs proof.
    """
    sql = """SELECT PROJECT_ID,COMMIT_HASH,FILE,COUNT(*) n,
      MIN(CAST(LINES_ADDED AS INTEGER)) alo,MAX(CAST(LINES_ADDED AS INTEGER)) ahi,
      MIN(CAST(LINES_REMOVED AS INTEGER)) dlo,MAX(CAST(LINES_REMOVED AS INTEGER)) dhi
      FROM GIT_COMMITS_CHANGES GROUP BY PROJECT_ID,COMMIT_HASH,FILE"""
    pools = {"CONFLICT": defaultdict(list), "CLEAN": defaultdict(list)}
    total = duplicates = extra = conflicting = 0
    for row in con.execute(sql):
        total += 1
        duplicates += row["n"] > 1
        extra += row["n"] - 1
        conflict = row["alo"] != row["ahi"] or row["dlo"] != row["dhi"]
        conflicting += conflict
        group = "CONFLICT" if conflict else "CLEAN"
        record = dict(row)
        record["selection_hash"] = digest([row["PROJECT_ID"], row["COMMIT_HASH"], row["FILE"]])
        # Bounded reservoir of smallest deterministic hashes per stratum/project.
        pool = pools[group][row["PROJECT_ID"]]
        pool.append(record)
        pool.sort(key=lambda r: r["selection_hash"])
        del pool[10:]
    sample = []
    for group in ("CONFLICT", "CLEAN"):
        available = pools[group]
        projects = sorted(p for p in available if p in git_sources)
        if not projects:
            projects = sorted(available)
        chosen = []
        for round_index in range(10):
            for project in projects:
                if round_index < len(available[project]):
                    chosen.append(available[project][round_index])
                    if len(chosen) == 10:
                        break
            if len(chosen) == 10:
                break
        for record in chosen:
            record = dict(record, stratum=group)
            path = git_sources.get(record["PROJECT_ID"])
            if path is None:
                record["verification_status"] = "NO_LOCAL_GIT_SOURCE"
            else:
                try:
                    proof = legacy_path_proof(path, record["COMMIT_HASH"], record["FILE"])
                    record["authoritative_diff"] = proof
                    raw = con.execute("SELECT LINES_ADDED,LINES_REMOVED FROM GIT_COMMITS_CHANGES WHERE PROJECT_ID=? AND COMMIT_HASH=? AND FILE=?",
                                      (record["PROJECT_ID"], record["COMMIT_HASH"], record["FILE"])).fetchall()
                    pairs = sorted({(numstat(r[0]), numstat(r[1])) for r in raw})
                    record["distinct_source_pairs"] = pairs
                    record["verification_status"] = ("AMBIGUOUS_PATH_IDENTITY" if proof["resolution"] == "AMBIGUOUS_BASENAME" else
                        "NO_MATCHING_PATH" if not proof["matches"] else "BINARY" if proof["matches"][0]["added"] is None else
                        "MATCHES_ONE_VARIANT_UNIQUE_PATH" if (proof["matches"][0]["added"], proof["matches"][0]["removed"]) in pairs
                        else "NO_SOURCE_VARIANT_MATCH_UNIQUE_PATH")
                except MissingGitObject:
                    record["verification_status"] = "GIT_OBJECTS_UNAVAILABLE"
            sample.append(record)
    return {"unique_keys": total, "duplicate_keys": duplicates, "extra_rows": extra,
            "conflicting_keys": conflicting, "sample_policy": "smallest_sha256_per_local_project_round_robin_10_per_stratum_else_unavailable_sources",
            "sample": sample, "F2_enabled": False,
            "disabled_reason": "SAMPLE_IS_NOT_FULL_WINDOW_RECONCILIATION_OR_COVERAGE_PROOF"}


def candidate_measurements(con, source_digest):
    """Stream raw-key lineage, preserving every null; never admits schema2 states."""
    sql = """SELECT m.*,a.REVISION,a.DATE FROM SONAR_MEASURES m LEFT JOIN SONAR_ANALYSIS a
             ON m.PROJECT_ID=a.PROJECT_ID AND m.ANALYSIS_KEY=a.ANALYSIS_KEY
             ORDER BY m.PROJECT_ID,m.ANALYSIS_KEY"""
    for row in con.execute(sql):
        values, errors = language_distribution(row["NCLOC_LANGUAGE_DISTRIBUTION"])
        ref = {"source_sha256": source_digest, "project_id": row["PROJECT_ID"], "analysis_id": row["ANALYSIS_KEY"],
               "revision_raw": row["REVISION"], "analysis_date_raw": row["DATE"]}
        yield {"schema_version": 2, "candidate_id": digest(ref), "source_reference": ref,
               "admission_status": "LEGACY_DOMAIN_UNVERIFIED", "language_ncloc": values, "language_errors": errors,
               "measures": {k.lower(): asdict(raw_measure(row[k], metric_unit(k)))
                            for k in METRICS}}


def candidate_identity_audit(con, source_digest):
    """Check exact legacy joins without materializing a new forecasting dataset."""
    import hashlib
    from ..contracts import canonical, revision
    project_counts, identities, missing_revision, invalid_revision = Counter(), set(), 0, 0
    hasher = hashlib.sha256()
    for candidate in candidate_measurements(con, source_digest):
        if candidate["candidate_id"] in identities:
            raise ValueError("Duplicate exact legacy source identity")
        identities.add(candidate["candidate_id"])
        ref = candidate["source_reference"]
        project_counts[ref["project_id"]] += 1
        missing_revision += ref["revision_raw"] in (None, "")
        try:
            revision(ref["revision_raw"])
        except ValueError:
            invalid_revision += 1
        hasher.update(canonical(ref) + b"\n")
    return {"candidate_records": len(identities), "projects": dict(sorted(project_counts.items())),
            "missing_revision": missing_revision, "invalid_or_missing_revision": invalid_revision,
            "ordered_source_reference_sha256": hasher.hexdigest(), "strict_admitted_records": 0,
            "admission_status": "LEGACY_DOMAIN_UNVERIFIED", "timestamp_policy": "RAW_DATE_PRESERVED_NOT_ASSUMED_UTC"}
