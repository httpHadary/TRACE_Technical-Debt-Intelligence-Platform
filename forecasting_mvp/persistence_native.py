"""Additive metric/language-aware v2 lane over the unchanged persistence formula."""
from contracts import digest
from forecasting_multilanguage.native_project import (SOURCE_VERSION, TARGETS, UNIT, validate_admission)
from . import persistence_flow as flow

VERSION = 'persistence.presentation.v2'
ACTUAL_VERSION = 'persistence.actuals.v2'


def stock(components, target):
    flow.total(components)  # Validate every provided component, including unselected ones.
    return components['maintainability'] if target == 'native_sqale_index_minutes' else flow.total(components)


def validate_source(source):
    flow.exact(source, ('version', 'source', 'target', 'unit', 'horizons', 'admission', 'observations'))
    if source['version'] != SOURCE_VERSION or source['target'] not in TARGETS or source['unit'] != UNIT:
        raise ValueError('Unsupported native observation version/target/unit')
    flow.provenance(source['source'])
    expected = [dict(row, observation_id=digest(dict(target=source['target'], row=row)))
                for row in validate_admission(source['admission'])]
    if len({r['observed_utc'] for r in expected}) != len(expected):
        raise ValueError('Native measured commits sharing a UTC second are blocked by the persistence clock contract; timestamps are never adjusted')
    if source['observations'] != expected:
        raise ValueError('Native observations/evidence/target identity mismatch')
    return dict(version=flow.SOURCE_VERSION, source=source['source'], horizons=source['horizons'],
                observations=[{k: v for k, v in row.items() if k != 'native'} for row in expected])


def derive(source):
    projection = validate_source(source)
    target = source['target']
    history, forecasts = flow.derive(projection, _target=target, _stock=lambda c: stock(c, target))
    by_id = {r['observation_id']: r['native'] for r in source['observations']}
    for row in history:
        row.update(target=target, unit=UNIT, native=by_id[row['observation_id']])
    for row in forecasts:
        row.update(unit=UNIT, native=by_id[row['origin_observation_id']])
    return history, forecasts


def evaluate(forecasts, actuals):
    target = forecasts[0]['target']
    if any(f['target'] != target for f in forecasts): raise ValueError('One native target per bundle required')
    projection = None
    if actuals is not None:
        flow.exact(actuals, ('version', 'source', 'target', 'unit', 'admission', 'actuals'))
        if actuals['version'] != ACTUAL_VERSION or actuals['target'] != target or actuals['unit'] != UNIT:
            raise ValueError('Actual target/version/unit mismatch')
        admitted = validate_admission(actuals['admission'])
        sequence = actuals['admission']['revision_sequence']
        for f in forecasts:
            if admitted[0]['native']['project_key'] != f['native']['project_key']:
                raise ValueError('Actual native project differs from sealed origin')
            if digest(sequence[:f['origin_revision_index']+1]) != f['native']['lineage_prefix_sha256']:
                raise ValueError('Actual Git lineage differs from sealed origin')
        states = {(r['repository_id'], r['revision']): r for r in admitted}
        rows = []
        for row in actuals['actuals']:
            flow.exact(row, ('forecast_id', 'target', 'repository_id', 'origin_observation_id', 'domain_id', 'scope_id',
                             'horizon_unit', 'horizon', 'endpoint_revision', 'endpoint_revision_index', 'observed_utc', 'components', 'native'))
            measured = states.get((row['repository_id'], row['endpoint_revision']))
            if measured is None or any(row[k] != measured[k] for k in ('domain_id', 'scope_id', 'components', 'native')) or row['endpoint_revision_index'] != measured['revision_index']:
                raise ValueError('Actual native measurement binding mismatch')
            selected = [state for state in sequence if flow.utc(state['timestamp']) <= flow.utc(row['observed_utc'])]
            if not selected or selected[-1]['sha'] != row['endpoint_revision']:
                raise ValueError('Actual must select exact Git state at evaluation instant; no stale measurement')
            if flow.utc(row['observed_utc']) > flow.utc(actuals['admission']['registration']['ref_observed_utc']):
                raise ValueError('Actual cutoff outside archived ref evidence')
            if flow.utc(row['observed_utc']) < flow.utc(measured['observed_utc']):
                raise ValueError('Actual evaluation instant precedes measured source state')
            rows.append({k: v for k, v in row.items() if k != 'native'})
        projection = dict(version=flow.ACTUAL_VERSION, source=actuals['source'], actuals=rows)
    results = flow.evaluate(forecasts, projection, _stock=lambda c: stock(c, target))
    for row, f in zip(results, forecasts):
        row.update(target=target, unit=UNIT, domain_id=f['domain_id'], scope_id=f['scope_id'], native=f['native'],
                   actual_native=next((r['native'] for r in actuals['actuals'] if r['forecast_id'] == f['forecast_id']), None) if actuals else None)
    return results


def metadata(source):
    return dict(source=source['source'], target=source['target'], unit=UNIT,
                evidence='SOFTWARE_VALIDATION_ONLY' if source['source']['kind'] == 'SYNTHETIC' else 'OPERATOR_PROVIDED_UNVALIDATED',
                source_evidence_sha256=digest(source['admission']),
                authenticity='SOURCE_CLAIMS_AND_LOCAL_GIT_BINDING_NOT_INDEPENDENT_AUTHENTICATION')
