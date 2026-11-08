"""Strict offline native-project exports. All source rights/authenticity are claims.

No scanner, network, checkout, or file-level debt aggregation is performed here.
See NATIVE_PROJECT.md for the exact versioned archive and envelope contracts.
"""
from dataclasses import asdict
from pathlib import Path, PurePosixPath
import hashlib
import re

from contracts import read_json, source_path, safe_id
from forecasting_mvp.io import artifact_path
from forecasting_mvp.persistence_flow import exact, numeric, provenance, utc
from .contracts import analyzer_domain, digest, hash_id, raw_measure, revision
from .git_events import GitArchive, git
from .registry import SUFFIXES, language_distribution, language_family

ARCHIVE_VERSION = 'native.project.archive.v1'
SOURCE_VERSION = 'persistence.observations.v2'
UNIT = 'estimated_remediation_minutes'
TARGETS = {'native_sqale_index_minutes': ('sqale_index',),
           'native_total_principal_minutes': ('sqale_index', 'reliability_remediation_effort', 'security_remediation_effort')}
METRICS = ('sqale_index', 'reliability_remediation_effort', 'security_remediation_effort')
PROGRAMMING = {'java', 'py', 'js', 'ts'}
ANCILLARY = {'.xml': 'xml', '.css': 'css', '.html': 'web', '.htm': 'web', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml'}
ROLES = ('measures', 'inventory', 'coverage', 'files', 'scanner', 'ce')
BINDING = ('project_key', 'analysis_id', 'revision', 'source_tree_sha')


def language(path):
    source_path(path)
    suffix = PurePosixPath(path).suffix.lower()
    return SUFFIXES.get(suffix) or ANCILLARY.get(suffix)


def scoped(path, scope):
    return (any(root == '.' or path.startswith(root + '/') for root in scope['roots'])
            and not any(path == p or path.startswith(p + '/') for p in scope['excluded_paths']))


def registration(value):
    exact(value, ('repository_id', 'family_id', 'canonical_url', 'tip_sha', 'ref_observed_utc', 'declared_languages', 'scope'))
    safe_id(value['repository_id']); safe_id(value['family_id'])
    if not isinstance(value['canonical_url'], str) or not value['canonical_url'].startswith('https://') or '@' in value['canonical_url']:
        raise ValueError('Credential-free canonical HTTPS source claim required')
    revision(value['tip_sha']); utc(value['ref_observed_utc'])
    langs = value['declared_languages']
    if not isinstance(langs, list) or not langs or len(langs) != len(set(langs)) or set(langs) - PROGRAMMING:
        raise ValueError('Unique supported programming languages required')
    scope = value['scope']
    exact(scope, ('roots', 'excluded_paths', 'review_status', 'reviewer'))
    for key in ('roots', 'excluded_paths'):
        if not isinstance(scope[key], list) or len(scope[key]) != len(set(scope[key])):
            raise ValueError('Unique explicit scope paths required')
        for path in scope[key]:
            if key != 'roots' or path != '.': source_path(path)
    if not scope['roots'] or scope['review_status'] != 'REVIEWED_NO_UNRESOLVED_GENERATED_VENDOR_OR_NONCODE' or not isinstance(scope['reviewer'], str) or not scope['reviewer'].strip():
        raise ValueError('Explicit complete content/scope review claim required')
    return value


def _domain(manifest):
    domain = analyzer_domain(manifest)
    if domain['status'] != 'COMPLETE':
        raise ValueError('Incomplete analyzer domain: ' + ','.join(domain['missing_fields']))
    if manifest['metric_mode'] != 'STANDARD' or manifest['metric_semantics'] != 'native_standard_remediation_minutes':
        raise ValueError('Only STANDARD native remediation minutes are supported; no MQR conversion')
    return domain


def _analyzers(manifest, languages):
    supported = set()
    for plugin in manifest['plugins']:
        lang = plugin['language']
        supported.update(('js', 'ts') if lang in ('js', 'javascript') else (lang,))
    if set(languages) - supported:
        raise ValueError('Missing installed analyzer for native language coverage')


def _entry(entry, reg, manifest, evidence):
    exact(entry, ('project_key', 'analysis_id', 'revision', 'source_tree_sha', 'state_utc', 'executed_utc', 'available_utc', 'retrieved_utc', 'artifacts'))
    if not all(isinstance(entry[k], str) and entry[k].strip() for k in ('project_key', 'analysis_id')):
        raise ValueError('Native project/analysis identity required')
    revision(entry['revision']); revision(entry['source_tree_sha'])
    for key in ('state_utc', 'executed_utc', 'retrieved_utc'): utc(entry[key])
    if not utc(entry['state_utc']) <= utc(entry['executed_utc']) <= utc(entry['retrieved_utc']):
        raise ValueError('Impossible native measurement chronology')
    if entry['available_utc'] is not None and not utc(entry['executed_utc']) <= utc(entry['available_utc']) <= utc(entry['retrieved_utc']):
        raise ValueError('Impossible availability chronology')
    exact(entry['artifacts'], ROLES); exact(evidence, ROLES)
    for role in ROLES:
        ref = entry['artifacts'][role]
        exact(ref, ('path', 'sha256')); source_path(ref['path']); hash_id(ref['sha256'])
        # The embedded raw UTF-8 preserves byte hashes and strict duplicate-key validation on replay.
        raw = evidence[role]
        if not isinstance(raw, str) or hashlib.sha256(raw.encode()).hexdigest() != ref['sha256']:
            raise ValueError('Archived payload digest mismatch: ' + role)
    from contracts import _unique_object
    import json
    docs = {k: json.loads(v, object_pairs_hook=_unique_object,
                         parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x))) for k, v in evidence.items()}
    for role, doc in docs.items():
        if not isinstance(doc, dict) or any(doc.get(k) != entry[k] for k in BINDING):
            raise ValueError('Native analysis/revision/tree/project mismatch: ' + role)
    inventory, coverage, files, scanner, ce, payload = (docs[k] for k in ('inventory', 'coverage', 'files', 'scanner', 'ce', 'measures'))
    exact(inventory, BINDING + ('git_files', 'production_paths', 'reviewed_paths'))
    paths = inventory['git_files']
    if not isinstance(paths, list) or not paths or paths != sorted(set(paths)):
        raise ValueError('Unique sorted complete Git inventory required')
    for path in paths: source_path(path)
    if inventory['reviewed_paths'] != paths:
        raise ValueError('Complete Git content review required')
    scope = reg['scope']
    for path in scope['excluded_paths']:
        if not any(p == path or p.startswith(path + '/') for p in paths):
            raise ValueError('Excluded scope path absent from Git inventory')
    expected = sorted(p for p in paths if scoped(p, scope) and language(p) in SUFFIXES.values())
    if not expected or inventory['production_paths'] != expected:
        raise ValueError('Complete programming source inventory required')
    if {language(p) for p in expected} != set(reg['declared_languages']):
        raise ValueError('Declared programming languages mismatch Git scope')
    exact(files, BINDING + ('pagination_complete', 'files'))
    if files['pagination_complete'] is not True or not isinstance(files['files'], list):
        raise ValueError('Complete native file pagination required')
    analyzed = {}
    for row in files['files']:
        exact(row, ('path', 'language'))
        p, lang = row['path'], row['language']
        if p in analyzed or p not in paths or not scoped(p, scope) or language(p) != lang or lang is None:
            raise ValueError('Native file/language/scope mismatch')
        analyzed[p] = lang
    if sorted(analyzed) != sorted(p for p in paths if scoped(p, scope) and language(p) is not None):
        raise ValueError('Incomplete analyzed ancillary/programming scope')
    if sorted(p for p, lang in analyzed.items() if lang in SUFFIXES.values()) != expected:
        raise ValueError('Incomplete analyzed programming scope')
    exact(coverage, BINDING + ('status', 'expected_source_files', 'analyzed_files', 'failed_files', 'unsupported_files', 'analyzed_source_files'))
    if (coverage['status'] != 'COMPLETE' or any(type(coverage[k]) is not int for k in ('expected_source_files', 'analyzed_files', 'failed_files', 'unsupported_files'))
            or coverage['failed_files'] != 0 or coverage['unsupported_files'] != 0
            or coverage['expected_source_files'] != len(expected) or coverage['analyzed_files'] != len(expected)
            or coverage['analyzed_source_files'] != [dict(path=p, language=analyzed[p]) for p in expected]):
        raise ValueError('Complete native analyzed scope/language evidence required')
    exact(scanner, BINDING + ('exit_code', 'sensors_complete', 'ce_task_id'))
    exact(ce, BINDING + ('task',))
    exact(ce['task'], ('id', 'status', 'analysisId', 'componentKey'))
    if (type(scanner['exit_code']) is not int or scanner['exit_code'] != 0 or scanner['sensors_complete'] is not True
            or not isinstance(scanner['ce_task_id'], str) or not scanner['ce_task_id']
            or ce['task'] != dict(id=scanner['ce_task_id'], status='SUCCESS', analysisId=entry['analysis_id'], componentKey=entry['project_key'])):
        raise ValueError('Archived successful scanner/CE evidence required')
    exact(payload, BINDING + ('component',))
    exact(payload['component'], ('key', 'qualifier', 'measures'))
    if payload['component']['key'] != entry['project_key'] or payload['component']['qualifier'] != 'TRK':
        raise ValueError('Native project aggregate required; file debt forbidden')
    raw = {}
    if not isinstance(payload['component']['measures'], list): raise ValueError('Native measures list required')
    for row in payload['component']['measures']:
        exact(row, ('metric', 'value', 'unit'))
        key = row['metric']
        if key in raw: raise ValueError('Duplicate native metric')
        if key not in METRICS + ('ncloc', 'ncloc_language_distribution'):
            raise ValueError('Unsupported native metric')
        expected_unit = UNIT if key in METRICS else 'lines' if key == 'ncloc' else 'native_language_distribution'
        if row['unit'] != expected_unit: raise ValueError('Native metric unit mismatch')
        raw[key] = row['value']
    langs, errors = language_distribution(raw.get('ncloc_language_distribution'))
    if errors or not langs or set(langs) != set(analyzed.values()):
        raise ValueError('Incomplete/mismatched native measured language distribution')
    if (set(langs) & set(SUFFIXES.values())) != set(reg['declared_languages']):
        raise ValueError('Native programming language mismatch')
    _analyzers(manifest, langs)
    def number(value):
        if isinstance(value, str):
            if not re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?', value): raise ValueError('Invalid native number')
            value = float(value)
        return numeric(value, nullable=True)
    ncloc = number(raw.get('ncloc'))
    if ncloc is None or ncloc != sum(langs.values()):
        raise ValueError('Native aggregate NCLOC/distribution mismatch')
    measures = {key: asdict(raw_measure(number(raw.get(key)), UNIT)) for key in METRICS}
    return dict(measures=measures, languages=langs, programming_languages=sorted(set(langs) & PROGRAMMING),
                ancillary_languages=sorted(set(langs) - PROGRAMMING), language_family=language_family(langs),
                project_key=entry['project_key'], analysis_id=entry['analysis_id'], source_tree_sha=entry['source_tree_sha'],
                scope_id=digest(scope), domain_id=_domain(manifest)['domain_id'], source_evidence_sha256=digest(dict(entry=entry, evidence=evidence)),
                artifact_hashes={k: entry['artifacts'][k]['sha256'] for k in ROLES})


def validate_admission(admission):
    exact(admission, ('version', 'registration', 'domain', 'entries', 'evidence', 'git_identity', 'revision_sequence'))
    if admission['version'] != ARCHIVE_VERSION: raise ValueError('Unsupported native archive version')
    reg = registration(admission['registration']); _domain(admission['domain']); hash_id(admission['git_identity'])
    build_mode = admission['domain']['build_mode']
    if build_mode not in ('source_only', 'java_compiled') or ('java' in reg['declared_languages'] and build_mode != 'java_compiled'):
        raise ValueError('Java requires java_compiled build-aware evidence; supported source languages require source_only or java_compiled')
    if admission['domain']['scope_policy_sha256'] != digest(reg['scope']):
        raise ValueError('Analyzer domain scope policy hash mismatch')
    entries, evidence, sequence = admission['entries'], admission['evidence'], admission['revision_sequence']
    if not isinstance(entries, list) or not entries or not isinstance(evidence, list) or len(entries) != len(evidence):
        raise ValueError('Nonempty native entries/evidence required')
    if not isinstance(sequence, list) or not sequence: raise ValueError('Git revision sequence required')
    for row in sequence:
        exact(row, ('sha', 'tree', 'timestamp', 'parents'))
        revision(row['sha']); revision(row['tree']); utc(row['timestamp'])
        if not isinstance(row['parents'], list): raise ValueError('Git parents required')
        for parent in row['parents']: revision(parent)
    if len({r['sha'] for r in sequence}) != len(sequence) or sequence[-1]['sha'] != reg['tip_sha']:
        raise ValueError('Git tip/sequence mismatch')
    for i, row in enumerate(sequence):
        if (i == 0 and row['parents']) or (i and (not row['parents'] or row['parents'][0] != sequence[i-1]['sha'] or utc(row['timestamp']) < utc(sequence[i-1]['timestamp']))) or utc(row['timestamp']) > utc(reg['ref_observed_utc']):
            raise ValueError('Incomplete/nonchronological Git first-parent lineage')
    if admission['git_identity'] != digest(dict(tip=reg['tip_sha'], ref_observed_at=reg['ref_observed_utc'], commits=sequence)):
        raise ValueError('Git lineage identity mismatch')
    positions = {r['sha']: i for i, r in enumerate(sequence)}
    output = []
    seen, analyses, projects = set(), set(), set()
    for entry, proof in zip(entries, evidence):
        native = _entry(entry, reg, admission['domain'], proof)
        pos = positions.get(entry['revision'])
        if pos is None or sequence[pos]['tree'] != entry['source_tree_sha'] or sequence[pos]['timestamp'] != entry['state_utc']:
            raise ValueError('Git revision/tree/state binding mismatch')
        native['lineage_prefix_sha256'] = digest(sequence[:pos+1])
        if entry['revision'] in seen or entry['analysis_id'] in analyses:
            raise ValueError('Duplicate native revision/analysis identity')
        projects.add(entry['project_key'])
        if len(projects) > 1: raise ValueError('One native project identity per source required')
        seen.add(entry['revision']); analyses.add(entry['analysis_id'])
        output.append(dict(repository_id=reg['repository_id'], revision=entry['revision'], revision_index=pos,
                           observed_utc=entry['state_utc'], domain_id=native['domain_id'], scope_id=native['scope_id'],
                           components={name: native['measures'][key]['value'] for name, key in zip(('maintainability', 'reliability', 'security'), METRICS)},
                           native=native))
    return output


def ingest(index_path, archive, git_path, target):
    """Validate local Git objects and archive bytes, return a self-contained v2 source."""
    if target not in TARGETS: raise ValueError('Explicit supported native target required')
    index = read_json(index_path)
    exact(index, ('version', 'source', 'registration', 'domain', 'horizons', 'entries'))
    if index['version'] != ARCHIVE_VERSION: raise ValueError('Unsupported native archive version')
    provenance(index['source']); reg = registration(index['registration'])
    lineage = GitArchive(git_path, reg['tip_sha'], reg['ref_observed_utc'])
    evidence = []
    for entry in index['entries']:
        exact(entry['artifacts'], ROLES)
        proof = {role: artifact_path(archive, entry['artifacts'][role]['path']).read_bytes().decode('utf-8') for role in ROLES}
        _entry(entry, reg, index['domain'], proof)
        import json
        inventory = json.loads(proof['inventory'])
        tree_entries = [p for p in git(git_path, 'ls-tree', '-r', '-z', revision(entry['revision'])).split(b'\0') if p]
        paths = []
        for row in tree_entries:
            info, path = row.split(b'\t', 1)
            path = path.decode()
            if scoped(path, reg['scope']) and info.split()[0] not in (b'100644', b'100755'):
                raise ValueError('Regular Git source blobs required; no symlink/submodule source')
            paths.append(path)
        paths.sort()
        if inventory['git_files'] != paths: raise ValueError('Archive differs from exact local Git tree inventory')
        evidence.append(proof)
    admission = dict(version=ARCHIVE_VERSION, registration=reg, domain=index['domain'], entries=index['entries'], evidence=evidence,
                     git_identity=lineage.identity, revision_sequence=[dict(c.__dict__, parents=list(c.parents)) for c in lineage.commits])
    rows = validate_admission(admission)
    source = dict(version=SOURCE_VERSION, source=index['source'], target=target, unit=UNIT, horizons=index['horizons'], admission=admission,
                  observations=[dict(r, observation_id=digest(dict(target=target, row=r))) for r in rows])
    from forecasting_mvp.persistence_native import derive
    derive(source)
    return source


def output_outside_sources(output, archive, git_path):
    destination = Path(output).resolve()
    if any(destination.is_relative_to(Path(p).resolve()) for p in (archive, git_path)):
        raise ValueError('Native outputs must stay outside immutable archive/Git sources')
