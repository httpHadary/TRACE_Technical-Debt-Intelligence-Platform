"""Historical directed dependencies and evolutionary/organizational coupling."""
from collections import Counter, defaultdict
from itertools import combinations
import posixpath
import re
import xml.etree.ElementTree as ET

import networkx as nx

from .git import java_text, nearest_root
from .identity import DESCRIPTORS
from .schema import GRAPH_FEATURES, timestamp


def extract_graph(repo, snapshot, identities, packages, definition, history_days=182):
    path_modules = {p: name for name, rec in identities.items() for p in rec["paths"]}
    weights, unresolved = Counter(), []
    coverage = {name: {"parsed_files": 0, "total_files": len(rec["paths"]),
                       "imports": 0, "unresolved_imports": 0, "build_total": 0,
                       "build_parsed": 0, "unresolved_build_dependencies": 0}
                for name, rec in identities.items()}
    class_modules, package_modules = defaultdict(set), defaultdict(set)
    tree = repo.tree(snapshot.commit)
    # Source imports are an approximation, never a claim of complete call-graph coverage.
    for path, name in path_modules.items():
        package = packages[path]
        package_modules[package].add(name)
        text = java_text(repo.text(snapshot.commit, path))
        coverage[name]["parsed_files"] += 1
        classes = re.findall(r"\b(?:class|interface|enum|record)\s+(\w+)", text)
        for cls in classes:
            class_modules[(package + "." if package else "") + cls].add(name)
    for path, name in sorted(path_modules.items()):
        text = java_text(repo.text(snapshot.commit, path))
        for static, imported in re.findall(r"\bimport\s+(static\s+)?([\w.*]+)\s*;", text):
            coverage[name]["imports"] += 1
            candidates = set()
            if imported.endswith(".*"):
                candidates = (class_modules.get(imported[:-2], set()) if static else
                              package_modules.get(imported[:-2], set()))
            else:
                prefix = imported
                while prefix and not candidates:
                    candidates = class_modules.get(prefix, set())
                    prefix = prefix.rpartition(".")[0]
            if not candidates:
                coverage[name]["unresolved_imports"] += 1
                unresolved.append({"module": name, "kind": "import", "path": path, "reference": imported,
                                   "reason": "external_or_unresolved"})
            for other in sorted(candidates - {name}):
                weights[(name, other, "source_dependency")] += 1
    descriptors, artifacts = {}, defaultdict(set)
    for path in sorted(tree):
        if posixpath.basename(path) not in DESCRIPTORS:
            continue
        root = posixpath.dirname(path) or "<root>"
        owners = ({root} & set(identities) if definition.strategy == "build" else
                  {name for p, name in path_modules.items() if nearest_root(p, {posixpath.dirname(path)}) == root})
        if not owners:
            continue
        for owner in owners:
            coverage[owner]["build_total"] += 1
        text = repo.text(snapshot.commit, path)
        dependencies = []
        parsed = True
        if path.endswith("pom.xml"):
            try:
                project = ET.fromstring(text)
                # Remove namespaces; only direct dependency declarations, no dependencyManagement.
                for item in project.iter():
                    item.tag = item.tag.rsplit("}", 1)[-1]
                aid = project.findtext("artifactId")
                gid = project.findtext("groupId") or project.findtext("parent/groupId")
                if aid:
                    artifacts[(gid or "", aid)].update(owners)
                for dep in project.findall("dependencies/dependency"):
                    dependencies.append((dep.findtext("groupId") or "", dep.findtext("artifactId") or ""))
            except ET.ParseError:
                parsed = False
                for owner in owners:
                    unresolved.append({"module": owner, "kind": "build_extraction", "path": path,
                                       "reference": path, "reason": "malformed_xml"})
        else:
            # Only literal project dependencies are resolvable without executing Gradle.
            dependencies = [("gradle", value) for value in
                            re.findall(r"\bproject\s*\(\s*(?:path\s*[:=]\s*)?['\"](:[^'\"]+)['\"]\s*\)", text)]
            parsed = False  # Groovy/Kotlin scripts may compute unobserved dependencies.
            for owner in owners:
                unresolved.append({"module": owner, "kind": "build_extraction", "path": path,
                                   "reference": path, "reason": "dynamic_build_not_executed"})
        descriptors[path] = (owners, dependencies)
        for owner in owners:
            coverage[owner]["build_parsed"] += int(parsed)
    for path, (owners, dependencies) in sorted(descriptors.items()):
        for group, artifact in dependencies:
            targets = ({artifact.lstrip(":").replace(":", "/")} & set(identities)
                       if group == "gradle" else artifacts.get((group, artifact), set()))
            for owner in owners:
                if not targets:
                    coverage[owner]["unresolved_build_dependencies"] += 1
                    unresolved.append({"module": owner, "kind": "build", "path": path,
                                       "reference": f"{group}:{artifact}", "reason": "external_or_unresolved"})
                for target in sorted(targets - {owner}):
                    weights[(owner, target, "build_dependency")] += 1
    changes, contributors, activity = defaultdict(set), defaultdict(set), defaultdict(list)
    events = repo.events(snapshot.commit, snapshot.cutoff, history_days)
    history_mappings = {}
    aliases = defaultdict(list)
    for name, record in identities.items():
        for historic_name, start in record["historical_names"].items():
            aliases[historic_name].append((name, start))
    for commit, date, author, path, added, deleted in events:
        if not repo.production(path):
            continue
        # Map at the event commit, not at a future snapshot. Deleted paths use its parent.
        if commit not in history_mappings:
            history_mappings[commit] = definition.groups(repo, commit,
                [p for p in repo.tree(commit) if repo.production(p)])[0]
        name = next((m for m, paths in history_mappings[commit].items() if path in paths), None)
        if name is None:
            parent = repo.run("rev-parse", f"{commit}^").strip()
            if parent not in history_mappings:
                history_mappings[parent] = definition.groups(repo, parent,
                    [p for p in repo.tree(parent) if repo.production(p)])[0]
            name = next((m for m, paths in history_mappings[parent].items() if path in paths), None)
        matches = [(current_name, start) for current_name, start in aliases.get(name, [])
                   if start is None or timestamp(date) > timestamp(start)]
        if len(matches) == 1:
            name = matches[0][0]
            if added is None or deleted is None:
                raise ValueError("Unmeasurable production Java churn")
            changes[commit].add(name)
            contributors[name].add(author)
            activity[name].append((commit, author, added + deleted))
    for names in changes.values():
        for a, b in combinations(sorted(names), 2):
            weights[(a, b, "cochange")] += 1
    for a, b in combinations(sorted(identities), 2):
        overlap = contributors[a] & contributors[b]
        if overlap:
            weights[(a, b, "contributor")] = len(overlap) / len(contributors[a] | contributors[b])
    dependency = nx.DiGraph()
    dependency.add_nodes_from(identities)
    dependency.add_edges_from((a, b) for a, b, kind in weights if kind.endswith("dependency"))
    cyclic = set()
    for component in nx.strongly_connected_components(dependency):
        if len(component) > 1:
            cyclic.update(component)
    centrality = nx.pagerank(dependency, alpha=0.85, tol=1e-10, max_iter=500) if identities else {}
    statistics = {}
    for name, rec in sorted(identities.items()):
        c = coverage[name]
        stats = {key: 0.0 for key in GRAPH_FEATURES}
        stats.update(dependency_in_degree=dependency.in_degree(name), dependency_out_degree=dependency.out_degree(name),
                     dependency_coupling=len(set(dependency.predecessors(name)) | set(dependency.successors(name))) /
                                         max(1, len(identities) - 1),
                     dependency_cycle=int(name in cyclic), dependency_pagerank=centrality[name],
                     source_coverage=c["parsed_files"] / max(1, c["total_files"]),
                     unresolved_imports=c["unresolved_imports"],
                     unresolved_build_dependencies=c["unresolved_build_dependencies"],
                     dependency_available=1, history_graph_available=1,
                     build_coverage=c["build_parsed"] / c["build_total"] if c["build_total"] else None)
        for kind in ("cochange", "contributor"):
            neighbors = [(a if b == name else b, w) for (a, b, k), w in weights.items()
                         if k == kind and name in (a, b)]
            stats[kind + "_degree"] = len(neighbors)
            stats[kind + "_weight"] = sum(w for _, w in neighbors)
        statistics[name] = {**stats, **c, "graph_status": ("PARTIAL_BUILD_SOURCE_APPROXIMATION"
                            if c["build_parsed"] < c["build_total"] else "OBSERVED_SOURCE_APPROXIMATION"),
                            "commits_26w": len({e[0] for e in activity[name]}),
                            "authors_26w": len({e[1] for e in activity[name]}),
                            "churn_26w": sum(e[2] for e in activity[name])}
    edges = [{"source": identities[a]["stable_module_id"], "target": identities[b]["stable_module_id"],
              "edge_type": kind, "weight": weight, "directed": int(kind.endswith("dependency"))}
             for (a, b, kind), weight in sorted(weights.items())]
    return edges, statistics, unresolved
