"""Phase 4.2.1: bounded 12-failure diagnostics, never benchmark replacement."""
import argparse
import importlib.metadata
import json
import math
from pathlib import Path
import resource
import sys
import time
from datetime import timedelta

from contracts import read_csv, read_json, write_csv, write_json
from .chronos_adapter import ChronosSmallAdapter, NativeQuantileCrossingError, verify_checkpoint
from .chronos_eval_worker import admitted_records
from .chronos_smoke import supervise
from .chronos_smoke_worker import PINNED_RUNTIME, validate_runtime_versions
from .contracts import utc_iso, utc_timestamp
from .io import file_sha256, publish_manifest, verify_bundle

PUBLISHED_STUDY_ID = "70b372e32c7292aca8b260b1a44c28787c3f03b7c11277159a53dd18cc22c958"
CROSSING_MESSAGE = "Native quantile crossing; do not manufacture sorted quantiles"
RAW_FIELDS = ("context_id","evaluation_phase","repository_id","repeat","step_days","timestamp",
              "raw_q10","raw_q50","raw_q90","lower_crossing_minutes","upper_crossing_minutes",
              "crossing","selected_endpoint")


def require(condition,message):
    if not condition:raise ValueError(message)


class CapturePipeline:
    """Observe native results without altering model inputs, kwargs or outputs."""
    def __init__(self,pipeline):
        self.pipeline=pipeline
        self.result=None

    def predict_df(self,*args,**kwargs):
        self.result=self.pipeline.predict_df(*args,**kwargs)
        return self.result


def raw_path_diagnostics(frame,request):
    """Analyze all raw steps without sorting, clipping or returning a forecast."""
    require(len(frame)==90 and set(frame.columns)=={"item_id","timestamp","target_name","predictions","0.1","0.5","0.9"},
            "Unexpected native diagnostic shape")
    import pandas as pd
    rows=[]
    for step,row in enumerate(frame.to_dict("records"),1):
        stamp=pd.Timestamp(row['timestamp'])
        stamp=stamp.tz_localize('UTC') if stamp.tzinfo is None else stamp.tz_convert('UTC')
        expected=utc_timestamp(request.origin_utc)+timedelta(days=step)
        require(row['item_id']=='series' and row['target_name']=='debt_minutes' and utc_timestamp(stamp)==expected,
                "Diagnostic identity/timestamp mismatch")
        low,mid,high=(float(row[k]) for k in ('0.1','0.5','0.9'))
        require(all(math.isfinite(v) for v in (low,mid,high,float(row['predictions']))),"Nonfinite diagnostic output")
        lower,upper=max(0.,low-mid),max(0.,mid-high)
        rows.append({'step_days':step,'timestamp':utc_iso(expected),'raw_q10':low,'raw_q50':mid,'raw_q90':high,
                     'lower_crossing_minutes':lower,'upper_crossing_minutes':upper,
                     'crossing':lower>0 or upper>0,'selected_endpoint':step in (30,60,90)})
    crossed=[r for r in rows if r['crossing']]
    return rows,{'crossing_steps':[r['step_days'] for r in crossed],
                 'lower_crossing_steps':[r['step_days'] for r in rows if r['lower_crossing_minutes']>0],
                 'upper_crossing_steps':[r['step_days'] for r in rows if r['upper_crossing_minutes']>0],
                 'maximum_crossing_minutes':max(max(r['lower_crossing_minutes'],r['upper_crossing_minutes']) for r in rows),
                 'selected_endpoints':[{**r,'ordered':not r['crossing']} for r in rows if r['selected_endpoint']]}


def input_characteristics(request,context):
    values=request.values;n=len(values);mean=sum(values)/n
    return {'context_days':n,'distinct_measurements':context['distinct_observation_ids'],
            'distinct_values':len(set(values)),'constant_history':len(set(values))==1,
            'first_minutes':values[0],'current_minutes':values[-1],'minimum_minutes':min(values),'maximum_minutes':max(values),
            'population_std_minutes':math.sqrt(sum((v-mean)**2 for v in values)/n),
            'past_net_change_minutes':values[-1]-values[0],
            'past_value_transitions':sum(a!=b for a,b in zip(values,values[1:])),
            'zero_value_days':sum(v==0 for v in values)}


def failed_requests(benchmark):
    manifest=verify_bundle(benchmark);study=read_json(benchmark/'study.json');audit=read_json(benchmark/'run_audit.json')
    require(manifest['metadata']['phase']=='4.2' and study['study_id']==PUBLISHED_STUDY_ID
            and audit['study_id']==PUBLISHED_STUDY_ID and audit['failed_contexts']==12,
            'Only the published 12-failure Phase 4.2 experiment is admitted')
    selected=[]
    for stage in ('validation','test'):
        failures=audit['worker_summaries'][stage]['failures']
        wanted={r['context_id'] for r in failures}
        require(len(wanted)==len(failures)==6 and all(r['error_type']=='ValueError' and r['error']==CROSSING_MESSAGE for r in failures),
                'Published failure identities/type changed')
        bundle=benchmark/'requests'/stage;verify_bundle(bundle)
        with (bundle/'requests.jsonl').open() as stream:records=[json.loads(line) for line in stream]
        admitted=admitted_records(records,read_json(bundle/'policy.json'))
        selected.extend((record,request) for record,request in admitted if request.context_id in wanted)
    require(len(selected)==12 and len({request.context_id for _,request in selected})==12,'Missing/duplicate failed contexts')
    return sorted(selected,key=lambda v:v[1].context_id),manifest,study


def published_interval_diagnostics(benchmark):
    """Descriptive arithmetic on published metrics; no new evaluation or labels."""
    _,rows=read_csv(benchmark/'chronos_interval_metrics.csv')
    selected=[r for r in rows if r['repository_id']=='ALL']
    result=[]
    for row in selected:
        successes=int(row['successes'])
        covered=float(row['pooled_coverage80'])*successes if successes else 0
        require(math.isclose(covered,round(covered),abs_tol=1e-7),'Nonintegral published coverage count')
        misses=successes-round(covered)
        result.append({**row,'pooled_misses':misses,'noncollapsed_misses':misses-int(row['collapsed_misses'])})
    return result


def diagnostic_worker(benchmark,checkpoint,output):
    benchmark,checkpoint,output=map(lambda p:Path(p).resolve(),(benchmark,checkpoint,output))
    require(not output.exists() and all(not output.is_relative_to(p) and not p.is_relative_to(output) for p in (benchmark,checkpoint)),
            'New diagnostic output separate from experiment/checkpoint required')
    started=time.monotonic();selected,manifest,study=failed_requests(benchmark)
    checkpoint_admission=verify_checkpoint(checkpoint)
    require(checkpoint_admission==study['checkpoint'],'Checkpoint identity must equal published experiment')
    versions={p:importlib.metadata.version(p) for p in PINNED_RUNTIME};validate_runtime_versions(versions)
    code={p.name:file_sha256(p) for p in Path(__file__).parent.glob('*.py')}
    adapter=ChronosSmallAdapter.load_cpu(checkpoint);capture=CapturePipeline(adapter.pipeline);adapter.pipeline=capture
    raw=[];cases=[];input_records=[]
    for record,request in selected:
        repeated=[];diagnoses=[]
        for repeat in (1,2):
            capture.result=None
            try:
                adapter.predict_path(request)
            except NativeQuantileCrossingError as exc:
                require(str(exc)==CROSSING_MESSAGE and capture.result is not None,'Unexpected crossing failure')
            else:raise ValueError('Published failure did not reproduce; do not replace benchmark')
            rows,diagnosis=raw_path_diagnostics(capture.result,request)
            require(bool(diagnosis['crossing_steps']),'Failure has no crossing evidence')
            repeated.append(rows);diagnoses.append(diagnosis)
            for row in rows:raw.append({'context_id':request.context_id,'evaluation_phase':record['forecasts'][0]['evaluation_phase'],
                                       'repository_id':request.repository_id,'repeat':repeat,**row})
        require(repeated[0]==repeated[1] and diagnoses[0]==diagnoses[1],'Diagnostic repeat mismatch; stop')
        cases.append({'context_id':request.context_id,'repository_id':request.repository_id,
                      'evaluation_phase':record['forecasts'][0]['evaluation_phase'],'origin_utc':request.origin_utc,
                      'forecast_ids':[f['forecast_id'] for f in record['forecasts']],
                      'input':input_characteristics(request,record['context']),'repeat_equal':True,**diagnoses[0]})
        input_records.append(record)
    require(verify_bundle(benchmark)==manifest and verify_checkpoint(checkpoint)==checkpoint_admission,'Frozen benchmark/checkpoint changed')
    require(code=={p.name:file_sha256(p) for p in Path(__file__).parent.glob('*.py')},'Diagnostic source changed')
    output.mkdir(parents=True)
    write_csv(output/'diagnostic_raw_quantiles.csv',raw,RAW_FIELDS)
    write_json(output/'failed_context_inputs.json',input_records)
    write_json(output/'published_interval_diagnostics.json',published_interval_diagnostics(benchmark))
    summary={'status':'PASS','phase':'4.2.1','published_study_id':PUBLISHED_STUDY_ID,
             'benchmark_manifest_sha256':file_sha256(benchmark/'manifest.json'),'diagnostic_contexts':12,'model_calls':24,
             'repeat_equal':True,'no_other_context_inferred':True,'labels_opened':False,'benchmark_rerun':False,
             'original_predictions_replaced':False,'model_configuration_changed':False,'checkpoint':checkpoint_admission,
             'runtime_versions':versions,'implementation_sha256':code,'worker_elapsed_seconds':time.monotonic()-started,
             'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'cases':cases}
    write_json(output/'diagnostic_summary.json',summary)
    publish_manifest(output,[p.name for p in output.iterdir()],{'phase':'4.2.1','status':'PASS','source_sha256':manifest['metadata']['source_sha256']})
    return summary


def run_diagnostics(benchmark,checkpoint,runtime,output):
    benchmark,checkpoint,output=map(lambda p:Path(p).resolve(),(benchmark,checkpoint,output))
    require(not output.exists() and all(not output.is_relative_to(p) and not p.is_relative_to(output) for p in (benchmark,checkpoint)),
            'New diagnostic output separate from experiment/checkpoint required')
    # Validate scope before creating the process or loading a model.
    _,original,_=failed_requests(benchmark);admission=verify_checkpoint(checkpoint)
    output.mkdir(parents=True)
    command=[str(Path(runtime).absolute()),'-m','forecasting_mvp.chronos_diagnostics','--worker',
             '--benchmark',str(benchmark),'--checkpoint',str(checkpoint),'--out',str(output/'results')]
    resources=supervise(command,output,timeout=300,max_rss_bytes=2*1024**3)
    write_json(output/'resources.json',resources)
    require(resources['status']=='PASS','Diagnostic worker failed; no benchmark replacement; inspect worker.log')
    worker=verify_bundle(output/'results')
    require(verify_bundle(benchmark)==original and verify_checkpoint(checkpoint)==admission,'Protected artifacts changed')
    publish_manifest(output,['resources.json','worker.log','results/manifest.json',*['results/'+p for p in worker['artifacts']]],
                     {'phase':'4.2.1','status':'PASS','source_sha256':original['metadata']['source_sha256']})
    return {'status':'PASS','diagnostic_contexts':12,'model_calls':24,'benchmark_preserved':True,'resources':resources}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('benchmark','checkpoint','out'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--runtime-python');parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    if not args.worker and not args.runtime_python:parser.error('--runtime-python required for bounded diagnostics')
    try:
        result=diagnostic_worker(args.benchmark,args.checkpoint,args.out) if args.worker else run_diagnostics(
            args.benchmark,args.checkpoint,args.runtime_python,args.out)
        print(json.dumps({k:v for k,v in result.items() if k not in ('cases','checkpoint','implementation_sha256')},indent=2));return 0
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','error_type':type(exc).__name__,'error':str(exc)}));return 3


if __name__=='__main__':raise SystemExit(main())
