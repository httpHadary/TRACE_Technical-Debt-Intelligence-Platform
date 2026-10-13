"""Synthetic software proof only; metrics in these fixtures are not real accuracy."""
from datetime import timedelta
from pathlib import Path
import os
import subprocess
import sys

import pytest

from contracts import read_csv, read_json, write_json
from forecasting.dataset import build_dataset, transform, verify_dataset
from forecasting.evaluation import EvaluationConfig, evaluate_dataset, feature_matrix, load_rows, make_folds, metrics
from forecasting.git import GitRepository, java_package
from forecasting.graphs import extract_graph
from forecasting.identity import IdentityTracker, ModuleDefinition
from forecasting.interfaces import ForecastDataset, aggregate_file_predictions, align_external_predictions
from forecasting.schema import ForecastConfig, Snapshot, assert_available, iso, timestamp

META = dict(sonarqube_version="10", java_analyzer_version="7", quality_profile_hash="profile1",
            compatible_rule_domain_version="rules1", scanner_image="image@sha256:" + "a" * 64,
            analysis_mode="SOURCE_ONLY")
ROOT_TIME = timestamp("2020-01-01T00:00:00Z")


class Fixture:
    def __init__(self, path):
        self.path = path
        path.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "offline@example.invalid")
        self.git("config", "user.name", "Fixture")
        for name in ("a", "b"):
            other = "b" if name == "a" else "a"
            self.write(f"{name}/pom.xml", f"<project><groupId>acme</groupId><artifactId>{name}</artifactId>"
                f"<dependencies><dependency><groupId>acme</groupId><artifactId>{other}</artifactId></dependency>"
                "</dependencies></project>")
            for index in (1, 2):
                cls = name.upper() + str(index)
                self.write(f"{name}/src/main/java/acme/{name}/{cls}.java",
                           f"package acme.{name};\nimport acme.{other}.{other.upper()}1;\npublic class {cls} {{}}\n")
        self.commit(ROOT_TIME)

    def write(self, path, text):
        target = self.path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def git(self, *args, date=None):
        env = dict(os.environ)
        if date:
            env.update(GIT_AUTHOR_DATE=iso(date), GIT_COMMITTER_DATE=iso(date))
        return subprocess.run(["git", "-C", str(self.path), *args], check=True,
                              capture_output=True, text=True, env=env).stdout.strip()

    def commit(self, date):
        self.git("add", "-A")
        self.git("commit", "--allow-empty", "-m", "fixture", date=date)
        return self.git("rev-parse", "HEAD")

    def snapshot(self, cutoff, debt=20, meta=None, weekly=True):
        repo = GitRepository(self.path)
        commit = repo.resolve("main", iso(cutoff))
        files = {p: dict(sqale_minutes=debt, combined_effort_minutes=None if debt is None else debt + 5, ncloc=100,
                        complexity=10, cognitive_complexity=None, finding_count=2)
                 for p in repo.tree(commit) if repo.production(p)}
        return Snapshot("fixture", iso(cutoff), commit, files, meta or META.copy(), weekly=weekly)

    def source(self, snapshots):
        return {"repo_path": str(self.path), "branch": "main", "snapshots": snapshots}


@pytest.fixture
def fixture(tmp_path):
    return Fixture(tmp_path / "git")


def test_prediction_contract_rejects_84_and_naive_time():
    assert ForecastConfig(horizon="exact90").days == 90
    assert ForecastConfig(horizon="approx91").days == 91
    with pytest.raises(ValueError):
        ForecastConfig(horizon="84")
    with pytest.raises(ValueError):
        timestamp("2020-01-01")
    with pytest.raises(ValueError):
        ForecastConfig(growth_threshold_minutes=float("nan"))
    with pytest.raises(ValueError):
        assert_available("2020-01-01T00:00:00Z", ["2020-01-02T00:00:00Z"])


def test_known_graph_cycles_build_imports_cochange_and_contributors(fixture):
    snapshot = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    repo = GitRepository(fixture.path)
    definition = ModuleDefinition.create(repo, snapshot, ForecastConfig(strategy="build"))
    identities, packages, _ = IdentityTracker(definition).update(repo, snapshot)
    edges, stats, unresolved = extract_graph(repo, snapshot, identities, packages, definition)
    kinds = {e["edge_type"] for e in edges}
    assert kinds == {"build_dependency", "source_dependency", "cochange", "contributor"}
    assert stats["a"]["dependency_out_degree"] == 1
    assert stats["a"]["dependency_in_degree"] == 1
    assert stats["a"]["dependency_cycle"] == 1
    assert stats["a"]["contributor_weight"] == 1
    assert stats["a"]["commits_26w"] == 1
    assert stats["a"]["build_coverage"] == 1
    assert stats["a"]["graph_status"] == "OBSERVED_SOURCE_APPROXIMATION"
    assert not unresolved


def test_future_backdated_branch_cannot_change_historical_graph(fixture):
    snapshot = fixture.snapshot(ROOT_TIME + timedelta(days=2))
    config = ForecastConfig(strategy="build")
    before = transform([fixture.source([snapshot])], config)
    fixture.git("checkout", "-b", "future-side")
    fixture.write("a/src/main/java/acme/a/A1.java", "package acme.a; class A1 {}\n")
    fixture.commit(ROOT_TIME + timedelta(days=1))
    fixture.git("checkout", "main")
    fixture.git("merge", "--no-ff", "future-side", "-m", "later merge", date=ROOT_TIME + timedelta(days=100))
    after = transform([fixture.source([snapshot])], config)
    assert before["edges"] == after["edges"]
    assert before["graphs"] == after["graphs"]
    assert before["states"] == after["states"]


def test_graph_unknowns_are_not_empty_graph(fixture):
    fixture.write("a/build.gradle", "dependencies { implementation project(':b') }\n")
    fixture.write("a/pom.xml", "broken XML")
    fixture.write("a/src/main/java/acme/a/A1.java",
                  'package acme.a; import external.Missing; class A1 { String s="import fake.No;"; }')
    fixture.commit(ROOT_TIME + timedelta(days=1))
    data = transform([fixture.source([fixture.snapshot(ROOT_TIME + timedelta(days=2))])], ForecastConfig(strategy="build"))
    a = next(r for r in data["graphs"] if r["stable_module_id"] == next(s["stable_module_id"] for s in data["states"] if s["module_path"] == "a"))
    assert a["unresolved_imports"] == 1
    assert a["build_coverage"] == 0
    assert a["dependency_available"] == 1
    assert any(e["edge_type"] == "build_dependency" for e in data["edges"])
    assert java_package('/*package fake;*/ package actual; class A {}') == "actual"


def test_birth_deletion_and_complete_membership_rename(fixture):
    config = ForecastConfig(strategy="build")
    first = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    repo = GitRepository(fixture.path)
    tracker = IdentityTracker(ModuleDefinition.create(repo, first, config))
    original, _, _ = tracker.update(repo, first)
    fixture.git("mv", "a", "renamed")
    fixture.commit(ROOT_TIME + timedelta(days=2))
    renamed, _, events = tracker.update(repo, fixture.snapshot(ROOT_TIME + timedelta(days=3)))
    assert renamed["renamed"]["stable_module_id"] == original["a"]["stable_module_id"]
    assert renamed["renamed"]["lineage_status"] == "RENAMED_MEMBERSHIP"
    fixture.git("rm", "-r", "b")
    fixture.write("new/pom.xml", "<project/>")
    fixture.write("new/src/main/java/newpkg/N.java", "package newpkg; class N {}")
    fixture.commit(ROOT_TIME + timedelta(days=4))
    current, _, events = tracker.update(repo, fixture.snapshot(ROOT_TIME + timedelta(days=5)))
    assert "b" not in current and current["new"]["lineage_status"] == "BIRTH"
    assert any(e["event"] == "DELETION_OR_RESTRUCTURE" and e["source"] == "b" for e in events)


def test_split_and_merge_are_explicitly_ambiguous(fixture):
    repo = GitRepository(fixture.path)
    first = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    tracker = IdentityTracker(ModuleDefinition.create(repo, first, ForecastConfig(strategy="build")))
    tracker.update(repo, first)
    fixture.write("c/pom.xml", "<project/>")
    destination = fixture.path / "c/src/main/java/acme/a"
    destination.mkdir(parents=True)
    fixture.git("mv", "a/src/main/java/acme/a/A2.java", "c/src/main/java/acme/a/A2.java")
    fixture.commit(ROOT_TIME + timedelta(days=2))
    split, _, events = tracker.update(repo, fixture.snapshot(ROOT_TIME + timedelta(days=3)))
    assert split["a"]["lineage_status"] == split["c"]["lineage_status"] == "AMBIGUOUS_SPLIT"
    fixture.git("mv", "c/src/main/java/acme/a/A2.java", "a/src/main/java/acme/a/A2.java")
    fixture.git("rm", "c/pom.xml")
    fixture.commit(ROOT_TIME + timedelta(days=4))
    merged, _, _ = tracker.update(repo, fixture.snapshot(ROOT_TIME + timedelta(days=5)))
    assert merged["a"]["lineage_status"] == "AMBIGUOUS_MERGE"


def test_package_strategy_is_separate_and_frozen(fixture):
    source = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    repo = GitRepository(fixture.path)
    build = ModuleDefinition.create(repo, source, ForecastConfig(strategy="build"))
    package = ModuleDefinition.create(repo, source, ForecastConfig(strategy="package"))
    assert build.config_id != package.config_id
    assert package.package_base == "acme"
    fixture.write("c/pom.xml", "<project/>")
    fixture.write("c/src/main/java/other/pkg/C.java", "package other.pkg; class C {}")
    fixture.commit(ROOT_TIME + timedelta(days=2))
    groups, _ = package.groups(repo, "HEAD", fixture.snapshot(ROOT_TIME + timedelta(days=3)).files)
    assert set(groups) == {"acme.a", "acme.b", "other.pkg"}
    assert package.package_base == "acme"


def test_scope_movement_decomposition_and_future_membership_not_predictors(fixture):
    first = fixture.snapshot(ROOT_TIME + timedelta(days=1), debt=20)
    destination = fixture.path / "b/src/main/java/acme/a"
    destination.mkdir(parents=True)
    fixture.git("mv", "a/src/main/java/acme/a/A2.java", "b/src/main/java/acme/a/A2.java")
    fixture.commit(ROOT_TIME + timedelta(days=50))
    future = fixture.snapshot(timestamp(first.cutoff) + timedelta(days=91), debt=20)
    data = transform([fixture.source([first, future])], ForecastConfig(strategy="build", growth_threshold_minutes=10))
    labels = {next(s["module_path"] for s in data["states"] if s["observation_id"] == r["observation_id"]): r
              for r in data["labels"] if r["prediction_timestamp"] == first.cutoff}
    assert labels["a"]["debt_delta_minutes"] == -20
    assert labels["b"]["debt_delta_minutes"] == 20
    assert labels["b"]["retained_debt_delta_minutes"] == 0
    assert labels["b"]["added_debt_minutes"] == 20
    assert labels["b"]["membership_changed"] == 1
    with pytest.raises(ValueError):
        feature_matrix([], ["added_debt_minutes"])
    original = transform([fixture.source([first])], ForecastConfig(strategy="build"))
    assert data["states"][:2] == original["states"]


@pytest.mark.parametrize("mode,offset,status", [("exact90", 90, "OBSERVED"), ("exact90", 91, "UNKNOWN_OBSERVATION"),
                                                  ("approx91", 91, "OBSERVED"), ("approx91", 84, "UNKNOWN_OBSERVATION")])
def test_only_exact_endpoint_has_target(fixture, mode, offset, status):
    first = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    future = fixture.snapshot(timestamp(first.cutoff) + timedelta(days=offset), debt=40, weekly=offset % 7 == 0)
    data = transform([fixture.source([first, future])], ForecastConfig(strategy="build", horizon=mode))
    label = data["labels"][0]
    assert label["target_status"] == status
    assert label["horizon_days"] == (90 if mode == "exact90" else 91)
    if status != "OBSERVED":
        assert label["debt_delta_minutes"] is None and label["growth_label"] is None


def test_missing_target_and_intermediate_analyzer_change(fixture):
    first = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    future = fixture.snapshot(timestamp(first.cutoff) + timedelta(days=91), debt=None)
    for values in future.files.values():
        values["combined_effort_minutes"] = None
    data = transform([fixture.source([first, future])], ForecastConfig(strategy="build"))
    assert data["labels"][0]["debt_delta_minutes"] is None
    future = fixture.snapshot(timestamp(first.cutoff) + timedelta(days=91), debt=40)
    middle = fixture.snapshot(timestamp(first.cutoff) + timedelta(days=7), meta={**META, "quality_profile_hash": "changed"})
    data = transform([fixture.source([first, middle, future])], ForecastConfig(strategy="build"))
    assert data["labels"][0]["target_status"] == "INCOMPATIBLE"
    assert not data["arrays"]["snapshot_mask"][2, 0]


def test_immutable_reproducible_dataset_masks_and_graph_interface(fixture, tmp_path):
    snapshots = [fixture.snapshot(ROOT_TIME + timedelta(days=1 + 7 * i), debt=20 + i) for i in range(16)]
    source, config = fixture.source(snapshots), ForecastConfig(strategy="build")
    one = build_dataset([source], config, tmp_path / "one", data_kind="synthetic")
    two = build_dataset([source], config, tmp_path / "two", data_kind="synthetic")
    assert one["data_version"] == two["data_version"]
    assert one["outputs"] == two["outputs"]
    with pytest.raises(FileExistsError):
        build_dataset([source], config, tmp_path / "one", "synthetic")
    dataset = ForecastDataset(tmp_path / "one")
    seq = dataset.sequence(dataset.states[0]["observation_id"])
    assert seq["snapshot_mask"].sum() == 1
    assert not seq["feature_mask"][:, 4].any()  # missing cognitive complexity preserved
    window = dataset.graph_window(dataset.states[0]["observation_id"])
    assert len(window) == 26 and not window[0]["graph_available"]
    assert window[-1]["graph_available"] and "cochange" in window[-1]["relations"]
    audit = read_json(tmp_path / "one/dataset_audit.json")
    assert audit["incomplete_history_observations"] == 32
    assert audit["eligible_labels"] == 6
    (tmp_path / "one/module_labels.csv").write_text("tampered")
    with pytest.raises(ValueError, match="checksum"):
        verify_dataset(tmp_path / "one")


def test_file_aggregation_uses_only_origin_membership_and_exact_cohort():
    origin = dict(repository_id="repo", stable_module_id="module", prediction_timestamp="2020-01-01T00:00:00Z", observation_id="origin")
    membership = [{**origin, "stable_file_id": "file1"}, {**origin, "stable_file_id": "futurefile", "prediction_timestamp": "2020-04-01T00:00:00Z"}]
    files = [{"repository_id": "repo", "stable_file_id": "file1", "prediction_timestamp": origin["prediction_timestamp"],
              "max_feature_timestamp": origin["prediction_timestamp"], "predicted_debt_delta_minutes": 10}]
    predictions = aggregate_file_predictions(membership, files, [origin])
    assert predictions[0]["predicted_debt_delta_minutes"] == 10
    assert align_external_predictions([origin], predictions) == predictions
    with pytest.raises(ValueError):
        align_external_predictions([origin], [])
    with pytest.raises(ValueError):
        aggregate_file_predictions(membership, [], [origin])


@pytest.fixture
def long_dataset(fixture, tmp_path):
    snapshots = []
    for i in range(75):
        cutoff = ROOT_TIME + timedelta(days=8 + 7 * i)
        fixture.write("a/src/main/java/acme/a/A1.java",
                      f"package acme.a; import acme.b.B1; class A1 {{ int revision={i}; }}\n")
        fixture.commit(cutoff - timedelta(days=1))
        snapshot = fixture.snapshot(cutoff, debt=(i % 20) * 10)
        for p, values in snapshot.files.items():
            values["ncloc"] = 100 + i
            if p.startswith("b/"):
                values["sqale_minutes"] = (19 - i % 20) * 10
        snapshots.append(snapshot)
    output = tmp_path / "long"
    build_dataset([fixture.source(snapshots)], ForecastConfig(strategy="build", growth_threshold_minutes=5), output, "synthetic")
    return output, snapshots


def test_actual_catboost_models_shared_folds_predictions_and_purging(long_dataset, tmp_path):
    dataset, snapshots = long_dataset
    config = EvaluationConfig(first_validation_cutoff=snapshots[30].cutoff, validation_weeks=4, test_weeks=4,
                              min_train_rows=10, iterations=5, precision_k=1)
    manifest, rows = load_rows(dataset)
    folds = make_folds(rows, config)
    fold = folds[0]
    assert all(timestamp(r["label_end_timestamp"]) < timestamp(fold["validation_start"]) for r in fold["train"])
    assert all(timestamp(r["label_end_timestamp"]) < timestamp(fold["test_start"]) for r in fold["validation"])
    result = evaluate_dataset(dataset, tmp_path / "eval", config)
    assert result["status"] == "COMPLETE" and result["claim"] == "SOFTWARE_VALIDATION_ONLY"
    predictions = read_csv(tmp_path / "eval/predictions.csv")[1]
    for phase in ("validation", "test"):
        populations = [{r["observation_id"] for r in predictions if r["model"] == model and r["period"] == phase} for model in ("M0", "M1", "M2")]
        assert populations[0] == populations[1] == populations[2]
    assert list((tmp_path / "eval/models").rglob("*.cbm"))
    comparisons = read_json(tmp_path / "eval/model_comparison.json")
    assert len(comparisons) == 6
    assert all(r["effective_independent_sample_size"] is None for r in comparisons)
    repeat = evaluate_dataset(dataset, tmp_path / "eval-repeat", config)
    assert read_csv(tmp_path / "eval-repeat/predictions.csv")[1] == predictions
    assert repeat["status"] == "COMPLETE"


def test_repo_holdout_excludes_repository_and_future_labels():
    rows = []
    for repository in ("a", "b", "c"):
        for i in range(80):
            date = ROOT_TIME + timedelta(weeks=i)
            rows.append(dict(repository_id=repository, prediction_timestamp=iso(date), label_end_timestamp=iso(date + timedelta(days=91))))
    folds = make_folds(rows, EvaluationConfig(iso(ROOT_TIME + timedelta(weeks=30)), validation_weeks=4, test_weeks=4))
    assert len(folds) == 4
    for fold in folds[1:]:
        assert all(r["repository_id"] != fold["heldout_repository"] for r in fold["train"])
        assert all(r["repository_id"] == fold["heldout_repository"] for r in fold["test"])


def test_verified_collector_bridge_integration(sandbox, monkeypatch, tmp_path):
    import scan_weekly_snapshots
    from forecasting.__main__ import read_workspace, endpoint_requests
    sandbox["collect"]()
    for week in range(2, 16):
        scan_weekly_snapshots.fill_week_from("week_01", f"week_{week:02d}")
    write_json("repo_context.json", dict(repository_id="sample", repo_path=str(sandbox["repo"]),
        project_key="p:sample", branch="main", start_date="2020-01-02", weeks=15))
    from contracts import sha256
    before = sha256("data/snapshots.csv")
    source = read_workspace(sandbox["work"])
    assert len(source["snapshots"]) == 15
    assert source["snapshots"][0]["cutoff"] == "2020-01-09T00:00:00+00:00"
    assert source["snapshots"][0]["files"][sandbox["paths"][0]]["sqale_minutes"] == 0
    requests = endpoint_requests(source)
    assert len(requests) == 15
    output = tmp_path / "verified-forecast"
    build_dataset([source], ForecastConfig(), output, "synthetic")
    assert read_json(output / "dataset_audit.json")["eligible_labels"] == 2
    assert sha256("data/snapshots.csv") == before and sandbox["docker_calls"] == 1
    # Exercise the documented public CLI, including honest insufficient-data exit.
    source_root = Path(__file__).resolve().parents[1]
    cli_output = tmp_path / "cli-dataset"
    generated = subprocess.run([sys.executable, "-m", "forecasting", "build", "--workspace", str(sandbox["work"]),
                                "--output", str(cli_output)], cwd=source_root, capture_output=True, text=True)
    assert generated.returncode == 0, generated.stderr
    evaluated = subprocess.run([sys.executable, "-m", "forecasting", "evaluate", "--dataset", str(cli_output),
                                "--output", str(tmp_path / "cli-evaluation"),
                                "--first-validation-cutoff", "2020-02-01T00:00:00Z"],
                               cwd=source_root, capture_output=True, text=True)
    assert evaluated.returncode == 2, evaluated.stderr
    assert read_json(tmp_path / "cli-evaluation/experiment_manifest.json")["status"] == "INSUFFICIENT_DATA"


def test_endpoint_collection_reuses_verified_scan_and_binds_exact_cutoff(sandbox, tmp_path, monkeypatch):
    from forecasting.collector_bridge import collect_endpoints, load_verified
    from forecasting.__main__ import endpoint_requests
    import scan_snapshot
    import sonar_evidence
    import scan_weekly_snapshots
    import build_module_mart as legacy_mart
    from run_all_repos import verify_generation
    from contracts import sha256
    sandbox["collect"]()
    scan_weekly_snapshots.fill_week_from("week_01", "week_02")
    write_json("repo_context.json", dict(repository_id="sample", repo_path=str(sandbox["repo"]),
        project_key="p:sample", branch="main", start_date="2020-01-02", weeks=2))
    monkeypatch.setattr(sys, "argv", ["build_module_mart.py", "2020-01-02", "main", "2"])
    legacy_mart.main()
    legacy_generation = verify_generation(sandbox["work"])
    requests = endpoint_requests(load_verified())
    write_json(tmp_path / "requests.json", requests)
    before = {str(p): sha256(p) for p in Path("data").rglob("*") if p.is_file()}
    real_scan, real_export = scan_snapshot.scan_snapshot, sonar_evidence.collect_snapshot
    monkeypatch.setattr(scan_snapshot, "scan_snapshot", lambda commit, label:
                        real_scan(commit, label, client_factory=sandbox["client"]))
    monkeypatch.setattr(sonar_evidence, "collect_snapshot", lambda label:
                        real_export(label, client_factory=sandbox["client"]))
    collect_endpoints(tmp_path / "requests.json")
    source = load_verified()
    assert len(source["snapshots"]) == 4 and sandbox["docker_calls"] == 2
    assert {str(p): sha256(p) for p in Path("data").rglob("*") if p.is_file()} == before
    assert len(read_csv("data/snapshots.csv")[1]) == 2
    assert len(read_csv("forecast_endpoints/data/snapshots.csv")[1]) == 2
    assert verify_generation(sandbox["work"]) == legacy_generation
    data = transform([source], ForecastConfig(horizon="exact90"))
    assert data["labels"][0]["target_status"] == "OBSERVED"
    assert data["labels"][0]["horizon_days"] == 90
    # Simulate completion before the sidecar commit marker was durable.
    Path("forecast_endpoints/data/forecast_endpoint_cutoffs.json").unlink()
    collect_endpoints(tmp_path / "requests.json")
    assert len(load_verified()["snapshots"]) == 4 and sandbox["docker_calls"] == 2
    assert verify_generation(sandbox["work"]) == legacy_generation
    assert sonar_evidence.DATA == Path("data") and scan_snapshot.DATA == Path("data")


def test_deletion_is_excluded_not_zero_debt(fixture):
    first = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    fixture.git("rm", "-r", "a")
    fixture.commit(ROOT_TIME + timedelta(days=10))
    future = fixture.snapshot(timestamp(first.cutoff) + timedelta(days=91))
    data = transform([fixture.source([first, future])], ForecastConfig(strategy="build"))
    a = next(s for s in data["states"] if s["module_path"] == "a")
    label = next(r for r in data["labels"] if r["observation_id"] == a["observation_id"])
    assert label["target_status"] == "UNKNOWN_OBSERVATION" and label["debt_delta_minutes"] is None
    assert label["exclusion_reason"] == "module_deleted_or_lineage_unresolved"


def test_insufficient_data_exports_honest_report(fixture, tmp_path):
    dataset = tmp_path / "small"
    build_dataset([fixture.source([fixture.snapshot(ROOT_TIME + timedelta(days=1))])],
                  ForecastConfig(), dataset, "synthetic")
    result = evaluate_dataset(dataset, tmp_path / "small-eval", EvaluationConfig("2021-01-01T00:00:00Z"))
    assert result["status"] == "INSUFFICIENT_DATA"
    assert read_json(tmp_path / "small-eval/model_comparison.json") == []
    assert read_csv(tmp_path / "small-eval/predictions.csv")[1] == []
    assert not (tmp_path / "small-eval/models").exists()


def test_unverified_real_inputs_and_failed_dataset_are_rejected(fixture, tmp_path):
    snapshot = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    with pytest.raises(ValueError, match="verified collector"):
        build_dataset([fixture.source([snapshot])], ForecastConfig(), tmp_path / "unverified")
    snapshot.files.pop(next(iter(snapshot.files)))
    with pytest.raises(ValueError, match="population"):
        build_dataset([fixture.source([snapshot])], ForecastConfig(), tmp_path / "failed", "synthetic")
    assert read_json(tmp_path / "failed/manifest.json")["status"] == "FAILED"
    with pytest.raises(ValueError, match="Incomplete"):
        verify_dataset(tmp_path / "failed")


def test_pr_metrics_insufficient_events_and_negative_snapshot_blocks():
    rows = [dict(repository_id="repo", stable_module_id=str(i), observation_id=str(i), module_strategy="build",
                 prediction_timestamp=iso(ROOT_TIME + timedelta(weeks=i)), label_end_timestamp=iso(ROOT_TIME + timedelta(weeks=i + 13)),
                 debt_delta_minutes=10 if i < 2 else 0, growth_label=int(i < 2), membership_changed_target=0) for i in range(4)]
    config = EvaluationConfig("2021-01-01T00:00:00Z", precision_k=1)
    result = metrics(rows, [0] * 4, [0] * 4, config)
    assert result["precision_at_k"] == .5 and result["precision_eligible_snapshot_blocks"] == 4
    insufficient = metrics(rows[:1], [0], [0], config)
    assert insufficient["growth_pr_auc_average_precision"] is None
    assert insufficient["precision_at_k"] is None


def test_new_module_birth_keeps_prior_id_and_short_history(fixture):
    first = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    prefix = transform([fixture.source([first])], ForecastConfig(strategy="build"))
    fixture.write("new/pom.xml", "<project/>")
    fixture.write("new/src/main/java/newpkg/N.java", "package newpkg; class N {}")
    fixture.commit(ROOT_TIME + timedelta(days=5))
    second = fixture.snapshot(ROOT_TIME + timedelta(days=8))
    extended = transform([fixture.source([first, second])], ForecastConfig(strategy="build"))
    assert prefix["states"] == extended["states"][:2]
    new = next(r for r in extended["states"] if r["module_path"] == "new")
    assert new["lineage_status"] == "BIRTH" and new["history_points"] == 1
    assert new["commits_26w"] == 1


def test_graph_frames_mask_incompatible_analyzers(fixture, tmp_path):
    snapshots = [fixture.snapshot(ROOT_TIME + timedelta(days=1 + 7 * i),
                 meta={**META, "quality_profile_hash": "changed"} if i == 1 else META.copy()) for i in range(3)]
    path = tmp_path / "compatibility"
    build_dataset([fixture.source(snapshots)], ForecastConfig(strategy="build"), path, "synthetic")
    dataset = ForecastDataset(path)
    origin = next(r for r in dataset.states if r["prediction_timestamp"] == snapshots[-1].cutoff)
    window = dataset.graph_window(origin["observation_id"])
    assert window[-2]["compatibility_status"] == "INCOMPATIBLE_ANALYZER"
    assert not window[-2]["graph_available"] and not window[-2]["feature_mask"].any()
    assert window[-2]["relations"] == {}
    assert window[-1]["graph_available"]


def test_split_interval_excludes_label_even_with_observed_debt(fixture):
    first = fixture.snapshot(ROOT_TIME + timedelta(days=1))
    fixture.write("c/pom.xml", "<project/>")
    (fixture.path / "c/src/main/java/acme/a").mkdir(parents=True)
    fixture.git("mv", "a/src/main/java/acme/a/A2.java", "c/src/main/java/acme/a/A2.java")
    fixture.commit(ROOT_TIME + timedelta(days=10))
    middle = fixture.snapshot(ROOT_TIME + timedelta(days=15))
    future = fixture.snapshot(timestamp(first.cutoff) + timedelta(days=91))
    data = transform([fixture.source([first, middle, future])], ForecastConfig(strategy="build"))
    a = next(r for r in data["states"] if r["module_path"] == "a")
    label = next(r for r in data["labels"] if r["observation_id"] == a["observation_id"])
    assert label["exclusion_reason"] == "ambiguous_module_lineage" and label["debt_delta_minutes"] is None


def test_auto_strategy_does_not_count_orphan_as_descriptor_module(fixture):
    fixture.git("rm", "b/pom.xml")
    fixture.commit(ROOT_TIME + timedelta(days=1))
    snapshot = fixture.snapshot(ROOT_TIME + timedelta(days=2))
    definition = ModuleDefinition.create(GitRepository(fixture.path), snapshot, ForecastConfig())
    assert definition.strategy == "package"


def test_invalid_endpoint_request_does_not_scan_or_change_namespace(sandbox, tmp_path):
    from forecasting.collector_bridge import collect_endpoints
    import sonar_evidence
    import scan_snapshot
    sandbox["collect"]()
    write_json("repo_context.json", dict(repository_id="sample", repo_path=str(sandbox["repo"]),
        project_key="p:sample", branch="main", start_date="2020-01-02", weeks=1))
    write_json(tmp_path / "bad-request.json", [{"repository_id": "sample", "label": "endpoint_bad",
               "origin_cutoff": "2020-01-09T00:00:00Z", "cutoff": "2020-04-02T00:00:00Z",
               "commit": sandbox["commit"]}])
    with pytest.raises(ValueError, match="exactly 90"):
        collect_endpoints(tmp_path / "bad-request.json")
    assert sandbox["docker_calls"] == 1 and not Path("forecast_endpoints").exists()
    assert sonar_evidence.DATA == Path("data") and scan_snapshot.DATA == Path("data")


def test_namespace_restored_after_endpoint_scan_failure(sandbox, tmp_path, monkeypatch):
    from forecasting.collector_bridge import collect_endpoints, load_verified
    from forecasting.__main__ import endpoint_requests
    import sonar_evidence
    import scan_snapshot
    sandbox["collect"]()
    write_json("repo_context.json", dict(repository_id="sample", repo_path=str(sandbox["repo"]),
        project_key="p:sample", branch="main", start_date="2020-01-02", weeks=1))
    write_json(tmp_path / "requests.json", endpoint_requests(load_verified()))
    def fail(*args):
        raise OSError("Synthetic scanner failure")
    monkeypatch.setattr(scan_snapshot, "scan_snapshot", fail)
    with pytest.raises(OSError, match="Synthetic scanner"):
        collect_endpoints(tmp_path / "requests.json")
    assert sonar_evidence.DATA == Path("data") and scan_snapshot.DATA == Path("data")
    assert not Path("data/run.lock").exists() and not Path("forecast_endpoints/data/run.lock").exists()
