"""Original metadata fixtures only; no measurements, training or collection."""
import copy
import json
from datetime import timedelta
from pathlib import Path
import pytest
from forecasting_multilanguage.contracts import utc,iso,horizon_endpoint
from forecasting_research.phase6_6 import readiness as r
from tools import check_phase6_6_readiness as audit

BASE=Path(__file__).resolve().parents[1]
ORIGIN='2024-01-01T00:00:00Z'

def signal():
    return dict(signal_id='past_activity',source_version_sha256='a'*64,record_version_utc=ORIGIN,
                available_utc=ORIGIN,retrieved_utc='2026-01-01T00:00:00Z',max_source_event_utc='2023-12-31T00:00:00Z',
                window_start_utc='2023-12-02T00:00:00Z',window_end_utc=ORIGIN,window_complete=True,
                availability_proof_sha256='b'*64,semantic_role='OBSERVED_PAST',planned_due_utc=None,event_population_status='PRESENT')
def inspect(s):return r.inspect_signal(s,origin_utc=ORIGIN,study_mode='OPERATIONAL_ASOF')
def row(i,role='train',family='dev',days=0,h=90):
    origin=iso(utc(ORIGIN)+timedelta(days=days))
    return dict(forecast_id=f'{i:064x}',family_id=family,role=role,origin_utc=origin,horizon_days=h,context_days=90,
                label_available_utc=horizon_endpoint(origin,h))
def schedule():return [row(1),row(2,'validation',days=181),row(3,'calibration',days=362),row(4,'test',family='new',days=543)]
def plan():return json.loads((BASE/'examples/phase6_6/readiness_plan.json').read_text())

def test_coherent_descriptor_is_not_proof_or_admission():
    result=inspect(signal())
    assert result['temporal_metadata_status']=='COHERENT_CLAIMS_ONLY'
    assert not result['can_admit_data'] and result['proof_authenticity']=='NOT_VERIFIED_BY_THIS_FUNCTION'

@pytest.mark.parametrize('key',['value','debt_minutes','future_direction','target','outcome','model_score'])
def test_numerical_or_outcome_payload_rejected(key):
    s=signal();s[key]=12
    with pytest.raises(ValueError):inspect(s)

@pytest.mark.parametrize('key',['available_utc','record_version_utc'])
def test_late_or_mutable_final_version_not_available(key):
    s=signal();s[key]='2024-01-02T00:00:00Z'
    if key=='record_version_utc':s['available_utc']=s[key]
    assert inspect(s)['temporal_metadata_status']=='BLOCKED'

def test_commit_date_without_publication_evidence_is_not_enough():
    s=signal();s['availability_proof_sha256']=None
    assert 'NO_AVAILABILITY_PROOF_REFERENCE' in inspect(s)['blockers']

def test_future_plan_deadline_is_not_future_realization():
    s=signal();s.update(signal_id='directional_intent',semantic_role='DECLARED_PLAN',planned_due_utc='2024-03-01T00:00:00Z')
    result=inspect(s);assert not result['blockers'] and not result['planned_date_is_realization_evidence']

def test_observed_future_date_cannot_be_relabelled_plan():
    s=signal();s['planned_due_utc']='2024-03-01T00:00:00Z'
    with pytest.raises(ValueError):inspect(s)

@pytest.mark.parametrize('key',['max_source_event_utc','window_end_utc'])
def test_future_source_is_blocked(key):
    s=signal();s[key]='2024-01-02T00:00:00Z';s.update(record_version_utc='2024-01-03T00:00:00Z',available_utc='2024-01-03T00:00:00Z')
    assert 'FUTURE_SOURCE_OR_WINDOW' in inspect(s)['blockers']

def test_retrospective_is_explicitly_different():
    s=signal();s.update(record_version_utc='2025-01-01T00:00:00Z',available_utc='2025-01-01T00:00:00Z',availability_proof_sha256=None)
    assert inspect(s)['blockers']
    result=r.inspect_signal(s,origin_utc=ORIGIN,study_mode='RETROSPECTIVE_FIXED_ANALYZER')
    assert not result['blockers'] and result['study_mode']=='RETROSPECTIVE_FIXED_ANALYZER' and not result['can_admit_data']

@pytest.mark.parametrize('value',[None,False])
def test_incomplete_or_unknown_window_is_not_zero(value):
    s=signal();s['window_complete']=value;assert 'WINDOW_NOT_PROVEN_COMPLETE' in inspect(s)['blockers']

def test_verified_empty_window_is_distinct_from_unknown():
    s=signal();s.update(max_source_event_utc=None,event_population_status='NO_EVENTS')
    assert inspect(s)['temporal_metadata_status']=='COHERENT_CLAIMS_ONLY'
    s['event_population_status']='UNKNOWN';assert 'EVENT_POPULATION_UNKNOWN' in inspect(s)['blockers']

def test_empty_event_status_cannot_invent_event():
    s=signal();s['event_population_status']='NO_EVENTS'
    with pytest.raises(ValueError):inspect(s)

@pytest.mark.parametrize('update',[dict(source_version_sha256='x'),dict(window_complete=1),dict(event_population_status='ZERO'),dict(signal_id='future_churn'),dict(semantic_role='ACTUAL_FUTURE')])
def test_bad_descriptor_types_and_identity(update):
    s=signal();s.update(update)
    with pytest.raises(ValueError):inspect(s)

@pytest.mark.parametrize('update',[dict(available_utc='2023-01-01T00:00:00Z'),dict(retrieved_utc='2023-01-01T00:00:00Z'),dict(window_start_utc='2025-01-01T00:00:00Z'),dict(max_source_event_utc='2024-01-02T00:00:00Z')])
def test_impossible_chronology_rejected(update):
    s=signal();s.update(update)
    with pytest.raises(ValueError):inspect(s)

def test_schedule_full_information_purge_and_independent_family():
    result=r.inspect_schedule(schedule(),exposed_families=['old'])
    assert result['status']=='COHERENT_METADATA_ONLY' and not result['can_start_experiment']

@pytest.mark.parametrize('gap',[90,179,180])
def test_90_day_label_plus90_day_context_requires_more_than180_day_origin_gap(gap):
    rows=schedule();rows[1]=row(2,'validation',days=gap)
    result=r.inspect_schedule(rows,exposed_families=[])
    assert any(b['code']=='INFORMATION_INTERVAL_OVERLAP' for b in result['blockers'])

def test_exposed_family_cannot_be_fresh_holdout():
    result=r.inspect_schedule(schedule(),exposed_families=['new'])
    assert any(b['code']=='EXPOSED_FAMILY_IN_CONFIRMATORY_TEST' for b in result['blockers'])

def test_family_cannot_cross_confirmatory_roles():
    rows=schedule();rows[-1]['family_id']='dev'
    assert any(b['code']=='FAMILY_CROSSES_CONFIRMATORY_ROLE' for b in r.inspect_schedule(rows,exposed_families=[])['blockers'])

def test_unavailable_training_labels_block_pooled_model_across_repositories():
    rows=schedule();rows[0]['label_available_utc']='2030-01-01T00:00:00Z';rows[1]['family_id']='other'
    result=r.inspect_schedule(rows,exposed_families=[])
    assert any(b['code']=='LABEL_NOT_AVAILABLE_BEFORE_NEXT_ROLE' and b['later']==rows[1]['forecast_id'] for b in result['blockers'])

def test_unknown_label_availability_remains_unknown():
    rows=schedule();rows[0]['label_available_utc']=None
    assert any(b['code']=='UNKNOWN_DELAYED_LABEL_AVAILABILITY' for b in r.inspect_schedule(rows,exposed_families=[])['blockers'])

@pytest.mark.parametrize('mutation',['duplicate','too_many','missing_role','bad_context','future_label_value','bad_exposure_type'])
def test_bad_or_partial_schedules(mutation):
    rows=schedule()
    if mutation=='duplicate':rows.append(copy.deepcopy(rows[0]))
    elif mutation=='too_many':rows*=100
    elif mutation=='missing_role':
        assert r.inspect_schedule(rows[:1],exposed_families=[])['status']=='BLOCKED';return
    elif mutation=='bad_context':rows[0]['context_days']=512
    elif mutation=='future_label_value':rows[0]['actual_minutes']=100
    else:
        with pytest.raises(ValueError):r.inspect_schedule(rows,exposed_families='old')
        return
    with pytest.raises(ValueError):r.inspect_schedule(rows,exposed_families=[])

@pytest.mark.parametrize('h',[30,60,90])
def test_horizon_specific_delayed_feedback(h):
    end=horizon_endpoint(ORIGIN,h);late=iso(utc(end)+timedelta(days=3))
    assert r.feedback_eligibility(origin_utc=ORIGIN,horizon_days=h,label_available_utc=late,update_utc=end,domain_matches=True)['timing_status']=='BLOCKED'
    result=r.feedback_eligibility(origin_utc=ORIGIN,horizon_days=h,label_available_utc=late,update_utc=late,domain_matches=True)
    assert result['timing_status']=='COHERENT_TIMING_ONLY' and not result['permission_to_update_model']

@pytest.mark.parametrize('h',[True,29,31,91,'30'])
def test_wrong_endpoints_rejected(h):
    with pytest.raises(ValueError):r.feedback_eligibility(origin_utc=ORIGIN,horizon_days=h,label_available_utc=None,update_utc=ORIGIN,domain_matches=True)

def test_label_cannot_exist_before_its_target():
    with pytest.raises(ValueError):r.feedback_eligibility(origin_utc=ORIGIN,horizon_days=90,label_available_utc=ORIGIN,update_utc=ORIGIN,domain_matches=True)

def test_domain_mismatch_blocks_feedback():
    result=r.feedback_eligibility(origin_utc=ORIGIN,horizon_days=30,label_available_utc=None,update_utc='2025-01-01T00:00:00Z',domain_matches=False)
    assert set(result['blockers'])=={'UNKNOWN_LABEL_AVAILABILITY','MEASUREMENT_DOMAIN_MISMATCH'}

@pytest.mark.parametrize('key,value',[('authorization_status','APPROVED'),('future_data_use_authorized',True),('measurement_domain_status','PASS'),('strict_target_history_status','ADMITTED')])
def test_no_self_approval_or_promotion(key,value):
    p=plan();p[key]=value
    with pytest.raises(ValueError):r.inspect_plan(p)

def test_actual_readiness_audit_stays_blocked_and_deterministic():
    before=(BASE/'examples/phase5_2_2_c/human_permission_checklist.json').read_bytes()
    a=audit.audit(BASE);assert a==audit.audit(BASE)
    assert a['phase_c_decisions']==24 and a['evidence_files_verified']==20 and not a['real_data_admitted'] and not a['predictive_signal_validated']
    assert all(v==0 for v in a['operations'].values())
    assert (BASE/'examples/phase5_2_2_c/human_permission_checklist.json').read_bytes()==before

@pytest.mark.parametrize('path',['/etc/passwd','../db','examples/../raw.json','data.csv','forecasting_multilanguage/remediation/content.py'])
def test_only_allowlisted_metadata_can_be_opened(path):
    with pytest.raises(ValueError):audit.reference(BASE,dict(path=path,sha256='a'*64))

def test_bad_hash_and_symlink_metadata_rejected(tmp_path):
    name=audit.REFERENCES[0]
    with pytest.raises(ValueError):audit.reference(BASE,dict(path=name,sha256='0'*64))
    (tmp_path/name).symlink_to(BASE/name)
    with pytest.raises(ValueError):audit.reference(tmp_path,dict(path=name,sha256='0'*64))

def test_no_model_collection_or_network_surface():
    import inspect
    text=inspect.getsource(r)+inspect.getsource(audit)
    for bad in ('import requests','import sqlite','import torch','subprocess','from_pretrained','urlopen','model.fit','Predictor('):assert bad not in text
