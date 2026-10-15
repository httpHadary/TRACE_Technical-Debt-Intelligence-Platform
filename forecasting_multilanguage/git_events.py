"""Read-only Git plumbing. Never checks out code, fetches objects or runs hooks."""
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
from .contracts import digest, iso, revision, utc
from .registry import source_language


class MissingGitObject(ValueError):
    pass


class OutsideRefEvidence(ValueError):
    pass


def git(path, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1",
               GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0", GIT_GRAFT_FILE=os.devnull)
    return subprocess.run(["git", "--literal-pathspecs", "-c", "core.fsmonitor=false", "-c", "diff.external=",
                           "-c", "diff.algorithm=myers", "-c", "diff.indentHeuristic=false", "-c", "log.showSignature=false",
                           "-C", str(path), *args], env=env, capture_output=True, check=True,
                          timeout=60).stdout


@dataclass(frozen=True)
class Commit:
    sha: str
    parents: tuple
    timestamp: str
    tree: str


class GitArchive:
    def __init__(self, path, tip_sha, ref_observed_at):
        self.path = Path(path)
        self.tip = revision(tip_sha)
        self.observed_at = iso(utc(ref_observed_at))
        if git(self.path, "rev-parse", "--is-shallow-repository").strip() != b"false":
            raise ValueError("Shallow boundary cannot prove complete windows")
        raw = git(self.path, "log", "--first-parent", "--reverse", "--format=%H%x09%P%x09%ct%x09%T", self.tip)
        self.commits = []
        for line in raw.decode().splitlines():
            sha, parents, seconds, tree = line.split("\t")
            commit = Commit(revision(sha), tuple(parents.split()),
                            iso(datetime.fromtimestamp(int(seconds), timezone.utc)), revision(tree))
            previous = self.commits[-1] if self.commits else None
            if (previous and (not commit.parents or commit.parents[0] != previous.sha
                              or utc(commit.timestamp) < utc(previous.timestamp))) or (not previous and commit.parents):
                raise ValueError("Incomplete ancestry or first-parent timestamp inversion")
            if utc(commit.timestamp) > utc(self.observed_at):
                raise ValueError("Ref observation precedes included revision")
            self.commits.append(commit)
        if not self.commits or self.commits[-1].sha != self.tip:
            raise ValueError("Tip identity mismatch")
        self.by_sha = {c.sha: c for c in self.commits}
        self.identity = digest({"tip": self.tip, "ref_observed_at": self.observed_at,
                                "commits": [c.__dict__ for c in self.commits]})

    def state(self, cutoff):
        stamp = utc(cutoff)
        if stamp > utc(self.observed_at):
            raise OutsideRefEvidence("Cutoff outside ref evidence")
        states = [c for c in self.commits if utc(c.timestamp) <= stamp]
        return states[-1] if states else None

    def paths(self, commit):
        args = (["diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--name-only", "-z", commit.parents[0], commit.sha]
                if commit.parents else ["diff-tree", "--root", "--no-commit-id", "--no-renames", "--name-only", "-r", "-z", commit.sha])
        return tuple(p.decode("utf-8", errors="strict") for p in git(self.path, *args).split(b"\0") if p)

    def production_paths(self, sha):
        paths = git(self.path, "ls-tree", "-r", "--name-only", "-z", revision(sha)).split(b"\0")
        return tuple(sorted(p.decode() for p in paths if p and source_language(p.decode())))

    def events(self, start, cutoff):
        if utc(start) > utc(cutoff):
            raise ValueError("Window chronology")
        self.state(cutoff)
        return [dict(commit_sha=c.sha, state_utc=c.timestamp, available_utc=None,
                     paths=[p for p in self.paths(c) if source_language(p)],
                     event_id=digest([self.identity, c.sha]))
                for c in self.commits if utc(start) < utc(c.timestamp) <= utc(cutoff)]


def first_parent_numstat(path, sha, filename):
    """Authoritative no-renames first-parent diff; root uses Git's empty tree."""
    revision(sha)
    try:
        raw = git(path, "show", "-s", "--format=%P", sha)
        parents = raw.decode().strip().split()
        args = (["diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--numstat", "-z", parents[0], sha, "--", filename]
                if parents else ["diff-tree", "--root", "--no-commit-id", "--no-renames", "--numstat", "-r", "-z", sha, "--", filename])
        output = git(path, *args)
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode(errors="replace").lower()
        if any(s in message for s in ("bad object", "bad revision", "not a valid object", "unable to read tree", "could not read")):
            raise MissingGitObject("Commit/first-parent objects unavailable") from exc
        raise
    rows = [v.split(b"\t", 2) for v in output.split(b"\0") if v]
    matched = [v for v in rows if len(v) == 3 and v[2].decode() == filename]
    if not matched:
        return {"status": "NO_CHANGE", "added": 0, "removed": 0, "raw_sha256": digest(output.hex())}
    if len(matched) != 1:
        raise ValueError("Unexpected numstat identity")
    added, removed, _ = matched[0]
    if added == b"-" or removed == b"-":
        return {"status": "BINARY", "added": None, "removed": None, "raw_sha256": digest(output.hex())}
    return {"status": "OBSERVED", "added": int(added), "removed": int(removed), "raw_sha256": digest(output.hex())}


def legacy_path_proof(path, sha, legacy_filename):
    """V2 FILE may be a basename, not a repository-relative path.

    Compare against the full authoritative diff. Multiple matching paths remain
    ambiguous even when one raw numeric pair happens to match. Never repair by sum.
    """
    revision(sha)
    try:
        parents = git(path, "show", "-s", "--format=%P", sha).decode().strip().split()
        args = (["diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--numstat", "-z", parents[0], sha]
                if parents else ["diff-tree", "--root", "--no-commit-id", "--no-renames", "--numstat", "-r", "-z", sha])
        raw = git(path, *args)
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode(errors="replace").lower()
        if any(s in message for s in ("bad object", "bad revision", "not a valid object", "unable to read tree", "could not read")):
            raise MissingGitObject("Commit/first-parent objects unavailable") from exc
        raise
    matches = []
    for row in raw.split(b"\0"):
        if not row:
            continue
        added, removed, filename = row.split(b"\t", 2)
        filename = filename.decode()
        if filename == legacy_filename or ("/" not in legacy_filename and Path(filename).name == legacy_filename):
            matches.append({"path": filename, "added": None if added == b"-" else int(added),
                            "removed": None if removed == b"-" else int(removed)})
    return {"resolution": "AMBIGUOUS_BASENAME" if len(matches) > 1 else "UNIQUE_PATH" if matches else "NO_MATCHING_PATH",
            "first_parent_sha": parents[0] if parents else None, "matches": sorted(matches, key=lambda r: r["path"]),
            "raw_diff_sha256": __import__("hashlib").sha256(raw).hexdigest()}
