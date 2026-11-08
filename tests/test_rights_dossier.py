"""Documentary gate tests only; no runtime/model/network or approval actuation."""
import copy
import hashlib
import inspect
import json
from pathlib import Path
import pytest
from tools import check_rights_dossier as d

BASE=Path(__file__).resolve().parents[1]
FOLDER=BASE/'examples/phase5_2_2_c'
NAMES=['licensing_evidence_matrix.json','intended_use_matrix.json','human_permission_checklist.json',
 'data_field_rights_matrix.json','runtime_prerequisites.json','compilation_closeout_reference.json','source_and_scope_reference.json']

def documents():return {name:json.loads((FOLDER/name).read_text()) for name in NAMES}

def test_complete_dossier_is_not_collection_permission():
    result=d.validate(BASE)
    assert result['status']=='RIGHTS_DECISION_DOSSIER_PASS_ADMISSION_BLOCKED'
    assert not result['collection_authorized'] and not result['legal_acceptance']
    assert all(value==0 for value in result['operations'].values())

@pytest.mark.parametrize('decision',range(24))
def test_no_decision_can_be_self_approved(decision):
    docs=documents();docs['human_permission_checklist.json']['decisions'][decision]['status']='APPROVED'
    with pytest.raises(ValueError):d.validate_documents(docs)

@pytest.mark.parametrize('mutation',['permission','invented_signature','new_license','new_date','wrong_sha','wrong_artifact','replacement_terms','contact','legal_opinion','full_license'])
def test_license_evidence_is_pinned_and_no_permissions_are_invented(mutation):
    docs=documents();license=docs['licensing_evidence_matrix.json'];row=license['analyzers'][0]
    if mutation=='permission':row['permission_status']='APPROVED'
    elif mutation=='invented_signature':row['independently_verified_written_permission']=[dict(signature='fictional')]
    elif mutation=='new_license':row['license_version']='SSAL-1.0.1'
    elif mutation=='new_date':row['license_date']='2025-11-20'
    elif mutation=='wrong_sha':row['license_sha256']='0'*64
    elif mutation=='wrong_artifact':row['artifact_sha256']='0'*64
    elif mutation=='replacement_terms':row['newer_website_terms_substituted']=True
    elif mutation=='contact':license['external_contact_made']=True
    elif mutation=='legal_opinion':row['legal_opinion']=True
    else:row['private_text']='not publishable'
    with pytest.raises(ValueError):d.validate_documents(docs)

@pytest.mark.parametrize('mode',['internal_research','local_AI','external_AI_processing','publication','redistribution','commercial_or_hosted'])
def test_each_data_use_mode_needs_its_own_review(mode):
    docs=documents();docs['data_field_rights_matrix.json']['fields'][0]['use_mode_permissions'][mode]='APPROVED'
    with pytest.raises(ValueError):d.validate_documents(docs)

@pytest.mark.parametrize('key',['intended_use_permission','retention_permission','publication_permission'])
def test_retention_and_release_not_implied_by_provenance(key):
    docs=documents();docs['data_field_rights_matrix.json']['fields'][0][key]='ESTABLISHED'
    with pytest.raises(ValueError):d.validate_documents(docs)

@pytest.mark.parametrize('key',['question','affected_artifacts','evidence','responsible_human_or_organization','required_proof','allowed_while_unresolved','prohibited_while_unresolved'])
def test_human_decision_requires_reviewable_fields(key):
    docs=documents();docs['human_permission_checklist.json']['decisions'][0][key]=None
    with pytest.raises(ValueError):d.validate_documents(docs)

@pytest.mark.parametrize('mutation',['runtime_pass','inspection_authority','resources','metric_scan','duplicate_gate','compile_attempt','source_admission','anonymization','dropped_use','dropped_field','duplicate_decision'])
def test_runtime_scientific_and_rights_gates_fail_closed(mutation):
    docs=documents()
    if mutation=='runtime_pass':docs['runtime_prerequisites.json']['gates'][0]['runtime_property_status']='PASS'
    elif mutation=='inspection_authority':docs['runtime_prerequisites.json']['gates'][0]['inspection_authorized_now']=True
    elif mutation=='resources':docs['runtime_prerequisites.json']['unchanged_resource_limits']['minimum_host_memavailable_bytes']=4*1024**3
    elif mutation=='metric_scan':docs['runtime_prerequisites.json']['actual_native_analyses_for_new_study']=1
    elif mutation=='duplicate_gate':docs['compilation_closeout_reference.json']['new_gate_created']=True
    elif mutation=='compile_attempt':docs['compilation_closeout_reference.json']['new_compilation_attempts']=1
    elif mutation=='source_admission':docs['source_and_scope_reference.json']['source_states'][0]['legal_acceptance']=True
    elif mutation=='anonymization':docs['data_field_rights_matrix.json']['numeric_or_anonymized_data_exemption_assumed']=True
    elif mutation=='dropped_use':docs['intended_use_matrix.json']['uses'].pop()
    elif mutation=='dropped_field':docs['data_field_rights_matrix.json']['fields'].pop()
    else:docs['human_permission_checklist.json']['decisions'][0]['decision_id']=docs['human_permission_checklist.json']['decisions'][1]['decision_id']
    with pytest.raises(ValueError):d.validate_documents(docs)

@pytest.mark.parametrize('path',['../escape','/absolute','x/../../escape','x\\unsafe'])
def test_reference_traversal_is_rejected(tmp_path,path):
    with pytest.raises(ValueError):d.safe_reference(tmp_path,dict(path=path,sha256='0'*64))

def test_bound_reads_and_symlink_guards(tmp_path,monkeypatch):
    p=tmp_path/'input';p.write_bytes(b'12345');monkeypatch.setattr(d,'LIMIT',4)
    with pytest.raises(ValueError):d.bounded(p)
    link=tmp_path/'link';link.symlink_to(p)
    with pytest.raises(ValueError):d.bounded(link)


def test_reference_hash_tampering_rejected(tmp_path):
    (tmp_path/'file').write_bytes(b'unchanged')
    with pytest.raises(ValueError):d.safe_reference(tmp_path,dict(path='file',sha256='0'*64))


def test_repeated_validation_is_deterministic():
    left=d.validate(BASE);right=d.validate(BASE)
    assert json.dumps(left,sort_keys=True)==json.dumps(right,sort_keys=True)


def test_validator_has_no_execution_network_or_mutation_entrypoint():
    import ast
    source=inspect.getsource(d);module=ast.parse(source)
    imports={n.names[0].name for n in ast.walk(module) if isinstance(n,ast.Import)}
    assert imports=={'hashlib','json'}
    for forbidden in ('subprocess','urllib','socket','execute_once','docker(','write_text','write_bytes','sqlite3','requests','training','fit('):
        assert forbidden not in source


def test_old_gate_is_the_single_authority_and_closeout_lists_all_identities():
    close=json.loads((FOLDER/'compilation_closeout_reference.json').read_text());p=BASE/close['authority']['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==close['authority']['sha256']
    gate=json.loads(p.read_text());text=(BASE/'SIX_REVISION_COMPILATION_CLOSEOUT.md').read_text()
    assert len(gate['records'])==6 and all(row['status']=='COMPILE_PASS' for row in gate['records'])
    for row in gate['records']:
        assert row['commit'] in text and row['tree'] in text and row['pom_sha256'] in text
    assert not close['new_gate_created'] and not close['historical_scan_permission']


def test_local_models_and_external_services_are_distinct_unapproved_questions():
    q=json.loads((FOLDER/'intended_use_matrix.json').read_text());by_id={u['use_id']:u for u in q['uses']}
    assert q['local_ai_is_external_to_analyzer_program']
    assert len({by_id[k]['question'] for k in ('U04','U05','U06')})==3
    assert all(u['status']=='NOT_APPROVED' for u in q['uses'])
