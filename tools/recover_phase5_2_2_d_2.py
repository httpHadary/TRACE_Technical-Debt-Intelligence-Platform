"""Task D.2: one fresh100-request batch; static XML/ZIP reads, never Maven."""
import argparse
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import time
import urllib.error
import urllib.request
import zipfile
from tools.maven_recovery.acquisition import Acquisition, BudgetExceeded, CENTRAL, parse_xml, relative_path
from tools.maven_recovery.continuation import digest
from tools.recover_phase5_2_2_d_1 import audit, classify, frontier_coordinate

BASE='e57cfe77241cdda1130ac1a7fd88ee4dd4f8a879'
SOURCE=Path('/home/hp/tst/research/forecasting_mvp/phase5_2_2_d_1/2026-10-16/continuation-1')
FRONTIER=['commons-logging/commons-logging/1.0.3/commons-logging-1.0.3.pom',
          'commons-digester/commons-digester/1.6/commons-digester-1.6.jar']
MAX_REQUESTS=100
MAX_BYTES=32*1024*1024
MAX_ARTIFACT=32*1024*1024
MAX_DISK=256*1024*1024
MAX_SECONDS=600


def enforce_process_limits():
    if len(os.sched_getaffinity(0))!=1 or not 0<resource.getrlimit(resource.RLIMIT_AS)[0]<=1073741824:
        raise ValueError('Require taskset one CPU and prlimit --as=1073741824')


def verify_rows(root, manifest):
    records={}
    for row in manifest['artifacts']:
        path=relative_path(*row['coordinates'],row['extension'],row['classifier'])
        p=Path(root)/'repository'/path
        if path!=row['path'] or path in records or any(v.is_symlink() for v in (p,*p.parents)):
            raise ValueError('Artifact identity/symlink mismatch')
        if not 0<=p.stat().st_size==row['bytes']<=MAX_ARTIFACT or digest(p)!=row['sha256']:
            raise ValueError('Artifact SHA256/size mismatch')
        raw=p.read_bytes();checksum=row['repository_checksum']
        if (row['source_url']!=CENTRAL+path or checksum['algorithm'] not in ('sha512','sha256','sha1')
                or checksum['url']!=CENTRAL+path+'.'+checksum['algorithm']
                or hashlib.new(checksum['algorithm'],raw).hexdigest()!=checksum['value']):
            raise ValueError('Artifact provenance/checksum mismatch')
        if row['extension']=='pom':
            pom=parse_xml(raw);ns={'m':'http://maven.apache.org/POM/4.0.0'}
            for key,expected in zip(('groupId','artifactId','version'),row['coordinates']):
                value=pom.findtext('m:'+key,namespaces=ns)
                if value is None and key!='artifactId':value=pom.findtext('m:parent/m:'+key,namespaces=ns)
                if value!=expected:raise ValueError('POM coordinate mismatch')
        else:
            with zipfile.ZipFile(io.BytesIO(raw)) as jar:
                if sum(v.file_size for v in jar.infolist())>128*1024*1024 or jar.testzip() is not None:
                    raise ValueError('JAR CRC/size mismatch')
        records[path]=copy.deepcopy(row)
    return records


class Recovery(Acquisition):
    def __init__(self,root,source,published):
        target=Path(root).absolute();source=Path(source).absolute()
        protected=(source,Path('/home/hp/tst/research/forecasting_mvp/phase5_2_2_d/2026-10-16/isolated-cache'))
        if any(target.is_relative_to(p) or p.is_relative_to(target) for p in protected):
            raise ValueError('D.2 must be separate from earlier caches')
        # Read and reverify the entire D.1 seed before creating the new cache.
        old=json.loads((source/'dependency_manifest.json').read_text())
        if (old['version']!='task-d1-acquisition-v1' or old['repository']!=CENTRAL
                or old['requests']!=400 or old['parent_task_d']['requests']!=2000):
            raise ValueError('Earlier ledger identity mismatch')
        if old!=published:raise ValueError('Published D.1 seed manifest mismatch')
        verified=verify_rows(source,old)
        super().__init__(target)
        self.seed_paths=set(verified);self.network_enabled=False;self.http_events=[]
        self.parent=dict(task_d1_manifest_sha256=digest(source/'dependency_manifest.json'),
            task_d1_requests=400,task_d_requests=2000,seed_artifacts=len(verified))
        for path,row in verified.items():
            src=source/'repository'/path;dst=self.cache/path
            self.check_disk(row['bytes'])
            dst.parent.mkdir(parents=True,exist_ok=True)
            with src.open('rb') as left,dst.open('xb') as right:
                for block in iter(lambda:left.read(65536),b''):right.write(block)
            if digest(dst)!=row['sha256'] or dst.stat().st_ino==src.stat().st_ino:
                raise ValueError('Independent seed-copy verification failed')
            self.records[path]=row
        self.seal()

    def check_disk(self,extra=0):
        size=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
        if size+extra>MAX_DISK:raise BudgetExceeded('D.2 disk cap exceeded')
        return size

    def fetch(self,path,limit):
        if not self.network_enabled:raise ValueError('OFFLINE_MISSING: '+path)
        if not re.fullmatch(r'[A-Za-z0-9_./-]+',path) or '..' in path:raise ValueError('Unsafe path')
        self.check_disk(MAX_ARTIFACT)
        url=CENTRAL+path;req=urllib.request.Request(url,headers={'User-Agent':'TechDebt360-Task-D.2-bounded-acquisition'})
        for attempt in range(1,4):
            if self.requests>=MAX_REQUESTS or time.monotonic()-self.started>=MAX_SECONDS:
                raise BudgetExceeded('D.2 request/time cap exhausted')
            self.requests+=1
            try:
                response=self.opener.open(req,timeout=15);break
            except urllib.error.HTTPError as exc:
                self.http_events.append(dict(path=path,status=exc.code));raise
            except (urllib.error.URLError,TimeoutError) as exc:
                self.transport_failures.append(dict(path=path,attempt=attempt,error_type=type(exc).__name__))
                if attempt==3:raise
                time.sleep(0.25)
        with response:
            if response.status!=200 or response.geturl()!=url:raise ValueError('Unexpected repository response')
            cap=min(limit,MAX_BYTES-self.bytes);length=response.headers.get('Content-Length')
            expected=int(length) if length is not None else None
            if cap<=0 or (expected is not None and not 0<=expected<=cap):
                raise BudgetExceeded('D.2 payload/artifact cap exhausted')
            data=bytearray()
            while expected is None or len(data)<expected:
                if time.monotonic()-self.started>=MAX_SECONDS:raise BudgetExceeded('D.2 wall cap exhausted')
                allowance=min(65536,cap-len(data))
                if allowance<=0:raise BudgetExceeded('Cannot prove EOF within D.2 payload cap')
                chunk=response.read(allowance)
                if not chunk:
                    if expected is not None and len(data)!=expected:raise ValueError('Truncated response')
                    break
                self.bytes+=len(chunk);data.extend(chunk)
            return bytes(data)

    def seal(self):
        result=dict(version='task-d2-acquisition-v1',repository=CENTRAL,parent_ledgers=self.parent,
            requests=self.requests,transferred_bytes=self.bytes,seed_count=len(self.seed_paths),
            new_count=len(self.records)-len(self.seed_paths),elapsed_seconds=time.monotonic()-self.started,
            limits=dict(address_space_bytes=1073741824,cpus=1,requests=MAX_REQUESTS,response_bytes=MAX_BYTES,
                        artifact_bytes=MAX_ARTIFACT,disk_bytes=MAX_DISK,seconds=MAX_SECONDS),
            address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],cpu_affinity=sorted(os.sched_getaffinity(0)),
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            http_events=self.http_events,transport_failures=self.transport_failures,
            artifacts=[dict(row,origin='D1_VERIFIED_COPY' if path in self.seed_paths else 'D2_CENTRAL') for path,row in sorted(self.records.items())],
            original_caches_modified=False,maven_goals=0,downloaded_code_executed=0,
            trust_limit='HTTPS repository and same-origin checksum; no independent publisher-signature claim')
        tmp=self.root/'dependency_manifest.json.tmp';tmp.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        tmp.replace(self.root/'dependency_manifest.json');self.check_disk()
        return result


class OfflineCache:
    def __init__(self,root):
        self.root=Path(root).absolute();self.cache=self.root/'repository'
        m=json.loads((self.root/'dependency_manifest.json').read_text())
        if (m['version']!='task-d2-acquisition-v1' or m['repository']!=CENTRAL
                or not 0<=m['requests']<=100 or not 0<=m['transferred_bytes']<=MAX_BYTES
                or m['parent_ledgers']['task_d1_requests']!=400 or m['parent_ledgers']['task_d_requests']!=2000):
            raise ValueError('D.2 ledger mismatch')
        self.records=verify_rows(self.root,m);self.used_paths=set();self.network_enabled=False
    get=Acquisition.get
    def fetch(self,path,limit):raise ValueError('OFFLINE_MISSING: '+path)


def static_status(result):
    # PROFILE unknowns remain visible, but do not invent missing artifacts on
    # the known static branch. Runtime/effective-model readiness is separate.
    if (result['missing_paths'] or any(i['kind']!='PROFILE' for i in result['unresolved'])
            or any(p['required_through_compile'] is None or p['disposition']=='UNRESOLVED'
                   for s in result['states'] for p in s['plugins'])):
        return 'PARTIAL'
    return 'PASS_STATIC_CLOSURE_COMPLETE'


def offline_audit(base,a):
    result=audit(base,a)
    result.update(version='task-d2-static-audit-v1',base_commit=BASE,status=static_status(result),
                  effective_model_verification='PENDING')
    return result


def execute(base,output):
    enforce_process_limits()
    published=json.loads((base/'examples/phase5_2_2_d_1/dependency_manifest.json').read_text())
    if len(published['artifacts'])!=611:raise ValueError('Expected611 pinned D.1 artifacts')
    a=Recovery(output,SOURCE,published);checkpoints=[];stop=None;errors=[]
    def checkpoint(name):
        q=offline_audit(base,a)
        checkpoints.append(dict(name=name,requests=a.requests,new_artifacts=len(a.records)-len(a.seed_paths),missing=q['missing_paths']))
        (a.root/'requirements.json').write_text(json.dumps(q,sort_keys=True,indent=2)+'\n')
        (a.root/'checkpoints.json').write_text(json.dumps(checkpoints,sort_keys=True,indent=2)+'\n')
        a.seal();print(name,'requests',a.requests,'new',len(a.records)-len(a.seed_paths),'missing',len(q['missing_paths']),flush=True)
        return q
    try:
        q=checkpoint('SEEDED_OFFLINE')
        if q['missing_paths']!=sorted(FRONTIER):raise ValueError('Frozen two-file frontier not reproduced')
        paths=list(FRONTIER)
        while paths:
            before=len(a.records);a.network_enabled=True
            for path in paths:
                try:a.get(*frontier_coordinate(path))
                except urllib.error.HTTPError as exc:
                    errors.append(dict(path=path,http_status=exc.code))
            q=checkpoint('AFTER_EXACT_FRONTIER')
            if not q['missing_paths'] or len(a.records)==before:break
            paths=q['missing_paths']
    except Exception as exc:
        stop=dict(type=type(exc).__name__,reason=str(exc)[:1500])
    finally:
        q=checkpoint('FINAL_OFFLINE')
        status='BLOCKED' if stop is not None else static_status(q)
        m=a.seal();categories,matrix=classify(q,dict(m,http_events=m['http_events']),a.root)
        for row,state in zip(matrix,q['states']):
            row['static_closure_status']=static_status(dict(missing_paths=state['missing_paths'],
                unresolved=state['issues'],states=[state]))
            row['effective_model_verification']='PENDING'
        comparison=dict(version='task-d2-frontier-v1',before=sorted(FRONTIER),after=q['missing_paths'],
            resolved=sorted(set(FRONTIER)&set(a.records)),newly_exposed_remaining=sorted(set(q['missing_paths'])-set(FRONTIER)),
            checkpoints=checkpoints,status=status,stop=stop,http_errors=errors,
            offline_build_readiness=q['offline_build_readiness'],effective_model_verification='PENDING')
        for name,data in [('frontier_comparison.json',comparison),('artifact_classification.json',categories),('compile_readiness_matrix.json',matrix)]:
            (a.root/name).write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
        a.check_disk()
    return a,q,comparison


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--audit-only',action='store_true')
    args=p.parse_args();enforce_process_limits();base=Path(__file__).resolve().parents[1]
    if args.audit_only:
        print(json.dumps(offline_audit(base,OfflineCache(args.output)),sort_keys=True,indent=2));return
    a,q,f=execute(base,args.output)
    print(f['status'],'offline build readiness',q['offline_build_readiness'],'requests',a.requests)


if __name__=='__main__':main()
