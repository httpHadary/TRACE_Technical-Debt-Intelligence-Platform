"""Read-only Phase 0 inspection; does not build histories, labels or forecasts."""
import importlib.metadata
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import sys

from contracts import number

from .io import file_sha256


REQUIRED_COLUMNS = {
    "SONAR_ANALYSIS": {"PROJECT_ID", "ANALYSIS_KEY", "DATE", "REVISION"},
    "SONAR_MEASURES": {"PROJECT_ID", "ANALYSIS_KEY", "SQALE_INDEX", "QUALITY_PROFILES"},
    "GIT_COMMITS": {"PROJECT_ID", "COMMIT_HASH", "COMMITTER_DATE", "PARENTS", "IN_MAIN_BRANCH"},
}


def audit_v2(path):
    path = Path(path).resolve(strict=True)
    before = file_sha256(path)
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA temp_store=MEMORY")
        integrity = [row[0] for row in db.execute("PRAGMA integrity_check")]
        schema = {name: [dict(zip(("cid", "name", "type", "notnull", "default", "pk"), row))
                         for row in db.execute(f'PRAGMA table_info("{name}")')]
                  for name in REQUIRED_COLUMNS}
        missing = {name: sorted(columns - {c["name"] for c in schema[name]})
                   for name, columns in REQUIRED_COLUMNS.items()}
        if any(missing.values()):
            result = {"status": "BLOCKED", "integrity_check": integrity, "schema": schema,
                      "missing_columns": missing}
        else:
            counts = {name: db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                      for name in REQUIRED_COLUMNS}
            projects = [row[0] for row in db.execute("SELECT DISTINCT PROJECT_ID FROM SONAR_MEASURES ORDER BY PROJECT_ID")]
            coverage = [dict(zip(("repository_id", "measurements", "first_historical_time", "last_historical_time"), row))
                        for row in db.execute("SELECT m.PROJECT_ID, COUNT(*), MIN(a.DATE), MAX(a.DATE) FROM SONAR_MEASURES m LEFT JOIN SONAR_ANALYSIS a ON a.PROJECT_ID=m.PROJECT_ID AND a.ANALYSIS_KEY=m.ANALYSIS_KEY GROUP BY m.PROJECT_ID ORDER BY m.PROJECT_ID")]
            zeros = missing_values = invalid = 0
            valid = []
            for (raw,) in db.execute("SELECT SQALE_INDEX FROM SONAR_MEASURES"):
                try:
                    value = number(raw)
                except ValueError:
                    invalid += 1
                    continue
                if value is None:
                    missing_values += 1
                else:
                    valid.append(value)
                    zeros += value == 0
            blank = db.execute("SELECT COUNT(*) FROM SONAR_ANALYSIS WHERE ANALYSIS_KEY IS NULL OR TRIM(ANALYSIS_KEY)=''").fetchone()[0]
            duplicate_measures = db.execute("SELECT COUNT(*) FROM (SELECT PROJECT_ID,ANALYSIS_KEY FROM SONAR_MEASURES GROUP BY PROJECT_ID,ANALYSIS_KEY HAVING COUNT(*)>1)").fetchone()[0]
            duplicate_git = db.execute("SELECT COUNT(*) FROM (SELECT PROJECT_ID,COMMIT_HASH FROM GIT_COMMITS GROUP BY PROJECT_ID,COMMIT_HASH HAVING COUNT(*)>1)").fetchone()[0]
            duplicate_analysis = db.execute("SELECT COUNT(*) FROM (SELECT PROJECT_ID,ANALYSIS_KEY FROM SONAR_ANALYSIS WHERE ANALYSIS_KEY IS NOT NULL AND TRIM(ANALYSIS_KEY)<>'' GROUP BY PROJECT_ID,ANALYSIS_KEY HAVING COUNT(*)>1)").fetchone()[0]
            joined = db.execute("SELECT COUNT(*) FROM SONAR_ANALYSIS a JOIN SONAR_MEASURES m ON m.PROJECT_ID=a.PROJECT_ID AND m.ANALYSIS_KEY=a.ANALYSIS_KEY JOIN GIT_COMMITS g ON g.PROJECT_ID=a.PROJECT_ID AND g.COMMIT_HASH=a.REVISION WHERE a.ANALYSIS_KEY IS NOT NULL AND TRIM(a.ANALYSIS_KEY)<>''").fetchone()[0]
            result = {"status": "PASS" if integrity == ["ok"] and not (invalid or duplicate_measures or duplicate_git or duplicate_analysis) else "PARTIAL",
                      "integrity_check": integrity, "schema": schema, "missing_columns": missing,
                      "counts": counts, "repository_count": len(projects), "repositories": projects,
                      "coverage": coverage, "blank_analysis_keys": blank,
                      "duplicate_measure_keys": duplicate_measures, "duplicate_git_keys": duplicate_git,
                      "duplicate_analysis_keys": duplicate_analysis, "joined_measurements": joined,
                      "sqale": {"unit": "estimated_remediation_minutes", "metric": "SQALE_INDEX",
                                "missing": missing_values, "invalid": invalid, "observed_zero": zeros,
                                "valid": len(valid), "min": min(valid) if valid else None,
                                "max": max(valid) if valid else None},
                      "forecasting_eligibility": "NOT_EVALUATED_PHASE_0",
                      "limitations": ["Historical dates are not verified scan execution/online availability",
                                      "No state grid, future labels or independent cohort constructed",
                                      "Analyzer/rule/scope provenance still needs Phase 1 admission"]}
    after = file_sha256(path)
    result.update(path=str(path), bytes=path.stat().st_size, sha256=before,
                  sha256_after=after, unchanged=before == after)
    if before != after:
        result["status"] = "BLOCKED"
    return result


def environment_record(disk_path):
    names = ("pytest", "requests", "pandas", "numpy", "scikit-learn", "catboost", "networkx",
             "torch", "transformers", "accelerate", "chronos-forecasting", "granite-tsfm", "einops")
    versions = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    memory = {}
    if Path("/proc/meminfo").exists():
        for line in Path("/proc/meminfo").read_text().splitlines():
            name, value = line.split(":", 1)
            if name in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
                memory[name + "_bytes"] = int(value.split()[0]) * 1024
    disk = shutil.disk_usage(disk_path)
    cpu_name = None
    if Path("/proc/cpuinfo").exists():
        cpu_name = next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                         if line.startswith("model name")), None)
    cgroup = {}
    for name in ("memory.max", "memory.current", "cpu.max"):
        path = Path("/sys/fs/cgroup") / name
        if path.exists():
            cgroup[name] = path.read_text().strip()
    return {"python": platform.python_version(), "executable": sys.executable,
            "platform": platform.platform(), "sqlite": sqlite3.sqlite_version,
            "logical_cpus": os.cpu_count(), "cpu_model": cpu_name, "packages": versions, "memory": memory,
            "cgroup_limits": cgroup,
            "disk": {"path": str(Path(disk_path).resolve()), "total_bytes": disk.total, "free_bytes": disk.free},
            "nvidia_smi": shutil.which("nvidia-smi"), "cuda_devices": sorted(str(p) for p in Path("/dev").glob("nvidia*")),
            "model_loading": "NOT_ATTEMPTED", "compatibility": "METADATA_ONLY"}
