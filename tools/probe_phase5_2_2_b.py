"""Task B: five sequential offline version probes; no server or project execution."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid
import zipfile

MEMORY=1073741824
TMPFS=33554432
EXECUTION_TIMEOUT=30
MAX_TEMP=384*1024*1024
LABEL='techdebt360.phase522b'
WRAPPER='''#!/bin/sh
set -u
printf 'TD522B_MEMORY_MAX='
cat /sys/fs/cgroup/memory.max || exit 120
printf 'TD522B_CPU_MAX='
cat /sys/fs/cgroup/cpu.max || exit 120
[ "$(cat /sys/fs/cgroup/memory.max)" = "1073741824" ] || exit 121
read quota period < /sys/fs/cgroup/cpu.max
[ "$quota" != max ] && [ "$quota" -le "$period" ] || exit 122
printf 'TD522B_START_UPTIME='
cut -d ' ' -f 1 /proc/uptime
"$@" > /tmp/version.stdout 2> /tmp/version.stderr
status=$?
printf 'TD522B_END_UPTIME='
cut -d ' ' -f 1 /proc/uptime
printf 'TD522B_EXIT=%s\n' "$status"
printf 'TD522B_MEMORY_PEAK='
cat /sys/fs/cgroup/memory.peak || exit 123
printf 'TD522B_CPU_STAT_BEGIN\n'
cat /sys/fs/cgroup/cpu.stat || exit 123
printf 'TD522B_STDOUT_BEGIN\n'
cat /tmp/version.stdout
printf '\nTD522B_STDERR_BEGIN\n'
cat /tmp/version.stderr
printf '\nTD522B_OUTPUT_END\n'
exit "$status"
'''


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b)
    return h.hexdigest()


def docker(*args,timeout=20):
    env=dict(os.environ,GOMAXPROCS='1',GOMEMLIMIT='128MiB',MALLOC_ARENA_MAX='1')
    p=subprocess.run(['docker',*map(str,args)],env=env,capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError('Docker '+args[0]+' failed: '+p.stderr.decode(errors='replace')[:1500])
    if args[0]=='logs':p.stdout+=p.stderr
    if len(p.stdout)>2*1024*1024:raise ValueError('Docker response bound exceeded')
    return p.stdout


def expected_files(manifest,role):
    key={'scanner':'scanner_image_offline_files','build':'build_image_offline_files'}[role]
    result={}
    for row in manifest[key]['files']:
        if row['path'] in result and result[row['path']]!=row['sha256']:raise ValueError('Conflicting published artifact identity')
        result[row['path']]=row['sha256']
    return result


def verify_container(c,owner,image,mount_sources):
    if (c['Config']['Labels'].get(LABEL)!=owner or c['Image']!=image or c['Config']['User']!='1000:1000'
        or c['HostConfig']['NetworkMode']!='none' or c['HostConfig']['Memory']!=MEMORY
        or c['HostConfig']['MemorySwap']!=MEMORY or c['HostConfig']['NanoCpus']!=1000000000
        or not c['HostConfig']['ReadonlyRootfs'] or c['HostConfig']['Privileged']
        or 'ALL' not in c['HostConfig']['CapDrop']
        or not any(v.startswith('no-new-privileges') for v in c['HostConfig']['SecurityOpt'])):
        raise ValueError('Disposable probe isolation mismatch')
    for mount in c['Mounts']:
        if mount['Type']=='bind' and (mount['Source'] not in mount_sources or mount['RW']):
            raise ValueError('Unregistered or writable host bind')
        if mount['Type'] not in ('bind','volume'):raise ValueError('Unexpected mount type')
    return True


def parse_log(text):
    def field(key):return next(v.split('=',1)[1] for v in text.splitlines() if v.startswith(key+'='))
    code=int(field('TD522B_EXIT'));peak=int(field('TD522B_MEMORY_PEAK'))
    quota,period=map(int,field('TD522B_CPU_MAX').split())
    if int(field('TD522B_MEMORY_MAX'))!=MEMORY or peak>MEMORY or quota>period:raise ValueError('Measured probe resource limit mismatch')
    cpu=text.split('TD522B_CPU_STAT_BEGIN\n',1)[1].split('TD522B_STDOUT_BEGIN\n',1)[0]
    stdout=text.split('TD522B_STDOUT_BEGIN\n',1)[1].split('\nTD522B_STDERR_BEGIN\n',1)[0]
    stderr=text.split('\nTD522B_STDERR_BEGIN\n',1)[1].split('\nTD522B_OUTPUT_END',1)[0]
    return dict(command_exit_code=code,cgroup_memory_peak_bytes=peak,memory_limit_bytes=MEMORY,
        cpu_quota_period=[quota,period],cpu_stat={v.split()[0]:int(v.split()[1]) for v in cpu.splitlines()},
        command_wall_seconds=float(field('TD522B_END_UPTIME'))-float(field('TD522B_START_UPTIME')),stdout=stdout,stderr=stderr)


class Probes:
    def __init__(self,manifest,output):
        self.manifest=manifest;self.output=Path(output);self.output.mkdir(parents=True,exist_ok=False)
        self.owner=uuid.uuid4().hex;self.cleanup=[];self.artifacts=[];self.temp_peak=0
        self.preexisting_volumes=set(docker('volume','ls','-q').decode().splitlines())

    @contextmanager
    def container(self,label,role,entry,args=(),mounts=()):
        name='td522b-'+self.owner[:10]+'-'+label
        image=self.manifest['images'][role]['reference'];actual=json.loads(docker('image','inspect',image))[0]['Id']
        if actual!=self.manifest['images'][role]['image_id']:raise ValueError('Pinned image identity changed')
        cmd=['create','--name',name,'--label',LABEL+'='+self.owner,'--pull','never','--network','none',
            '--memory',str(MEMORY),'--memory-swap',str(MEMORY),'--cpus','1','--pids-limit','64',
            '--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--read-only','--tmpfs','/tmp:rw,nosuid,nodev,size='+str(TMPFS),'--shm-size','8388608',
            '--log-driver','local','--log-opt','max-size=1m','--log-opt','max-file=1','--log-opt','compress=false','--workdir','/tmp',
            '--entrypoint',entry]
        for key,value in {'HOME':'/tmp','MAVEN_CONFIG':'/tmp/empty-m2','MAVEN_SKIP_RC':'true','MAVEN_ARGS':'',
            'MAVEN_OPTS':'-Xms16m -Xmx256m -XX:ActiveProcessorCount=1',
            'SONAR_SCANNER_JAVA_OPTS':'-Xms16m -Xmx256m -XX:ActiveProcessorCount=1',
            'SONAR_SCANNER_OPTS':'-Xms16m -Xmx256m -XX:ActiveProcessorCount=1',
            'NODE_OPTIONS':'--max-old-space-size=128'}.items():cmd+=['--env',key+'='+value]
        for src,dst in mounts:cmd+=['--mount',f'type=bind,src={src},dst={dst},readonly']
        docker(*cmd,image,*args)
        try:
            inspect=json.loads(docker('inspect',name))[0]
            verify_container(inspect,self.owner,actual,{str(v[0]) for v in mounts})
            volumes=[v['Name'] for v in inspect['Mounts'] if v['Type']=='volume']
            if set(volumes)&self.preexisting_volumes:raise ValueError('Preexisting volume reuse forbidden')
            yield name,inspect
        finally:
            # Label and unique name checked before any removal; never target old containers.
            current=json.loads(docker('inspect',name))[0]
            if current['Config']['Labels'].get(LABEL)!=self.owner:raise ValueError('Cleanup ownership mismatch')
            volumes=[v['Name'] for v in current['Mounts'] if v['Type']=='volume']
            docker('rm','-f','-v',name)
            remaining=set(docker('volume','ls','-q').decode().splitlines())
            if set(volumes)&remaining:raise ValueError('Task-specific anonymous volume cleanup incomplete')
            self.cleanup.append(dict(container=name,removed=True,anonymous_volumes_removed=len(volumes),started=not current['State']['StartedAt'].startswith('0001-')))

    def storage(self,temp):
        size=sum(p.stat().st_size for p in Path(temp).rglob('*') if p.is_file())
        if size>MAX_TEMP:raise ValueError('Task temporary storage cap exceeded')
        self.temp_peak=max(self.temp_peak,size)

    def copy_verify(self,name,relative,expected,temp):
        path=Path(temp)/('artifact-'+str(len(self.artifacts)))
        docker('cp',name+':/'+relative,path)
        if path.stat().st_size>128*1024*1024:raise ValueError('Artifact copy bound exceeded')
        self.storage(temp)
        actual=sha(path)
        if actual!=expected:raise ValueError('Published artifact SHA256 mismatch: '+relative)
        self.artifacts.append(dict(path=relative,sha256=actual,bytes=path.stat().st_size))
        path.unlink()

    def node(self,temp):
        plugin=next(p for p in self.manifest['plugins'] if 'javascript' in p['filename'])
        # A stopped extraction donor only; /bin/true is never started.
        with self.container('node-artifact','server','/bin/true') as (name,_):
            jar_path=Path(temp)/'javascript.jar'
            docker('cp',name+':/opt/sonarqube/lib/extensions/'+plugin['filename'],jar_path)
            self.storage(temp)
            if jar_path.stat().st_size>128*1024*1024:raise ValueError('Node carrier size cap exceeded')
            if sha(jar_path)!=plugin['sha256']:raise ValueError('Pinned Node carrier JAR changed')
            expected=plugin['embedded_node'];node=Path(temp)/'node';compressed=hashlib.sha256();binary=hashlib.sha256();size=0
            with zipfile.ZipFile(jar_path) as jar,jar.open('linux-x64/node.xz') as stream,node.open('xb') as dest:
                if jar.read('linux-x64/version.txt').decode().strip()!=expected['version_file']:raise ValueError('Node version-file mismatch')
                decompressor=lzma.LZMADecompressor()
                while chunk:=stream.read(65536):
                    compressed.update(chunk);data=decompressor.decompress(chunk);size+=len(data)
                    if size>160*1024*1024:raise ValueError('Node extraction size cap exceeded')
                    binary.update(data);dest.write(data);dest.flush();self.storage(temp)
                if not decompressor.eof or decompressor.unused_data:raise ValueError('Invalid Node XZ boundary')
            if compressed.hexdigest()!=expected['compressed_sha256'] or binary.hexdigest()!=expected['binary_sha256']:raise ValueError('Pinned Node artifact SHA256 mismatch')
            jar_path.unlink();node.chmod(0o555)
            self.artifacts.append(dict(path='javascript-plugin/linux-x64/node',sha256=binary.hexdigest(),bytes=size,
                compressed_sha256=compressed.hexdigest(),carrier_jar_sha256=plugin['sha256']))
            return node

    def probe(self,label,role,command,paths,temp,node=None):
        wrapper=Path(temp)/'probe.sh';mounts=[(wrapper,'/task-probe.sh')]
        if node:mounts.append((node,'/task-runtime/node'))
        with self.container(label,role,'/bin/sh',['/task-probe.sh',*command],mounts) as (name,inspect):
            for path in paths:self.copy_verify(name,path,expected_files(self.manifest,role)[path],temp)
            started=time.monotonic();docker('start',name)
            timed_out=False
            try:exit_code=int(docker('wait',name,timeout=EXECUTION_TIMEOUT).strip())
            except subprocess.TimeoutExpired:
                timed_out=True;docker('kill',name);exit_code=int(docker('wait',name,timeout=10).strip())
            logs=docker('logs',name).decode(errors='replace')
            # Docker logs can send container stderr through its own stderr channel;
            # wrapper redirects both target streams, so evidence stays on stdout.
            if len(logs.encode())>65536:raise ValueError('Probe output bound exceeded')
            (self.output/(label+'.log')).write_text(logs)
            after=json.loads(docker('inspect',name))[0]
            result=dict(probe=label,image=inspect['Image'],command=command,container_exit_code=exit_code,
                timed_out=timed_out,oom_killed=after['State']['OOMKilled'],host_execution_wall_seconds=time.monotonic()-started,
                network_mode=inspect['HostConfig']['NetworkMode'],read_only_root=True,user='1000:1000',
                tmpfs_limit_bytes=TMPFS,pids_limit=64,capabilities_dropped=['ALL'],host_project_or_credential_mounts=False)
            if not timed_out and 'TD522B_EXIT=' in logs:
                result.update(parse_log(logs))
                import re
                output=re.sub(r'\x1b\[[0-9;]*m','',result['stdout']+'\n'+result['stderr'])
                markers={'scanner-cli':['SonarScanner CLI 8.0.1.6346'],'scanner-java':['version "21.0.11"'],
                    'maven':['Apache Maven 3.9.11','Java version: 17.0.17'],'build-java':['version "17.0.17"'],'node':['v24.11.0']}[label]
                result['expected_version_markers']=markers;result['expected_versions_observed']=all(v in output for v in markers)
                result['status']='PASS' if exit_code==result['command_exit_code']==0 and not result['oom_killed'] and result['expected_versions_observed'] else 'FAIL'
            else:result.update(status='BLOCKED_OR_TIMEOUT',resource_evidence_complete=False)
            return result

    def execute(self):
        results=[]
        try:
            with tempfile.TemporaryDirectory(prefix='task-b-',dir=self.output) as temp:
                Path(temp,'probe.sh').write_text(WRAPPER);os.chmod(Path(temp,'probe.sh'),0o444)
                jobs=[('scanner-cli','scanner',['/opt/sonar-scanner/bin/sonar-scanner','--version','-Dsonar.scanner.skipJreProvisioning=true','-Dsonar.scanner.skipNodeProvisioning=true'],
                    ['opt/sonar-scanner/bin/sonar-scanner','opt/sonar-scanner/conf/sonar-scanner.properties','opt/sonar-scanner/lib/sonar-scanner-cli-8.0.1.6346.jar','usr/lib/jvm/java-21-amazon-corretto.x86_64/bin/java','usr/lib/jvm/java-21-amazon-corretto.x86_64/release']),
                    ('scanner-java','scanner',['/usr/lib/jvm/java-21-amazon-corretto.x86_64/bin/java','-Xms16m','-Xmx128m','-XX:ActiveProcessorCount=1','-version'],['usr/lib/jvm/java-21-amazon-corretto.x86_64/bin/java','usr/lib/jvm/java-21-amazon-corretto.x86_64/release']),
                    ('maven','build',['/usr/share/maven/bin/mvn','--version'],['usr/share/maven/bin/mvn','usr/share/maven/lib/maven-core-3.9.11.jar','opt/java/openjdk/bin/java','opt/java/openjdk/release']),
                    ('build-java','build',['/opt/java/openjdk/bin/java','-Xms16m','-Xmx128m','-XX:ActiveProcessorCount=1','-version'],['opt/java/openjdk/bin/java','opt/java/openjdk/release'])]
                for label,role,command,paths in jobs:results.append(self.probe(label,role,command,paths,temp))
                node=self.node(temp)
                results.append(self.probe('node','scanner',['/task-runtime/node','--version'],[],temp,node))
        finally:
            evidence=dict(version='phase5_2_2_b-runtime-probes-v1',probe_results=results,artifact_checks=self.artifacts,
                cleanup=self.cleanup,host_temporary_storage_peak_bytes=self.temp_peak,limits=dict(memory_bytes=MEMORY,cpus=1,execution_timeout_seconds=EXECUTION_TIMEOUT,
                    tmpfs_bytes=TMPFS,task_temp_storage_cap_bytes=MAX_TEMP),server_started=False,historical_compilations=0,
                scans=0,provisioning_allowed=False,parallel_probes=1,rights_approval_granted=False)
            (self.output/'runtime_evidence.json').write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
        return evidence


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args(argv)
    base=Path(__file__).resolve().parents[1]
    manifest=json.loads((base/'examples/phase5_2_1/runtime_artifact_inspection.json').read_text())
    evidence=Probes(manifest,a.output).execute()
    print([(r['probe'],r['status']) for r in evidence['probe_results']])


if __name__=='__main__':main()
