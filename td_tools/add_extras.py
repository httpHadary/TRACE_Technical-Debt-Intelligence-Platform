"""
add_extras.py - add Halstead + git-activity metrics to a run that is already done.
No build, no SonarQube: it only reads the commits from git. Takes seconds per week.

  python add_extras.py --repo ~/td-work/square_retrofit --out ~/td-out/retrofit_matched

It reads weeks_plan.csv and status.csv in --out, computes the metrics for every
SUCCESS week, and rebuilds project_level.csv, module_level.csv and file_level.csv.
"""
import argparse, os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import td_pipeline as tp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="the git clone used for the run")
    ap.add_argument("--out", required=True, help="the run's output folder")
    a = ap.parse_args()

    plan = pd.read_csv(os.path.join(a.out, "weeks_plan.csv"), sep=";")
    st = pd.read_csv(os.path.join(a.out, "status.csv"), sep=";")
    ok = set(st[st.status == "SUCCESS"]["week"].astype(str))
    sf = pd.read_csv(os.path.join(a.out, "raw_sonar_file.csv"), sep=";", usecols=["week", "module"])
    mods = sf.groupby(sf.week.astype(str))["module"].apply(set).to_dict()

    for n in tp.EXTRA_RAW:
        p = os.path.join(a.out, f"raw_{n}.csv")
        if os.path.exists(p):
            os.remove(p)

    def append(name, rows, cols):
        p = os.path.join(a.out, f"raw_{name}.csv")
        df = pd.DataFrame(rows, columns=cols)
        df.to_csv(p, sep=";", index=False, mode="a", header=not os.path.exists(p))

    prev = None
    for week, sha in zip(plan.week.astype(str), plan.sha):
        if week in ok:
            tp.write_extras(a.repo, week, sha, prev, mods.get(week, {"."}), append)
            tp.log(f"{week} {sha[:10]} done")
        prev = sha
    tp.join_levels(a.out)


if __name__ == "__main__":
    main()
