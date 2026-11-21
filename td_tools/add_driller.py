#!/usr/bin/env python3
"""
add_driller.py - add the Java Driller columns (jd_*) to runs that are already finished,
without SonarQube: for every successful snapshot it checks out that commit, runs JavaDriller on
the same main source folders, then rebuilds the level tables (td_pipeline.join_levels).

One-time setup (on the laptop, inside ~/td-tools):
    mkdir -p lib driller
    mvn -q dependency:copy -Dartifact=com.github.javaparser:javaparser-core:3.26.2 -DoutputDirectory=lib
    javac -cp lib/javaparser-core-3.26.2.jar -d driller JavaDriller.java

Then, per finished run (repeat for each repo):
    python add_driller.py --repo ~/td-work/square_okhttp --out ~/td-out/okhttp_final
and rebuild the marts:
    python run_repos.py repos.csv --mart-only

New runs need nothing: td_pipeline.py runs the Driller itself once driller/ and lib/ exist.
Snapshots already in raw_jd_file.csv are skipped, so it can be stopped and run again.
Output from an older Driller version (fewer columns) is moved to *.v1.bak and redone.
"""
import argparse, os, subprocess, sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import td_pipeline as tp  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="the git clone used for the run")
    ap.add_argument("--out", required=True, help="the run folder")
    ap.add_argument("--driller-cp", default=None)
    ap.add_argument("--java", default="/usr/lib/jvm/java-17-openjdk-amd64/bin/java")
    a = ap.parse_args()
    repo, out = os.path.expanduser(a.repo), os.path.expanduser(a.out)
    cp = a.driller_cp or tp.driller_classpath()
    if not cp:
        sys.exit("Java Driller not built - see the setup lines at the top of this file")
    st = pd.read_csv(os.path.join(out, "status.csv"), sep=";")
    st = st[st.status == "SUCCESS"]
    tp.driller_upgrade(out)      # output of an older Driller version -> *.v1.bak, drill again
    done = set()
    jp = os.path.join(out, "raw_jd_file.csv")
    if os.path.exists(jp):
        done = set(pd.read_csv(jp, sep=";", usecols=["week"]).week.astype(str))
    logfile = os.path.join(out, "build_and_scan.log")
    todo = [(str(w), s) for w, s in zip(st.week, st.sha) if str(w) not in done]
    print(f"{len(todo)} snapshots to drill ({len(done)} already done)")
    for i, (week, sha) in enumerate(todo, 1):
        r = subprocess.run(f"git checkout -f -q {sha} && git clean -fdxq", cwd=repo, shell=True)
        if r.returncode:
            print(f"[{i}/{len(todo)}] {week}: checkout failed - skipped")
            continue
        ok = tp.run_driller(repo, week, sha, out, cp, a.java, logfile)
        print(f"[{i}/{len(todo)}] {week} {sha[:10]} {'ok' if ok else 'FAILED'}", flush=True)
    tp.join_levels(out)
    print("level tables rebuilt with jd_* columns:", out)


if __name__ == "__main__":
    main()
