"""
td_pipeline.py - one command that rebuilds the Tsoukalas et al. (2020) dataset
for one repo, at PROJECT, MODULE and FILE level.

For every weekly snapshot (oldest first) it:
  1. checks out the last commit before that week's date      (git)
  2. builds it with JDK 8, tests skipped                      (Maven 3.6.3)
  3. analyses it, back-dated to that week                     (sonar-scanner -> SonarQube)
  4. saves project + file measures right away                 (SonarQube Web API)
  5. runs CKJM Extended on the compiled classes               (run_ckjm.py)
Then it joins everything into:
  <out>/project_level.csv   one row per week
  <out>/module_level.csv    one row per module per week
  <out>/file_level.csv      one row per .java file per week

Needs run_ckjm.py and ckjm_ext.jar in the same folder as this file.
See RUN_GUIDE.md for setup.
"""
import argparse, csv, datetime as dt, glob, json, os, re, shutil, subprocess, sys, time
import numpy as np
import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_ckjm as ck  # noqa: E402
import preflight as pf  # noqa: E402
import extras as ex  # noqa: E402

SONAR_METRICS = [
    "bugs", "vulnerabilities", "code_smells", "sqale_index",
    "reliability_remediation_effort", "security_remediation_effort",
    "ncloc", "lines", "comment_lines", "complexity", "cognitive_complexity",
    "duplicated_blocks", "duplicated_lines", "uncovered_lines", "lines_to_cover",
    "coverage", "classes", "functions", "files", "statements",
    "violations", "blocker_violations", "critical_violations", "major_violations",
    "minor_violations", "info_violations",
    "sqale_debt_ratio", "sqale_rating", "reliability_rating", "security_rating",
    "comment_lines_density", "duplicated_lines_density",
]
# metrics that can be summed from files to a module (ratios/ratings cannot)
SUMMABLE = ["bugs", "vulnerabilities", "code_smells", "sqale_index",
            "reliability_remediation_effort", "security_remediation_effort",
            "ncloc", "lines", "comment_lines", "complexity", "cognitive_complexity",
            "duplicated_blocks", "duplicated_lines", "uncovered_lines",
            "lines_to_cover", "classes", "functions", "statements", "violations"]
CK_KEYS = ck.METRICS + ck.EXTRA


# ---------------------------------------------------------------- helpers
def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


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


def sh(cmd, cwd, env=None, logfile=None):
    p = subprocess.run(cmd, cwd=cwd, shell=True, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if logfile:
        with open(logfile, "a") as f:
            f.write(f"\n$ {cmd}\n{p.stdout}\n")
    return p


def chunks(lst, n=15):                      # SonarQube allows max 15 metric keys per call
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# Main-code source roots. Old Apache projects (commons-io before ~2010) use src/java.
MAIN_ROOTS = ("/src/main/java/", "/src/java/")


def module_and_rel(path):
    """'retrofit-converters/gson/src/main/java/retrofit2/X.java'
       -> ('retrofit-converters/gson', 'retrofit2/X.java')"""
    path = path.replace("\\", "/")
    module = path.split("/src/")[0] if "/src/" in path else "."
    rel = path
    for root in MAIN_ROOTS:              # src/main/java (Maven 2+) or src/java (old Apache layout)
        if root in "/" + path:
            rel = ("/" + path).split(root, 1)[1]
            break
    return module, rel


def read_dates(csv_path):
    """Week dates from the authors' Zenodo CSV (first column)."""
    df = pd.read_csv(csv_path, sep=";")
    col = df.columns[0]
    s = df[col].astype(str)
    dates = pd.to_datetime(s, dayfirst=s.str.contains("/").any())
    return sorted(d.date() for d in dates)


NONFILE_KEYS = ["code_smells", "sqale_index", "bugs", "reliability_remediation_effort",
                "vulnerabilities", "security_remediation_effort", "violations",
                "blocker_violations", "critical_violations", "major_violations",
                "minor_violations", "info_violations"]


def effort_minutes(txt, hours_per_day=8):
    """'1d2h5min' -> minutes (SonarQube uses 8-hour days)"""
    if not txt:
        return 0
    m = re.findall(r"(\d+)\s*(d|h|min)", str(txt))
    return sum(int(v) * {"d": hours_per_day * 60, "h": 60, "min": 1}[u] for v, u in m)


# ---------------------------------------------------------------- SonarQube API
class Sonar:
    def __init__(self, url, token, key):
        self.url, self.key = url.rstrip("/"), key
        self.s = requests.Session()
        self.s.auth = (token, "")

    def get(self, path, **params):
        r = self.s.get(self.url + path, params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    def post(self, path, **params):
        r = self.s.post(self.url + path, params=params, timeout=60)
        return r

    def check(self):
        sysst = self.get("/api/system/status")
        st = sysst["status"]
        try:
            self.major = int(str(sysst.get("version", "99")).split(".")[0])
        except ValueError:
            self.major = 99
        if st != "UP":
            sys.exit(f"SonarQube status is {st}, wait until it is UP")
        valid, page = set(), 1
        while True:
            r = self.get("/api/metrics/search", ps=500, p=page)
            valid |= {m["key"] for m in r["metrics"]}
            total = r.get("total") or r.get("paging", {}).get("total", 0)
            if not r["metrics"] or page * 500 >= total:
                return valid
            page += 1

    def set_housekeeping(self):
        # Analyses are back-dated to 2015-2018, i.e. "older than 5 years".
        # With the default settings SonarQube would thin or DELETE them.
        for k, v in [("sonar.dbcleaner.weeksBeforeKeepingOnlyOneSnapshotByMonth", 5000),
                     ("sonar.dbcleaner.weeksBeforeKeepingOnlyAnalysesWithVersion", 5000),
                     ("sonar.dbcleaner.weeksBeforeDeletingAllSnapshots", 10000)]:
            r = self.post("/api/settings/set", key=k, value=v)
            log("housekeeping", k, "=", v, "->", r.status_code)

    def delete_project(self):
        r = self.post("/api/projects/delete", project=self.key)
        log("deleted old SonarQube project" if r.ok else "no old project to delete")

    def wait_task(self, report_task_file, timeout=1800):
        task_id = None
        with open(report_task_file) as f:
            for line in f:
                if line.startswith("ceTaskId="):
                    task_id = line.strip().split("=", 1)[1]
        t0 = time.time()
        while time.time() - t0 < timeout:
            task = self.get("/api/ce/task", id=task_id)["task"]
            st = task["status"]
            if st in ("SUCCESS", "FAILED", "CANCELED"):
                self.last_error = task.get("errorMessage", "")
                return st
            time.sleep(3)
        return "TIMEOUT"

    def project_measures(self, metrics):
        out = {}
        for part in chunks(metrics):
            r = self.get("/api/measures/component", component=self.key,
                         metricKeys=",".join(part))
            for m in r["component"]["measures"]:
                out[m["metric"]] = m.get("value")
        return out

    def file_measures(self, metrics):
        files = {}
        for part in chunks(metrics):
            page = 1
            while True:
                r = self.get("/api/measures/component_tree", component=self.key,
                             qualifiers="FIL", metricKeys=",".join(part), ps=500, p=page)
                for c in r["components"]:
                    row = files.setdefault(c["path"], {})
                    for m in c["measures"]:
                        row[m["metric"]] = m.get("value")
                if page * 500 >= r["paging"]["total"]:
                    break
                page += 1
        return files

    def nonfile_issues(self):
        """Open issues raised on a folder/package or on the project itself (not on a file).
        Some rules (e.g. 'packages need package-info.java') do this. They count in the
        project totals, so we add them to the right module. Returns {module: {metric: value}}"""
        out, page = {}, 1
        while True:
            r = self.get("/api/issues/search", componentKeys=self.key, resolved="false",
                         ps=500, p=page, additionalFields="_all")
            quals = {c["key"]: (c.get("qualifier"), c.get("path", "")) for c in r.get("components", [])}
            for iss in r.get("issues", []):
                q, path = quals.get(iss["component"], ("FIL", ""))
                if q in ("FIL", "UTS"):
                    continue
                mod = module_and_rel(path)[0] if (path and q != "TRK") else "(project)"
                d = out.setdefault(mod, {k: 0 for k in NONFILE_KEYS})
                t, eff = iss.get("type"), effort_minutes(iss.get("effort") or iss.get("debt"))
                key = {"CODE_SMELL": ("code_smells", "sqale_index"), "BUG": ("bugs", "reliability_remediation_effort"),
                       "VULNERABILITY": ("vulnerabilities", "security_remediation_effort")}.get(t)
                if not key:
                    continue
                d[key[0]] += 1; d[key[1]] += eff; d["violations"] += 1
                sev = (iss.get("severity") or "").lower()
                if f"{sev}_violations" in d:
                    d[f"{sev}_violations"] += 1
            total = r.get("paging", {}).get("total", r.get("total", 0))
            if page * 500 >= min(total, 10000):
                return out
            page += 1

    def analyzer_fingerprint(self):
        """SonarQube version + the Java quality profile used + a hash of its active rules.
        Equal hash = identical rule set, so TD values are comparable across snapshots/runs."""
        import hashlib, json
        fp = {"sonarqube_version": None, "quality_profile": None, "quality_profile_key": None,
              "active_rules": None, "rules_hash": None}
        try:
            fp["sonarqube_version"] = self.s.get(self.url + "/api/server/version", timeout=30).text.strip()
            q = []
            try:      # the profile used by this project (404 if the project does not exist yet)
                q = self.get("/api/qualityprofiles/search", language="java", project=self.key).get("profiles") or []
            except requests.HTTPError:
                pass
            if not q:  # new project -> it will get the default Java profile
                q = [p for p in self.get("/api/qualityprofiles/search", language="java")["profiles"]
                     if p.get("isDefault")]
            if q:
                fp["quality_profile"], fp["quality_profile_key"] = q[0]["name"], q[0]["key"]
                rules, page = [], 1
                while True:
                    r = self.get("/api/rules/search", qprofile=q[0]["key"], activation="true",
                                 ps=500, p=page, f="severity")
                    rules += [(x["key"], x.get("severity", "")) for x in r.get("rules", [])]
                    if page * 500 >= r.get("total", 0):
                        break
                    page += 1
                fp["active_rules"] = len(rules)
                fp["rules_hash"] = hashlib.sha256(json.dumps(sorted(rules)).encode()).hexdigest()[:16]
        except Exception as e:
            fp["error"] = str(e)
        return fp

    def history(self, metrics):
        """Project history as SonarQube stored it - used only as a cross-check."""
        hist = {}
        for part in chunks(metrics):
            page = 1
            while True:
                r = self.get("/api/measures/search_history", component=self.key,
                             metrics=",".join(part), ps=1000, p=page)
                for m in r["measures"]:
                    for h in m["history"]:
                        hist.setdefault(h["date"][:10], {})[m["metric"]] = h.get("value")
                if page * 1000 >= r["paging"]["total"]:
                    break
                page += 1
        return hist


# ---------------------------------------------------------------- one snapshot
GRADLE_INIT = """
// added by td_pipeline: copies each Java project's libraries to build/ckjm-deps
allprojects {
    afterEvaluate { p ->
        if (p.plugins.hasPlugin('java')) {
            p.tasks.create('ckjmDeps', Copy) {
                def names = %s
                for (n in names) {
                    def c = p.configurations.findByName(n)
                    if (c != null) { from({ c }) }
                }
                into "${p.buildDir}/ckjm-deps"
            }
        }
    }
}
"""


SNAP_RE = re.compile(r"<([A-Za-z0-9_.\-]+\.version)>([^<]+?)-SNAPSHOT</\1>")


def fix_snapshot_deps(repo, logfile):
    """Old commits often depend on pre-release libraries ('3.0.0-SNAPSHOT') that were
    deleted from the internet later. Use the released version instead ('3.0.0').
    Only <xxx.version> properties are changed - the project's own <version> stays."""
    changed = []
    poms = glob.glob(os.path.join(repo, "**/pom.xml"), recursive=True)
    # the repo's OWN version (e.g. zxing.version = 3.3.4-SNAPSHOT = the version being built) must
    # stay: its modules depend on each other through it, and "3.3.4" may never have been released
    own = set()
    for pom in poms:
        with open(pom, encoding="utf-8", errors="replace") as f:
            own |= set(re.findall(r"<version>([^<$]+-SNAPSHOT)</version>", f.read()))

    def swap(m):
        if f"{m.group(2)}-SNAPSHOT" in own:
            return m.group(0)
        return f"<{m.group(1)}>{m.group(2)}</{m.group(1)}>"
    for pom in poms:
        with open(pom, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        new = SNAP_RE.sub(swap, txt)
        if new != txt:
            changed += [f"{m.group(1)}={m.group(2)}" for m in SNAP_RE.finditer(txt)
                        if f"{m.group(2)}-SNAPSHOT" not in own]
            with open(pom, "w", encoding="utf-8") as f:
                f.write(new)
    if changed:
        with open(logfile, "a") as f:
            f.write(f"\n[td_pipeline] SNAPSHOT -> release: {sorted(set(changed))}\n")
        log("   snapshot deps -> release:", ", ".join(sorted(set(changed))))


def build(repo, a, logfile, settings=None, sha=None):
    settings = settings or {}
    jhome = a.java8_home
    if sha:
        try:
            lv = pf.java_level_of(repo, sha)
        except Exception:
            lv = None
        j17 = os.path.dirname(os.path.dirname(a.java17))
        if lv and lv > 8 and os.path.isdir(j17):
            jhome = j17                    # the pom asks for Java 9+: JDK 8 cannot compile it
            log(f"   pom asks for Java {lv} -> building with {j17}")
    env = dict(os.environ, JAVA_HOME=jhome,
               PATH=f"{jhome}/bin:{os.path.dirname(a.mvn)}:{os.environ['PATH']}")
    extra = " ".join(f"-D{k}={v}" for k, v in settings.get("mvn_props", {}).items())
    if a.build_cmd:
        cmd = a.build_cmd
    elif os.path.exists(os.path.join(repo, "pom.xml")):
        if not a.keep_snapshots:
            fix_snapshot_deps(repo, logfile)
        # -DskipTests only exists since surefire 2.4; older poms (commons-io 2007-2008 uses 2.3)
        # still RUN the tests, and one flaky test then fails the build. failure.ignore covers them.
        cmd = (f"{a.mvn} -B -q install -DskipTests -Dmaven.test.failure.ignore=true "
               "-Dmaven.test.error.ignore=true -Dcheckstyle.skip=true "
               "-Danimal.sniffer.skip=true -Dmaven.javadoc.skip=true -Denforcer.skip=true "
               "-Dgpg.skip=true -Drat.skip=true "
               "org.apache.maven.plugins:maven-dependency-plugin:3.6.1:copy-dependencies "
               f"-DincludeScope={'test' if a.with_tests else 'compile'} "
               f"-DoutputDirectory=target/ckjm-deps "
               # okhttp 2016-2018 picks this version in profiles that match only OLD JDK 8 updates;
               # with today's JDK 8 the property is undefined and Maven refuses the pom
               "-Dalpn.jdk8.version=8.1.13.v20181017 "
               f"{extra} {a.mvn_args}")
    elif glob.glob(os.path.join(repo, "build.gradle*")):
        # Gradle project (like kafka): the authors' "Perform Gradle Analysis" step
        names = (["compileClasspath", "compile", "testCompileClasspath", "testCompile"]
                 if a.with_tests else ["compileClasspath", "compile"])
        init = os.path.join(repo, ".td-ckjm-deps.gradle")
        with open(init, "w") as f:
            f.write(GRADLE_INIT % ("[" + ", ".join(f"'{n}'" for n in names) + "]"))
        gradle = "./gradlew" if os.path.exists(os.path.join(repo, "gradlew")) else a.gradle
        tasks = "compileJava compileTestJava" if a.with_tests else "compileJava"
        cmd = (f"{gradle} -q --no-daemon --init-script .td-ckjm-deps.gradle "
               f"{tasks} ckjmDeps -x test {a.gradle_args}")
    else:
        log("   no pom.xml or build.gradle found")
        return False
    maven = os.path.exists(os.path.join(repo, "pom.xml")) and not a.build_cmd
    # test code is not measured; when its test code uses classes newer JDK 8 updates removed
    # (dubbo: com.sun.org.apache.regexp.internal) the preflight says so and tests are not compiled.
    # Both ways are tried, the preflight's choice first.
    tries = [cmd]
    if maven and not a.with_tests:
        skip = cmd + " -Dmaven.test.skip=true"
        tries = [skip, cmd] if settings.get("skip_test_compile") else [cmd, skip]
    for k, c in enumerate(tries):
        if k:
            log("   build failed - trying again " + ("WITHOUT" if "maven.test.skip" in c else "WITH")
                + " compiling tests")
        if sh(c, repo, env, logfile).returncode == 0:
            return True
    return False


def lib_patterns(repo):
    pats = [p for p in ["**/target/ckjm-deps/*.jar", "**/build/ckjm-deps/*.jar"]
            if glob.glob(os.path.join(repo, p), recursive=True)]
    return ",".join(pats) or "**/target/ckjm-deps/*.jar"


def analysis_date(week, attempt):
    """First try: the plain date (local midnight, as before). A retry: the same day plus `attempt`
    minutes. A failed try can still leave a saved analysis at that time, and SonarQube only accepts
    a NEWER date ("It's only possible to rebuild the past in a chronological order")."""
    if not attempt:
        return week.isoformat()
    t = dt.datetime.combine(week, dt.time(0, min(attempt, 59))).astimezone()
    return t.strftime("%Y-%m-%dT%H:%M:%S%z")


def main_source_roots(repo):
    """The main-code folders that are scanned (same list for SonarQube and the Java Driller)."""
    return sorted({os.path.relpath(d, repo) for pat in ("**/src/main/java", "**/src/java")
                   for d in glob.glob(os.path.join(repo, pat), recursive=True)
                   if "/test/" not in d.replace("\\", "/")})


def driller_classpath(a=None):
    """Class path of the Java Driller: --driller-cp, or ~/td-tools/driller + lib/javaparser-core-*.jar."""
    cp = getattr(a, "driller_cp", None) if a else None
    if cp:
        return cp
    d = os.path.join(HERE, "driller")
    jars = sorted(glob.glob(os.path.join(HERE, "lib", "javaparser-core-*.jar")))
    if os.path.exists(os.path.join(d, "JavaDriller.class")) and jars:
        return os.pathsep.join([d, jars[-1]])
    return None


JD_VERSION_COL = "noncohesive_classes"     # newest raw_jd_file.csv column


def driller_upgrade(out):
    """raw_jd_*.csv written by an older Java Driller (fewer columns) cannot be appended to:
    move them aside (*.v1.bak) so every snapshot is drilled again with the new version."""
    p = os.path.join(out, "raw_jd_file.csv")
    if not os.path.exists(p):
        return False
    with open(p) as f:
        head = f.readline()
    if JD_VERSION_COL in head:
        return False
    for n in ("raw_jd_file.csv", "raw_jd_deps.csv"):
        q = os.path.join(out, n)
        if os.path.exists(q):
            os.replace(q, q + ".v1.bak")
    log("   Java Driller output was from an older version -> moved to *.v1.bak, drilling again")
    return True


def run_driller(repo, week, sha, out, cp, java, logfile=None):
    """Java Driller (JavaParser): fan-in/out, coupling, cohesion, has-test per file + dependency
    edges -> appends raw_jd_file.csv / raw_jd_deps.csv. Never fails the snapshot."""
    roots = main_source_roots(repo)
    if not roots:
        return False
    driller_upgrade(out)
    cmd = [java, "-Xss8m", "-cp", cp, "JavaDriller", "--root", repo, "--roots", ",".join(roots),
           "--week", str(week), "--sha", sha, "--out", out]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if logfile:
        with open(logfile, "a") as f:
            f.write(f"\n$ JavaDriller {week} {sha[:10]}\n{p.stdout}{p.stderr[-3000:]}\n")
    if p.returncode != 0:
        log("   Java Driller failed (snapshot kept) - see build_and_scan.log")
        return False
    return True


def scan(repo, week, sha, a, logfile, attempt=0):
    srcs = main_source_roots(repo)
    bins = [os.path.relpath(d, repo) for d in ck.find_class_dirs(repo)]
    if not srcs or not bins:
        return "NO_SOURCES"
    shutil.rmtree(os.path.join(repo, ".scannerwork"), ignore_errors=True)
    props = {
        "sonar.host.url": a.sonar,
        ("sonar.login" if getattr(sonar, "major", 99) < 10 else "sonar.token"): a.token,
        "sonar.projectKey": a.key, "sonar.projectName": a.key,
        "sonar.projectVersion": sha[:10], "sonar.projectDate": analysis_date(week, attempt),
        "sonar.sources": ",".join(srcs), "sonar.java.binaries": ",".join(bins),
        "sonar.java.libraries": lib_patterns(repo),
        "sonar.sourceEncoding": "UTF-8", "sonar.scm.disabled": "true",
        # Java only: old projects keep package.html etc. next to the code, and newer SonarQube
        # versions would count them in ncloc/files (the paper's data is Java only).
        "sonar.inclusions": "**/*.java",
    }
    if a.with_tests:
        tests = sorted({os.path.relpath(d, repo) for d in
                        glob.glob(os.path.join(repo, "**/src/test/java"), recursive=True)})
        tbins = sorted({os.path.relpath(d, repo) for pat in
                        ["**/target/test-classes", "**/build/classes/java/test", "**/build/classes/test"]
                        for d in glob.glob(os.path.join(repo, pat), recursive=True)})
        if tests:
            props["sonar.tests"] = ",".join(tests)
        if tbins:
            props["sonar.java.test.binaries"] = ",".join(tbins)
            props["sonar.java.test.libraries"] = lib_patterns(repo)
    cmd = a.scanner + " " + " ".join(f'-D{k}="{v}"' for k, v in props.items())
    if sh(cmd, repo, None, logfile).returncode != 0:
        return "SCAN_FAILED"
    return sonar.wait_task(os.path.join(repo, ".scannerwork", "report-task.txt"))


# ---------------------------------------------------------------- main
def main():
    global sonar
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-url", required=True)
    ap.add_argument("--key", required=True, help="SonarQube project key, e.g. square:retrofit")
    ap.add_argument("--dates-from", help="authors' Zenodo CSV -> use exactly their weeks")
    ap.add_argument("--plan-csv", help="week;sha file from align_paper.py -> analyse exactly these commits")
    ap.add_argument("--weeks", type=int, default=150, help="if no --dates-from")
    ap.add_argument("--end", help="last week YYYY-MM-DD (if no --dates-from)")
    ap.add_argument("--limit", type=int, default=0, help="only the first N weeks (quick test)")
    ap.add_argument("--work", required=True, help="folder for the git clone")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sonar", default="http://localhost:9000")
    ap.add_argument("--token", default=os.environ.get("SONAR_TOKEN"))
    ap.add_argument("--java8-home", default="/usr/lib/jvm/java-8-openjdk-amd64")
    ap.add_argument("--java17", default="/usr/lib/jvm/java-17-openjdk-amd64/bin/java")
    ap.add_argument("--mvn", default="/opt/maven-3.6.3/bin/mvn")
    ap.add_argument("--scanner", default="/opt/sonar-scanner/bin/sonar-scanner")
    ap.add_argument("--mvn-args", default="", help="extra Maven args, e.g. \"-pl '!samples'\"")
    ap.add_argument("--build-cmd", default=None, help="replace the Maven command (Gradle etc.)")
    ap.add_argument("--retries", type=int, default=5,
                    help="re-send an analysis this many times if SonarQube's server fails to process it")
    ap.add_argument("--keep-snapshots", action="store_true",
                    help="do NOT replace -SNAPSHOT library versions with the released version")
    ap.add_argument("--gradle", default="gradle", help="Gradle to use when the repo has no ./gradlew")
    ap.add_argument("--gradle-args", default="", help="extra Gradle args")
    ap.add_argument("--with-tests", action="store_true",
                    help="also send test code to SonarQube (like the authors' Maven scan); "
                         "ncloc stays main-code only, but test issues count in code_smells/TD")
    ap.add_argument("--driller-cp", default=None,
                    help="class path of the Java Driller (default: ~/td-tools/driller + lib/javaparser-core-*.jar "
                         "when both exist; otherwise the step is skipped)")
    ap.add_argument("--give-up-after", type=int, default=0,
                    help="stop (exit code 3) if the first N snapshots all fail - a repo that does not "
                         "build should not burn hours; 0 = never")
    ap.add_argument("--reset", action="store_true",
                    help="delete the SonarQube project and start again")
    a = ap.parse_args()
    if not a.token:
        sys.exit("Set SONAR_TOKEN or pass --token")

    os.makedirs(a.out, exist_ok=True)
    logfile = os.path.join(a.out, "build_and_scan.log")
    sonar = Sonar(a.sonar, a.token, a.key)
    valid = sonar.check()
    missing = [m for m in SONAR_METRICS if m not in valid]
    metrics = [m for m in SONAR_METRICS if m in valid]
    if missing:
        log("these metrics do not exist in your SonarQube and are skipped:", missing)
    sonar.set_housekeeping()
    os.makedirs(a.out, exist_ok=True)
    fp = sonar.analyzer_fingerprint()
    with open(os.path.join(a.out, "analysis_meta.csv"), "a") as f:
        if f.tell() == 0:
            f.write("run_started;sonarqube_version;quality_profile;active_rules;rules_hash\n")
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')};{fp['sonarqube_version']};{fp['quality_profile']};"
                f"{fp['active_rules']};{fp['rules_hash']}\n")
    log("analyzer:", fp)

    # ---- clone + choose weekly commits
    repo = os.path.join(a.work, a.key.replace(":", "_").replace("/", "_"))
    os.makedirs(a.work, exist_ok=True)
    if not os.path.isdir(os.path.join(repo, ".git")):
        log("cloning", a.repo_url)
        if sh(f"git clone {a.repo_url} {repo}", a.work).returncode != 0:
            sys.exit("git clone failed")
    branch = main_branch(repo)
    log("branch:", branch)
    if a.plan_csv:
        weeks = []
    elif a.dates_from:
        weeks = read_dates(a.dates_from)
    else:
        end = dt.date.fromisoformat(a.end) if a.end else dt.date.today()
        weeks = [end - dt.timedelta(weeks=i) for i in range(a.weeks)][::-1]
    if a.limit:
        weeks = weeks[:a.limit]

    plan = []
    if a.plan_csv:
        pc = pd.read_csv(a.plan_csv, sep=";")
        weeks = []
        plan = [(pd.to_datetime(w).date(), sh_) for w, sh_ in zip(pc["week"], pc["sha"])]
        if a.limit:
            plan = plan[:a.limit]
    for w in weeks:
        sha = sh(f"git rev-list -n 1 --first-parent --before='{w} 00:00' {branch}",
                 repo).stdout.strip()
        if sha:
            plan.append((w, sha))
    bad = [(w, s) for w, s in plan if not re.fullmatch(r"[0-9a-f]{40}", str(s))]
    if not plan or bad:
        sys.exit(f"no valid weekly commits found (branch {branch}); bad entries: {bad[:3]}")
    log(f"{len(plan)} weeks planned: {plan[0][0]} -> {plan[-1][0]}")
    # ---- preflight: what do these commits need to build? (once per run folder)
    settings_path = os.path.join(a.out, "build_settings.json")
    settings = {}
    try:
        if os.path.exists(settings_path) and not a.reset:
            with open(settings_path) as f:
                settings = json.load(f)
            log("preflight: using", settings_path)
        else:
            settings, notes = pf.run(repo, [s_ for _, s_ in plan], a.out)
            for n in notes:
                log(n)
    except Exception as e:                      # a preflight problem must never stop the run
        log("preflight skipped:", repr(e))
    pd.DataFrame(plan, columns=["week", "sha"]).to_csv(
        os.path.join(a.out, "weeks_plan.csv"), sep=";", index=False)

    # ---- resume support
    status_path = os.path.join(a.out, "status.csv")
    done = set()
    if a.reset:
        sonar.delete_project()
        for f in glob.glob(os.path.join(a.out, "raw_*.csv")) + [status_path]:
            os.remove(f) if os.path.exists(f) else None
    elif os.path.exists(status_path):
        done = set(pd.read_csv(status_path, sep=";")["week"].astype(str))

    raw = {n: os.path.join(a.out, f"raw_{n}.csv") for n in
           ["sonar_project", "sonar_file", "sonar_nonfile", "ck_class", "ck_file", "ck_module", "ck_project"]
           + EXTRA_RAW}

    def append(name, rows, cols):
        new = not os.path.exists(raw[name])
        with open(raw[name], "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
            if new:
                w.writeheader()
            w.writerows(rows)

    def status(week, sha, st):
        new = not os.path.exists(status_path)
        with open(status_path, "a") as f:
            if new:
                f.write("week;sha;status\n")
            f.write(f"{week};{sha};{st}\n")

    # ---- loop over weeks, oldest first
    any_ok = os.path.exists(status_path) and \
        (pd.read_csv(status_path, sep=";")["status"] == "SUCCESS").any()
    fails = 0

    def failed():
        nonlocal_fails[0] += 1
        if a.give_up_after and not any_ok and nonlocal_fails[0] >= a.give_up_after:
            log(f"GIVING UP: the first {nonlocal_fails[0]} snapshots all failed - see build_and_scan.log")
            sys.exit(3)
    nonlocal_fails = [fails]

    for i, (week, sha) in enumerate(plan, 1):
        if str(week) in done:
            continue
        log(f"[{i}/{len(plan)}] {week} {sha[:10]}")
        sh(f"git checkout -f -q {sha} && git clean -fdxq", repo)

        log_start = os.path.getsize(logfile) if os.path.exists(logfile) else 0
        if not build(repo, a, logfile, settings, sha):
            try:                                # why it failed -> build_errors.csv
                with open(logfile, errors="replace") as f:
                    f.seek(log_start)
                    kind, line = pf.classify(f.read()[-200000:])
                ep = os.path.join(a.out, "build_errors.csv")
                with open(ep, "a", newline="") as f:
                    w = csv.writer(f, delimiter=";")
                    if f.tell() == 0:
                        w.writerow(["week", "sha", "kind", "first_error"])
                    w.writerow([week, sha, kind, line])
                log(f"   ({kind}) {line[:160]}")
            except Exception:
                pass
            log("   build FAILED - see build_and_scan.log"); status(week, sha, "BUILD_FAILED"); failed(); continue
        st = scan(repo, week, sha, a, logfile)
        tries = 0
        while st == "FAILED" and tries < a.retries:   # SonarQube server-side failure: try again
            tries += 1
            err = [" ".join((getattr(sonar, "last_error", "") or "").split())]   # whole message, one line
            err = err if err[0] else []
            wait = int(os.environ.get("TD_RETRY_WAIT", 15)) * 2 ** (tries - 1)   # 15, 30, 60, 120, 240 s
            log(f"   SonarQube processing FAILED ({err[0][:400] if err else 'no message'}) "
                f"- retry {tries}/{a.retries} in {wait}s")
            time.sleep(wait)
            st = scan(repo, week, sha, a, logfile, attempt=tries)
        if st != "SUCCESS":
            log("   analysis", st); status(week, sha, st); failed(); continue

        any_ok = True
        base = {"week": week, "sha": sha}
        append("sonar_project", [{**base, **sonar.project_measures(metrics)}],
               ["week", "sha"] + metrics)
        frows = []
        for path, vals in sonar.file_measures(metrics).items():
            mod, rel = module_and_rel(path)
            frows.append({**base, "module": mod, "file": rel, "path": path, **vals})
        append("sonar_file", frows, ["week", "sha", "module", "file", "path"] + metrics)
        try:
            nf = sonar.nonfile_issues()
            append("sonar_nonfile", [{**base, "module": m, **v} for m, v in nf.items()],
                   ["week", "sha", "module"] + NONFILE_KEYS)
        except Exception as e:  # never stop the run for this
            log("   could not read folder-level issues:", e)

        # CKJM on the same compiled classes
        class_dirs = ck.find_class_dirs(repo)
        class_files, owner = [], {}
        for d in class_dirs:
            for f in glob.glob(os.path.join(d, "**/*.class"), recursive=True):
                if os.path.basename(f) not in ("module-info.class", "package-info.class"):
                    class_files.append(f); owner[f] = d
        jars = sorted(glob.glob(os.path.join(repo, "**/target/ckjm-deps/*.jar"), recursive=True)
                      + glob.glob(os.path.join(repo, "**/build/ckjm-deps/*.jar"), recursive=True))
        out, dropped = ck.run_ckjm(os.path.join(HERE, "ckjm_ext.jar"), class_files,
                                   class_dirs + jars, a.java17)
        rows = ck.parse(out)
        fq_mod = {os.path.relpath(f, d)[:-6].replace(os.sep, "."): ck.module_of(d, repo)
                  for f, d in owner.items()}
        for r in rows:
            r.update(base, module=fq_mod.get(r["class"], "?"),
                     file=r["class"].split("$")[0].replace(".", "/") + ".java")
        append("ck_class", rows, ["week", "sha", "module", "file", "class"] + CK_KEYS)

        def group(keyf):
            g = {}
            for r in rows:
                g.setdefault(keyf(r), []).append(r)
            return g
        append("ck_file", [{**base, "module": m, "file": f, "n_classes": len(rs),
                            **ck.avg_rows(rs, CK_KEYS)}
                           for (m, f), rs in group(lambda r: (r["module"], r["file"])).items()],
               ["week", "sha", "module", "file", "n_classes"] + CK_KEYS)
        append("ck_module", [{**base, "module": m, "n_classes": len(rs),
                              **ck.avg_rows(rs, CK_KEYS)}
                             for m, rs in group(lambda r: r["module"]).items()],
               ["week", "sha", "module", "n_classes"] + CK_KEYS)
        append("ck_project", [{**base, "n_classes": len(rows), "n_dropped": len(dropped),
                               **(ck.avg_rows(rows, CK_KEYS) if rows else {})}],
               ["week", "sha", "n_classes", "n_dropped"] + CK_KEYS)
        if len(dropped) > 0.05 * max(len(class_files), 1):
            log(f"   WARNING CKJM dropped {len(dropped)}/{len(class_files)} classes")
        prev_sha = plan[i - 2][1] if i > 1 else None
        modules = {r["module"] for r in frows} | {r["module"] for r in rows}
        write_extras(repo, week, sha, prev_sha, modules, append)
        jd_cp = driller_classpath(a)
        if jd_cp:
            run_driller(repo, week, sha, a.out, jd_cp, a.java17, logfile)
        status(week, sha, "SUCCESS")
        log(f"   ok: {len(frows)} files, {len(rows)} classes")

    # ---- cross-check: what SonarQube kept in its own history
    hist = sonar.history(metrics)
    pd.DataFrame.from_dict(hist, orient="index").sort_index().to_csv(
        os.path.join(a.out, "sonar_history_check.csv"), sep=";", index_label="date")

    if not os.path.exists(os.path.join(a.out, "raw_sonar_project.csv")):
        log("no snapshot was collected - nothing to join (see build_errors.csv)")
        sys.exit(3)
    join_levels(a.out)
    try:                                   # history / lineage / window features + targets
        import history
        history.run(repo, a.out)
    except Exception as e:
        log("history step failed (run it alone: python history.py --repo ... --out ...):", e)


EXTRA_RAW = ["halstead_file", "halstead_module", "halstead_project",
             "git_file", "git_module", "git_project"]
EXTRA_COLS = {
    "halstead_file": ["week", "sha", "module", "file"] + ex.H_COLS,
    "halstead_module": ["week", "sha", "module"] + ex.H_COLS + ["halstead_volume_sum", "halstead_files"],
    "halstead_project": ["week", "sha"] + ex.H_COLS + ["halstead_volume_sum", "halstead_files",
                                                      "halstead_skipped_files"],
    "git_file": ["week", "sha", "module", "file"] + ex.G_COLS,
    "git_module": ["week", "sha", "module"] + ex.G_COLS + ["files_changed"],
    "git_project": ["week", "sha"] + ex.G_COLS + ["files_changed"],
}


def write_extras(repo, week, sha, prev_sha, modules, append):
    """Halstead + git activity for one snapshot, at file/module/project level."""
    base = {"week": week, "sha": sha}
    hf, hm, hp = ex.halstead_snapshot(repo, sha, base)
    gf, gm, gp = ex.git_activity(repo, prev_sha, sha, base, modules)
    for name, rows in [("halstead_file", hf), ("halstead_module", hm), ("halstead_project", [hp]),
                       ("git_file", gf), ("git_module", gm), ("git_project", [gp])]:
        append(name, rows, EXTRA_COLS[name])


def add_total_principal(df):
    for c in ["sqale_index", "reliability_remediation_effort", "security_remediation_effort"]:
        if c not in df:
            df[c] = 0
    df["total_principal"] = (df["sqale_index"].fillna(0) + df["reliability_remediation_effort"].fillna(0)
                             + df["security_remediation_effort"].fillna(0))
    return df


def merge_extras(out, df, level, keys):
    """add Halstead + git (+ history) columns if those raw files exist (older runs: add_extras.py)"""
    hp = os.path.join(out, f"raw_hist_{level}.csv")
    if os.path.exists(hp):
        h = pd.read_csv(hp, sep=";").drop_duplicates(keys, keep="last")
        for k in ("week",):
            h[k] = pd.to_datetime(h[k]).dt.strftime("%Y-%m-%d")
            df[k] = pd.to_datetime(df[k]).dt.strftime("%Y-%m-%d")
        df = df.merge(h, on=keys, how="left")
    for kind in ["halstead", "git"]:
        path = os.path.join(out, f"raw_{kind}_{level}.csv")
        if not os.path.exists(path):
            continue
        x = pd.read_csv(path, sep=";").drop_duplicates(keys, keep="last")
        if kind == "git" and level == "module":
            # activity outside every Java module (root files) lives in the "(project)" row:
            # create that row for weeks where SonarQube had no project-wide issues
            have = set(map(tuple, df[keys].astype(str).values))
            new = x[(x["module"] == "(project)")][keys]
            new = new[[tuple(r) not in have for r in new.astype(str).values]]
            if len(new):
                df = pd.concat([df, new], ignore_index=True)
        x = x.rename(columns={"files_changed": "git_files_changed"}) if level != "file" else x
        df = df.merge(x, on=keys, how="left")
        if kind == "git" and level != "project":
            # files/modules with no commits in that window had 0 activity
            for c in ["commit_count", "lines_added", "lines_deleted", "code_churn",
                      "contributors_count", "git_files_changed"]:
                if c in df:
                    df[c] = df[c].fillna(0).astype(int)
            gp = os.path.join(out, "raw_git_project.csv")
            if os.path.exists(gp):
                w = pd.read_csv(gp, sep=";")[["week", "sha", "window_days"]].drop_duplicates(["week", "sha"])
                df = df.drop(columns=["window_days"], errors="ignore").merge(w, on=["week", "sha"], how="left")
    return df


def ck_levels(out):
    """CK metrics per file / module / project, aggregated like the paper (Tsoukalas et al. 2020,
    sec. 4.2): the average of the class values WEIGHTED BY EACH CLASS'S LINES OF CODE (CKJM LOC).
    Recomputed from raw_ck_class.csv, so older runs are fixed by a plain --join-only."""
    p = os.path.join(out, "raw_ck_class.csv")
    if not os.path.exists(p):
        return None
    c = pd.read_csv(p, sep=";")
    if c.empty or "LOC" not in c:
        return None
    keys = [k for k in CK_KEYS if k in c]

    def agg(g):
        w = g["LOC"].clip(lower=0).to_numpy(float)
        vals = g[keys].to_numpy(float)
        if w.sum() > 0:
            m = (vals * w[:, None]).sum(axis=0) / w.sum()
        else:
            m = vals.mean(axis=0)
        r = dict(zip(keys, np.round(m, 4)))
        r["n_classes"] = len(g)
        return pd.Series(r)

    res = {}
    for lvl, by in (("file", ["week", "sha", "module", "file"]), ("module", ["week", "sha", "module"]),
                    ("project", ["week", "sha"])):
        try:
            res[lvl] = c.groupby(by).apply(agg, include_groups=False).reset_index()
        except TypeError:                       # pandas < 2.2
            res[lvl] = c.groupby(by).apply(agg).reset_index()
    rp = os.path.join(out, "raw_ck_project.csv")
    if os.path.exists(rp):
        dropped = pd.read_csv(rp, sep=";")[["week", "sha", "n_dropped"]]
        res["project"] = res["project"].merge(dropped, on=["week", "sha"], how="left")
    return res


JD_COLS = ["class_count", "method_count", "fan_in", "external_class_count", "fan_out", "coupling",
           "cohesion", "has_test", "lcom4_classes", "noncohesive_classes"]


def merge_driller(out, filelvl):
    """Java Driller file metrics -> file level, columns jd_*; joined on week + sha + path."""
    p = os.path.join(out, "raw_jd_file.csv")
    if not os.path.exists(p):
        return filelvl
    jd = pd.read_csv(p, sep=";").drop_duplicates(["week", "sha", "path"], keep="last")
    jd = jd[jd.parse_status == "OK"]
    for c in JD_COLS:
        if c not in jd:
            jd[c] = np.nan
    jd = jd.rename(columns={c: "jd_" + c for c in JD_COLS})
    # share of measured classes that do more than one job (LCOM4 > 1)
    jd["jd_noncohesive_share"] = np.where(jd["jd_lcom4_classes"] > 0,
                                          jd["jd_noncohesive_classes"] / jd["jd_lcom4_classes"].where(
                                              jd["jd_lcom4_classes"] > 0, 1), np.nan)
    jd["week"] = jd["week"].astype(str)
    filelvl = filelvl.copy()
    filelvl["week"] = filelvl["week"].astype(str)
    return filelvl.merge(jd[["week", "sha", "path"] + ["jd_" + c for c in JD_COLS] + ["jd_noncohesive_share"]],
                         on=["week", "sha", "path"], how="left")


def driller_levels(out):
    """Java Driller values that need the dependency edges, on ALL THREE levels.

    From raw_jd_deps.csv (one row = file A uses file B, in one snapshot):
      jd_cross_module_deps  edges that START here and END in another module   (outgoing)
      jd_cross_module_in    edges that END here and START in another module   (incoming)
      jd_cross_dep_share    jd_cross_module_deps / all outgoing edges (0 = self-contained,
                            1 = every dependency leaves the module); empty when there are none
    file:    edges of that file;  module: edges of its files;  project: all edges
             (at project level every cross-module edge is both out and in, so in = out).
    Module / project also get sums and means of the file values:
      jd_dependencies (sum of fan-out), jd_method_count, jd_class_count (sums),
      jd_cohesion_mean, jd_test_share (means)."""
    fp = os.path.join(out, "file_level.csv")
    if not os.path.exists(os.path.join(out, "raw_jd_file.csv")) or not os.path.exists(fp):
        return
    f = pd.read_csv(fp, sep=";", low_memory=False)
    if "jd_fan_out" not in f:
        return
    f["week"] = f["week"].astype(str)
    EDGE = ["jd_cross_module_deps", "jd_cross_module_in", "jd_cross_dep_share"]
    f = f.drop(columns=[c for c in EDGE if c in f])

    # edges with the module of each end
    dp = os.path.join(out, "raw_jd_deps.csv")
    d = pd.read_csv(dp, sep=";").drop_duplicates() if os.path.exists(dp) else pd.DataFrame(
        columns=["week", "sha", "source_path", "target_path"])
    d["week"] = d["week"].astype(str)
    d["src_module"] = d.source_path.map(lambda x: module_and_rel(x)[0])
    d["dst_module"] = d.target_path.map(lambda x: module_and_rel(x)[0])
    x = d[d.src_module != d.dst_module]

    def share(df):
        dep = df["jd_dependencies"] if "jd_dependencies" in df else df["jd_fan_out"]
        return np.where(dep > 0, df["jd_cross_module_deps"] / dep.where(dep > 0, 1), np.nan)

    # ---- file level
    fo = x.groupby(["week", "sha", "source_path"]).size().rename("jd_cross_module_deps").reset_index() \
          .rename(columns={"source_path": "path"})
    fi = x.groupby(["week", "sha", "target_path"]).size().rename("jd_cross_module_in").reset_index() \
          .rename(columns={"target_path": "path"})
    f = f.merge(fo, on=["week", "sha", "path"], how="left").merge(fi, on=["week", "sha", "path"], how="left")
    has = f["jd_fan_out"].notna()
    for c in ("jd_cross_module_deps", "jd_cross_module_in"):
        f.loc[has, c] = f.loc[has, c].fillna(0)
        f.loc[~has, c] = np.nan
    f["jd_cross_dep_share"] = share(f)
    f.to_csv(fp, sep=";", index=False)

    # ---- module and project level
    agg = {"jd_fan_out": "sum", "jd_method_count": "sum", "jd_class_count": "sum",
           "jd_has_test": "mean", "jd_lcom4_classes": "sum", "jd_noncohesive_classes": "sum"}
    names = {"jd_fan_out": "jd_dependencies", "jd_has_test": "jd_test_share"}
    # cohesion of a module / project = mean of its files' cohesion WEIGHTED BY FILE LINES OF CODE
    # (SonarQube ncloc), like the LOC-weighted CK values (paper sec. 4.2); files without a
    # cohesion value (no measurable class) are left out of both sums
    for c in ("jd_lcom4_classes", "jd_noncohesive_classes"):
        if c not in f:
            f[c] = np.nan
    w = pd.to_numeric(f["ncloc"], errors="coerce") if "ncloc" in f else pd.Series(1.0, index=f.index)
    use = f["jd_cohesion"].notna() & (w > 0)
    f["_cw"] = np.where(use, w, 0.0)
    f["_cwv"] = np.where(use, f["jd_cohesion"] * w, 0.0)
    mo = x.groupby(["week", "sha", "src_module"]).size().rename("jd_cross_module_deps").reset_index() \
          .rename(columns={"src_module": "module"})
    mi = x.groupby(["week", "sha", "dst_module"]).size().rename("jd_cross_module_in").reset_index() \
          .rename(columns={"dst_module": "module"})
    po = x.groupby(["week", "sha"]).size().rename("jd_cross_module_deps").reset_index()
    pi = po.rename(columns={"jd_cross_module_deps": "jd_cross_module_in"})
    for level, keys, eo, ei in (("module", ["week", "sha", "module"], mo, mi),
                                ("project", ["week", "sha"], po, pi)):
        lp = os.path.join(out, f"{level}_level.csv")
        if not os.path.exists(lp):
            continue
        df = pd.read_csv(lp, sep=";", low_memory=False)
        df["week"] = df["week"].astype(str)
        df = df.drop(columns=[c for c in df.columns if c.startswith("jd_")])
        fj = f[has]
        g = fj.groupby(keys).agg({**agg, "_cw": "sum", "_cwv": "sum"}).rename(columns=names).reset_index()
        g["jd_cohesion_mean"] = np.where(g["_cw"] > 0, g["_cwv"] / g["_cw"].where(g["_cw"] > 0, 1), np.nan)
        g["jd_noncohesive_share"] = np.where(g["jd_lcom4_classes"] > 0, g["jd_noncohesive_classes"] /
                                             g["jd_lcom4_classes"].where(g["jd_lcom4_classes"] > 0, 1), np.nan)
        g = g.drop(columns=["_cw", "_cwv"])
        df = df.merge(g, on=keys, how="left").merge(eo, on=keys, how="left").merge(ei, on=keys, how="left")
        ok = df["jd_dependencies"].notna()
        for c in ("jd_cross_module_deps", "jd_cross_module_in"):
            df.loc[ok, c] = df.loc[ok, c].fillna(0)
            df.loc[~ok, c] = np.nan
        df["jd_cross_dep_share"] = share(df)
        df.to_csv(lp, sep=";", index=False)


def join_levels(out):
    r = lambda n: pd.read_csv(os.path.join(out, f"raw_{n}.csv"), sep=";")
    ckw = ck_levels(out)
    sp = r("sonar_project")
    ckp = ckw["project"] if ckw else r("ck_project")
    proj = add_total_principal(sp.merge(ckp, on=["week", "sha"], how="left"))
    proj = merge_extras(out, proj, "project", ["week", "sha"])
    proj.to_csv(os.path.join(out, "project_level.csv"), sep=";", index=False)

    sf = r("sonar_file")
    ckf = ckw["file"] if ckw else r("ck_file")
    filelvl = add_total_principal(sf.merge(ckf, on=["week", "sha", "module", "file"], how="left"))
    filelvl = merge_extras(out, filelvl, "file", ["week", "sha", "module", "file"])
    filelvl = merge_driller(out, filelvl)
    filelvl.to_csv(os.path.join(out, "file_level.csv"), sep=";", index=False)

    summ = [c for c in SUMMABLE if c in sf]
    sm = sf.groupby(["week", "sha", "module"])[summ].sum().reset_index()
    sm["n_files"] = sf.groupby(["week", "sha", "module"]).size().values
    nfp = os.path.join(out, "raw_sonar_nonfile.csv")
    if os.path.exists(nfp):
        nf = pd.read_csv(nfp, sep=";")
        keys = ["week", "sha", "module"]
        cols = [c for c in NONFILE_KEYS if c in sm and c in nf]
        nfg = nf.groupby(keys)[cols].sum().reset_index().rename(columns={c: c + "__nf" for c in cols})
        sm = sm.merge(nfg, on=keys, how="outer")
        for c in cols:
            sm["folder_level_" + c] = sm[c + "__nf"].fillna(0)
            sm[c] = sm[c].fillna(0) + sm[c + "__nf"].fillna(0)
            sm = sm.drop(columns=[c + "__nf"])
        sm["n_files"] = sm["n_files"].fillna(0).astype(int)
    # Issues SonarQube puts on the whole project (not on a file or folder) can't belong to a
    # module. They are exactly: project total - (files + folder-level). Add them as one extra
    # row per week with module "(project)", so modules add up to the project.
    sp_w = sp.set_index("week")
    extra = []
    for (wk, sha_), g in sm.groupby(["week", "sha"]):
        if wk not in sp_w.index:
            continue
        row = {"week": wk, "sha": sha_, "module": "(project)", "n_files": 0}
        anything = False
        for c in NONFILE_KEYS:
            if c in sm and c in sp_w:
                diff = float(sp_w.loc[wk, c]) - float(g[c].sum())
                if abs(diff) > 1e-6:
                    anything = True
                row[c] = diff
        if anything:
            extra.append(row)
    if extra:
        sm = pd.concat([sm, pd.DataFrame(extra)], ignore_index=True)
    mod = add_total_principal(sm.merge(ckw["module"] if ckw else r("ck_module"),
                                       on=["week", "sha", "module"], how="left"))
    mod = merge_extras(out, mod, "module", ["week", "sha", "module"])
    pr = mod["module"] == "(project)"
    for c in NONFILE_KEYS + ["total_principal"]:     # project-wide issues: none -> 0, not empty
        if c in mod:
            mod.loc[pr, c] = mod.loc[pr, c].fillna(0)
    mod.to_csv(os.path.join(out, "module_level.csv"), sep=";", index=False)
    driller_levels(out)
    log(f"project_level.csv {len(proj)} rows | module_level.csv {len(mod)} rows | "
        f"file_level.csv {len(filelvl)} rows")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--join-only":
        join_levels(sys.argv[2])
    else:
        main()
