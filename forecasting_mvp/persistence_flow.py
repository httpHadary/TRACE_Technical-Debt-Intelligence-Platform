"""Deterministic, model-free presentation bundles. No collection or training entry points."""
from datetime import date, datetime, timedelta, timezone
import math
from pathlib import Path
import re
import heapq

from contracts import digest, read_json, safe_id, write_json
from .io import artifact_path, file_sha256

VERSION = 'persistence.presentation.v1'
SOURCE_VERSION = 'persistence.observations.v1'
ACTUAL_VERSION = 'persistence.actuals.v1'
COMPONENTS = ('maintainability', 'reliability', 'security')
HORIZONS = {'revision_step': [3, 4, 12], 'elapsed_day': [30, 60, 90]}
TARGET = 'native_total_principal_minutes'


def exact(obj, fields):
    if not isinstance(obj, dict) or set(obj) != set(fields):
        raise ValueError('Exact fields required: ' + ', '.join(sorted(fields)))


def utc(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        raise ValueError('Canonical UTC timestamp required')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def numeric(value, nullable=False):
    if nullable and value is None:
        return None
    if type(value) not in (int, float) or value < 0:
        raise ValueError('Finite nonnegative JSON number required')
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError('Finite nonnegative JSON number required')
    return value


def revision(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', value):
        raise ValueError('Full lowercase revision hash required')
    return value


def total(components):
    exact(components, COMPONENTS)
    values = [numeric(components[k], nullable=True) for k in COMPONENTS]
    if any(v is None for v in values):
        return None
    return numeric(sum(values))


def provenance(value):
    exact(value, ('source_id', 'kind', 'description', 'permission', 'provenance'))
    safe_id(value['source_id'])
    if value['kind'] not in ('SYNTHETIC', 'OPERATOR_PROVIDED'):
        raise ValueError('Explicit source kind required')
    for key in ('description', 'permission', 'provenance'):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError('Explicit source provenance and permission claims required')
    # These are operator claims, never permission granted by this software.
    return value


def derive(source):
    exact(source, ('version', 'source', 'horizons', 'observations'))
    if source['version'] != SOURCE_VERSION:
        raise ValueError('Unsupported observation version')
    provenance(source['source'])
    horizons = source['horizons']
    if not isinstance(horizons, dict) or not horizons or set(horizons) - set(HORIZONS):
        raise ValueError('Registered horizon unit required')
    for unit, values in horizons.items():
        if values != HORIZONS[unit] or any(type(v) is not int for v in values):
            raise ValueError('Exact registered horizon values required')
    if not isinstance(source['observations'], list) or not source['observations']:
        raise ValueError('Observations required')
    identities, revisions, indices, times = set(), set(), set(), set()
    groups = {}
    for row in source['observations']:
        exact(row, ('observation_id', 'repository_id', 'revision', 'revision_index', 'observed_utc',
                    'domain_id', 'scope_id', 'components'))
        for key in ('observation_id', 'repository_id', 'domain_id', 'scope_id'):
            safe_id(row[key])
        revision(row['revision'])
        if type(row['revision_index']) is not int or row['revision_index'] < 0:
            raise ValueError('Nonnegative revision index required')
        utc(row['observed_utc'])
        total(row['components'])
        for seen, identity in ((identities, row['observation_id']),
                               (revisions, (row['repository_id'], row['revision'])),
                               (indices, (row['repository_id'], row['revision_index'])),
                               (times, (row['repository_id'], row['observed_utc']))):
            if identity in seen:
                raise ValueError('Duplicate observation identity/revision/index/time')
            seen.add(identity)
        groups.setdefault(row['repository_id'], []).append(row)
    history, forecasts = [], []
    for repo, rows in sorted(groups.items()):
        rows.sort(key=lambda r: r['revision_index'])
        previous = None
        for row in rows:
            stock = total(row['components'])
            comparable = (previous is not None and all(row[k] == previous[k] for k in ('domain_id', 'scope_id'))
                          and stock is not None and total(previous['components']) is not None)
            if previous and utc(row['observed_utc']) <= utc(previous['observed_utc']):
                raise ValueError('Observation UTC order contradicts revision order')
            history.append(dict(row, stock_minutes=stock,
                                measured_change_minutes=stock-total(previous['components']) if comparable else None,
                                change_status='MEASURED' if comparable else 'INCOMPARABLE' if previous else 'NO_PREVIOUS_OBSERVATION'))
            previous = row
        origin = history[-1]
        for unit, values in sorted(horizons.items()):
            for horizon in values:
                identity = dict(source_id=digest(source['source']), origin=origin['observation_id'],
                                origin_identity=digest(rows[-1]), target=TARGET, unit=unit, horizon=horizon)
                stock = origin['stock_minutes']
                endpoint_utc = None
                if unit == 'elapsed_day':
                    try:
                        endpoint_utc = (utc(origin['observed_utc'])+timedelta(days=horizon)).strftime('%Y-%m-%dT%H:%M:%SZ')
                    except OverflowError as exc:
                        raise ValueError('Calendar endpoint exceeds supported UTC range') from exc
                forecasts.append(dict(forecast_id=digest(identity), repository_id=repo, model='persistence',
                                      target=TARGET, origin_observation_id=origin['observation_id'],
                                      origin_revision=origin['revision'], origin_utc=origin['observed_utc'],
                                      origin_revision_index=origin['revision_index'], origin_components=origin['components'],
                                      domain_id=origin['domain_id'], scope_id=origin['scope_id'],
                                      horizon_unit=unit, horizon=horizon,
                                      endpoint_revision_index=origin['revision_index']+horizon if unit == 'revision_step' else None,
                                      endpoint_utc=endpoint_utc,
                                      origin_stock_minutes=stock, prediction_minutes=stock,
                                      predicted_change_minutes=0 if stock is not None else None,
                                      interval_lower=None, interval_upper=None,
                                      status='AVAILABLE' if stock is not None else 'UNAVAILABLE',
                                      unavailable_reason=None if stock is not None else 'LATEST_OBSERVATION_MISSING_COMPONENT'))
    return history, forecasts


def evaluate(forecasts, actuals):
    by_id = {f['forecast_id']: f for f in forecasts}
    measured = {}
    if actuals is not None:
        exact(actuals, ('version', 'source', 'actuals'))
        if actuals['version'] != ACTUAL_VERSION:
            raise ValueError('Unsupported actual projection version')
        provenance(actuals['source'])
        if not isinstance(actuals['actuals'], list):
            raise ValueError('Actual list required')
        endpoints = {}
        for row in actuals['actuals']:
            exact(row, ('forecast_id', 'target', 'repository_id', 'origin_observation_id', 'domain_id', 'scope_id',
                        'horizon_unit', 'horizon', 'endpoint_revision', 'endpoint_revision_index', 'observed_utc', 'components'))
            f = by_id.get(row['forecast_id'])
            if f is None or row['forecast_id'] in measured:
                raise ValueError('Wrong or duplicate actual target')
            for key in ('target', 'repository_id', 'origin_observation_id', 'domain_id', 'scope_id', 'horizon_unit', 'horizon'):
                if type(row[key]) is not type(f[key]) or row[key] != f[key]:
                    raise ValueError('Actual target/domain/clock mismatch')
            revision(row['endpoint_revision'])
            if utc(row['observed_utc']) <= utc(f['origin_utc']):
                raise ValueError('Actual endpoint must follow origin')
            if type(row['endpoint_revision_index']) is not int or row['endpoint_revision_index'] < 0:
                raise ValueError('Actual endpoint revision index required')
            if f['horizon_unit'] == 'revision_step':
                if row['endpoint_revision_index'] != f['endpoint_revision_index'] or row['endpoint_revision'] == f['origin_revision']:
                    raise ValueError('Wrong actual revision endpoint')
            elif row['observed_utc'] != f['endpoint_utc']:
                raise ValueError('Actual must match exact UTC horizon')
            if row['endpoint_revision_index'] < f['origin_revision_index']:
                raise ValueError('Actual revision cannot precede origin')
            same_revision = row['endpoint_revision'] == f['origin_revision']
            if same_revision != (row['endpoint_revision_index'] == f['origin_revision_index']):
                raise ValueError('Actual revision/index identity mismatch')
            if same_revision and row['components'] != f['origin_components']:
                raise ValueError('Unchanged selected revision must retain origin components')
            stock = total(row['components'])
            if stock is None:
                raise ValueError('Actual must have measured components')
            endpoint = (row['repository_id'], row['endpoint_revision'])
            # Calendar evaluation instants may select the same unchanged revision.
            value = (row['endpoint_revision_index'], row['domain_id'], row['scope_id'], row['components'])
            if endpoint in endpoints and endpoints[endpoint] != value:
                raise ValueError('Inconsistent actual endpoint')
            endpoints[endpoint] = value
            index_key = (row['repository_id'], row['endpoint_revision_index'])
            if index_key in endpoints and endpoints[index_key] != row['endpoint_revision']:
                raise ValueError('Inconsistent actual revision index')
            endpoints[index_key] = row['endpoint_revision']
            measured[row['forecast_id']] = (row, stock)
        # All clocks select states from the same repository revision sequence.
        # Later evaluation instants may reuse a state, but cannot move backward.
        previous = {}
        for row in sorted(actuals['actuals'], key=lambda r: (r['repository_id'], r['observed_utc'])):
            prior = previous.get(row['repository_id'])
            if prior is not None and (
                    row['endpoint_revision_index'] < prior['endpoint_revision_index'] or
                    (row['observed_utc'] == prior['observed_utc'] and
                     row['endpoint_revision_index'] != prior['endpoint_revision_index'])):
                raise ValueError('Actual chronology contradicts revision sequence across horizons/clocks')
            previous[row['repository_id']] = row
    results = []
    for f in forecasts:
        match = measured.get(f['forecast_id'])
        stock = match[1] if match else None
        available = f['status'] == 'AVAILABLE'
        error = f['prediction_minutes']-stock if match and available else None
        results.append(dict(forecast_id=f['forecast_id'], repository_id=f['repository_id'],
                            horizon_unit=f['horizon_unit'], horizon=f['horizon'],
                            status='MEASURED' if match and available else 'UNAVAILABLE' if not available else 'PENDING',
                            actual_minutes=stock, actual_change_minutes=stock-f['origin_stock_minutes'] if match and available else None,
                            error_minutes=error, absolute_error_minutes=abs(error) if error is not None else None,
                            endpoint_revision=match[0]['endpoint_revision'] if match else None,
                            observed_utc=match[0]['observed_utc'] if match else None))
    return results


def _seal(root):
    return {'status': 'SEALED', 'model': 'persistence',
            'forecasts_sha256': file_sha256(root/'forecasts.json'), 'actuals_loaded': False}


def evaluation_summary(forecasts, evaluations):
    """Deterministic descriptive errors, never a claim of current accuracy."""
    reports = []
    for unit, horizon in sorted({(f['horizon_unit'], f['horizon']) for f in forecasts}):
        fs = [f for f in forecasts if (f['horizon_unit'], f['horizon']) == (unit, horizon)]
        rows = [e for e in evaluations if (e['horizon_unit'], e['horizon']) == (unit, horizon)]
        measured = [e for e in rows if e['status'] == 'MEASURED']
        available = sum(f['status'] == 'AVAILABLE' for f in fs)
        subsets = {}
        for name, predicate in (
            ('all', lambda d: True), ('changed', lambda d: d != 0),
            ('stable', lambda d: d == 0), ('increase', lambda d: d > 0), ('decrease', lambda d: d < 0),
        ):
            selected = [r for r in measured if predicate(r['actual_change_minutes'])]
            repositories = []
            for repo in sorted({r['repository_id'] for r in selected}):
                errors = [r['error_minutes'] for r in selected if r['repository_id'] == repo]
                repositories.append(dict(repository_id=repo, count=len(errors),
                    mae_minutes=math.fsum(abs(e)/len(errors) for e in errors),
                    rmse_minutes=math.hypot(*(e/math.sqrt(len(errors)) for e in errors))))
            errors = [r['error_minutes'] for r in selected]
            subsets[name] = dict(count=len(errors), repositories=repositories,
                macro_mae_minutes=math.fsum(r['mae_minutes']/len(repositories) for r in repositories) if repositories else None,
                macro_rmse_minutes=math.fsum(r['rmse_minutes']/len(repositories) for r in repositories) if repositories else None,
                pooled_mae_minutes=math.fsum(abs(e)/len(errors) for e in errors) if errors else None,
                pooled_rmse_minutes=math.hypot(*(e/math.sqrt(len(errors)) for e in errors)) if errors else None)
        reports.append(dict(horizon_unit=unit, horizon=horizon, forecasts=len(fs), available_forecasts=available,
            measured_actuals=len(measured), pending=sum(r['status'] == 'PENDING' for r in rows),
            unavailable=sum(r['status'] == 'UNAVAILABLE' for r in rows),
            actual_coverage=len(measured)/available if available else None,
            subsets=subsets, current_accuracy='UNVALIDATED'))
    return reports


def _finish(root, kind, metadata):
    write_json(root/'evaluation_summary.json', evaluation_summary(read_json(root/'forecasts.json'), read_json(root/'evaluations.json')))
    files = sorted(p.name for p in root.iterdir())
    artifacts = {f: file_sha256(root/f) for f in files}
    record = dict(version=VERSION, status='COMPLETE', kind=kind, model='persistence',
                  bundle_id=digest(dict(artifacts=artifacts, metadata=metadata, kind=kind)), artifacts=artifacts,
                  metadata=metadata, permission_status='SOURCE_CLAIMS_ONLY_NOT_GRANTED_BY_IMPORT',
                  current_accuracy='UNVALIDATED')
    write_json(root/'manifest.json', record)
    try:
        verify_presentation(root)
    except Exception:
        (root/'manifest.json').unlink()
        raise
    return record


def _new_output(output):
    output = Path(output).absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()  # Exclusive ownership. COMPLETE manifest is published last.
    return output


def build(source_path, output, actuals_path=None):
    source = read_json(source_path)
    history, forecasts = derive(source)
    root = _new_output(output)
    try:
        write_json(root/'source.json', source)
        write_json(root/'history.json', history)
        write_json(root/'forecasts.json', forecasts)
        write_json(root/'prediction_seal.json', _seal(root))
        # Deliberately open optional evaluator data only after predictions are on disk and sealed.
        actuals = read_json(actuals_path) if actuals_path is not None else None
        evaluations = evaluate(forecasts, actuals)
        write_json(root/'actuals.json', actuals)
        write_json(root/'evaluations.json', evaluations)
        return _finish(root, 'OBSERVATIONS', dict(source=source['source'],
                       evidence='SOFTWARE_VALIDATION_ONLY' if source['source']['kind'] == 'SYNTHETIC' else 'OPERATOR_PROVIDED_UNVALIDATED'))
    except Exception:
        # Preserve sealed failed evidence for inspection; absence of COMPLETE
        # prevents this directory from being served as a published bundle.
        raise


def _day(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError('Canonical date-only historical clock required')
    return date.fromisoformat(value)


def archive_predictions(registration, requests, predictions):
    """Derive only origin-known records, before opening any scored outcomes."""
    if registration.get('horizons_revision_steps') != [3, 4, 12] or registration.get('target') != 'total_principal = maintainability + reliability + security estimated remediation minutes':
        raise ValueError('Unsupported historical target/horizons')
    if requests.get('clock') != registration.get('clock'):
        raise ValueError('Historical request clock mismatch')
    if not isinstance(requests.get('contexts'), list) or not requests['contexts']:
        raise ValueError('Historical contexts required')
    contexts, nodes, predecessors, successors = {}, {}, {}, {}
    for c in requests['contexts']:
        safe_id(c['context_id']); safe_id(c['repository_id'])
        if c['context_id'] in contexts:
            raise ValueError('Duplicate historical context')
        n = len(c['past_values'])
        if n < 1 or len(c['history_shas']) != n or len(c['history_commit_dates']) != n or len(set(c['history_shas'])) != n:
            raise ValueError('Historical context membership mismatch')
        if c['history_shas'][-1] != c['origin_sha'] or c['history_commit_dates'][-1] != c['origin_commit_date']:
            raise ValueError('Historical origin mismatch')
        previous = None
        for sha, day, value in zip(c['history_shas'], c['history_commit_dates'], c['past_values']):
            revision(sha); _day(day); numeric(value)
            key = (c['repository_id'], sha)
            if key in nodes and nodes[key] != (day, value):
                raise ValueError('Inconsistent historical observation')
            nodes[key] = (day, value)
            if previous is not None:
                if key in predecessors and predecessors[key] != previous:
                    raise ValueError('Inconsistent historical predecessor')
                if previous in successors and successors[previous] != key:
                    raise ValueError('Inconsistent historical successor')
                predecessors[key] = previous
                successors[previous] = key
            previous = key
        contexts[c['context_id']] = c
    # Contexts can overlap and arrive in any order. Only explicit consecutive
    # sequence edges support a measured change; disjoint chains stay explicit.
    ready = [(key[0], nodes[key][0], key[1]) for key in nodes if key not in predecessors]
    heapq.heapify(ready)
    history = []
    while ready:
        repo, day, sha = heapq.heappop(ready)
        key = (repo, sha)
        value = nodes[key][1]
        previous = predecessors.get(key)
        history.append(dict(repository_id=repo, revision=sha, commit_date=day,
                            stock_minutes=value, components=None, domain_id='archived-analyzer-defined',
                            scope_id='archived-principal', measured_change_minutes=value-nodes[previous][1] if previous else None,
                            change_status='ARCHIVED_SEQUENCE_MEASURED' if previous else 'NO_PREVIOUS_OBSERVATION'))
        following = successors.get(key)
        if following:
            heapq.heappush(ready, (following[0], nodes[following][0], following[1]))
    if len(history) != len(nodes):
        raise ValueError('Cyclic historical sequence')
    pred_map = {}
    for row in predictions:
        if row.get('method') != 'persistence':
            raise ValueError('Non-persistence export forbidden')
        fid = safe_id(row['forecast_id'])
        if fid in pred_map:
            raise ValueError('Duplicate historical endpoint')
        pred_map[fid] = row
    expected = {f'{cid}-{h}' for cid in contexts for h in (3, 4, 12)}
    if set(pred_map) != expected:
        raise ValueError('Historical request/prediction membership mismatch')
    forecasts = []
    for fid, p in sorted(pred_map.items()):
        c = contexts.get(p['context_id'])
        h = p['horizon_revision_steps']
        if c is None or type(h) is not int or h not in (3, 4, 12) or fid != f"{c['context_id']}-{h}" or p['repository_id'] != c['repository_id']:
            raise ValueError('Historical prediction identity mismatch')
        stock = numeric(c['past_values'][-1])
        for name in ('current', 'prediction', 'raw_prediction', 'signed_delta', 'raw_signed_delta'):
            numeric(p.get(name))
        if any(p.get(k) != v for k, v in {'current': stock, 'prediction': stock, 'raw_prediction': stock,
                                         'signed_delta': 0, 'raw_signed_delta': 0, 'q10': None, 'q90': None}.items()):
            raise ValueError('Historical persistence formula/interval mismatch')
        forecasts.append(dict(forecast_id=fid, context_id=c['context_id'], repository_id=c['repository_id'], model='persistence',
                              target=TARGET, origin_observation_id=c['context_id'], origin_revision=c['origin_sha'],
                              origin_commit_date=c['origin_commit_date'], origin_utc=None,
                              domain_id='archived-analyzer-defined', scope_id='archived-principal',
                              horizon_unit='revision_step', horizon=h, endpoint_utc=None,
                              origin_stock_minutes=stock, prediction_minutes=stock,
                              predicted_change_minutes=0, interval_lower=None, interval_upper=None,
                              status='AVAILABLE', unavailable_reason=None))
    position = {(r['repository_id'], r['revision']): i for i, r in enumerate(history)}
    forecasts.sort(key=lambda f: (f['repository_id'], position[f['repository_id'], f['origin_revision']], f['horizon']))
    return history, forecasts


def archive_evaluations(history, forecasts, predictions, scores, requests):
    pred_map = {p['forecast_id']: p for p in predictions}
    score_map = {}
    for row in scores:
        if row.get('method') != 'persistence':
            raise ValueError('Non-persistence export forbidden')
        fid = row['forecast_id']
        if fid in score_map:
            raise ValueError('Duplicate historical endpoint')
        score_map[fid] = row
    if set(score_map) != set(pred_map):
        raise ValueError('Historical score membership mismatch')
    # Use explicit context edges, never chronological proximity in the merged
    # history: adjacent displayed rows can belong to disconnected sequences.
    successors, predecessors, nodes = {}, set(), set()
    for context in requests['contexts']:
        keys = [(context['repository_id'], sha) for sha in context['history_shas']]
        nodes.update(keys)
        for left, right in zip(keys, keys[1:]):
            successors[left] = right
            predecessors.add(right)
    positions, chains = {}, {}
    for start in sorted(nodes-predecessors):
        chain, node = [], start
        while node is not None:
            positions[node] = (start, len(chain))
            chain.append(node)
            node = successors.get(node)
        chains[start] = chain
    seen = {(r['repository_id'], r['revision']): (r['commit_date'], r['stock_minutes']) for r in history}
    evaluations = []
    for f in forecasts:
        s = score_map[f['forecast_id']]
        if any(s.get(k) != v for k, v in pred_map[f['forecast_id']].items()):
            raise ValueError('Historical scored prediction differs from sealed prediction')
        actual = numeric(s['actual'])
        revision(s['endpoint_sha'])
        elapsed = s['elapsed_commit_date_days']
        if type(elapsed) is not int or elapsed < 0 or s['endpoint_sha'] == f['origin_revision'] or (_day(s['endpoint_commit_date'])-_day(f['origin_commit_date'])).days != elapsed:
            raise ValueError('Historical endpoint/date exposure mismatch')
        key = (f['repository_id'], s['endpoint_sha'])
        chain_id, origin_position = positions[f['repository_id'], f['origin_revision']]
        target_position = origin_position+f['horizon']
        chain = chains[chain_id]
        endpoint_position = positions.get(key)
        if ((target_position < len(chain) and key != chain[target_position]) or
                (endpoint_position is not None and endpoint_position[0] == chain_id and
                 endpoint_position[1]-origin_position != f['horizon'])):
            raise ValueError('Historical endpoint contradicts explicit revision-step distance')
        if key in seen and seen[key] != (s['endpoint_commit_date'], actual):
            raise ValueError('Historical actual contradicts observed endpoint')
        seen[key] = (s['endpoint_commit_date'], actual)
        error = f['prediction_minutes']-actual
        evaluations.append(dict(forecast_id=f['forecast_id'], repository_id=f['repository_id'], horizon_unit='revision_step', horizon=f['horizon'],
                                status='MEASURED', actual_minutes=actual, actual_change_minutes=actual-f['origin_stock_minutes'],
                                error_minutes=error, absolute_error_minutes=abs(error),
                                endpoint_revision=s['endpoint_sha'], endpoint_commit_date=s['endpoint_commit_date'],
                                elapsed_commit_date_days=elapsed))
    return evaluations


def archive_projection(registration, requests, predictions, scores):
    """Validate the original principal contracts without a research runner."""
    history, forecasts = archive_predictions(registration, requests, predictions)
    return history, forecasts, archive_evaluations(history, forecasts, predictions, scores, requests)


def import_historical(bundle, output):
    source = Path(bundle).absolute()
    if source.is_symlink():
        raise ValueError('Symlink bundle forbidden')
    manifest_path = artifact_path(source, 'artifact_manifest.json')
    manifest = read_json(manifest_path)
    files = manifest.get('files')
    required = {'request_seal.json', 'prediction_seal.json', 'requests.json', 'predictions.json', 'scored_predictions.json', 'registration.json'}
    if not isinstance(files, dict) or not required <= set(files):
        raise ValueError('Historical artifact manifest membership required')
    for name, item in files.items():
        exact(item, ('bytes', 'sha256'))
        path = artifact_path(source, name)
        if type(item['bytes']) is not int or item['bytes'] != path.stat().st_size or file_sha256(path) != item['sha256']:
            raise ValueError('Historical artifact hash/size mismatch: '+name)
    for seal_name, names in (('request_seal.json', ['requests.json']), ('prediction_seal.json', ['predictions.json', 'registration.json'])):
        if read_json(artifact_path(source, seal_name)) != {n: file_sha256(artifact_path(source, n)) for n in names}:
            raise ValueError('Historical seal mismatch')
    registration = read_json(artifact_path(source, 'registration.json'))
    requests = read_json(artifact_path(source, 'requests.json'))
    # Projection contains only origin-known context fields, never covariates or another model.
    keys = ('context_id', 'repository_id', 'past_values', 'history_shas', 'history_commit_dates', 'origin_sha', 'origin_commit_date')
    requests = dict(clock=requests['clock'], contexts=[{k: c[k] for k in keys} for c in requests['contexts']])
    all_predictions = read_json(artifact_path(source, 'predictions.json'))
    predictions = [p for p in all_predictions if p.get('method') == 'persistence']
    if len(predictions) != 678:
        raise ValueError('Expected exactly 678 original persistence endpoints')
    history, forecasts = archive_predictions(registration, requests, predictions)
    root = _new_output(output)
    try:
        # Seal the prediction projection before opening scored outcomes.
        write_json(root/'archive_origins.json', dict(registration=registration, requests=requests, predictions=predictions))
        write_json(root/'archive_origin_seal.json', {'sha256': file_sha256(root/'archive_origins.json'), 'actuals_loaded': False})
        write_json(root/'history.json', history)
        write_json(root/'forecasts.json', forecasts)
        write_json(root/'prediction_seal.json', _seal(root))
        scores = [p for p in read_json(artifact_path(source, 'scored_predictions.json')) if p.get('method') == 'persistence']
        evaluations = archive_evaluations(history, forecasts, predictions, scores, requests)
        write_json(root/'archive_scores.json', scores)
        write_json(root/'evaluations.json', evaluations)
        metadata = dict(evidence=registration.get('evidence'), source_manifest_sha256=file_sha256(manifest_path),
                        source_files={n: files[n] for n in sorted(required)}, registration=registration,
                        component_status='NOT_PRESENT_IN_ARCHIVED_CONTEXTS', date_precision='DATE_ONLY_NOT_UTC',
                        permission=registration.get('rights', 'NOT_ESTABLISHED'),
                        provenance=registration.get('provenance', 'NOT_ESTABLISHED'))
        return _finish(root, 'HISTORICAL_PRINCIPAL', metadata)
    except Exception:
        raise


def verify_presentation(bundle):
    root = Path(bundle).absolute()
    if root.is_symlink():
        raise ValueError('Symlink bundle forbidden')
    manifest = read_json(artifact_path(root, 'manifest.json'))
    exact(manifest, ('version', 'status', 'kind', 'model', 'bundle_id', 'artifacts', 'metadata', 'permission_status', 'current_accuracy'))
    if manifest['version'] != VERSION or manifest['status'] != 'COMPLETE' or manifest['model'] != 'persistence' or manifest['current_accuracy'] != 'UNVALIDATED' or manifest['permission_status'] != 'SOURCE_CLAIMS_ONLY_NOT_GRANTED_BY_IMPORT':
        raise ValueError('Unsupported/incomplete presentation bundle')
    common = {'history.json', 'forecasts.json', 'prediction_seal.json', 'evaluations.json', 'evaluation_summary.json'}
    if manifest['kind'] == 'OBSERVATIONS':
        required = common | {'source.json', 'actuals.json'}
    elif manifest['kind'] == 'HISTORICAL_PRINCIPAL':
        required = common | {'archive_origins.json', 'archive_origin_seal.json', 'archive_scores.json'}
    else:
        raise ValueError('Unknown presentation kind')
    if not isinstance(manifest['artifacts'], dict) or set(manifest['artifacts']) != required:
        raise ValueError('Exact presentation artifact membership required')
    if {p.name for p in root.iterdir()} != required | {'manifest.json'}:
        raise ValueError('Unexpected presentation artifact membership')
    for name, expected in manifest['artifacts'].items():
        if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
            raise ValueError('Canonical artifact SHA-256 required')
        if file_sha256(artifact_path(root, name)) != expected:
            raise ValueError('Presentation artifact hash mismatch: '+name)
    if manifest['bundle_id'] != digest(dict(artifacts=manifest['artifacts'], metadata=manifest['metadata'], kind=manifest['kind'])):
        raise ValueError('Presentation bundle identity mismatch')
    load = lambda name: read_json(artifact_path(root, name+'.json'))
    forecasts = load('forecasts')
    if load('prediction_seal') != _seal(root):
        raise ValueError('Presentation prediction seal mismatch')
    if manifest['kind'] == 'OBSERVATIONS':
        source = load('source')
        history, expected_forecasts = derive(source)
        evaluations = evaluate(expected_forecasts, load('actuals'))
        expected_metadata = dict(source=source['source'], evidence='SOFTWARE_VALIDATION_ONLY' if source['source']['kind'] == 'SYNTHETIC' else 'OPERATOR_PROVIDED_UNVALIDATED')
        if manifest['metadata'] != expected_metadata:
            raise ValueError('Source provenance mismatch')
    else:
        origins = load('archive_origins')
        if load('archive_origin_seal') != dict(sha256=file_sha256(root/'archive_origins.json'), actuals_loaded=False):
            raise ValueError('Historical projection seal mismatch')
        history, expected_forecasts, evaluations = archive_projection(origins['registration'], origins['requests'], origins['predictions'], load('archive_scores'))
        if len(expected_forecasts) != 678 or manifest['metadata']['registration'] != origins['registration']:
            raise ValueError('Historical projection identity mismatch')
        exact(manifest['metadata'], ('evidence', 'source_manifest_sha256', 'source_files', 'registration', 'component_status', 'date_precision', 'permission', 'provenance'))
        if (manifest['metadata']['evidence'] != origins['registration'].get('evidence') or
                manifest['metadata']['permission'] != origins['registration'].get('rights', 'NOT_ESTABLISHED') or
                manifest['metadata']['provenance'] != origins['registration'].get('provenance', 'NOT_ESTABLISHED') or
                manifest['metadata']['component_status'] != 'NOT_PRESENT_IN_ARCHIVED_CONTEXTS' or
                manifest['metadata']['date_precision'] != 'DATE_ONLY_NOT_UTC'):
            raise ValueError('Historical provenance mismatch')
    if history != load('history') or expected_forecasts != forecasts or evaluations != load('evaluations'):
        raise ValueError('Presentation semantics mismatch')
    if load('evaluation_summary') != evaluation_summary(forecasts, evaluations):
        raise ValueError('Presentation evaluation summary mismatch')
    return manifest


def load_presentation(bundle):
    manifest = verify_presentation(bundle)
    root = Path(bundle)
    return dict(manifest=manifest, **{k: read_json(artifact_path(root, k+'.json')) for k in ('history', 'forecasts', 'evaluations', 'evaluation_summary')})
