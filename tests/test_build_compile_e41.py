"""E.4.1 policy/evidence tests. No Docker/Maven execution or network access."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import pytest
from tools import build_compile_e41 as e

BASE=Path(__file__).resolve().parents[1]


def test_pinned_command_cache_and_unchanged_smoke():
    assert e.maven_command()==e.prior.maven_command()
    old=Path(e.b.__file__).with_name('build_sandbox_setup.sh')
    original=old.read_bytes();s=e.wrapper_script()
    assert original==old.read_bytes()
    assert '--e41-offline-compile' in s and '--e02-offline-compile' not in s and '--no-maven-smoke' not in s
    assert '-eq 753 ]' in s and '-eq 653 ]' not in s
    assert s.count('/usr/share/maven/bin/mvn')==1
    assert s.index("trap 'finish")<s.index('run_stage MODE')
    assert 'INJECTED_PRE_MAVEN_FAILURE' not in s and b'INJECTED_PRE_MAVEN_FAILURE' in original
    assert '240s /usr/share/maven/bin/mvn' in s and '-Duser.home=/tmp' in s
    assert 'enforcer.skip' not in s and 'git init' not in s
    assert subprocess.run(['/bin/sh','-n'],input=s.encode(),capture_output=True).returncode==0


def test_published_753_manifest_and_canonical_identity():
    p=BASE/'examples/phase5_2_2_e_4/dependency_manifest.json'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==e.MANIFEST
    rows=json.loads(p.read_text())['artifacts'];assert len(rows)==753
    raw=''.join(f"{r['sha256']}  {r['bytes']}  {r['path']}\n" for r in sorted(rows,key=lambda r:r['path']))
    assert hashlib.sha256(raw.encode()).hexdigest()==e.CACHE_ID
    budget=e.capacity(rows)
    assert budget['payload_bytes']==80688146
    assert budget['estimated_total_bytes']<e.REPOSITORY_CAP==128*1024**2
    assert budget['metadata_reserve_bytes']==16*1024**2


def test_repository_capacity_cannot_silently_expand():
    with pytest.raises(ValueError,match='128MiB'):e.capacity([dict(path='g/a/1/a-1.jar',bytes=e.REPOSITORY_CAP)])


@pytest.mark.parametrize('parent',['phase5_2_2_e_0_2','phase5_2_2_e_0_3','phase5_2_2_e_0_4','phase5_2_2_e_0_5','phase5_2_2_e_0_5_1','phase5_2_2_d_3'])
def test_prepare_refuses_old_tasks_before_reading_or_writing(monkeypatch,parent):
    monkeypatch.setattr(e,'verify_cache',lambda *a:pytest.fail('No access after invalid destination'))
    with pytest.raises(ValueError):e.prepare(BASE,e.RESEARCH/parent/'forbidden-new-task')


def test_claim_exclusive_without_any_second_gate_or_container(tmp_path,monkeypatch):
    (tmp_path/'attempt_claim.json').write_text('{}')
    monkeypatch.setattr(e.b,'enforce_process_limits',lambda:None)
    monkeypatch.setattr(e,'verify_prepared',lambda *a:pytest.fail('No second attempt'))
    with pytest.raises(FileExistsError):e.execute_once(tmp_path)


def test_failed_input_integrity_never_creates_container(tmp_path,monkeypatch):
    monkeypatch.setattr(e.b,'enforce_process_limits',lambda:None)
    def fail(*args):raise ValueError('tampered cache')
    monkeypatch.setattr(e,'verify_prepared',fail)
    monkeypatch.setattr(e.b,'docker',lambda *a:pytest.fail('No Docker on integrity failure'))
    result=e.execute_once(tmp_path)
    assert result['errors'][0]['kind']=='INPUT_INTEGRITY'
    assert 'substatus' not in result


def test_failed_resource_admission_never_creates_container(tmp_path,monkeypatch):
    monkeypatch.setattr(e.b,'enforce_process_limits',lambda:None)
    monkeypatch.setattr(e,'verify_prepared',lambda *a:None)
    def fail(*args):raise RuntimeError('BLOCKED_RESOURCES')
    monkeypatch.setattr(e,'admission',fail)
    monkeypatch.setattr(e.b,'docker',lambda *a:pytest.fail('No Docker on resource failure'))
    result=e.execute_once(tmp_path)
    assert result['substatus']=='BLOCKED_RESOURCES' and (tmp_path/'attempt_claim.json').exists()


def test_four_gib_gate_and_metadata_budget_not_weakened(tmp_path,monkeypatch):
    rows=json.loads((BASE/'examples/phase5_2_2_e_4/dependency_manifest.json').read_text())
    (tmp_path/'artifact_seed_manifest.json').write_text(json.dumps(rows))
    monkeypatch.setattr(e.b,'admission',lambda:dict(available_ram_bytes=4*1024**3-1))
    with pytest.raises(RuntimeError,match='4GiB'):e.admission(tmp_path)
    monkeypatch.setattr(e.b,'admission',lambda:dict(available_ram_bytes=4*1024**3))
    assert e.admission(tmp_path)['headroom_bytes']==2*1024**3


def container(tmp_path):
    return dict(Name='/owned',Image=e.b.IMAGE,Config=dict(User='1000:1000',Labels={e.LABEL:'owned'},
        Cmd=['/inspection/wrapper.sh',e.MODE],Entrypoint=['/bin/sh'],WorkingDir='/source',Env=[
            'MAVEN_OPTS='+e.OPTIONS,'HOME=/tmp','MAVEN_CONFIG=/tmp/.m2','MAVEN_SKIP_RC=true','MAVEN_ARGS=',
            'JAVA_TOOL_OPTIONS=','JDK_JAVA_OPTIONS=']),
        HostConfig=dict(Memory=e.MEMORY,MemorySwap=e.MEMORY,NanoCpus=1000000000,PidsLimit=64,NetworkMode='none',
            ShmSize=8388608,ReadonlyRootfs=True,Privileged=False,CapAdd=None,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Tmpfs=e.b.tmpfs_options(),
            Ulimits=[dict(Name='fsize',Soft=8388608,Hard=8388608),dict(Name='nofile',Soft=1024,Hard=1024)]),
        Mounts=[dict(Type='bind',Destination='/'+p,Source=str(tmp_path/p),RW=False) for p in ('inputs','inspection')])


@pytest.mark.parametrize('mutation',['e02_mode','smoke_mode','heap','root','memory','swap','network','owner','pids','shm','cap','writable_mount','socket_mount','jvm_injection'])
def test_compile_policy_refuses_unsafe_or_wrong_version_settings(tmp_path,mutation):
    c=container(tmp_path);e.validate_container(c,'owned',tmp_path)
    if mutation=='e02_mode':c['Config']['Cmd'][-1]='--e02-offline-compile'
    elif mutation=='smoke_mode':c['Config']['Cmd'][-1]='--no-maven-smoke'
    elif mutation=='heap':c['Config']['Env'][0]='MAVEN_OPTS=-Xmx2g'
    elif mutation=='root':c['Config']['User']='0:0'
    elif mutation=='memory':c['HostConfig']['Memory']=1024**3
    elif mutation=='swap':c['HostConfig']['MemorySwap']=3*1024**3
    elif mutation=='network':c['HostConfig']['NetworkMode']='bridge'
    elif mutation=='owner':c['Config']['Labels']={e.prior.LABEL:'owned'}
    elif mutation=='pids':c['HostConfig']['PidsLimit']=128
    elif mutation=='shm':c['HostConfig']['ShmSize']=64*1024**2
    elif mutation=='cap':c['HostConfig']['CapAdd']=['SYS_ADMIN']
    elif mutation=='writable_mount':c['Mounts'][0]['RW']=True
    elif mutation=='socket_mount':c['Mounts'].append(dict(Type='bind',Destination='/var/run/docker.sock',Source='/var/run/docker.sock',RW=False))
    else:c['Config']['Env'][-1]='JDK_JAVA_OPTIONS=-javaagent:/unapproved.jar'
    with pytest.raises(ValueError):e.validate_container(c,'owned',tmp_path)


def evidence(tmp_path,stdout,exit_code=1):
    cap=tmp_path/'capture';cap.mkdir()
    seed=json.loads((BASE/'examples/phase5_2_2_e_4/dependency_manifest.json').read_text())
    (tmp_path/'artifact_seed_manifest.json').write_text(json.dumps(seed))
    for name,text in {'maven.stdout':stdout,'maven.stderr':'','setup.complete':'true\n','source.verify.exit':'0\n',
            'maven.exit':str(exit_code)+'\n','cache.post.sha256':''.join(r['sha256']+'  /runtime-repository/'+r['path']+'\n' for r in seed['artifacts']),
            'source.post.sha256':'','memory.peak':'1000\n'}.items():(cap/name).write_text(text)
    run=dict(terminal_state=dict(ExitCode=exit_code,OOMKilled=False),cleanup_complete=True,errors=[],events=[dict(action='start')])
    (tmp_path/'execution.json').write_text(json.dumps(run));return cap,seed


def test_753_seed_preservation_includes_recovered_target_artifacts_and_excludes_them_from_metadata(tmp_path):
    cap,seed=evidence(tmp_path,'[INFO] Scanning for projects...\n[ERROR] original enforcer rejection\n')
    q=e.analyze(tmp_path)
    assert q['cache_changes']['seed_artifacts_unchanged']
    assert q['cache_changes']['added_metadata']==[]
    row=next(x for x in seed['artifacts'] if x['coordinates'][2]=='5.11.2')
    content=(cap/'cache.post.sha256').read_text().replace(row['sha256']+'  /runtime-repository/'+row['path'],'0'*64+'  /runtime-repository/'+row['path'])
    (cap/'cache.post.sha256').write_text(content)
    q=e.analyze(tmp_path)
    assert not q['cache_changes']['seed_artifacts_unchanged']
    assert row['path'] in q['cache_changes']['missing_or_changed_seed_artifacts']


def test_plugin_runtime_resolution_failure_has_exact_missing_coordinates(tmp_path):
    cap,_=evidence(tmp_path,'[INFO] Scanning for projects...\n[INFO] --- enforcer:3.5.0:enforce (enforce-maven) @ commons-cli ---\n[ERROR] Plugin org.apache.maven.plugins:maven-enforcer-plugin:3.5.0 or one of its dependencies could not be resolved: com.example:missing:jar:1.2 has not been downloaded from it before.\n')
    q=e.analyze(tmp_path)
    assert q['status']=='BLOCKED_DEPENDENCY' and q['maven_actually_launched']
    assert q['missing_artifacts'][0]['path']=='com/example/missing/1.2/missing-1.2.jar'
    assert q['missing_artifacts'][0]['dependency_domain']=='PLUGIN_RUNTIME_OR_PLUGIN_ARTIFACT'
    assert q['actual_plugin_order'][0]['prefix']=='enforcer'


def test_scm_context_failure_never_fabricates_git_or_missing_dependency(tmp_path):
    evidence(tmp_path,'[INFO] Scanning for projects...\n[ERROR] SCM failure: not a git repository\n')
    q=e.analyze(tmp_path)
    assert q['status']=='BLOCKED_SCM_CONTEXT' and q['missing_artifacts']==[]


def test_maven_initialization_or_zero_exit_without_classes_cannot_pass(tmp_path):
    evidence(tmp_path,'[INFO] Scanning for projects...\n[INFO] BUILD SUCCESS\n',0)
    q=e.analyze(tmp_path)
    assert q['status']=='PARTIAL' and not q['classes']['complete']
    assert q['evidence_completeness']['complete'] is False


def test_absent_cgroup_measurements_are_unavailable_not_invented(tmp_path):
    cap,_=evidence(tmp_path,'[INFO] Scanning for projects...\n[ERROR] build failed\n')
    (cap/'memory.peak').unlink()
    q=e.analyze(tmp_path)
    assert q['cgroup_peak_memory_bytes'] is None
    assert 'memory.peak' in q['evidence_completeness']['unavailable']


def test_no_acquisition_or_old_runner_entrypoint():
    source=Path(e.__file__).read_text()
    assert 'urllib' not in source and 'Acquisition' not in source
    assert 'prior.execute_once(' not in source and 'run_smoke(' not in source
    assert 'run_phase5_2_2_e_0' not in source
    assert e.LABEL!=e.prior.LABEL!=e.b.LABEL


def test_class_identity_verification_accounts_for_nonclass_production_resources(tmp_path):
    import io,tarfile,struct
    def utf(s):
        data=s.encode();return b'\x01'+struct.pack('>H',len(data))+data
    name='org/apache/commons/cli/Foo'
    pool=utf(name)+b'\x07\x00\x01'+utf('java/lang/Object')+b'\x07\x00\x03'+utf('SourceFile')+utf('Foo.java')
    raw=b'\xca\xfe\xba\xbe'+struct.pack('>HHH',0,52,7)+pool+struct.pack('>HHHHHHH',0x21,2,4,0,0,0,1)+struct.pack('>HIH',5,2,6)
    source=tmp_path/'inputs/source/src/main/java/org/apache/commons/cli';source.mkdir(parents=True)
    (source/'Foo.java').write_text('package org.apache.commons.cli; public class Foo {}')
    cap=tmp_path/'capture';cap.mkdir()
    with tarfile.open(cap/'classes.tar','w') as tar:
        for path,data in [(name+'.class',raw),('META-INF/LICENSE.txt',b'synthetic resource fixture')]:
            entry=tarfile.TarInfo(path);entry.size=len(data);tar.addfile(entry,io.BytesIO(data))
    q=e.class_manifest(tmp_path)
    assert q['complete'] and q['class_count']==1
    assert q['resources'][0]['path']=='META-INF/LICENSE.txt'
    assert q['classes'][0]['major']==52


def test_e41_mode_is_separate_and_all_old_entrypoints_are_absent():
    source=Path(e.__file__).read_text()
    assert e.MODE=='--e41-offline-compile' and e.LABEL=='techdebt360.phase522e41'
    assert 'build_compile_e04' not in source and 'prior.execute_once(' not in source
    assert '--e04-offline-compile' not in e.wrapper_script()
    assert 'source.modes.before' in e.wrapper_script() and 'source.modes.after' in e.wrapper_script()


def test_original_maven_command_has_no_skips_or_extra_goals():
    assert e.maven_command()==['/usr/share/maven/bin/mvn','--offline','--batch-mode',
        '--no-transfer-progress','--errors','-s','/inspection/settings.xml','-gs','/inspection/settings.xml',
        '-Dmaven.repo.local=/runtime-repository','-Duser.home=/tmp','-Dmaven.test.skip=true',
        '-Dmaven.compiler.release=8','compile']
    assert e.OPTIONS=='-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp'
    assert e.RECOVERY.name=='recovery-1' and e.RECOVERY.parent.parent.name=='phase5_2_2_e_4'


def test_tminus90_identity_never_substitutes_t0_model():
    assert e.COMMIT=='aad30eff27ac5c9a13194125226653c6c2826c58'
    assert e.TREE=='d7434665397c8dd8156fff7ecaed29a14feeb951'
    assert e.POM=='1c82171f91da0f4aa2994bb367e4c9ef8e65414940100be081715605739d9e0b'
    assert e.MODE=='--e41-offline-compile'
    script=e.wrapper_script()
    assert '-eq 138 ]' in script and '-eq 117 ]' not in script
    assert '-eq 753 ]' in script and '-eq 697 ]' not in script
    source=Path(e.__file__).read_text()
    assert 'effective_pom_sha256=None' in source
    assert 'bf4a9243703b32ca' not in source and 'b.E0' not in source
    assert 'prior.execute_once(' not in source


def test_target_lifecycle_registered_from_own_descriptors(tmp_path):
    import zipfile
    directory=tmp_path/'examples/phase5_2_2_e_4';directory.mkdir(parents=True)
    repository=tmp_path/'repository';jar=repository/'org/codehaus/mojo/buildnumber-maven-plugin/3.2.1/buildnumber-maven-plugin-3.2.1.jar'
    jar.parent.mkdir(parents=True)
    raw=b'<plugin><groupId>org.codehaus.mojo</groupId><artifactId>buildnumber-maven-plugin</artifactId><version>3.2.1</version><goalPrefix>buildnumber</goalPrefix></plugin>'
    with zipfile.ZipFile(jar,'w') as archive:archive.writestr('META-INF/maven/plugin.xml',raw)
    plugin=dict(gav=['org.codehaus.mojo','buildnumber-maven-plugin','3.2.1'],jar_sha256=e.b.sha(jar),descriptor_sha256=hashlib.sha256(raw).hexdigest(),configured_executions=[dict(goal='create',id='default',phase='generate-resources')],default_bindings=[])
    (directory/'buildplan_descriptor_verification.json').write_text(json.dumps(dict(plugins=[plugin])))
    expected=e.registered_lifecycle(tmp_path,repository)
    assert expected[0]['version']=='3.2.1'
    rows=[dict(r,project='commons-cli') for r in expected]
    assert e.lifecycle_matches(rows,expected)
    assert not e.lifecycle_matches(rows+[dict(prefix='surefire',version='3.4.0',goal='test',execution='default-test',project='commons-cli')],expected)
    rows[0]['version']='unexpected'
    assert not e.lifecycle_matches(rows,expected)


@pytest.mark.parametrize('parent',['phase5_2_2_e_1_1','phase5_2_2_e_2','phase5_2_2_e_2_1','phase5_2_2_e_3','phase5_2_2_e_3_1','phase5_2_2_e_4'])
def test_successful_build_and_new_seed_phase_are_protected(monkeypatch,parent):
    monkeypatch.setattr(e,'verify_cache',lambda *args:pytest.fail('Do not read seeds for forbidden output'))
    with pytest.raises(ValueError):e.prepare(BASE,e.RESEARCH/parent/'forbidden')


def test_target_enforcer_and_other_compile_versions_are_registered():
    matrix=json.loads((BASE/'examples/phase5_2_2_e_4/buildplan_descriptor_verification.json').read_text())
    versions={r['gav'][1]:r['gav'][2] for r in matrix['plugins']}
    assert versions['maven-enforcer-plugin']=='3.5.0'
    assert versions['buildnumber-maven-plugin']=='3.2.1'
    assert versions['maven-compiler-plugin']=='3.13.0'
    assert versions['maven-artifact-plugin']=='3.5.1'
    assert e.SOURCE_MANIFEST==hashlib.sha256((BASE/'examples/phase5_2_2_e_4/source_manifest.json').read_bytes()).hexdigest()
    q=json.loads((BASE/'examples/phase5_2_2_e_4/source_manifest.json').read_text())
    assert len(q['source_entries'])==138 and len(q['production_java_sources'])==36
    assert q['actual_effective_model_sha256'] is None


def test_nonfatal_rat_warnings_have_observed_plugin_context(tmp_path):
    cap,_=evidence(tmp_path,'[INFO] Scanning for projects...\n[INFO] --- apache-rat:0.16.1:check (rat-check) @ commons-cli ---\n[WARNING] The POM for log4j:log4j:jar:1.2.12 is missing, no dependency information available\n[ERROR] Original build failed later\n')
    result=e.analyze(tmp_path)
    warning=result['missing_pom_descriptors'][0]
    assert warning['dependency_domain']=='PLUGIN_METADATA_COLLECTION'
    assert warning['observed_during']['prefix']=='apache-rat' and warning['fatal'] is False


def test_enforcer_failure_never_promotes_to_compile_pass(tmp_path):
    evidence(tmp_path,'[INFO] Scanning for projects...\n[INFO] --- enforcer:3.5.0:enforce (enforce-java-version) @ commons-cli ---\n[ERROR] Rule RequireJavaVersion failed\n')
    result=e.analyze(tmp_path)
    assert result['status']=='BLOCKED_BUILD_OR_RESOURCE' and not result['classes']['complete']


def test_old_e11_runner_is_not_invoked():
    code=Path(e.__file__).read_text()
    assert 'build_compile_e11' not in code and 'prior.execute_once(' not in code
    assert e.MODE=='--e41-offline-compile'
    assert e.LABEL=='techdebt360.phase522e41'
    assert '--e11-offline-compile' not in e.wrapper_script()


def test_help_package_population_is_required_and_identity_bound():
    source=json.loads((BASE/'examples/phase5_2_2_e_4/source_manifest.json').read_text())
    paths=e.production_inputs(source['source_entries'])
    assert len(paths)==36 and sum('/cli/help/' in p for p in paths)==10
    assert paths==sorted(source['production_java_sources'])
    with pytest.raises(ValueError):e.production_inputs([r for r in source['source_entries'] if '/cli/help/' not in r['path']])
    with pytest.raises(ValueError):e.production_inputs(source['source_entries']+[dict(path=paths[0])])


def test_actual_tmpfs_usage_is_captured_separately_from_payload_estimate():
    s=e.wrapper_script()
    assert 'df -B1 /runtime-repository' in s and 'du -s -B1 /runtime-repository' in s
    assert 'stat -f -c' in s
    for name in ('repository-usage.before.txt','repository-usage.after.txt'):
        assert name in e.ALLOWED and name in s


def test_help_nested_anonymous_and_package_info_class_mapping(tmp_path):
    import io,tarfile,struct
    directory=tmp_path/'inputs/source/src/main/java/org/apache/commons/cli/help';directory.mkdir(parents=True)
    (directory/'Foo.java').write_text('package org.apache.commons.cli.help; public class Foo {}')
    (directory/'package-info.java').write_text('package org.apache.commons.cli.help;')
    def bytecode(name,source):
        def utf(s):
            raw=s.encode();return b'\x01'+struct.pack('>H',len(raw))+raw
        pool=utf(name)+b'\x07\x00\x01'+utf('java/lang/Object')+b'\x07\x00\x03'+utf('SourceFile')+utf(source)
        return b'\xca\xfe\xba\xbe'+struct.pack('>HHH',0,52,7)+pool+struct.pack('>HHHHHHH',0x21,2,4,0,0,0,1)+struct.pack('>HIH',5,2,6)
    cap=tmp_path/'capture';cap.mkdir()
    with tarfile.open(cap/'classes.tar','w') as archive:
        for simple,source in [('Foo','Foo.java'),('Foo$Inner','Foo.java'),('Foo$1','Foo.java'),('package-info','package-info.java')]:
            name='org/apache/commons/cli/help/'+simple;raw=bytecode(name,source)
            member=tarfile.TarInfo(name+'.class');member.size=len(raw);archive.addfile(member,io.BytesIO(raw))
    result=e.class_manifest(tmp_path)
    assert result['complete'] and result['class_count']==4
    assert {r['kind'] for r in result['classes']}=={'top_level','nested','anonymous','package_info'}


def test_killed_maven_exit137_is_a_resource_failure_even_without_oom_flag(tmp_path):
    evidence(tmp_path,'[INFO] Scanning for projects...\n',exit_code=137)
    result=e.analyze(tmp_path)
    assert result['status']=='BLOCKED_BUILD_OR_RESOURCE' and result['maven_exit']==137


def test_no_consumed_e31_entrypoint_and_target_phase_protection():
    source=Path(e.__file__).read_text()
    assert 'build_compile_e31' not in source and '--e31-offline-compile' not in e.wrapper_script()
    assert e.MODE=='--e41-offline-compile' and e.LABEL=='techdebt360.phase522e41'
    assert 'phase5_2_2_e_3_1' in source and 'phase5_2_2_e_4' in source


def test_nonfatal_scm_fallback_cannot_hide_a_later_compiler_failure(tmp_path):
    evidence(tmp_path,'[INFO] Scanning for projects...\n[WARNING] not a git repository; using original fallback\n[INFO] --- compiler:3.13.0:compile (default-compile) @ commons-cli ---\n[ERROR] Compilation failure: invalid Java source\n')
    result=e.analyze(tmp_path)
    assert result['status']=='BLOCKED_BUILD_OR_RESOURCE'
    assert result['first_error']=='[ERROR] Compilation failure: invalid Java source'
