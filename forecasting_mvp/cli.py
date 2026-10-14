"""Verification, history, frozen datasets and Phase 3 statistical baseline replay."""
import argparse
import json
import sqlite3

from contracts import write_json

from .config import StudyConfig
from .io import verify_bundle
from .verification import audit_v2, environment_record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate-config", help="Phase 0 configuration validation")
    check.add_argument("--config", required=True)
    audit = commands.add_parser("audit-v2", help="Phase 0 read-only SQLite verification, no dataset construction")
    audit.add_argument("--config", required=True)
    audit.add_argument("--output", required=True)
    env = commands.add_parser("environment", help="Installed metadata only; never import or load models")
    env.add_argument("--disk-path", required=True)
    verify = commands.add_parser("verify-bundle")
    verify.add_argument("--bundle", required=True)
    ingest = commands.add_parser("ingest-history", help="Phase 1 historical measurements and ancestry audit only")
    ingest.add_argument("--config", required=True)
    ingest.add_argument("--out", required=True)
    dataset = commands.add_parser("build-forecasting-dataset", help="Phase 2 exact targets/splits; no models")
    dataset.add_argument("--config", required=True)
    dataset.add_argument("--out", required=True)
    harden = commands.add_parser("validate-frozen-dataset", help="Phase 2.1 read-only data/SQL hardening; no models")
    harden.add_argument("--bundle", required=True)
    harden.add_argument("--source-db", required=True)
    harden.add_argument("--out", required=True)
    harden.add_argument("--study-id", default="phase-2-v2-calendar-v1")
    baseline = commands.add_parser("run-baselines", help="Phase 3 statistical forecasts/evaluation only; no pretrained models")
    baseline.add_argument("--bundle", required=True)
    baseline.add_argument("--history-bundle", required=True)
    baseline.add_argument("--hardening-bundle", required=True)
    baseline.add_argument("--out", required=True)
    prepare = commands.add_parser("prepare-chronos-smoke", help="Freeze six train/validation-only smoke contexts; no model")
    prepare.add_argument("--bundle", required=True)
    prepare.add_argument("--history-bundle", required=True)
    prepare.add_argument("--baseline-bundle", required=True)
    prepare.add_argument("--registration", default="forecasting_mvp/study.phase0.json")
    prepare.add_argument("--out", required=True)
    smoke = commands.add_parser("chronos-smoke", help="Bounded CPU smoke only; no test-cohort benchmark")
    smoke.add_argument("--requests-bundle", required=True)
    smoke.add_argument("--checkpoint", required=True)
    smoke.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-config":
            config = StudyConfig.load(args.config)
            record = {"status": "PASS", "phase": 0, "config_id": config.config_id}
        elif args.command == "audit-v2":
            from pathlib import Path
            config = StudyConfig.load(args.config)
            output = Path(args.output).resolve()
            if output.exists() or output == Path(config.dataset_path).resolve():
                raise ValueError("New output file required")
            if not output.is_relative_to(Path(config.output_root).resolve()):
                raise ValueError("Audit output must be inside registered output root")
            record = audit_v2(config.dataset_path)
            write_json(output, record)
        elif args.command == "ingest-history":
            from .v2_import import HistoryConfig, ingest_history
            record = ingest_history(HistoryConfig.load(args.config), args.out)
        elif args.command == "build-forecasting-dataset":
            from .dataset import DatasetConfig, construct_dataset
            record = construct_dataset(DatasetConfig.load(args.config), args.out)
        elif args.command == "validate-frozen-dataset":
            from .hardening import audit_dataset
            result = audit_dataset(args.bundle, args.source_db, args.out, study_id=args.study_id)
            record = {k: v for k, v in result.items() if k not in ("raw_sql_checks", "raw_sql_queries", "frozen_artifact_hashes")}
        elif args.command == "environment":
            record = environment_record(args.disk_path)
        elif args.command == "run-baselines":
            from .baseline_run import run_baselines
            record = run_baselines(args.bundle, args.history_bundle, args.hardening_bundle, args.out)
        elif args.command == "prepare-chronos-smoke":
            from .chronos_smoke import prepare_smoke
            record = prepare_smoke(args.bundle,args.history_bundle,args.baseline_bundle,args.registration,args.out)
        elif args.command == "chronos-smoke":
            from .chronos_smoke import run_smoke
            record = run_smoke(args.requests_bundle,args.checkpoint,args.out)
        else:
            record = verify_bundle(args.bundle)
    except (ValueError, OSError, TypeError, KeyError, sqlite3.Error) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}))
        return 3
    print(json.dumps(record, indent=2, allow_nan=False))
    return 0 if record.get("status", "PASS") == "PASS" or record.get("status") == "COMPLETE" else 2
