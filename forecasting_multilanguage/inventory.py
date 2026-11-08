"""Bounded local-only archive discovery. Metadata findings are not admission."""
import csv
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlsplit
from .git_events import git
from .io import file_sha256
from .registry import language_distribution
from .contracts import digest


def exposure_inventory(records):
    """Exact URL aliases coalesce; names/fork families remain unresolved.

    All prior-study sources count as exposed, including old sealed cohorts.
    This is deliberately not an automatic new held-out family enrollment service.
    """
    output = {}
    for record in records:
        identity, source = record["identity"].strip(), record["source_ref"]
        if not identity or not source:
            raise ValueError("Exposure identity/source reference required")
        url = repository_url(identity)
        if url is None and identity.count("/") == 1 and not any(c in identity for c in (" ", ":", "\\")):
            url = repository_url("https://github.com/" + identity)
        key = digest(url or identity.lower())
        item = output.setdefault(key, {"exposure_key": key, "canonical_url": url, "names": [], "source_refs": [],
            "exposure_status": "EXPOSED", "family_resolution": "URL_ALIAS_ONLY_FORK_UNVERIFIED" if url else "UNRESOLVED_NAME",
            "eligible_for_new_held_out": False})
        item["names"] = sorted(set(item["names"] + [identity]))
        item["source_refs"] = sorted(set(item["source_refs"] + [source]))
    return [output[k] for k in sorted(output)]


def repository_url(value):
    value = value.strip()
    if value.startswith("git@github.com:"):
        value = "https://github.com/" + value.split(":", 1)[1]
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        return None
    return f"https://{parsed.hostname.lower()}{parsed.path.rstrip('/').removesuffix('.git').lower()}"


def discover_local_sources(roots, *, max_files=100000, max_depth=8, excluded_roots=()):
    """Caller explicitly supplies approved roots. No home-wide or network search.

    Excludes model outputs, private settings, caches, fixtures, held-out directories
    and source worktrees after finding a .git root. Missing traversal coverage is
    reported, never interpreted as evidence that no archives exist elsewhere.
    """
    repos, payloads, registries, inaccessible = [], [], [], []
    excluded_roots = sorted({Path(p).resolve() for p in excluded_roots})
    considered, truncated = 0, False
    skip = {".git", "node_modules", "__pycache__", ".pytest_cache", "m2-cache", "model_cache",
            "target", "build", "dist", "test", "tests", "sealed", "holdout", "checkpoints"}
    for raw_root in sorted(set(map(str, roots))):
        root = Path(raw_root).resolve()
        if not root.exists():
            inaccessible.append(str(root))
            continue
        for parent, dirs, files in os.walk(root, followlinks=False):
            directory = Path(parent)
            if any(directory.is_relative_to(p) for p in excluded_roots):
                dirs[:] = []
                continue
            depth = len(directory.relative_to(root).parts)
            dirs[:] = sorted(d for d in dirs if d not in skip and not d.startswith((".venv", ".env")) and not (directory / d).is_symlink())
            if (directory / ".git").exists():
                try:
                    url = repository_url(git(directory, "config", "--get", "remote.origin.url").decode())
                    tip = git(directory, "rev-parse", "HEAD").decode().strip()
                    if url:
                        repos.append({"path": str(directory), "canonical_url": url, "tip_sha": tip,
                                      "status": "GIT_ONLY_NOT_LICENSE_OR_ANALYSIS_ADMISSION"})
                except subprocess.CalledProcessError:
                    inaccessible.append(str(directory))
                dirs[:] = []
            if depth >= max_depth:
                if dirs:
                    truncated = True
                dirs[:] = []
            for name in sorted(files):
                considered += 1
                if considered > max_files:
                    truncated = True
                    break
                path = directory / name
                lower = name.lower()
                if path.is_symlink() or path.stat().st_size > 2_000_000:
                    continue
                if lower.endswith(".csv") and ("registry" in lower or "repositories" in lower):
                    with path.open(newline="", encoding="utf-8-sig") as stream:
                        rows = csv.DictReader(stream)
                        columns = rows.fieldnames or []
                        # Read only identity/exposure columns, never outcome fields.
                        keys = [k for k in columns if k.lower() in ("repository", "repository_id", "repo", "url", "role", "license")]
                        identities = [{k: row[k] for k in keys} for row in rows] if keys else []
                    registries.append({"path": str(path), "sha256": file_sha256(path), "identities": identities})
                if lower.endswith(".json") and any(word in lower for word in ("measure", "snapshot", "analysis", "manifest", "admission_result")):
                    try:
                        value = json.loads(path.read_text())
                    except (ValueError, UnicodeError):
                        continue
                    if not isinstance(value, dict):
                        continue
                    components = [value["component"]] if isinstance(value.get("component"), dict) else value.get("components", [])
                    if not isinstance(components, list):
                        continue
                    for component in components:
                        if not isinstance(component, dict) or not isinstance(component.get("measures"), list):
                            continue
                        distributions = [m.get("value") for m in component["measures"] if m.get("metric") == "ncloc_language_distribution"]
                        languages, errors = language_distribution(distributions[0] if len(distributions) == 1 else None)
                        payloads.append({"path": str(path), "sha256": file_sha256(path), "languages": languages,
                                         "component_key_hash": __import__("hashlib").sha256(str(component.get("key")).encode()).hexdigest(),
                                         "language_errors": errors, "status": "UNREGISTERED_RAW_PAYLOAD",
                                         "missing_admission": ["REGISTERED_LICENSE_AND_FAMILY", "COMPLETE_ANALYZER_DOMAIN",
                                                               "BOUND_STATE_SCOPE_INVENTORY_AND_COVERAGE"]})
            if considered > max_files:
                break
        if considered > max_files:
            break
    return {"schema_version": 2, "search_roots": sorted(set(map(str, roots))),
            "excluded_roots": list(map(str, excluded_roots)), "max_depth": max_depth,
            "max_files": max_files, "files_considered": min(considered, max_files), "bounded_search_truncated": truncated,
            "inaccessible_or_missing": sorted(inaccessible), "git_repositories": sorted(repos, key=lambda r: r["path"]),
            "raw_sonar_payloads": sorted(payloads, key=lambda r: r["path"]), "exposure_registries": registries,
            "strict_admitted_pilots": [], "status": "PARTIAL/BLOCKED_NONJAVA_DATA"}
