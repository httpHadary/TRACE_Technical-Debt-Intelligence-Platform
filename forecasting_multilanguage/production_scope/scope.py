"""Versioned source population. Git objects only; no checkout, build or scanner."""
from pathlib import PurePosixPath
from ..contracts import digest, revision, utc
from ..git_events import git

VERSION = "production-root-study-v1"
REPOSITORIES = {
    "apache/commons-cli": ("212343", "src/main", ("java",), "java_dominant"),
    "pallets/click": ("19103692", "src/click", ("py",), "python_dominant"),
    "adamchainz/django-browser-reload": ("438426152", "src/django_browser_reload", ("py", "js"), "mixed_python_jsts"),
}
EXCLUDED = ("test", "tests", "__tests__", "fixture", "fixtures", "doc", "docs", "example", "examples",
            "vendor", "vendored", "node_modules", "generated", "dist", "build", "__pycache__")
SUFFIXES = {".java": "java", ".py": "py", ".js": "js"}


def policy(repository_id):
    provider, root, languages, target = REPOSITORIES[repository_id]
    return dict(version=VERSION, repository_id=repository_id, provider_repository_id=provider,
                root=root, languages=list(languages), target=target,
                suffixes={k: v for k, v in SUFFIXES.items() if v in languages},
                excluded_components=list(EXCLUDED), excluded_names=["test_*", "*_test.py", "*.min.js", "*.map"],
                noncode_names=["py.typed"] if "py" in languages else ["overview.html", "package.html"],
                unknown="BLOCK", nonregular="BLOCK_INSIDE_ROOT", rename_policy="no-renames",
                content_review="required_bound_to_full_inventory_before_admission")


def scope_id(repository_id):
    return digest(policy(repository_id))


def path_parts(path):
    if (not isinstance(path, str) or not path or "\\" in path or "\0" in path
            or PurePosixPath(path).is_absolute() or any(p in ("", ".", "..") for p in path.split("/"))):
        raise ValueError("Canonical repository-relative POSIX path required")
    return PurePosixPath(path)


def classify(repository_id, path):
    p, pol = path_parts(path), policy(repository_id)
    if not path.startswith(pol["root"] + "/"):
        return "OUTSIDE_ROOT", None
    local = path[len(pol["root"]) + 1:]
    parts = local.split("/")
    name = parts[-1].lower()
    if (any(c.lower() in EXCLUDED for c in parts[:-1]) or name.startswith("test_")
            or name.endswith(("_test.py", ".min.js", ".map"))):
        return "EXCLUDED_POLICY", None
    if name in pol["noncode_names"]:
        return "NONCODE_EXPLICIT", None
    language = pol["suffixes"].get(p.suffix.lower())
    return ("PRODUCTION", language) if language else ("UNKNOWN_BLOCKING", None)


def inventory(lineage, repository_id, sha):
    if sha not in lineage.by_sha:
        raise ValueError("Revision outside registered first-parent lineage")
    rows = []
    for raw in git(lineage.path, "ls-tree", "-r", "-z", revision(sha)).split(b"\0"):
        if not raw:
            continue
        header, name = raw.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        path = name.decode("utf-8", errors="strict")
        role, language = classify(repository_id, path)
        if role != "OUTSIDE_ROOT" and (mode not in ("100644", "100755") or kind != "blob"):
            role, language = "NONREGULAR_BLOCKING", None
        rows.append(dict(path=path, mode=mode, object_type=kind, git_object_id=revision(oid), role=role, language=language))
    rows.sort(key=lambda r: r["path"])
    if len({r["path"] for r in rows}) != len(rows):
        raise ValueError("Duplicate Git path")
    production = [r for r in rows if r["role"] == "PRODUCTION"]
    blockers = [r["path"] for r in rows if r["role"].endswith("BLOCKING")]
    if not production:
        blockers.append("EMPTY_PRODUCTION_SCOPE")
    result = dict(version=VERSION, repository_id=repository_id, scope_id=scope_id(repository_id),
                  commit_sha=sha, source_tree_sha=lineage.by_sha[sha].tree,
                  entries=rows, production_paths=[r["path"] for r in production], blockers=blockers,
                  status="PASS_SOURCE_INVENTORY" if not blockers else "BLOCKED_SOURCE_INVENTORY")
    return dict(result, inventory_id=digest(result))


class ScopedGit:
    """Composition, not mutation of the frozen GitArchive; includes scoped event IDs."""
    def __init__(self, archive, repository_id):
        policy(repository_id)
        self.archive, self.repository_id = archive, repository_id
        self.path, self.tip, self.observed_at = archive.path, archive.tip, archive.observed_at
        self.commits, self.by_sha = archive.commits, archive.by_sha
        self.identity = digest([VERSION, archive.identity, scope_id(repository_id)])

    def state(self, cutoff):
        return self.archive.state(cutoff)

    def inventory(self, sha):
        return inventory(self.archive, self.repository_id, sha)

    def production_paths(self, sha):
        record = self.inventory(sha)
        if record["blockers"]:
            raise ValueError("Incomplete production inventory")
        return tuple(record["production_paths"])

    def events(self, start, cutoff):
        if utc(start) > utc(cutoff):
            raise ValueError("Window chronology")
        self.state(cutoff)
        output = []
        for c in self.commits:
            if not utc(start) < utc(c.timestamp) <= utc(cutoff):
                continue
            # Unknown production states anywhere in the feature window must not disappear.
            self.production_paths(c.sha)
            paths = [p for p in self.archive.paths(c) if classify(self.repository_id, p)[0] == "PRODUCTION"]
            output.append(dict(commit_sha=c.sha, state_utc=c.timestamp, available_utc=None,
                               paths=paths, event_id=digest([self.identity, c.sha])))
        return output
