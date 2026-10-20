"""Bounded allowlisted documentary audit; cannot open metric payloads or run tools."""
import hashlib
import json
from pathlib import Path
from forecasting_research.phase6_6.readiness import inspect_plan
from tools.check_rights_dossier import validate as validate_rights, bounded

FOLDER='examples/phase6_6'
# Only these already-published code/report/metadata files can be audit references.
REFERENCES=(
 'PHASE_6_5_FORECAST_INFORMATION_REPORT.md','PHASE_6_5_REAL_EVIDENCE_REQUIREMENTS.md','PHASE_6_6_EVIDENCE_HANDOFF.md',
 'PHASE_5_1_IMPLEMENTATION_REPORT.md','FEATURE_AVAILABILITY_MATRIX.md','PHASE_5_2_2_C_RIGHTS_DECISION_REPORT.md',
 'examples/phase5_1/pilot_and_source_readiness.json','examples/phase5_1/legacy_identity_audit.json',
 'examples/phase5_1/churn_diagnostics.json','examples/phase5_2_2_c/human_permission_checklist.json',
 'examples/phase5_2_2_c/runtime_prerequisites.json','examples/phase5_2_2_c/dossier_readiness.json',
 'examples/phase5_2_2_e_5_1/six_revision_compile_gate.json','examples/phase6_5/decision.json',
 'examples/phase6_5/verification.json','examples/phase6_5/preservation.json',
 'forecasting_multilanguage/contracts.py','forecasting_multilanguage/cohorts.py',
 'forecasting_multilanguage/features.py','forecasting_multilanguage/admission.py')


def reference(base,row):
    if not isinstance(row,dict) or set(row)!={'path','sha256'} or not isinstance(row['path'],str) or row['path'] not in REFERENCES:
        raise ValueError('Only allowlisted published evidence; no raw data/file discovery')
    raw=bounded(Path(base)/row['path'])
    if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Existing evidence changed')
    return raw


def audit(base):
    base=Path(base);folder=base/FOLDER
    refs=json.loads(bounded(folder/'evidence_index.json'))
    if set(refs)!={'scope','sources'} or refs['scope']!='PUBLISHED_METADATA_ONLY' or not isinstance(refs['sources'],list):
        raise ValueError('Invalid documentary index')
    if len(refs['sources'])!=len(REFERENCES) or {r['path'] for r in refs['sources']}!=set(REFERENCES):
        raise ValueError('Complete unique evidence inventory required')
    for row in refs['sources']:reference(base,row)
    rights=validate_rights(base)
    if rights['decisions']!=24 or rights['collection_authorized']:raise ValueError('Rights gate changed')
    plan=json.loads(bounded(folder/'readiness_plan.json'));result=inspect_plan(plan)
    matrix=json.loads(bounded(folder/'signal_matrix.json'))
    if set(matrix)!={'scope','signals'} or matrix['scope']!='RESEARCH_HYPOTHESES_NOT_VALIDATED':raise ValueError('No real signal validation claim allowed')
    expected=set(plan['signals'])
    if len(matrix['signals'])!=len(expected) or {r['signal_id'] for r in matrix['signals']}!=expected:
        raise ValueError('Signal inventory mismatch')
    catalog=json.loads(bounded(folder/'research_sources.json'))
    if catalog['scope']!='BOUNDED_STATIC_PUBLIC_RESEARCH' or catalog['dataset_files_downloaded']!=0:
        raise ValueError('Static research only; no data acquisition')
    source_ids=[s['id'] for s in catalog['sources']]
    if len(source_ids)!=len(set(source_ids)):raise ValueError('Duplicate research evidence identity')
    required={'signal_id','priority','proposed_features','predictive_question','origin_proof_required',
              'source_status','rights_status','validation_status','confounders','falsification','evidence_ids'}
    for row in matrix['signals']:
        if set(row)!=required or row['rights_status']!='NOT_APPROVED' or row['validation_status']!='NOT_VALIDATED_ON_INDEPENDENT_REAL_DATA':
            raise ValueError('Signal hypotheses cannot become permissions or results')
        if row['priority'] not in ('P0_CONTROL','P1_PILOT','P2_CONDITIONAL','P3_DEFERRED'):
            raise ValueError('Unknown research priority')
        for k in ('proposed_features','origin_proof_required','confounders','evidence_ids'):
            if not isinstance(row[k],list) or not row[k]:raise ValueError('Incomplete signal evidence questions')
        if set(row['evidence_ids'])-set(source_ids):raise ValueError('Unresolved research evidence reference')
    return dict(**result,evidence_files_verified=len(REFERENCES),phase_c_decisions=rights['decisions'],
                candidate_signal_families=len(expected),metadata_only=True,operation_scope='Local documentary audit; public literature review is separate',
                operations=dict(restricted_data_reads=0,data_collection=0,model_fits=0,forecasts=0,scans=0,
                                containers=0,maven=0,downloads=0,permission_changes=0))

if __name__=='__main__':
    print(json.dumps(audit(Path(__file__).resolve().parents[1]),sort_keys=True,indent=2))
