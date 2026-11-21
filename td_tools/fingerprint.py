"""Write the analyzer fingerprint (SonarQube version + quality profile + hash of active rules)
for a run folder that was made before td_pipeline.py recorded it.

Only valid if the SonarQube server and its Java quality profile were NOT changed since that run.

    export SONAR_TOKEN=...            # same token as for td_pipeline.py
    python fingerprint.py --out ~/td-out/retrofit_final --key square:retrofit
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from td_pipeline import Sonar

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True, help="run folder")
ap.add_argument("--key", required=True, help="SonarQube project key used for that run")
ap.add_argument("--sonar", default="http://localhost:9000")
ap.add_argument("--token", default=os.environ.get("SONAR_TOKEN"))
a = ap.parse_args()
if not a.token:
    sys.exit("Set SONAR_TOKEN or pass --token")
out = os.path.expanduser(a.out)
s = Sonar(a.sonar, a.token, a.key)
s.check()
fp = s.analyzer_fingerprint()
if fp.get("error") or not fp.get("rules_hash"):
    sys.exit(f"could not read the fingerprint: {fp}")
path = os.path.join(out, "analysis_meta.csv")
with open(path, "a") as f:
    if f.tell() == 0:
        f.write("run_started;sonarqube_version;quality_profile;active_rules;rules_hash\n")
    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} (added later);{fp['sonarqube_version']};"
            f"{fp['quality_profile']};{fp['active_rules']};{fp['rules_hash']}\n")
print("written to", path, fp)
