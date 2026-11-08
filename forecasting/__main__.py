"""CLI for verified dataset generation, endpoint planning and baseline evaluation."""
from datetime import timedelta
from pathlib import Path
import argparse
import os
import subprocess
import sys
import tempfile

from contracts import digest, read_json, write_json
from .schema import ForecastConfig, iso, timestamp


def read_workspace(workspace):
    workspace = Path(workspace).resolve()
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="td-forecast-read-") as directory:
        out = Path(directory) / "source.json"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(root)
        result = subprocess.run([sys.executable, "-m", "forecasting.collector_bridge", "--output", str(out)],
                                cwd=workspace, env=env, capture_output=True, text=True)
        if result.returncode:
            raise ValueError(f"Verified workspace ingestion failed: {workspace}\n{result.stderr}")
        return read_json(out)


def endpoint_requests(source):
    from .git import GitRepository
    repo = GitRepository(source["repo_path"])
    known = {s["cutoff"] for s in source["snapshots"]}
    requests = []
    for snapshot in source["snapshots"]:
        if not snapshot["weekly"]:
            continue
        end = iso(timestamp(snapshot["cutoff"]) + timedelta(days=90))
        if end not in known:
            requests.append({"repository_id": snapshot["repository_id"], "cutoff": end,
                             "label": "endpoint90_" + digest([snapshot["repository_id"], end])[:24],
                             "commit": repo.resolve(source["branch"], end), "origin_cutoff": snapshot["cutoff"]})
    return requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--workspace", action="append", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--horizon", choices=("exact90", "approx91"), default="approx91")
    build.add_argument("--growth-threshold-minutes", type=float, default=30)
    build.add_argument("--strategy", choices=("auto", "build", "package"), default="auto")
    build.add_argument("--package-extra-depth", type=int, default=1)
    plan = commands.add_parser("endpoint-plan")
    plan.add_argument("--workspace", required=True)
    plan.add_argument("--output", required=True)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--dataset", required=True)
    evaluate.add_argument("--output", required=True)
    evaluate.add_argument("--first-validation-cutoff", required=True)
    evaluate.add_argument("--folds", type=int, default=1)
    evaluate.add_argument("--validation-weeks", type=int, default=8)
    evaluate.add_argument("--test-weeks", type=int, default=8)
    evaluate.add_argument("--step-weeks", type=int, default=32)
    evaluate.add_argument("--iterations", type=int, default=200)
    evaluate.add_argument("--precision-k", type=int, default=5)
    args = parser.parse_args()
    if args.command == "build":
        from .dataset import build_dataset
        config = ForecastConfig(horizon=args.horizon, growth_threshold_minutes=args.growth_threshold_minutes,
                                strategy=args.strategy, package_extra_depth=args.package_extra_depth)
        record = build_dataset([read_workspace(w) for w in args.workspace], config, args.output)
        print(f"COMPLETE: {record['data_version']} ({args.horizon}, {config.days} days)")
    elif args.command == "endpoint-plan":
        if Path(args.output).exists():
            raise ValueError("Endpoint request output already exists")
        requests = endpoint_requests(read_workspace(args.workspace))
        write_json(args.output, requests)
        print(f"Planned {len(requests)} endpoint snapshots; no scans were submitted")
    else:
        from .evaluation import EvaluationConfig, evaluate_dataset
        config = EvaluationConfig(first_validation_cutoff=args.first_validation_cutoff, folds=args.folds,
                                  validation_weeks=args.validation_weeks, test_weeks=args.test_weeks,
                                  step_weeks=args.step_weeks, iterations=args.iterations, precision_k=args.precision_k)
        record = evaluate_dataset(args.dataset, args.output, config)
        print(record["status"])
        if record["status"] != "COMPLETE":
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
