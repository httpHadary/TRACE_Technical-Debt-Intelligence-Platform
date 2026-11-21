"""
history.py - history and extra features for every snapshot, at PROJECT, MODULE and FILE level.

Runs AFTER td_pipeline.py (or on any finished run). Needs no SonarQube and no build:
it reads the run's raw tables + the git history of the clone, and writes
    raw_hist_project.csv / raw_hist_module.csv / raw_hist_file.csv
which td_pipeline.join_levels() merges into project_level.csv / module_level.csv / file_level.csv.

    python history.py --repo ~/td-work/square_retrofit --out ~/td-out/retrofit_final

TIME RULES (no look-ahead):
  * T0 of a row = committer time of the commit analysed for that week (not the week label).
  * Day windows  "_21d/_30d/_90d/_180d" use REAL time: (T0 - N days, T0].
    SonarQube-based changes compare T0 with the latest snapshot at or before T0 - N days
    ("as of"); slopes use all snapshots from that as-of point up to T0. If no snapshot is that
    old, the value is empty (history not available) - never guessed.
  * Week windows "_1w/_3w/_4w/_12w" count WEEKLY SNAPSHOTS (rows), like the paper's sliding
    window (t-1, t-2, ...). A lag over a failed week is empty.
  * Targets (target_td_*) are the ONLY columns that read the future. Never use them as inputs.

DEFINITIONS (all levels unless noted)
  technical_debt_minutes_t0  = total_principal (alias, not duplicated)
  td_{3,4,12}w_lag           = total_principal 3/4/12 weekly snapshots earlier
  td_change_{1,3,4,12}w      = total_principal(t0) - total_principal(lag)
  td_slope_{4,12}w           = OLS slope of the last 4/12 weekly values (minutes per week); needs all points
  td_volatility_4w           = population std of the last 4 weekly values
  td_growth_rate_4w          = td_change_4w / td_4w_lag (0 if both are 0; empty if 0 -> >0 or lag unknown)
  finding_density_t0         = 1000 x violations / ncloc        (finding_count_t0 = sonar violations)
  development_cost_t0        = 30 min x ncloc  (SonarQube's default cost per line)
  fn_* (function complexity distribution, from parsing the source with javalang):
       fn_count, fn_complexity_max, fn_complexity_mean,
       fn_complexity_dist_{1,2,4,6,8,10,12}: methods with complexity in SonarQube's buckets
       [1,2) [2,4) [4,6) [6,8) [8,10) [10,12) [12,+)
       method complexity = 1 + if/for/while/do/case/catch/?:/&&/|| inside the method body
  git_commits_{N}d, git_lines_churned_{N}d  (main Java files; module/project = their files;
       commits are DISTINCT commits, churn is summed)
  churn_slope_{N}d           = OLS slope of churn in equal sub-windows of the N days (per week)
  git_commit_acceleration    = commits in last 7 days - commits in the 7 days before
  git_churn_acceleration     = same for churned lines
  commit_burstiness_180d, churn_burstiness_180d = variance/mean of 26 sub-window counts
  major_author_commits       = commits by the most active author, all history <= T0
  knowledge_fragmentation_180d = Shannon entropy (bits) of authors' commit shares, last 180 days
  complexity_slope_{N}d      = slope of complexity per 1,000 lines (per week)
  duplication_change_{N}d    = change in duplicated-lines density (%)
  cognitive_complexity_change_{N}d, ncloc_change_{N}d, violations_change_{N}d
  debt_density_change_{N}d   = change in 1000 x total_principal / ncloc (minutes per KLOC)
  target_td_{3w,1m,3m} (+ _status) = total_principal 3/4/12 weekly snapshots LATER (TARGET)
 module only:
  mod_avg_complexity         = average SonarQube complexity of the module's files
  parent_module_id           = parent folder of the module ('.' = repository root)
  afferent_coupling_ca       = other modules that import a class of this module
  efferent_coupling_ce       = other modules whose classes this module imports
  module_lineage_status / module_lineage_confidence
 file only:
  lineage_id, lineage_status (NEW/UNCHANGED/MODIFIED/RENAMED), lineage_confidence (HIGH/AMBIGUOUS)
  file_extension, file_created_date, file_age_days
  file_deleted               = 1 if the file is gone in the NEXT snapshot (future info - META, not an input)
"""
import argparse, bisect, hashlib, math, os, re, sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
import javalang
from javalang import tree as JT

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extras as ex  # noqa: E402

DAY_WINDOWS = {"21d": 21, "30d": 30, "90d": 90, "180d": 180}
SUBWINDOWS = {"21d": 3, "30d": 4, "90d": 13, "180d": 26}       # equal sub-windows for slopes
LAGS = {"1w": 1, "3w": 3, "4w": 4, "12w": 12}
TARGETS = {"3w": 3, "1m": 4, "3m": 12}
DEV_COST_PER_LINE = 30
FN_BUCKETS = [1, 2, 4, 6, 8, 10, 12]
DAY = 86400.0


# ------------------------------------------------------------------ small helpers
def ols_slope(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 2 or np.ptp(x) == 0 or np.isnan(y).any():
        return np.nan
    xm = x - x.mean()
    return float((xm * (y - y.mean())).sum() / (xm ** 2).sum())


def entropy(counter):
    tot = sum(counter.values())
    if not tot:
        return np.nan
    return abs(float(-sum((c / tot) * math.log2(c / tot) for c in counter.values() if c)))


def burstiness(vals):
    vals = np.asarray(vals, float)
    if len(vals) < 2 or vals.mean() <= 0:
        return 0.0
    return float(vals.var() / vals.mean())


def safe_div(a, b, k=1.0):
    return np.where((b > 0) & np.isfinite(b), k * a / np.where(b > 0, b, 1), np.nan)


# ------------------------------------------------------------------ git history (one pass)
BRACE = re.compile(r"^(.*?)\{(.*?) => (.*?)\}(.*)$")


def split_rename(path):
    """'a/{old => new}/F.java' -> ('a/old/F.java', 'a/new/F.java'); plain path -> (None, path)"""
    if " => " not in path:
        return None, path
    m = BRACE.match(path)
    if m:
        pre, old, new, post = m.groups()
        return (pre + old + post).replace("//", "/"), (pre + new + post).replace("//", "/")
    old, new = path.split(" => ", 1)
    return old.strip(), new.strip()


class GitHistory:
    """Every non-merge commit up to `tip`: per path, events (time, commit, author, added, deleted).
    Renames are followed: history(path) also includes the file's earlier paths."""

    def __init__(self, repo, tip):
        out = ex.git(repo, "log", "--no-merges", "-M", "--numstat", "--format=@@%H|%ct|%ae", tip)
        self.events = defaultdict(list)            # path -> [(t, commit, author, a, d)]
        self.renamed_into = defaultdict(list)      # new_path -> [(old_path, t)]
        commit = t = author = None
        for line in out.splitlines():
            if line.startswith("@@"):
                commit, ct, author = line[2:].split("|", 2)
                t = int(ct)
                continue
            p = line.split("\t")
            if len(p) != 3 or commit is None:
                continue
            a = int(p[0]) if p[0].isdigit() else 0
            d = int(p[1]) if p[1].isdigit() else 0
            old, new = split_rename(p[2])
            self.events[new].append((t, commit, author, a, d))
            if old and old != new:
                self.renamed_into[new].append((old, t))
        for evs in self.events.values():
            evs.sort()

    avail = None          # commit -> first snapshot rank where it is reachable (set by run())

    def history(self, path, upto, rank=None, _depth=0):
        """events of the file now at `path`, following renames, with time <= upto and
        (if rank is given) reachable from snapshot `rank`"""
        ok = (lambda e: True) if rank is None or self.avail is None else \
            (lambda e: self.avail.get(e[1], 10 ** 9) <= rank)
        evs = [e for e in self.events.get(path, []) if e[0] <= upto and ok(e)]
        if _depth < 20:
            for old, t in self.renamed_into.get(path, []):
                if t <= upto:
                    evs += self.history(old, t, rank, _depth + 1)
        return evs


# ------------------------------------------------------------------ source parsing (cached by blob)
DECISIONS = (JT.IfStatement, JT.ForStatement, JT.WhileStatement, JT.DoStatement,
             JT.CatchClause, JT.TernaryExpression)


def method_complexity(node):
    """1 + decision points inside this method. Nested methods, constructors and classes
    (inner / anonymous / local) are skipped here - they are counted as their own methods."""
    count = 1
    stack = list(node.children)
    while stack:
        cur = stack.pop()
        if isinstance(cur, (list, tuple, set)):
            stack.extend(cur)
            continue
        if not isinstance(cur, JT.Node):
            continue
        if isinstance(cur, (JT.MethodDeclaration, JT.ConstructorDeclaration, JT.ClassDeclaration)):
            continue
        if isinstance(cur, DECISIONS):
            count += 1
        elif isinstance(cur, JT.SwitchStatementCase):
            count += sum(1 for c in (cur.case or []) if c != "default")
        elif isinstance(cur, JT.BinaryOperation) and cur.operator in ("&&", "||"):
            count += 1
        stack.extend(cur.children)
    return count


class SourceInfo:
    def __init__(self):
        self.cache = {}       # blob id -> dict

    def parse(self, blob_id, text):
        if blob_id in self.cache:
            return self.cache[blob_id]
        info = {"ok": False, "fn": [], "package": None, "imports": []}
        try:
            cu = javalang.parse.parse(text)
            info["package"] = cu.package.name if cu.package else ""
            info["imports"] = [(i.path, bool(i.wildcard), bool(i.static)) for i in (cu.imports or [])]
            fns = []
            for _, n in cu.filter(JT.MethodDeclaration):
                if n.body is not None:
                    fns.append(method_complexity(n))
            for _, n in cu.filter(JT.ConstructorDeclaration):
                fns.append(method_complexity(n))
            info["fn"] = fns
            info["ok"] = True
        except Exception:
            pass
        self.cache[blob_id] = info
        return info


def fn_stats(cc_list):
    out = {"fn_count": len(cc_list),
           "fn_complexity_max": max(cc_list) if cc_list else 0,
           "fn_complexity_mean": float(np.mean(cc_list)) if cc_list else 0.0}
    edges = FN_BUCKETS + [10 ** 9]
    for lo, hi in zip(edges[:-1], edges[1:]):
        out[f"fn_complexity_dist_{lo}"] = sum(1 for c in cc_list if lo <= c < hi)
    return out


def tree_blobs(repo, sha):
    """{path: blob_id} of main Java files at a commit"""
    out = ex.git(repo, "ls-tree", "-r", sha)
    res = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob" and ex.is_main_java(path):
            res[path] = parts[2]
    return res


def read_blob_texts(repo, blob_ids):
    import subprocess
    ids = list(blob_ids)
    if not ids:
        return {}
    out = subprocess.run(["git", "-C", repo, "cat-file", "--batch"],
                         input="".join(f"{b}\n" for b in ids).encode(), capture_output=True).stdout
    res, pos = {}, 0
    for b in ids:
        nl = out.index(b"\n", pos)
        head = out[pos:nl].split()
        size = int(head[2])
        res[b] = out[nl + 1: nl + 1 + size].decode("utf-8", "replace")
        pos = nl + 1 + size + 1
    return res


# ------------------------------------------------------------------ lineage between snapshots
def diff_events(repo, a, b):
    out = ex.git(repo, "diff", "-M", "-C", "--name-status", a, b)
    ev = []
    for line in out.splitlines():
        p = line.split("\t")
        if not p or not p[0]:
            continue
        st = p[0][0]
        if st in "RC" and len(p) == 3:
            ev.append((st, p[1], p[2]))
        elif st in "AMD" and len(p) == 2:
            ev.append((st, p[1], p[1]))
    return ev


def lineage_id(salt, path):
    return hashlib.sha1(f"{salt}:{path}".encode()).hexdigest()[:16]


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="git clone used for the run")
    ap.add_argument("--out", required=True, help="the run's output folder")
    a = ap.parse_args()
    run(os.path.expanduser(a.repo), os.path.expanduser(a.out))


def run(repo, out):
    import td_pipeline as tp

    for lvl in ("project", "module", "file"):
        p = os.path.join(out, f"raw_hist_{lvl}.csv")
        if os.path.exists(p):
            os.remove(p)
    tp.join_levels(out)                                     # fresh level files without history

    plan = pd.read_csv(os.path.join(out, "weeks_plan.csv"), sep=";")
    plan["week"] = pd.to_datetime(plan["week"]).dt.strftime("%Y-%m-%d")
    plan["idx"] = range(len(plan))
    st = pd.read_csv(os.path.join(out, "status.csv"), sep=";")
    st["week"] = pd.to_datetime(st["week"]).dt.strftime("%Y-%m-%d")
    ok_weeks = set(st[st.status == "SUCCESS"].week)
    plan["ok"] = plan.week.isin(ok_weeks)
    ctime = {}
    for sha in plan.sha.unique():
        ctime[sha] = int(ex.git(repo, "show", "-s", "--format=%ct", sha).strip())
    plan["t0"] = plan.sha.map(ctime)
    okp = plan[plan.ok].reset_index(drop=True)
    widx = dict(zip(plan.week, plan.idx))

    rd = lambda n: pd.read_csv(os.path.join(out, f"{n}_level.csv"), sep=";")
    P, M, F = rd("project"), rd("module"), rd("file")
    for d in (P, M, F):
        d["week"] = pd.to_datetime(d["week"]).dt.strftime("%Y-%m-%d")
        d["idx"] = d.week.map(widx)
        d["t0"] = d.sha.map(ctime)

    print(f"walking git history up to {okp.sha.iloc[-1][:10]} ...", flush=True)
    G = GitHistory(repo, plan.sha.iloc[-1])
    # NO LOOK-AHEAD: a commit counts at snapshot k only if it is REACHABLE from that snapshot's
    # commit. (A side-branch commit dated in March but merged in May is not in March's code.)
    avail, prev = {}, None
    for k, sha in enumerate(okp.sha):
        rng = [sha] if prev is None else [f"{prev}..{sha}"]
        if sha != prev:
            for c in ex.git(repo, "rev-list", "--no-merges", *rng).split():
                avail.setdefault(c, k)
        prev = sha
    G.avail = avail
    week_rank = {w: k for k, w in enumerate(okp.week)}
    S = SourceInfo()
    salt = os.path.basename(repo.rstrip("/"))

    # ---- per snapshot: files, lineage, parsing
    lineage = {}            # path -> (lid, confidence)  (state at previous ok snapshot)
    snap_files = {}         # week -> {path: info}
    prev_sha = None
    for _, r in okp.iterrows():
        blobs = tree_blobs(repo, r.sha)
        status = {}
        if prev_sha is None:
            lineage = {p: (lineage_id(salt, p), "HIGH") for p in blobs}
            status = {p: "NEW" for p in blobs}
        elif r.sha == prev_sha:
            status = {p: "UNCHANGED" for p in blobs}
        else:
            evs = [e for e in diff_events(repo, prev_sha, r.sha)
                   if ex.is_main_java(e[1]) or ex.is_main_java(e[2])]
            src_count = Counter(e[1] for e in evs if e[0] in "RC")
            nxt = {}
            touched = set()
            for stt, old, new in evs:
                touched.update([old, new])
                if stt == "D":
                    continue
                if stt == "A":
                    nxt[new] = (lineage_id(salt, f"{new}@{r.sha}"), "HIGH"); status[new] = "NEW"
                elif stt == "M":
                    nxt[new] = lineage.get(new, (lineage_id(salt, new), "HIGH")); status[new] = "MODIFIED"
                else:   # R / C
                    lid, conf = lineage.get(old, (lineage_id(salt, old), "HIGH"))
                    if stt == "C" or src_count[old] > 1:
                        conf = "AMBIGUOUS"
                        if stt == "C":
                            lid = lineage_id(salt, f"{new}@{r.sha}")
                    nxt[new] = (lid, conf); status[new] = "RENAMED" if stt == "R" else "NEW"
            for p, v in lineage.items():
                if p not in touched and p in blobs:
                    nxt[p] = v; status[p] = "UNCHANGED"
            lineage = {p: v for p, v in nxt.items() if p in blobs}
        for p in blobs:
            if p not in lineage:
                lineage[p] = (lineage_id(salt, f"{p}@{r.sha}"), "HIGH"); status.setdefault(p, "NEW")
        texts = read_blob_texts(repo, [b for b in set(blobs.values()) if b not in S.cache])
        info = {}
        for p, b in blobs.items():
            src = S.parse(b, texts.get(b, "")) if b not in S.cache else S.cache[b]
            info[p] = {"blob": b, "lid": lineage[p][0], "conf": lineage[p][1],
                       "lstatus": status.get(p, "UNCHANGED"), "src": src}
        snap_files[r.week] = info
        prev_sha = r.sha
    print(f"parsed {len(S.cache)} distinct file versions", flush=True)

    # ---------------------------------------------------------------- FILE level
    F = F[F["path"].astype(str).map(ex.is_main_java)].copy()
    rows = []
    for _, r in F.iterrows():
        inf = snap_files.get(r.week, {}).get(r.path)
        if inf is None:
            continue
        T0 = r.t0
        evs = G.history(r.path, T0, week_rank[r.week])
        row = {"week": r.week, "sha": r.sha, "module": r.module, "file": r.file,
               "lineage_id": inf["lid"], "lineage_status": inf["lstatus"],
               "lineage_confidence": inf["conf"],
               "file_extension": os.path.splitext(r.path)[1].lstrip("."),
               "parse_ok": int(inf["src"]["ok"])}
        first = min((e[0] for e in evs), default=None)
        row["file_created_date"] = pd.to_datetime(first, unit="s").strftime("%Y-%m-%d") if first else None
        row["file_age_days"] = round((T0 - first) / DAY, 2) if first else np.nan
        row.update(git_window_features(evs, T0))
        row.update(fn_stats(inf["src"]["fn"]) if inf["src"]["ok"] else {})
        rows.append(row)
    HF = pd.DataFrame(rows)

    # ---------------------------------------------------------------- MODULE / PROJECT git + fn
    mrows, prows = [], []
    for _, r in okp.iterrows():
        info = snap_files[r.week]
        by_mod = defaultdict(list)
        for p in info:
            by_mod[ex.module_and_rel(p)[0]].append(p)
        all_evs = []
        mod_evs = {}
        for m, paths in by_mod.items():
            evs = []
            for p in paths:
                evs += G.history(p, r.t0, week_rank[r.week])
            mod_evs[m] = evs
            all_evs += evs
        # module coupling from imports
        fq_mod = {}
        pkg_mods = defaultdict(set)
        for p in info:
            m, rel = ex.module_and_rel(p)
            fq = rel[:-5].replace("/", ".")
            fq_mod[fq] = m
            pkg_mods[fq.rsplit(".", 1)[0] if "." in fq else ""].add(m)
        deps = defaultdict(set)
        for p, inf in info.items():
            m = ex.module_and_rel(p)[0]
            for path_, wild, static in inf["src"]["imports"]:
                targets = set()
                if wild and not static:
                    targets = pkg_mods.get(path_, set())
                else:
                    name = path_
                    while name and name not in fq_mod and "." in name:
                        name = name.rsplit(".", 1)[0]          # static member / nested class
                    if name in fq_mod:
                        targets = {fq_mod[name]}
                for tm in targets:
                    if tm != m:
                        deps[m].add(tm)
        afferent = Counter(t for m in deps for t in deps[m])
        for m, paths in by_mod.items():
            fn = [c for p in paths if info[p]["src"]["ok"] for c in info[p]["src"]["fn"]]
            row = {"week": r.week, "sha": r.sha, "module": m,
                   "parent_module_id": (m.rsplit("/", 1)[0] if "/" in m else ".") if m != "." else None,
                   "afferent_coupling_ca": afferent.get(m, 0), "efferent_coupling_ce": len(deps.get(m, ())),
                   "parse_failed_files": sum(1 for p in paths if not info[p]["src"]["ok"])}
            row.update(git_window_features(mod_evs[m], r.t0))
            row.update(fn_stats(fn))
            mrows.append(row)
        fn = [c for p in info if info[p]["src"]["ok"] for c in info[p]["src"]["fn"]]
        row = {"week": r.week, "sha": r.sha,
               "parse_failed_files": sum(1 for p in info if not info[p]["src"]["ok"])}
        row.update(git_window_features(all_evs, r.t0))
        row.update(fn_stats(fn))
        prows.append(row)
    HM, HP = pd.DataFrame(mrows), pd.DataFrame(prows)

    # module lineage: does the module continue from the previous snapshot?
    HM = module_lineage(HM, HF)

    # ---------------------------------------------------------------- SonarQube-based history
    HP = HP.merge(sonar_history(P, ["__all__"], plan), on=["week", "sha"], how="left")
    HM = HM.merge(sonar_history(M, ["module"], plan), on=["week", "sha", "module"], how="outer")
    Fl = F.merge(HF[["week", "sha", "module", "file", "lineage_id"]], on=["week", "sha", "module", "file"], how="inner")
    HF = HF.merge(sonar_history(Fl, ["lineage_id"], plan, carry=("module", "file")).drop(columns=["lineage_id"]),
                  on=["week", "sha", "module", "file"], how="left")
    # a file whose identity is AMBIGUOUS (copied / split) can't be matched to its future self
    amb = HF["lineage_confidence"] == "AMBIGUOUS"
    for k in TARGETS:
        if f"target_td_{k}" in HF:
            HF.loc[amb, f"target_td_{k}"] = np.nan
            HF.loc[amb, f"target_td_{k}_status"] = "AMBIGUOUS_LINEAGE"
    # mod_avg_complexity = average file complexity
    mc = F.groupby(["week", "sha", "module"])["complexity"].mean().rename("mod_avg_complexity").reset_index()
    HM = HM.merge(mc, on=["week", "sha", "module"], how="left")
    # file_deleted: gone (lineage ends) in the next ok snapshot  -> META only
    nxt_ids = {}
    oks = list(okp.week)
    for i, w in enumerate(oks[:-1]):
        nxt_ids[w] = {v["lid"] for v in snap_files[oks[i + 1]].values()}
    HF["file_deleted"] = [(int(lid not in nxt_ids[w]) if w in nxt_ids else np.nan)
                          for w, lid in zip(HF.week, HF.lineage_id)]

    for lvl, d in (("project", HP), ("module", HM), ("file", HF)):
        d.to_csv(os.path.join(out, f"raw_hist_{lvl}.csv"), sep=";", index=False)
        print(f"raw_hist_{lvl}.csv {d.shape}")
    tp.join_levels(out)


def git_window_features(evs, T0):
    """evs: [(t, commit, author, added, deleted)] -> window features at T0 (only t <= T0 used)"""
    evs = [e for e in evs if e[0] <= T0]
    res = {}
    for k, n in DAY_WINDOWS.items():
        lo = T0 - n * DAY
        w = [e for e in evs if e[0] > lo]
        res[f"git_commits_{k}"] = len({e[1] for e in w})
        res[f"git_lines_churned_{k}"] = sum(e[3] + e[4] for e in w)
        nb = SUBWINDOWS[k]
        width = n * DAY / nb
        bins = np.zeros(nb)
        for e in w:
            j = min(nb - 1, int((T0 - e[0]) // width))
            bins[nb - 1 - j] += e[3] + e[4]
        res[f"churn_slope_{k}"] = ols_slope(np.arange(nb) * (width / (7 * DAY)), bins)
    c1 = len({e[1] for e in evs if e[0] > T0 - 7 * DAY})
    c0 = len({e[1] for e in evs if T0 - 14 * DAY < e[0] <= T0 - 7 * DAY})
    ch1 = sum(e[3] + e[4] for e in evs if e[0] > T0 - 7 * DAY)
    ch0 = sum(e[3] + e[4] for e in evs if T0 - 14 * DAY < e[0] <= T0 - 7 * DAY)
    res["git_commit_acceleration"] = c1 - c0
    res["git_churn_acceleration"] = ch1 - ch0
    nb, width = 26, 180 * DAY / 26
    cb, chb = np.zeros(nb), np.zeros(nb)
    seen = [set() for _ in range(nb)]
    for e in evs:
        if e[0] > T0 - 180 * DAY:
            j = min(nb - 1, int((T0 - e[0]) // width))
            seen[j].add(e[1]); chb[j] += e[3] + e[4]
    cb = np.array([len(s) for s in seen], float)
    res["commit_burstiness_180d"] = burstiness(cb)
    res["churn_burstiness_180d"] = burstiness(chb)
    per_author = Counter()
    for c, au in {(e[1], e[2]) for e in evs}:
        per_author[au] += 1
    res["major_author_commits"] = max(per_author.values()) if per_author else 0
    recent = Counter()
    for c, au in {(e[1], e[2]) for e in evs if e[0] > T0 - 180 * DAY}:
        recent[au] += 1
    res["knowledge_fragmentation_180d"] = entropy(recent)
    return res


def module_lineage(HM, HF):
    """CONTINUED: module existed in the previous snapshot. RENAMED: most of its files (by lineage)
    were in ONE other module before. NEW: otherwise. Confidence HIGH / MEDIUM / LOW."""
    out = []
    weeks = sorted(HM.week.unique())
    prev_mods, prev_lid_mod = set(), {}
    for w in weeks:
        cur = HF[HF.week == w]
        lid_mod = dict(zip(cur.lineage_id, cur.module))
        for m in HM[HM.week == w].module:
            if m in prev_mods:
                out.append((w, m, "CONTINUED", "HIGH"))
                continue
            lids = [l for l, mm in lid_mod.items() if mm == m]
            before = Counter(prev_lid_mod[l] for l in lids if l in prev_lid_mod)
            if before and lids:
                src, n = before.most_common(1)[0]
                share = n / len(lids)
                if share >= 0.5:
                    out.append((w, m, "RENAMED", "HIGH" if share >= 0.8 else "MEDIUM"))
                    continue
            out.append((w, m, "NEW", "HIGH" if not prev_mods else "LOW" if before else "HIGH"))
        prev_mods, prev_lid_mod = set(HM[HM.week == w].module), lid_mod
    lin = pd.DataFrame(out, columns=["week", "module", "module_lineage_status", "module_lineage_confidence"])
    return HM.merge(lin, on=["week", "module"], how="left")


def sonar_history(D, keys, plan, carry=()):
    """TD lags/changes/slopes (weekly snapshots) and SonarQube day-window changes (as-of)."""
    D = D.copy()
    if keys == ["__all__"]:
        D["__all__"] = "project"
    D = D[D.idx.notna()]
    num = lambda c: pd.to_numeric(D[c], errors="coerce") if c in D else pd.Series(np.nan, index=D.index)
    D["tp"] = num("total_principal")
    ncloc = num("ncloc")
    D["v_ncloc"] = ncloc
    D["v_viol"] = num("violations")
    D["v_cog"] = num("cognitive_complexity")
    D["v_cc_density"] = safe_div(num("complexity"), ncloc, 1000)
    if "duplicated_lines_density" in D:
        D["v_dup"] = num("duplicated_lines_density")
    else:
        D["v_dup"] = safe_div(num("duplicated_lines"), num("lines"), 100)
    D["v_debt_density"] = safe_div(D["tp"], ncloc, 1000)
    D["finding_density_t0"] = safe_div(D["v_viol"], ncloc, 1000)
    D["development_cost_t0"] = DEV_COST_PER_LINE * ncloc
    res = []
    plan_idx = plan.set_index("idx")
    for key, g in D.groupby(keys, dropna=True):
        g = g.sort_values("idx")
        by_idx = dict(zip(g.idx.astype(int), g.tp))
        series = g.drop_duplicates("sha", keep="last").sort_values("t0")   # one point per commit
        ts = series.t0.to_numpy()
        for _, r in g.iterrows():
            i, T0 = int(r.idx), r.t0
            o = {k: r[k] for k in ["week", "sha"] + ([] if keys == ["__all__"] else keys) + list(carry)}
            o["finding_density_t0"] = r.finding_density_t0
            o["development_cost_t0"] = r.development_cost_t0
            for k, n in LAGS.items():
                lag = by_idx.get(i - n, np.nan)
                if k != "1w":
                    o[f"td_{k}_lag"] = lag
                o[f"td_change_{k}"] = r.tp - lag
            for n in (4, 12):
                pts = [by_idx.get(j, np.nan) for j in range(i - n + 1, i + 1)]
                o[f"td_slope_{n}w"] = ols_slope(range(n), pts)
                o[f"td_history_points_{n}w"] = int(np.sum(~np.isnan(pts)))
            pts4 = np.array([by_idx.get(j, np.nan) for j in range(i - 3, i + 1)])
            o["td_volatility_4w"] = float(np.std(pts4)) if not np.isnan(pts4).any() else np.nan
            l4 = by_idx.get(i - 4, np.nan)
            if l4 == l4 and l4 > 0:
                o["td_growth_rate_4w"] = (r.tp - l4) / l4
            elif l4 == 0 and r.tp == 0:
                o["td_growth_rate_4w"] = 0.0          # 0 -> 0: no growth
            else:
                o["td_growth_rate_4w"] = np.nan       # unknown lag, or 0 -> >0 (infinite growth)
            for k, n in DAY_WINDOWS.items():
                start = T0 - n * DAY
                j = bisect.bisect_right(ts, start) - 1          # as-of snapshot at/before start
                if j < 0:
                    for c in ("complexity_slope", "duplication_change", "cognitive_complexity_change",
                              "ncloc_change", "violations_change", "debt_density_change"):
                        o[f"{c}_{k}"] = np.nan
                    o[f"sonar_history_ok_{k}"] = 0
                    continue
                base = series.iloc[j]
                win = series[(series.t0 >= base.t0) & (series.t0 <= T0)]
                o[f"complexity_slope_{k}"] = ols_slope((win.t0 - T0) / (7 * DAY), win.v_cc_density)
                o[f"duplication_change_{k}"] = r.v_dup - base.v_dup
                o[f"cognitive_complexity_change_{k}"] = r.v_cog - base.v_cog
                o[f"ncloc_change_{k}"] = r.v_ncloc - base.v_ncloc
                o[f"violations_change_{k}"] = r.v_viol - base.v_viol
                o[f"debt_density_change_{k}"] = r.v_debt_density - base.v_debt_density
                o[f"sonar_history_ok_{k}"] = 1
            for k, n in TARGETS.items():
                j = i + n
                if j not in plan_idx.index:
                    o[f"target_td_{k}"], o[f"target_td_{k}_status"] = np.nan, "BEYOND_RUN"
                elif not plan_idx.loc[j, "ok"]:
                    o[f"target_td_{k}"], o[f"target_td_{k}_status"] = np.nan, "WEEK_NOT_SCANNED"
                elif j in by_idx:
                    o[f"target_td_{k}"], o[f"target_td_{k}_status"] = by_idx[j], "OBSERVED"
                else:
                    o[f"target_td_{k}"], o[f"target_td_{k}_status"] = np.nan, "ENTITY_GONE"
            res.append(o)
    out = pd.DataFrame(res)
    if keys == ["__all__"]:
        out = out.drop(columns=["__all__"], errors="ignore")
    return out


if __name__ == "__main__":
    main()
