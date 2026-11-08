"""Causal module definitions and conservative, evidence-based membership lineage."""
from collections import defaultdict
from dataclasses import dataclass
import posixpath

from contracts import digest
from .git import java_package, nearest_root

DESCRIPTORS = ("pom.xml", "build.gradle", "build.gradle.kts")


@dataclass
class ModuleDefinition:
    repository_id: str
    strategy: str
    package_base: str
    extra_depth: int
    first_commit: str
    scope: tuple

    @classmethod
    def create(cls, repo, snapshot, config):
        paths = sorted(snapshot.files)
        roots = {posixpath.dirname(p) for p in repo.tree(snapshot.commit)
                 if posixpath.basename(p) in DESCRIPTORS}
        actual = {nearest_root(p, roots) for p in paths
                  if nearest_root(p, roots) != "<root>" or "" in roots}
        strategy = config.strategy
        if strategy == "auto":
            strategy = "build" if len(actual) >= 2 else "package"
        packages = [java_package(repo.text(snapshot.commit, p)).split(".") for p in paths]
        common = []
        for parts in zip(*packages):
            if len(set(parts)) != 1:
                break
            common.append(parts[0])
        return cls(snapshot.repository_id, strategy, ".".join(common), config.package_extra_depth,
                   snapshot.commit, tuple(snapshot.scope))

    @property
    def config_id(self):
        return digest(self.__dict__)

    def groups(self, repo, commit, paths):
        roots = {posixpath.dirname(p) for p in repo.tree(commit)
                 if posixpath.basename(p) in DESCRIPTORS}
        groups, packages = defaultdict(set), {}
        base = self.package_base.split(".") if self.package_base else []
        for path in sorted(paths):
            package = packages[path] = java_package(repo.text(commit, path))
            if self.strategy == "build":
                name = nearest_root(path, roots)
            else:
                parts = package.split(".") if package else []
                if parts[:len(base)] == base:
                    parts = parts[:len(base) + self.extra_depth]
                name = ".".join(parts) or "(default-package)"
            groups[name].add(path)
        return dict(groups), packages


class IdentityTracker:
    def __init__(self, definition):
        self.definition = definition
        self.previous, self.previous_commit = {}, None
        self.previous_cutoff = None
        self.births = {}

    def update(self, repo, snapshot):
        groups, packages = self.definition.groups(repo, snapshot.commit, snapshot.files)
        renames = repo.rename_pairs(self.previous_commit, snapshot.commit) if self.previous_commit else {}
        old_to_new, new_to_old = defaultdict(set), defaultdict(set)
        transformed = {}
        for old, record in self.previous.items():
            transformed[old] = {renames.get(p, p) for p in record["paths"]}
            for new, paths in groups.items():
                if transformed[old] & paths:
                    old_to_new[old].add(new)
                    new_to_old[new].add(old)
        result, events = {}, []
        for name, paths in sorted(groups.items()):
            previous = self.previous.get(name)
            parents = new_to_old[name]
            status, inherited = "BIRTH", None
            if previous and transformed[name] & paths:
                inherited, status = previous, "CONTINUING"
                if transformed[name] != paths:
                    status = "MEMBERSHIP_CHANGED"
            elif len(parents) == 1:
                old = next(iter(parents))
                # Full one-to-one membership continuity is evidence for a rename. Partial
                # overlap, ambiguous splits and copies never silently inherit an identity.
                if old not in groups and old_to_new[old] == {name} and transformed[old] == paths:
                    inherited, status = self.previous[old], "RENAMED_MEMBERSHIP"
                    events.append({"event": "RENAME", "source": old, "target": name})
            if len(parents) > 1 and any(p not in groups for p in parents):
                status = "AMBIGUOUS_MERGE"
            elif any(len(old_to_new[p]) > 1 and any(n not in self.previous for n in old_to_new[p])
                     for p in parents):
                status = "AMBIGUOUS_SPLIT"
            elif previous and not transformed[name] & paths:
                status = "AMBIGUOUS_REPLACEMENT"
            if inherited is None:
                stable_id = digest([self.definition.config_id, name, snapshot.cutoff])
                birth = snapshot.cutoff
            else:
                stable_id, birth = inherited["stable_module_id"], inherited["birth_timestamp"]
            result[name] = {"stable_module_id": stable_id, "module_path": name,
                            "birth_timestamp": birth, "lineage_status": status, "paths": paths,
                            "left_censored": inherited["left_censored"] if inherited else self.previous_commit is None,
                            "historical_names": {**(inherited["historical_names"] if inherited else {}),
                                                 name: (inherited["historical_names"].get(name, self.previous_cutoff)
                                                        if inherited else self.previous_cutoff)},
                            "membership_hash": digest(sorted(paths)),
                            "parent_ids": sorted(self.previous[p]["stable_module_id"] for p in parents)}
            if status.startswith("AMBIGUOUS"):
                events.append({"event": status, "source": sorted(parents), "target": name})
            self.births.setdefault(stable_id, birth)
        continued_ids = {r["stable_module_id"] for r in result.values()}
        for old, record in sorted(self.previous.items()):
            if record["stable_module_id"] not in continued_ids:
                events.append({"event": "DELETION_OR_RESTRUCTURE", "source": old, "target": sorted(old_to_new[old]),
                               "stable_module_id": record["stable_module_id"]})
        for old, names in sorted(old_to_new.items()):
            for name in sorted(names):
                if name != old and old in groups and name in self.previous:
                    events.append({"event": "FILE_MOVEMENT", "source": old, "target": name})
        self.previous, self.previous_commit = result, snapshot.commit
        self.previous_cutoff = snapshot.cutoff
        return result, packages, events
