"""Read immutable Git objects, never checkout or fetch a repository."""
import posixpath
import re
import subprocess

from contracts import source_path
from .schema import timestamp


class GitRepository:
    def __init__(self, path, scope=()):
        self.path, self.scope = str(path), tuple(scope)
        self._trees, self._blobs, self._events = {}, {}, {}
        if self.run("rev-parse", "--is-shallow-repository").strip() != "false":
            raise ValueError("Complete Git history required")

    def run(self, *args, binary=False):
        r = subprocess.run(["git", "-C", self.path, *args], capture_output=True, check=True)
        return r.stdout if binary else r.stdout.decode("utf-8", errors="strict")

    def resolve(self, branch, cutoff):
        return self.run("rev-list", "--first-parent", "-1", f"--before={cutoff}", branch).strip()

    def tree(self, commit):
        if commit not in self._trees:
            tree = {}
            for row in self.run("ls-tree", "-r", "-z", commit).split("\0"):
                if row:
                    info, path = row.split("\t", 1)
                    mode, kind, blob = info.split()
                    if kind == "blob":
                        tree[source_path(path)] = blob
            self._trees[commit] = tree
        return self._trees[commit]

    def text(self, commit, path):
        blob = self.tree(commit)[path]
        if blob not in self._blobs:
            self._blobs[blob] = self.run("cat-file", "blob", blob)
        return self._blobs[blob]

    def production(self, path):
        source_path(path)
        if not path.endswith(".java"):
            return False
        for root in ("src/main/java/", "src/java/", *self.scope):
            i = path.find(root)
            if i >= 0 and (i == 0 or path[i - 1] == "/"):
                return not set(path[:i].strip("/").split("/")) & {
                    "target", "build", "generated", "generated-sources", "vendor", "tests", "test"}
        return False

    def events(self, commit, cutoff, days=182):
        # Walking ONLY this commit's ancestry excludes later-merged backdated commits.
        if commit not in self._events:
            events = []
            current = None
            output = self.run("log", commit, "--no-merges", "--format=COMMIT|%H|%cI|%ae",
                              "--numstat", "-z", "--no-renames")
            for part in output.split("\0"):
                part = part.lstrip("\n")
                if part.startswith("COMMIT|"):
                    _, sha, date, author = part.split("|", 3)
                    current = (sha, date, author.rstrip("\n"))
                    continue
                fields = part.split("\t", 2)
                if current and len(fields) == 3:
                    added, deleted, path = fields
                    events.append((*current, source_path(path),
                                   None if added == "-" else int(added),
                                   None if deleted == "-" else int(deleted)))
            self._events[commit] = events
        end = timestamp(cutoff)
        from datetime import timedelta
        return [e for e in self._events[commit] if end - timedelta(days=days) < timestamp(e[1]) <= end]

    def rename_pairs(self, previous, current):
        parts = self.run("diff", "--name-status", "-z", "--find-renames=100%", previous, current).split("\0")
        result, i = {}, 0
        while i < len(parts) and parts[i]:
            status = parts[i]
            if status.startswith(("R", "C")):
                old, new = parts[i + 1:i + 3]
                if status == "R100":
                    result[old] = new
                i += 3
            else:
                i += 2
        return result


def java_text(text):
    # Mask comments and literals: fake imports/packages inside strings are not dependencies.
    return re.sub(r'/\*.*?\*/|//[^\n]*|""".*?"""|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                  lambda m: "\n" * m.group().count("\n") + " ", text, flags=re.S)


def java_package(text):
    m = re.search(r"\bpackage\s+([\w.]+)\s*;", java_text(text))
    return m.group(1) if m else ""


def nearest_root(path, roots):
    directory = posixpath.dirname(path)
    while directory:
        if directory in roots:
            return directory
        directory = posixpath.dirname(directory)
    return "<root>"
