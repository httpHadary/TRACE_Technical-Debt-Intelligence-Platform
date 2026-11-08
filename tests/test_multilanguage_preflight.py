"""Synthetic source-planning tests; no builds, scanners, models or live services."""
from datetime import timedelta
import copy
import json
import subprocess

import pytest

from test_multilanguage_foundation import archive, command, write
from forecasting_multilanguage import preflight
from forecasting_multilanguage.contracts import iso, utc, digest
from forecasting_multilanguage.io import verify, file_sha256
from forecasting_multilanguage.registry import SCOPE_ID


def config(a):
    return dict(repository_id="synthetic", family_id="synthetic-family", canonical_url="https://example.invalid/synthetic",
                provider_repository_id="fixture", path=str(a["repo"]), tip_sha=a["registration"]["tip_sha"],
                ref_observed_utc=a["registration"]["branch_reference_observed_at"], t0_utc=a["cutoff"],
                production_roots=["main.py", "main.js"], expected_target="mixed_python_jsts",
                license_paths=["LICENSE"], build_paths=["pyproject.toml"])


def test_exact_six_cutoffs_and_no_weekly_substitution():
    t0="2024-10-01T00:00:00Z"
    records=preflight.six_cutoffs(t0)
    assert [r["offset_days"] for r in records]==[-90,-30,0,30,60,90]
    assert [r["cutoff_utc"] for r in records]==["2024-07-03T00:00:00Z","2024-09-01T00:00:00Z",t0,
        "2024-10-31T00:00:00Z","2024-11-30T00:00:00Z","2024-12-30T00:00:00Z"]
    assert all((utc(r["cutoff_utc"])-utc(t0)).total_seconds()==r["offset_days"]*86400 for r in records)


@pytest.mark.parametrize("path,role,language",[
    ("src/main.py","PROPOSED_PRODUCTION_SOURCE","py"),
    ("src/runtime.mjs","PROPOSED_PRODUCTION_SOURCE","js"),
    ("src/view.html","PROPOSED_PRODUCTION_SOURCE","web"),
    ("src/style.css","PROPOSED_PRODUCTION_SOURCE","css"),
    ("src/site.scss","UNRECOGNIZED_PRODUCTION_EXTENSION_REVIEW_REQUIRED",None),
    ("src/public/main.min.js","GENERATED_OR_VENDOR_REVIEW_REQUIRED",None),
    ("src/tests/main.py","TEST_VENDOR_GENERATED_DOC_OR_EXAMPLE",None),
    ("src/test_runtime.py","TEST_VENDOR_GENERATED_DOC_OR_EXAMPLE",None),
    ("src/vendor/library.js","TEST_VENDOR_GENERATED_DOC_OR_EXAMPLE",None),
    ("src/generated/output.py","TEST_VENDOR_GENERATED_DOC_OR_EXAMPLE",None),
    ("docs/conf.py","TEST_VENDOR_GENERATED_DOC_OR_EXAMPLE",None),
    ("src/main/java/overview.html","TEST_VENDOR_GENERATED_DOC_OR_EXAMPLE",None),
    ("src/fonts/main.woff2","PRODUCTION_ASSET_NOT_NATIVE_DEBT_SOURCE",None),
    ("src/data.json","PRODUCTION_RESOURCE_OR_METADATA_REVIEW_REQUIRED",None),
    ("other/main.py","OUTSIDE_DECLARED_PRODUCTION_ROOTS",None),
])
def test_every_file_has_explicit_scope_disposition(path,role,language):
    record=preflight.classify_path(path,["src"])
    assert (record["role"],record["proposed_language"])==(role,language)


@pytest.mark.parametrize("path",["../outside.py","/absolute.py","src/../../secret.py","bad\\name.py",""])
def test_unsafe_inventory_paths_fail(path):
    with pytest.raises(ValueError): preflight.classify_path(path,["src"])


def test_exact_git_inventory_and_no_automatic_admission(archive):
    a=archive;c=config(a)
    before={str(p):p.read_bytes() for p in a["raw"].glob("*.json")}
    result,inventories=preflight.plan_repository(c)
    assert result["lineage"]["complete_first_parent_objects"]
    assert result["lineage"]["frozen_schema2_lineage_status"]=="PASS"
    assert result["distinct_cutoff_commits"]==6
    assert len(inventories)==6
    assert result["native_debt_values"] is None and result["actual_analysis_ids"]==[]
    assert not result["collection_authorized"]
    assert result["cutoffs"][2]["commit_sha"]==a["index"][2]["commit_sha"]
    assert all(r["confirmed_sonar_ncloc_stratum"] is None for r in result["cutoffs"])
    assert before=={str(p):p.read_bytes() for p in a["raw"].glob("*.json")}
    assert result["frozen_scope_policy_hash"]==SCOPE_ID


def test_provisional_mix_is_not_actual_sonar_language_evidence():
    record=preflight.metadata_stratum({"py":90,"js":10,"web":500})
    assert record["proxy_stratum"]=="mixed_python_jsts"
    assert record["confirmed_sonar_ncloc_stratum"] is None
    assert preflight.metadata_stratum({"js":90,"ts":10})["proxy_stratum"]=="jsts_dominant"


@pytest.mark.parametrize("extra",["actual_minutes","target_status","model_error","label_store","test_scores"])
def test_outcome_driven_selection_fields_forbidden(archive,extra):
    c=config(archive);c[extra]=1
    with pytest.raises(ValueError,match="metadata-only"): preflight.plan_repository(c)


def test_preflight_publication_deterministic_and_preserves_inputs(archive):
    a=archive;c=config(a);path=a["tmp"]/"preflight.local.json";write(path,[c])
    original=path.read_bytes()
    for name in ("plan1","plan2"):
        preflight.main(["--config",str(path),"--output",str(a["tmp"]/name)])
    one,two=verify(a["tmp"]/"plan1"),verify(a["tmp"]/"plan2")
    assert one==two and path.read_bytes()==original
    assert (a["tmp"]/"plan1/manifest.json").read_bytes()==(a["tmp"]/"plan2/manifest.json").read_bytes()
    with pytest.raises(ValueError): preflight.main(["--config",str(path),"--output",str(a["repo"]/"new")])


def test_no_silent_fix_for_historical_inversion(archive):
    a=archive;c=config(a)
    (a["repo"]/"main.py").write_text("# inversion fixture\n")
    command(a["repo"],"add","main.py")
    import os
    command(a["repo"],"commit","-qm","inversion",env=dict(os.environ,GIT_AUTHOR_DATE="2020-06-01T00:00:00Z",GIT_COMMITTER_DATE="2020-06-01T00:00:00Z"))
    c["tip_sha"]=command(a["repo"],"rev-parse","HEAD")
    result,_=preflight.plan_repository(c)
    assert result["lineage"]["frozen_schema2_lineage_status"]=="BLOCKED"
    assert len(result["lineage"]["timestamp_inversions"])==1
    assert result["collection_authorized"] is False


def test_shallow_history_fails_and_no_fetch(archive,monkeypatch):
    a=archive;c=config(a);original=preflight.git;calls=[]
    def checked(path,*args):
        calls.append(args)
        if args==("rev-parse","--is-shallow-repository"):return b"true\n"
        return original(path,*args)
    monkeypatch.setattr(preflight,"git",checked)
    with pytest.raises(ValueError,match="Shallow"): preflight.plan_repository(c)
    assert not any("fetch" in call or "checkout" in call for call in calls)


def test_symlinks_and_submodules_not_complete_source_claims(archive):
    import os
    a=archive
    os.symlink("main.py",a["repo"]/"linked.py")
    command(a["repo"],"add","linked.py")
    command(a["repo"],"commit","-qm","symlink")
    rows=preflight.tree_inventory(a["repo"],command(a["repo"],"rev-parse","HEAD"),["linked.py"])
    row=next(r for r in rows if r["path"]=="linked.py")
    assert row["role"]=="SYMLINK_OR_SUBMODULE_REQUIRES_SEPARATE_PROOF"


def test_no_duplicate_family_configuration(archive):
    a=archive;c=config(a);path=a["tmp"]/"duplicates.json";write(path,[c,c])
    with pytest.raises(ValueError,match="Unique"): preflight.main(["--config",str(path),"--output",str(a["tmp"]/"bad")])


def test_missing_exact_past_state_and_future_ref_fail(archive):
    c=config(archive);c["t0_utc"]="2010-01-01T00:00:00Z"
    with pytest.raises(ValueError,match="No code state"): preflight.plan_repository(c)
    c=config(archive);c["t0_utc"]="2022-01-01T00:00:00Z"
    with pytest.raises(ValueError,match="beyond observed ref"): preflight.plan_repository(c)
