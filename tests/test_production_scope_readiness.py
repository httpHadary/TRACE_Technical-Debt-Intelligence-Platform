"""Synthetic contract fixtures only; no actual builds, scans, measurements or labels."""
import copy
from dataclasses import replace
from datetime import timedelta
import json
import os
from pathlib import Path
import pytest
from test_multilanguage_foundation import command, write
from forecasting_multilanguage.contracts import analyzer_domain, digest, utc, iso
from forecasting_multilanguage.git_events import GitArchive
from forecasting_multilanguage.registry import SCOPE_ID, validate_registration as old_registry
from forecasting_multilanguage.features import FEATURE_CONTRACT
from forecasting_multilanguage.targets import TARGET_CONTRACT
from forecasting_multilanguage.production_scope.scope import *
from forecasting_multilanguage.production_scope.registry import contract_ids, validate_registration
from forecasting_multilanguage.production_scope.archive import read_archive, verify_coverage
from forecasting_multilanguage.production_scope.admission import PastStore
from forecasting_multilanguage.production_scope.interfaces import build_features, prediction_input, origin_identity, target_status
from forecasting_multilanguage.production_scope.readiness import inspect_sources

REPO = "adamchainz/django-browser-reload"
ROOT = "src/django_browser_reload/"


@pytest.fixture
def study(tmp_path):
    repo = tmp_path / "git"; repo.mkdir()
    command(repo, "init", "-q")
    command(repo, "config", "user.name", "Synthetic scope fixture")
    command(repo, "config", "user.email", "fixture@example.invalid")
    command(repo, "config", "commit.gpgsign", "false")
    (repo / ROOT).mkdir(parents=True)
    (repo / "docs").mkdir()
    raw = tmp_path / "raw"; raw.mkdir()
    ids = contract_ids(REPO)
    domain = analyzer_domain(dict(server_version="synthetic", edition="synthetic", scanner_version="synthetic",
        scanner_image_sha256="1"*64, plugins=[dict(key=k,language=k,version="synthetic",binary_sha256="2"*64) for k in ("py","js")],
        rules_sha256="3"*64,scope_policy_sha256=ids["scope_policy_hash"],build_mode="source_only",
        runtime_manifest_sha256="4"*64,dependency_policy_sha256="5"*64,suppression_policy_sha256="6"*64,
        metric_mode="STANDARD",metric_semantics="native_sqale_index_minutes_v1"))
    stamps = [iso(utc("2020-01-01T00:00:00Z")+timedelta(days=d)) for d in (0,60,90,120,150,180)]
    shas=[]
    for i, stamp in enumerate(stamps):
        (repo/ROOT/"main.py").write_text("pass\n"*(i+1))
        (repo/ROOT/"main.js").write_text("// synthetic\n")
        (repo/ROOT/"py.typed").write_text("")
        (repo/"docs"/"example.py").write_text("# not production\n")
        command(repo,"add",".")
        command(repo,"commit","-qm",f"synthetic {i}",env=dict(os.environ,GIT_AUTHOR_DATE=stamp,GIT_COMMITTER_DATE=stamp))
        shas.append(command(repo,"rev-parse","HEAD"))
    registration = dict(schema_version=2,contract_version=VERSION,study_id="synthetic-only",
        repository_id=REPO,canonical_url="https://github.com/"+REPO,provider_repository_id="438426152",
        family_id="github:438426152",source_license_spdx="MIT",data_reuse_terms="Synthetic fixture only",
        source_reference="synthetic-only",source_digest="7"*64,exposure_status="EXPOSED",exposure_evidence_refs=["synthetic-only"],
        reserved_role="development",branch_reference="synthetic-main",branch_reference_observed_at="2021-01-01T00:00:00Z",
        tip_sha=shas[-1],lineage_policy="COMPLETE_FIRST_PARENT",declared_languages=["py","js"],
        study_mode="RETROSPECTIVE_FIXED_ANALYZER",**ids)
    lineage = ScopedGit(GitArchive(repo,shas[-1],registration["branch_reference_observed_at"]),REPO)
    index=[]
    for i,sha in enumerate(shas):
        inv=lineage.inventory(sha)
        entry=dict(repository_id=REPO,family_id=registration["family_id"],commit_sha=sha,source_tree_sha=inv["source_tree_sha"],
            state_utc=stamps[i],analysis_id=f"synthetic-{i}",executed_utc="2021-01-01T00:00:00Z",available_utc=None,
            retrieved_utc="2021-01-02T00:00:00Z",domain_id=domain["domain_id"],scope_id=ids["scope_policy_hash"],
            native_project_key="synthetic-project")
        def save(field,value):
            entry[field]=f"{i}-{field}.json"
            return write(raw/entry[field],value)
        entry["raw_payload_sha256"]=save("payload",dict(analysis_id=entry["analysis_id"],revision=sha,
            component=dict(key=entry["native_project_key"],measures=[dict(metric="sqale_index",value=str(i*10)),
                dict(metric="ncloc_language_distribution",value="py=10;js=10") ])))
        entry["inventory_sha256"]=save("inventory_payload",inv)
        entry["review_sha256"]=save("review_payload",dict(version=VERSION,inventory_id=inv["inventory_id"],
            status="REVIEWED_NO_UNRESOLVED_GENERATED_VENDOR_OR_NONCODE",reviewer="synthetic-reviewer",
            reviewed_paths=[r["path"] for r in inv["entries"] if r["role"]!="OUTSIDE_ROOT"]))
        files=[dict(path=r["path"],language=r["language"]) for r in inv["entries"] if r["role"]=="PRODUCTION"]
        components_hash=save("file_components_payload",dict(analysis_id=entry["analysis_id"],revision=sha,
            project_key=entry["native_project_key"],pagination_complete=True,files=files))
        scanner_hash=save("scanner_completion_payload",dict(exit_code=0,sensors_complete=True,analysis_id=entry["analysis_id"],revision=sha,project_key=entry["native_project_key"],ce_task_id=f"synthetic-task-{i}"))
        ce_hash=save("ce_success_payload",dict(task=dict(id=f"synthetic-task-{i}",status="SUCCESS",analysisId=entry["analysis_id"],componentKey=entry["native_project_key"])))
        entry["coverage_sha256"]=save("coverage_payload",dict(version=VERSION,repository_id=REPO,scope_id=ids["scope_policy_hash"],
            commit_sha=sha,source_tree_sha=inv["source_tree_sha"],analysis_id=entry["analysis_id"],inventory_id=inv["inventory_id"],
            native_project_key=entry["native_project_key"],status="COMPLETE",failed_files=0,unsupported_files=0,
            expected_source_files=2,analyzed_files=2,analyzed_source_files=files,
            raw_file_components_sha256=components_hash,scanner_completion_sha256=scanner_hash,ce_success_sha256=ce_hash))
        index.append(entry)
    observations,proofs=read_archive(raw,index,lineage)
    store=PastStore(registration,domain,lineage,observations,proofs)
    return dict(repo=repo,raw=raw,index=index,lineage=lineage,registration=registration,domain=domain,
                observations=observations,proofs=proofs,store=store,cutoff=stamps[2])


@pytest.mark.parametrize("repo,root",[(k,v[1]) for k,v in REPOSITORIES.items()])
def test_exact_roots_and_new_contracts(repo,root):
    ids=contract_ids(repo)
    assert ids["scope_policy_hash"] != SCOPE_ID
    assert ids["feature_contract_id"] != FEATURE_CONTRACT
    assert ids["target_contract_id"] != TARGET_CONTRACT
    assert classify(repo,root+"ish/main.py")==("OUTSIDE_ROOT",None)
    assert len(set(ids.values()))==3


@pytest.mark.parametrize("path",["/src/a.py","../src/a.py","src//a.py","src/./a.py","src/../a.py","src\\a.py",""])
def test_noncanonical_paths(path):
    with pytest.raises(ValueError):classify(REPO,path)


@pytest.mark.parametrize("relative",["tests/t.py","fixtures/t.py","examples/e.js","vendor/x.py","generated/x.js","dist/x.js","test_x.py","a_test.py","a.min.js","a.js.map"])
def test_exclusions(relative):
    assert classify(REPO,ROOT+relative)==("EXCLUDED_POLICY",None)


@pytest.mark.parametrize("relative",["x.mjs","x.ts","x.pyi","x.html","x.css","x.vue","x.unknown","README","x.png"])
def test_unknown_production_extensions_fail_closed(relative):
    assert classify(REPO,ROOT+relative)==("UNKNOWN_BLOCKING",None)


def test_scope_features_and_targets(study):
    a=study
    assert validate_registration(a["registration"])
    with pytest.raises(ValueError):old_registry(a["registration"])
    assert a["lineage"].production_paths(a["lineage"].tip)==(ROOT+"main.js",ROOT+"main.py")
    feature=build_features(a["store"],a["cutoff"])
    assert feature["feature_contract_id"]==a["registration"]["feature_contract_id"]
    x=prediction_input(feature,expected_cutoff=a["cutoff"])
    assert x["debt_minutes_t0"]==20
    assert x["ncloc_t0"] is None
    for horizon in (30,60,90):
        origin=origin_identity(a["store"],a["cutoff"],horizon)
        label=target_status(origin,a["store"])
        assert utc(origin["endpoint_utc"])-utc(origin["origin_utc"])==timedelta(days=horizon)
        assert label["actual_minutes"]=={30:30,60:40,90:50}[horizon]
    with pytest.raises(ValueError):origin_identity(a["store"],a["cutoff"],91)
    assert a["observations"][0].measures["sqale_index"].value==0


@pytest.mark.parametrize("field,value",[("reserved_role","held_out"),("family_id","github:other"),
    ("scope_policy_hash",SCOPE_ID),("feature_contract_id",FEATURE_CONTRACT),("target_contract_id",TARGET_CONTRACT),
    ("contract_version","wrong"),("declared_languages",["py"]),("data_reuse_terms","UNKNOWN")])
def test_registration_identity(study,field,value):
    record=dict(study["registration"],**{field:value})
    with pytest.raises(ValueError):validate_registration(record)


@pytest.mark.parametrize("field,value",[("actual_minutes",0),("split","test"),("endpoint_utc","2021-01-01T00:00:00Z")])
def test_model_boundary_rejects_labels(study,field,value):
    record=build_features(study["store"],study["cutoff"]);record[field]=value
    record["context_id"]=digest({k:v for k,v in record.items() if k!="context_id"})
    with pytest.raises(ValueError):prediction_input(record,expected_cutoff=study["cutoff"])


def test_future_evidence_and_wrong_context_rejected(study):
    r=build_features(study["store"],study["cutoff"])
    r["features"]["debt_minutes_t0"]["max_source_state_utc"]="2021-01-01T00:00:00Z"
    r["context_id"]=digest({k:v for k,v in r.items() if k!="context_id"})
    with pytest.raises(ValueError):prediction_input(r,expected_cutoff=study["cutoff"])
    r=build_features(study["store"],study["cutoff"])
    with pytest.raises(ValueError):prediction_input(r,expected_cutoff="2020-04-02T00:00:00Z")


@pytest.mark.parametrize("mutation",["wrong_file","extra_file","missing_file","duplicate_file","wrong_language","tree","analysis","review","partial","pagination","scanner","ce"])
def test_no_partial_scope_success(study,mutation):
    a=study;entry=copy.deepcopy(a["index"][2]);raw=a["raw"]
    c=json.loads((raw/entry["coverage_payload"]).read_text())
    if mutation=="wrong_file":c["analyzed_source_files"][0]["path"]=ROOT+"other.js"
    if mutation=="extra_file":c["analyzed_source_files"].append(dict(path="docs/example.py",language="py"))
    if mutation=="missing_file":c["analyzed_source_files"].pop()
    if mutation=="duplicate_file":c["analyzed_source_files"][1]=c["analyzed_source_files"][0]
    if mutation=="wrong_language":c["analyzed_source_files"][0]["language"]="py"
    if mutation=="tree":c["source_tree_sha"]="a"*40
    if mutation=="analysis":c["analysis_id"]="other"
    if mutation=="partial":c["analyzed_files"]=1
    if mutation=="review":
        r=json.loads((raw/entry["review_payload"]).read_text());r["status"]="UNREVIEWED"
        entry["review_sha256"]=write(raw/entry["review_payload"],r)
    if mutation in ("pagination","scanner","ce"):
        field={"pagination":"file_components_payload","scanner":"scanner_completion_payload","ce":"ce_success_payload"}[mutation]
        r=json.loads((raw/entry[field]).read_text())
        if mutation=="pagination":r["pagination_complete"]=False
        if mutation=="scanner":r["sensors_complete"]=False
        if mutation=="ce":r["task"]["status"]="FAILED"
        key={"pagination":"raw_file_components_sha256","scanner":"scanner_completion_sha256","ce":"ce_success_sha256"}[mutation]
        c[key]=write(raw/entry[field],r)
    if mutation in ("wrong_file", "extra_file", "missing_file", "duplicate_file", "wrong_language"):
        # Keep raw export and declared coverage mutually consistent, with valid
        # hashes. Only comparison against the authoritative Git scope can reject.
        components=json.loads((raw/entry["file_components_payload"]).read_text())
        components["files"]=c["analyzed_source_files"]
        c["raw_file_components_sha256"]=write(raw/entry["file_components_payload"],components)
    entry["coverage_sha256"]=write(raw/entry["coverage_payload"],c)
    with pytest.raises(ValueError):read_archive(raw,[entry],a["lineage"])


def test_proof_mutation_and_duplicate_admission(study):
    a=study;obs=a["observations"][0]
    proofs=copy.deepcopy(a["proofs"]);proofs[obs.observation_id]["coverage"]["analyzed_files"]=1
    with pytest.raises(ValueError):PastStore(a["registration"],a["domain"],a["lineage"],[obs],proofs)
    with pytest.raises(ValueError):PastStore(a["registration"],a["domain"],a["lineage"],[obs,obs],a["proofs"])
    with pytest.raises(ValueError):PastStore(a["registration"],a["domain"],a["lineage"],[obs],{})
    with pytest.raises(ValueError):PastStore(a["registration"],a["domain"],a["lineage"].archive,[obs],a["proofs"])


@pytest.mark.parametrize("case",["unknown","symlink","generated"])
def test_git_inventory_blockers_and_exclusions(study,case):
    a=study;path=a["repo"]/ROOT/({"unknown":"x.ts","symlink":"link.py","generated":"generated/x.py"}[case])
    path.parent.mkdir(parents=True,exist_ok=True)
    if case=="symlink":path.symlink_to("main.py")
    else:path.write_text("# synthetic\n")
    command(a["repo"],"add",".")
    command(a["repo"],"commit","-qm","synthetic new scope state",env=dict(os.environ,GIT_AUTHOR_DATE="2020-08-01T00:00:00Z",GIT_COMMITTER_DATE="2020-08-01T00:00:00Z"))
    tip=command(a["repo"],"rev-parse","HEAD")
    lineage=ScopedGit(GitArchive(a["repo"],tip,"2021-01-01T00:00:00Z"),REPO)
    inv=lineage.inventory(tip)
    assert bool(inv["blockers"]) == (case!="generated")
    if case!="generated":
        with pytest.raises(ValueError):lineage.production_paths(tip)


def test_unmeasured_changed_state_not_carried(study):
    a=study
    subset=a["observations"][:3]
    store=PastStore(a["registration"],a["domain"],a["lineage"],subset,a["proofs"])
    origin=origin_identity(store,a["cutoff"],30)
    label=target_status(origin,store)
    assert label["actual_minutes"] is None and label["label_status"]=="UNKNOWN"
    assert store.at(origin["endpoint_utc"]) is None


def test_actual_published_source_grid_deterministic():
    # Source-only inspection of existing real Git objects; no measurements/outcomes.
    base=Path(__file__).resolve().parents[1]/"examples/phase5_2"
    configs=json.loads((base/"replay_sources.example.json").read_text())
    if not all(Path(c["path"]).exists() for c in configs):pytest.skip("Pinned local Git objects unavailable")
    jobs=json.loads((base/"readiness_manifest.json").read_text())["planned_jobs"]
    one=inspect_sources(configs,jobs);two=inspect_sources(configs,jobs)
    assert one==two and len(one["source_states"])==18
    assert len({r["commit_sha"] for r in one["source_states"]})==18
    assert all(not r["inventory"]["blockers"] for r in one["source_states"])
    assert all(r["reserved_role"]=="quarantine" for r in one["registrations"])
    bad=copy.deepcopy(jobs);bad[0]["tree_sha"]="a"*40
    with pytest.raises(ValueError):inspect_sources(configs,bad)


@pytest.mark.parametrize("change",["mqr","plugins","scope","incomplete","quarantine","ref"])
def test_domain_and_admission_gates(study,change):
    a=study;domain=copy.deepcopy(a["domain"]);reg=copy.deepcopy(a["registration"])
    if change=="mqr":domain["manifest"]["metric_mode"]="MQR"
    if change=="plugins":domain["manifest"]["plugins"]=domain["manifest"]["plugins"][:1]
    if change=="scope":domain["manifest"]["scope_policy_sha256"]=SCOPE_ID
    if change=="incomplete":domain["manifest"]["rules_sha256"]=None
    if change in ("mqr","plugins","scope","incomplete"):domain=analyzer_domain(domain["manifest"])
    if change=="quarantine":reg["reserved_role"]="quarantine"
    if change=="ref":reg["branch_reference_observed_at"]="2022-01-01T00:00:00Z"
    with pytest.raises(ValueError):PastStore(reg,domain,a["lineage"],a["observations"],a["proofs"])


@pytest.mark.parametrize("languages",[{"py":20,"js":0},{"py":99,"js":1},{"py":10,"js":10,"ts":10}])
def test_native_language_coverage_not_path_proxy(study,languages):
    a=study;obs=replace(a["observations"][0],languages=languages)
    proofs={obs.observation_id:a["proofs"][a["observations"][0].observation_id]}
    with pytest.raises(ValueError):PastStore(a["registration"],a["domain"],a["lineage"],[obs],proofs)


def test_past_only_operational_availability(study):
    a=study;reg=dict(a["registration"],study_mode="OPERATIONAL_ASOF")
    store=PastStore(reg,a["domain"],a["lineage"],a["observations"],a["proofs"])
    assert store.at(a["cutoff"]) is None


def test_identity_and_integrity_reject_changed_bytes(study):
    a=study;e=a["index"][0]
    (a["raw"]/e["file_components_payload"]).write_text("{}")
    with pytest.raises(ValueError):read_archive(a["raw"],[e],a["lineage"])


def test_inventory_identity_is_deterministic_and_revision_bound(study):
    a=study;sha=a["observations"][0].commit_sha
    assert a["lineage"].inventory(sha)==a["lineage"].inventory(sha)
    with pytest.raises(ValueError):a["lineage"].inventory("a"*40)
    paths=a["lineage"].events("2020-01-01T00:00:00Z",a["cutoff"])
    assert all(p.startswith(ROOT) for event in paths for p in event["paths"])


def test_scanner_ce_task_identity(study):
    a=study;entry=copy.deepcopy(a['index'][0]);raw=a['raw']
    c=json.loads((raw/entry['coverage_payload']).read_text())
    scanner=json.loads((raw/entry['scanner_completion_payload']).read_text())
    scanner['ce_task_id']='other-task'
    c['scanner_completion_sha256']=write(raw/entry['scanner_completion_payload'],scanner)
    entry['coverage_sha256']=write(raw/entry['coverage_payload'],c)
    with pytest.raises(ValueError):read_archive(raw,[entry],a['lineage'])


def test_source_preflight_rejects_outcome_fields():
    base=Path(__file__).resolve().parents[1]/'examples/phase5_2'
    configs=json.loads((base/'replay_sources.example.json').read_text())
    jobs=json.loads((base/'readiness_manifest.json').read_text())['planned_jobs']
    configs[0]['future_debt']=10
    with pytest.raises(ValueError,match='source-only'):inspect_sources(configs,jobs)
