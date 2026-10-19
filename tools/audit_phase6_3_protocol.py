"""Post-run protocol audit, not a selector patch or corrected experiment."""
from pathlib import Path
import json
import sys
from forecasting_research.phase6_3.study import verify,verify_prediction_seal


def assess(selection,metrics):
    issues=[]
    for h in (30,60,90):
        head=selection['horizons'][str(h)]
        config=head['configs']['adaptive_persistence']
        if not head['method_safety']['adaptive_persistence'] and config['shrink']!=0:
            issues.append(dict(id='AP_NO_SAFE_FALLBACK_'+str(h),kind='PROTOCOL_DEVIATION',horizon=h,
                observed_config=config,required_action='Protected zero-adjustment AP, not an active unconstrained choice',
                validation_safety=head['risks']['adaptive_persistence'],
                cause="selection.choose uses eligible or candidates; AP has no special protected fallback when all candidates are unverified",
                correction_status='NOT_APPLIED; original registration/model/selection/predictions retained'))
        row=next(r for r in metrics['aggregate'] if r['method']=='adaptive_persistence' and r['partition']=='test'
                 and r['horizon']==h and r['scale']=='all' and r['stratum']=='large_decrease')
        if row['n']<8:
            issues.append(dict(id='MAIN_LARGE_DECREASE_SUPPORT_'+str(h),kind='ESSENTIAL_EVALUATION_UNSUPPORTED',
                               horizon=h,n=row['n'],required_minimum=8,metric_status='UNAVAILABLE' if row['n']==0 else 'EXPLORATORY',
                               correction_status='No cases added, seeds changed or cohort rebuilt after test exposure'))
    return dict(phase_status='PARTIAL' if issues else 'PASS',scope='SYNTHETIC_ENGINEERING_TEST',issues=issues,
                numerical_integrity_separate=True,original_outcome_not_rewritten=True,
                fits=0,forecasts=0,corrected_predictions=0,new_cohorts=0,
                next_action='Separately authorize a versioned selector correction, no-safe-AP regression, and new preregistered cohort with adequate development-planned decrease strata; no execution now')


def audit(root):
    root=Path(root);verify(root);verify_prediction_seal(root)
    return assess(json.loads((root/'selection.json').read_text()),json.loads((root/'metrics.json').read_text()))


if __name__=='__main__': print(json.dumps(audit(sys.argv[1]),sort_keys=True))
