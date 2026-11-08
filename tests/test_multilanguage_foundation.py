"""Synthetic software fixtures only; no real-world data, models or scans."""
from dataclasses import replace
from datetime import timedelta
import copy
import json
import os
from pathlib import Path
import sqlite3
import subprocess

import pytest

from forecasting_multilanguage.contracts import *
from forecasting_multilanguage.registry import *
from forecasting_multilanguage.io import publish, verify, file_sha256
from forecasting_multilanguage.git_events import GitArchive, first_parent_numstat, legacy_path_proof, MissingGitObject
from forecasting_multilanguage.admission import PastStore
from forecasting_multilanguage.adapters.sonar_archive import read_archive
from forecasting_multilanguage.adapters.v2 import numstat, read_only_database, churn_audit
from forecasting_multilanguage.features import build_features, prediction_input, FEATURES
from forecasting_multilanguage.targets import origin_identity, target_status
from forecasting_multilanguage.cohorts import validate_cohorts, purged_training_ids
from forecasting_multilanguage.inventory import discover_local_sources
from forecasting_multilanguage.cli import build_archive, main


def write(path, value):
    path.write_bytes(canonical(value) + b"\n")
    return file_sha256(path)


def command(path, *args, env=None):
    return subprocess.check_output(["git", "-C", str(path), *args], env=env, stderr=subprocess.DEVNULL).decode().strip()


@pytest.fixture
def archive(tmp_path):
    repo = tmp_path / "git"
    repo.mkdir()
    command(repo, "init", "-q")
    command(repo, "config", "user.name", "Synthetic fixture")
    command(repo, "config", "user.email", "fixture@example.invalid")
    command(repo, "config", "commit.gpgsign", "false")
    raw = tmp_path / "raw"
    raw.mkdir()
    base = utc("2020-01-01T00:00:00Z")
    stamps = [iso(base + timedelta(days=d)) for d in (0, 60, 90, 120, 150, 180)]
    domain = analyzer_domain(dict(server_version="fixture-1", edition="fixture-community",
        scanner_version="fixture-1", scanner_image_sha256="1"*64,
        plugins=[dict(key=k,language=k,version="fixture-1",binary_sha256="2"*64) for k in ("py","js")],
        rules_sha256="3"*64, scope_policy_sha256=SCOPE_ID, build_mode="source_only",
        runtime_manifest_sha256="4"*64, dependency_policy_sha256="5"*64,
        suppression_policy_sha256="6"*64,metric_mode="STANDARD",metric_semantics="native_sqale_index_minutes_v1"))
    index = []
    for i, stamp in enumerate(stamps):
        (repo/"main.py").write_text("# fixture\n" + "pass\n"*(i+1))
        (repo/"main.js").write_text("// fixture\n")
        command(repo,"add","main.py","main.js")
        env = dict(os.environ, GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)
        command(repo,"commit","-qm",f"fixture {i}",env=env)
        sha, tree = command(repo,"rev-parse","HEAD"), command(repo,"rev-parse","HEAD^{tree}")
        entry = dict(repository_id="fixture",family_id="fixture-family",commit_sha=sha,source_tree_sha=tree,
            state_utc=stamp,analysis_id=f"fixture-analysis-{i}",executed_utc="2021-01-01T00:00:00Z",
            available_utc=None,retrieved_utc="2021-01-02T00:00:00Z",domain_id=domain["domain_id"],
            scope_id=SCOPE_ID,native_project_key="fixture-native",payload=f"p{i}.json",
            coverage_payload=f"c{i}.json",inventory_payload=f"i{i}.json")
        entry["raw_payload_sha256"] = write(raw/entry["payload"],dict(analysis_id=entry["analysis_id"],revision=sha,
            component=dict(key="fixture-native",measures=[dict(metric="sqale_index",value=str(i*10)),
                dict(metric="ncloc",value="20"),dict(metric="ncloc_language_distribution",value="py=10;js=10") ])))
        entry["coverage_sha256"] = write(raw/entry["coverage_payload"],dict(status="COMPLETE",failed_files=0,
            unsupported_files=0,expected_source_files=2,analyzed_files=2,commit_sha=sha,analysis_id=entry["analysis_id"]))
        entry["inventory_sha256"] = write(raw/entry["inventory_payload"],dict(commit_sha=sha,production_paths=["main.py","main.js"]))
        index.append(entry)
    registration = dict(schema_version=2,study_id="synthetic-software-test",repository_id="fixture",
        canonical_url="https://example.invalid/fixture",provider_repository_id="fixture-provider",family_id="fixture-family",
        source_license_spdx="MIT",data_reuse_terms="Synthetic fixture only",source_reference="synthetic-software-test",
        source_digest="7"*64,exposure_status="EXPOSED",exposure_evidence_refs=["fixture"],reserved_role="development",
        branch_reference="fixture-main",branch_reference_observed_at="2021-01-01T00:00:00Z",tip_sha=index[-1]["commit_sha"],
        lineage_policy="COMPLETE_FIRST_PARENT",declared_languages=["py","js"],scope_policy_hash=SCOPE_ID,
        study_mode="RETROSPECTIVE_FIXED_ANALYZER")
    lineage = GitArchive(repo,registration["tip_sha"],registration["branch_reference_observed_at"])
    observations = read_archive(raw,index)
    store = PastStore(registration,domain,lineage,observations)
    return dict(repo=repo,raw=raw,index=index,registration=registration,domain=domain,lineage=lineage,
                observations=observations,store=store,cutoff=stamps[2],tmp=tmp_path)


@pytest.mark.parametrize("value",[None,"", "None", float("nan"),float("inf"),-1,True,"12"])
def test_missing_numeric(value):
    assert raw_measure(value).value is None


def test_zero_roundtrip_and_immutable_publication(tmp_path):
    value = {"zero":raw_measure(0).__dict__,"missing":raw_measure(None).__dict__}
    m=publish(tmp_path/"one",{"a.json":value},{"fixture":True})
    assert verify(tmp_path/"one")==m
    assert json.loads((tmp_path/"one/a.json").read_text())["zero"]["value"]==0
    publish(tmp_path/"two",{"a.json":value},{"fixture":True})
    assert (tmp_path/"one/manifest.json").read_bytes()==(tmp_path/"two/manifest.json").read_bytes()
    with pytest.raises(ValueError): publish(tmp_path/"one",{"a.json":value},{})
    (tmp_path/"one/a.json").write_text("{}")
    with pytest.raises(ValueError): verify(tmp_path/"one")


@pytest.mark.parametrize("name",["../escape.json","/absolute.json","manifest.json"])
def test_failed_publish_no_complete(tmp_path,name):
    with pytest.raises(ValueError): publish(tmp_path/"bad",{name:{}},{})
    assert not (tmp_path/"bad").exists()


@pytest.mark.parametrize("timestamp",["2020-01-01", "2020-01-01T00:00:00+02:00",None])
def test_utc_required(timestamp):
    with pytest.raises((ValueError,TypeError)): utc(timestamp)


@pytest.mark.parametrize("horizon",[30,60,90])
def test_exact_targets(archive,horizon):
    a=archive
    origin=origin_identity(a["store"],a["cutoff"],horizon)
    label=target_status(origin,a["store"])
    assert (utc(label["endpoint_utc"])-utc(a["cutoff"])).total_seconds()==horizon*86400
    assert label["actual_minutes"]=={30:30,60:40,90:50}[horizon]
    assert label["actual_delta_minutes"]=={30:10,60:20,90:30}[horizon]
    with pytest.raises(ValueError): origin_identity(a["store"],a["cutoff"],91)


def test_unknown_endpoint_no_carry_or_nearest(archive):
    a=archive
    subset=[o for o in a["observations"] if o.commit_sha!=a["index"][3]["commit_sha"]]
    store=PastStore(a["registration"],a["domain"],a["lineage"],subset)
    label=target_status(origin_identity(store,a["cutoff"],30),store)
    assert label["actual_minutes"] is None and label["missing_reason"]=="EXACT_ENDPOINT_STATE_UNMEASURED"
    assert store.at(iso(utc(a["cutoff"])+timedelta(days=31))) is None


def test_same_unchanged_state_proof(archive):
    a=archive
    cutoff=iso(utc(a["index"][0]["state_utc"])+timedelta(days=1))
    label=target_status(origin_identity(a["store"],cutoff,30),a["store"])
    assert label["actual_minutes"]==0 and label["actual_delta_minutes"]==0
    assert label["endpoint_state_proof_id"]


def test_feature_values_missingness_and_past_boundary(archive):
    a=archive
    record=build_features(a["store"],a["cutoff"])
    payload=prediction_input(record,expected_cutoff=a["cutoff"])
    assert payload["debt_minutes_t0"]==20
    assert payload["commits_30d"]==1  # open left endpoint at day60
    assert payload["commits_90d"]==2  # root at left boundary excluded
    assert payload["debt_change_30d"]==10
    assert payload["scope_language_family"]=="mixed_python_jsts"
    assert payload["files_t0"] is None and payload["files_t0__missing"]==1
    assert payload["debt_ols_slope_90d"] is not None
    assert not set(payload)&{"repository_id","family_id","actual_minutes","label_status"}
    changed=[replace(o,measures=dict(o.measures,sqale_index=Measure(999,"OBSERVED",unit="estimated_remediation_minutes")))
             if utc(o.state_utc)>utc(a["cutoff"]) else o for o in a["observations"]]
    future=PastStore(a["registration"],a["domain"],a["lineage"],changed)
    assert build_features(future,a["cutoff"])==record
    # Target changes are independent; forecast identities and X remain fixed.
    origin=origin_identity(a["store"],a["cutoff"],30)
    assert origin_identity(future,a["cutoff"],30)==origin
    assert target_status(origin,future)["actual_minutes"]==999


@pytest.mark.parametrize("field",["actual_minutes","TD_90","label_status","partition","future_paths","endpoint_observation_id"])
def test_reject_outcome_fields(archive,field):
    record=build_features(archive["store"],archive["cutoff"])
    record[field]=1
    with pytest.raises(ValueError): prediction_input(record,expected_cutoff=archive["cutoff"])
    del record[field]
    record["features"][field]={"value":1}
    with pytest.raises(ValueError): prediction_input(record,expected_cutoff=archive["cutoff"])


def test_reject_forged_future_evidence_and_cutoff(archive):
    record=build_features(archive["store"],archive["cutoff"])
    with pytest.raises(ValueError): prediction_input(record,expected_cutoff="2019-01-01T00:00:00Z")
    record["features"]["debt_minutes_t0"]["max_source_state_utc"]="2021-01-01T00:00:00Z"
    record["context_id"]=digest({k:v for k,v in record.items() if k!="context_id"})
    with pytest.raises(ValueError,match="Future source"): prediction_input(record,expected_cutoff=archive["cutoff"])


def test_no_event_censor_and_sparse_trends(archive):
    a=archive
    cutoff="2020-12-31T00:00:00Z"
    record=build_features(a["store"],cutoff)
    assert record["features"]["commits_90d"]["value"]==0
    assert record["features"]["days_since_last_commit_in_90d"]["value"] is None
    assert record["features"]["no_commit_in_complete_90d"]["value"]==1
    assert record["features"]["debt_ols_slope_90d"]["value"] is None


def test_domain_identity_and_compatibility(archive):
    a=archive
    incomplete=analyzer_domain({})
    assert incomplete["status"]=="INCOMPLETE"
    with pytest.raises(ValueError): PastStore(a["registration"],incomplete,a["lineage"],a["observations"])
    m=dict(a["domain"]["manifest"],server_version="fixture-2")
    other=analyzer_domain(m)
    observations=[replace(o,domain_id=other["domain_id"]) for o in a["observations"]]
    store=PastStore(a["registration"],other,a["lineage"],observations)
    label=target_status(origin_identity(a["store"],a["cutoff"],30),store)
    assert label["label_status"]=="DOMAIN_INCOMPATIBLE" and label["actual_minutes"] is None


def test_duplicate_identity_and_contradictory_state(archive):
    a=archive
    with pytest.raises(ValueError): PastStore(a["registration"],a["domain"],a["lineage"],a["observations"]*2)
    other=replace(a["observations"][0],analysis_id="another",measures={"sqale_index":Measure(1,"OBSERVED",unit="estimated_remediation_minutes")})
    with pytest.raises(ValueError,match="Contradictory"): PastStore(a["registration"],a["domain"],a["lineage"],a["observations"]+[other])


@pytest.mark.parametrize("change",[{"failed_files":1},{"analyzed_files":1},{"available_utc":"2019-01-01T00:00:00Z"},{"source_tree_sha":"0"*40}])
def test_bad_scope_clock_tree(archive,change):
    a=archive
    with pytest.raises(ValueError):
        bad=replace(a["observations"][0],**change)
        PastStore(a["registration"],a["domain"],a["lineage"],[bad])


def test_native_payload_integrity_coverage_and_inventory(archive):
    a=archive
    (a["raw"]/a["index"][0]["payload"]).write_text("{}")
    with pytest.raises(ValueError,match="digest"): read_archive(a["raw"],a["index"])


def test_operational_unknown_availability_rejected(archive):
    a=archive
    r=dict(a["registration"],study_mode="OPERATIONAL_ASOF")
    store=PastStore(r,a["domain"],a["lineage"],a["observations"])
    assert store.at(a["cutoff"]) is None
    with pytest.raises(ValueError): build_features(store,a["cutoff"])


@pytest.mark.parametrize("distribution,expected",[({"java":100,"xml":100},"java_dominant"),({"py":90,"js":10},"mixed_python_jsts"),({"py":100},"python_dominant"),({"js":90,"ts":10},"jsts_dominant"),({"java":50,"go":50},"mixed_other"),({},"unknown")])
def test_language_classification(distribution,expected):
    assert language_family(distribution)==expected


def test_language_tokens_and_paths():
    assert language_distribution("py=10,js=20;ts=3")==({"py":10,"js":20,"ts":3},[])
    assert language_distribution("py=NaN")[1]
    assert language_distribution("py=1;py=2")[1]
    assert source_language("src/main.py")=="py"
    assert source_language("tests/main.py") is None
    with pytest.raises(ValueError): source_language("../main.py")
    assert PILOT_TARGETS==("java_dominant","python_dominant","mixed_python_jsts")


def test_exposure_aliases_and_purging(archive):
    r=archive["registration"]
    with pytest.raises(ValueError): validate_cohorts([dict(r,reserved_role="held_out")])
    with pytest.raises(ValueError): validate_cohorts([r,dict(r,family_id="alias-family")])
    assert validate_cohorts([r])=={"fixture-family":"development"}
    origins=[dict(forecast_id=str(d),origin_utc="2020-01-01T00:00:00Z",horizon_days=d) for d in (30,60,90)]
    boundary=iso(utc("2020-01-01T00:00:00Z")+timedelta(days=150))
    assert purged_training_ids(origins,boundary)==["30"]  # equality excluded
    with pytest.raises(ValueError): purged_training_ids(origins+origins,boundary)


def test_readonly_db_and_numstat_conflicts(tmp_path):
    path=tmp_path/"source.db"
    con=sqlite3.connect(path)
    con.execute("CREATE TABLE GIT_COMMITS_CHANGES (PROJECT_ID,COMMIT_HASH,FILE,LINES_ADDED,LINES_REMOVED)")
    for i in range(3):
        for kind in range(2):
            row=(str(i),f"{i+kind:040x}",f"{kind}.py","1","0")
            con.execute("INSERT INTO GIT_COMMITS_CHANGES VALUES (?,?,?,?,?)",row)
            if kind: con.execute("INSERT INTO GIT_COMMITS_CHANGES VALUES (?,?,?,?,?)",row[:3]+("2","0"))
    con.commit();con.close()
    before=path.read_bytes()
    with read_only_database(path,file_sha256(path)) as con:
        with pytest.raises(sqlite3.OperationalError): con.execute("DELETE FROM GIT_COMMITS_CHANGES")
        audit=churn_audit(con,{})
    assert audit["conflicting_keys"]==3 and audit["F2_enabled"] is False
    assert path.read_bytes()==before
    assert numstat("012")==12
    with pytest.raises(ValueError): numstat("1.0")


def test_first_parent_authoritative_diff(archive):
    a=archive
    proof=first_parent_numstat(a["repo"],a["index"][1]["commit_sha"],"main.py")
    assert proof["added"]==1 and proof["removed"]==0
    root=first_parent_numstat(a["repo"],a["index"][0]["commit_sha"],"main.py")
    assert root["added"]==2
    with pytest.raises(MissingGitObject): first_parent_numstat(a["repo"],"0"*40,"main.py")


def test_inversion_and_shallow_history_rejected(archive):
    a=archive
    (a["repo"]/"main.py").write_text("# inversion\n")
    command(a["repo"],"add","main.py")
    command(a["repo"],"commit","-qm","inversion",env=dict(os.environ,GIT_AUTHOR_DATE="2019-01-01T00:00:00Z",GIT_COMMITTER_DATE="2019-01-01T00:00:00Z"))
    with pytest.raises(ValueError,match="inversion"): GitArchive(a["repo"],command(a["repo"],"rev-parse","HEAD"),a["registration"]["branch_reference_observed_at"])
    (a["repo"]/".git/shallow").write_text(a["index"][1]["commit_sha"]+"\n")
    with pytest.raises(ValueError,match="Shallow"): GitArchive(a["repo"],a["registration"]["tip_sha"],a["registration"]["branch_reference_observed_at"])


def test_archive_end_to_end_determinism_and_preservation(archive):
    a=archive
    inputs={"study.json":a["registration"],"domain.json":a["domain"]["manifest"],"index.json":a["index"],"cutoffs.json":[a["cutoff"]]}
    for name,value in inputs.items(): write(a["tmp"]/name,value)
    before={str(p):file_sha256(p) for p in a["raw"].glob("*.json")}
    args=[a["tmp"]/n for n in inputs]+[a["raw"],a["repo"]]
    for name in ("out1","out2"):
        build_archive(args[0],args[1],args[2],args[4],args[5],args[3],a["tmp"]/name)
    assert (a["tmp"]/"out1/manifest.json").read_bytes()==(a["tmp"]/"out2/manifest.json").read_bytes()
    assert json.loads((a["tmp"]/"out1/readiness.json").read_text())["label_statuses"]=={"OBSERVED":3}
    assert {str(p):file_sha256(p) for p in a["raw"].glob("*.json") }==before
    assert main(["inventory-local","--root",str(a["raw"]),"--output",str(a["tmp"]/"inventory")])==0
    assert verify(a["tmp"]/"inventory")["schema_version"]==2


def test_legacy_basename_resolution_and_stratified_sample(archive):
    a=archive
    con=sqlite3.connect(":memory:")
    con.row_factory=sqlite3.Row
    con.execute("CREATE TABLE GIT_COMMITS_CHANGES (PROJECT_ID,COMMIT_HASH,FILE,LINES_ADDED,LINES_REMOVED)")
    for project in ("a","b","c"):
        for entry in a["index"]:
            for path in ("main.py","main.js"):
                row=(project,entry["commit_sha"],path,"1","0")
                con.execute("INSERT INTO GIT_COMMITS_CHANGES VALUES (?,?,?,?,?)",row)
                if path=="main.py": con.execute("INSERT INTO GIT_COMMITS_CHANGES VALUES (?,?,?,?,?)",row[:3]+("9","1"))
    mapping={p:str(a["repo"]) for p in ("a","b","c")}
    first=churn_audit(con,mapping)
    assert first==churn_audit(con,mapping)
    assert len(first["sample"])==20
    assert {r["PROJECT_ID"] for r in first["sample"]}=={"a","b","c"}
    assert all("authoritative_diff" in r for r in first["sample"])
    (a["repo"]/"nested").mkdir()
    (a["repo"]/"nested/main.py").write_text("# fixture\n")
    (a["repo"]/"main.py").write_text("# changed fixture\n")
    command(a["repo"],"add","main.py","nested/main.py")
    command(a["repo"],"commit","-qm","basename fixture")
    proof=legacy_path_proof(a["repo"],command(a["repo"],"rev-parse","HEAD"),"main.py")
    assert proof["resolution"]=="AMBIGUOUS_BASENAME" and len(proof["matches"])==2
    assert legacy_path_proof(a["repo"],command(a["repo"],"rev-parse","HEAD"),"nested/main.py")["resolution"]=="UNIQUE_PATH"


@pytest.mark.parametrize("metric",["metric_mode","scanner_version","rules_sha256"])
def test_domain_unsupported_or_incomplete(archive,metric):
    a=archive
    manifest=dict(a["domain"]["manifest"])
    manifest[metric]="MQR" if metric=="metric_mode" else "unknown"
    d=analyzer_domain(manifest)
    with pytest.raises(ValueError): PastStore(a["registration"],d,a["lineage"],a["observations"])


def test_archive_inventory_language_missing_and_exact_origin_identity(archive):
    a=archive
    with pytest.raises(ValueError): PastStore(dict(a["registration"],declared_languages=["py"]),a["domain"],a["lineage"],a["observations"])
    bad=replace(a["observations"][0],production_paths=("main.py","false.js"))
    with pytest.raises(ValueError): PastStore(a["registration"],a["domain"],a["lineage"],[bad])
    origin=origin_identity(a["store"],a["cutoff"],30)
    origin["horizon_days"]=60
    with pytest.raises(ValueError): target_status(origin,a["store"])


def test_fatal_git_errors_are_not_missing_objects(monkeypatch,tmp_path):
    from forecasting_multilanguage import git_events
    def fatal(*args):
        raise subprocess.CalledProcessError(128,["git"],stderr=b"fatal: unsafe repository ownership")
    monkeypatch.setattr(git_events,"git",fatal)
    with pytest.raises(subprocess.CalledProcessError): legacy_path_proof(tmp_path,"1"*40,"main.py")
    with pytest.raises(subprocess.CalledProcessError): first_parent_numstat(tmp_path,"1"*40,"main.py")


def test_exposure_union_and_unresolved_names():
    from forecasting_multilanguage.inventory import exposure_inventory
    records=[dict(identity="Apache/Commons-IO",source_ref="prior_registry"),
             dict(identity="https://github.com/apache/commons-io.git",source_ref="v2"),
             dict(identity="unresolved-project-name",source_ref="restricted_archive_metadata")]
    result=exposure_inventory(records)
    assert len(result)==2
    assert all(r["exposure_status"]=="EXPOSED" and not r["eligible_for_new_held_out"] for r in result)
    assert any(r["family_resolution"]=="UNRESOLVED_NAME" for r in result)
    assert exposure_inventory(list(reversed(records)))==result


def test_legacy_candidate_join_and_raw_missingness():
    from forecasting_multilanguage.adapters.v2 import candidate_measurements, METRICS
    c=sqlite3.connect(":memory:");c.row_factory=sqlite3.Row
    c.execute("CREATE TABLE SONAR_ANALYSIS (PROJECT_ID,ANALYSIS_KEY,REVISION,DATE)")
    c.execute("CREATE TABLE SONAR_MEASURES (PROJECT_ID,ANALYSIS_KEY,NCLOC_LANGUAGE_DISTRIBUTION,"+",".join(METRICS)+")")
    c.execute("INSERT INTO SONAR_ANALYSIS VALUES (?,?,?,?)",("p","analysis","1"*40,"2020-01-01"))
    c.execute("INSERT INTO SONAR_ANALYSIS VALUES (?,?,?,?)",("other","analysis","2"*40,"2020-02-01"))
    values=["p","analysis","java=1"]+[0 if key=="SQALE_INDEX" else None for key in METRICS]
    c.execute("INSERT INTO SONAR_MEASURES VALUES ("+",".join("?" for _ in values)+")",values)
    record=list(candidate_measurements(c,"1"*64))
    assert len(record)==1 and record[0]["source_reference"]["revision_raw"]=="1"*40
    assert record[0]["measures"]["sqale_index"]["value"]==0
    assert record[0]["measures"]["ncloc"]["value"] is None
    assert record[0]["admission_status"]=="LEGACY_DOMAIN_UNVERIFIED"


@pytest.mark.parametrize("field",["server_version","scanner_version","build_mode"])
def test_domain_wrong_types_rejected(archive,field):
    manifest=dict(archive["domain"]["manifest"])
    manifest[field]=42
    with pytest.raises(ValueError): analyzer_domain(manifest)


def test_canonical_origin_identity(archive):
    a=archive
    assert origin_identity(a["store"],a["cutoff"],30)==origin_identity(a["store"],a["cutoff"].replace("Z","+00:00"),30)


def test_missing_origins_are_preserved_as_attempts(archive):
    a=archive
    inputs={"study.json":a["registration"],"domain.json":a["domain"]["manifest"],"index.json":[],"cutoffs.json":[a["cutoff"]]}
    for name,value in inputs.items(): write(a["tmp"]/name,value)
    result=build_archive(a["tmp"]/"study.json",a["tmp"]/"domain.json",a["tmp"]/"index.json",a["raw"],a["repo"],a["tmp"]/"cutoffs.json",a["tmp"]/"empty")
    readiness=json.loads((a["tmp"]/"empty/readiness.json").read_text())
    assert readiness["feature_contexts"]==0 and readiness["excluded_origins"]==1
    assert readiness["status"]=="BLOCKED_NO_MEASURED_ORIGINS"
    assert len((a["tmp"]/"empty/forecast_labels.csv").read_text().splitlines())==1
    assert json.loads((a["tmp"]/"empty/origin_admission.json").read_text())[0]["status"]=="EXCLUDED"


def test_inventory_exclusion_prevents_self_contamination(tmp_path):
    root=tmp_path/"sources";root.mkdir()
    output=root/"outputs";output.mkdir()
    before=discover_local_sources([root],excluded_roots=[output])
    (output/"new_manifest.json").write_text("{}")
    assert discover_local_sources([root],excluded_roots=[output])==before
    with pytest.raises(ValueError): main(["inventory-local","--root",str(root),"--output",str(root/"bad")])


def test_boolean_native_metric_is_not_observed(archive):
    a=archive
    entry=a["index"][0]
    path=a["raw"]/entry["payload"]
    payload=json.loads(path.read_text())
    payload["component"]["measures"][0]["value"]=True
    entry["raw_payload_sha256"]=write(path,payload)
    observation=read_archive(a["raw"],[entry])[0]
    assert observation.measures["sqale_index"].status=="INVALID"
    assert observation.measures["sqale_index"].value is None


@pytest.mark.parametrize("missing_rights",[None,"","unknown","none"])
def test_unknown_source_or_data_rights_never_admitted(archive,missing_rights):
    for field in ("source_license_spdx","data_reuse_terms"):
        with pytest.raises(ValueError): validate_registration(dict(archive["registration"],**{field:missing_rights}))
