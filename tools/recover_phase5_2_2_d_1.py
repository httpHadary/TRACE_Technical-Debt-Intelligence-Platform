"""One Task D.1 batch: fresh verified copies, <=400 requests, offline checkpoints."""
import argparse
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import urllib.error
import zipfile
from tools.maven_recovery.acquisition import BudgetExceeded, parse_xml, relative_path
from tools.maven_recovery.continuation import Continuation, ReadOnlyCache, digest, MAX_REQUESTS, MAX_DISK
from tools.maven_recovery.model import Models, NS, PHASES, text, expand
from tools.recover_phase5_2_2_d import git

BASE = '8be4c79ab02f67d53bbefa597df56c65f4f97055'
SOURCE = Path('/home/hp/tst/research/forecasting_mvp/phase5_2_2_d/2026-10-16/isolated-cache')
PRIORITIES = [('org.apache.maven.plugins','maven-resources-plugin','3.3.1'),
              ('org.apache.maven.plugins','maven-enforcer-plugin','3.5.0'),
              ('org.codehaus.mojo','buildnumber-maven-plugin','3.2.1')]
JAR_PLUGIN = ('org.apache.maven.plugins','maven-jar-plugin','3.4.2')
USER = {'maven.test.skip':'true','maven.compiler.release':'8','user.home':'/tmp'}


def root_models(base, a):
    config = json.loads((base/'examples/phase5_2/replay_sources.example.json').read_text())
    repo = next(r['path'] for r in config if r['repository_id']=='apache/commons-cli')
    references = json.loads((base/'examples/phase5_2_1/dependency_inspection.json').read_text())['states']
    rows = []
    for reference in references:
        commit = reference['commit_sha'];raw = git(repo,'show',commit+':pom.xml')
        if hashlib.sha256(raw).hexdigest()!=reference['pom_sha256'] or git(repo,'rev-parse',commit+'^{tree}').decode().strip()!=reference['tree_sha']:
            raise ValueError('Historical source identity mismatch')
        files = git(repo,'ls-tree','-r','--name-only',commit).decode().splitlines()
        models = Models(a)
        model = models.build(parse_xml(raw),files,USER,['commons-cli',commit])
        rows.append((reference,models,model))
    return rows


def audit(base, a):
    """Every model read is offline. UNKNOWN is not build readiness PASS."""
    a.network_enabled = False
    states=[];required=set();later=set();all_accessed=set();issues=[];optional=[]
    for reference,models,model in root_models(base,a):
        a.used_paths=set()
        # Rebuild to include this revision's parent/import paths in its evidence.
        models=Models(a)
        # The first projection already contains the exact frozen Git inventory;
        # obtaining it again uses Git reads only, never Maven/project execution.
        config=json.loads((base/'examples/phase5_2/replay_sources.example.json').read_text())
        repo=next(r['path'] for r in config if r['repository_id']=='apache/commons-cli')
        commit=reference['commit_sha'];raw=git(repo,'show',commit+':pom.xml')
        model=models.build(parse_xml(raw),git(repo,'ls-tree','-r','--name-only',commit).decode().splitlines(),USER,['commons-cli',commit])
        plugins=models.compile_plugins(model)
        model_roots=[d for d in model['dependencies'] if d['scope'] in ('compile','provided','system')]
        edges=models.closure(model_roots,'project compile')
        for (g,artifact),plugin in model['plugins'].items():
            if artifact=='maven-remote-resources-plugin':
                for value in plugin.findall('m:configuration/m:resourceBundles/m:resourceBundle',NS):
                    gav=expand(value.text,model['properties']).split(':')
                    try:
                        relative_path(*gav);models.remote(gav);a.get(*gav,'jar')
                    except (ValueError,urllib.error.HTTPError) as exc:
                        models.issue('RESOURCE_BUNDLE',gav,exc)
        for p in plugins:
            if p['required_through_compile'] is True:
                edges+=p['dependencies']
                for ext in ('pom','jar'):
                    required.add(relative_path(*p['gav'],ext))
            elif p['required_through_compile'] is False and p['disposition']=='DESCRIPTOR_VERIFIED_LATER_PHASE':
                for ext in ('pom','jar'):
                    later.add(relative_path(*p['gav'],ext))
        for edge in edges:
            required.add(relative_path(*edge['gav']))
            if edge['type']!='pom':
                required.add(relative_path(*edge['gav'],'jar',edge['classifier'] or ('tests' if edge['type']=='test-jar' else '')))
        accessed=set(a.used_paths);all_accessed|=accessed
        missing=sorted(accessed-set(a.records))
        profile_unknown=[p for m in [model,*models.models.values()] for p in m['profiles'] if p['active'] is None]
        ambiguous=[p for p in plugins if p['required_through_compile'] is None or p['disposition']=='UNRESOLVED']
        nonprofile=[i for i in models.issues if i['kind']!='PROFILE']
        status='BLOCKED' if missing or nonprofile or ambiguous else 'UNKNOWN'
        states.append(dict(commit_sha=commit,tree_sha=reference['tree_sha'],pom_sha256=reference['pom_sha256'],
            offset_days=reference['offset_days'],parent_version=reference['parent_version'],
            plugins=plugins,missing_paths=missing,profile_decisions=model['profiles'],unknown_profiles=profile_unknown,
            issues=models.issues,compile_dependency_readiness=status,
            effective_model_verified=False,offline_build_readiness='UNKNOWN' if status=='UNKNOWN' else 'BLOCKED'))
        for gav,m in models.models.items():
            for dep in m['dependencies']:
                if dep['optional'] or dep['scope'] not in ('compile','runtime'):
                    row=dict(model=list(gav),dependency=dep,disposition='OPTIONAL_OR_NON_RUNTIME_NOT_ACQUIRED')
                    if row not in optional:optional.append(row)
        for issue in models.issues:
            if issue not in issues:issues.append(issue)
    # Required takes precedence when another plugin happens to share a later descriptor.
    later-=required
    a.used_paths=all_accessed
    return dict(version='task-d1-static-audit-v1',base_commit=BASE,states=states,
        missing_paths=sorted(all_accessed-set(a.records)),accessed_artifact_paths=sorted(all_accessed),
        required_compile_candidates=sorted(required),later_phase_descriptor_paths=sorted(later),
        optional_or_nonruntime=optional,unresolved=issues,offline_build_readiness='BLOCKED' if any(s['offline_build_readiness']=='BLOCKED' for s in states) else 'UNKNOWN',
        status='PARTIAL',limitation='Static candidate union, not Maven mediation/effective-model or compilation proof')


def descriptor(a, gav):
    models=Models(a);models.remote(gav)
    raw=a.get(*gav,'jar')
    with zipfile.ZipFile(io.BytesIO(raw)) as jar:
        root=parse_xml(jar.read('META-INF/maven/plugin.xml'))
    return dict(gav=list(gav),goals=[dict(goal=m.findtext('goal'),phase=m.findtext('phase')) for m in root.findall('mojos/mojo')],executed=False)


def frontier_coordinate(path):
    parts=path.split('/');group='.'.join(parts[:-3]);artifact=parts[-3];version=parts[-2];ext=parts[-1].rsplit('.',1)[1]
    if relative_path(group,artifact,version,ext)!=path:
        raise ValueError('Ambiguous frontier coordinate')
    return group,artifact,version,ext


def classify(result, manifest, cache):
    """Evidence categories preserve UNKNOWN and do not admit conditional code."""
    known={r['path'] for r in manifest['artifacts']}
    required=set(result['required_compile_candidates'])
    accessed=set(result['accessed_artifact_paths'])
    # Failed compile-dependency reads never reach closure's successful edge
    # list. Preserve their actual requested identities as required, not metadata.
    for issue in result.get('unresolved',[]):
        if issue['kind']=='DEPENDENCY':
            for ext in ('pom','jar'):
                try:path=relative_path(*issue['identity'],ext)
                except ValueError:continue
                if path in accessed:required.add(path)
    later=set(result['later_phase_descriptor_paths'])-required
    matrix=[]
    for state in result['states']:
        matrix.append(dict(commit_sha=state['commit_sha'],tree_sha=state['tree_sha'],
            pom_sha256=state['pom_sha256'],offset_days=state['offset_days'],parent_version=state['parent_version'],
            compile_dependency_readiness=state['compile_dependency_readiness'],
            offline_build_readiness=state['offline_build_readiness'],effective_model_verified=False,
            missing_paths=state['missing_paths'],unknown_profile_count=len(state['unknown_profiles']),
            plugins=[{k:p[k] for k in ('gav','required_through_compile','disposition','executions')} for p in state['plugins']]))
    profiles={}
    for state in result['states']:
        for p in state['unknown_profiles']:
            profiles[(tuple(p['model']),p['id'])]=p
    conditional=[]
    for (gav,profile_id),p in sorted(profiles.items()):
        path=relative_path(*gav)
        if path not in known:
            raise ValueError('Conditional profile source lacks verified provenance')
        model=parse_xml((Path(cache)/'repository'/path).read_bytes())
        profile=next(e for e in model.findall('m:profiles/m:profile',NS) if text(e,'id')==profile_id)
        declarations=[]
        for query,kind in (('m:dependencies/m:dependency','dependency'),
                           ('m:dependencyManagement/m:dependencies/m:dependency','managed_dependency'),
                           ('m:build/m:plugins/m:plugin','plugin')):
            for e in profile.findall(query,NS):
                declarations.append(dict(kind=kind,gav=[text(e,'groupId'),text(e,'artifactId'),text(e,'version')],
                    scope=text(e,'scope'),status='CONDITIONAL_UNKNOWN_NOT_ADMITTED'))
        conditional.append(dict(model=list(gav),profile_id=profile_id,source_path=path,
            source_sha256=next(r['sha256'] for r in manifest['artifacts'] if r['path']==path),
            status='UNKNOWN',reason=p['reason'],declarations=declarations))
    categories=dict(version='task-d1-artifact-classification-v1',
        required_compile_static_candidates=sorted(required),
        conditional_profile_declarations=conditional,later_phase_descriptor_only=sorted(later),
        model_or_configuration_metadata=sorted(set(result['accessed_artifact_paths'])-required-later),
        optional_or_nonruntime_declarations=result['optional_or_nonruntime'],
        unused_verified_cache_paths=sorted(known-set(result['accessed_artifact_paths'])),
        missing_unverified=[dict(path=p,status='NOT_VERIFIED_WITHIN_BUDGET') for p in result['missing_paths']],
        unavailable_artifact_evidence=[e for e in manifest['http_events'] if e['path'].endswith(('.pom','.jar'))],
        ambiguous_profile_decisions_preserved=True,
        limitation='Required candidates are a static union, not Maven mediation or effective-profile proof')
    return categories,matrix


def execute(base, output):
    if len(os.sched_getaffinity(0))!=1 or not 0<resource.getrlimit(resource.RLIMIT_AS)[0]<=1073741824:
        raise ValueError('Require one CPU via taskset and prlimit --as=1073741824')
    old=json.loads((base/'examples/phase5_2_2_d/dependency_manifest.json').read_text())
    previous=json.loads((base/'examples/phase5_2_2_d/readiness_manifest.json').read_text())['missing_requested_paths']
    if len(previous)!=22:raise ValueError('Frozen Task D frontier mismatch')
    a=Continuation(output,SOURCE,old);checkpoints=[];descriptors=[];errors=[];stopped=None
    def checkpoint(name):
        result=audit(base,a)
        checkpoints.append(dict(name=name,requests=a.requests,new_artifacts=len(a.records)-len(a.seed_paths),missing_paths=result['missing_paths']))
        (a.root/'requirements.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        (a.root/'checkpoints.json').write_text(json.dumps(checkpoints,sort_keys=True,indent=2)+'\n')
        a.seal();print(name,'requests',a.requests,'new',len(a.records)-len(a.seed_paths),'missing',len(result['missing_paths']),flush=True)
        return result
    try:
        initial=checkpoint('SEEDED_OFFLINE')
        if initial['missing_paths']!=sorted(previous):raise ValueError('Independent seed audit did not reproduce frozen22-file frontier')
        # Pin the three compile-path descriptors before any broad dependency walk.
        for gav in PRIORITIES:
            a.network_enabled=True
            try:descriptors.append(descriptor(a,gav))
            except (ValueError,urllib.error.HTTPError) as exc:errors.append(dict(step='descriptor',gav=list(gav),error=str(exc)))
        checkpoint('COMPILE_DESCRIPTORS')
        # Inspect the cheap JAR descriptor before a larger transitive traversal.
        a.network_enabled=True
        try:descriptors.append(descriptor(a,JAR_PLUGIN))
        except (ValueError,urllib.error.HTTPError) as exc:errors.append(dict(step='jar-descriptor',gav=list(JAR_PLUGIN),error=str(exc)))
        checkpoint('JAR_DESCRIPTOR_ONLY')
        for gav in PRIORITIES:
            a.network_enabled=True;models=Models(a)
            root=dict(gav=list(gav),type='jar',classifier='',scope='compile',optional=False,exclusions=[])
            models.closure([root],'priority compile plugin '+gav[1])
            # Include configured plugin-dependency overrides from the pinned roots.
            for _,model_set,model in root_models(base,a):
                p=model['plugins'].get(gav[:2])
                if p is not None and expand(text(p,'version'),model['properties'])==gav[2]:
                    configured=[model_set.dependency(e,model['properties']) for e in p.findall('m:dependencies/m:dependency',NS)]
                    models.closure(configured,'configured compile plugin '+gav[1])
            checkpoint('CLOSURE_'+gav[1])
        current=checkpoint('PRIORITY_CLOSURES_FINISHED')
        # Remaining old-frontier entries first, followed by newly exposed compile candidates.
        for _ in range(4):
            frontier=sorted(set(current['missing_paths']),key=lambda p:(p not in previous,p))
            if not frontier:break
            start=len(a.records)
            a.network_enabled=True
            for path in frontier:
                try:a.get(*frontier_coordinate(path))
                except (ValueError,urllib.error.HTTPError) as exc:errors.append(dict(step='frontier',path=path,error=str(exc)))
            current=checkpoint('FRONTIER_PASS_'+str(_+1))
            if len(a.records)==start:break
    except BudgetExceeded as exc:
        stopped=dict(reason=str(exc),status='BUDGET_EXHAUSTED')
    except Exception as exc:
        stopped=dict(reason=str(exc),type=type(exc).__name__,status='EXECUTION_ERROR')
        raise
    finally:
        a.network_enabled=False
        final=checkpoint('FINAL_OFFLINE')
        resolved=sorted(set(previous)&set(a.records));remaining=sorted(set(previous)-set(a.records))
        comparison=dict(version='task-d1-frontier-comparison-v1',before=previous,resolved_original=resolved,
            remaining_original=remaining,after=final['missing_paths'],newly_exposed_remaining=sorted(set(final['missing_paths'])-set(previous)),
            checkpoints=checkpoints,stop=stopped,errors=errors,descriptors=descriptors,
            original_task_d_requests=2000,new_batch_requests=a.requests,
            requests_budget=MAX_REQUESTS,offline_build_readiness=final['offline_build_readiness'])
        (a.root/'frontier_comparison.json').write_text(json.dumps(comparison,sort_keys=True,indent=2)+'\n')
        a.seal();a.check_disk()
    return a,final,comparison


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    parser.add_argument('--audit-only',action='store_true',help='Read-only verification; print deterministic audit JSON without network')
    args=parser.parse_args()
    if args.audit_only:
        if len(os.sched_getaffinity(0))!=1 or not 0<resource.getrlimit(resource.RLIMIT_AS)[0]<=1073741824:
            raise ValueError('Require one CPU via taskset and prlimit --as=1073741824')
        print(json.dumps(audit(Path(__file__).resolve().parents[1],ReadOnlyCache(args.output)),sort_keys=True,indent=2))
        return
    a,result,comparison=execute(Path(__file__).resolve().parents[1],args.output)
    print('Task D.1 PARTIAL; offline build readiness',result['offline_build_readiness'],'requests',a.requests)


if __name__=='__main__':main()
