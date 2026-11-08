"""Prepare six metadata-selected train/validation contexts; supervised bounded smoke."""
import gzip
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from contracts import digest, read_csv, read_json, write_json
from .baseline_run import historical_measurement_times, plan_requests
from .chronos_adapter import MODEL_ID, REVISION, verify_checkpoint
from .config import StudyConfig
from .io import file_sha256, publish_manifest, verify_bundle
from .prediction_input import admit_prediction_input

TIMEOUT_SECONDS = 900
MAX_RSS_BYTES = 2 * 1024**3
PATTERNS = ("constant", "increasing", "decreasing")
PHASES = ("train", "validation")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def prepare_smoke(bundle, history_bundle, baseline_bundle, registration, output):
    bundle, history, baselines, output = map(lambda p: Path(p).resolve(), (bundle, history_bundle, baseline_bundle, output))
    require(not output.exists() and all(not output.is_relative_to(p) and not p.is_relative_to(output)
            for p in (bundle, history, baselines)), "New output separate from frozen inputs required")
    registered = StudyConfig.load(registration)
    candidate = next(m for m in registered.models if m.name == "chronos-small")
    require(candidate.model_id == MODEL_ID and candidate.revision == REVISION and candidate.license == "Apache-2.0"
            and registered.smoke_timeout_seconds == TIMEOUT_SECONDS, "Registered checkpoint/budget mismatch")
    manifests = {name: verify_bundle(path) for name, path in (("phase1",history),("phase2",bundle),("phase3",baselines))}
    require([manifests[p]["metadata"]["phase"] for p in ("phase1","phase2","phase3")] == [1,2,3], "Phase 1/2/3 inputs required")
    require(len({m["metadata"]["source_sha256"] for m in manifests.values()}) == 1, "Mixed source domains")
    splits = read_json(bundle / "forecasting_splits.json")
    baseline_study = read_json(baselines / "study.json")
    require(baseline_study["frozen_split_id"] == splits["split_id"]
            and baseline_study["frozen_input_hashes"] == manifests["phase2"]["artifacts"], "Baselines do not bind frozen study")
    requests = plan_requests(bundle / "forecasting_features.csv", splits)
    _, features = read_csv(bundle / "forecasting_features.csv", key="context_id")
    chosen = {}
    for feature in features:
        cid = feature["context_id"]
        if cid not in requests or set(requests[cid]) != {30,60,90}:
            continue
        phases = {r["evaluation_phase"] for r in requests[cid].values()}
        if len(phases) != 1 or not phases <= set(PHASES):
            continue
        phase = next(iter(phases))
        slope, std = float(feature["slope90"]), float(feature["std90"])
        pattern = "constant" if std == 0 else "increasing" if slope > 0 else "decreasing" if slope < 0 else None
        if pattern is None:
            continue
        # Constant: least scan reuse diversity; moving contexts: most measured scans.
        count = int(feature["distinct_observation_ids"])
        rank = (count if pattern == "constant" else -count, cid)
        key = phase, pattern
        if key not in chosen or rank < chosen[key][0]:
            chosen[key] = rank, cid
    require(set(chosen) == {(p,k) for p in PHASES for k in PATTERNS}, "Six predefined context-pattern cells not available")
    selected_ids = {v[1] for v in chosen.values()}
    require(len(selected_ids) == 6, "Distinct predefined smoke contexts required")
    contexts = {}
    with gzip.open(bundle / "forecasting_contexts.jsonl.gz", "rt", encoding="utf-8") as stream:
        for line in stream:
            context = json.loads(line)
            if context["context_id"] in selected_ids:
                require(context["context_id"] not in contexts, "Duplicate smoke context")
                contexts[context["context_id"]] = context
    require(set(contexts) == selected_ids, "Missing predefined contexts")
    times = historical_measurement_times(history / "historical_debt.csv")
    records = []
    for (phase, pattern), (_, cid) in sorted(chosen.items()):
        context = contexts[cid]
        past_times = {ref: times[ref] for ref in set(context["observation_ids"])}
        admit_prediction_input(context, 90, expected_origin_utc=requests[cid][90]["origin_utc"], measurement_times=past_times)
        require(context["repository_id"] not in splits["held_repository_ids"], "Held repository forbidden in smoke")
        records.append({"sample_id": digest(["phase4_1_metadata_smoke_v1",phase,pattern,cid]), "pattern": pattern,
            "evaluation_phase": phase, "context": context, "measurement_times": past_times,
            "forecasts": [requests[cid][h] for h in (30,60,90)]})
    for name, path in (("phase1",history),("phase2",bundle),("phase3",baselines)):
        require(verify_bundle(path) == manifests[name], "Frozen inputs changed during preparation")
    output.mkdir(parents=True)
    with (output / "smoke_requests.jsonl").open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, separators=(",",":"), allow_nan=False)+"\n")
    policy = {"phase": "4.1", "status": "PREDEFINED", "model_id": MODEL_ID, "revision": REVISION,
        "selection_policy": "phase_pattern_past_scan_diversity_then_context_hash_v1",
        "phases": list(PHASES), "patterns": list(PATTERNS), "contexts": 6, "endpoint_predictions": 18,
        "horizons_days": [30,60,90], "context_days": 90, "prediction_length": 90, "repeats_per_context": 2,
        "seed": 42, "cpu_threads": 2, "cpu_interop_threads": 1, "dtype": "float32", "cross_learning": False,
        "timeout_seconds": TIMEOUT_SECONDS, "max_rss_bytes": MAX_RSS_BYTES, "labels_opened": False,
        "test_ids_selected": 0, "source_sha256": manifests["phase2"]["metadata"]["source_sha256"],
        "frozen_split_id": splits["split_id"], "held_repository_ids": splits["held_repository_ids"],
        "input_manifests": manifests,
        "samples": [{"sample_id":r["sample_id"],"pattern":r["pattern"],"evaluation_phase":r["evaluation_phase"],
                     "context_id":r["context"]["context_id"],"repository_id":r["context"]["repository_id"],
                     "origin_utc":r["context"]["origin_utc"],"distinct_context_measurements":r["context"]["distinct_observation_ids"],
                     "forecast_ids":[v["forecast_id"] for v in r["forecasts"]]} for r in records]}
    write_json(output / "smoke_policy.json", policy)
    publish_manifest(output,["smoke_requests.jsonl","smoke_policy.json"],
                     {"phase":"4.1","stage":"predefined_train_validation_inputs","source_sha256":policy["source_sha256"]})
    return {"status":"PASS","contexts":6,"endpoint_predictions":18,"labels_opened":False,"test_ids_selected":0}


def supervise(command, output, *, timeout=TIMEOUT_SECONDS, max_rss_bytes=MAX_RSS_BYTES):
    """Fixed worker process group, external wall-clock/RSS guard, no shell."""
    start, peak, failure = time.monotonic(), 0, None
    environment = {**os.environ, "CUDA_VISIBLE_DEVICES":"", "HF_HUB_OFFLINE":"1", "TRANSFORMERS_OFFLINE":"1",
                   "OMP_NUM_THREADS":"2", "MKL_NUM_THREADS":"2", "OPENBLAS_NUM_THREADS":"2", "PYTHONDONTWRITEBYTECODE":"1"}
    with (output / "worker.log").open("w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=log, env=environment, start_new_session=True)
        while process.poll() is None:
            try:
                status = Path(f"/proc/{process.pid}/status").read_text()
                rss = next(int(line.split()[1])*1024 for line in status.splitlines() if line.startswith("VmRSS:"))
                peak = max(peak,rss)
            except (OSError, StopIteration):
                pass
            if time.monotonic()-start > timeout:
                failure = "SMOKE_TIMEOUT"
            elif peak > max_rss_bytes:
                failure = "SMOKE_MEMORY_LIMIT"
            if failure:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                break
            time.sleep(.1)
        exit_code = process.wait()
    return {"status":"PASS" if exit_code == 0 and failure is None else "BLOCKED",
            "failure":failure or ("WORKER_FAILED" if exit_code else None), "worker_exit_code":exit_code,
            "elapsed_seconds":time.monotonic()-start,"observed_peak_rss_bytes":peak,
            "timeout_seconds":timeout,"max_rss_bytes":max_rss_bytes}


def run_smoke(request_bundle, checkpoint, output):
    request_bundle, checkpoint, output = map(lambda p:Path(p).resolve(),(request_bundle,checkpoint,output))
    require(not output.exists() and all(not output.is_relative_to(p) and not p.is_relative_to(output)
            for p in (request_bundle,checkpoint)), "New smoke output separate from inputs/checkpoint required")
    manifest = verify_bundle(request_bundle)
    policy = read_json(request_bundle / "smoke_policy.json")
    require(policy["phase"] == "4.1" and policy["contexts"] == 6 and policy["phases"] == list(PHASES)
            and policy["timeout_seconds"] == TIMEOUT_SECONDS and policy["max_rss_bytes"] == MAX_RSS_BYTES
            and policy["test_ids_selected"] == 0, "Only bounded predefined train/validation smoke admitted")
    admission = verify_checkpoint(checkpoint)
    output.mkdir(parents=True)
    command = [sys.executable,"-m","forecasting_mvp.chronos_smoke_worker","--requests",str(request_bundle),
               "--checkpoint",str(checkpoint),"--out",str(output)]
    resource = supervise(command,output)
    write_json(output / "smoke_resources.json",resource)
    require(resource["status"] == "PASS", "Bounded smoke failed; inspect smoke_resources.json and worker.log")
    worker = verify_bundle(output / "results")
    require(verify_bundle(request_bundle) == manifest and verify_checkpoint(checkpoint) == admission,
            "Smoke inputs/checkpoint changed")
    publish_manifest(output,["smoke_resources.json","worker.log", "results/manifest.json", *["results/"+p for p in worker["artifacts"]]],
        {"phase":"4.1","status":"PASS","stage":"runtime_smoke_only","source_sha256":policy["source_sha256"],
         "full_benchmark_run":False,"test_labels_opened":False})
    return {"status":"PASS","contexts":6,"endpoint_predictions":18,"full_benchmark_run":False,
            "test_labels_opened":False,"resources":resource}
