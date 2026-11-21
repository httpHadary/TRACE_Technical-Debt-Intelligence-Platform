"""
Run CKJM Extended on every weekly snapshot and save class, file, module and
project level CK metrics.

This is the step missing from the authors' posted scripts. Run it AFTER
"Perform Maven Analysis" / "Perform Gradle Analysis", because CKJM reads the
compiled .class files those builds leave behind (target/classes or
build/classes/java/main).

Usage
-----
  python run_ckjm.py --extract-dir C:/Projects/kafka --jar ckjm_ext.jar \
                     --out-prefix apache_kafka [--maven-deps] [--sonar-csv apache_kafka_measures.csv]

EXTRACT_DIR is the same folder the GitHub script filled:
  "0 kafka-<sha>", "1 kafka-<sha>", ...  (0 = oldest week)

Outputs (all ';' separated, like the authors' CSVs)
  <prefix>_ckjm_class.csv    one row per class per week
  <prefix>_ckjm_file.csv     one row per .java file per week (inner classes merged)
  <prefix>_ckjm_module.csv   one row per module per week
  <prefix>_ckjm_project.csv  one row per week  (= the 16 CK columns in the paper)
  <prefix>_merged.csv        project rows joined to the SonarQube CSV (if --sonar-csv)
"""
import argparse, csv, glob, os, re, subprocess, sys
from collections import defaultdict
from statistics import mean

METRICS = ["WMC", "DIT", "NOC", "CBO", "RFC", "LCOM", "Ca", "Ce", "NPM", "LCOM3",
           "LOC", "DAM", "MOA", "MFA", "CAM", "IC", "CBM", "AMC"]
EXTRA = ["max_CC", "avg_CC"]
SEP = os.pathsep            # ':' on Linux/Mac, ';' on Windows

# Folders that hold compiled MAIN code (test classes are left out on purpose)
CLASS_DIR_PATTERNS = ["**/target/classes", "**/build/classes/java/main",
                      "**/build/classes/main", "**/out/production/*"]

LINE_RE = re.compile(r"^(\S+)((?:\s+-?[\d.]+(?:E-?\d+)?){18})\s*$")
CC_RE = re.compile(r"^\s*~\s.*:\s*(\d+)\s*$")


def find_class_dirs(root):
    dirs = set()
    for pat in CLASS_DIR_PATTERNS:
        for d in glob.glob(os.path.join(root, pat), recursive=True):
            if os.path.isdir(d) and "test" not in os.path.relpath(d, root).lower().split(os.sep):
                dirs.add(os.path.normpath(d))
    return sorted(dirs)


def module_of(class_dir, root):
    rel = os.path.relpath(class_dir, root).replace("\\", "/")
    for tail in ["/target/classes", "/build/classes/java/main", "/build/classes/main"]:
        if rel.endswith(tail) or rel == tail.lstrip("/"):
            rel = rel[: -len(tail)] if rel.endswith(tail) else ""
            break
    return rel or "."


def dependency_jars(root, use_maven, gradle_cache):
    """Library jars are needed so CKJM can load superclasses (DIT, MFA, NOC...)."""
    if use_maven and glob.glob(os.path.join(root, "**/pom.xml"), recursive=True):
        subprocess.run("mvn -q dependency:copy-dependencies -DincludeScope=compile "
                       "-DoutputDirectory=target/ckjm-deps", cwd=root, shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    jars = glob.glob(os.path.join(root, "**/target/ckjm-deps/*.jar"), recursive=True)
    jars += glob.glob(os.path.join(root, "**/target/dependency/*.jar"), recursive=True)
    if gradle_cache:
        jars += glob.glob(os.path.join(gradle_cache, "**/*.jar"), recursive=True)
    return sorted(set(jars))


def run_ckjm(jar, class_files, classpath, java="java", max_retries=50):
    """Run CKJM once over all classes (so Ca and NOC see the whole project).
    If a class's superclass cannot be found CKJM aborts the whole run, so we
    drop that one class and retry. Dropped classes are reported."""
    import tempfile
    files = list(class_files)
    dropped = []
    # one copy of each library: every module copies the same jars into its own target/ckjm-deps
    seen, uniq = set(), []
    for c in [jar] + list(classpath):
        k = os.path.basename(c) if c.endswith(".jar") else c
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    cp = SEP.join(uniq)
    # a big multi-module project (dubbo) gives a class path longer than the OS allows on a
    # command line -> pass it in a Java argument file (@file, Java 9+)
    argf = tempfile.NamedTemporaryFile("w", suffix=".args", delete=False)
    argf.write("-cp\n\"" + cp.replace("\\", "\\\\") + "\"\n")
    argf.close()
    try:
        return _run_ckjm_loop(java, argf.name, files, dropped, max_retries)
    finally:
        os.unlink(argf.name)


def _run_ckjm_loop(java, argfile, files, dropped, max_retries):
    for _ in range(max_retries):
        if not files:
            return "", dropped
        p = subprocess.run([java, "@" + argfile, "gr.spinellis.ckjm.MetricsFilter"],
                           input="\n".join(files), capture_output=True, text=True)
        if p.returncode == 0:
            return p.stdout, dropped
        m = re.search(r"file name\s+(\S.*\.class)", p.stdout + p.stderr)
        if not m or m.group(1).strip() not in files:
            raise RuntimeError("CKJM failed:\n" + p.stderr[-2000:])
        bad = m.group(1).strip()
        files.remove(bad)
        dropped.append(bad)
    raise RuntimeError("Too many classes with missing superclasses - add dependency jars")


def parse(output):
    rows, cur = [], None
    for line in output.splitlines():
        m = LINE_RE.match(line)
        if m:
            vals = [float(v) for v in m.group(2).split()]
            cur = {"class": m.group(1), **dict(zip(METRICS, vals)), "_cc": []}
            rows.append(cur)
            continue
        c = CC_RE.match(line)
        if c and cur is not None:
            cur["_cc"].append(int(c.group(1)))
    for r in rows:
        cc = r.pop("_cc")
        r["max_CC"] = max(cc) if cc else 0
        r["avg_CC"] = round(mean(cc), 4) if cc else 0
    return rows


def avg_rows(rows, keys):
    return {k: round(mean(r[k] for r in rows), 4) for k in keys}


def version_folders(extract_dir):
    out = []
    for name in os.listdir(extract_dir):
        full = os.path.join(extract_dir, name)
        if os.path.isdir(full) and name.split()[0].isdigit():
            out.append((int(name.split()[0]), name.split("-")[-1], full))
    return sorted(out)


def write(path, rows, cols):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("wrote", path, len(rows), "rows")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract-dir", required=True)
    ap.add_argument("--jar", required=True, help="path to ckjm_ext.jar")
    ap.add_argument("--out-prefix", required=True)
    ap.add_argument("--maven-deps", action="store_true",
                    help="run 'mvn dependency:copy-dependencies' in each snapshot")
    ap.add_argument("--gradle-cache", default=None,
                    help="e.g. ~/.gradle/caches/modules-2/files-2.1 (Gradle projects)")
    ap.add_argument("--skip-inner", action="store_true",
                    help="ignore inner/anonymous classes (names with $)")
    ap.add_argument("--sonar-csv", default=None)
    ap.add_argument("--java", default="java",
                    help="Java 17+ used to RUN CKJM (projects may still build with Java 8)")
    a = ap.parse_args()

    keys = METRICS + EXTRA
    cls_rows, file_rows, mod_rows, proj_rows = [], [], [], []

    for idx, sha, root in version_folders(a.extract_dir):
        class_dirs = find_class_dirs(root)
        if not class_dirs:
            print(f"[{idx}] {sha}: no compiled classes - did the build fail? skipped")
            continue
        class_files, owner = [], {}
        for d in class_dirs:
            for f in glob.glob(os.path.join(d, "**/*.class"), recursive=True):
                base = os.path.basename(f)
                if base in ("module-info.class", "package-info.class"):
                    continue
                if a.skip_inner and "$" in base:
                    continue
                class_files.append(f)
                owner[f] = d
        jars = dependency_jars(root, a.maven_deps, a.gradle_cache)
        out, dropped = run_ckjm(a.jar, class_files, class_dirs + jars, a.java)
        rows = parse(out)
        if not rows:
            print(f"[{idx}] {sha}: CKJM measured 0 classes ({len(dropped)} dropped) - skipped")
            continue
        if len(dropped) > 0.05 * len(class_files):
            print(f"[{idx}] {sha}: WARNING {len(dropped)} of {len(class_files)} classes "
                  "dropped - add dependency jars (--maven-deps / --gradle-cache)")

        # map each class name -> module and source file
        fqcn_module = {}
        for f, d in owner.items():
            fq = os.path.relpath(f, d)[:-6].replace(os.sep, ".").replace("/", ".")
            fqcn_module[fq] = module_of(d, root)
        for r in rows:
            outer = r["class"].split("$")[0]
            r.update(week_index=idx, sha=sha,
                     module=fqcn_module.get(r["class"], "?"),
                     file=outer.replace(".", "/") + ".java")
        cls_rows += rows

        by_file, by_mod = defaultdict(list), defaultdict(list)
        for r in rows:
            by_file[(r["module"], r["file"])].append(r)
            by_mod[r["module"]].append(r)
        for (m, f), rs in by_file.items():
            file_rows.append({"week_index": idx, "sha": sha, "module": m, "file": f,
                              "n_classes": len(rs), **avg_rows(rs, keys)})
        for m, rs in by_mod.items():
            mod_rows.append({"week_index": idx, "sha": sha, "module": m,
                             "n_classes": len(rs), **avg_rows(rs, keys)})
        proj_rows.append({"week_index": idx, "sha": sha, "n_classes": len(rows),
                          "n_dropped": len(dropped), **avg_rows(rows, keys)})
        print(f"[{idx}] {sha}: {len(rows)} classes, {len(dropped)} dropped, {len(jars)} jars")

    write(f"{a.out_prefix}_ckjm_class.csv", cls_rows,
          ["week_index", "sha", "module", "file", "class"] + keys)
    write(f"{a.out_prefix}_ckjm_file.csv", file_rows,
          ["week_index", "sha", "module", "file", "n_classes"] + keys)
    write(f"{a.out_prefix}_ckjm_module.csv", mod_rows,
          ["week_index", "sha", "module", "n_classes"] + keys)
    write(f"{a.out_prefix}_ckjm_project.csv", proj_rows,
          ["week_index", "sha", "n_classes", "n_dropped"] + keys)

    if a.sonar_csv:
        import pandas as pd
        sonar = pd.read_csv(a.sonar_csv, sep=";")
        sonar["date"] = pd.to_datetime(sonar[sonar.columns[0]])   # first column = date
        sonar = sonar.sort_values("date")
        ck = pd.DataFrame(proj_rows).sort_values("week_index")
        if len(sonar) != len(ck):
            print(f"WARNING: SonarQube has {len(sonar)} weeks but CKJM has {len(ck)}. "
                  "Joined by position on the overlapping part only - check by hand.")
        n = min(len(sonar), len(ck))
        merged = pd.concat([sonar.iloc[-n:].reset_index(drop=True),
                            ck.iloc[-n:].reset_index(drop=True)], axis=1)
        merged.to_csv(f"{a.out_prefix}_merged.csv", sep=";", index=False)
        print("wrote", f"{a.out_prefix}_merged.csv", len(merged), "rows")


if __name__ == "__main__":
    sys.exit(main())
