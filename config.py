from contracts import read_json
import os
from pathlib import Path

# ============================================================
# REPOSITORY / PROJECT  (filled per repo by repo_context.json,
# which run_all_repos.py writes into each repo's working dir)
# ============================================================
PROJECT_KEY = ""
REPO_PATH = ""
REPOSITORY_ID = ""
BRANCH = "master"

_ctx_path = Path("repo_context.json")
if _ctx_path.exists():
    _ctx = read_json(_ctx_path)
    PROJECT_KEY = _ctx.get("project_key", PROJECT_KEY)
    REPO_PATH = _ctx.get("repo_path", REPO_PATH)
    REPOSITORY_ID = _ctx.get("repository_id", REPOSITORY_ID)
    BRANCH = _ctx.get("branch", BRANCH)

# Old scripts still say config.KAFKA_REPO_PATH -- same value, kept as an alias.
KAFKA_REPO_PATH = REPO_PATH

# ============================================================
# SONARQUBE -- keep credentials outside source control and archives.
# ============================================================
SONAR_URL = os.getenv('SONAR_URL', 'http://localhost:9000')
SONAR_TOKEN = os.getenv("SONAR_TOKEN", "")
SONAR_URL_FROM_SCANNER = os.getenv('SONAR_URL_FROM_SCANNER', 'http://host.docker.internal:9000')
DOCKER_NETWORK = None

JAVA_BINARIES_PATH = os.getenv('TD_JAVA_BINARIES') or None
SCANNER_IMAGE = os.getenv('SONAR_SCANNER_IMAGE', '')
BUILD_IMAGE = os.getenv('TD_BUILD_IMAGE', '')
COMPILED_EVIDENCE_FILE = os.getenv('TD_COMPILED_EVIDENCE', '')
LANGUAGE = "JAVA"
COMPATIBLE_RULE_DOMAIN_VERSION = "td-rule-domain-v1"

# ============================================================
# PIPELINE SETTINGS
# ============================================================
# Weekly calendar layout (computed from the repo, nothing hard-coded per repo):
#   week 1 starts at   midpoint - HISTORY_WEEKS      (warm-up so 6m windows are full)
#   T0 weeks           HISTORY_WEEKS+1 .. total - HORIZON_WEEKS
#   => T0 week HISTORY_WEEKS+1 starts exactly AT the repo midpoint.
HISTORY_WEEKS = 26      # longest trailing window (6m)
HORIZON_WEEKS = 12      # longest target horizon (3m)
T0_WEEKS = 100          # how many T0 weeks to produce (~100 needed for VALIDATION/TEST after purges)
DEFAULT_WEEKS = HISTORY_WEEKS + T0_WEEKS + HORIZON_WEEKS   # 138

# Dataset cleanliness (set False to keep the raw/ragged rows)
DROP_INELIGIBLE_ROWS = True            # keep only eligible_t0 == True (production Java + full 26w history)
REQUIRE_ALL_TARGETS_OBSERVED = False   # retain per-target unknowns; select OBSERVED targets when modeling
FILL_OMITTED_ZERO_MEASURES = False     # absence is unknown unless an explicit verified contract says otherwise

TARGET_HORIZONS = {"3w": 3, "1m": 4, "3m": 12}
SONAR_HISTORY_WINDOWS = {"3w": 3, "1m": 4, "3m": 12, "6m": 26}

ACTIVE_STATUSES = {"OPEN", "CONFIRMED", "REOPENED"}

NON_PRODUCTION_PATH_PATTERNS = (
    "/test/", "/tests/", "/generated/", "/build/", "/vendor/",
    "/example/", "/examples/", "/sample/", "/samples/",
    "/benchmark/", "/benchmarks/", "/jmh/", "/template/", "-template/",
)
# File-name rule for demo / benchmark classes inside normal source folders
# (gson ParseBenchmark.java, RawCollectionsExample.java; webgoat SampleAttack.java).
import re as _re
NON_PRODUCTION_FILENAME_REGEX = _re.compile(r"(Benchmark|Example|Sample)[A-Za-z0-9_]*\.java$")


# ============================================================
# MODULE-LEVEL EXTRACTION  (build_module_mart.py)
# ============================================================
# What is a "module"?
#   "build"   -> nearest ancestor directory that has a build descriptor (pom.xml, build.gradle,
#                build.gradle.kts). Right for multi-module Maven/Gradle repos (gson, webgoat, ...).
#   "package" -> Java package one level below the repo's common base package
#                (e.g. org.apache.commons.io.input). Right for single-build-module repos
#                (commons-io, commons-lang, jsoup), where "build" would give ONE module.
#   "auto"    -> "build" if production Java lives in >= 2 build modules, else "package".
# The decision is made ONCE per repo and frozen in <workdir>/module_strategy.json, so weekly
# updates never silently change what a module is. Use a fresh workspace to re-decide.
MODULE_STRATEGY = "auto"
EXTRA_PRODUCTION_ROOTS = ()  # explicit repository-specific legacy roots, each ending in '/'
MODULE_PACKAGE_EXTRA_DEPTH = 1          # "package" strategy: sub-package levels below the base package
BUILD_DESCRIPTORS = ("pom.xml", "build.gradle", "build.gradle.kts")
ROOT_MODULE_LABEL = "<root>"

# SonarQube's default development cost per line of code (Java), used for sqale_debt_ratio:
#   sqale_debt_ratio = sqale_index / (ncloc * DEV_COST_PER_LINE_MIN) * 100
# Change it if your server's "Development cost" setting (sonar.technicalDebt.developmentCost) differs.
DEV_COST_PER_LINE_MIN = 30
# SonarQube maintainability rating grid (upper bounds of the debt ratio, %): A<=5 B<=10 C<=20 D<=50 else E
SQALE_RATING_BOUNDS = ((5.0, "A"), (10.0, "B"), (20.0, "C"), (50.0, "D"))
