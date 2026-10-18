"""Validate Phase C documentary completeness; cannot grant rights or run tools.

Only bounded local metadata reads and hashes. No approval transition, collection,
network, analyzer, compiler or model entry point exists here.
"""
import hashlib
import json
from pathlib import Path

STATUS='RIGHTS_DECISION_DOSSIER_PASS_ADMISSION_BLOCKED'
LIMIT=2*1024**2
VERSIONS={'sonar-java-plugin-8.37.0.45887.jar':'423d8aaae641b69da7d4e2cbcb28759b18406f76738aa651c574b2a9cba170ab',
 'sonar-python-plugin-5.27.0.35548.jar':'126234f10b1507e63055a028f8762fa80beaf078bbe07cbe4571a62cdecef952',
 'sonar-javascript-plugin-13.4.0.43982-multi.jar':'719bbc19e51820a9fb90578cc92c6ccdf8320896381c5d82a4c2ddab76933af1'}
LICENSE_SHA='b93b383060f0b26e95538455d8a92b0c9bc5bf61c3a1fd42583fc3d535330a03'

def bounded(path):
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('Symlink evidence forbidden')
    with path.open('rb') as stream:raw=stream.read(LIMIT+1)
    if len(raw)>LIMIT:raise ValueError('Evidence reading limit exceeded')
    return raw

def safe_reference(base,record):
    name=record['path'];path=Path(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or not name:
        raise ValueError('Unsafe documentary reference')
    raw=bounded(Path(base)/path)
    if hashlib.sha256(raw).hexdigest()!=record['sha256']:raise ValueError('Evidence identity changed')
    return raw

def validate_documents(docs):
    """Fail closed: this phase can validate an unapproved dossier, never approval."""
    license=docs['licensing_evidence_matrix.json'];rows=license['analyzers']
    if len(rows)!=3 or {r['artifact']:r['artifact_sha256'] for r in rows}!=VERSIONS:raise ValueError('Pinned analyzer population changed')
    for row in rows:
        if (row['license_version']!='SSAL-1.0' or row['license_date']!='2024-11-13' or row['license_sha256']!=LICENSE_SHA
            or row['permission_status']!='NOT_APPROVED' or row['independently_verified_written_permission']
            or row['newer_website_terms_substituted'] or row['legal_opinion']):raise ValueError('License identity or permission changed')
    if license['legal_permission_granted'] or license['external_contact_made'] or license['whole_third_party_license_text_published']:
        raise ValueError('This task grants no rights or contact authority')
    uses=docs['intended_use_matrix.json']['uses'];decisions=docs['human_permission_checklist.json']['decisions']
    expected={'U'+str(i).zfill(2) for i in range(1,16)}
    if len(uses)!=15 or {r['use_id'] for r in uses}!=expected:raise ValueError('Each intended use needs a separate question')
    ids={r['decision_id'] for r in decisions}
    if len(ids)!=len(decisions) or len(decisions)!=24 or not {r['decision_id'] for r in uses}<=ids:raise ValueError('Missing or duplicate decisions')
    for row in uses:
        if row['status']!='NOT_APPROVED' or row['current_phase_execution']:raise ValueError('Intended use is not approved')
    for row in decisions:
        if row['status']!='NOT_APPROVED' or row['approval_evidence']:raise ValueError('Human approval cannot be synthesized here')
        for key in ('question','affected_artifacts','evidence','responsible_human_or_organization','required_proof','allowed_while_unresolved','prohibited_while_unresolved'):
            if not row.get(key):raise ValueError('Incomplete human decision: '+key)
    check=docs['human_permission_checklist.json']
    if check['approval_evidence_found'] or check['approved_decision_count'] or check['legal_acceptance'] or check['current_collection_status']!='BLOCKED':raise ValueError('Collection must remain blocked')
    for row in check['prior_task_A_decisions_unchanged']:
        if row['status']!='NOT_APPROVED':raise ValueError('Task A decisions must remain unapproved')
    categories={r['category'] for r in decisions}
    if categories!={'SOURCE_LICENSE','ANALYZER_LICENSE','DATASET_USE_RIGHTS','RUNTIME_PERMISSION'}:raise ValueError('Independent categories required')
    fields=docs['data_field_rights_matrix.json']['fields']
    if len(fields)!=17 or {r['field_id'] for r in fields}!={'F'+str(i).zfill(2) for i in range(1,18)}:raise ValueError('Field family incomplete')
    modes={'internal_research','local_AI','external_AI_processing','publication','redistribution','commercial_or_hosted'}
    for row in fields:
        if set(row['use_mode_permissions'])!=modes or set(row['use_mode_permissions'].values())!={'NOT_APPROVED'}:raise ValueError('Field-use permission not established')
        if any(row[k]!='NOT_APPROVED' for k in ('intended_use_permission','retention_permission','publication_permission')):raise ValueError('Retention and release need human approval')
        if not set(row['responsible_decisions'])<=ids:raise ValueError('Unknown field decision')
    if docs['data_field_rights_matrix.json']['numeric_or_anonymized_data_exemption_assumed']:raise ValueError('No anonymization shortcut')
    runtime=docs['runtime_prerequisites.json']
    if len(runtime['gates'])!=16 or len({r['gate_id'] for r in runtime['gates']})!=16:raise ValueError('Runtime gate incomplete')
    for row in runtime['gates']:
        if row['runtime_property_status']!='UNKNOWN' or row['permission_status']!='NOT_APPROVED' or row['inspection_authorized_now']:
            raise ValueError('Unverified runtime cannot pass')
    limits=runtime['unchanged_resource_limits']
    if limits['minimum_host_memavailable_bytes']!=10*1024**3 or limits['minimum_disk_free_bytes']!=15*1024**3 or limits['max_total_replay_memory_bytes']!=8*1024**3:
        raise ValueError('Collection limits cannot be weakened')
    if runtime['collection_status']!='BLOCKED' or runtime['actual_native_analyses_for_new_study'] or runtime['source_states']!=18:raise ValueError('No study collection authorized')
    close=docs['compilation_closeout_reference.json']
    if close['new_gate_created'] or close['new_compilation_attempts'] or close['historical_scan_permission']:raise ValueError('Closeout only references existing gate')
    if close['authority']['path']!='examples/phase5_2_2_e_5_1/six_revision_compile_gate.json':raise ValueError('Wrong compilation authority')
    source=docs['source_and_scope_reference.json']
    if len(source['source_states'])!=18 or len({r['commit_sha'] for r in source['source_states']})!=18 or source['new_dataset_created']:
        raise ValueError('Frozen source population changed')
    for row in source['source_states']:
        if row['legal_acceptance'] or row['operational_admission_status']!='QUARANTINE_UNCHANGED':raise ValueError('Source admission remains quarantine')
    # Catch accidental publication of captured license/source dumps or secrets.
    encoded=json.dumps(docs,sort_keys=True)
    if any(word in encoded for word in ('private_text','-----BEGIN PRIVATE KEY-----','SONAR Source-Available License v1.0\\nLast Updated')):
        raise ValueError('Private/full-license content forbidden')
    return dict(status=STATUS,decisions=len(decisions),uses=len(uses),field_families=len(fields),runtime_gates=16,collection_authorized=False,legal_acceptance=False)


def validate(base):
    base=Path(base);folder=base/'examples/phase5_2_2_c'
    names=['licensing_evidence_matrix.json','intended_use_matrix.json','human_permission_checklist.json',
        'data_field_rights_matrix.json','runtime_prerequisites.json','compilation_closeout_reference.json','source_and_scope_reference.json']
    docs={n:json.loads(bounded(folder/n)) for n in names}
    index=json.loads(bounded(folder/'evidence_index.json'))
    for row in index['sources']:safe_reference(base,row)
    # Resolve every immutable evidence reference embedded in these matrices.
    def references(value):
        if isinstance(value,dict):
            if 'path' in value and 'sha256' in value and set(value)<= {'path','sha256','bytes','kind'}:safe_reference(base,value)
            else:
                for item in value.values():references(item)
        elif isinstance(value,list):
            for item in value:references(item)
    references(docs)
    gate=json.loads(safe_reference(base,docs['compilation_closeout_reference.json']['authority']))
    if gate['status']!='COMMONS_CLI_SIX_REVISION_COMPILE_GATE_PASS' or gate['revision_count']!=6 or len(gate['records'])!=6:
        raise ValueError('Existing compilation evidence unavailable')
    if not all(row['status']=='COMPILE_PASS' and all(row['checks'].values()) for row in gate['records']):raise ValueError('Incomplete compilation receipt')
    for name in ('LICENSING_CLARIFICATION_DRAFT.md','CONDITIONAL_NEXT_STEPS.md','NEXT_ACTION_HANDOFF.md'):
        bounded(folder/name)
    draft=bounded(folder/'LICENSING_CLARIFICATION_DRAFT.md').decode()
    if 'DRAFT, NOT SENT' not in draft or 'has not been sent' not in draft:raise ValueError('Unsent draft label required')
    return dict(**validate_documents(docs),evidence_sources_verified=len(index['sources']),existing_compilation_gate_referenced=True,
        operations=dict(maven=0,java=0,containers=0,scans=0,models=0,dataset_reconstruction=0,external_contact=0))

if __name__=='__main__':
    print(json.dumps(validate(Path(__file__).resolve().parents[1]),sort_keys=True,indent=2))
