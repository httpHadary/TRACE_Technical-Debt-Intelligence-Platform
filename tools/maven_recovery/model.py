"""Conservative static POM inventory; not a substitute for Maven's effective model.

Only XML/ZIP data is read. Unresolved versions, ranges and unsupported activation
are recorded, never replaced with an invented release or silently executed.
"""
import copy
import io
import re
import urllib.error
import zipfile
from .acquisition import parse_xml, relative_path

NS = {'m': 'http://maven.apache.org/POM/4.0.0'}
PHASES = ('validate', 'initialize', 'generate-sources', 'process-sources',
          'generate-resources', 'process-resources', 'compile')


def text(e, key, default=None):
    return e.findtext('m:' + key, default=default, namespaces=NS)


def expand(value, properties):
    if value is None:
        return None
    for _ in range(30):
        new = re.sub(r'\$\{([^}]+)\}', lambda m: properties.get(m[1], m[0]), value)
        if new == value:
            break
        value = new
    return value


def major(version):
    parts = version.split('.')
    return int(parts[1] if parts[0] == '1' and len(parts) > 1 else parts[0])


def jdk_matches(spec, actual=17):
    if spec.startswith('!'):
        return not jdk_matches(spec[1:], actual)
    if spec.startswith(('[', '(')):
        if ',' not in spec:
            if spec[0] != '[' or spec[-1] != ']':
                raise ValueError('Unsupported exact JDK range')
            return actual == major(spec[1:-1])
        low, high = spec[1:-1].split(',')
        return ((not low or actual >= major(low) + (spec[0] == '('))
                and (not high or actual <= major(high) - (spec[-1] == ')')))
    return str(actual).startswith(spec)


def activation(profile, files, user):
    act = profile.find('m:activation', NS)
    if act is None:
        return False, 'NO_IMPLICIT_ACTIVATION'
    checks = []
    for child in act:
        key = child.tag.split('}')[-1]
        if key == 'jdk':
            try:
                checks.append(jdk_matches(child.text))
            except ValueError:
                return None, 'UNSUPPORTED_JDK_ACTIVATION_' + repr(child.text)
        elif key == 'file':
            for kind in ('exists', 'missing'):
                path = text(child, kind)
                if path:
                    path = path.replace('${basedir}/', '').replace('${project.basedir}/', '')
                    if '${' in path or path.startswith('/') or '..' in path.split('/'):
                        return None, 'UNRESOLVED_FILE_ACTIVATION'
                    present = path in files or any(n.startswith(path.rstrip('/') + '/') for n in files)
                    checks.append(present if kind == 'exists' else not present)
        elif key == 'property':
            name, value = text(child, 'name'), text(child, 'value')
            if name.startswith('!'):
                checks.append(name[1:] not in user)
            elif value is None:
                checks.append(name in user)
            elif value.startswith('!'):
                checks.append(user.get(name) != value[1:])
            else:
                checks.append(user.get(name) == value)
        elif key == 'activeByDefault':
            checks.append(child.text == 'true')
        else:
            return None, 'UNSUPPORTED_ACTIVATION_' + key
    return all(checks) if checks else False, 'STATIC_JDK17_FILES_AND_FIXED_USER_PROPERTIES'


def merge_xml(parent, child):
    """Small XML merge for dependency/plugin declarations, not arbitrary config."""
    result = copy.deepcopy(parent)
    for part in child:
        key = part.tag.split('}')[-1]
        old = result.find(part.tag)
        if key in ('executions', 'dependencies') and old is not None:
            for row in part:
                if key == 'executions':
                    identity = lambda e: text(e, 'id', 'default')
                else:
                    identity = lambda e: (text(e, 'groupId'), text(e, 'artifactId'), text(e, 'type', 'jar'), text(e, 'classifier', ''))
                match = next((e for e in old if identity(e) == identity(row)), None)
                if match is not None:
                    index = list(old).index(match);old.remove(match);old.insert(index, merge_xml(match, row))
                else:
                    old.append(copy.deepcopy(row))
        else:
            if old is not None:
                result.remove(old)
            result.append(copy.deepcopy(part))
    return result


class Models:
    def __init__(self, acquisition):
        self.a = acquisition
        self.models = {}
        self.busy = set()
        self.issues = []

    def issue(self, kind, identity, reason):
        row = dict(kind=kind, identity=identity, reason=str(reason))
        if row not in self.issues:
            self.issues.append(row)

    def remote(self, gav):
        gav = tuple(gav)
        if gav in self.models:
            return self.models[gav]
        if gav in self.busy:
            raise ValueError('POM parent/import cycle')
        self.busy.add(gav)
        try:
            result = self.build(parse_xml(self.a.get(*gav)), files=(), user={}, identity=gav)
            self.models[gav] = result
            return result
        finally:
            self.busy.remove(gav)

    def layers(self, pom, seen=()):
        parent = pom.find('m:parent', NS)
        result = []
        if parent is not None:
            gav = tuple(text(parent, k) for k in ('groupId', 'artifactId', 'version'))
            relative_path(*gav)
            if gav in seen or len(seen) > 20:
                raise ValueError('Parent chain cycle/depth')
            result += self.layers(parse_xml(self.a.get(*gav)), seen + (gav,))
        return result + [pom]

    def build(self, pom, files, user, identity):
        layers = self.layers(pom)
        props = {}; parts = []; profiles = []; chain = []
        for layer in layers:
            parent = layer.find('m:parent', NS)
            group = text(layer, 'groupId') or (text(parent, 'groupId') if parent is not None else None)
            version = text(layer, 'version') or (text(parent, 'version') if parent is not None else None)
            chain.append([group, text(layer, 'artifactId'), version])
            parts.append(layer)
            for profile in layer.findall('m:profiles/m:profile', NS):
                enabled, reason = activation(profile, files, user)
                profiles.append(dict(model=chain[-1], id=text(profile, 'id'), active=enabled, reason=reason))
                if enabled:
                    parts.append(profile)
                elif enabled is None:
                    self.issue('PROFILE', list(identity), profiles[-1])
            for part in parts[-(1 + sum(1 for x in profiles if x['model'] == chain[-1] and x['active'])):]:
                element = part.find('m:properties', NS)
                if element is not None:
                    props.update({p.tag.split('}')[-1]: p.text or '' for p in element})
        props.update({'project.groupId': chain[-1][0] or '', 'project.artifactId': chain[-1][1],
                      'project.version': chain[-1][2] or '', 'pom.version': chain[-1][2] or ''})
        if len(chain) > 1:
            props.update({'project.parent.groupId': chain[-2][0], 'project.parent.version': chain[-2][2],
                          'project.parent.artifactId': chain[-2][1]})
        props.update(user)
        for _ in range(30):
            new = {k: expand(v, props) for k, v in props.items()}
            if new == props:
                break
            props = new
        management = {}; dependencies = {}; plugins = {}; managed_plugins = {}; imports = []
        for part in parts:
            local_management = {}
            for e in part.findall('m:dependencyManagement/m:dependencies/m:dependency', NS):
                row = self.dependency(e, props)
                if row['scope'] == 'import' and row['type'] == 'pom':
                    try:
                        gav = row['gav'];relative_path(*gav)
                        imported = self.remote(gav)
                        for key, value in imported['management'].items():
                            local_management.setdefault(key, value)
                        imports.append(gav)
                    except (ValueError, urllib.error.HTTPError) as exc:
                        self.issue('BOM', row['gav'], exc)
                else:
                    local_management[self.depkey(row)] = row
            management.update(local_management)
            for e in part.findall('m:dependencies/m:dependency', NS):
                row = self.dependency(e, props)
                key = self.depkey(row)
                inherited = dependencies.get(key)
                if inherited:
                    for field in ('scope', 'optional', 'exclusions'):
                        if field not in row['explicit_fields']:
                            row[field] = inherited[field]
                    if 'version' not in row['explicit_fields']:
                        row['gav'][2] = inherited['gav'][2]
                    row['explicit_fields'] = sorted(set(row['explicit_fields']) | set(inherited['explicit_fields']))
                dependencies[key] = row
            for query, target in (('m:build/m:pluginManagement/m:plugins/m:plugin', managed_plugins),
                                  ('m:build/m:plugins/m:plugin', plugins)):
                for e in part.findall(query, NS):
                    key = (text(e, 'groupId', 'org.apache.maven.plugins'), text(e, 'artifactId'))
                    target[key] = merge_xml(target[key], e) if key in target else copy.deepcopy(e)
        for key, row in dependencies.items():
            managed = management.get(key)
            if managed:
                if row['gav'][2] is None:
                    row['gav'][2] = managed['gav'][2]
                for field in ('scope', 'optional', 'exclusions'):
                    if field not in row['explicit_fields']:
                        row[field] = managed[field]
        for key, e in list(plugins.items()):
            if key in managed_plugins:
                plugins[key] = merge_xml(managed_plugins[key], e)
        return dict(properties=props, management=management, dependencies=list(dependencies.values()),
                    plugins=plugins, managed_plugins=managed_plugins, profiles=profiles, chain=chain, imports=imports)

    @staticmethod
    def depkey(row):
        return (*row['gav'][:2], row['type'], row['classifier'])

    @staticmethod
    def dependency(e, props):
        get = lambda key, default=None: expand(text(e, key, default), props)
        return dict(gav=[get(k) for k in ('groupId', 'artifactId', 'version')],
            type=get('type', 'jar'), classifier=get('classifier', ''), scope=get('scope', 'compile'),
            optional=get('optional', 'false') == 'true',
            explicit_fields=sorted(child.tag.split('}')[-1] for child in e),
            exclusions=[[text(x, k) for k in ('groupId', 'artifactId')]
                        for x in e.findall('m:exclusions/m:exclusion', NS)])

    def closure(self, roots, reason):
        """Exact conservative runtime dependency union; no mediation claim."""
        queue = [(r, True, ()) for r in roots]; visited = set(); edges = []
        for row, direct, excluded in queue:
            gav = row['gav']; key = (*gav, row['type'], row['classifier'], tuple(excluded))
            if key in visited:
                continue
            visited.add(key)
            try:
                relative_path(*gav)
                if row['type'] not in ('jar', 'pom', 'test-jar', 'maven-plugin'):
                    raise ValueError('Unsupported dependency type: ' + row['type'])
                model = self.remote(gav)
                if row['type'] != 'pom':
                    self.a.get(*gav, 'jar', row['classifier'] or ('tests' if row['type'] == 'test-jar' else ''))
                edges.append(dict(gav=gav, type=row['type'], classifier=row['classifier'], reason=reason))
                for dep in model['dependencies']:
                    if dep['scope'] not in ('compile', 'runtime') or dep['optional']:
                        continue
                    exclusions = tuple(excluded) + tuple(tuple(x) for x in row['exclusions'])
                    if any((g in ('*', dep['gav'][0]) and a in ('*', dep['gav'][1])) for g, a in exclusions):
                        continue
                    queue.append((dep, False, exclusions))
            except (ValueError, urllib.error.HTTPError) as exc:
                self.issue('DEPENDENCY', gav, exc)
        return edges

    def compile_plugins(self, model):
        # Versions come from the inherited POM; Maven3.9.11's default jar binding
        # is only a fallback for resources when no managed version exists.
        plugins = dict(model['plugins'])
        for artifact, fallback, phase, goal in (
                ('maven-resources-plugin', '3.3.1', 'process-resources', 'resources'),
                ('maven-compiler-plugin', '3.13.0', 'compile', 'compile')):
            key = ('org.apache.maven.plugins', artifact)
            if key not in plugins:
                plugins[key] = copy.deepcopy(model['managed_plugins'].get(key)) if key in model['managed_plugins'] else parse_xml(
                    ('<plugin xmlns="' + NS['m'] + '"><artifactId>' + artifact
                     + '</artifactId><version>' + fallback + '</version></plugin>').encode())
        output = []
        for (group, artifact), plugin in plugins.items():
            executions = plugin.findall('m:executions/m:execution', NS)
            default = artifact in ('maven-resources-plugin', 'maven-compiler-plugin')
            potential = default or any(text(e, 'phase') in PHASES or text(e, 'phase') is None for e in executions)
            version = expand(text(plugin, 'version'), model['properties'])
            known_required = default or any(text(e, 'phase') in PHASES for e in executions)
            record = dict(gav=[group, artifact, version], required_through_compile=True if known_required else (None if potential else False),
                          executions=[], dependencies=[], disposition='LATER_PHASE_OR_UNBOUND')
            output.append(record)
            if not potential:
                continue
            try:
                relative_path(group, artifact, version)
                self.remote((group, artifact, version))
                raw = self.a.get(group, artifact, version, 'jar')
                with zipfile.ZipFile(io.BytesIO(raw)) as jar:
                    descriptor = parse_xml(jar.read('META-INF/maven/plugin.xml'))
                mojo = {m.findtext('goal'): m for m in descriptor.findall('mojos/mojo')}
                if default:
                    record['executions'].append(dict(id='DEFAULT_JAR_BINDING', phase='compile' if artifact == 'maven-compiler-plugin' else 'process-resources'))
                for e in executions:
                    for goal in e.findall('m:goals/m:goal', NS):
                        if goal.text not in mojo:
                            raise ValueError('Goal missing from plugin descriptor: ' + goal.text)
                        phase = text(e, 'phase') or mojo[goal.text].findtext('phase')
                        record['executions'].append(dict(id=text(e, 'id', 'default'), goal=goal.text, phase=phase))
                required = any(e['phase'] in PHASES for e in record['executions'])
                record['required_through_compile'] = required
                record['disposition'] = 'ACQUIRE_STATIC_COMPILE_CLOSURE' if required else 'DESCRIPTOR_VERIFIED_LATER_PHASE'
                if required:
                    root = dict(gav=[group, artifact, version], type='jar', classifier='', scope='compile', optional=False, exclusions=[])
                    configured = [self.dependency(e, model['properties']) for e in plugin.findall('m:dependencies/m:dependency', NS)]
                    record['dependencies'] = self.closure([root, *configured], 'compile plugin ' + artifact)
            except (ValueError, urllib.error.HTTPError, KeyError) as exc:
                record['disposition'] = 'UNRESOLVED';self.issue('PLUGIN', record['gav'], exc)
        return output
