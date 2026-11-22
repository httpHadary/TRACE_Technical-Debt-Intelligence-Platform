# TD Forecasting Data Pipeline – Run Guide (fresh Linux)

This guide takes a **clean Ubuntu machine** (22.04 or 24.04) to a finished dataset at
**project level, module level and file level**. It rebuilds the data of
*Tsoukalas et al. (2020), "Technical debt forecasting: An empirical study on open-source repositories"*.

The test repo is **square/retrofit**:
- It is one of the 15 projects in the paper, so we can compare our numbers with theirs.
- It is small and builds with Maven in the paper's period (2015–2018).
- It has several modules, so the module level is a real test.

---

## 0. What you will have at the end

| File | One row = | Use |
|---|---|---|
| `project_level.csv` | one week | same shape as the paper's dataset |
| `module_level.csv` | one module in one week | module-level forecasting |
| `file_level.csv` | one `.java` file in one week | file-level forecasting |
| `validate.py` report | – | PASS/WARN/FAIL checks + comparison with the paper |

**Time needed:** setup takes about 1 hour. Each week of data takes 2–4 minutes, so
5 weeks (the quick test) is about 15 minutes and 150 weeks (the full run) is 5–8 hours.

**Machine:** at least 8 GB RAM (SonarQube alone uses about 3–4 GB), 30 GB free disk, and internet.

### How the pieces fit

```
GitHub repo ──git checkout (1 commit per week)──► source code
                                                     │
                     Maven 3.6.3 + JDK 8 (build) ◄───┘
                                                     │ compiled .class files
               ┌─────────────────────────────────────┤
               ▼                                     ▼
   sonar-scanner (back-dated)                 CKJM Extended (Java 17)
               │                                     │
               ▼                                     │
   SonarQube server (Docker)                         │
   bugs, code smells, TD minutes…                    │ WMC, DIT, CBO, Ca…
               └──────────► td_pipeline.py ◄─────────┘
                                 │
          project_level.csv  module_level.csv  file_level.csv
                                 │
                            validate.py  ◄── paper's Zenodo CSV
```

---

## 1. Basic tools

```bash
sudo apt update
sudo apt install -y git curl wget unzip ca-certificates gnupg \
                    python3 python3-venv python3-pip \
                    openjdk-8-jdk openjdk-17-jdk
```

Why two Java versions:
- **JDK 8** builds the old 2015–2018 code. Newer Java versions fail on old Maven plugins.
- **JDK 17** runs CKJM Extended (`ckjm_ext.jar`).

Check that both are installed:

```bash
ls /usr/lib/jvm/
# you should see java-8-openjdk-amd64 and java-17-openjdk-amd64
/usr/lib/jvm/java-8-openjdk-amd64/bin/java -version     # 1.8.0_...
/usr/lib/jvm/java-17-openjdk-amd64/bin/java -version    # 17...
```

> If `openjdk-8-jdk` is "not found", install Temurin 8 instead:
> ```bash
> wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg
> echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(. /etc/os-release; echo $VERSION_CODENAME) main" | sudo tee /etc/apt/sources.list.d/adoptium.list
> sudo apt update && sudo apt install -y temurin-8-jdk
> ```
> Then use `--java8-home /usr/lib/jvm/temurin-8-jdk-amd64` in step 8.

---

## 2. Install Docker (only for the SonarQube server)

These are Docker's official steps for Ubuntu:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
 | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# use docker without sudo (log out and back in after this)
sudo usermod -aG docker $USER
```

Check:

```bash
docker run --rm hello-world
docker compose version
```

---

## 3. Install Maven 3.6.3

Use exactly **3.6.3**. Maven 3.8+ blocks the `http://` repositories that many 2015–2018 projects still use.

```bash
cd /tmp
wget https://archive.apache.org/dist/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.tar.gz
sudo tar -xzf apache-maven-3.6.3-bin.tar.gz -C /opt
sudo mv /opt/apache-maven-3.6.3 /opt/maven-3.6.3
JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64 /opt/maven-3.6.3/bin/mvn -v
```

---

## 4. Install sonar-scanner (command line)

It comes with its own Java, so it does not care which Java you use for the build.

```bash
cd /tmp
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-6.2.1.4610-linux-x64.zip
sudo unzip -q sonar-scanner-cli-6.2.1.4610-linux-x64.zip -d /opt
sudo ln -sfn /opt/sonar-scanner-6.2.1.4610-linux-x64 /opt/sonar-scanner
/opt/sonar-scanner/bin/sonar-scanner -v
```

> If the link gives 404, a newer version exists. Take the Linux x64 zip from
> https://docs.sonarsource.com/sonarqube-server/latest/analyzing-source-code/scanners/sonarscanner/
> and change the two file names above.

---

## 5. Start the SonarQube server

### 5.1 Kernel settings (Elasticsearch inside SonarQube needs them)

```bash
sudo sysctl -w vm.max_map_count=524288
sudo sysctl -w fs.file-max=131072
# keep after reboot:
echo -e "vm.max_map_count=524288\nfs.file-max=131072" | sudo tee /etc/sysctl.d/99-sonarqube.conf
```

### 5.2 docker-compose file

```bash
mkdir -p ~/sonarqube && cd ~/sonarqube
cat > docker-compose.yml <<'EOF'
services:
  sonarqube:
    image: sonarqube:community
    depends_on: [db]
    environment:
      SONAR_JDBC_URL: jdbc:postgresql://db:5432/sonar
      SONAR_JDBC_USERNAME: sonar
      SONAR_JDBC_PASSWORD: sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
      - sonarqube_logs:/opt/sonarqube/logs
    ports:
      - "9000:9000"
    restart: unless-stopped
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: sonar
      POSTGRES_PASSWORD: sonar
      POSTGRES_DB: sonar
    volumes:
      - postgresql:/var/lib/postgresql/data
    restart: unless-stopped
volumes:
  sonarqube_data:
  sonarqube_extensions:
  sonarqube_logs:
  postgresql:
EOF
docker compose up -d
```

Wait 1–3 minutes, then check:

```bash
curl -s http://localhost:9000/api/system/status
# wait until you see  "status":"UP"
```

If it never reaches UP: `docker compose logs sonarqube | tail -50`. The most common cause is step 5.1 not being done.

### 5.3 First login and token

1. Open **http://localhost:9000** in a browser (from another PC use `http://<server-ip>:9000`).
2. Log in with **admin / admin**, then set a new password.
3. Top right: **My Account → Security → Generate Tokens**
   - Name: `td-pipeline`
   - Type: **User Token** (an analysis token cannot read the API)
   - Copy the token.
4. Save it in your shell:

   ```bash
   echo 'export SONAR_TOKEN=squ_xxxxxxxxxxxxxxxxxxxx' >> ~/.bashrc
   source ~/.bashrc
   curl -s -u $SONAR_TOKEN: http://localhost:9000/api/authentication/validate
   # {"valid":true}
   ```

### 5.4 Two settings that matter for this study

**a) Standard Experience mode.** The paper uses *bugs, vulnerabilities, code smells*.
Newer SonarQube versions may open in "Multi-Quality Rule" mode. Go to
**Administration → Configuration → General Settings → Mode** and choose **Standard Experience**.
If you don't see a "Mode" option, your version doesn't have it, so skip this.

**b) Housekeeping.** We back-date the analyses to 2015–2018, which is more than 5 years ago.
With default settings SonarQube would **delete them or thin them to one per month**.
The pipeline tries to set these at start-up. Set them by hand too, to be sure:
**Administration → Configuration → General Settings → Housekeeping → General**, then
click **Save** under each one.

| Setting in the UI | Key | Value |
|---|---|---|
| Keep only one analysis a month after | `sonar.dbcleaner.weeksBeforeKeepingOnlyOneSnapshotByMonth` | 5000 |
| Keep only analyses with a version event after | `sonar.dbcleaner.weeksBeforeKeepingOnlyAnalysesWithVersion` | 5000 |
| Delete all analyses after | `sonar.dbcleaner.weeksBeforeDeletingAllSnapshots` | 10000 |

Leave the other settings (and the "Dashboards history retention" one) as they are.
If the page refuses a value, any number above **700** weeks is enough for 2015 data.

---

## 6. Get the pipeline files

Put these files in one folder (`~/td-tools`):

| File | What it is |
|---|---|
| `td_pipeline.py` | main script (all steps) |
| `run_ckjm.py` | CKJM Extended wrapper (used by the main script) |
| `ckjm_ext.jar` | CKJM Extended, already built |
| `validate.py` | checks the result |
| `align_paper.py` | matches the paper's rows to real commits (step 8b) |
| `diag_match.py` | quick line-count diagnostic |
| `extras.py` | Halstead + git-activity metrics (used by the pipeline) |
| `add_extras.py` | adds those metrics to a run that is already finished |
| `build_mart.py` | packs finished runs into one data mart for the AI team (section 12b) |
| `preflight.py` | checks what each repo's commits need before building (used by td_pipeline.py) |
| `run_repos.py` + `repos.csv` | runs the whole pipeline for many repos and builds one mart (section 13) |
| `fingerprint.py` | adds the analyzer fingerprint to a run made before it was recorded (section 12b) |
| `history.py` | history/window features, lineage, module coupling, targets (section 10d) |
| `PIPELINE_COMPARISON.md` | how this pipeline differs from the team's td_pipeline_final |
| `RUN_GUIDE.md` | this file |

```bash
mkdir -p ~/td-tools ~/td-work ~/td-out ~/zenodo
# copy the files into ~/td-tools

python3 -m venv ~/td-env
source ~/td-env/bin/activate
pip install --upgrade pip
pip install pandas requests numpy scipy javalang pyarrow
```

Check that CKJM runs:

```bash
cd /tmp && unzip -oq ~/td-tools/ckjm_ext.jar gr/spinellis/ckjm/MetricsFilter.class
/usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp ~/td-tools/ckjm_ext.jar gr.spinellis.ckjm.MetricsFilter gr/spinellis/ckjm/MetricsFilter.class
# OK if it prints a line like:
# gr.spinellis.ckjm.MetricsFilter 8 1 0 19 57 6 0 19 5 0.4286 285 1.0000 0 ...
```

---

## 7. Download the paper's data for retrofit (for the comparison)

```bash
cd ~/zenodo
wget -O square_retrofit_measures.csv \
  "https://zenodo.org/records/4534110/files/square_retrofit_measures.csv?download=1"
head -c 300 square_retrofit_measures.csv
```

The first column has the paper's 150 week dates. The pipeline uses **exactly these weeks**,
so we can compare week by week.

---

## 8. Quick test: 5 weeks

```bash
source ~/td-env/bin/activate
cd ~/td-tools

python td_pipeline.py \
  --repo-url https://github.com/square/retrofit.git \
  --key square:retrofit \
  --dates-from ~/zenodo/square_retrofit_measures.csv \
  --limit 5 \
  --work ~/td-work --out ~/td-out/retrofit \
  --java8-home /usr/lib/jvm/java-8-openjdk-amd64 \
  --java17 /usr/lib/jvm/java-17-openjdk-amd64/bin/java \
  --mvn /opt/maven-3.6.3/bin/mvn \
  --scanner /opt/sonar-scanner/bin/sonar-scanner \
  --reset
```

You should see something like:

```
11:40:02 housekeeping ... -> 204
11:40:05 5 weeks planned: <first paper date> -> <5th paper date>
11:40:05 [1/5] <first paper date> <commit>
11:42:40    ok: 160 files, 410 classes
...
11:52:10 project_level.csv 5 rows | module_level.csv 30 rows | file_level.csv 800 rows
```

(The numbers will differ. The point is that every week ends with `ok`.)

The first week is slow because Maven downloads all the libraries. Later weeks are faster.

**Look at it in SonarQube:** open http://localhost:9000, then the project `square:retrofit`, then
**Activity**. You should see 5 analyses dated 2015, one week apart.

### Check the quick test

```bash
python validate.py --out ~/td-out/retrofit --paper ~/zenodo/square_retrofit_measures.csv
```

What you want to see:
- No `[FAIL]` lines.
- `sum of files == sum of modules == project` → **PASS**. This proves the 3 levels agree.
- `CKJM dropped at most ...` under 5%.
- In the paper table, `ncloc` ratio close to **1.00** and trend rho high.

If that looks good, run the full set.

---

## 8b. Match the paper's exact commits (do this before the full run)

**Finding:** the paper's date labels do **not** follow the real commit dates. For retrofit, the
code labelled `2017-01-27` is really from **2015-12-18** (Java 3738, XML 703 against 700, 91 files:
an exact match). The gap is not constant either (about 45–58 weeks). If we use their dates,
we analyse different code from what they analysed.

So match every paper row to its real commit **by content** (Java lines, pom.xml lines, file
count), keeping the order:

```bash
cd ~/td-tools
python align_paper.py --repo ~/td-work/square_retrofit \
                      --paper ~/zenodo/square_retrofit_measures.csv \
                      --out ~/td-out/retrofit_plan.csv
```

Check the summary line: `mean error` should be near **0.00**, and most rows should show
`java_ours == java_paper`.

Then re-run the 5-week test on **exactly those commits**, in a new output folder:

```bash
python td_pipeline.py \
  --repo-url https://github.com/square/retrofit.git \
  --key square:retrofit \
  --plan-csv ~/td-out/retrofit_plan.csv \
  --limit 5 \
  --work ~/td-work --out ~/td-out/retrofit_matched \
  --java8-home /usr/lib/jvm/java-8-openjdk-amd64 \
  --java17 /usr/lib/jvm/java-17-openjdk-amd64/bin/java \
  --mvn /opt/maven-3.6.3/bin/mvn \
  --scanner /opt/sonar-scanner/bin/sonar-scanner \
  --reset

python validate.py --out ~/td-out/retrofit_matched --paper ~/zenodo/square_retrofit_measures.csv
```

Now `ncloc` (Java only on both sides) should have a ratio of **1.00**.

**Test code:** the authors' Maven scan also sent the test code (`src/test/java`) to SonarQube.
Test code does not count in `ncloc`, but its issues **do** count in `code_smells` and `sqale_index`.
To do the same, add `--with-tests` to the pipeline command (and `--reset` when you switch). Any gap left in
code_smells or TD comes from the SonarQube version and rule set, not from the code.

For the full run (step 9), use `--plan-csv ~/td-out/retrofit_plan.csv` instead of
`--dates-from ...`, and `--out ~/td-out/retrofit_matched`.

> For repos **not** in the paper, skip this step and use `--weeks/--end`. Then the dates are real
> commit dates, which is more accurate than the paper's labels.

---

## 8c. Old SonarQube 7.9 (to match the paper's code smells and TD)

With today's SonarQube, retrofit gets about **8 code smells** where the paper has about **180**,
even on exactly the same code (ncloc, classes and complexity all match at 1.00). Adding test code
does not explain it. The reason is the rule set: the paper used the 2019 rules (SonarQube 7.x).
To reproduce their numbers, run SonarQube **7.9 LTS** next to the new one, on port **9001**:

```bash
docker run -d --name sonarqube79 -p 9001:9000 sonarqube:7.9-community
# wait until UP (1-3 min):
curl -s http://localhost:9001/api/system/status
```

1. Open http://localhost:9001 and log in with admin / admin.
2. Go to **My Account → Security → Generate Tokens** and copy the token. It is a different token from the new server's.

Old scanner (it comes with Java 11, which is what 7.9 needs):

```bash
cd /tmp
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.8.1.3023-linux.zip
sudo unzip -q sonar-scanner-cli-4.8.1.3023-linux.zip -d /opt
sudo ln -sfn /opt/sonar-scanner-4.8.1.3023-linux /opt/sonar-scanner-4
```

Run the 5-week test against it. Note the 3 changes: `--sonar`, `--token` and `--scanner`:

```bash
cd ~/td-tools
python td_pipeline.py \
  --repo-url https://github.com/square/retrofit.git \
  --key square:retrofit \
  --plan-csv ~/td-out/retrofit_plan.csv \
  --limit 5 \
  --sonar http://localhost:9001 --token <TOKEN_FROM_9001> \
  --scanner /opt/sonar-scanner-4/bin/sonar-scanner \
  --work ~/td-work --out ~/td-out/retrofit_sq79 \
  --java8-home /usr/lib/jvm/java-8-openjdk-amd64 \
  --java17 /usr/lib/jvm/java-17-openjdk-amd64/bin/java \
  --mvn /opt/maven-3.6.3/bin/mvn \
  --reset

python validate.py --out ~/td-out/retrofit_sq79 --paper ~/zenodo/square_retrofit_measures.csv
```

One housekeeping line may show `400`, because that setting does not exist in 7.9. That is fine.
7.9 uses its built-in database. That is OK for this dataset, but keep the container (don't delete it)
until you have exported your CSVs.

---

## 9. Full run: all 150 weeks

Run the same command **without `--limit` and without `--reset`**. It skips the weeks it
already did and continues. Use `nohup` so it keeps going if you close the terminal:

```bash
cd ~/td-tools
nohup python td_pipeline.py \
  --repo-url https://github.com/square/retrofit.git \
  --key square:retrofit \
  --dates-from ~/zenodo/square_retrofit_measures.csv \
  --work ~/td-work --out ~/td-out/retrofit \
  --java8-home /usr/lib/jvm/java-8-openjdk-amd64 \
  --java17 /usr/lib/jvm/java-17-openjdk-amd64/bin/java \
  --mvn /opt/maven-3.6.3/bin/mvn \
  --scanner /opt/sonar-scanner/bin/sonar-scanner \
  > ~/td-out/retrofit/run.log 2>&1 &

tail -f ~/td-out/retrofit/run.log        # Ctrl+C stops watching, not the run
```

If it stops (power cut, error), just run the same command again and it resumes.

When it finishes:

```bash
python validate.py --out ~/td-out/retrofit --paper ~/zenodo/square_retrofit_measures.csv
```

---

## 10. Output files

All files are `;`-separated, in `~/td-out/retrofit/`.

| File | Contents |
|---|---|
| **project_level.csv** | week, sha, all SonarQube metrics, `total_principal`, CK averages, `n_classes`, `n_dropped` |
| **module_level.csv** | week, sha, module, SonarQube counts **summed** over the module's files, `total_principal`, CK averages over the module's classes, `n_files`, `n_classes` |
| `folder_level_*` (in module_level.csv) | issues SonarQube raises on a folder/package instead of a file (for example "package needs package-info.java"). They are already **included** in the module's totals; these columns show how much came from folders |
| module `(project)` (in module_level.csv) | issues SonarQube puts on the **whole project**, not on any file or folder (17 code smells for retrofit). They belong to no module, so they get their own row. Keep or drop this row depending on your analysis |
| **file_level.csv** | week, sha, module, file, path, SonarQube file metrics, `total_principal`, CK averages over the classes in that file (inner classes included) |
| `raw_*.csv` | raw pieces before joining (`raw_ck_class.csv` = class level) |
| `weeks_plan.csv` | week → commit chosen |
| `status.csv` | SUCCESS / BUILD_FAILED / … per week |
| `sonar_history_check.csv` | what SonarQube kept in its own history (should match project_level) |
| `build_and_scan.log` | full Maven and scanner output (look here when a week fails) |

**Target column:** `total_principal = sqale_index + reliability_remediation_effort + security_remediation_effort` (minutes).

**The paper's 4 selected features:** `bugs`, `code_smells`, `duplicated_blocks`, `Ca`.
The notebook divides bugs, code_smells and duplicated_blocks by `ncloc` before the regression.

To rebuild the 3 joined files from the raw files (for example after editing a raw file):

```bash
python td_pipeline.py --join-only ~/td-out/retrofit
```

---

## 10b. Extra metrics: Halstead and git activity (all 3 levels)

The pipeline also computes these **for every snapshot**, at file, module and project level.
They come from git only (no build), so they are cheap.

**Halstead** (main code only, `src/main/java`, same scope as `ncloc`):

| Column | Meaning |
|---|---|
| `n1`, `n2` | distinct operators / distinct operands |
| `N1`, `N2` | total operators / total operands |
| `halstead_vocabulary` | n1 + n2 |
| `halstead_length` | N1 + N2 |
| `halstead_volume` | length × log2(vocabulary) |
| `halstead_difficulty` | (n1 / 2) × (N2 / n2) |
| `halstead_effort` | difficulty × volume |
| `halstead_volume_sum` | (module/project only) sum of the file volumes |

- Operators = Java operators + all keywords (including `public`, `static`, `int`, …).
- Operands = identifiers + literals.
- Brackets, `;` and `,` are not counted.
- At module and project level the distinct counts are the **union** over the files (distinct
  counts cannot be added), so `halstead_volume` is bigger than `halstead_volume_sum`.

**Git activity** (commits between the previous snapshot and this one, merges excluded):

| Column | Meaning |
|---|---|
| `commit_count` | commits in that window |
| `lines_added`, `lines_deleted`, `code_churn` | lines added / deleted / both |
| `contributors_count` | distinct author e-mails |
| `git_files_changed` | files touched (module/project level) |
| `window_days` | how many real days the window covers |

With `--plan-csv` (paper commits) the windows are **not** always 7 days, because the paper's
weeks are not evenly spaced. Use `window_days` if you need "per week" numbers
(for example `commit_count / window_days * 7`). The first snapshot uses the 7 days before it.

**Already finished a run before this existed?** Add the metrics without re-running SonarQube:

```bash
python add_extras.py --repo ~/td-work/square_retrofit --out ~/td-out/retrofit_matched
```

---

## 10d. History features, lineage and targets (history.py)

`td_pipeline.py` now runs this step **automatically at the end**. For a run that is already
finished, run it alone (no SonarQube, no build needed - about 10-60 seconds):

```bash
python history.py --repo ~/td-work/square_retrofit --out ~/td-out/retrofit_final
python validate.py --out ~/td-out/retrofit_final --paper ~/zenodo/square_retrofit_measures.csv \
                   --repo ~/td-work/square_retrofit
```

It adds, at **project, module and file level**:
- TD history: `td_3w_lag`, `td_4w_lag`, `td_12w_lag`, `td_change_1w/3w/4w/12w`, `td_slope_4w/12w`,
  `td_volatility_4w`, `td_growth_rate_4w`, `finding_density_t0`, `development_cost_t0`
- 21/30/90/180-day windows: `git_commits_*`, `git_lines_churned_*`, `churn_slope_*`,
  `complexity_slope_*`, `duplication_change_*`, `cognitive_complexity_change_*`, `ncloc_change_*`,
  `violations_change_*`, `debt_density_change_*`
- `git_commit_acceleration`, `git_churn_acceleration`, `commit/churn_burstiness_180d`,
  `major_author_commits`, `knowledge_fragmentation_180d`, function-complexity distribution `fn_*`
- module only: `mod_avg_complexity`, `parent_module_id`, `afferent_coupling_ca`, `efferent_coupling_ce`,
  `module_lineage_status/confidence`
- file only: `lineage_id/status/confidence`, `file_extension`, `file_created_date`, `file_age_days`,
  `file_deleted` (future - META)
- **targets**: `target_td_3w`, `target_td_1m`, `target_td_3m` + `_status`

Week windows count weekly snapshots (like the paper); day windows use real commit time.
Nothing after t0 is read except the targets and `file_deleted`. Only commits reachable from the
t0 commit are counted. **CK metrics are now LOC-weighted like the paper** (re-run `--join-only` or
`history.py` on old runs to update them; project WMC on commons-io changed from 10.5 to 40.4).

`validate.py --repo <clone>` adds the stale-scan check (SonarQube line count = git line count).
The mart's `data_dictionary.csv` gives every column a role: ID / FEATURE / FLAG / META / TARGET.
`manifest.json` lists tool versions, settings, the SonarQube rule-set fingerprint and a checksum
per file.

---

## 10c. Gradle projects (for example kafka)

The pipeline now recognises Gradle projects by themselves (no `pom.xml` but a `build.gradle`).
- It builds with `./gradlew` if the repo has one, or else with the `gradle` you give in `--gradle /path/to/gradle`.
- It copies each module's libraries to `build/ckjm-deps/` for CKJM and SonarQube.

Old Gradle projects (2015–2018) often need the **matching old Gradle version** and JDK 8.
Kafka in that period did not commit `gradlew`, so you need to download, for example, Gradle 4.x
from https://services.gradle.org/distributions/ and pass `--gradle ~/gradle-4.10.3/bin/gradle`.
Test with `--limit 3` first.

---

## 11. Is the data correct? (reading validate.py)

| Check | Pass means | If it fails |
|---|---|---|
| weeks collected / spacing 7 days | no missing weeks | see `status.csv` and the log |
| ranges | every value is legal (ratings 1–5, % 0–100, DAM 0–1, LCOM3 0–2 …) | a parsing or join problem: tell me the column |
| violations = bugs + vulnerabilities + code_smells | SonarQube numbers are complete | the API call cut some metrics |
| sum of files = sum of modules = project | the 3 levels agree | file pages were missed |
| CKJM dropped < 5% | inheritance metrics are trustworthy | the library jars were not copied (see step 12) |
| ncloc jump > 20% | no broken builds | look at that week: a module may not have compiled |
| paper: ncloc ratio ≈ 1 | we analysed the same code as the authors | wrong weeks or wrong branch |
| paper: issue counts / TD ratio | newer SonarQube has more rules, so it can be far from 1 | that's fine if trend rho is high (> 0.8) |
| paper: CK columns close | they also averaged per class | if far off, they aggregated differently: write it down in your report |

---

## 12. Problems and fixes

| Problem | Fix |
|---|---|
| SonarQube never UP, log says `max virtual memory areas vm.max_map_count` | do step 5.1 again |
| `401` errors | the token is wrong or not exported: `echo $SONAR_TOKEN` |
| `Date of analysis cannot be older than the date of the last known analysis` | you ran weeks out of order; restart with `--reset` |
| week says `BUILD_FAILED` | open `build_and_scan.log`. If one module fails every time (often `samples`), skip it: `--mvn-args "-pl '!samples'"` and restart with `--reset` |
| Maven `Could not transfer artifact ... http://` | you are not using Maven 3.6.3 |
| `Could not resolve ... X.Y.Z-SNAPSHOT` | an old pre-release library that was deleted. The pipeline now swaps `<xxx.version>X.Y.Z-SNAPSHOT` for the released `X.Y.Z` (it prints `snapshot deps -> release`). Turn it off with `--keep-snapshots` |
| A failed week in the middle | it can't be redone later (SonarQube refuses an analysis older than the latest one). Fix the cause, then run again with `--reset` |
| `CKJM dropped ... classes` warning | library jars are missing; check `ls ~/td-work/square_retrofit/*/target/ckjm-deps` after a build |
| Disk full | `docker system prune`, then delete `~/td-work` (it is only a clone) |
| Fewer analyses in SonarQube Activity than weeks | housekeeping (step 5.4b); `project_level.csv` is still fine because each week is saved right after its analysis |

---

## 12b. Data mart for the AI team

Pack one or more finished runs into one documented package (CSV + data dictionary + README +
validation report + manifest, zipped). Give each project a short name and repeat
`--run/--plan/--paper/--repo` with that name:

```bash
python build_mart.py \
  --run retrofit=~/td-out/retrofit_final   --plan retrofit=~/td-out/retrofit_plan.csv \
  --paper retrofit=~/zenodo/square_retrofit_measures.csv --repo retrofit=~/td-work/square_retrofit \
  --run commonsio=~/td-out/commonsio_final --plan commonsio=~/td-out/commonsio_plan.csv \
  --paper commonsio=~/zenodo/<commons-io csv> --repo commonsio=~/td-work/apache_commons-io \
  --out ~/td-mart
```

- `--repo` adds the stale-scan check to the report (leave it out and the check is skipped).
- The report ends with an **"across projects"** part:
  - `[FAIL] DIFFERENT SonarQube versions / rule sets` = TD of the projects is not comparable.
    All projects must be scanned with the same SonarQube and the same profile
    (Sonar way comprehensive). Do not update the SonarQube Docker image between repos.
  - `[WARN] no analyzer fingerprint` = the run was made before the pipeline recorded it.
    If SonarQube and the profile have not changed since, add it afterwards:
    `python fingerprint.py --out ~/td-out/retrofit_final --key square:retrofit`
    (needs SonarQube up and `SONAR_TOKEN` set).
  - `[WARN] ... lacks N columns` / `no CK values` = a project could not give some metrics
    (for example no build).

Send `~/td-mart.zip`.

---

## 13. Many repos in one go: repos.csv + run_repos.py

List the repos in `repos.csv` (one row per repo) and let `run_repos.py` do everything for each:
clone -> download the paper CSV from Zenodo -> match the paper rows to commits -> build + scan +
CKJM + Halstead + git + history -> validate -> one line in `~/td-out/repos_status.csv`.
At the end it packs every repo with status `OK` into one mart (`~/td-mart.zip`).

`repos.csv` columns:

| Column | Meaning |
|---|---|
| `name` | short id, becomes `project_id` in the mart (e.g. `retrofit`) |
| `enabled` | `1` = run, `0` = skip |
| `git_url` | GitHub URL |
| `sonar_key` | SonarQube key `owner:repo`; the clone goes to `~/td-work/owner_repo` |
| `paper_csv` | file name on Zenodo (e.g. `commonsio_measures.csv`); empty = not a paper repo |
| `weeks`, `end` | only for non-paper repos: number of weeks and last week |
| `mvn_args`, `gradle_args`, `build_cmd`, `with_tests` | passed to td_pipeline.py |
| `out` | run folder; default `~/td-out/<name>_final` |
| `notes` | free text |

The file already lists all 15 open-source repos of the paper; retrofit, commons-io,
java-websocket and zxing are enabled (all Maven). Turn others on one at a time after a test.

```bash
source ~/td-env/bin/activate && cd ~/td-tools
export SONAR_TOKEN=...                                  # SonarQube must be UP (section 5)

python run_repos.py repos.csv --dry-run                 # only prints the commands
python run_repos.py repos.csv --test 5                  # 5 weeks per repo into <name>_test folders
nohup python run_repos.py repos.csv > ~/td-out/run_repos.log 2>&1 &    # the real run
tail -f ~/td-out/run_repos.log
```

- **Resume:** run the same command again. Repos with status `OK` are skipped (`--redo` runs them
  again), and an unfinished repo continues from the week it stopped at.
- `--only commonsio,zxing` runs just those rows; `--resume-from zxing` skips the rows before it;
  `--mart-only` only rebuilds the mart; `--no-mart` skips it.
- **One repo failing does not stop the others.** Status values in `repos_status.csv`:
  `OK`, `CLONE_FAILED`, `PAPER_DOWNLOAD_FAILED`, `ALIGN_FAILED`, `ALIGN_POOR` (paper rows do not
  match the code well - check `<name>_plan.csv`), `PIPELINE_FAILED`, `TOO_FEW_WEEKS` (< 90% of
  weeks built - see `build_and_scan.log`), `VALIDATE_FAILED` (see `<out>/validation.txt`).
- **It handles the usual problems by itself:**
  - paper rows that match no commit (Java more than 0.5% off) -> **fallback** to one real commit per
    week on the paper's dates (`snapshot_method = weekly_on_paper_dates`, paper used for trends only;
    `--no-fallback` stops instead);
  - a repo whose first 5 snapshots all fail (does not build) -> `GAVE_UP` after minutes, not hours
    (`--give-up-after N`); after you fix the build, the same command starts it clean;
  - less than 15 GB free disk -> stops before the next repo (`--min-free-gb`);
  - a started run folder never switches method (`METHOD_CHANGED`), so lags are never mixed;
  - only one full run at a time (lock); `--test` runs can go alongside.
- **Before building, each repo is checked** (`preflight.py`, automatic): every 10th planned commit
  is read straight from git for its build tool, Java level, Gradle version, versions that old poms
  only set inside JDK profiles (okhttp's `alpn.jdk8.version`) and test code that uses removed JDK
  classes (dubbo). The answers go into `<run folder>/build_settings.json` and are applied to every
  build: missing properties are set, a commit whose pom asks for Java 9+ is built with JDK 17,
  tests are not compiled when they cannot be. A failed build is retried the other way round
  (with / without compiling tests), and its reason is written to `<run folder>/build_errors.csv`
  (kind: undefined_version_property, internal_jdk_api, java_version,
  snapshot_or_missing_dependency, network, out_of_memory, compile_error, test_failure, other).
- **Marts:** every repo gets its own mart as soon as it is `OK`: `~/td-marts/<name>/` and
  `~/td-marts/<name>.zip`. The combined mart of all OK repos is `~/td-mart.zip`. Each mart has a
  `diagnostics/<name>/` folder (status per week, build errors, preflight, build settings,
  analyzer, weeks plan, validation) to investigate a repo later. Rebuild all marts:
  `python run_repos.py repos.csv --mart-only`.
- **SonarQube must stay the same** for all repos. At start it reads the server's version, Java
  profile and rule hash; if a repo already `OK` was made with different ones it stops everything,
  because TD values would not be comparable. It also warns if the default profile is not
  "Sonar way comprehensive".
- Retrofit is already done: the first run only re-validates it (a few minutes) and records its
  analyzer fingerprint, so `fingerprint.py` is not needed.
- Big repos (nifi, spring-boot, jenkins, guava) can take hours per week; Gradle repos (kafka,
  groovy, ofbiz) need old Gradle/JDK. Always do `--test 5 --only <name>` first.

## 13b. One repo by hand (what run_repos.py does for each row)

Everything stays the same (SonarQube, profile, tools); only names and URLs change.
Example for commons-io; the clone folder is always `~/td-work/<owner>_<repo>`.

```bash
source ~/td-env/bin/activate && cd ~/td-tools
export SONAR_TOKEN=...                      # SonarQube must be up (section 5)

# 1. paper data (the file names are on https://zenodo.org/records/4534110)
wget -O ~/zenodo/<file>.csv "https://zenodo.org/records/4534110/files/<file>.csv?download=1"

# 2. clone and match the paper rows to real commits
git clone https://github.com/apache/commons-io.git ~/td-work/apache_commons-io
python align_paper.py --repo ~/td-work/apache_commons-io --paper ~/zenodo/<file>.csv \
                      --out ~/td-out/commonsio_plan.csv      # check: mean error near 0

# 3. quick test on 5 weeks, then the full run (same command without --limit/--reset)
python td_pipeline.py --repo-url https://github.com/apache/commons-io.git --key apache:commons-io \
  --plan-csv ~/td-out/commonsio_plan.csv --limit 5 --reset \
  --work ~/td-work --out ~/td-out/commonsio_final
python validate.py --out ~/td-out/commonsio_final --paper ~/zenodo/<file>.csv --repo ~/td-work/apache_commons-io

# 4. add it to the mart (section 12b) next to retrofit
```

- Run **one repo at a time** (they share the one SonarQube server). Use `nohup ... &` for the
  full run (section 9).
- The history step (history.py) runs automatically at the end of td_pipeline.py.
- **Gradle projects** (kafka, ...): add `--gradle` (and `--gradle-args` if needed), section 10c.
  Gradle versions from 2015-2018 need an old JDK/Gradle; test 5 weeks first.
- **A repo not in the paper:** skip steps 1-2 and use `--weeks 150 --end YYYY-MM-DD`;
  leave out `--paper`.
- If a week does not build, look at `build_and_scan.log`. One or two missing weeks are fine
  (they show as WARN); many missing weeks mean the build needs a fix.

---

## 13c. Java Driller (jd_* columns, 5th extractor)

`JavaDriller.java` is the pipeline version of the team's `Java_Driller_Data.java` (same metric
logic; file id = path from the repo root; only main source folders; CSV output per snapshot).
Build it once, inside `~/td-tools`:

```bash
cd ~/td-tools
mkdir -p lib driller
/opt/maven-3.6.3/bin/mvn -q dependency:copy \
  -Dartifact=com.github.javaparser:javaparser-core:3.26.2 -DoutputDirectory=lib
/usr/lib/jvm/java-17-openjdk-amd64/bin/javac -cp lib/javaparser-core-3.26.2.jar -d driller JavaDriller.java
ls driller/JavaDriller.class lib/javaparser-core-3.26.2.jar      # both must exist
```

- **New runs:** nothing to do. `td_pipeline.py` finds `driller/` and `lib/` and runs the Driller
  on every snapshot (it never fails a snapshot; a problem is only logged).
- **Runs already finished** (no rescan, no SonarQube needed; about 1-3 s per snapshot):

```bash
python add_driller.py --repo ~/td-work/square_retrofit         --out ~/td-out/retrofit_final
python add_driller.py --repo ~/td-work/apache_commons-io       --out ~/td-out/commonsio_final
python add_driller.py --repo ~/td-work/tootallnate_java-websocket --out ~/td-out/java_websocket_final
python add_driller.py --repo ~/td-work/zxing_zxing             --out ~/td-out/zxing_final
python add_driller.py --repo ~/td-work/square_okhttp           --out ~/td-out/okhttp_final
python add_driller.py --repo ~/td-work/apache_dubbo            --out ~/td-out/dubbo_final
python run_repos.py repos.csv --mart-only                      # rebuild all marts with jd_*
```

  Use the real folder names from `ls ~/td-work ~/td-out`. It can be stopped and started again:
  snapshots already in `raw_jd_file.csv` are skipped.
- **After updating td-tools** (new Driller columns), rebuild the level tables without drilling
  again: run the same `add_driller.py` lines (each prints `0 snapshots to drill`, then rebuilds),
  then `python run_repos.py repos.csv --mart-only`.
- **New Driller version** (2026-10-20: `lcom4_classes`, `noncohesive_classes`): the old
  `raw_jd_*.csv` are moved to `*.v1.bak` automatically and every snapshot is drilled again
  (the same `add_driller.py` lines; about 20-40 minutes for the 6 repos). Rebuild the Driller first:
  `javac -cp lib/javaparser-core-3.26.2.jar -d driller JavaDriller.java`.
- Output: `raw_jd_file.csv` and `raw_jd_deps.csv` (bronze); `jd_*` columns in file, module and
  project tables (silver and the marts). `validate.py` warns when more than 5% of SonarQube files
  have no Driller row.
