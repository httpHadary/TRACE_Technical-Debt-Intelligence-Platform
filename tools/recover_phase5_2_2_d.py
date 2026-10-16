"""Task D: statically acquire exact Commons CLI compile inputs, never run Maven."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import urllib.error
from tools.maven_recovery.acquisition import Acquisition, OfflineAcquisition, parse_xml, relative_path
from tools.maven_recovery.model import Models


def stage_cache(root):
    """Stage only final traversal inputs, excluding earlier unused candidates."""
    root = Path(root)
    manifest = json.loads((root / 'dependency_manifest.json').read_text())
    requirements = json.loads((root / 'requirements.json').read_text())
    requested = set(requirements['accessed_artifact_paths'])
    destination = root / 'admitted-repository'
    if destination.exists():
        raise ValueError('Refusing staged cache overwrite')
    # Payload acquisition remains capped at256MiB. Including this one staged
    # copy and bounded metadata, Task D disk consumption must stay below544MiB.
    artifacts = manifest['artifacts']
    if sum(r['bytes'] for r in artifacts) * 2 > 512 * 1024 * 1024:
        raise ValueError('Staging disk budget exceeded')
    occupied = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    if occupied + sum(r['bytes'] for r in artifacts if r['path'] in requested) > 544 * 1024 * 1024:
        raise ValueError('Whole Task D cache disk budget exceeded')
    for row in artifacts:
        path = relative_path(*row['coordinates'], row['extension'], row['classifier'])
        source = root / 'repository' / path
        if path != row['path'] or any(p.is_symlink() for p in (source, *source.parents)):
            raise ValueError('Staging artifact identity mismatch')
        if hashlib.sha256(source.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Staging artifact integrity mismatch')
    destination.mkdir(mode=0o700)
    for row in artifacts:
        if row['path'] in requested:
            target = destination / row['path'];target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / 'repository' / row['path'], target)
            if hashlib.sha256(target.read_bytes()).hexdigest() != row['sha256']:
                raise ValueError('Staged copy mismatch')
            row['disposition'] = 'STAGED_STATIC_CANDIDATE'
        else:
            row['disposition'] = 'EARLIER_UNUSED_CANDIDATE_NOT_STAGED'
    manifest['staged_cache'] = 'admitted-repository'
    manifest['staging_is_build_completeness_proof'] = False
    manifest['missing_requested_paths'] = sorted(requested - {r['path'] for r in artifacts})
    manifest['requirements_sha256'] = hashlib.sha256((root / 'requirements.json').read_bytes()).hexdigest()
    (root / 'staged_dependency_manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    return manifest


def git(repo, *args):
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
    result = subprocess.run(['git', '--no-optional-locks', '-c', 'core.hooksPath=/dev/null',
        '-C', str(repo), *args], capture_output=True, env=env, timeout=15, check=True)
    if len(result.stdout) > 2 * 1024 * 1024:
        raise ValueError('Git read bound exceeded')
    return result.stdout


def recover(base, output, resume=False, offline=False):
    # Require actual host enforcement, not merely a claimed config limit.
    if len(os.sched_getaffinity(0)) != 1 or not 0 < resource.getrlimit(resource.RLIMIT_AS)[0] <= 1073741824:
        raise ValueError('Invoke with taskset one CPU and prlimit --as=1073741824')
    references = json.loads((base / 'examples/phase5_2_1/dependency_inspection.json').read_text())
    config = json.loads((base / 'examples/phase5_2/replay_sources.example.json').read_text())
    repo = Path(next(r['path'] for r in config if r['repository_id'] == 'apache/commons-cli'))
    acquisition = (OfflineAcquisition if offline else Acquisition)(output, resume=resume)
    models = Models(acquisition); states = []
    user = {'maven.test.skip': 'true', 'maven.compiler.release': '8', 'user.home': '/tmp'}
    result = dict(version='task-d-static-requirements-v1', base_commit='1caf129975a39aeaab1614e457a7114f0bf477e3',
        status='PARTIAL_STATIC_NOT_OFFLINE_BUILD_PROOF', repository_id='apache/commons-cli', states=states,
        future_build_context=dict(jdk='17.0.17+10', maven='3.9.11', user_properties=user,
            explicit_profiles=[], settings='No user settings or user caches read'),
        unresolved=models.issues, project_goals_executed=0,
        limitation='Static inherited/profile/dependency candidate union; not Maven mediation, effective model, or build proof')
    prepared = []
    try:
        for state in references['states']:
            commit = state['commit_sha'];raw = git(repo, 'show', commit + ':pom.xml')
            if hashlib.sha256(raw).hexdigest() != state['pom_sha256']:
                raise ValueError('Pinned historical POM identity mismatch')
            tree = git(repo, 'rev-parse', commit + '^{tree}').decode().strip()
            if tree != state['tree_sha']:
                raise ValueError('Pinned historical tree mismatch')
            files = git(repo, 'ls-tree', '-r', '--name-only', commit).decode().splitlines()
            if any(n in files for n in ('.mvn/extensions.xml', '.mvn/maven.config', '.mvn/jvm.config')):
                models.issue('LOCAL_MAVEN_CONFIGURATION', commit, 'Requires separate static extension/config review')
            model = models.build(parse_xml(raw), files, user, ['commons-cli', commit])
            from tools.maven_recovery.model import text, expand
            record = dict(commit_sha=commit, tree_sha=tree, offset_days=state['offset_days'],
                pom_sha256=state['pom_sha256'], parent_version=state['parent_version'],
                parent_chain=model['chain'][:-1], imported_boms=model['imports'],
                profile_decisions=model['profiles'], declared_dependencies=model['dependencies'],
                compile_classpath_candidates=[], plugins=[], static_traversal_finished=False,
                declared_build_plugins=[dict(gav=[g,a,expand(text(p,'version'),model['properties'])])
                    for (g,a),p in model['plugins'].items()])
            states.append(record)
            prepared.append((record, model))
        # Inventory every pinned revision before the potentially larger plugin
        # traversal, so a hard cap never hides the other five requirements.
        for record, model in prepared:
            # Test-scoped versions are inventoried, but their JARs are not part
            # of compile acquisition. Do not fetch unrelated test/build goals.
            record['compile_classpath_candidates'] = models.closure(
                [d for d in model['dependencies'] if d['scope'] in ('compile', 'provided', 'system')],
                'project compile dependencies')
            record['plugins'] = models.compile_plugins(model)
            # Remote-resource plugin's data bundles are config references,
            # not plugin-runtime transitive dependencies. Read their explicit GAV.
            from tools.maven_recovery.model import NS, text, expand
            record['configured_resource_bundles'] = []
            for plugin in model['plugins'].values():
                if text(plugin, 'artifactId') != 'maven-remote-resources-plugin':
                    continue
                for e in plugin.findall('m:configuration/m:resourceBundles/m:resourceBundle', NS):
                    gav = expand(e.text, model['properties']).split(':')
                    try:
                        relative_path(*gav);models.remote(gav);acquisition.get(*gav, 'jar')
                        record['configured_resource_bundles'].append(gav)
                    except (ValueError, urllib.error.HTTPError) as exc:
                        models.issue('RESOURCE_BUNDLE', gav, exc)
            record['static_traversal_finished'] = True
            print('INVENTORIED',record['offset_days'],record['commit_sha'], 'artifacts',len(acquisition.records),flush=True)
    except Exception as exc:
        result['execution_error'] = dict(type=type(exc).__name__, message=str(exc)[:1500])
        raise
    finally:
        acquisition.seal()
        result['accessed_artifact_paths'] = sorted(acquisition.used_paths)
        (acquisition.root / 'requirements.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True);parser.add_argument('--resume', action='store_true')
    parser.add_argument('--stage-only', action='store_true', help='Offline hash verification and fresh candidate-cache staging')
    parser.add_argument('--offline-audit', action='store_true', help='No network; enumerate the unresolved cached-graph frontier')
    args = parser.parse_args()
    if args.stage_only:
        stage_cache(args.output)
        print('Verified candidate cache staged; no network or Maven execution')
        return
    result = recover(Path(__file__).resolve().parents[1], args.output, args.resume, args.offline_audit)
    print(result['status'], 'unresolved records:', len(result['unresolved']))


if __name__ == '__main__':
    main()
