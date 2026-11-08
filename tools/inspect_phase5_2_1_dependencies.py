"""Static pinned POM/cache inspection only: no Maven goals or dependency resolution."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile

CACHES = (Path('/home/hp/.m2/repository'), Path('/home/hp/tst/td360_v3_real_operator_v0100/workspace/m2-cache/repository'))
FAMILIES = ('org/apache/commons/commons-parent', 'org/apache/maven/plugins/maven-compiler-plugin',
            'org/apache/maven/plugins/maven-enforcer-plugin', 'org/apache/maven/plugins/maven-resources-plugin')
NS = {'m':'http://maven.apache.org/POM/4.0.0'}


def inspect(base):
    configs=json.loads((base/'examples/phase5_2/replay_sources.example.json').read_text())
    source=next(c for c in configs if c['repository_id']=='apache/commons-cli')
    jobs=json.loads((base/'examples/phase5_2/readiness_manifest.json').read_text())['planned_jobs']
    states=[]
    for job in jobs:
        if job['repository_id']!=source['repository_id']:continue
        # No checkout, build hooks or lazy object fetch.
        from forecasting_multilanguage.git_events import git
        raw=git(source['path'],'show',job['commit_sha']+':pom.xml')
        pom=ET.fromstring(raw)
        get=lambda element,key:element.findtext('m:'+key,namespaces=NS)
        parent=pom.find('m:parent',NS)
        version=get(parent,'version')
        parent_rel=Path('org/apache/commons/commons-parent')/version/('commons-parent-'+version+'.pom')
        parents=[]
        for number,cache in enumerate(CACHES):
            path=cache/parent_rel
            parents.append(dict(cache_id=number,path=parent_rel.as_posix(),present=path.is_file(),
                                sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None))
        deps=[]
        for dep in pom.findall('m:dependencies/m:dependency',NS):
            deps.append({k:get(dep,k) for k in ('groupId','artifactId','version','scope','optional')})
        states.append(dict(commit_sha=job['commit_sha'],tree_sha=job['tree_sha'],offset_days=job['offset_days'],
            pom_sha256=hashlib.sha256(raw).hexdigest(),parent_version=version,parent_cache=parents,
            direct_dependencies=deps,profile_ids=[get(v,'id') for v in pom.findall('m:profiles/m:profile',NS)],
            compiler_source=pom.findtext('m:properties/m:maven.compiler.source',namespaces=NS),
            compiler_target=pom.findtext('m:properties/m:maven.compiler.target',namespaces=NS),
            effective_build_graph_verified=False))
    artifacts=[]
    for number,cache in enumerate(CACHES):
        for family in FAMILIES:
            folder=cache/family
            for path in sorted(folder.rglob('*')) if folder.is_dir() else ():
                if path.is_symlink() or not path.is_file() or path.suffix not in ('.pom','.jar'):continue
                data=path.read_bytes()
                record=dict(cache_id=number,path=path.relative_to(cache).as_posix(),sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data))
                if path.suffix=='.jar':
                    with zipfile.ZipFile(path) as jar:record['zip_crc_status']='PASS' if jar.testzip() is None else 'CORRUPT'
                else:
                    try:ET.fromstring(data);record['xml_parse_status']='PASS'
                    except ET.ParseError:record['xml_parse_status']='INVALID'
                artifacts.append(record)
    return dict(version='phase5_2_1-static-dependencies-v1',states=states,cached_artifacts=artifacts,
                historical_builds_executed=0,dependency_resolution_executed=False,
                status='PARTIAL_STATIC_ONLY',limitations=['Parent/plugin presence and CRC do not establish transitive dependency or effective-profile completeness',
                  'No settings.xml or credentials inspected', 'No Java compilation or classpath generated'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);args=parser.parse_args()
    out=Path(args.output)
    if out.exists():raise ValueError('Refusing overwrite')
    # Run as a module from the existing checkout; no package installation.
    result=inspect(Path(__file__).resolve().parents[1]);out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('Static dependency evidence recorded:',out)


if __name__=='__main__':main()
