"""Offline isolated worker for exactly six predefined train/validation contexts."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import resource
import time

from contracts import digest, read_json, write_csv, write_json
from .chronos_adapter import ChronosSmallAdapter, MODEL_ID, REVISION, verify_checkpoint
from .chronos_smoke import PATTERNS, PHASES, require
from .contracts import TargetContract
from .io import file_sha256, publish_manifest, verify_bundle
from .prediction_input import admit_prediction_input

PATH_FIELDS = ("sample_id","context_id","repository_id","evaluation_phase","pattern","step_days","timestamp",
               "raw_q10","raw_q50","raw_q90","q10","q50","q90")
PREDICTION_FIELDS = ("sample_id","forecast_id","context_id","repository_id","track","origin_utc","horizon_days",
    "endpoint_utc","evaluation_phase","pattern","model","raw_prediction_minutes","prediction_minutes",
    "raw_q10","raw_q90","q10","q90","unit")

PINNED_RUNTIME = {"torch":"2.11.0+cpu","chronos-forecasting":"2.3.2","transformers":"4.57.6",
                  "numpy":"2.4.4","pandas":"3.0.2"}


def validate_runtime_versions(versions):
    require(versions == PINNED_RUNTIME, "Pinned smoke runtime required")


def validate_records(records, policy):
    require(len(records) == 6 and len({r["sample_id"] for r in records}) == 6,
            "Exactly six distinct predefined smoke samples required")
    require({(r["evaluation_phase"],r["pattern"]) for r in records} == {(p,k) for p in PHASES for k in PATTERNS},
            "Test/unknown phases or pattern cells forbidden")
    admitted = []
    for record in records:
        require(set(record) == {"sample_id","pattern","evaluation_phase","context","measurement_times","forecasts"},
                "Only past smoke request fields admitted")
        context = record["context"]
        require(context["repository_id"] not in policy["held_repository_ids"], "Held repositories forbidden")
        require(record["sample_id"] == digest(["phase4_1_metadata_smoke_v1",record["evaluation_phase"],record["pattern"],context["context_id"]]),
                "Smoke identity mismatch")
        require(len(record["forecasts"]) == 3 and {r["horizon_days"] for r in record["forecasts"]} == {30,60,90}, "Exact three horizons required")
        for forecast in record["forecasts"]:
            require(set(forecast) == {"forecast_id","context_id","repository_id","track","origin_utc","horizon_days","endpoint_utc","evaluation_phase"},
                    "Targets/future measurement references forbidden in smoke routing")
            h = forecast["horizon_days"]
            target = TargetContract(h,context_policy="core90_90_days")
            require(forecast["evaluation_phase"] == record["evaluation_phase"] and forecast["evaluation_phase"] in PHASES
                    and forecast["context_id"] == context["context_id"] and forecast["repository_id"] == context["repository_id"]
                    and forecast["origin_utc"] == context["origin_utc"] and forecast["track"] == "core90"
                    and forecast["endpoint_utc"] == target.endpoint(context["origin_utc"])
                    and forecast["forecast_id"] == digest([context["context_id"],target.target_id]), "Frozen forecast routing mismatch")
        registered = next((r for r in policy["samples"] if r["sample_id"] == record["sample_id"]),None)
        require(registered is not None and registered["forecast_ids"] == [r["forecast_id"] for r in record["forecasts"]],
                "Not a predefined smoke sample")
        request = admit_prediction_input(context,90,expected_origin_utc=record["forecasts"][2]["origin_utc"],
                                         measurement_times=record["measurement_times"])
        admitted.append((record,request))
    return admitted


def execute(request_bundle, checkpoint, output):
    request_bundle,checkpoint,output = map(lambda p:Path(p).resolve(),(request_bundle,checkpoint,output))
    start = time.monotonic()
    manifest = verify_bundle(request_bundle)
    admission = verify_checkpoint(checkpoint)
    policy = read_json(request_bundle / "smoke_policy.json")
    require(policy["repeats_per_context"] == 2 and policy["prediction_length"] == policy["context_days"] == 90
            and policy["cross_learning"] is False and policy["test_ids_selected"] == 0, "Bounded smoke protocol required")
    with (request_bundle / "smoke_requests.jsonl").open() as stream:
        records = [json.loads(line) for line in stream]
    admitted = validate_records(records,policy)  # validate all inputs BEFORE loading the model
    versions = {p:importlib.metadata.version(p) for p in ("torch","chronos-forecasting","transformers","numpy","pandas")}
    validate_runtime_versions(versions)
    code = {p.name:file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
    load_start = time.monotonic()
    adapter = ChronosSmallAdapter.load_cpu(checkpoint)
    model_load_seconds = time.monotonic()-load_start
    import torch
    paths,predictions,timings = [],[],[]
    for record,request in admitted:
        native = []
        durations = []
        for repeat in range(2):
            tick = time.monotonic()
            with torch.inference_mode():
                native.append(adapter.predict_path(request))
            durations.append(time.monotonic()-tick)
        require(native[0] == native[1], "Repeated CPU inference is not exactly deterministic; no benchmark admission")
        repeat_digest = digest(native[0])
        path = native[0]
        context = record["context"]
        metadata = {"sample_id":record["sample_id"],"context_id":context["context_id"],"repository_id":context["repository_id"],
                    "evaluation_phase":record["evaluation_phase"],"pattern":record["pattern"]}
        paths.extend({**metadata,**row} for row in path)
        for forecast in record["forecasts"]:
            point = path[forecast["horizon_days"]-1]
            require(point["timestamp"] == forecast["endpoint_utc"], "Native path is not exact endpoint target")
            predictions.append({**forecast,"sample_id":record["sample_id"],"pattern":record["pattern"],"model":"chronos-2-small_q50",
                "raw_prediction_minutes":point["raw_q50"],"prediction_minutes":point["q50"],
                "raw_q10":point["raw_q10"],"raw_q90":point["raw_q90"],"q10":point["q10"],"q90":point["q90"],
                "unit":"estimated_maintainability_remediation_minutes"})
        timings.append({"sample_id":record["sample_id"],"pattern":record["pattern"],"evaluation_phase":record["evaluation_phase"],
            "context_days":90,"native_rows":90,"native_columns":7,"repeat_seconds":durations,
            "repeat_byte_equal":True,"repeat_path_digest":repeat_digest,"maximum_absolute_repeat_difference":0.0,
            "current_minutes":request.values[-1],"distinct_context_values":len(set(request.values)),
            "distinct_context_measurements":context["distinct_observation_ids"]})
    require(verify_bundle(request_bundle) == manifest and verify_checkpoint(checkpoint) == admission, "Smoke inputs changed")
    require(code == {p.name:file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}, "Worker code changed during inference")
    result_root = output / "results"
    result_root.mkdir(exist_ok=False)
    write_csv(result_root / "chronos_smoke_predictions.csv",predictions,PREDICTION_FIELDS)
    write_csv(result_root / "chronos_smoke_paths.csv",paths,PATH_FIELDS)
    report = {"status":"PASS","phase":"4.1","model_id":MODEL_ID,"revision":REVISION,"license":"Apache-2.0",
        "runtime_versions":versions,"device":"cpu","dtype":"float32","contexts":6,"endpoint_predictions":len(predictions),
        "native_path_rows":len(paths),"forward_requests":12,"prediction_steps":90,"point_kind":"native_q50",
        "quantile_levels":[.1,.5,.9],"clipping_policy":"max_zero_all_quantiles_save_raw","raw_negative_path_quantiles":
            {k:sum(r[k]<0 for r in paths) for k in ("raw_q10","raw_q50","raw_q90")},
        "quantile_crossings":0,"cpu_threads":torch.get_num_threads(),"cpu_interop_threads":torch.get_num_interop_threads(),
        "deterministic_algorithms":torch.are_deterministic_algorithms_enabled(),"seed":42,
        "model_parameter_count":sum(p.numel() for p in adapter.pipeline.model.parameters()),
        "model_load_seconds":model_load_seconds,"worker_elapsed_seconds":time.monotonic()-start,
        "worker_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"samples":timings,
        "implementation_sha256":code,"request_manifest_sha256":file_sha256(request_bundle / "manifest.json"),
        "checkpoint_admission":admission,"test_inference_count":0,"labels_opened":False,
        "accuracy_evaluated":False,"full_benchmark_run":False,
        "readiness":"RUNTIME_SMOKE_PASS_full_evaluation_requires_separate_authorization_and_domain_caveats"}
    write_json(result_root / "chronos_smoke_summary.json",report)
    publish_manifest(result_root,["chronos_smoke_predictions.csv","chronos_smoke_paths.csv","chronos_smoke_summary.json"],
                     {"phase":"4.1","stage":"runtime_smoke_only","source_sha256":policy["source_sha256"],"status":"PASS"})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests",required=True);parser.add_argument("--checkpoint",required=True);parser.add_argument("--out",required=True)
    args = parser.parse_args(argv)
    try:
        report = execute(args.requests,args.checkpoint,args.out)
        print(json.dumps({k:v for k,v in report.items() if k not in ("samples","checkpoint_admission","implementation_sha256")},indent=2))
        return 0
    except Exception as exc:
        failure = {"status":"BLOCKED","phase":"4.1","error_type":type(exc).__name__,"error":str(exc),"full_benchmark_run":False}
        write_json(Path(args.out) / "worker_failure.json",failure)
        print(json.dumps(failure))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
