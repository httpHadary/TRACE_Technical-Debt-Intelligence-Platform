"""Read-only E.0.6 output audit; no container/Maven/Java execution or retries."""
import json
from pathlib import Path
import re
import collections
from tools import build_compile_e06 as e
from tools.maven_recovery.acquisition import parse_xml
from tools.maven_recovery.model import NS, text

# Exact frozen T0 executions through compile, distinct from the deploy-plan list.
EXPECTED=(('enforcer','3.5.0','enforce','enforce-maven-version'),
 ('enforcer','3.5.0','enforce','enforce-java-version'),
 ('apache-rat','0.16.1','check','rat-check'),
 ('artifact','3.5.1','check-buildplan','check-buildplan'),
 ('build-helper','3.6.0','parse-version','parse-version'),
 ('antrun','3.1.0','run','javadoc.resources'),
 ('remote-resources','3.2.0','process','process-resource-bundles'),
 ('buildnumber','3.2.1','create','default'),
 ('resources','3.3.1','resources','default-resources'),
 ('compiler','3.13.0','compile','default-compile'))


def warning_context(stdout):
    """Attribute warnings to actual goal banners, never to planned goal mentions."""
    current=None;warnings=[]
    for line in stdout.splitlines():
        match=re.search(r'--- ([^: ]+):([^: ]+):([^ ]+) \(([^)]+)\) @ ([^ ]+) ---',line)
        if match:current=dict(prefix=match[1],version=match[2],goal=match[3],execution=match[4])
        missing=re.search(r'^\[WARNING\] The POM for ([\w.-]+):([\w.-]+):jar:([\w.-]+) is missing',line)
        if missing:
            warnings.append(dict(gav=list(missing.groups()),evidence=line,observed_during=current,
                classification='NONFATAL_MISSING_POM_WARNING',fatal=False,
                dependency_domain='PLUGIN_METADATA_COLLECTION' if current else 'UNKNOWN',
                required_runtime_jar='UNKNOWN_NOT_INFERRED_FROM_POM_WARNING'))
    return warnings


def modes(raw):
    values={}
    for line in raw.splitlines():
        mode,path=line.split(' ',1)
        if path in values:raise ValueError('Duplicate mode identity')
        values[path]=mode
    return values


def lifecycle_check(order):
    actual=[tuple(row[k] for k in ('prefix','version','goal','execution')) for row in order]
    return actual==list(EXPECTED) and all(row['project']=='commons-cli' for row in order)


def audit(root):
    root=Path(root);cap=root/'capture'
    run=json.loads((root/'execution.json').read_text());result=json.loads((root/'result.json').read_text())
    registration=json.loads((root/'compile_registration.json').read_text())
    sources=json.loads((root/'source_seed_manifest.json').read_text())['entries']
    stdout=(cap/'maven.stdout').read_text();classes=e.class_manifest(root)
    expected_modes={r['path']:'755' if r['mode']=='100755' else '644' for r in sources}
    before=modes((cap/'source.modes.before').read_text());after=modes((cap/'source.modes.after').read_text())
    input_paths={(r['path']) for r in sources if r['path'].startswith('src/main/') and r['path'].endswith('.java')}
    actual_inputs={s.removeprefix('/source/') for s in (cap/'compiler-inputs.txt').read_text().splitlines()}
    actual_classes={s.replace('\\','/') for s in (cap/'compiler-created.txt').read_text().splitlines()}
    class_paths={r['path'] for r in classes['classes']}
    checks=dict(maven_exit_zero=result['maven_exit']==0,docker_exit_zero=run['terminal_state']['ExitCode']==0,
        real_compiler_banner='Compiling 26 source files with javac [debug release 8]' in stdout,
        exact_original_lifecycle=lifecycle_check(result['actual_plugin_order']),
        check_buildplan_returned_success=lifecycle_check(result['actual_plugin_order']) and '[INFO] BUILD SUCCESS' in stdout,
        all_top_level_and_class_structures_verified=classes['complete'] and all(r['major']==52 for r in classes['classes']),
        all26_compiler_inputs_match=actual_inputs==input_paths and len(actual_inputs)==26,
        all37_compiler_outputs_match=actual_classes==class_paths and len(actual_classes)==37,
        modes_before_exact=before==expected_modes,modes_after_preserved=all(after.get(k)==v for k,v in expected_modes.items()),
        no_git_metadata=not any(k=='.git' or k.startswith('.git/') for k in after),
        no_test_classes=not (cap/'test-classes.present').exists(),
        tracked_bytes_preserved=result['tracked_source_hashes_unchanged'],
        all697_seed_bytes_preserved=result['cache_changes']['seed_artifacts_unchanged'],
        all_required_original_capture=result['evidence_completeness']['complete'],
        one_container_start=sum(x['action']=='start' for x in run['events'])==1,
        cleanup_complete=run['cleanup_complete'],no_oom=run['terminal_state']['OOMKilled'] is False,
        immutable_wrapper=e.b.sha(root/'inspection/wrapper.sh')==registration['executed_wrapper_sha256'])
    e.verify_prepared(root)
    identity=parse_xml((e.RESEARCH/'phase5_2_2_d_3/2026-10-16/effective-pom/effective-pom.xml').read_bytes())
    declarations=[dict(gav=[text(d,k) for k in ('groupId','artifactId','version')],scope=text(d,'scope','compile'))
        for d in identity.findall('m:dependencies/m:dependency',NS)]
    return dict(status='COMPILE_PASS' if result['status']=='COMPILE_PASS' and all(checks.values()) else 'PARTIAL',
        checks=checks,classes=classes,class_kinds=dict(collections.Counter(r['kind'] for r in classes['classes'])),
        warnings=warning_context(stdout),compiler_inputs=sorted(actual_inputs),compiler_created_files=sorted(actual_classes),
        compiler_evidence=dict(invocation_observation='Compiler3.13.0 goal and javac [debug release8] log, actual26 inputs and37 outputs',
            observed_runtime_classpath='UNAVAILABLE_NOT_LOGGED_BY_REGISTERED_COMMAND',
            declared_project_dependencies=declarations,
            declared_compile_dependencies=[r['gav'] for r in declarations if r['scope'] in ('compile','provided','system')],
            limitation='Do not equate effective declarations with a captured compiler argument vector; no extra goal/debug setting was used'),
        original_registration_sha256=e.b.sha(root/'compile_registration.json'),original_result_sha256=e.b.sha(root/'result.json'),
        executed_wrapper_sha256=e.b.sha(root/'inspection/wrapper.sh'),
        added_source_paths=sorted(after.keys()-before.keys()),new_attempts=0,maven_executions_by_this_auditor=0,
        warning_attribution='Final attribution uses actual goal banners; legacy generic PROJECT_DEPENDENCY warning labels are not authoritative')
