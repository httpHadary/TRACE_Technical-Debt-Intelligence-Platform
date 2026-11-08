import copy
from pathlib import Path
import pytest
import config
import scan_snapshot
from contracts import sha256, write_json
from sonar_evidence import source_inventory


@pytest.mark.parametrize('path',['A.class','target/project.jar','build/libs/project.jar'])
def test_source_only_owned_bytecode_rejected(tmp_path,path):
    work=tmp_path/'source'; work.mkdir()
    item=work/path; item.parent.mkdir(parents=True,exist_ok=True); item.write_bytes(b'fake')
    with pytest.raises(ValueError):
        scan_snapshot.binary_policy(tmp_path,'a'*40,work,[])


@pytest.mark.parametrize('defect',[None,'commit','tree','image','jdk','status','returncode','hash','class','unlisted'])
def test_compiled_evidence_contract(sandbox,monkeypatch,defect):
    repo=sandbox['repo']; commit=sandbox['commit']
    binary=repo/'target/classes/A.class'
    binary.parent.mkdir(parents=True)
    binary.write_bytes(bytes.fromhex('cafebabe0000003d'))
    log=repo/'build.log'; log.write_text('synthetic build only')
    image='builder@sha256:'+'b'*64
    inventory=source_inventory(repo,commit)
    proof={'commit':commit,'tree':sandbox['git']('rev-parse',commit+'^{tree}'),
           'source_inventory':inventory,'status':'PASS','returncode':0,'jdk_major':17,
           'command':['docker','run','--rm',image,'mvn','compile'],'image':image,
           'build_log':str(log),'build_log_sha256':sha256(log),'binaries':{'A.class':sha256(binary)}}
    if defect in ('commit','tree','image'): proof[defect]='wrong'
    if defect=='jdk': proof['jdk_major']=99
    if defect=='status': proof['status']='FAIL'
    if defect=='returncode': proof['returncode']=True
    if defect=='hash': proof['binaries']['A.class']='0'*64
    if defect=='class':
        binary.write_bytes(b'not a class')
        proof['binaries']['A.class']=sha256(binary)
    if defect=='unlisted': (binary.parent/'B.class').write_bytes(binary.read_bytes())
    proof_path=repo/'proof.json'; write_json(proof_path,proof)
    monkeypatch.setattr(config,'JAVA_BINARIES_PATH',str(binary.parent))
    monkeypatch.setattr(config,'BUILD_IMAGE',image)
    monkeypatch.setattr(config,'COMPILED_EVIDENCE_FILE',str(proof_path))
    work=sandbox['work']/'compiled'; work.mkdir()
    if defect:
        with pytest.raises(ValueError):
            scan_snapshot.binary_policy(repo,commit,work,inventory)
    else:
        mode,root,_=scan_snapshot.binary_policy(repo,commit,work,inventory)
        assert mode=='COMPILED'
        assert sha256(work/root/'A.class')==sha256(binary)
