"""Phase 4.2 validation-first, sealed-test Chronos experiment orchestration."""
from collections import Counter,defaultdict
import gzip
import json
from pathlib import Path

from contracts import digest,read_csv,read_json,write_csv,write_json
from .baseline_evaluation import METRIC_FIELDS
from .baseline_run import PREDICTION_FIELDS,plan_requests,historical_measurement_times,label_view
from .chronos_adapter import MODEL_ID,REVISION,verify_checkpoint
from .chronos_evaluation import CHRONOS,INTERVAL_FIELDS,compare_points,interval_metrics,select_validation_policy,plot_results
from .chronos_eval_worker import FIELDS
from .chronos_smoke import supervise
from .io import file_sha256,verify_bundle,publish_manifest


def require(condition,message):
    if not condition:raise ValueError(message)


def read_predictions(path,chronos=False):
    header,rows=read_csv(path,key="forecast_id" if chronos else ("forecast_id","model"))
    require(tuple(header)==(FIELDS if chronos else PREDICTION_FIELDS),"Prediction schema mismatch")
    for row in rows:
        for key in ("horizon_days","window_days","distinct_context_measurements","distinct_context_values"):row[key]=int(row[key])
        for key in ("raw_prediction_minutes","prediction_minutes","current_minutes"):
            row[key]=float(row[key])
        if chronos:
            for key in ("raw_q10","raw_q90","q10","q90","maximum_repeat_difference"):
                row[key]=float(row[key]) if row[key]!="" else None
    return rows


def prepare_requests(bundle,history,splits,root):
    planned=plan_requests(bundle/"forecasting_features.csv",splits)
    wanted={cid:r for cid,r in planned.items() if {v["evaluation_phase"] for v in r.values()} in
            ({"validation"},{"test_temporal"},{"test_repository"})}
    times=historical_measurement_times(history/"historical_debt.csv")
    records=[]
    with gzip.open(bundle/"forecasting_contexts.jsonl.gz","rt",encoding="utf-8") as stream:
        for line in stream:
            context=json.loads(line);cid=context["context_id"]
            if cid in wanted:
                records.append({"context":context,"measurement_times":{ref:times[ref] for ref in set(context["observation_ids"])},
                                "forecasts":[wanted[cid][h] for h in (30,60,90)]})
    require(len(records)==len(wanted),"Missing inference contexts")
    validation=[r for r in records if r["forecasts"][0]["evaluation_phase"]=="validation"]
    # Fixed 12-context pilot: smallest hashes in past constant/positive/negative cells,
    # then hash fill. No labels, model output or test contexts influence this selection.
    cells=defaultdict(list)
    for r in validation:
        values=r["context"]["values"];delta=values[-1]-values[0]
        pattern="constant" if len(set(values))==1 else "increasing" if delta>0 else "decreasing" if delta<0 else "other"
        cells[pattern].append(r)
    pilot={}
    for rows in cells.values():
        for r in sorted(rows,key=lambda r:r["context"]["context_id"])[:3]:pilot[r["context"]["context_id"]]=r
    for r in sorted(validation,key=lambda r:r["context"]["context_id"]):
        if len(pilot)>=12:break
        pilot[r["context"]["context_id"]]=r
    require(len(pilot)==12,"Twelve-context validation pilot required")
    groups={"pilot":list(pilot.values()),"validation":validation,
            "test":[r for r in records if r["forecasts"][0]["evaluation_phase"].startswith("test_")]}
    for stage,rows in groups.items():
        rows.sort(key=lambda r:r["context"]["context_id"])
        target=root/stage;target.mkdir(parents=True)
        with (target/"requests.jsonl").open("w") as stream:
            for row in rows:stream.write(json.dumps(row,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n")
        policy={"phase":"4.2","stage":stage,"contexts":len(rows),"forecast_ids":sorted(f["forecast_id"] for r in rows for f in r["forecasts"]),
                "held_repository_ids":splits["held_repository_ids"],"source_sha256":verify_bundle(bundle)["metadata"]["source_sha256"]}
        write_json(target/"policy.json",policy)
        publish_manifest(target,["requests.jsonl","policy.json"],{"phase":"4.2","stage":stage,"source_sha256":policy["source_sha256"]})
    return {stage:len(rows) for stage,rows in groups.items()}


def run_worker(runtime,requests,checkpoint,output,timeout):
    output.mkdir()
    resources=supervise([str(runtime),"-m","forecasting_mvp.chronos_eval_worker","--requests",str(requests),
                        "--checkpoint",str(checkpoint),"--out",str(output/"results")],output,timeout=timeout,max_rss_bytes=2*1024**3)
    write_json(output/"resources.json",resources)
    require(resources["status"]=="PASS","Chronos worker resource/execution failure; inspect worker.log")
    verify_bundle(output/"results")
    return read_json(output/"results/worker_summary.json")


def seal(root,stage):
    result=root/stage/"results"
    record={"status":"SEALED","stage":stage,"prediction_sha256":file_sha256(result/"predictions.csv"),
            "worker_manifest_sha256":file_sha256(result/"manifest.json"),"numerical_labels_loaded":False,
            "selection_sha256":file_sha256(root/"selection.json") if stage=="test" else None}
    write_json(root/(stage+"_prediction_seal.json"),record)
    return record


def check_seal(root,stage,expected):
    record=read_json(root/(stage+"_prediction_seal.json"))
    require(record==expected,"Prediction seal record changed")
    verify_bundle(root/stage/"results")
    require(file_sha256(root/stage/"results/predictions.csv")==record["prediction_sha256"]
            and file_sha256(root/stage/"results/manifest.json")==record["worker_manifest_sha256"],"Sealed predictions changed")
    if stage=="test":require(file_sha256(root/"selection.json")==record["selection_sha256"],"Frozen validation selection changed")


def run_chronos(bundle,history_bundle,baseline_bundle,smoke_bundle,runtime_python,checkpoint,output):
    bundle,history,baseline,smoke,runtime,checkpoint,output=map(lambda p:Path(p).absolute(),
        (bundle,history_bundle,baseline_bundle,smoke_bundle,runtime_python,checkpoint,output))
    require(not output.exists() and all(not output.is_relative_to(p) and not p.is_relative_to(output)
            for p in (bundle,history,baseline,smoke,checkpoint)),"New output separate from inputs required")
    manifests={name:verify_bundle(path) for name,path in (("phase1",history),("phase2",bundle),("phase3",baseline),("phase4_1",smoke))}
    require([manifests[n]["metadata"]["phase"] for n in manifests]==[1,2,3,"4.1"],"Registered phase bundles required")
    require(len({m["metadata"]["source_sha256"] for m in manifests.values()})==1,"Mixed data sources")
    admission=verify_checkpoint(checkpoint)
    splits=read_json(bundle/"forecasting_splits.json");base_study=read_json(baseline/"study.json")
    require(base_study["frozen_split_id"]==splits["split_id"] and base_study["frozen_input_hashes"]==manifests["phase2"]["artifacts"],"Baseline frozen cohort mismatch")
    require(read_json(smoke/"results/chronos_smoke_summary.json")["revision"]==REVISION,"Smoke checkpoint mismatch")
    require(runtime.is_file(),"Existing isolated runtime executable required")
    code={p.name:file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
    output.mkdir(parents=True)
    study={"phase":"4.2","model_id":MODEL_ID,"revision":REVISION,"checkpoint":admission,"primary_track":"core90",
        "input_manifests":manifests,"split_id":splits["split_id"],"implementation_sha256":code,
        "inference":{"prediction_length":90,"context_length":90,"quantiles":[.1,.5,.9],"point":"q50","device":"cpu",
                     "dtype":"float32","cross_learning":False,"batch_size":1,"threads":2,"interop_threads":1,"seed":42,
                     "clipping":"max_zero_save_raw","fine_tune":False},
        "pilot_policy":"12_validation_contexts_past_pattern_then_hash_repeat_twice",
        "selection":"validation_macro_MAE_within_1percent_prefer_persistence_mean_trend_chronos",
        "failure_policy":"persistence_fallback_record_status_and_success_matched_intervals_never_fabricated",
        "native_interval_policy":"no_calibration_no_rescaling_no_quantile_tuning",
        "resources":{"pilot_seconds":900,"validation_seconds":1800,"test_seconds":1800,"max_worker_rss_bytes":2*1024**3},
        "bootstrap":{"paired_repository_repetitions":2000,"seed":42,"percentile_confidence":.95},
        "constant_interval_checks":{"collapsed":"q90_equals_q10","near_collapsed":"width_le_1e-6_times_max_1_current_stock"}}
    study_id=digest(study);write_json(output/"study.json",{"study_id":study_id,**study})
    events=["study_registered_before_any_Chronos_outcomes"]
    counts=prepare_requests(bundle,history,splits,output/"requests")
    summaries={}
    print("Phase 4.2: bounded validation pilot",flush=True)
    summaries["pilot"]=run_worker(runtime,output/"requests/pilot",checkpoint,output/"pilot",900)
    require(summaries["pilot"]["successful_contexts"]>0 and summaries["pilot"]["pilot_repeats_equal"],
            "No valid deterministic native pilot inference; stop before full inference")
    events.append("validation_pilot_passed_without_labels")
    print("Phase 4.2: complete validation inference",flush=True)
    summaries["validation"]=run_worker(runtime,output/"requests/validation",checkpoint,output/"validation",1800)
    valseal=seal(output,"validation");events.append("complete_validation_predictions_sealed")
    val=read_predictions(output/"validation/results/predictions.csv",True)
    val_labels=label_view(bundle/"forecasting_labels.csv",{r["forecast_id"] for r in val},verify_seal=lambda:check_seal(output,"validation",valseal))
    require(all(r["evaluation_phase"]=="validation" for r in val_labels.values()),"Validation-only label view required")
    events.append("validation_only_labels_loaded")
    controls=read_predictions(baseline/"baseline_predictions.csv")
    vm,vs=compare_points(val,controls,val_labels)
    selection=select_validation_policy(vm,val);selection["study_id"]=study_id;selection["frozen_inference"]=study["inference"]
    write_json(output/"selection.json",selection);events.append("inference_and_selection_frozen_on_validation_only")
    print("Phase 4.2: frozen temporal and held-repository inference",flush=True)
    summaries["test"]=run_worker(runtime,output/"requests/test",checkpoint,output/"test",1800)
    testseal=seal(output,"test");events.append("all_temporal_and_held_test_predictions_sealed_before_test_labels")
    test=read_predictions(output/"test/results/predictions.csv",True)
    for phase in ("test_temporal","test_repository"):
        require(digest(sorted(r["forecast_id"] for r in test if r["evaluation_phase"]==phase))==
                read_json(baseline/"prediction_seal.json")["forecast_id_digests"][phase],"Frozen test IDs changed")
    labels=label_view(bundle/"forecasting_labels.csv",{r["forecast_id"] for r in test},verify_seal=lambda:check_seal(output,"test",testseal))
    events.append("test_numerical_labels_loaded_after_seal")
    tm,ts=compare_points(test,controls,labels)
    metrics=vm+tm;success_metrics=vs+ts
    intervals=interval_metrics(val+test,{**val_labels,**labels})
    write_csv(output/"chronos_comparison_metrics.csv",metrics,METRIC_FIELDS)
    write_csv(output/"chronos_success_matched_metrics.csv",success_metrics,METRIC_FIELDS)
    write_csv(output/"chronos_interval_metrics.csv",intervals,INTERVAL_FIELDS)
    # Original baselines are reused, never regenerated, and their original metric rows must match.
    _,old_metrics=read_csv(baseline/"baseline_metrics.csv")
    old={(r["evaluation_phase"],int(r["horizon_days"]),r["subset"],r["repository_id"],r["model"]):r for r in old_metrics}
    for row in metrics:
        if row["model"]==CHRONOS:continue
        prior=old[row["evaluation_phase"],row["horizon_days"],row["subset"],row["repository_id"],row["model"]]
        require(all((str(value) if value is not None else "")==prior[key] for key,value in row.items()),"Original baseline metric changed")
    plot_results(metrics,intervals,output/"chronos_comparison.png")
    all_predictions=val+test
    write_csv(output/"chronos_predictions.csv",sorted(all_predictions,key=lambda r:r["forecast_id"]),FIELDS)
    sample=[]
    for phase in ("validation","test_temporal","test_repository"):
        for h in (30,60,90):sample.extend(sorted([r for r in all_predictions if r["evaluation_phase"]==phase and r["horizon_days"]==h],key=lambda r:r["forecast_id"])[:5])
    write_csv(output/"chronos_predictions_sample.csv",sample,FIELDS)
    check_seal(output,"validation",valseal);check_seal(output,"test",testseal)
    require(all(verify_bundle(path)==manifests[name] for name,path in (("phase1",history),("phase2",bundle),("phase3",baseline),("phase4_1",smoke))),"Frozen input modified")
    require(verify_checkpoint(checkpoint)==admission and code=={p.name:file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},"Checkpoint/code modified")
    failures=sum(summaries[p]["failed_contexts"] for p in ("validation","test"))
    audit={"status":"PASS" if not failures else "PARTIAL","phase":"4.2","study_id":study_id,"events":events,"contexts":counts,
        "prediction_rows":len(all_predictions),"failed_contexts":failures,"worker_summaries":summaries,
        "frozen_inputs_unchanged":True,"original_baseline_metrics_identical":True,"test_ids_unchanged":True,
        "no_fine_tuning":True,"no_test_informed_tuning":True,"metric_rows":len(metrics),"interval_rows":len(intervals)}
    write_json(output/"run_audit.json",audit)
    artifacts=[str(p.relative_to(output)) for p in sorted(output.rglob("*")) if p.is_file()]
    publish_manifest(output,artifacts,{"phase":"4.2","status":audit["status"],"study_id":study_id,"source_sha256":manifests["phase2"]["metadata"]["source_sha256"]})
    return {k:v for k,v in audit.items() if k!="worker_summaries"}
