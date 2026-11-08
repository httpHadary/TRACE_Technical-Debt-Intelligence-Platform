"""Pure readiness checks. Technical coherence is never permission or proof.

Descriptors carry no signal values, labels, payloads or model state. Existing
schema-v2 UTC, horizon, digest and purge contracts remain the authoritative seam.
"""
from datetime import timedelta
from forecasting_multilanguage.contracts import utc, horizon_endpoint, hash_id, digest, MODES
from forecasting_multilanguage.cohorts import purged_training_ids
from . import VERSION

SIGNALS=('debt_history','past_activity','product_state','past_churn','directional_intent')
DESCRIPTOR_FIELDS={'signal_id','source_version_sha256','record_version_utc','available_utc','retrieved_utc',
                   'max_source_event_utc','window_start_utc','window_end_utc','window_complete',
                   'availability_proof_sha256','semantic_role','planned_due_utc','event_population_status'}


def exact(obj,fields):
    if not isinstance(obj,dict) or set(obj)!=set(fields):raise ValueError('Exact metadata fields required; no values or labels')


def inspect_signal(obj,*,origin_utc,study_mode):
    exact(obj,DESCRIPTOR_FIELDS);origin=utc(origin_utc)
    if obj['signal_id'] not in SIGNALS or study_mode not in MODES:raise ValueError('Unregistered signal/mode')
    hash_id(obj['source_version_sha256'])
    if obj['semantic_role'] not in ('OBSERVED_PAST','DECLARED_PLAN'):raise ValueError('Unknown semantic role')
    if obj['semantic_role']=='DECLARED_PLAN' and obj['signal_id']!='directional_intent':raise ValueError('Plan semantics only for declared intent')
    if obj['event_population_status'] not in ('PRESENT','NO_EVENTS','UNKNOWN'):raise ValueError('Explicit event-population status required')
    if obj['event_population_status']=='NO_EVENTS' and (obj['signal_id'] not in ('past_activity','past_churn') or obj['max_source_event_utc'] is not None):raise ValueError('No-events proof is distinct from a fabricated event')
    if obj['window_complete'] is not None and type(obj['window_complete']) is not bool:raise ValueError('Completeness is true/false/unknown')
    clocks={k:utc(obj[k]) if obj[k] is not None else None for k in
            ('record_version_utc','available_utc','retrieved_utc','max_source_event_utc','window_start_utc','window_end_utc')}
    version,available,retrieved=(clocks[k] for k in ('record_version_utc','available_utc','retrieved_utc'))
    if version and available and version>available:raise ValueError('Record cannot be available before its version exists')
    if available and retrieved and available>retrieved:raise ValueError('Retrieval before claimed availability')
    start,end=clocks['window_start_utc'],clocks['window_end_utc']
    if start and end and start>end:raise ValueError('Reversed source window')
    event=clocks['max_source_event_utc']
    if version and ((event and event>version) or (end and end>version)):
        raise ValueError('Source cannot postdate its derived record version')
    if obj['availability_proof_sha256'] is not None:hash_id(obj['availability_proof_sha256'])
    due=obj['planned_due_utc']
    if due is not None:
        utc(due)
        if obj['semantic_role']!='DECLARED_PLAN':raise ValueError('A future deadline is a plan, not observed future activity')
    blockers=[]
    required_clocks=('record_version_utc','available_utc','retrieved_utc','window_start_utc','window_end_utc')
    if any(clocks[k] is None for k in required_clocks):blockers.append('MISSING_CLOCK_EVIDENCE')
    if obj['event_population_status']=='UNKNOWN' or (obj['event_population_status']=='PRESENT' and event is None):
        blockers.append('EVENT_POPULATION_UNKNOWN')
    if any(clocks[k] is not None and clocks[k]>origin for k in ('max_source_event_utc','window_end_utc')):
        blockers.append('FUTURE_SOURCE_OR_WINDOW')
    if obj['window_complete'] is not True:blockers.append('WINDOW_NOT_PROVEN_COMPLETE')
    if study_mode=='OPERATIONAL_ASOF':
        if version is None or version>origin:blockers.append('RECORD_VERSION_NOT_KNOWN_AT_ORIGIN')
        if available is None or available>origin:blockers.append('NOT_AVAILABLE_AT_ORIGIN')
        if obj['availability_proof_sha256'] is None:blockers.append('NO_AVAILABILITY_PROOF_REFERENCE')
    # Later reconstruction is a different estimand/availability assumption. The
    # review neither certifies it nor disguises it as operational evidence.
    return dict(signal_id=obj['signal_id'],descriptor_id=digest(obj),study_mode=study_mode,
                temporal_metadata_status='COHERENT_CLAIMS_ONLY' if not blockers else 'BLOCKED',
                blockers=sorted(set(blockers)),proof_authenticity='NOT_VERIFIED_BY_THIS_FUNCTION',
                planned_date_is_realization_evidence=False,can_admit_data=False)


ROW_FIELDS={'forecast_id','family_id','role','origin_utc','horizon_days','context_days','label_available_utc'}
ROLES=('train','validation','calibration','test')


def inspect_schedule(rows,*,exposed_families):
    """Operational-as-of schedule; retrospective replay needs separate review."""
    if not isinstance(exposed_families,(list,tuple,set,frozenset)) or any(not isinstance(v,str) or not v for v in exposed_families):raise ValueError('Explicit resolved exposure identities required')
    if not isinstance(rows,list) or not 1<=len(rows)<=256:raise ValueError('Bounded metadata schedule required')
    seen=set();groups={};blockers=[]
    for row in rows:
        exact(row,ROW_FIELDS);hash_id(row['forecast_id'])
        if row['forecast_id'] in seen:raise ValueError('Duplicate forecast identity')
        seen.add(row['forecast_id'])
        if not isinstance(row['family_id'],str) or not row['family_id']:raise ValueError('Family identity required')
        if row['role'] not in ROLES or type(row['context_days']) is not int or row['context_days']!=90:
            raise ValueError('Frozen90-day context and explicit role required')
        endpoint=utc(horizon_endpoint(row['origin_utc'],row['horizon_days']))
        if row['label_available_utc'] is not None and utc(row['label_available_utc'])<endpoint:
            raise ValueError('Horizon label cannot be available before exact endpoint')
        groups.setdefault(row['family_id'],[]).append(row)
        if row['role']=='test' and row['family_id'] in exposed_families:
            blockers.append(dict(code='EXPOSED_FAMILY_IN_CONFIRMATORY_TEST',forecast_id=row['forecast_id']))
    for family,members in groups.items():
        if any(r['role']=='test' for r in members) and any(r['role']!='test' for r in members):
            blockers.append(dict(code='FAMILY_CROSSES_CONFIRMATORY_ROLE',family_id=family))
        for early in members:
            for later in members:
                if ROLES.index(early['role'])>=ROLES.index(later['role']):continue
                # Reuse the existing strict90-day-context purge. Equality is NOT
                # safe: prior label endpoint must precede later context start.
                accepted=purged_training_ids([dict(forecast_id=early['forecast_id'],origin_utc=early['origin_utc'],horizon_days=early['horizon_days'])],later['origin_utc'])
                if not accepted:blockers.append(dict(code='INFORMATION_INTERVAL_OVERLAP',earlier=early['forecast_id'],later=later['forecast_id']))
    # A pooled model also needs prior-role labels to be available before later
    # forecasts from DIFFERENT repositories. Family isolation alone is insufficient.
    for early in rows:
        for later in rows:
            if ROLES.index(early['role'])>=ROLES.index(later['role']):continue
            if early['label_available_utc'] is None:
                blockers.append(dict(code='UNKNOWN_DELAYED_LABEL_AVAILABILITY',forecast_id=early['forecast_id']))
            elif utc(early['label_available_utc'])>utc(later['origin_utc']):
                blockers.append(dict(code='LABEL_NOT_AVAILABLE_BEFORE_NEXT_ROLE',earlier=early['forecast_id'],later=later['forecast_id']))
    missing=sorted(set(ROLES)-{r['role'] for r in rows})
    if missing:blockers.append(dict(code='INCOMPLETE_ROLE_SCHEDULE',missing=missing))
    return dict(status='COHERENT_METADATA_ONLY' if not blockers else 'BLOCKED',rows=len(rows),families=len(groups),
                blockers=blockers,exposure_identity_resolution='REQUIRES_CUSTODIAN_REVIEW',can_start_experiment=False)


def feedback_eligibility(*,origin_utc,horizon_days,label_available_utc,update_utc,domain_matches):
    if type(domain_matches) is not bool:raise ValueError('Explicit domain comparison required')
    endpoint=utc(horizon_endpoint(origin_utc,horizon_days));update=utc(update_utc)
    if label_available_utc is not None and utc(label_available_utc)<endpoint:raise ValueError('Impossible early horizon outcome')
    reasons=[]
    if update<endpoint:reasons.append('HORIZON_NOT_MATURED')
    if label_available_utc is None:reasons.append('UNKNOWN_LABEL_AVAILABILITY')
    elif utc(label_available_utc)>update:reasons.append('LABEL_NOT_YET_AVAILABLE')
    if not domain_matches:reasons.append('MEASUREMENT_DOMAIN_MISMATCH')
    return dict(timing_status='COHERENT_TIMING_ONLY' if not reasons else 'BLOCKED',blockers=reasons,
                permission_to_update_model=False)


def inspect_plan(plan):
    exact(plan,{'version','scope','study_mode','horizons_days','signals','measurement_domain_status',
                'strict_target_history_status','family_resolution_status','signal_provenance_status',
                'preregistration_status','authorization_status','future_data_use_authorized'})
    if plan['version']!=VERSION or plan['scope']!='METADATA_ONLY_NO_DATA_ADMISSION' or plan['study_mode'] not in MODES:
        raise ValueError('Readiness scope/version mismatch')
    if plan['horizons_days']!=[30,60,90] or any(type(v) is not int for v in plan['horizons_days']):raise ValueError('Exact horizons required')
    if not isinstance(plan['signals'],list) or not plan['signals'] or set(plan['signals'])-set(SIGNALS) or len(plan['signals'])!=len(set(plan['signals'])):
        raise ValueError('Unique known signal families required')
    if plan['authorization_status']!='NOT_APPROVED' or plan['future_data_use_authorized'] is not False:
        raise ValueError('This readiness phase cannot grant permissions')
    statuses=('measurement_domain_status','strict_target_history_status','family_resolution_status','signal_provenance_status','preregistration_status')
    for k in statuses:
        if plan[k] not in ('UNKNOWN','BLOCKED','DOCUMENTED_REQUIRES_INDEPENDENT_REVIEW'):
            raise ValueError('Unverified status cannot be promoted to admission')
    return dict(version=VERSION,status='READINESS_PLAN_REVIEWED_ADMISSION_BLOCKED',
                technical_blockers={k:plan[k] for k in statuses},rights_status='NOT_APPROVED',
                collection_authorized=False,real_data_admitted=False,experiment_authorized=False,
                predictive_signal_validated=False,legal_opinion=False)
