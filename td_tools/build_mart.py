"""
build_mart.py - pack one or more finished runs into ONE data mart for the AI team.

  python build_mart.py --run retrofit=~/td-out/retrofit_final \
                       --plan retrofit=~/td-out/retrofit_plan.csv \
                       --paper retrofit=~/zenodo/square_retrofit_measures.csv \
                       --out ~/td-mart

  (repeat --run/--plan/--paper for more projects: --run commonsio=~/td-out/commonsio_final ...)

Creates <out>/ and <out>.zip with:
  mart_project.csv      one row per project per week
  mart_module.csv       one row per module per week
  mart_file.csv         one row per Java file per week
  mart_all_levels.csv   the three stacked, with a "level" column (the combined mart)
  data_dictionary.csv   every column: group, meaning, unit, valid range, levels
  validation_report.txt validate.py output for every run
  README.md             what this is, how it was made, known issues, how to use it
"""
import argparse, os, shutil, subprocess, sys, datetime as dt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ column catalogue
# name: (group, meaning, unit, range)
D = {
 # keys
 "project_id": ("key", "short project name", "-", "text"),
 "level": ("key", "project / module / file", "-", "text"),
 "week": ("key", "week label (paper's date if --plan-csv was used)", "date", "YYYY-MM-DD"),
 "week_index": ("key", "0,1,2... order of the week within the project", "-", ">=0"),
 "sha": ("key", "git commit analysed for that week", "-", "40 hex chars"),
 "commit_date": ("key", "real date of that commit", "date", "YYYY-MM-DD"),
 "module": ("key", "module folder ('.' = root, '(project)' = issues on the whole project)", "-", "text"),
 "file": ("key", "Java file path inside the source root (src/main/java or src/java)", "-", "text"),
 "path": ("key", "full file path in the repo", "-", "text"),
 # Java Driller (JavaParser, source code) - file level
 "jd_class_count": ("javadriller", "classes and interfaces declared in the file (module/project: sum)", "count", ">=0"),
 "jd_method_count": ("javadriller", "methods declared in the file (module/project: sum)", "count", ">=0"),
 "jd_fan_in": ("javadriller", "project files that depend on this file", "files", ">=0"),
 "jd_external_class_count": ("javadriller", "classes in other files that reference this file", "classes", ">=0"),
 "jd_fan_out": ("javadriller", "project files this file depends on", "files", ">=0"),
 "jd_coupling": ("javadriller", "distinct files in fan-in UNION fan-out (a file counted once)", "files", ">=0"),
 "jd_cohesion": ("javadriller", "mean over classes of 1 / LCOM4 (Hitz & Montazeri 1995: method groups linked by shared fields or calls); 1 = one job; empty = no measurable class", "-", "0-1"),
 "jd_has_test": ("javadriller", "1 = a test class named <Class>Test/Tests/IT/Spec... exists", "0/1", "0-1"),
 "jd_dependencies": ("javadriller", "file-to-file dependencies starting in the module/project (sum of fan-out)", "edges", ">=0"),
 "jd_cross_module_deps": ("javadriller", "outgoing cross-module dependencies: file-to-file edges that start here (file / module) and end in another module; project = all cross-module edges", "edges", ">=0"),
 "jd_cross_module_in": ("javadriller", "incoming cross-module dependencies: edges that end here (file / module) and start in another module; project = all cross-module edges (= jd_cross_module_deps)", "edges", ">=0"),
 "jd_cross_dep_share": ("javadriller", "jd_cross_module_deps / all outgoing dependencies (file: jd_fan_out; module/project: jd_dependencies); 0 = self-contained, 1 = every dependency leaves the module; empty when there are none", "ratio", "0-1"),
 "jd_cohesion_mean": ("javadriller", "jd_cohesion of the module's/project's files, averaged with each file's ncloc as the weight (like the LOC-weighted CK values); files without a cohesion value left out", "-", "0-1"),
 "jd_lcom4_classes": ("javadriller", "classes measured for cohesion (not interfaces; at least one method with code); module/project: sum", "classes", ">=0"),
 "jd_noncohesive_classes": ("javadriller", "measured classes with LCOM4 > 1, i.e. doing more than one job; module/project: sum", "classes", ">=0"),
 "jd_noncohesive_share": ("javadriller", "jd_noncohesive_classes / jd_lcom4_classes: share of classes doing more than one job (0 = all cohesive); empty when no class was measured", "ratio", "0-1"),
 "jd_test_share": ("javadriller", "share of files that have a test class", "ratio", "0-1"),
 # flags
 "same_commit_as_prev_week": ("flag", "1 if no new commit since the previous week (values repeat)", "0/1", "0-1"),
 "days_since_prev_week": ("flag", "days between this week and the previous kept week (7 normally, 14 after a failed week)", "days", ">=0"),
 # target
 "total_principal": ("TARGET", "technical debt principal = sqale_index + reliability_remediation_effort + security_remediation_effort", "minutes", ">=0"),
 "td_density": ("TARGET", "total_principal / ncloc", "minutes per line", ">=0"),
 # sonar
 "sonar_bugs": ("sonarqube", "reliability issues", "count", ">=0"),
 "sonar_vulnerabilities": ("sonarqube", "security issues", "count", ">=0"),
 "sonar_code_smells": ("sonarqube", "maintainability issues", "count", ">=0"),
 "sonar_sqale_index": ("sonarqube", "effort to fix all code smells (maintainability TD)", "minutes", ">=0"),
 "sonar_reliability_remediation_effort": ("sonarqube", "effort to fix all bugs", "minutes", ">=0"),
 "sonar_security_remediation_effort": ("sonarqube", "effort to fix all vulnerabilities", "minutes", ">=0"),
 "sonar_ncloc": ("sonarqube", "lines of code without comments/blank lines (main Java code)", "lines", ">=0"),
 "sonar_lines": ("sonarqube", "all physical lines", "lines", ">=0"),
 "sonar_comment_lines": ("sonarqube", "comment lines", "lines", ">=0"),
 "sonar_complexity": ("sonarqube", "cyclomatic complexity (sum)", "-", ">=0"),
 "sonar_cognitive_complexity": ("sonarqube", "cognitive complexity (sum)", "-", ">=0"),
 "sonar_duplicated_blocks": ("sonarqube", "duplicated code blocks", "count", ">=0"),
 "sonar_duplicated_lines": ("sonarqube", "duplicated lines", "lines", ">=0"),
 "sonar_uncovered_lines": ("sonarqube", "lines not covered by tests (tests are not run -> = lines_to_cover)", "lines", ">=0"),
 "sonar_lines_to_cover": ("sonarqube", "executable lines", "lines", ">=0"),
 "sonar_coverage": ("sonarqube", "test coverage - NOT MEASURED (tests not run), always empty", "%", "empty"),
 "is_package_info": ("flag", "1 = package-info.java (documentation only, no class, no TD)", "0/1", "0-1"),
 "has_ck": ("flag", "1 = file has CK values (0 = no Java class: package-info / Kotlin)", "0/1", "0-1"),
 "has_halstead": ("flag", "1 = file has Halstead values (0 = not a Java file)", "0/1", "0-1"),
 "sonar_classes": ("sonarqube", "classes incl. inner classes", "count", ">=0"),
 "sonar_functions": ("sonarqube", "methods", "count", ">=0"),
 "sonar_files": ("sonarqube", "files", "count", ">=0"),
 "sonar_statements": ("sonarqube", "statements", "count", ">=0"),
 "sonar_violations": ("sonarqube", "all issues = bugs + vulnerabilities + code_smells", "count", ">=0"),
 "sonar_blocker_violations": ("sonarqube", "issues with severity blocker", "count", ">=0"),
 "sonar_critical_violations": ("sonarqube", "issues with severity critical", "count", ">=0"),
 "sonar_major_violations": ("sonarqube", "issues with severity major", "count", ">=0"),
 "sonar_minor_violations": ("sonarqube", "issues with severity minor", "count", ">=0"),
 "sonar_info_violations": ("sonarqube", "issues with severity info", "count", ">=0"),
 "sonar_sqale_debt_ratio": ("sonarqube", "sqale_index / (30 min x ncloc) x 100 (can exceed 100 for tiny files)", "%", ">=0"),
 "sonar_sqale_rating": ("sonarqube", "maintainability rating A..E", "1-5", "1-5"),
 "sonar_reliability_rating": ("sonarqube", "reliability rating A..E", "1-5", "1-5"),
 "sonar_security_rating": ("sonarqube", "security rating A..E", "1-5", "1-5"),
 "sonar_comment_lines_density": ("sonarqube", "comment_lines / (ncloc + comment_lines) x 100", "%", "0-100"),
 "sonar_duplicated_lines_density": ("sonarqube", "duplicated lines %", "%", "0-100"),
 "sonar_n_files": ("sonarqube", "Java files in the module (module level)", "count", ">=0"),
 # ck
 "ck_WMC": ("ck", "weighted methods per class (= number of methods)", "avg per class", ">=0"),
 "ck_DIT": ("ck", "depth of inheritance tree", "avg per class", ">=1"),
 "ck_NOC": ("ck", "number of direct subclasses", "avg per class", ">=0"),
 "ck_CBO": ("ck", "coupling between objects", "avg per class", ">=0"),
 "ck_RFC": ("ck", "response for a class", "avg per class", ">=0"),
 "ck_LCOM": ("ck", "lack of cohesion (C&K)", "avg per class", ">=0"),
 "ck_Ca": ("ck", "afferent coupling (classes using this one)", "avg per class", ">=0"),
 "ck_Ce": ("ck", "efferent coupling (classes this one uses)", "avg per class", ">=0"),
 "ck_NPM": ("ck", "public methods", "avg per class", ">=0"),
 "ck_LCOM3": ("ck", "lack of cohesion (Henderson-Sellers)", "avg per class", "0-2"),
 "ck_LOC": ("ck", "bytecode lines of code", "avg per class", ">=0"),
 "ck_DAM": ("ck", "data access metric (private/protected fields share)", "avg per class", "0-1"),
 "ck_MOA": ("ck", "measure of aggregation", "avg per class", ">=0"),
 "ck_MFA": ("ck", "measure of functional abstraction", "avg per class", "0-1"),
 "ck_CAM": ("ck", "cohesion among methods", "avg per class", "0-1"),
 "ck_IC": ("ck", "inheritance coupling", "avg per class", ">=0"),
 "ck_CBM": ("ck", "coupling between methods", "avg per class", ">=0"),
 "ck_AMC": ("ck", "average method complexity (bytecode size)", "avg per class", ">=0"),
 "ck_max_CC": ("ck", "max McCabe complexity of a method", "avg per class", ">=0"),
 "ck_avg_CC": ("ck", "average McCabe complexity of methods", "avg per class", ">=0"),
 "ck_n_classes": ("ck", "classes measured by CKJM (incl. inner)", "count", ">=0"),
 "ck_n_dropped": ("ck", "classes CKJM could not measure", "count", ">=0"),
 # halstead
 "halstead_n1": ("halstead", "distinct operators", "count", ">=0"),
 "halstead_n2": ("halstead", "distinct operands", "count", ">=0"),
 "halstead_N1": ("halstead", "total operators", "count", ">=0"),
 "halstead_N2": ("halstead", "total operands", "count", ">=0"),
 "halstead_vocabulary": ("halstead", "n1 + n2", "count", ">=0"),
 "halstead_length": ("halstead", "N1 + N2", "count", ">=0"),
 "halstead_volume": ("halstead", "length x log2(vocabulary) (module/project: from union of distinct tokens)", "bits", ">=0"),
 "halstead_difficulty": ("halstead", "(n1/2) x (N2/n2)", "-", ">=0"),
 "halstead_effort": ("halstead", "difficulty x volume", "-", ">=0"),
 "halstead_volume_sum": ("halstead", "sum of file volumes (module/project)", "bits", ">=0"),
 "halstead_files": ("halstead", "Java files tokenised", "count", ">=0"),
 "halstead_skipped_files": ("halstead", "files the tokenizer could not read", "count", ">=0"),
 # git
 "git_commit_count": ("git", "commits since the previous snapshot (no merges)", "count", ">=0"),
 "git_lines_added": ("git", "lines added in that window", "lines", ">=0"),
 "git_lines_deleted": ("git", "lines deleted in that window", "lines", ">=0"),
 "git_code_churn": ("git", "added + deleted", "lines", ">=0"),
 "git_contributors_count": ("git", "distinct author e-mails", "count", ">=0"),
 "git_files_changed": ("git", "files touched (module/project)", "count", ">=0"),
 "git_window_days": ("git", "real days covered by the window", "days", ">=0"),
}

SONAR = ["bugs", "vulnerabilities", "code_smells", "sqale_index", "reliability_remediation_effort",
         "security_remediation_effort", "ncloc", "lines", "comment_lines", "complexity",
         "cognitive_complexity", "duplicated_blocks", "duplicated_lines", "uncovered_lines",
         "lines_to_cover", "coverage", "classes", "functions", "files", "statements", "violations",
         "blocker_violations", "critical_violations", "major_violations", "minor_violations",
         "info_violations", "sqale_debt_ratio", "sqale_rating", "reliability_rating",
         "security_rating", "comment_lines_density", "duplicated_lines_density", "n_files"]
CK = ["WMC", "DIT", "NOC", "CBO", "RFC", "LCOM", "Ca", "Ce", "NPM", "LCOM3", "LOC", "DAM", "MOA",
      "MFA", "CAM", "IC", "CBM", "AMC", "max_CC", "avg_CC", "n_classes", "n_dropped"]
HAL = ["n1", "n2", "N1", "N2"]
GIT = ["commit_count", "lines_added", "lines_deleted", "code_churn", "contributors_count",
       "git_files_changed", "files_changed", "window_days"]


HIST_PATTERNS = [   # (regex, group, meaning, unit, range, role)
 (r"^td_(\d+)w_lag$", "history", "total_principal {0} weekly snapshots earlier", "minutes", ">=0", "FEATURE"),
 (r"^td_change_(\d+)w$", "history", "total_principal(t0) - total_principal {0} weekly snapshots earlier", "minutes", "any", "FEATURE"),
 (r"^td_slope_(\d+)w$", "history", "OLS slope of the last {0} weekly total_principal values (needs all {0})", "minutes/week", "any", "FEATURE"),
 (r"^td_volatility_4w$", "history", "population std of the last 4 weekly total_principal values", "minutes", ">=0", "FEATURE"),
 (r"^td_growth_rate_4w$", "history", "td_change_4w / td_4w_lag (0 if 0->0; empty if 0->>0 or lag unknown)", "ratio", "any", "FEATURE"),
 (r"^td_history_points_(\d+)w$", "flag", "how many of the last {0} weekly values exist", "count", "0-{0}", "FLAG"),
 (r"^finding_density_t0$", "history", "1000 x violations / ncloc (finding_count_t0 = sonar_violations)", "per KLOC", ">=0", "FEATURE"),
 (r"^development_cost_t0$", "history", "30 min x ncloc (SonarQube's default development cost)", "minutes", ">=0", "FEATURE"),
 (r"^fn_count$", "history", "methods + constructors parsed from the source", "count", ">=0", "FEATURE"),
 (r"^fn_complexity_max$", "history", "highest method cyclomatic complexity (0 = no methods)", "-", ">=0", "FEATURE"),
 (r"^fn_complexity_mean$", "history", "average method cyclomatic complexity (0 = no methods)", "-", ">=0", "FEATURE"),
 (r"^fn_complexity_dist_(\d+)$", "history", "methods with complexity in SonarQube bucket starting at {0} ([1,2) [2,4) [4,6) [6,8) [8,10) [10,12) [12,+))", "count", ">=0", "FEATURE"),
 (r"^git_commits_(\d+)d$", "history", "distinct commits touching the main Java files that exist at t0, last {0} days (deleted files not counted)", "count", ">=0", "FEATURE"),
 (r"^git_lines_churned_(\d+)d$", "history", "lines added + deleted in main Java files in the last {0} days", "lines", ">=0", "FEATURE"),
 (r"^churn_slope_(\d+)d$", "history", "OLS slope of churn over equal sub-windows of the last {0} days", "lines/week", "any", "FEATURE"),
 (r"^git_commit_acceleration$", "history", "commits in last 7 days - commits in the 7 days before", "count", "any", "FEATURE"),
 (r"^git_churn_acceleration$", "history", "churn in last 7 days - churn in the 7 days before", "lines", "any", "FEATURE"),
 (r"^commit_burstiness_180d$", "history", "variance/mean of commit counts in 26 sub-windows of 180 days", "-", ">=0", "FEATURE"),
 (r"^churn_burstiness_180d$", "history", "variance/mean of churn in 26 sub-windows of 180 days", "-", ">=0", "FEATURE"),
 (r"^major_author_commits$", "history", "commits by the most active author, all history up to t0", "count", ">=0", "FEATURE"),
 (r"^knowledge_fragmentation_180d$", "history", "Shannon entropy of authors' commit shares, last 180 days", "bits", ">=0", "FEATURE"),
 (r"^complexity_slope_(\d+)d$", "history", "slope of complexity per 1,000 lines over the last {0} days (as-of)", "per KLOC/week", "any", "FEATURE"),
 (r"^duplication_change_(\d+)d$", "history", "change in duplicated-lines density vs {0} days earlier", "%", "any", "FEATURE"),
 (r"^cognitive_complexity_change_(\d+)d$", "history", "change in cognitive complexity vs {0} days earlier", "-", "any", "FEATURE"),
 (r"^ncloc_change_(\d+)d$", "history", "change in ncloc vs {0} days earlier", "lines", "any", "FEATURE"),
 (r"^violations_change_(\d+)d$", "history", "change in violations vs {0} days earlier", "count", "any", "FEATURE"),
 (r"^debt_density_change_(\d+)d$", "history", "change in 1000 x total_principal/ncloc vs {0} days earlier", "min per KLOC", "any", "FEATURE"),
 (r"^sonar_history_ok_(\d+)d$", "flag", "1 = a snapshot at least {0} days old exists (the {0}d SonarQube columns are filled)", "0/1", "0-1", "FLAG"),
 (r"^mod_avg_complexity$", "history", "average SonarQube complexity of the module's files (module level)", "-", ">=0", "FEATURE"),
 (r"^parent_module_id$", "key", "parent folder of the module ('.' = repository root)", "-", "text", "ID"),
 (r"^afferent_coupling_ca$", "history", "other modules importing a class of this module (module level)", "modules", ">=0", "FEATURE"),
 (r"^efferent_coupling_ce$", "history", "other modules whose classes this module imports (module level)", "modules", ">=0", "FEATURE"),
 (r"^module_lineage_status$", "flag", "CONTINUED / RENAMED / NEW vs the previous snapshot", "-", "text", "FLAG"),
 (r"^module_lineage_confidence$", "flag", "HIGH / MEDIUM / LOW", "-", "text", "FLAG"),
 (r"^lineage_id$", "key", "stable file identity across renames (group rows of one file by this)", "-", "text", "ID"),
 (r"^lineage_status$", "flag", "NEW / UNCHANGED / MODIFIED / RENAMED vs the previous snapshot", "-", "text", "FLAG"),
 (r"^lineage_confidence$", "flag", "HIGH, or AMBIGUOUS (copied/split file: no targets)", "-", "text", "FLAG"),
 (r"^file_extension$", "history", "file extension", "-", "text", "FEATURE"),
 (r"^file_created_date$", "meta", "date of the first commit of this file (following renames)", "date", "YYYY-MM-DD", "META"),
 (r"^file_age_days$", "history", "days since the file was created (following renames)", "days", ">=0", "FEATURE"),
 (r"^file_deleted$", "meta", "1 = file is gone in the NEXT snapshot. FUTURE information - never an input", "0/1", "0-1", "META"),
 (r"^parse_ok$", "flag", "1 = the Java parser could read the file (fn_* filled)", "0/1", "0-1", "FLAG"),
 (r"^parse_failed_files$", "flag", "files the Java parser could not read", "count", ">=0", "FLAG"),
 (r"^target_td_(3w|1m|3m)$", "TARGET", "total_principal of the same entity {0} later (3w=3, 1m=4, 3m=12 weekly snapshots)", "minutes", ">=0", "TARGET"),
 (r"^target_td_(3w|1m|3m)_status$", "TARGET", "OBSERVED / BEYOND_RUN / WEEK_NOT_SCANNED / ENTITY_GONE / AMBIGUOUS_LINEAGE", "-", "text", "TARGET"),
]
ROLE_BY_GROUP = {"key": "ID", "flag": "FLAG", "TARGET": "FEATURE", "sonarqube": "FEATURE", "ck": "FEATURE",
                 "halstead": "FEATURE", "git": "FEATURE", "history": "FEATURE", "meta": "META"}
REQUESTED = {   # names asked for -> where they are in the mart
 "technical_debt_minutes_t0": "total_principal", "finding_count_t0": "sonar_violations",
 "file_cyclomatic_complexity": "sonar_complexity (level=file)", "file_lines_of_code": "sonar_ncloc (level=file)",
 "mod_lines_of_code": "sonar_ncloc (level=module)", "path_at_t0": "path",
 "file_lines_churned_{21,30,90,180}d": "git_lines_churned_{N}d (level=file)",
 "mod_lines_churned_{21,30,90,180}d": "git_lines_churned_{N}d (level=module)",
 "file_total_commits_{21,30,90,180}d": "git_commits_{N}d (level=file)",
 "file_major_author_commits": "major_author_commits (level=file)",
 "mod_knowledge_fragmentation": "knowledge_fragmentation_180d (level=module)",
 "Churn / Commit Burstiness": "churn_burstiness_180d / commit_burstiness_180d",
 "Function complexity distribution": "fn_complexity_dist_{1,2,4,6,8,10,12} (+ fn_count, fn_complexity_max/mean)",
 "Development cost": "development_cost_t0",
 "lineage_confidence / lineage_status (module)": "module_lineage_confidence / module_lineage_status",
}


def describe(c):
    import re as _re
    for pat, g, mean, unit, rng, role in HIST_PATTERNS:
        m = _re.match(pat, c)
        if m:
            arg = m.group(1) if m.groups() else ""
            return g, mean.format(arg), unit.format(arg), rng.format(arg), role
    g, mean, unit, rng = D.get(c, ("other", "", "", ""))
    if c.startswith("sonar_folder_level_"):
        g, mean, unit, rng = ("sonarqube", "part of the module value that comes from issues on folders (already included)", "", ">=0")
    role = ROLE_BY_GROUP.get(g, "FEATURE")
    return g, mean, unit, rng, role


def rename(df):
    m = {}
    for c in df.columns:
        if c in SONAR:
            m[c] = "sonar_" + c
        elif c.startswith("folder_level_"):
            m[c] = "sonar_" + c
        elif c in CK:
            m[c] = "ck_" + c
        elif c in HAL:
            m[c] = "halstead_" + c
        elif c in GIT:
            m[c] = "git_" + c.replace("git_", "")
    return df.rename(columns=m)


def tidy(df, level, pid, plan):
    df = rename(df.copy())
    df.insert(0, "level", level)
    df.insert(0, "project_id", pid)
    df["week"] = pd.to_datetime(df["week"]).dt.strftime("%Y-%m-%d")
    if plan is not None and "commit_date" not in df:
        df = df.merge(plan[["sha", "commit_date"]].drop_duplicates("sha"), on="sha", how="left")
    weeks = sorted(df["week"].unique())
    df["week_index"] = df["week"].map({w: i for i, w in enumerate(weeks)})
    wk = pd.Series(pd.to_datetime(weeks), index=weeks)
    gap = wk.diff().dt.days
    sha_by_week = df.drop_duplicates("week").set_index("week")["sha"]
    prev_sha = sha_by_week.shift(1)
    df["days_since_prev_week"] = df["week"].map(gap)
    df["same_commit_as_prev_week"] = df["week"].map((sha_by_week == prev_sha).astype(int))
    if level == "file":
        # SonarQube leaves a measure out when it is 0 for a file (e.g. a file with no bugs).
        # Checked: with empty = 0, the files add up exactly to the project totals.
        # Kind 1 - real zeros: SonarQube omits a measure that is 0 for a file
        zero = [c for c in df.columns if c.startswith("sonar_") and not c.endswith("_rating")
                and c != "sonar_coverage"]
        df[zero] = df[zero].fillna(0)
        if "total_principal" in df:
            df["total_principal"] = df["total_principal"].fillna(0)
        # Kind 2 - does not apply: no Java class (package-info.java, Kotlin) -> stay empty + flags
        fn = df["file"].astype(str)
        df["is_package_info"] = fn.str.endswith("package-info.java").astype(int)
        df["has_ck"] = df["ck_WMC"].notna().astype(int) if "ck_WMC" in df else 0
        df["has_halstead"] = (df["halstead_volume"].notna().astype(int)
                              if "halstead_volume" in df else 0)
    # Kind 3 - not measured: tests were never run, so coverage is unknown (not 0%)
    if "sonar_coverage" in df:
        df["sonar_coverage"] = np.nan
    if "total_principal" in df and "sonar_ncloc" in df:
        df["td_density"] = np.where(df["sonar_ncloc"] > 0, df["total_principal"] / df["sonar_ncloc"], np.nan)
    keys = [c for c in ["project_id", "level", "week", "week_index", "sha", "commit_date", "module",
                        "parent_module_id", "file", "path", "lineage_id", "lineage_status",
                        "lineage_confidence", "module_lineage_status", "module_lineage_confidence",
                        "same_commit_as_prev_week", "days_since_prev_week",
                        "is_package_info", "has_ck", "has_halstead",
                        "total_principal", "td_density"] if c in df]
    rest = [c for g in ["sonar_", "ck_", "halstead_", "git_"] for c in df.columns
            if c.startswith(g) and c not in keys]
    targets = [c for c in df.columns if c.startswith("target_")]
    other = [c for c in df.columns if c not in keys + rest + targets
             and c not in ("idx", "t0", "file_deleted")]
    meta = [c for c in ("file_deleted",) if c in df]
    return df[keys + rest + other + meta + targets]


def md_table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def kv(items):
    out = {}
    for it in items or []:
        k, v = it.split("=", 1)
        out[k] = os.path.expanduser(v)
    return out


def last_fingerprint(folder):
    mp = os.path.join(folder, "analysis_meta.csv")
    if not os.path.exists(mp):
        return None
    m = pd.read_csv(mp, sep=";")
    return None if m.empty else m.iloc[-1].to_dict()


def cross_run_checks(runs, levels):
    """Checks that only make sense when several projects are stacked in one mart."""
    out = ["===== across projects ====="]
    fps = {pid: last_fingerprint(f) for pid, f in runs.items()}
    missing = [p for p, f in fps.items() if f is None]
    keys = {p: (str(f.get("sonarqube_version")), str(f.get("quality_profile")), str(f.get("rules_hash")))
            for p, f in fps.items() if f is not None}
    if missing:
        out.append(f"[WARN] no analyzer fingerprint (analysis_meta.csv) for: {missing} - "
                   f"run: python fingerprint.py --out <run folder>")
    if len(set(keys.values())) > 1:
        out.append("[FAIL] projects were analysed with DIFFERENT SonarQube versions / rule sets - "
                   "TD values are not comparable across them:")
        out += [f"       {p}: version {k[0]}, profile {k[1]}, rules_hash {k[2]}" for p, k in keys.items()]
    elif keys:
        k = next(iter(keys.values()))
        out.append(f"[PASS] same analyzer for {len(keys)} project(s): SonarQube {k[0]}, "
                   f"profile '{k[1]}', rules_hash {k[2]}")
    for lvl, parts in levels.items():
        cols = {pid: set(df.columns) for pid, df in zip(runs, parts)}
        allc = set().union(*cols.values())
        for pid, c in cols.items():
            gone = sorted(allc - c)
            if gone:
                out.append(f"[WARN] {lvl}: {pid} lacks {len(gone)} column(s) other projects have "
                           f"(empty in the mart): {gone[:8]}{' ...' if len(gone) > 8 else ''}")
        for pid, df in zip(runs, parts):
            ck = [c for c in df.columns if c.startswith("ck_")]
            if ck and df[ck].isna().all().all():
                out.append(f"[WARN] {lvl}: {pid} has no CK values (no compiled classes?)")
    if len(runs) > 1:
        out.append("[INFO] several projects: split train/test by project_id or by time, "
                   "never randomly across rows")
    if not any(l.startswith(("[FAIL]", "[WARN]")) for l in out[1:]):
        out.append("[PASS] all projects have the same columns")
    return "\n".join(out) + "\n"


def write_parquet(df, path):
    """Parquet copy of a mart table: keeps column types, ~5-10x smaller, what Hugging Face
    datasets load fastest. Needs pyarrow (pip install pyarrow); skipped with a note if missing."""
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        if not getattr(write_parquet, "warned", False):
            print("NOTE: pyarrow not installed -> no Parquet files (pip install pyarrow)")
            write_parquet.warned = True
        return
    d = df.copy()
    for c in d.columns:                         # mixed text/number columns -> text
        if d[c].dtype == object:
            d[c] = d[c].astype("string")
    d.to_parquet(path, index=False, compression="zstd")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="name=output_folder")
    ap.add_argument("--plan", action="append", help="name=plan_csv (adds real commit dates)")
    ap.add_argument("--paper", action="append", help="name=zenodo_csv (adds validation vs paper)")
    ap.add_argument("--repo", action="append", help="name=git_clone (adds the stale-scan check)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    runs, plans, papers, repos = kv(a.run), kv(a.plan), kv(a.paper), kv(a.repo)
    out = os.path.expanduser(a.out)
    os.makedirs(out, exist_ok=True)

    levels = {"project": [], "module": [], "file": []}
    report = []
    summary = []
    for pid, folder in runs.items():
        plan = pd.read_csv(plans[pid], sep=";") if pid in plans else None
        if plan is None and pid in repos:          # no paper plan: real commit dates from git
            shas = pd.read_csv(os.path.join(folder, "project_level.csv"), sep=";", usecols=["sha"]).sha.unique()
            r = subprocess.run(["git", "-C", repos[pid], "show", "-s", "--format=%H %cs", *shas],
                               capture_output=True, text=True)
            pairs = [l.split() for l in r.stdout.splitlines() if len(l.split()) == 2]
            if pairs:
                plan = pd.DataFrame(pairs, columns=["sha", "commit_date"])
        pcols = pd.read_csv(os.path.join(folder, "project_level.csv"), sep=";", nrows=1).columns
        missing = [g for g, c in [("Halstead", "halstead_volume"), ("git", "commit_count")] if c not in pcols]
        if "td_3w_lag" not in pcols:
            print(f"NOTE {pid}: no history columns - run first: python history.py --repo <clone> --out {folder}")
        if missing:
            sys.exit(f"{pid}: {', '.join(missing)} metrics are missing in {folder}. Run first:\n"
                     f"  python add_extras.py --repo <the git clone> --out {folder}")
        for lvl in levels:
            df = pd.read_csv(os.path.join(folder, f"{lvl}_level.csv"), sep=";")
            levels[lvl].append(tidy(df, lvl, pid, plan))
        cmd = [sys.executable, os.path.join(HERE, "validate.py"), "--out", folder]
        if pid in papers:
            cmd += ["--paper", papers[pid]]
        if pid in repos:
            cmd += ["--repo", repos[pid]]
        else:
            print(f"NOTE {pid}: no --repo {pid}=<clone> given -> stale-scan check skipped")
        res = subprocess.run(cmd, capture_output=True, text=True)
        report.append(f"===== {pid}  ({folder}) =====\n{res.stdout}{res.stderr}\n")
        st = pd.read_csv(os.path.join(folder, "status.csv"), sep=";")
        p = levels["project"][-1]
        mfile = os.path.join(folder, "snapshot_method.txt")
        method = open(mfile).read().strip() if os.path.exists(mfile) else \
            ("paper_aligned" if pid in plans else "weekly")
        summary.append({"project_id": pid, "snapshot_method": method,
                        "weeks_ok": len(p), "weeks_planned": len(st),
                        "weeks_failed": int((st.status != "SUCCESS").sum()),
                        "first_week": p.week.min(), "last_week": p.week.max(),
                        "modules": levels["module"][-1].module.nunique(),
                        "file_rows": len(levels["file"][-1])})

    report.append(cross_run_checks(runs, levels))
    frames = {}
    for lvl, parts in levels.items():
        df = pd.concat(parts, ignore_index=True)
        df.to_csv(os.path.join(out, f"mart_{lvl}.csv"), index=False)
        write_parquet(df, os.path.join(out, f"mart_{lvl}.parquet"))
        frames[lvl] = df
    allv = pd.concat(frames.values(), ignore_index=True, sort=False)
    order = [c for c in frames["file"].columns] + [c for c in allv.columns if c not in frames["file"].columns]
    allv = allv[[c for c in order if c in allv.columns]]
    tail = [c for c in allv.columns if c == "file_deleted" or c.startswith("target_")]
    allv = allv[[c for c in allv.columns if c not in tail] + tail]
    allv.to_csv(os.path.join(out, "mart_all_levels.csv"), index=False)
    write_parquet(allv, os.path.join(out, "mart_all_levels.parquet"))

    # dictionary: only columns that exist
    rows = []
    same_week_target_parts = {"total_principal", "td_density", "sonar_sqale_index",
                              "sonar_reliability_remediation_effort", "sonar_security_remediation_effort",
                              "sonar_sqale_debt_ratio"}
    for c in allv.columns:
        g, mean, unit, rng, role = describe(c)
        lv = [l for l, f in frames.items() if c in f.columns and f[c].notna().any()]
        nn = allv[c].notna().mean()
        note = ""
        if c in same_week_target_parts:
            note = "t0 value of the target or its part: fine for forecasting t0+h, NOT for predicting t0 itself"
        elif role == "TARGET":
            note = "future value - never a model input"
        elif role == "META":
            note = "not a model input"
        rows.append({"column": c, "role": role, "group": g, "meaning": mean, "unit": unit,
                     "valid_range": rng, "levels": ",".join(lv), "filled_share": round(nn, 3),
                     "leakage_note": note})
    pd.DataFrame(rows).to_csv(os.path.join(out, "data_dictionary.csv"), index=False)

    with open(os.path.join(out, "validation_report.txt"), "w") as f:
        f.write("\n".join(report))

    s = pd.DataFrame(summary)
    readme = README.format(
        date=dt.date.today().isoformat(),
        summary=md_table(s),
        rows="\n".join(f"| `mart_{l}.csv` | {len(frames[l]):,} | {frames[l].shape[1]} |" for l in frames),
        allrows=f"{len(allv):,}", allcols=allv.shape[1])
    readme += HISTORY_README + "\n| Asked for | In the mart |\n|---|---|\n" + \
        "\n".join(f"| `{k}` | `{v}` |" for k, v in REQUESTED.items()) + "\n"
    with open(os.path.join(out, "README.md"), "w") as f:
        f.write(readme)

    # per-project diagnostics, to investigate a project later without its run folder
    DIAG = ["status.csv", "build_errors.csv", "preflight.csv", "build_settings.json",
            "analysis_meta.csv", "weeks_plan.csv", "snapshot_method.txt", "validation.txt"]
    for pid, folder in runs.items():
        dd = os.path.join(out, "diagnostics", pid)
        os.makedirs(dd, exist_ok=True)
        for fn in DIAG:
            if os.path.exists(os.path.join(folder, fn)):
                shutil.copy2(os.path.join(folder, fn), os.path.join(dd, fn))
    write_manifest(out, runs, frames, allv)
    zp = shutil.make_archive(out.rstrip("/"), "zip", out)
    print(s.to_string(index=False))
    print(f"\nmart written to {out}\nzip: {zp}  ({os.path.getsize(zp)/1e6:.1f} MB)")


def write_manifest(out, runs, frames, allv):
    """What was built, from what, with which tools - plus a checksum per file, so anyone can
    verify they have exactly this version of the data."""
    import hashlib, json, platform
    def sha(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    vers = {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__}
    try:
        import javalang
        vers["javalang"] = getattr(javalang, "__version__", "installed")
    except ImportError:
        pass
    analyzers = {}
    for pid, folder in runs.items():
        mp = os.path.join(folder, "analysis_meta.csv")
        if os.path.exists(mp):
            analyzers[pid] = pd.read_csv(mp, sep=";").to_dict("records")
    files = {}
    for root, _, names in os.walk(out):
        for n in sorted(names):
            fp = os.path.join(root, n)
            fn = os.path.relpath(fp, out)
            if fn != "manifest.json":
                files[fn] = {"bytes": os.path.getsize(fp), "sha256": sha(fp)}
    man = {"created": dt.datetime.now().isoformat(timespec="seconds"), "tool_versions": vers,
           "runs": runs, "analyzer_per_run": analyzers,
           "rows": {l: len(f) for l, f in frames.items()}, "columns": int(allv.shape[1]),
           "settings": {"day_windows": [21, 30, 90, 180], "week_lags": [1, 3, 4, 12],
                        "targets_weeks": {"3w": 3, "1m": 4, "3m": 12},
                        "ck_aggregation": "class values weighted by class LOC (paper sec. 4.2)",
                        "dev_cost_min_per_line": 30},
           "files": files}
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(man, f, indent=2, default=str)


HISTORY_README = """
## History features, targets and roles (history.py)

- **Every column has a role** in `data_dictionary.csv`: `ID`, `FEATURE`, `FLAG`, `META`, `TARGET`.
  Train only on `FEATURE` (+ `FLAG` if useful). `TARGET` and `META` columns are never inputs.
- **Targets:** `target_td_3w`, `target_td_1m`, `target_td_3m` = `total_principal` of the same
  project / module / file 3, 4 and 12 weekly snapshots later. Use a target only where its
  `*_status == OBSERVED`. Missing targets are never filled.
- **Week windows** (`td_*_lag`, `td_change_*w`, `td_slope_*w`, `td_volatility_4w`) count weekly
  snapshots, like the paper's sliding window. **Day windows** (`_21d`, `_30d`, `_90d`, `_180d`)
  use real commit time: (t0 - N days, t0]. Nothing after t0 is ever read, except the targets
  and the META column `file_deleted`.
- SonarQube-based day-window changes compare t0 with the latest snapshot at least N days older;
  if there is none, the cell is empty and `sonar_history_ok_<N>d = 0`.
- **Files are followed across renames** (`lineage_id`). Group by `lineage_id` (file level) or
  `module` (module level) when making cross-validation folds, so one file never sits on both sides.
- Files whose identity is ambiguous (copied / split, `lineage_confidence = AMBIGUOUS`) get no targets.
- Git day-window features count **main Java files** (`src/main/java`, or `src/java` in old Apache projects), so they add up exactly
  file -> module -> project (commits are distinct commits, so module commit counts can add to more).
- **CK metrics are LOC-weighted** like the paper (sec. 4.2): the class values are averaged with
  each class's lines of code as the weight - at file, module and project level.
- Module-only: `mod_avg_complexity`, `parent_module_id`, `afferent_coupling_ca`,
  `efferent_coupling_ce` (from Java imports between modules), `module_lineage_*`.
- Function complexity (`fn_*`) is computed by parsing the source (1 + if/for/while/do/case/catch/?:/&&/||
  per method); it is close to, but not identical with, SonarQube's own complexity.

### Requested column names -> mart columns
One column per measure, with the same name at every level (filter by `level`); the names
asked for map like this:
"""


README = """# Technical-debt data mart

Made {date} with td_pipeline (SonarQube + CKJM Extended + Halstead + git), following
Tsoukalas et al. (2020) "Technical debt forecasting: An empirical study on open-source repositories".

## Projects

{summary}

`snapshot_method`: **paper_aligned** = every row is the commit behind a paper row (matched by
content: Java lines + file count), so it can be compared with the paper week by week ·
**weekly_on_paper_dates** = the paper's rows match no commit (it scanned a different scope), so one
real commit per week on the paper's dates; compare with the paper by trend only · **weekly** = not
a paper repo, one real commit per week.

## Files

| File | Rows | Columns |
|---|---|---|
{rows}
| `mart_all_levels.csv` | {allrows} | {allcols} |
| `*.parquet` | same as the CSVs | same; typed and compressed (pandas `read_parquet`, Hugging Face) |
| `diagnostics/<project>/` | - | per-week status, build errors, preflight, build settings, analyzer, validation |
| `data_dictionary.csv` | one row per column | meaning, unit, valid range, levels |
| `validation_report.txt` | - | automatic checks per project (+ comparison with the paper) |

- One row = one **week** (snapshot) of one **project**, **module** or **Java file**.
- `mart_all_levels.csv` = the three stacked; filter with the `level` column.
- Keys: `project_id, level, week, module, file`. `sha` = commit analysed.
- **Target:** `total_principal` (minutes) = `sonar_sqale_index + sonar_reliability_remediation_effort + sonar_security_remediation_effort`.
  `td_density` = `total_principal / sonar_ncloc`.
- Column groups (prefix): `sonar_` SonarQube, `ck_` CKJM Extended (LOC-weighted average per class),
  `halstead_` Halstead, `git_` git activity (since the previous snapshot, or over `_Nd` day windows).

## How it was made

1. Weekly snapshots: for paper projects, every paper row was matched to its real commit by
   content (Java lines, pom.xml lines, file count) - the paper's date labels do not follow the
   real commit dates. `week` = paper label, `commit_date` = real commit date.
2. Each snapshot: built with JDK 8 / Maven 3.6.3 (tests skipped), analysed with SonarQube
   Community (current version, *Standard Experience* mode, Java profile **Sonar way comprehensive**),
   main Java code only.
3. CK metrics: CKJM Extended on the compiled classes, class values averaged with class LOC as the
   weight (paper sec. 4.2), at file/module/project level.
4. Halstead: javalang tokens; operators = operators + all keywords, operands = identifiers +
   literals; module/project use the union of distinct tokens.
5. Git: commits between the previous snapshot and this one, merges excluded, authors by e-mail.

## Things to know before modelling

- **Uneven real time:** paper weeks are not 7 real days apart. `git_window_days` gives the real
  length of each window; `same_commit_as_prev_week = 1` means the values just repeat.
- **Missing weeks:** a commit that could not be built is missing (`days_since_prev_week = 14`).
- **Module `(project)`** (module level): issues SonarQube raises on the whole project, not on any
  module. Keep it if module totals must equal the project; drop it for per-module models.
- **TD level vs paper:** the newer SonarQube rule set gives a lower TD level than the paper
  (retrofit: ~60%), but the trend agrees (Spearman rho 0.95-0.99). Size/complexity/duplication
  match exactly. Per-project numbers are in `validation_report.txt`.
- `sonar_coverage` is empty (not measured: tests were not run, as in the paper) and
  `sonar_uncovered_lines` = `sonar_lines_to_cover`.
- File level: `package-info.java` and Kotlin files have no CK / Halstead values (no Java class).
- **Empty values at file level - three kinds, handled differently:**
  1. *Real zeros* (`sonar_` counts/efforts, `total_principal`): SonarQube omits a measure when it
     is 0 for a file. Filled with **0** - this is the true value, not an imputation (checked: files
     then add up exactly to the project totals). Do NOT impute these with mean/median.
  2. *Does not apply* (`ck_`, `halstead_` for package-info.java / Kotlin files): left **empty**,
     flagged by `has_ck`, `has_halstead`, `is_package_info`. Tree models (XGBoost/LightGBM) handle
     empty natively; otherwise drop rows with `is_package_info = 1` (they have no TD).
  3. *Not measured* (`sonar_coverage`): tests were not run, so it is **empty** everywhere - drop it.
- **Java Driller cohesion (`jd_cohesion`) is often empty, on purpose.** It is 1 / LCOM4 and is
  empty when no class in the file has a method with code: interfaces, annotation types (`@GET`),
  enums, exception classes with only constructors. The empty share shows the repo's design style,
  not a data problem (share of file rows: commons-io 6.0%, zxing 8.4%, okhttp 15.4%, dubbo 22.0%,
  retrofit 35.2%, java-websocket 47.0%). Keep it empty ("does not apply"); do not fill with 0.
- **Zero-inflated target at file level:** most files have total_principal = 0. Consider
  `log1p(total_principal)`, a Tweedie/Poisson loss, or a two-step model (any TD? -> how much?).
- **Modules come and go:** modules are added, moved or removed over time (e.g. converters/adapters),
  so the module panel is unbalanced - a module has rows only for weeks where it existed.
  The same holds for files.
- **Same commit, tiny differences:** in 2 of the repeated-commit weeks, SonarQube reported 1 extra
  code smell (+10 min) on the identical code - SonarQube itself is not 100% deterministic.
  Effect < 0.5%.
- Constant / empty columns (no information): `sonar_coverage` (empty), `sonar_*_rating`, `ck_n_dropped`.
- **Target leakage - do NOT use as features when predicting `total_principal` of the same week:**
  `td_density`, `sonar_sqale_index`, `sonar_reliability_remediation_effort`,
  `sonar_security_remediation_effort` (they ARE the target's parts), `sonar_sqale_debt_ratio`
  (= sqale_index / ncloc). For **forecasting** (predict week t+h from weeks <= t), past values of
  these are fine and useful.
- **Strongly related features:** `sonar_ncloc`, `sonar_lines`, `sonar_statements`,
  `halstead_length` and `ck_LOC` all measure size (correlation ~1). Pick one or reduce them.
- **Git at module level:** `git_commit_count` / `git_contributors_count` count commits/authors that
  touched the module, so a commit touching 2 modules counts in both - module values add up to
  MORE than the project. Lines added/deleted/churn add up exactly. Changes to files outside every
  Java module (root pom.xml, README, ...) are in the `(project)` row.
- **Files with holes:** a few files disappear and come back later (deleted and re-created, e.g.
  `RequestFactory.java`). That is real history, not missing data.
- `git_window_days` is 0 for weeks that repeat the previous commit and up to ~68 days elsewhere.
- The paper normalised bugs, code_smells, duplicated_blocks, Ca (its selected features) and the
  target by `ncloc` before regression - do the same if you reproduce it.

## Java Driller columns (`jd_*`) on all three levels

Java Driller (the team's tool, pipeline version, JavaParser 3.26.2) reads the source of every
snapshot and records which project file uses which other project file (`raw_jd_deps.csv` in the
run folder). From that list the same measures exist for a file, a module and the whole project:

| Measure | File | Module | Project |
|---|---|---|---|
| outgoing dependencies | `jd_fan_out` | `jd_dependencies` (sum of its files) | `jd_dependencies` (all edges) |
| outgoing cross-module dependencies | `jd_cross_module_deps`: from this file into another module | `jd_cross_module_deps`: from its files into other modules | `jd_cross_module_deps`: all cross-module edges |
| incoming cross-module dependencies | `jd_cross_module_in`: from other modules into this file | `jd_cross_module_in`: from other modules into its files | `jd_cross_module_in`: all cross-module edges (= outgoing) |
| cross-module share | `jd_cross_dep_share` = cross-module out / fan-out | `jd_cross_dep_share` = cross-module out / dependencies | `jd_cross_dep_share` = cross-module edges / all edges |
| methods | `jd_method_count` | `jd_method_count` (sum) | `jd_method_count` (sum) |
| classes | `jd_class_count` | `jd_class_count` (sum) | `jd_class_count` (sum) |
| cohesion (1 / LCOM4) | `jd_cohesion` (mean over the file's classes) | `jd_cohesion_mean` (files weighted by ncloc) | `jd_cohesion_mean` (files weighted by ncloc) |
| classes measured for cohesion | `jd_lcom4_classes` | sum | sum |
| classes doing more than one job (LCOM4 > 1) | `jd_noncohesive_classes` | sum | sum |
| share of classes doing more than one job | `jd_noncohesive_share` | sum of non-cohesive / sum of measured | same, whole project |
| tests | `jd_has_test` (0/1) | `jd_test_share` (share of files) | `jd_test_share` (share of files) |

File level only: `jd_fan_in` (project files that use this file), `jd_external_class_count`
(classes in other files that use this file's classes), `jd_coupling` (distinct files linked
either way).

- `jd_cross_dep_share` runs from 0 (every dependency stays inside the module: self-contained) to
  1 (every dependency leaves it: tangled with other modules). Empty when there are no dependencies.
- Single-module repos (commons-io, java-websocket) have 0 cross-module dependencies by definition.
- Cohesion above file level: an average hides the bad classes, so two values are given.
  `jd_cohesion_mean` weights each file by its lines of code (a 5-line helper does not count as
  much as a 2,000-line core class - the same rule as the CK columns, paper sec. 4.2).
  `jd_noncohesive_share` counts classes: 0.20 = one class in five does more than one job.
- Cross-module dependencies of files add up exactly to modules and to the project (checked by
  `validate.py`).
- Where each measure comes from: LCOM4 - Hitz & Montazeri 1995; fan-in / fan-out - Henry &
  Kafura 1981 (doi 10.1109/TSE.1981.231113); coupling - CBO, Chidamber & Kemerer 1994
  (doi 10.1109/32.295895); tests by name - Van Rompaey & Demeyer 2009 (doi 10.1109/CSMR.2009.39);
  cross-module dependencies - MacCormack, Rusnak & Baldwin 2006 (doi 10.1287/mnsc.1060.0552).
- Java Driller works on source code, CKJM on compiled classes: `jd_fan_in` / `jd_fan_out` /
  `jd_coupling` count files, CKJM's `ck_Ca` / `ck_Ce` / `ck_CBO` count classes. They overlap -
  check their correlation and keep the one that predicts better.

## Flags and statuses explained

### File identity over time: `lineage_id`, `lineage_status`, `lineage_confidence`
A file's path can change (renamed, or moved to another folder). `lineage_id` is one id for
"the same file" in every snapshot, so its lags and targets follow it after a rename. Between two
scanned snapshots we run `git diff -M -C`: git treats a deleted file and an added file as a rename
when their contents are at least 50% similar.

| `lineage_status` | Meaning (compared with the previous scanned snapshot) |
|---|---|
| NEW | the file appears for the first time: added, copied from another file, or in the run's first snapshot |
| UNCHANGED | same path, git shows no change |
| MODIFIED | same path, content changed |
| RENAMED | new path, but git matched it to an old file; it keeps the old file's `lineage_id` |

| `lineage_confidence` | Meaning |
|---|---|
| HIGH | the file's identity is clear |
| AMBIGUOUS | git says the file was **copied** from another file, or one old file was renamed into **two or more** new files (a split). We cannot say which new file "is" the old one. It stays AMBIGUOUS for the rest of the run, keeps all its features, but gets no targets (`AMBIGUOUS_LINEAGE`). |

Example: `Call.java` moved from `okhttp/src/main/java/com/squareup/okhttp/` to
`okhttp/src/main/java/okhttp3/` (okhttp 3.0) is RENAMED with the same `lineage_id` when git finds the
two versions at least 50% alike, so `target_td_3w` of its last old-path row is read from its new-path row.

### Module identity: `module_lineage_status`, `module_lineage_confidence`
| Value | Meaning |
|---|---|
| CONTINUED (HIGH) | a module with this name existed in the previous snapshot |
| RENAMED (HIGH / MEDIUM) | a new name, but most of its files (by `lineage_id`) were in ONE other module before: HIGH when 80% or more, MEDIUM when 50-80% |
| NEW (HIGH / LOW) | a new module; LOW when some of its files existed elsewhere before but no single module gave half of them |

### Target status: `target_td_3w_status`, `target_td_1m_status`, `target_td_3m_status`
For a row at snapshot t and horizon h (3, 4 or 12 snapshots):

| Status | Meaning | Target value |
|---|---|---|
| OBSERVED | snapshot t+h was scanned and the same project / module / file (same `lineage_id`) is in it | filled |
| BEYOND_RUN | t+h is after the last snapshot of the run (the last 3, 4 or 12 rows of every run) | empty |
| WEEK_NOT_SCANNED | t+h is in the plan but could not be measured (its build failed) | empty |
| ENTITY_GONE | t+h was scanned, but this module or file is not in it: it was deleted (a rename is NOT gone - it is followed) | empty |
| AMBIGUOUS_LINEAGE | file level only: the file was copied or split, so its future self cannot be identified | empty |

**Why the status matters (survivorship bias).** If rows with an empty target are simply dropped,
the deleted files (ENTITY_GONE) disappear from training without anyone noticing. Deleted files are
often special (dead code, replaced classes), so the model would learn only from files that
survived. Train on `OBSERVED`, report how many rows each status has, and decide on purpose what to
do with the others (for example study ENTITY_GONE files separately). Nothing is filled in for you.

### Other flags
| Flag | 1 means | 0 means |
|---|---|---|
| `has_ck` | the file has CK values | no compiled class: package-info.java, Kotlin, or a class CKJM dropped |
| `has_halstead` | the file has Halstead values | the file could not be parsed as Java |
| `is_package_info` | the file is package-info.java (package docs only, no code, no TD) | an ordinary file |
| `same_commit_as_prev_week` | no new commit since the previous snapshot: the values just repeat | there is new code |
| `sonar_history_ok_<N>d` | a snapshot at least N days older exists, so the `_<N>d` SonarQube changes are filled | too early in the run: those cells are empty |
| `file_deleted` (META) | the file is gone in the next scanned snapshot. Future information - never an input | still there |

`days_since_prev_week` is not 0/1: it is the real number of days since the previous kept snapshot
(7 normally, 14 after one failed week).
"""

if __name__ == "__main__":
    main()
