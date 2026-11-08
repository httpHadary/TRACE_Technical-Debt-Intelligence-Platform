# Future isolated server inspection — Phase 5.2.1 handoff

**Not executed. No startup is authorized by Phase 5.2.1.** These commands are
for a later, separately authorized runtime-inspection step. They dispatch no
scan and execute no historical build. Collection needs another explicit gate.

## Admission before any startup

The operator must authorize a new disposable container named
`td360-p521-inspect`, on `127.0.0.1:19004`, using the existing image
`sonarqube@sha256:9026624a61cd25542a402a9e7213dd7dbb39724ac9597e331e6b85362558c079`.
Use an isolated, no-egress network and newly created empty, separately named
volumes for data/extensions/logs/temp. No old volume, old container filesystem,
Docker socket, source repository or credentials directory may be mounted.
No image pull, analyzer installation, version change or remote provisioning.
Startup configuration and any new-instance credential initialization belong to
that later authorization, not to this document's read-only commands.

Keep the sealed limits in `examples/phase5_2/readiness_manifest.json` unchanged:
MemAvailable ≥10,737,418,240 bytes; disk free ≥16,106,127,360 bytes; total replay
≤8,589,934,592 bytes; one job; shared2 CPUs; server cap3,758,096,384 bytes;
scanner cap4,294,967,296; monitor536,870,912. Historical builds, if separately
authorized later, use2,147,483,648 bytes while the isolated server is stopped.
Keep ≥10GiB disk reserve and ≤5GiB new artifacts; no swap-based RAM admission.

Before startup, record `/proc/meminfo`, `df -B1`, CPU/cgroup limits, existing
container IDs/states and old volume identities. Reject insufficient resources.
Do not free memory by automatically stopping services, delete data, increase
caps or reuse `td-target-sonar`. The startup step must supply a monitored
20-minute wall limit, private outputs, resource polling and a fail-closed stop
policy for **only its new container**. A failed startup cannot dispatch scans.

There is intentionally no `docker run/start`, volume creation, mode mutation,
password reset, scanner or Maven build command in this handoff.

## Verify the separately admitted container, then inspect

After that distinct step has provided a running disposable server and a
least-privilege inspection token, run from the project root:

```bash
set -eu
umask 077
export TD521_INSPECTION_OUT="$(mktemp -d /home/hp/tst/research/forecasting_mvp/phase5_2_1-inspection-XXXXXX)"
# Do not enable shell tracing or put credentials on command lines.
python3 - <<'PY'
import json, os, subprocess
from pathlib import Path
out=Path(os.environ['TD521_INSPECTION_OUT'])
inspect=lambda name:json.loads(subprocess.check_output(['docker','inspect',name]))[0]
old=inspect('td-target-sonar'); new=inspect('td360-p521-inspect')
assert old['Id']=='264185299cf7f1ad4a2784e6845c476dd4d9f2745e8de84b42905bac8a4bcba3'
assert not old['State']['Running']
assert new['Image']=='sha256:9026624a61cd25542a402a9e7213dd7dbb39724ac9597e331e6b85362558c079'
assert new['State']['Running']
assert new['HostConfig']['Memory']==3758096384
assert new['HostConfig']['MemorySwap']==3758096384  # no additional container swap
assert new['HostConfig']['NanoCpus']==2000000000
assert not new['HostConfig']['Privileged']
limits={v['Name']:v for v in new['HostConfig'].get('Ulimits',[])}
assert limits['nofile']['Soft']>=131072 and limits['nofile']['Hard']>=131072
assert limits['nproc']['Soft']>=8192 and limits['nproc']['Hard']>=8192
assert not new['HostConfig'].get('VolumesFrom')
assert new['HostConfig']['NetworkMode'] not in ('host','container:'+old['Id'])
ports=new['HostConfig']['PortBindings']
assert ports=={'9000/tcp':[{'HostIp':'127.0.0.1','HostPort':'19004'}]}
old_names={v.get('Name') for v in old['Mounts'] if v.get('Name')}
assert {v['Destination'] for v in new['Mounts']}=={
    '/opt/sonarqube/data','/opt/sonarqube/extensions','/opt/sonarqube/logs','/opt/sonarqube/temp'}
assert all(v['Type']=='volume' and v.get('Name') not in old_names for v in new['Mounts'])
# Separate startup receipt must prove these volumes were NEW and EMPTY;
# name inequality alone is insufficient.
network=json.loads(subprocess.check_output(['docker','network','inspect',new['HostConfig']['NetworkMode']]))[0]
assert network['Internal'] is True
safe=lambda c:{k:c[k] for k in ('Id','Image','State','Mounts')}
(out/'container-safety.json').write_text(json.dumps({'old':safe(old),'new':safe(new),
    'network':{'Id':network['Id'],'Internal':network['Internal']}},sort_keys=True,indent=2))
PY
```

Token entry is interactive and applies only to the new loopback server:

```bash
read -r -s -p 'New isolated server inspection token: ' TD521_INSPECTION_SECRET
printf '\n'
export TD521_INSPECTION_SECRET
python3 - <<'PY'
import hashlib,json,os,urllib.parse,urllib.request
from pathlib import Path
out=Path(os.environ['TD521_INSPECTION_OUT'])
base='http://127.0.0.1:19004'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise RuntimeError('Unexpected redirect; inspection aborted')
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
manifest=[]
def get(name,path,params=None):
    url=base+path+('?' + urllib.parse.urlencode(params) if params else '')
    req=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['TD521_INSPECTION_SECRET']})
    with opener.open(req,timeout=15) as r:
        assert r.status==200
        raw=r.read(20_000_001)
        assert len(raw)<=20_000_000
    with (out/name).open('xb') as f:f.write(raw)
    manifest.append({'file':name,'path':path,'params':params,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    return raw
status=json.loads(get('status.json','/api/system/status'))
assert status['status']=='UP' and status['version']=='26.8.0.126808'
assert get('version.txt','/api/server/version').decode().strip()=='26.8.0.126808'
schema=json.loads(get('webservices.json','/api/webservices/list',{'include_internals':'true'}))
actions={('/'+s['path']+'/'+a['key']):a for s in schema['webServices'] for a in s['actions']}
for path in ('/api/plugins/installed','/api/languages/list','/api/qualityprofiles/search','/api/settings/values'):
    assert path in actions and actions[path].get('post') is False
get('plugins.json','/api/plugins/installed')
get('languages.json','/api/languages/list')
get('profiles.json','/api/qualityprofiles/search')
# An absent/unsupported setting DOES NOT establish Standard mode.
get('mode-setting.json','/api/settings/values',{'keys':'sonar.multi-quality-mode.enabled'})
(out/'request-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2))
PY
unset TD521_INSPECTION_SECRET
```

Failure, authentication errors, unknown endpoints, version mismatch, changed
binary hashes or an incomplete response leave the gate BLOCKED. Do not fall
back to the old port19003, use default passwords, install a plugin or mutate
settings to force a pass. Raw inspection exports remain local and private;
publish only reviewed license-safe metadata/hashes.

## Mode, rules and configuration evidence still required

The above GETs are an initial inspection, **not full analyzer-domain admission**.
Fresh instances default to MQR. Confirm the new instance's actual
Administration → Configuration → Mode with a dated local screenshot/export and
runtime-supported API evidence. The generic system-property documentation marks
`sonar.multi-quality-mode.enabled` unsupported in Community Build; therefore do
not rely on setting an environment variable to force Standard mode. A missing
`settings/values` result is UNKNOWN, never `false`. If the installed release
requires a UI/settings mutation on the new instance, include that in the later
explicit authorization and capture before/after evidence. Never mutate the old
instance. [Mode overview](https://docs.sonarsource.com/sonarqube-community-build/instance-administration/analysis-functions/instance-mode/instance-mode-overview),
[system-property limitations](https://docs.sonarsource.com/sonarqube-community-build/server-installation/system-properties/system-properties).

Require Standard Experience and native `sqale_index` in estimated remediation
minutes. MQR maintainability effort is a different semantic family. Neither is
actual developer repair effort. Preserve mode evidence alongside raw metric
**definitions**; no project measures/outcomes are needed in this inspection.

Use the captured **installed** Web API description to bind supported methods,
required parameters, pagination fields and permission requirements before the
following GETs. Do not guess replacements when a release differs:

| Required export | Exact planned GET / binding |
| --- | --- |
| Selected profile metadata | `/api/qualityprofiles/search?language=java` and `py` / `js`; select and seal explicit keys/names, not just defaults |
| Complete profile backup | `/api/qualityprofiles/backup?language=LANG&qualityProfile=NAME`, URL-encoded from selected metadata |
| Active rules/parameters | `/api/rules/search?activation=true&qprofile=KEY&p=PAGE&ps=500&f=actives,remFn,remFnBaseEffort,remFnCoeff,defaultRemFn,defaultRemFnBaseEffort,defaultRemFnCoeff`; validate requested `f` values against installed descriptor first |
| Full per-rule remediation/overrides | `/api/rules/show?key=RULE&actives=true` for every active key; retain types, impacts, defaults and overrides, not descriptions as a proxy |
| Explicit semantic settings | `/api/settings/values?keys=KEYS` for audited scope/suffix/version/suppression/cache settings discovered in `/api/settings/list_definitions`; no unfiltered credential exports |
| Metric definitions | `/api/metrics/search?p=PAGE&ps=500`; retain definitions for Standard and MQR keys separately, not numerical project outcomes |

For each paginated API: require unchanged total, current page/size matching the
request, nonempty progress until the total is reached, exact distinct key count,
no duplicate/missing keys, every HTTP200 response archived and SHA256-bound in
ordered page manifests. If an API caps retrieval below total, partition by
language/rule repository using the installed descriptor and recheck global key
coverage. Reject partial exports. A profile backup alone does not prove all
remediation overrides. Capture safe startup settings, plugin versions/JAR hashes,
rule/profile semantics and all scope-affecting defaults/overrides before hashing
`analyzer_domain()`; do not hash UNKNOWN values as a compatible domain.

The Web API documents available endpoints in each instance and recommends bearer
authentication. The live descriptor is authoritative for26.8 parameter support.
[Official API documentation](https://docs.sonarsource.com/sonarqube-community-build/extension-guide/web-api),
[SonarSource endpoint usage](https://github.com/SonarSource/sonar-migration-tool/blob/main/API_ENDPOINTS.md).

## Subsequent gates, outside this phase

1. Verify scanner8.0.1.6346/JRE21.0.11, Maven3.9.11/Temurin17.0.17+10 and embedded
   Node24.11.0 with no-scan/no-build version probes in separately admitted
   sandboxes, using the pinned images/artifact hashes. No remote provisioning.
2. Resolve missing parent POMs71/76/78 and any transitive gaps via a separately
   authorized, pinned dependency acquisition step; currently no install/fetch is
   authorized. Parent74's presence does not prove a complete effective graph.
3. Obtain per-tree header/origin review, source/data/tool reuse acceptance and
   runtime permissions. New source registrations stay quarantined until then.
4. Only after separate historical-build/collection authorization: prove all Java
   builds/classpaths, seal18 configurations and unchanged limits, then collect
   native scanner/CE/file-component evidence as specified in the original plan.
   The new admission adapter requires exact Git production-file/language equality,
   not aggregate counts. No target/prediction can be created from this handoff.
