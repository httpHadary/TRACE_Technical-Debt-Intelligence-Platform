#!/usr/bin/env python3
"""
Run the whole pipeline for every repo listed in repos.csv, one after the other, and pack
all finished repos into ONE data mart at the end.

    source ~/td-env/bin/activate && cd ~/td-tools
    export SONAR_TOKEN=...                       # SonarQube must be UP
    python run_repos.py repos.csv --dry-run      # show what would run
    python run_repos.py repos.csv --test 5       # 5 weeks per repo, into <name>_test folders
    nohup python run_repos.py repos.csv > ~/td-out/run_repos.log 2>&1 &

For every row with enabled = 1:
  1. clone the repo into <work>/<owner>_<repo>        (skipped if it is already there)
  2. paper repo: download the paper CSV from Zenodo and match its rows to real commits
     (align_paper.py)                                   (skipped if the plan already exists)
     other repo: weekly commits from --weeks/--end
  3. td_pipeline.py: build + SonarQube + CKJM + Halstead + git + history  (resumes by itself)
  4. validate.py (with the stale-scan check) -> <out>/validation.txt
  5. a line in <out-dir>/repos_status.csv
One repo failing does not stop the others. A changed SonarQube / quality profile DOES stop
everything, because TD values would no longer be comparable between repos.
At the end: build_mart.py over every repo whose status is OK -> --mart-out (+ .zip).

repos.csv columns (only name, enabled, git_url, sonar_key are required):
  name         short id used in the mart (project_id), e.g. retrofit
  enabled      1 = run it, 0 = skip
  git_url      https://github.com/square/retrofit.git
  sonar_key    SonarQube project key, e.g. square:retrofit  (clone folder = square_retrofit)
  paper_csv    file name on Zenodo record 4534110 (e.g. square_retrofit_measures.csv);
               empty = not a paper repo -> uses weeks/end
               paper_csv AND weeks = paper rows cannot be matched to commits (zxing): regular
               weekly commits, the paper CSV is used only for the comparison in validate.py
  weeks, end   only for non-paper repos: number of weekly snapshots, last week (YYYY-MM-DD)
  mvn_args, gradle_args, build_cmd, with_tests   passed to td_pipeline.py
  out          run folder (default <out-dir>/<name>_final)
  notes        free text, ignored
"""
import argparse, ast, csv, datetime as dt, os, shlex, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
ZENODO = "https://zenodo.org/records/4534110/files/{}?download=1"
STATUS_COLS = ["name", "status", "method", "weeks_ok", "weeks_planned", "validate_pass", "validate_warn",
               "validate_fail", "started", "finished", "out", "message"]


def now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def say(*a):
    print(f"[{now()}]", *a, flush=True)


def expand(p):
    return os.path.abspath(os.path.expanduser(p)) if p else p


def run(cmd, logfile=None, dry=False):
    """Run a command, show its output live and copy it into logfile."""
    say("$", " ".join(shlex.quote(c) for c in cmd))
    if dry:
        return 0, ""
    lines = []
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          bufsize=1) as p:
        lf = open(logfile, "a") if logfile else None
        for line in p.stdout:
            print(line, end="", flush=True)
            lines.append(line)
            if lf:
                lf.write(line)
        if lf:
            lf.close()
    return p.returncode, "".join(lines)


def read_repos(path):
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(l for l in f if l.strip() and not l.startswith("#"))]
    out = []
    for r in rows:
        r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
        for k in ("name", "git_url", "sonar_key"):
            if not r.get(k):
                sys.exit(f"repos.csv: row {r} has no '{k}'")
        out.append(r)
    names = [r["name"] for r in out]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        sys.exit(f"repos.csv: duplicate names {dup}")
    return out


def load_status(path):
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as f:
        return {r["name"]: r for r in csv.DictReader(f)}


def save_status(path, st):
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=STATUS_COLS)
        w.writeheader()
        for r in st.values():
            w.writerow({k: r.get(k, "") for k in STATUS_COLS})
    os.replace(tmp, path)


def server_fingerprint(url, token):
    sys.path.insert(0, HERE)
    from td_pipeline import Sonar
    s = Sonar(url, token, "td-fingerprint-probe")
    s.check()                                   # exits if SonarQube is not UP
    fp = s.analyzer_fingerprint()
    if fp.get("error") or not fp.get("rules_hash"):
        sys.exit(f"could not read the SonarQube fingerprint: {fp}")
    return fp


def run_fingerprint(out):
    p = os.path.join(out, "analysis_meta.csv")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    return rows[-1] if rows else None


def same_analyzer(a, b):
    return all(str(a.get(k)) == str(b.get(k)) for k in ("sonarqube_version", "quality_profile", "rules_hash"))


def paper_dates(path):
    """First and last date label of a paper CSV (dd/mm/yyyy or yyyy-mm-dd) and the row count."""
    with open(path, newline="") as f:
        rows = [r for r in csv.reader(f, delimiter=";")][1:]
    ds = []
    for r in rows:
        if not r:
            continue
        t = r[0].strip().split(" ")[0]
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                ds.append(dt.datetime.strptime(t, fmt).date())
                break
            except ValueError:
                pass
    return (min(ds), max(ds), len(ds)) if ds else (None, None, 0)


def free_gb(path):
    import shutil
    return shutil.disk_usage(path).free / 1e9


def week_counts(out):
    p = os.path.join(out, "status.csv")
    if not os.path.exists(p):
        return 0, 0
    with open(p) as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    return sum(r["status"] == "SUCCESS" for r in rows), len(rows)


def one_repo(r, a, fp_server):
    name = r["name"]
    clone = os.path.join(a.work, r["sonar_key"].replace(":", "_").replace("/", "_"))
    out = expand(r.get("out")) or os.path.join(a.out_dir, f"{name}_final")
    if a.test:
        out = os.path.join(a.out_dir, f"{name}_test")
    os.makedirs(out, exist_ok=True)
    log = os.path.join(out, "run_repos.log")
    res = {"name": name, "out": out, "started": now()}

    # an earlier run of this folder must have used the same analyzer
    old = run_fingerprint(out)
    if old and not same_analyzer(old, fp_server):
        res.update(status="ANALYZER_CHANGED",
                   message=f"folder was scanned with {old.get('sonarqube_version')} / "
                           f"{old.get('quality_profile')} / {old.get('rules_hash')}, server now has "
                           f"{fp_server['sonarqube_version']} / {fp_server['quality_profile']} / "
                           f"{fp_server['rules_hash']}")
        return res

    # 1. clone
    if not os.path.isdir(os.path.join(clone, ".git")):
        rc, _ = run(["git", "clone", r["git_url"], clone], log, a.dry_run)
        if rc:
            res.update(status="CLONE_FAILED", message="git clone failed")
            return res

    # 2. weeks
    pipe = [PY, os.path.join(HERE, "td_pipeline.py"), "--repo-url", r["git_url"],
            "--key", r["sonar_key"], "--work", a.work, "--out", out, "--sonar", a.sonar]
    paper = None
    if r.get("paper_csv"):
        paper = os.path.join(a.zenodo, r["paper_csv"])
        if not os.path.exists(paper):
            say("downloading", r["paper_csv"])
            if not a.dry_run:
                try:
                    urllib.request.urlretrieve(ZENODO.format(r["paper_csv"]), paper + ".part")
                    os.replace(paper + ".part", paper)
                except Exception as e:
                    res.update(status="PAPER_DOWNLOAD_FAILED", message=str(e))
                    return res
        if r.get("weeks"):     # paper repo whose rows cannot be matched to commits: real weeks
            say(f"{name}: weeks given -> regular weekly commits; the paper is only compared with")
            pipe += ["--weeks", r["weeks"]] + (["--end", r["end"]] if r.get("end") else [])
            res["method"] = "weekly_on_paper_dates"
        else:
            plan = os.path.join(a.out_dir, f"{name}_plan.csv")
            if not os.path.exists(plan):
                rc, txt = run([PY, os.path.join(HERE, "align_paper.py"), "--repo", clone,
                               "--paper", paper, "--out", plan], log, a.dry_run)
                if rc:
                    res.update(status="ALIGN_FAILED", message="align_paper.py failed - see run_repos.log")
                    return res
            if not a.dry_run:
                with open(plan) as f:
                    pr = list(csv.DictReader(f, delimiter=";"))
                # judged on Java lines (the code that is scanned); XML is counted differently by SonarQube
                jerr = [abs(float(x["java_ours"]) - float(x["java_paper"])) / max(float(x["java_paper"]), 1)
                        for x in pr if x["java_paper"] not in ("", "None")]
                err = sum(jerr) / max(len(jerr), 1)
                exact = sum(e == 0 for e in jerr) / max(len(jerr), 1)
                say(f"{name}: paper alignment - mean Java difference {err:.2%}, exact Java match {exact:.0%}")
                if err > a.max_align_error:
                    first, last, n = paper_dates(paper)
                    if a.no_fallback or not last:
                        res.update(status="ALIGN_POOR",
                                   message=f"mean Java difference {err:.2%} > {a.max_align_error:.2%} "
                                           f"(check {plan}; raise --max-align-error to accept)")
                        return res
                    # the paper rows match no commit well enough: same period, real weekly commits
                    weeks = (last - first).days // 7 + 1
                    say(f"{name}: paper rows do not match the commits (Java {err:.2%} off) -> "
                        f"FALLBACK: {weeks} real weekly commits {first} -> {last}; "
                        f"the paper is only compared with")
                    pipe += ["--weeks", str(weeks), "--end", last.isoformat()]
                    res["method"] = "weekly_on_paper_dates"
                    res["message"] = f"fallback: paper rows {err:.2%} off"
                else:
                    pipe += ["--plan-csv", plan]
                    res["method"] = "paper_aligned"
            else:
                pipe += ["--plan-csv", plan]
                res["method"] = "paper_aligned"
    else:
        pipe += ["--weeks", r.get("weeks") or "150"]
        if r.get("end"):
            pipe += ["--end", r["end"]]
        res["method"] = "weekly"
    # a started folder must keep its snapshot method (mixing paper rows and real weeks = broken lags)
    mpath = os.path.join(out, "snapshot_method.txt")
    if not a.dry_run and res.get("method"):
        if os.path.exists(mpath) and os.path.exists(os.path.join(out, "status.csv")):
            old_m = open(mpath).read().strip()
            if old_m and old_m != res["method"]:
                res.update(status="METHOD_CHANGED",
                           message=f"{out} was started as '{old_m}', now '{res['method']}' - "
                                   f"use a new out folder or delete this one")
                return res
        with open(mpath, "w") as f:
            f.write(res["method"] + "\n")
    # SonarQube refuses an analysis dated before the project's last one. So a run that starts
    # from week 1 (new folder, or any --test run) first empties the SonarQube project, which
    # may still hold analyses from an earlier test. A started folder just resumes.
    sp = os.path.join(out, "status.csv")
    if os.path.exists(sp) and not a.dry_run:
        with open(sp) as f:
            if not any(row.get("status") == "SUCCESS" for row in csv.DictReader(f, delimiter=";")):
                os.remove(sp)       # nothing collected yet (e.g. GAVE_UP before a fix): start clean
    fresh = not os.path.exists(sp)
    if a.test or fresh:
        pipe += ["--reset"]
    if a.test:
        pipe += ["--limit", str(a.test)]
    if a.give_up_after:
        pipe += ["--give-up-after", str(a.give_up_after)]
    for col, opt in (("mvn_args", "--mvn-args"), ("gradle_args", "--gradle-args"),
                     ("build_cmd", "--build-cmd")):
        if r.get(col):
            pipe += [opt, r[col]]
    if r.get("with_tests", "0") in ("1", "yes", "true"):
        pipe += ["--with-tests"]
    pipe += shlex.split(a.pipeline_args)

    # 3. pipeline (resumes the weeks it already has)
    rc, _ = run(pipe, log, a.dry_run)
    if a.dry_run:
        res.update(status="DRY_RUN")
        return res
    ok, planned = week_counts(out)
    res.update(weeks_ok=ok, weeks_planned=planned)
    new = run_fingerprint(out)
    if new and not same_analyzer(new, fp_server):
        res.update(status="ANALYZER_CHANGED", message="SonarQube changed during the run")
        return res
    if rc == 3:
        res.update(status="GAVE_UP", message=f"the first {a.give_up_after} snapshots all failed "
                                             f"(build or scan) - see {out}/build_and_scan.log")
        return res
    if rc:
        res.update(status="PIPELINE_FAILED", message=f"td_pipeline.py exit {rc} - see {log}")
        return res

    # 4. validate
    vcmd = [PY, os.path.join(HERE, "validate.py"), "--out", out, "--repo", clone]
    if paper:
        vcmd += ["--paper", paper]
    rc, txt = run(vcmd)
    with open(os.path.join(out, "validation.txt"), "w") as f:
        f.write(txt)
    summ = {}
    for line in txt.splitlines():
        if line.startswith("SUMMARY:"):
            summ = ast.literal_eval(line.split(":", 1)[1].strip())
    res.update(validate_pass=summ.get("PASS", ""), validate_warn=summ.get("WARN", ""),
               validate_fail=summ.get("FAIL", ""))
    if not summ:
        res.update(status="VALIDATE_ERROR", message="validate.py gave no SUMMARY - see validation.txt")
    elif summ.get("FAIL", 0):
        res.update(status="VALIDATE_FAILED", message="see validation.txt")
    elif planned and ok / planned < a.min_weeks_share and not a.test:
        res.update(status="TOO_FEW_WEEKS",
                   message=f"only {ok}/{planned} weeks built (< {a.min_weeks_share:.0%}); "
                           f"see build_and_scan.log")
    else:
        note = [res.get("message", "")] if res.get("message") else []
        if ok != planned:
            note.append(f"{planned - ok} of {planned} weeks failed - see build_and_scan.log")
        res.update(status="OK", message="; ".join(note))
    return res


def build_mart(repos, st, a, only=None, out=None):
    """Combined mart of all OK repos (only=None) or the mart of one repo (only=name)."""
    args = []
    for r in repos:
        s = st.get(r["name"], {})
        if s.get("status") != "OK" or (only and r["name"] != only):
            continue
        n = r["name"]
        args += ["--run", f"{n}={s['out']}",
                 "--repo", f"{n}={os.path.join(a.work, r['sonar_key'].replace(':', '_').replace('/', '_'))}"]
        plan = os.path.join(a.out_dir, f"{n}_plan.csv")
        if r.get("paper_csv"):
            args += ["--paper", f"{n}={os.path.join(a.zenodo, r['paper_csv'])}"]
            mfile = os.path.join(s["out"], "snapshot_method.txt")
            method = s.get("method") or (open(mfile).read().strip() if os.path.exists(mfile) else "") \
                or ("weekly_on_paper_dates" if r.get("weeks") else "paper_aligned")
            if os.path.exists(plan) and method == "paper_aligned":
                args += ["--plan", f"{n}={plan}"]
    if not args:
        say("no repo with status OK -> no mart")
        return
    run([PY, os.path.join(HERE, "build_mart.py"), *args, "--out", out or a.mart_out], dry=a.dry_run)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repos_csv")
    ap.add_argument("--work", default="~/td-work", help="where the git clones live")
    ap.add_argument("--out-dir", default="~/td-out", help="run folders, plans, repos_status.csv")
    ap.add_argument("--zenodo", default="~/zenodo", help="where the paper CSVs are kept")
    ap.add_argument("--mart-out", default="~/td-mart", help="combined mart of all OK repos")
    ap.add_argument("--repo-marts", default="~/td-marts",
                    help="one mart per repo: <dir>/<name>/ + <dir>/<name>.zip, made as soon as it is OK")
    ap.add_argument("--sonar", default="http://localhost:9000")
    ap.add_argument("--token", default=os.environ.get("SONAR_TOKEN"))
    ap.add_argument("--only", default="", help="comma-separated names to run (ignores 'enabled')")
    ap.add_argument("--resume-from", default=None, help="skip the rows before this name")
    ap.add_argument("--redo", action="store_true", help="run repos again even if their status is OK")
    ap.add_argument("--test", type=int, default=0,
                    help="only N weeks per repo, into <name>_test folders; no mart")
    ap.add_argument("--no-mart", action="store_true")
    ap.add_argument("--mart-only", action="store_true", help="only rebuild the mart from repos_status.csv")
    ap.add_argument("--no-fallback", action="store_true",
                    help="when paper rows do not match the commits, stop with ALIGN_POOR instead of "
                         "falling back to real weekly commits on the paper's dates")
    ap.add_argument("--give-up-after", type=int, default=5,
                    help="give a repo up when its first N snapshots all fail (0 = never)")
    ap.add_argument("--min-free-gb", type=float, default=15,
                    help="stop before a repo when less disk space than this is free")
    ap.add_argument("--max-align-error", type=float, default=0.005,
                    help="largest accepted mean Java-line difference to the paper (0.005 = 0.5%%)")
    ap.add_argument("--min-weeks-share", type=float, default=0.9,
                    help="share of planned weeks that must build for status OK")
    ap.add_argument("--pipeline-args", default="",
                    help="extra args for td_pipeline.py for every repo, e.g. \"--mvn /opt/maven/bin/mvn\"")
    ap.add_argument("--dry-run", action="store_true", help="print the commands, run nothing")
    a = ap.parse_args()
    for k in ("work", "out_dir", "zenodo", "mart_out", "repo_marts"):
        setattr(a, k, expand(getattr(a, k)))
    for d in (a.work, a.out_dir, a.zenodo):
        os.makedirs(d, exist_ok=True)

    repos = read_repos(a.repos_csv)
    # only ONE real run at a time: two runs would write into the same run folders
    if not a.test and not a.dry_run and not a.mart_only:
        import fcntl
        global _lock
        _lock = open(os.path.join(a.out_dir, ".run_repos.lock"), "w")
        try:
            fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            sys.exit("another run_repos.py full run is already going (see ~/td-out/run_repos.log). "
                     "Wait for it to finish, then run this again; --test runs are fine meanwhile.")
    status_path = os.path.join(a.out_dir, "repos_status_test.csv" if a.test else "repos_status.csv")
    st = load_status(status_path)

    if a.mart_only:
        os.makedirs(a.repo_marts, exist_ok=True)
        for r in repos:
            if st.get(r["name"], {}).get("status") == "OK":
                build_mart(repos, st, a, only=r["name"], out=os.path.join(a.repo_marts, r["name"]))
        build_mart(repos, st, a)
        return

    if not a.token:
        sys.exit("Set SONAR_TOKEN or pass --token")
    os.environ["SONAR_TOKEN"] = a.token
    fp = server_fingerprint(a.sonar, a.token)
    say(f"SonarQube {fp['sonarqube_version']}, profile '{fp['quality_profile']}', "
        f"{fp['active_rules']} rules, rules_hash {fp['rules_hash']}")
    if "comprehensive" not in str(fp["quality_profile"]).lower():
        say("WARNING: the default Java profile is not 'Sonar way comprehensive' "
            "(see RUN_GUIDE section 5.4)")
    # repos already OK must have been made with this same analyzer
    for name, s in st.items():
        if s.get("status") == "OK":
            old = run_fingerprint(s["out"])
            if old and not same_analyzer(old, fp):
                sys.exit(f"STOP: {name} was scanned with a different SonarQube / rule set "
                         f"({old.get('sonarqube_version')}, {old.get('rules_hash')}). Mixing them makes "
                         f"TD values incomparable. Restore the old server/profile or redo all repos.")
            if not old:
                say(f"note: {name} has no analysis_meta.csv - add it with fingerprint.py")

    todo = repos
    if a.resume_from:
        names = [r["name"] for r in repos]
        if a.resume_from not in names:
            sys.exit(f"--resume-from {a.resume_from} is not in {a.repos_csv}")
        todo = repos[names.index(a.resume_from):]
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    if only:
        unknown = only - {r["name"] for r in repos}
        if unknown:
            sys.exit(f"--only: {sorted(unknown)} not in {a.repos_csv}")
        todo = [r for r in todo if r["name"] in only]
    else:
        todo = [r for r in todo if r.get("enabled", "1") in ("1", "yes", "true")]

    for r in todo:
        if not a.redo and not a.test and st.get(r["name"], {}).get("status") == "OK":
            say(f"===== {r['name']}: already OK - skipped (use --redo to run again)")
            continue
        free = min(free_gb(a.out_dir), free_gb(a.work))
        if free < a.min_free_gb:
            say(f"STOP: only {free:.0f} GB free disk (< {a.min_free_gb:.0f} GB) - free space and run again")
            break
        say(f"===== {r['name']} =====")
        t0 = time.time()
        try:
            res = one_repo(r, a, fp)
        except KeyboardInterrupt:
            say("stopped by user - run the same command again to continue")
            raise SystemExit(1)
        except Exception as e:
            res = {"name": r["name"], "status": "ERROR", "message": repr(e)}
        res["finished"] = now()
        if not a.dry_run:
            # re-read first: a --test run in another terminal may have written other rows meanwhile
            st = load_status(status_path)
            st[r["name"]] = {**st.get(r["name"], {}), **res}
            save_status(status_path, st)
        say(f"===== {r['name']}: {res['status']} {res.get('message', '')} "
            f"({(time.time() - t0) / 3600:.1f} h)")
        if res["status"] == "OK" and not a.test and not a.dry_run:
            try:                                  # this repo's own mart, right away
                os.makedirs(a.repo_marts, exist_ok=True)
                build_mart(repos, st, a, only=r["name"], out=os.path.join(a.repo_marts, r["name"]))
            except Exception as e:
                say(f"{r['name']}: could not build its own mart: {e!r}")
        if res["status"] == "ANALYZER_CHANGED":
            say("STOP: SonarQube or its rule set changed - no further repos are run")
            break

    print()
    print(f"{'name':<16}{'status':<20}{'method':<23}{'weeks':<10}{'validate P/W/F':<16}message")
    for r in repos:
        s = st.get(r["name"])
        if s:
            print(f"{s['name']:<16}{s.get('status', ''):<20}{s.get('method', ''):<23}"
                  f"{str(s.get('weeks_ok', ''))}/{str(s.get('weeks_planned', '')):<7}"
                  f"{s.get('validate_pass', '')}/{s.get('validate_warn', '')}/{s.get('validate_fail', ''):<11}"
                  f"{s.get('message', '')}")
    print(f"status file: {status_path}")

    if not a.no_mart and not a.test:
        build_mart(repos, st, a)


if __name__ == "__main__":
    main()
