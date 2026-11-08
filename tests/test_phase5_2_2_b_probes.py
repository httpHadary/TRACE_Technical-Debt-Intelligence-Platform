"""Pure safety/evidence tests; never starts a container or executes a runtime."""
import copy
import json
from pathlib import Path
import pytest
from tools import probe_phase5_2_2_b as probes


@pytest.fixture
def container():
    return {'Config':{'Labels':{probes.LABEL:'owner'},'User':'1000:1000'},'Image':'pinned',
        'HostConfig':{'NetworkMode':'none','Memory':probes.MEMORY,'MemorySwap':probes.MEMORY,
                     'NanoCpus':1000000000,'ReadonlyRootfs':True,'Privileged':False,
                     'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges']},
        'Mounts':[{'Type':'bind','Source':'/task-own/script','RW':False}]}


@pytest.mark.parametrize('field,value',[
    ('NetworkMode','bridge'),('Memory',2*probes.MEMORY),('MemorySwap',2*probes.MEMORY),
    ('NanoCpus',2000000000),('ReadonlyRootfs',False),('Privileged',True),('CapDrop',[]),('SecurityOpt',[])])
def test_isolation_cannot_silently_change(container,field,value):
    container['HostConfig'][field]=value
    with pytest.raises(ValueError):probes.verify_container(container,'owner','pinned',{'/task-own/script'})


def test_ownership_and_image_protection(container):
    assert probes.verify_container(container,'owner','pinned',{'/task-own/script'})
    with pytest.raises(ValueError):probes.verify_container(container,'different','pinned',{'/task-own/script'})
    with pytest.raises(ValueError):probes.verify_container(container,'owner','other-image',{'/task-own/script'})


@pytest.mark.parametrize('field,value',[('Source','/home/hp/.m2'),('RW',True),('Type','unexpected')])
def test_host_mount_restrictions(container,field,value):
    container['Mounts'][0][field]=value
    with pytest.raises(ValueError):probes.verify_container(container,'owner','pinned',{'/task-own/script'})


def test_conflicting_published_hashes_rejected():
    data={'scanner_image_offline_files':{'files':[{'path':'same','sha256':'a'*64},{'path':'same','sha256':'b'*64}]}}
    with pytest.raises(ValueError):probes.expected_files(data,'scanner')


def test_measured_memory_and_cpu_limits_rejected():
    base=Path(__file__).resolve().parents[1]/'examples/phase5_2_2_b/scanner-cli.log'
    text=base.read_text();value=probes.parse_log(text)
    assert value['command_exit_code']==0 and value['cgroup_memory_peak_bytes']<probes.MEMORY
    with pytest.raises(ValueError):probes.parse_log(text.replace('TD522B_MEMORY_MAX=1073741824','TD522B_MEMORY_MAX=2147483648'))
    with pytest.raises(ValueError):probes.parse_log(text.replace('TD522B_CPU_MAX=100000 100000','TD522B_CPU_MAX=200000 100000'))


def test_incomplete_resource_evidence_never_passes():
    with pytest.raises((ValueError,StopIteration)):probes.parse_log('SonarScanner CLI 8.0.1.6346\n')


def test_published_probes_are_version_only_and_complete():
    root=Path(__file__).resolve().parents[1]
    data=json.loads((root/'examples/phase5_2_2_b/runtime_evidence.json').read_text())
    assert {v['probe'] for v in data['probe_results']}=={'scanner-cli','scanner-java','maven','build-java','node'}
    for v in data['probe_results']:
        assert v['status']=='PASS' and v['container_exit_code']==v['command_exit_code']==0
        assert v['expected_versions_observed'] and v['network_mode']=='none'
        assert not v['oom_killed'] and not v['timed_out']
        assert v['cgroup_memory_peak_bytes']<=probes.MEMORY
        assert '--version' in v['command'] or '-version' in v['command']
        assert not set(v['command']) & {'compile','test','install','package','verify','sonar:sonar'}
    assert not data['server_started'] and data['scans']==data['historical_compilations']==0
    assert all(c['removed'] for c in data['cleanup'])
    assert sum(c['started'] for c in data['cleanup'])==5
    assert data['host_temporary_storage_peak_bytes']<=probes.MAX_TEMP
    assert not data['rights_approval_granted']


def test_native_console_warning_not_hidden_by_version_success():
    root=Path(__file__).resolve().parents[1]
    data=json.loads((root/'examples/phase5_2_2_b/runtime_evidence.json').read_text())
    maven=next(v for v in data['probe_results'] if v['probe']=='maven')
    assert 'UnsatisfiedLinkError' in maven['stderr']
    finding=next(v for v in data['compatibility_findings'] if v['probe']=='maven')
    assert finding['status']=='WARNING' and finding['command_succeeded']
    assert finding['native_console_loading_verified'] is False and finding['noexec_policy_retained']
