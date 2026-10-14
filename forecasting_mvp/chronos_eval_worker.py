"""Offline Phase 4.2 label-free worker. Receives only frozen past requests."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import resource
import time

from contracts import digest, read_json, write_csv, write_json
from .baseline_run import PREDICTION_FIELDS
from .chronos_adapter import ChronosSmallAdapter, verify_checkpoint
from .chronos_smoke_worker import PINNED_RUNTIME, validate_runtime_versions
from .contracts import TargetContract
from .io import file_sha256, publish_manifest, verify_bundle
from .prediction_input import admit_prediction_input

EXTRA_FIELDS = ("inference_status","error_type","error","raw_q10","raw_q90","q10","q90","maximum_repeat_difference")
FIELDS = (*PREDICTION_FIELDS,*EXTRA_FIELDS)


def require(condition,message):
    if not condition:
        raise ValueError(message)


def admitted_records(records,policy):
    require(policy["phase"]=="4.2" and policy["stage"] in ("pilot","validation","test"),"Registered Phase 4.2 stage required")
    phases = {"validation"} if policy["stage"] != "test" else {"test_temporal","test_repository"}
    ids,contexts = set(),set()
    admitted=[]
    for record in records:
        require(set(record)=={"context","measurement_times","forecasts"},"Only past context/reference/routing fields admitted")
        context=record["context"];cid=context["context_id"]
        require(cid not in contexts,"Duplicate inference context");contexts.add(cid)
        forecasts=record["forecasts"]
        require(len(forecasts)==3 and [r["horizon_days"] for r in forecasts]==[30,60,90],"Exact three registered horizons required")
        require(len({r["evaluation_phase"] for r in forecasts})==1,"Mixed prediction phases")
        for row in forecasts:
            require(set(row)=={"forecast_id","context_id","repository_id","track","origin_utc","horizon_days","endpoint_utc","evaluation_phase"},"Future/label field forbidden")
            target=TargetContract(row["horizon_days"],context_policy="core90_90_days")
            require(row["evaluation_phase"] in phases and row["forecast_id"] not in ids
                and row["context_id"]==cid and row["repository_id"]==context["repository_id"]
                and row["origin_utc"]==context["origin_utc"] and row["track"]=="core90"
                and row["endpoint_utc"]==target.endpoint(row["origin_utc"])
                and row["forecast_id"]==digest([cid,target.target_id]),"Unregistered forecast identity/phase")
            held=row["repository_id"] in policy["held_repository_ids"]
            require(held == (row["evaluation_phase"]=="test_repository"),"Repository holdout violation")
            ids.add(row["forecast_id"])
        request=admit_prediction_input(context,90,expected_origin_utc=forecasts[-1]["origin_utc"],measurement_times=record["measurement_times"])
        admitted.append((record,request))
    require(len(records)==policy["contexts"] and sorted(ids)==policy["forecast_ids"],"Incomplete fixed inference cohort")
    return admitted


def infer_records(admitted,adapter,repeat):
    predictions=[];failures=[];timings=[]
    for record,request in admitted:
        context=record["context"];start=time.monotonic()
        status,error_type,error="SUCCESS","",""
        path=None;difference=None
        try:
            path=adapter.predict_path(request)
            if repeat:
                again=adapter.predict_path(request)
        except Exception as exc:
            status,error_type,error="PERSISTENCE_FALLBACK",type(exc).__name__,str(exc)
            path=None
            failures.append({"context_id":request.context_id,"error_type":error_type,"error":error})
        if path is not None and repeat:
            # A valid but different repeat is a pilot gate failure, never a
            # recoverable native-path error hidden behind persistence fallback.
            require(path==again,"Deterministic pilot repeat mismatch")
            difference=0.0
        timings.append(time.monotonic()-start)
        for metadata in record["forecasts"]:
            endpoint=path[metadata["horizon_days"]-1] if path is not None else None
            if endpoint is not None:
                require(endpoint["timestamp"]==metadata["endpoint_utc"],"Exact native endpoint mismatch")
            predictions.append({**metadata,"model":"chronos_small","window_days":0,
                "raw_prediction_minutes":endpoint["raw_q50"] if endpoint else request.values[-1],
                "prediction_minutes":endpoint["q50"] if endpoint else request.values[-1],
                "current_minutes":request.values[-1],"origin_observation_id":context["observation_ids"][-1],
                "distinct_context_measurements":context["distinct_observation_ids"],"distinct_context_values":len(set(request.values)),
                "context_values_digest":digest(list(request.values)),"inference_status":status,"error_type":error_type,"error":error,
                **{k:endpoint[k] if endpoint else None for k in ("raw_q10","raw_q90","q10","q90")},
                "maximum_repeat_difference":difference})
    return sorted(predictions,key=lambda r:r["forecast_id"]),failures,timings


def execute(request_root,checkpoint,output):
    request_root,checkpoint,output=map(lambda p:Path(p).resolve(),(request_root,checkpoint,output))
    started=time.monotonic();manifest=verify_bundle(request_root);policy=read_json(request_root/"policy.json")
    admission=verify_checkpoint(checkpoint)
    validate_runtime_versions({p:importlib.metadata.version(p) for p in PINNED_RUNTIME})
    with (request_root/"requests.jsonl").open() as stream:records=[json.loads(line) for line in stream]
    admitted=admitted_records(records,policy)
    code={p.name:file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
    load=time.monotonic();adapter=ChronosSmallAdapter.load_cpu(checkpoint);load_time=time.monotonic()-load
    predictions,failures,timings=infer_records(admitted,adapter,policy["stage"]=="pilot")
    require(verify_bundle(request_root)==manifest and verify_checkpoint(checkpoint)==admission,"Worker input changed")
    require(code=={p.name:file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},"Worker code changed")
    output.mkdir(exist_ok=False)
    write_csv(output/"predictions.csv",predictions,FIELDS)
    summary={"status":"PASS" if not failures else "PARTIAL","phase":"4.2","stage":policy["stage"],"contexts":len(admitted),
        "prediction_rows":len(predictions),"failures":failures,"failed_contexts":len(failures),
        "successful_contexts":len(admitted)-len(failures),"labels_opened":False,"model_load_seconds":load_time,
        "worker_elapsed_seconds":time.monotonic()-started,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "context_inference_seconds_sum":sum(timings),"context_inference_seconds_min":min(timings),"context_inference_seconds_max":max(timings),
        "runtime_versions":PINNED_RUNTIME,"checkpoint":admission,"implementation_sha256":code,
        "request_manifest_sha256":file_sha256(request_root/"manifest.json"),"pilot_repeats_equal":
            all(r["maximum_repeat_difference"]==0.0 for r in predictions if r["inference_status"]=="SUCCESS") if policy["stage"]=="pilot" else None}
    write_json(output/"worker_summary.json",summary)
    publish_manifest(output,["predictions.csv","worker_summary.json"],{"phase":"4.2","stage":policy["stage"],"status":summary["status"],
                     "source_sha256":policy["source_sha256"],"labels_opened":False})
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("requests","checkpoint","out"):parser.add_argument("--"+key,required=True)
    args=parser.parse_args()
    try:
        result=execute(args.requests,args.checkpoint,args.out)
        print(json.dumps({k:v for k,v in result.items() if k not in ("implementation_sha256","checkpoint")},indent=2));return 0
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","error_type":type(exc).__name__,"error":str(exc)}));return 3


if __name__=="__main__":raise SystemExit(main())
