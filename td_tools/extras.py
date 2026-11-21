"""
extras.py - extra metrics for every snapshot, at FILE, MODULE and PROJECT level:

  1. Halstead (from the source code of that commit)
       n1, n2, N1, N2, vocabulary, length, volume, difficulty, effort
  2. Git activity (commits between the previous snapshot and this one)
       commit_count, lines_added, lines_deleted, code_churn,
       files_changed, contributors_count, window_days

Used by td_pipeline.py inside the weekly loop, and by add_extras.py to add these
metrics to runs that are already finished (no SonarQube or build needed).

Halstead counting policy (same as your script, with one fix):
  operators = Java operators + ALL keywords (incl. modifiers like public/static
              and basic types like int/boolean - javalang gives those their own
              token classes, so we test with isinstance, not the class name)
  operands  = identifiers + all literals (numbers, strings, chars, true/false, null)
  separators ( ) { } ; , . and annotations '@' are not counted.
Module and project values use the UNION of distinct operators/operands
(distinct counts cannot be summed); halstead_volume_sum = sum of file volumes.
Only main code (src/main/java) is counted, same scope as SonarQube's ncloc.
"""
import math, subprocess
from collections import defaultdict

import javalang
from javalang import tokenizer as T


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True,
                          text=True, errors="replace").stdout


# Main-code source roots. Old Apache projects (commons-io before ~2010) use src/java.
MAIN_ROOTS = ("/src/main/java/", "/src/java/")


def module_and_rel(path):
    path = path.replace("\\", "/")
    module = path.split("/src/")[0] if "/src/" in path else "."
    rel = path
    for root in MAIN_ROOTS:              # src/main/java (Maven 2+) or src/java (old Apache layout)
        if root in "/" + path:
            rel = ("/" + path).split(root, 1)[1]
            break
    return module, rel


def is_main_java(path):
    return path.endswith(".java") and any(r in "/" + path for r in MAIN_ROOTS)


# ------------------------------------------------------------------ Halstead
def tokens_of(source):
    ops, opnds = [], []
    for tok in T.tokenize(source):
        if isinstance(tok, T.Operator) or isinstance(tok, T.Keyword):
            ops.append(tok.value)
        elif isinstance(tok, T.Identifier) or isinstance(tok, T.Literal):
            opnds.append(tok.value)
    return ops, opnds


def halstead(n1, n2, N1, N2):
    vocab, length = n1 + n2, N1 + N2
    volume = length * math.log2(vocab) if vocab > 1 else 0.0
    difficulty = (n1 / 2) * (N2 / n2) if n2 else 0.0
    return {"n1": n1, "n2": n2, "N1": N1, "N2": N2,
            "halstead_vocabulary": vocab, "halstead_length": length,
            "halstead_volume": round(volume, 3),
            "halstead_difficulty": round(difficulty, 3),
            "halstead_effort": round(difficulty * volume, 3)}


def read_blobs(repo, sha, paths):
    if not paths:
        return {}
    inp = "".join(f"{sha}:{p}\n" for p in paths).encode()
    out = subprocess.run(["git", "-C", repo, "cat-file", "--batch"], input=inp,
                         capture_output=True).stdout
    res, pos = {}, 0
    for p in paths:
        nl = out.index(b"\n", pos)
        head = out[pos:nl].split()
        if len(head) < 3 or head[1] == b"missing":
            pos = nl + 1
            continue
        size = int(head[2])
        res[p] = out[nl + 1: nl + 1 + size].decode("utf-8", "replace")
        pos = nl + 1 + size + 1
    return res


def halstead_snapshot(repo, sha, base):
    """returns (file_rows, module_rows, project_row) for one commit"""
    files = [f for f in git(repo, "ls-tree", "-r", "--name-only", sha).splitlines()
             if is_main_java(f)]
    blobs = read_blobs(repo, sha, files)
    frows, skipped = [], 0
    mod_ops, mod_opnds = defaultdict(set), defaultdict(set)
    mod_N, mod_vol, mod_files = defaultdict(lambda: [0, 0]), defaultdict(float), defaultdict(int)
    all_ops, all_opnds, P = set(), set(), [0, 0]
    vol_sum = 0.0
    for path, src in blobs.items():
        try:
            ops, opnds = tokens_of(src)
        except Exception:
            skipped += 1
            continue
        m, rel = module_and_rel(path)
        h = halstead(len(set(ops)), len(set(opnds)), len(ops), len(opnds))
        frows.append({**base, "module": m, "file": rel, **h})
        mod_ops[m] |= set(ops); mod_opnds[m] |= set(opnds)
        mod_N[m][0] += len(ops); mod_N[m][1] += len(opnds)
        mod_vol[m] += h["halstead_volume"]; mod_files[m] += 1
        all_ops |= set(ops); all_opnds |= set(opnds)
        P[0] += len(ops); P[1] += len(opnds); vol_sum += h["halstead_volume"]
    mrows = [{**base, "module": m, **halstead(len(mod_ops[m]), len(mod_opnds[m]), *mod_N[m]),
              "halstead_volume_sum": round(mod_vol[m], 3), "halstead_files": mod_files[m]}
             for m in mod_ops]
    prow = {**base, **halstead(len(all_ops), len(all_opnds), *P),
            "halstead_volume_sum": round(vol_sum, 3), "halstead_files": len(frows),
            "halstead_skipped_files": skipped}
    return frows, mrows, prow


# ------------------------------------------------------------------ Git activity
def git_activity(repo, prev_sha, sha, base, modules):
    """Commits in prev_sha..sha (no merges). First snapshot: the 7 days before it."""
    t_now = int(git(repo, "show", "-s", "--format=%ct", sha).strip() or 0)
    if prev_sha and prev_sha != sha:
        rng = [f"{prev_sha}..{sha}"]
        t_prev = int(git(repo, "show", "-s", "--format=%ct", prev_sha).strip() or t_now)
    elif prev_sha == sha:
        rng, t_prev = None, t_now
    else:
        rng, t_prev = [f"--since=@{t_now - 7 * 86400}", sha], t_now - 7 * 86400
    window_days = round((t_now - t_prev) / 86400, 2)

    mods = sorted((m for m in modules if m != "."), key=len, reverse=True)

    def module_for(path):
        if is_main_java(path):
            m = module_and_rel(path)[0]
            if m in modules:
                return m
            # Java file of a module that is not in this snapshot (e.g. deleted in this window)
            return "(project)"
        for m in mods:
            if path.startswith(m + "/"):
                return m
        # root pom.xml, README, website, ... belong to no Java module
        return "." if "." in modules else "(project)"

    F = defaultdict(lambda: {"commits": set(), "added": 0, "deleted": 0, "authors": set()})
    M = defaultdict(lambda: {"commits": set(), "added": 0, "deleted": 0, "authors": set(), "files": set()})
    Pj = {"commits": set(), "added": 0, "deleted": 0, "authors": set(), "files": set()}
    if rng:
        out = git(repo, "log", "--no-merges", "--no-renames", "--numstat",
                  "--format=@@%H\t%ae", *rng)
        cur, author = None, None
        for line in out.splitlines():
            if line.startswith("@@"):
                cur, author = line[2:].split("\t", 1)
                Pj["commits"].add(cur); Pj["authors"].add(author)
                continue
            parts = line.split("\t", 2)
            if len(parts) != 3 or cur is None:
                continue
            a, d, path = parts
            a = int(a) if a.isdigit() else 0
            d = int(d) if d.isdigit() else 0
            Pj["added"] += a; Pj["deleted"] += d; Pj["files"].add(path)
            m = module_for(path)
            M[m]["commits"].add(cur); M[m]["authors"].add(author)
            M[m]["added"] += a; M[m]["deleted"] += d; M[m]["files"].add(path)
            if is_main_java(path):
                fm, rel = module_and_rel(path)
                f = F[(fm, rel)]
                f["commits"].add(cur); f["authors"].add(author)
                f["added"] += a; f["deleted"] += d

    def row(r, files=None):
        out = {"commit_count": len(r["commits"]), "lines_added": r["added"],
               "lines_deleted": r["deleted"], "code_churn": r["added"] + r["deleted"],
               "contributors_count": len(r["authors"]), "window_days": window_days}
        if files is not None:
            out["files_changed"] = len(files)
        return out

    frows = [{**base, "module": m, "file": rel, **row(v)} for (m, rel), v in F.items()]
    mrows = [{**base, "module": m, **row(v, v["files"])} for m, v in M.items()]
    prow = {**base, **row(Pj, Pj["files"])}
    return frows, mrows, prow


H_COLS = ["n1", "n2", "N1", "N2", "halstead_vocabulary", "halstead_length", "halstead_volume",
          "halstead_difficulty", "halstead_effort"]
G_COLS = ["commit_count", "lines_added", "lines_deleted", "code_churn", "contributors_count",
          "window_days"]
