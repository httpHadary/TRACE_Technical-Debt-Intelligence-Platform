#!/usr/bin/env python3
"""
preflight.py - look at a repo's planned commits BEFORE building them and work out what each
build needs, so known problems are avoided instead of failing first.

For a sample of the planned commits (every Nth + first + last) it reads, straight from git
(no checkout):
  build tool        pom.xml / build.gradle / build.xml (Ant only = cannot be built)
  java level        maven.compiler.source/target/release, <source>/<target>/<release>,
                    java.version, sourceCompatibility (Gradle)
  gradle version    gradle/wrapper/gradle-wrapper.properties
  profile-only      ${x} used as a version but only defined inside a <profile> (okhttp's
                    alpn.jdk8.version) -> Maven refuses the pom when no profile matches
  test internals    test code importing com.sun.* / sun.* (removed from newer JDK 8 updates;
                    dubbo) -> compile without tests from the start
  snapshots         external -SNAPSHOT libraries (swapped for releases at build time)

Writes into the run folder:
  preflight.csv        one row per sampled commit
  build_settings.json  what td_pipeline.py applies to every build of this repo
and prints a short report. td_pipeline.py runs it automatically on a new run folder.

    python preflight.py --repo ~/td-work/apache_dubbo --plan ~/td-out/dubbo_final/weeks_plan.csv \
                        --out ~/td-out/dubbo_final
"""
import argparse, csv, json, os, re, subprocess, sys
from collections import Counter

# values for properties that old poms only set inside JDK-specific profiles
KNOWN_PROPERTY_DEFAULTS = {
    "alpn.jdk8.version": "8.1.13.v20181017",     # okhttp 2016-2018
    "alpn.version": "8.1.13.v20181017",
    "npn.version": "8.1.2.v20120308",
}
INTERNAL_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?(com\.sun\.|sun\.)[\w.]+", re.M)


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          errors="replace").stdout


def blobs(repo, sha, paths):
    """Contents of several files of one commit in one `git cat-file --batch` call."""
    if not paths:
        return {}
    out = subprocess.run(["git", "-C", repo, "cat-file", "--batch"],
                         input="".join(f"{sha}:{p}\n" for p in paths).encode(),
                         capture_output=True).stdout
    res, pos = {}, 0
    for p in paths:
        nl = out.index(b"\n", pos)
        head = out[pos:nl].split()
        if len(head) != 3 or not head[2].isdigit():
            pos = nl + 1
            continue
        size = int(head[2])
        res[p] = out[nl + 1: nl + 1 + size].decode("utf-8", "replace")
        pos = nl + 1 + size + 1
    return res


def level(v, props):
    """'1.8' / '8' / '${java.version}' -> 8 (int) or None."""
    if not v:
        return None
    v = v.strip()
    for _ in range(3):
        m = re.fullmatch(r"\$\{([^}]+)\}", v)
        if not m:
            break
        v = props.get(m.group(1), "")
    m = re.fullmatch(r"1\.(\d+)|(\d+)(?:\.\d+)?", v)
    if not m:
        return None
    return int(m.group(1) or m.group(2))


def strip_profiles(pom):
    return re.sub(r"<profiles>.*?</profiles>", "", pom, flags=re.S)


def scan_commit(repo, sha):
    files = git(repo, "ls-tree", "-r", "--name-only", sha).splitlines()
    poms = [f for f in files if f.endswith("pom.xml")]
    gradles = [f for f in files if re.search(r"(^|/)build\.gradle(\.kts)?$", f)]
    ant = "build.xml" in files
    tool = "maven" if "pom.xml" in files else "gradle" if any("/" not in g for g in gradles) \
        else "ant" if ant else "none"
    tests = [f for f in files if f.endswith(".java") and "/src/test/" in "/" + f]
    wrapper = [f for f in files if f.endswith("gradle/wrapper/gradle-wrapper.properties")]
    got = blobs(repo, sha, poms + gradles[:40] + wrapper[:1] + tests[:3000])

    levels, used, defined, profile_only, snaps = [], set(), set(), set(), set()
    own = set()
    for p in poms:
        txt = got.get(p, "")
        own |= set(re.findall(r"<version>([^<$]+-SNAPSHOT)</version>", txt))
    for p in poms:
        txt = got.get(p, "")
        main = strip_profiles(txt)
        props = dict(re.findall(r"<([A-Za-z0-9_.\-]+)>([^<]*)</\1>", main))
        for block in re.findall(r"<properties>(.*?)</properties>", main, re.S):
            defined |= set(re.findall(r"<([A-Za-z0-9_.\-]+)>[^<]*</\1>", block))
        for key in ("maven.compiler.source", "maven.compiler.target", "maven.compiler.release",
                    "java.version", "jdk.version", "java.source.version"):
            lv = level(props.get(key), props)
            if lv:
                levels.append(lv)
        for tag in ("source", "target", "release"):
            for v in re.findall(rf"<{tag}>([^<]+)</{tag}>", main):
                lv = level(v, props)
                if lv and 1 <= lv <= 30:
                    levels.append(lv)
        for v in re.findall(r"<version>\$\{([^}]+)\}</version>", txt):
            used.add(v)
        for m in re.finditer(r"<profile>.*?</profile>", txt, re.S):
            for k in re.findall(r"<([A-Za-z0-9_.\-]+)>[^<]*</\1>", m.group(0)):
                profile_only.add(k)
        for k, v in re.findall(r"<([A-Za-z0-9_.\-]+\.version)>([^<]+?-SNAPSHOT)</\1>", txt):
            if v not in own:
                snaps.add(f"{k}={v}")
    for g in gradles:
        for v in re.findall(r"(?:source|target)Compatibility\s*=\s*['\"]?(?:JavaVersion\.VERSION_)?([\d._]+)",
                            got.get(g, "")):
            lv = level(v.replace("_", "."), {})
            if lv:
                levels.append(lv)
    builtin = {"project.version", "project.groupId", "project.artifactId", "project.parent.version",
               "parent.version", "version", "pom.version"}
    undefined = sorted(v for v in used - defined - builtin if not v.startswith(("project.", "env.")))
    prof = sorted(v for v in undefined if v in profile_only)
    gradle_v = None
    if wrapper:
        m = re.search(r"gradle-([\d.]+)-(?:all|bin)\.zip", got.get(wrapper[0], ""))
        gradle_v = m.group(1) if m else None
    internal = sum(1 for t in tests if INTERNAL_IMPORT.search(got.get(t, "")))
    return {"sha": sha, "tool": tool, "java_level": max(levels) if levels else "",
            "gradle": gradle_v or "", "modules": len(poms) or len(gradles),
            "profile_only_props": " ".join(prof),
            "undefined_props": " ".join(v for v in undefined if v not in prof),
            "tests_with_internal_jdk_imports": internal,
            "external_snapshots": " ".join(sorted(snaps))}


def java_level_of(repo, sha):
    """Highest Java level the poms / build.gradle files of one commit ask for (cheap: no tests read)."""
    files = git(repo, "ls-tree", "-r", "--name-only", sha).splitlines()
    builds = [f for f in files if f.endswith("pom.xml") or re.search(r"(^|/)build\.gradle(\.kts)?$", f)]
    got = blobs(repo, sha, builds[:200])
    lv = []
    for p, txt in got.items():
        if p.endswith("pom.xml"):
            main = strip_profiles(txt)
            props = dict(re.findall(r"<([A-Za-z0-9_.\-]+)>([^<]*)</\1>", main))
            for key in ("maven.compiler.source", "maven.compiler.target", "maven.compiler.release",
                        "java.version", "jdk.version"):
                v = level(props.get(key), props)
                if v:
                    lv.append(v)
            for tag in ("source", "target", "release"):
                for v in re.findall(rf"<{tag}>([^<]+)</{tag}>", main):
                    v = level(v, props)
                    if v and v <= 30:
                        lv.append(v)
        else:
            for v in re.findall(r"(?:source|target)Compatibility\s*=\s*['\"]?(?:JavaVersion\.VERSION_)?([\d._]+)", txt):
                v = level(v.replace("_", "."), {})
                if v:
                    lv.append(v)
    return max(lv) if lv else None


ERROR_KINDS = [   # (kind, pattern) - first match wins; used for build_errors.csv
    ("undefined_version_property", r"must be a valid version but is '\$\{"),
    ("internal_jdk_api", r"package (com\.sun|sun)\.[\w.]+ does not exist"),
    ("java_version", r"invalid (target|source) release|Source option \d+ is no longer supported|"
                     r"class file has wrong version|UnsupportedClassVersionError|release version \d+ not supported"),
    ("snapshot_or_missing_dependency", r"Could not (resolve|find artifact|transfer)|Non-resolvable|"
                                       r"Failure to find|was not found in"),
    ("network", r"UnknownHost|Connection (refused|reset|timed out)|Network is unreachable"),
    ("out_of_memory", r"OutOfMemoryError|Cannot allocate memory|GC overhead"),
    ("compile_error", r"COMPILATION ERROR|Compilation failure|error: "),
    ("test_failure", r"There are test failures|Tests in error"),
    ("no_build_file", r"no pom\.xml or build\.gradle"),
]


def classify(log_tail):
    """(kind, first error line) for the output of a failed build."""
    lines = [l for l in log_tail.splitlines()
             if re.search(r"\[ERROR\]|error:|FAILURE|Exception|no pom", l)
             and not re.search(r"^\s*\[ERROR\]\s*\[Help 1\]|re-run Maven|full stack trace|full debug|For more information|"
                               r"resume the build|^\s*\[ERROR\]\s*$", l)]
    for kind, pat in ERROR_KINDS:
        for l in lines:
            if re.search(pat, l):
                return kind, l.strip()[:300]
    return "other", (lines[0].strip()[:300] if lines else "")


def run(repo, shas, out, every=10):
    shas = list(dict.fromkeys(shas))
    pick = sorted(set(list(range(0, len(shas), every)) + [len(shas) - 1])) if shas else []
    rows = [{"index": i, **scan_commit(repo, shas[i])} for i in pick]
    with open(os.path.join(out, "preflight.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)

    tools = Counter(r["tool"] for r in rows)
    lv = [r["java_level"] for r in rows if r["java_level"] != ""]
    props = sorted({p for r in rows for p in r["profile_only_props"].split()})
    internal = sum(r["tests_with_internal_jdk_imports"] > 0 for r in rows)
    settings = {
        "mvn_props": {p: KNOWN_PROPERTY_DEFAULTS[p] for p in props if p in KNOWN_PROPERTY_DEFAULTS},
        "unknown_profile_props": [p for p in props if p not in KNOWN_PROPERTY_DEFAULTS],
        "skip_test_compile": internal > 0,
        "max_java_level": max(lv) if lv else None,
        "tools": dict(tools),
        "gradle_versions": sorted({r["gradle"] for r in rows if r["gradle"]}),
        "sampled_commits": len(rows),
    }
    with open(os.path.join(out, "build_settings.json"), "w") as f:
        json.dump(settings, f, indent=2)

    notes = [f"preflight: {len(rows)} of {len(shas)} planned commits checked; build tool {dict(tools)}"]
    if settings["max_java_level"]:
        notes.append(f"preflight: Java level up to {settings['max_java_level']}"
                     + (" -> builds with JDK 17 where the pom asks for > 8" if settings["max_java_level"] > 8 else ""))
    if settings["mvn_props"]:
        notes.append(f"preflight: will set {settings['mvn_props']} (only defined in old JDK profiles)")
    if settings["unknown_profile_props"]:
        notes.append(f"preflight: WARNING versions only set in profiles, no known value: "
                     f"{settings['unknown_profile_props']}")
    if internal:
        notes.append(f"preflight: test code uses internal JDK classes in {internal} sampled commits "
                     f"-> tests are not compiled (not measured anyway)")
    if tools.get("ant") or tools.get("none"):
        notes.append(f"preflight: WARNING {tools.get('ant', 0) + tools.get('none', 0)} sampled commits "
                     f"have no Maven/Gradle build (Ant only or none) -> those snapshots will fail")
    if settings["gradle_versions"]:
        notes.append(f"preflight: Gradle wrapper versions {settings['gradle_versions']}")
    return settings, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--plan", required=True, help="week;sha CSV (weeks_plan.csv or a paper plan)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--every", type=int, default=10, help="check every Nth commit (default 10)")
    a = ap.parse_args()
    with open(os.path.expanduser(a.plan)) as f:
        shas = [r["sha"] for r in csv.DictReader(f, delimiter=";")]
    os.makedirs(os.path.expanduser(a.out), exist_ok=True)
    _, notes = run(os.path.expanduser(a.repo), shas, os.path.expanduser(a.out), a.every)
    print("\n".join(notes))


if __name__ == "__main__":
    sys.exit(main())
