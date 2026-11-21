"""
align_paper.py - find the real commit behind every row of the paper's CSV.

Why: the authors' date labels do not follow the real commit dates (for retrofit
the code labelled 2017-01-27 is really from 2015-12-18). So we match each paper
row to a commit by CONTENT: Java lines, XML (pom.xml) lines and number of files,
which the paper's CSV stores (ncloc_language_distribution, files).
Rows are matched in order (time only moves forward).

  python align_paper.py --repo ~/td-work/square_retrofit \
        --paper ~/zenodo/square_retrofit_measures.csv \
        --out ~/td-out/retrofit_plan.csv

Output: week;sha;commit_date;java_ours;java_paper;xml_ours;xml_paper;files_ours;files_paper;error
Then run td_pipeline.py with  --plan-csv ~/td-out/retrofit_plan.csv
"""
import argparse, os, subprocess, sys
import numpy as np
import pandas as pd


def main_branch(repo):
    """The remote's default branch (origin/HEAD), else origin/main|master|trunk, else HEAD."""
    import subprocess as _sp
    def ok(*args):
        r = _sp.run(["git", "-C", repo, *args], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""
    b = ok("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if b:
        return b
    for cand in ("origin/main", "origin/master", "origin/trunk"):
        if ok("rev-parse", "--verify", "--quiet", cand):
            return cand
    return "HEAD"


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout


def ncloc_java(t):
    """Lines that hold code once comments are removed (SonarQube's ncloc). A line like
    `/*x*/ foo();` or `} /* end */` counts; string and char literals are respected."""
    n, blk = 0, False
    for line in t.splitlines():
        code, i, L = False, 0, len(line)
        while i < L:
            c = line[i]
            if blk:
                k = line.find("*/", i)
                if k < 0:
                    break
                blk, i = False, k + 2
                continue
            if c == "/" and line.startswith("//", i):
                break
            if c == "/" and line.startswith("/*", i):
                blk, i = True, i + 2
                continue
            if c in "\"'":                      # skip a string / char literal
                q, i = c, i + 1
                while i < L and line[i] != q:
                    i += 2 if line[i] == "\\" else 1
                code, i = True, i + 1
                continue
            if not c.isspace():
                code = True
            i += 1
        n += code
    return n


def ncloc_xml(t):
    n, blk = 0, False
    for line in t.splitlines():
        s = line.strip()
        if blk:
            blk = "-->" not in s
            continue
        if not s:
            continue
        if s.startswith("<!--"):
            blk = "-->" not in s
            continue
        n += 1
    return n


def fingerprint(repo, sha):
    files = git(repo, "ls-tree", "-r", "--name-only", sha).splitlines()
    jf = [f for f in files if f.endswith(".java")
          and ("/src/main/java/" in "/" + f or "/src/java/" in "/" + f)]   # src/java = old Apache layout
    pf = [f for f in files if f.endswith("pom.xml")]
    inp = "".join(f"{sha}:{f}\n" for f in jf + pf).encode()
    out = subprocess.run(["git", "-C", repo, "cat-file", "--batch"], input=inp,
                         capture_output=True).stdout
    pos, j, x = 0, 0, 0
    for f in jf + pf:
        nl = out.index(b"\n", pos)
        size = int(out[pos:nl].split()[2])
        body = out[nl + 1: nl + 1 + size].decode("utf-8", "ignore")
        pos = nl + 1 + size + 1
        if f.endswith(".java"):
            j += ncloc_java(body)
        else:
            x += ncloc_xml(body)
    return j, x, len(jf) + len(pf)


def save_cache(path, cache):
    pd.DataFrame([(k, *v) for k, v in cache.items()],
                 columns=["sha", "java", "xml", "files", "poms"]).to_csv(path + ".tmp", sep=";", index=False)
    os.replace(path + ".tmp", path)


def count_poms(repo, sha):
    return sum(f.endswith("pom.xml") for f in git(repo, "ls-tree", "-r", "--name-only", sha).splitlines())


def num(v):
    return None if v != v else int(v)


def parse_dist(s):
    d = {}
    for part in str(s).split(";"):
        if "=" in part:
            k, v = part.split("=")
            d[k] = float(v)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--paper", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--since", default=None, help="oldest commit date to consider (default: 3 years before first label)")
    ap.add_argument("--after-weeks", type=int, default=52,
                    help="also consider commits up to this many weeks after the last label "
                         "(systemml's real commits are ~20-40 weeks AFTER its labels)")
    ap.add_argument("--cache", default=None,
                    help="fingerprint cache (default: <out>_fingerprints.csv); makes re-runs fast")
    a = ap.parse_args()

    z = pd.read_csv(a.paper, sep=";")
    s = z[z.columns[0]].astype(str)
    z["week"] = pd.to_datetime(s, dayfirst=s.str.contains("/").any()).dt.date
    z = z.sort_values("week").reset_index(drop=True)
    dist = z["ncloc_language_distribution"].map(parse_dist)
    pj = dist.map(lambda d: d.get("java", np.nan) if d else np.nan).values.astype(float)
    px = dist.map(lambda d: d.get("xml", np.nan) if d else np.nan).values.astype(float)
    if np.nansum(px) == 0:
        # e.g. commons-io: the paper's scan did not index pom.xml -> match on Java + files only
        print("note: the paper has no XML lines -> XML is not used for matching")
        px[:] = np.nan
    use_xml = not np.all(np.isnan(px))   # without XML the paper's file count has no pom.xml either
    pfiles = pd.to_numeric(z["files"], errors="coerce").values if "files" in z else np.full(len(z), np.nan)
    nan_rows = int(pd.isna(pfiles).sum()) + int((dist.map(len) == 0).sum())
    if nan_rows:
        print(f"note: {nan_rows} paper row(s) miss 'files' or the language distribution; "
              f"they are matched on the values they have")

    branch = main_branch(a.repo)
    since = a.since or str(pd.Timestamp(z.week.iloc[0]) - pd.DateOffset(years=3))[:10]
    until = str(pd.Timestamp(z.week.iloc[-1]) + pd.DateOffset(weeks=a.after_weeks))[:10]
    log = git(a.repo, "log", "--format=%H %cI", "--date-order", "--reverse",
              f"--since={since}", f"--until={until}", branch).split("\n")
    commits = [l.split() for l in log if l.strip()]
    main_line = set(git(a.repo, "rev-list", "--first-parent", f"--since={since}",
                        f"--until={until}", branch).split())
    print(f"{len(z)} paper rows, {len(commits)} candidate commits ({since} -> {until}, branch {branch})")
    if not commits:
        sys.exit(f"no commits between {since} and {until} on {branch} - wrong repo or --since?")

    cache_path = a.cache or (os.path.splitext(a.out)[0] + "_fingerprints.csv")
    cache = {}
    if os.path.exists(cache_path):
        for r in pd.read_csv(cache_path, sep=";").itertuples(index=False):
            cache[r.sha] = (int(r.java), int(r.xml), int(r.files), int(r.poms))
        print(f"  {len(cache)} fingerprints from {cache_path}")
    fps, new = [], 0
    for i, (sha, date) in enumerate(commits):
        if sha not in cache:
            cj, cx, nfiles = fingerprint(a.repo, sha)
            cache[sha] = (cj, cx, nfiles, count_poms(a.repo, sha))
            new += 1
        cj, cx, nfiles, npoms = cache[sha]
        if not use_xml:
            cx, nfiles = 0, nfiles - npoms
        fps.append((cj, cx, nfiles))
        if i % 100 == 0:
            print(f"  fingerprinting {i}/{len(commits)}", flush=True)
        if new and new % 500 == 0:
            save_cache(cache_path, cache)
    if new:
        save_cache(cache_path, cache)

    def cost(i, j):
        cj, cx, cf = fps[j]
        side = 0.0 if commits[j][0] in main_line else 0.00001   # tie-break: prefer main-line commits (they build)
        c = side
        # Java lines and file count decide; XML only breaks ties (SonarQube's XML line count
        # differs from ours by a few lines, e.g. java-websocket 79 vs 82)
        for ours, theirs, w in ((cj, pj[i], 1.0), (cx, px[i], 0.1), (cf, pfiles[i], 1.0)):
            if theirs == theirs:                     # skip a value the paper row does not have (NaN)
                c += w * abs(ours - theirs) / max(theirs, 1)
        return c

    # monotone alignment: row i -> commit c[i], with c[i] >= c[i-1]
    n, m = len(z), len(commits)
    INF = float("inf")
    prev = [cost(0, j) for j in range(m)]
    back = []
    for i in range(1, n):
        best, arg, cur, bk = INF, -1, [0.0] * m, [0] * m
        for j in range(m):
            if prev[j] < best:
                best, arg = prev[j], j
            cur[j] = best + cost(i, j)
            bk[j] = arg
        back.append(bk)
        prev = cur
    j = min(range(m), key=lambda k: prev[k])
    path = [j]
    for bk in reversed(back):
        j = bk[j]
        path.append(j)
    path.reverse()

    rows = []
    for i, j in enumerate(path):
        sha, date = commits[j]
        cj, cx, cf = fps[j]
        rows.append({"week": z.week[i], "sha": sha, "commit_date": date[:10],
                     "main_line": sha in main_line,
                     "java_ours": cj, "java_paper": num(pj[i]), "xml_ours": cx,
                     "xml_paper": num(px[i]), "files_ours": cf, "files_paper": num(pfiles[i]),
                     "error": round(cost(i, j), 4)})
    out = pd.DataFrame(rows)
    out.to_csv(a.out, sep=";", index=False)
    exact = (out.java_ours == out.java_paper).mean()
    print(out.head(8).to_string(index=False))
    print("...")
    print(out.tail(4).to_string(index=False))
    print(f"\nmean error {out.error.mean():.3f} | rows with exact Java match: {exact:.0%} | "
          f"label - commit date (weeks): "
          f"{((pd.to_datetime(out.week) - pd.to_datetime(out.commit_date)).dt.days / 7).describe()[['min','50%','max']].round(1).to_dict()}")
    print("wrote", a.out)


if __name__ == "__main__":
    sys.exit(main())
