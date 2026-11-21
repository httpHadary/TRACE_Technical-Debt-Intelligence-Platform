"""
validate.py - is the collected data correct?

  python validate.py --out ~/td-out/retrofit --paper zenodo/square_retrofit_measures.csv

Prints PASS / WARN / FAIL lines for:
  1. structure      (weeks, gaps, failed weeks)
  2. value ranges   (each column inside its legal range)
  3. identities     (SonarQube numbers that must add up)
  4. level match    (sum of files == project, CK classes counted once)
  5. jumps          (sudden ncloc changes = broken build)
  6. paper          (same weeks compared with the authors' Zenodo CSV)
"""
import argparse, os
import warnings
import numpy as np
warnings.filterwarnings("ignore")
import pandas as pd

RANGES = {  # column: (min, max)   None = no limit
    "bugs": (0, None), "vulnerabilities": (0, None), "code_smells": (0, None),
    "sqale_index": (0, None), "reliability_remediation_effort": (0, None),
    "security_remediation_effort": (0, None), "total_principal": (0, None),
    "ncloc": (1, None), "comment_lines": (0, None), "complexity": (0, None),
    "duplicated_blocks": (0, None), "uncovered_lines": (0, None), "classes": (0, None),
    "coverage": (0, 100), "comment_lines_density": (0, 100),
    "duplicated_lines_density": (0, 100), "sqale_debt_ratio": (0, None),  # can pass 100%: a 2-line file with a 60-min issue = 100%+
    "sqale_rating": (1, 5), "reliability_rating": (1, 5), "security_rating": (1, 5),
    "WMC": (0, None), "DIT": (1, None), "NOC": (0, None), "CBO": (0, None),
    "RFC": (0, None), "LCOM": (0, None), "Ca": (0, None), "Ce": (0, None),
    "NPM": (0, None), "LCOM3": (0, 2), "LOC": (0, None), "DAM": (0, 1),
    "MOA": (0, None), "MFA": (0, 1), "CAM": (0, 1), "IC": (0, None),
    "CBM": (0, None), "AMC": (0, None),
}
res = {"PASS": 0, "WARN": 0, "FAIL": 0}


def say(level, msg):
    res[level] += 1
    print(f"[{level}] {msg}")


def check_ranges(df, name):
    for c, (lo, hi) in RANGES.items():
        if c not in df:
            continue
        v = pd.to_numeric(df[c], errors="coerce").dropna()
        bad = ((v < lo) if lo is not None else False) | ((v > hi) if hi is not None else False)
        n = int(np.sum(bad))
        if n:
            say("FAIL", f"{name}: {c} has {n} values outside [{lo}, {hi}]")
    say("PASS", f"{name}: range check done ({len(df)} rows)")


def near(a, b, tol):
    return np.abs(a - b) <= tol * np.maximum(1, np.abs(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--paper", help="authors' Zenodo CSV for the same repo")
    ap.add_argument("--repo", help="git clone of the run: enables the stale-scan check")
    a = ap.parse_args()
    rd = lambda n: pd.read_csv(os.path.join(a.out, n), sep=";")
    proj, mod, fil = rd("project_level.csv"), rd("module_level.csv"), rd("file_level.csv")
    proj["week"] = pd.to_datetime(proj["week"])
    proj = proj.sort_values("week")

    # 1. structure
    st = rd("status.csv")
    failed = st[st.status != "SUCCESS"]
    plan = rd("weeks_plan.csv")
    say("PASS" if failed.empty else "WARN",
        f"{len(proj)} of {len(plan)} planned weeks collected, {len(failed)} failed "
        f"{list(failed.status.value_counts().items()) if len(failed) else ''}")
    gaps = proj["week"].diff().dt.days.dropna()
    say("PASS" if (gaps == 7).all() else "WARN",
        f"week spacing: {gaps.value_counts().to_dict()} days (should all be 7)")
    dup = proj["sha"].duplicated().sum()
    if dup:
        say("WARN", f"{dup} weeks reuse the previous commit (no commits that week) - normal")

    # 2. ranges
    for df, n in [(proj, "project"), (mod, "module"), (fil, "file")]:
        check_ranges(df, n)

    # 3. identities (project level)
    p = proj  # read_csv already gives numbers
    if {"violations", "bugs", "vulnerabilities", "code_smells"} <= set(p):
        ok = near(p.violations, p.bugs + p.vulnerabilities + p.code_smells, 0.001).all()
        say("PASS" if ok else "FAIL", "violations == bugs + vulnerabilities + code_smells")
    sev = ["blocker_violations", "critical_violations", "major_violations",
           "minor_violations", "info_violations"]
    if set(sev) <= set(p) and "violations" in p:
        ok = near(p.violations, p[sev].fillna(0).sum(axis=1), 0.001).all()
        say("PASS" if ok else "FAIL", "violations == sum of 5 severities")
    if {"comment_lines_density", "comment_lines", "ncloc"} <= set(p):
        calc = p.comment_lines / (p.ncloc + p.comment_lines) * 100
        ok = near(p.comment_lines_density, calc, 0.01).all()
        say("PASS" if ok else "WARN", "comment_lines_density == comment_lines/(ncloc+comment_lines)*100")
    if {"sqale_debt_ratio", "sqale_index", "ncloc"} <= set(p):
        calc = p.sqale_index / (30 * p.ncloc) * 100
        ok = near(p.sqale_debt_ratio, calc, 0.05).all()
        say("PASS" if ok else "WARN", "sqale_debt_ratio ~= sqale_index/(30*ncloc)*100")

    # 4. levels agree
    for c in ["ncloc", "bugs", "code_smells", "vulnerabilities", "sqale_index"]:
        if c in fil and c in p:
            fs = fil.groupby("week")[c].sum()
            if "folder_level_" + c in mod:   # issues on folders/packages belong to no file
                # the "(project)" row is added once below; its folder_level_ value is the same
                # project-wide issues again, so it must not be counted twice
                fl = mod[mod.module != "(project)"]
                fs = fs.add(fl.groupby("week")["folder_level_" + c].sum(), fill_value=0)
            if "(project)" in set(mod["module"]):  # issues on the whole project belong to no file
                fs = fs.add(mod[mod.module == "(project)"].groupby("week")[c].sum(), fill_value=0)
            ms = mod.groupby("week")[c].sum()
            pv = p.set_index(p.week.dt.strftime("%Y-%m-%d"))[c]
            idx = fs.index.intersection(pv.index)
            ok_f = near(fs[idx].values, pv[idx].values, 0.001).all()
            ok_m = near(ms[idx].values, pv[idx].values, 0.001).all()
            say("PASS" if ok_f and ok_m else "FAIL",
                f"sum of files == sum of modules == project for {c}")
    if "(project)" in set(mod["module"]):
        pr = mod[mod.module == "(project)"]
        print(f"[INFO] issues on the whole project (not on any file), kept as module '(project)': "
              f"code_smells avg {pr.get('code_smells', pd.Series([0])).fillna(0).mean():.1f} per week")
    if "n_classes" in p and "n_classes" in mod:
        ok = (mod.groupby("week")["n_classes"].sum().values == p["n_classes"].values).all()
        say("PASS" if ok else "FAIL", "CK classes: modules add up to project")
    if "n_dropped" in p:
        worst = (p.n_dropped / p.n_classes.clip(lower=1)).max()
        say("PASS" if worst <= 0.05 else "WARN",
            f"CKJM dropped at most {worst:.1%} of classes in a week (keep under 5%)")
    if "file" in fil and "WMC" in fil:
        fn = fil["file"].astype(str)
        real = fil[fn.str.endswith(".java") & ~fn.str.endswith("package-info.java")]  # Java files with a class
        miss = real["WMC"].isna().mean()
        say("PASS" if miss < 0.05 else "WARN",
            f"{miss:.1%} of Sonar files have no CKJM match (should be near 0)")
    # 3c. Java Driller coverage (when the step ran): every scanned file should have jd_ values
    if "jd_fan_out" in fil:
        miss = fil["jd_fan_out"].isna().mean() * 100
        say("PASS" if miss <= 5 else "WARN",
            f"{miss:.1f}% of Sonar files have no Java Driller row (parse failed or not run; keep under 5%)")

    # 3d. Java Driller cross-module edges add up: files -> modules -> project
    cm = "jd_cross_module_deps"
    if cm in fil and cm in mod and cm in proj:
        fs = fil.groupby("week")[cm].sum()
        ms = mod.groupby("week")[cm].sum()
        ps = proj.set_index(proj["week"].astype(str))[cm]
        fs.index, ms.index = fs.index.astype(str), ms.index.astype(str)
        ok = (fs.reindex(ps.index).fillna(0) == ps.fillna(0)).all() and \
             (ms.reindex(ps.index).fillna(0) == ps.fillna(0)).all()
        say("PASS" if ok else "WARN", "Java Driller: cross-module dependencies of files == modules == project")

    # 4b. keys must be unique
    for d, n, k in [(proj, "project", ["week"]), (mod, "module", ["week", "module"]),
                    (fil, "file", ["week", "module", "file"])]:
        dup = int(d.duplicated(k).sum())
        say("PASS" if dup == 0 else "FAIL", f"{n}: keys {k} unique ({dup} duplicates)")

    # 4c. history features (history.py): lags = past values, targets = future values
    if "td_3w_lag" in p:
        plan = rd("weeks_plan.csv")
        pidx = {str(pd.to_datetime(w).date()): i for i, w in enumerate(plan.week)}
        q = p.assign(i=p.week.dt.strftime("%Y-%m-%d").map(pidx)).set_index("i")
        bad_lag = bad_tgt = 0
        for i, r in q.iterrows():
            if (i - 3) in q.index and r.td_3w_lag == r.td_3w_lag:
                bad_lag += int(abs(r.td_3w_lag - q.loc[i - 3, "total_principal"]) > 1e-6)
            if (i + 3) in q.index and r.get("target_td_3w") == r.get("target_td_3w"):
                bad_tgt += int(abs(r.target_td_3w - q.loc[i + 3, "total_principal"]) > 1e-6)
        say("PASS" if bad_lag == 0 else "FAIL", f"td_3w_lag equals the value 3 weeks earlier ({bad_lag} wrong)")
        say("PASS" if bad_tgt == 0 else "FAIL", f"target_td_3w equals the value 3 weeks later ({bad_tgt} wrong)")
        if "lineage_id" in fil:
            f2 = fil.dropna(subset=["lineage_id"]).copy()
            f2["i"] = pd.to_datetime(f2.week).dt.strftime("%Y-%m-%d").map(pidx)
            look = f2.set_index(["lineage_id", "i"])["total_principal"]
            look = look[~look.index.duplicated()]
            ok = f2.dropna(subset=["target_td_3w"])
            wrong = sum(abs(look.get((l, i + 3), np.nan) - t) > 1e-6
                        for l, i, t in zip(ok.lineage_id, ok.i, ok.target_td_3w))
            say("PASS" if wrong == 0 else "FAIL",
                f"file targets follow the same file (lineage) 3 weeks later ({wrong} wrong of {len(ok)})")
        for c in ("git_lines_churned_90d",):
            if c in fil and c in mod:
                a1 = fil.groupby("week")[c].sum(); a2 = mod.groupby("week")[c].sum()
                a3 = p.set_index(p.week.dt.strftime("%Y-%m-%d"))[c]
                okk = near(a1.values, a3.loc[a1.index].values, 1e-9).all() and near(a2.values, a3.loc[a2.index].values, 1e-9).all()
                say("PASS" if okk else "FAIL", f"history: files == modules == project for {c}")

    # 4d. same analyzer / rule set for every run that wrote into this folder
    mp = os.path.join(a.out, "analysis_meta.csv")
    if os.path.exists(mp):
        meta = pd.read_csv(mp, sep=";")
        n = meta[["sonarqube_version", "quality_profile", "rules_hash"]].drop_duplicates().shape[0]
        known = meta.quality_profile.notna().all() and (meta.quality_profile.astype(str) != "None").all()
        say(("PASS" if n == 1 else "WARN") if known else "WARN",
            f"analyzer fingerprint: {n} distinct (SonarQube {meta.sonarqube_version.iloc[-1]}, "
            f"profile '{meta.quality_profile.iloc[-1]}', {meta.active_rules.iloc[-1]} rules)")

    # 4e. stale scans: SonarQube's line count of a file must match git's for the same commit.
    # SonarQube counts the empty line after a final newline, so it may be git's count + 1.
    if a.repo and "lines" in fil:
        import subprocess
        from collections import Counter
        diffs, missing, tot = Counter(), 0, 0
        for sha, g in fil.dropna(subset=["lines"]).groupby("sha"):
            inp = "".join(f"{sha}:{x}\n" for x in g.path)
            outb = subprocess.run(["git", "-C", os.path.expanduser(a.repo), "cat-file", "--batch"],
                                  input=inp.encode(), capture_output=True).stdout
            pos = 0
            for x, sl in zip(g.path, g.lines):
                nl = outb.index(b"\n", pos)
                head = outb[pos:nl].split()
                tot += 1
                if len(head) != 3 or not head[2].isdigit():      # "<name> missing" / "ambiguous"
                    pos = nl + 1
                    missing += 1
                    continue
                size = int(head[2]); body = outb[nl + 1: nl + 1 + size]; pos = nl + 1 + size + 1
                if head[1] != b"blob":
                    missing += 1
                    continue
                diffs[int(sl) - body.count(b"\n")] += 1
        ok = diffs.get(0, 0) + diffs.get(1, 0)
        bad = tot - ok
        common = ", ".join(f"{d:+d}: {n}" for d, n in diffs.most_common(4))
        say("PASS" if bad <= 0.01 * max(tot, 1) else "FAIL",
            f"stale-scan check: SonarQube lines match git for {ok} of {tot} file-weeks "
            f"(SonarQube - git newlines -> {common}; files not found in git: {missing})")

    # 5. jumps
    ch = p.ncloc.pct_change().abs()
    big = p.loc[ch > 0.2, ["week", "sha", "ncloc"]]
    say("PASS" if big.empty else "WARN",
        "no ncloc jump > 20% week to week" if big.empty else
        f"ncloc jumps > 20% at:\n{big.to_string(index=False)}\n    check these builds")

    # 6. paper
    if a.paper:
        z = pd.read_csv(a.paper, sep=";")
        s = z[z.columns[0]].astype(str)
        z["week"] = pd.to_datetime(s, dayfirst=s.str.contains("/").any())
        if "ncloc_language_distribution" in z:
            z["ncloc"] = z["ncloc_language_distribution"].astype(str).str.extract(
                r"java=(\d+)")[0].astype(float)          # compare Java with Java
        if "total_principal" not in z and "sqale_index" in z:
            z["total_principal"] = z[["sqale_index", "reliability_remediation_effort",
                                      "security_remediation_effort"]].sum(axis=1)
        m = pd.merge_asof(p.sort_values("week"), z.sort_values("week"), on="week",
                          tolerance=pd.Timedelta(days=3), direction="nearest",
                          suffixes=("_ours", "_paper"))
        print(f"\nCompared with the paper on {m.filter(like='_paper').dropna(how='all').shape[0]} weeks")
        print(f"{'column':32s}{'ours(avg)':>12s}{'paper(avg)':>12s}{'ratio':>8s}{'trend rho':>11s}")
        for c in ["ncloc", "classes", "complexity", "comment_lines", "bugs", "vulnerabilities",
                  "code_smells", "duplicated_blocks", "sqale_index", "total_principal",
                  "WMC", "DIT", "CBO", "RFC", "LCOM", "Ca", "Ce"]:
            o, t = f"{c}_ours", f"{c}_paper"
            if o not in m or t not in m:
                continue
            d = m[[o, t]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(d) < 3:
                continue
            ratio = d[o].mean() / d[t].mean() if d[t].mean() else np.nan
            rho = d[o].rank().corr(d[t].rank())  # Spearman without scipy
            print(f"{c:32s}{d[o].mean():12.1f}{d[t].mean():12.1f}{ratio:8.2f}{rho:11.2f}")
        print("\nHow to read: ncloc/classes ratio should be ~1.00 (same code). "
              "Issue counts and TD can differ (newer SonarQube rules) but the trend rho "
              "should be high (> 0.8). CK metrics should be close if they averaged per class.")

    print(f"\nSUMMARY: {res}")


if __name__ == "__main__":
    main()
