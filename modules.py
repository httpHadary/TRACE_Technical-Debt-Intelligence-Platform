"""
Module resolution: which module does a file belong to?

Two strategies (see config.MODULE_STRATEGY):
  build    nearest ancestor directory with pom.xml / build.gradle(.kts)
  package  Java package, truncated to <common base package> + MODULE_PACKAGE_EXTRA_DEPTH levels

The strategy (and, for "package", the base package) is decided once and frozen in
module_strategy.json inside the repo's working directory.
"""
import json
import posixpath
import subprocess
from pathlib import Path

import config
import re
from contracts import source_path, digest, read_json, write_json

STRATEGY_FILE = Path("module_strategy.json")
_SRC_ROOT_MARKERS = ("src/main/java/", "src/java/", "src/main/kotlin/")


def is_production_file(file_path):
    """.java outside test/generated/build/vendor/example/sample/benchmark/template paths
    (same rule as build_td_mart.is_production_file)."""
    source_path(file_path)
    if not file_path.endswith('.java'):
        return False
    # Package segments named test/build/sample are ordinary production packages.
    # Exclusions apply to source roots and their ancestors, not Java namespaces.
    for marker in (*_SRC_ROOT_MARKERS[:2], *config.EXTRA_PRODUCTION_ROOTS):
        index = file_path.find(marker)
        if index < 0 or index and file_path[index - 1] != '/':
            continue
        ancestors = set(file_path[:index].strip('/').split('/'))
        return not ancestors & {'target', 'build', 'generated', 'generated-sources', 'vendor', 'tests', 'test'}
    return False


def _git(repo_path, args):
    r = subprocess.run(["git", "-C", str(repo_path), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="strict")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def list_files(repo_path, commit):
    return [source_path(p) for p in _git(repo_path, ["ls-tree", "-r", "--name-only", '-z', commit]).split('\0') if p]


def build_dirs_of(files):
    """Set of directories ('' = repo root) that contain a build descriptor."""
    return {posixpath.dirname(f) for f in files if posixpath.basename(f) in config.BUILD_DESCRIPTORS}


def nearest_build_dir(path, build_dirs):
    d = posixpath.dirname(path)
    while True:
        if d in build_dirs:
            return d
        if not d:
            return None
        d = posixpath.dirname(d)


def package_of(path):
    """'a/src/main/java/org/x/y/F.java' -> 'org.x.y'; no recognised source root -> directory with dots."""
    for marker in _SRC_ROOT_MARKERS:
        i = path.find(marker)
        if i != -1 and (i == 0 or path[i - 1] == "/"):
            rest = path[i + len(marker):]
            break
    else:
        rest = path
    return posixpath.dirname(rest).replace("/", ".")


def _common_prefix(lists):
    if not lists:
        return []
    first = min(lists)
    last = max(lists)
    out = []
    for a, b in zip(first, last):
        if a != b:
            break
        out.append(a)
    return out


def detect_strategy(repo_path, commit):
    """Decide from the earliest observation; later structure cannot redefine history."""
    files = list_files(repo_path, commit)
    prod = [f for f in files if is_production_file(f)]
    bdirs = build_dirs_of(files)
    build_modules = {nearest_build_dir(f, bdirs) for f in prod} - {None}
    requested = config.MODULE_STRATEGY
    strategy = requested
    if requested == "auto":
        strategy = "build" if len(build_modules) >= 2 else "package"
    if strategy not in ('build', 'package') or config.MODULE_PACKAGE_EXTRA_DEPTH < 0:
        raise ValueError('Invalid module configuration')
    decision = {"strategy": strategy, "requested": requested, "decided_at_commit": commit,
                'repository_id': config.REPOSITORY_ID, 'build_roots': sorted(bdirs),
                'scope': list(config.EXTRA_PRODUCTION_ROOTS),
                "extra_depth": config.MODULE_PACKAGE_EXTRA_DEPTH, "package_base": ""}
    if strategy == "package":
        pkgs = [declared_package(repo_path, commit, f).split('.') for f in prod]
        decision["package_base"] = ".".join(_common_prefix(pkgs))
    decision['mapping_id'] = digest(decision)
    return decision


def load_or_decide_strategy(repo_path, commit):
    if STRATEGY_FILE.exists():
        saved = read_json(STRATEGY_FILE)
        expected = detect_strategy(repo_path, commit)
        if saved != expected:
            raise ValueError('Module definition differs from frozen first observation; use a fresh workspace')
        return saved
    decision = detect_strategy(repo_path, commit)
    write_json(STRATEGY_FILE, decision)
    print(f">>> Module strategy frozen in {STRATEGY_FILE}: {decision['strategy']}"
          + (f" (base package '{decision['package_base']}')" if decision["strategy"] == "package" else ""))
    return decision


class ModuleMapper:
    """file path -> module id, for one commit."""

    def __init__(self, decision, build_dirs=None, packages=None, repo=None):
        self.strategy = decision["strategy"]
        self.build_dirs = build_dirs or set()
        self.base = [p for p in decision.get("package_base", "").split(".") if p]
        self.extra = int(decision.get("extra_depth", 1))
        self._cache = {}
        self.packages = packages
        self.repo = repo

    def module_of(self, path, source_commit=None):
        key = (path, source_commit)
        m = self._cache.get(key)
        if m is None:
            m = self._cache[key] = self._resolve(path, source_commit)
        return m

    def _resolve(self, path, source_commit=None):
        source_path(path)
        if self.strategy == "build":
            d = nearest_build_dir(path, self.build_dirs)
            return config.ROOT_MODULE_LABEL if d in (None, "") else d
        package = self.packages.get(path, package_of(path)) if self.packages is not None else package_of(path)
        if self.packages is not None and path not in self.packages and self.repo is not None:
            if not source_commit:
                raise ValueError('No source identity for module mapping')
            # Deleted files are absent from the weekly tree. Use their actual historical
            # package, never the directory name as a replacement for source evidence.
            tree = source_commit
            if path not in list_files(self.repo, tree):
                tree = _git(self.repo, ['rev-parse', f'{tree}^']).strip()
            package = declared_package(self.repo, tree, path)
        parts = [p for p in package.split('.') if p]
        if not parts:
            return "(default-package)"
        if parts[:len(self.base)] == self.base:
            parts = parts[:len(self.base) + self.extra]
        return ".".join(parts)


def mapper_for_commit(repo_path, commit, decision, _cache={}):
    key = (str(Path(repo_path).resolve()), commit, digest(decision))
    if key not in _cache:
        bdirs = set(decision['build_roots']) if decision['strategy'] == 'build' else None
        packages = ({p: declared_package(repo_path, commit, p) for p in list_files(repo_path, commit)
                     if is_production_file(p)} if decision['strategy'] == 'package' else None)
        _cache[key] = ModuleMapper(decision, bdirs, packages, repo_path)
    return _cache[key]


def declared_package(repo_path, commit, path):
    text = _git(repo_path, ['show', f'{commit}:{source_path(path)}'])
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    match = re.search(r'^\s*package\s+([\w.]+)\s*;', text, flags=re.M)
    return match.group(1) if match else ''
