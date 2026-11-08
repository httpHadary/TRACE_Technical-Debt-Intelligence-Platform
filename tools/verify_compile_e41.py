"""Read-only T+60 output verification; never executes Maven or a container."""
import collections
import json
from pathlib import Path
import re
from tools import build_compile_e41 as e
from tools.verify_compile_e06 import warning_context, modes


def output_sets_match(actual_inputs, actual_created, sources, classes):
    expected_inputs={r['path'] for r in sources if r['path'].startswith('src/main/') and r['path'].endswith('.java')}
    return dict(compiler_inputs_exact=bool(expected_inputs) and actual_inputs==expected_inputs,
        compiler_created_files_exact=bool(classes.get('classes')) and actual_created=={r['path'] for r in classes['classes']})


def nesting_metadata(raw):
    """Read InnerClasses/EnclosingMethod as data, after full structural validation."""
    import struct
    e.parse_class(raw)
    offset=8
    def take(n):
        nonlocal offset
        if n<0 or offset+n>len(raw):raise ValueError('Truncated nesting metadata')
        data=raw[offset:offset+n];offset+=n;return data
    def u2():return struct.unpack('>H',take(2))[0]
    def u4():return struct.unpack('>I',take(4))[0]
    count=u2();pool={};index=1
    while index<count:
        tag=take(1)[0]
        if tag==1:pool[index]=take(u2()).decode('utf-8')
        elif tag in (7,8,16):take(2)
        elif tag in (3,4,9,10,11,12,18):take(4)
        elif tag in (5,6):take(8);index+=1
        elif tag==15:take(3)
        else:raise ValueError('Unsupported nesting constant')
        index+=1
    u2();this=u2();u2()
    take(2*u2())
    def attributes():
        result=[]
        for _ in range(u2()):
            name=pool[u2()];result.append((name,take(u4())))
        return result
    for _ in range(2):
        for _ in range(u2()):take(6);attributes()
    result=dict(own_inner_record=False,anonymous=False,enclosing_method=False,inner_name=None)
    for label,data in attributes():
        if label=='EnclosingMethod':
            if len(data)!=4:raise ValueError('Malformed EnclosingMethod')
            result['enclosing_method']=True
        elif label=='InnerClasses':
            count=struct.unpack_from('>H',data)[0]
            if len(data)!=2+8*count:raise ValueError('Malformed InnerClasses')
            for i in range(count):
                inner,outer,name,flags=struct.unpack_from('>HHHH',data,2+i*8)
                if inner==this:
                    if result['own_inner_record']:raise ValueError('Duplicate own inner record')
                    result.update(own_inner_record=True,anonymous=name==0,inner_name=pool[name] if name else None)
    return result


def classify_class_kinds(classes,metadata=None):
    """Separate synthetic helpers from true anonymous classes using bytecode data."""
    metadata=metadata or {}
    for row in classes.get('classes',[]):
        row['adapter_kind']=row['kind'];row['synthetic_flag']=bool(row['access_flags'] & 0x1000)
        if row['kind']=='anonymous':
            record=metadata.get(row['path'],{})
            row['nesting_metadata']=record
            if row['synthetic_flag']:
                row['kind']='synthetic'
                row['classification_basis']='Class-file ACC_SYNTHETIC flag'
            elif record.get('own_inner_record') and record.get('anonymous') and record.get('enclosing_method'):
                row['kind']='anonymous'
                row['classification_basis']='Own InnerClasses inner_name_index=0 and EnclosingMethod; not synthetic'
            else:
                row['kind']='unnamed_or_local_unresolved'
                row['classification_basis']='Numeric name alone cannot establish anonymous/local semantics'
        else:row['classification_basis']='Frozen source identity and class-file SourceFile/internal name'
    return classes


def audit(root):
    root=Path(root);cap=root/'capture'
    run=json.loads((root/'execution.json').read_text());result=json.loads((root/'result.json').read_text())
    registration=json.loads((root/'compile_registration.json').read_text())
    sources=json.loads((root/'source_seed_manifest.json').read_text())['entries']
    def read(name):
        p=cap/name
        return p.read_text(errors='replace') if p.is_file() else None
    stdout=read('maven.stdout') or ''
    try:classes=e.class_manifest(root)
    except (ValueError,OSError,__import__('tarfile').TarError) as exc:
        classes=dict(status='INVALID_OR_UNAVAILABLE',complete=False,classes=[],error=str(exc))
    metadata={}
    if classes.get('complete'):
        import tarfile
        numbered={r['path'] for r in classes['classes'] if r['kind']=='anonymous'}
        # class_manifest already validated every archive member, size and identity.
        with tarfile.open(cap/'classes.tar','r:') as archive:
            for member in archive:
                path=member.name.removeprefix('./')
                if path in numbered:
                    with archive.extractfile(member) as stream:metadata[path]=nesting_metadata(stream.read())
    classes=classify_class_kinds(classes,metadata)
    expected_modes={r['path']:'755' if r['mode']=='100755' else '644' for r in sources}
    before=modes(read('source.modes.before') or '');after=modes(read('source.modes.after') or '')
    input_lines=(read('compiler-inputs.txt') or '').splitlines()
    output_lines=(read('compiler-created.txt') or '').splitlines()
    inputs={s.removeprefix('/source/') for s in input_lines}
    outputs={s.replace('\\','/') for s in output_lines}
    population=sum(r['path'].startswith('src/main/') and r['path'].endswith('.java') for r in sources)
    checks=dict(maven_exit_zero=result['maven_exit']==0,docker_exit_zero=run.get('terminal_state',{}).get('ExitCode')==0,
        actual_compiler_release8=bool(re.search(r'Compiling '+str(population)+r' source files with javac \[debug release 8\]',stdout)),
        target_compiler_population=sorted(inputs)==registration['production_java_sources']==e.production_inputs(sources),
        target_help_package=sum('/cli/help/' in p for p in inputs)==10,
        target_lifecycle=e.lifecycle_matches(result['actual_plugin_order'],registration['lifecycle']),
        successful_terminal_build='[INFO] BUILD SUCCESS' in stdout,
        all_top_level_and_class_structures=classes['complete'] and all(r['major']==52 for r in classes['classes']),
        nested_class_kinds_proven=not any(r['kind']=='unnamed_or_local_unresolved' for r in classes.get('classes',[])),
        compiler_input_list_unique=len(input_lines)==len(inputs),compiler_created_list_unique=len(output_lines)==len(outputs),
        **output_sets_match(inputs,outputs,sources,classes),
        modes_before_exact=before==expected_modes,modes_after_preserved=all(after.get(k)==v for k,v in expected_modes.items()),
        no_git_metadata=not any(k=='.git' or k.startswith('.git/') for k in after),
        no_test_classes=not (cap/'test-classes.present').exists(),
        tracked_bytes_preserved=result['tracked_source_hashes_unchanged'],
        all753_seed_bytes_preserved=result['cache_changes']['seed_artifacts_unchanged'],
        required_capture=result['evidence_completeness']['complete'],
        one_start=sum(x['action']=='start' for x in run.get('events',[]))==1,
        cleanup=run['cleanup_complete'],no_oom=run.get('terminal_state',{}).get('OOMKilled') is False,
        immutable_wrapper=e.b.sha(root/'inspection/wrapper.sh')==registration['executed_wrapper_sha256'],
        target_model_not_substituted=registration['effective_pom_sha256'] is None and registration['parent_version']=='78' and registration['apache_parent_version']=='33')
    e.verify_prepared(root)
    if result['status']=='COMPILE_PASS':status='COMPILE_PASS' if all(checks.values()) else 'PARTIAL'
    else:status=result['status']
    return dict(status=status,checks=checks,classes=classes,
        class_kinds=dict(collections.Counter(r['kind'] for r in classes.get('classes',[]))),
        warnings=warning_context(stdout),compiler_inputs=sorted(inputs),compiler_created_files=sorted(outputs),
        compiler_evidence=dict(registered_source_count=population,observed_input_count=len(inputs),observed_class_count=len(outputs),
            actual_runtime_classpath='UNAVAILABLE_NOT_LOGGED_BY_REGISTERED_COMMAND',
            actual_effective_pom_sha256=None,actual_active_profiles='UNAVAILABLE_NOT_ENUMERATED_BY_REGISTERED_COMPILE',
            limitation='Actual execution and Java8 outputs do not enumerate profiles or resolve an exported effective model'),
        registration_sha256=e.b.sha(root/'compile_registration.json'),result_sha256=e.b.sha(root/'result.json'),
        executed_wrapper_sha256=e.b.sha(root/'inspection/wrapper.sh'),added_source_paths=sorted(after.keys()-before.keys()),
        new_attempts=0,maven_executions_by_this_auditor=0,
        unavailable=sorted(n for n in ['compiler-inputs.txt','compiler-created.txt','source.modes.before','source.modes.after'] if read(n) is None))
