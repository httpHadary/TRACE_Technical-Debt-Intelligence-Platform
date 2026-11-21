"""
diag_match.py - why is our ncloc different from the paper's?

Counts Java lines (quick count, no SonarQube) for every paper week, for every
combination of module groups and for week shifts of -8..+8, and shows which
combination matches the paper's ncloc best.

  python diag_match.py --repo ~/td-work/square_retrofit \
                       --paper ~/zenodo/square_retrofit_measures.csv \
                       --out ~/td-out/retrofit --weeks 40
"""
import argparse, itertools, os, subprocess
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


def count_ncloc(text):
    n, in_block = 0, False
    for line in text.splitlines():
        s = line.strip()
        if in_block:
            if "*/" in s:
                in_block = False
            continue
        if not s or s.startswith("//"):
            continue
        if s.startswith("/*"):
            in_block = "*/" not in s
            continue
        n += 1
    return n


def group_of(path):
    """top-level module group: retrofit, retrofit-adapters, retrofit-converters, ..."""
    for root in ("/src/main/java/", "/src/java/"):
        if root in "/" + path:
            return ("/" + path).split(root)[0].strip("/").split("/")[0] or "."
    return "."


def snapshot(repo, sha):
    files = [f for f in git(repo, "ls-tree", "-r", "--name-only", sha).splitlines()
             if f.endswith(".java") and ("/src/main/java/" in "/" + f or "/src/java/" in "/" + f)]
    per = {}
    if not files:
        return per
    inp = "".join(f"{sha}:{f}\n" for f in files)
    p = subprocess.run(["git", "-C", repo, "cat-file", "--batch"], input=inp.encode(),
                       capture_output=True)
    data, pos = p.stdout, 0
    for f in files:
        nl = data.index(b"\n", pos)
        size = int(data[pos:nl].split()[2])
        body = data[nl + 1: nl + 1 + size].decode("utf-8", "ignore")
        pos = nl + 1 + size + 1
        g = group_of(f)
        per[g] = per.get(g, 0) + count_ncloc(body)
    return per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--paper", required=True)
    ap.add_argument("--out", help="our td-out folder (to calibrate the quick count)")
    ap.add_argument("--weeks", type=int, default=40, help="how many paper weeks to test")
    a = ap.parse_args()

    z = pd.read_csv(a.paper, sep=";")
    s = z[z.columns[0]].astype(str)
    z["week"] = pd.to_datetime(s, dayfirst=s.str.contains("/").any()).dt.date
    z = z.sort_values("week").reset_index(drop=True)
    print("PAPER FILE:", len(z), "rows,", z.week.iloc[0], "->", z.week.iloc[-1])
    print("columns:", ", ".join(z.columns[:60]))
    show = [c for c in ["week", "ncloc", "classes", "files", "directories", "code_smells",
                        "sqale_index", "ncloc_language_distribution"] if c in z]
    print(z[show].head(6).to_string(index=False), "\n")

    branch = main_branch(a.repo)
    weeks = list(z.week.iloc[:a.weeks])
    shifts = range(-8, 9)
    cache = {}

    def counts(d):
        sha = git(a.repo, "rev-list", "-n", "1", "--first-parent", f"--before={d} 00:00", branch).strip()
        if sha not in cache:
            cache[sha] = snapshot(a.repo, sha) if sha else {}
        return cache[sha]

    # calibrate quick count against our SonarQube ncloc
    factor = 1.0
    if a.out and os.path.exists(os.path.join(a.out, "project_level.csv")):
        ours = pd.read_csv(os.path.join(a.out, "project_level.csv"), sep=";")
        q = sum(counts(pd.to_datetime(ours.week.iloc[0]).date()).values())
        if q:
            factor = ours.ncloc.iloc[0] / q
        print(f"calibration: SonarQube ncloc / quick count = {factor:.3f}")
        mod = pd.read_csv(os.path.join(a.out, "module_level.csv"), sep=";")
        w0 = mod[mod.week == mod.week.min()][["module", "ncloc", "classes"]].sort_values("ncloc", ascending=False)
        print("our modules in week 1:\n" + w0.to_string(index=False) + "\n")

    groups = sorted({g for d in weeks[:1] for g in counts(d)} |
                    {g for d in weeks[-1:] for g in counts(d)})
    print("module groups found:", groups)
    target = z.ncloc.iloc[:a.weeks].astype(float).values

    results = []
    for k in shifts:
        per_week = [counts(pd.Timestamp(d) + pd.Timedelta(weeks=k)) for d in weeks]
        for r in range(1, len(groups) + 1):
            for combo in itertools.combinations(groups, r):
                est = [factor * sum(pw.get(g, 0) for g in combo) for pw in per_week]
                err = sum(abs(e - t) / t for e, t in zip(est, target) if t) / len(target)
                results.append((err, k, combo, est[0], est[-1]))
    results.sort(key=lambda x: x[0])
    print(f"\nBEST MATCHES (paper ncloc week1={target[0]:.0f}, week{len(target)}={target[-1]:.0f})")
    print(f"{'error':>7} {'shift':>6}  {'first':>7} {'last':>7}  modules")
    for err, k, combo, e0, e1 in results[:10]:
        print(f"{err:7.1%} {k:+6d}  {e0:7.0f} {e1:7.0f}  {', '.join(combo)}")
    allg = [r for r in results if r[2] == tuple(groups) and r[1] == 0][0]
    print(f"\nall modules, no shift: error {allg[0]:.1%}")


if __name__ == "__main__":
    main()
