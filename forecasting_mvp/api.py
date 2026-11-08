"""Read-only, loopback-only standard library presentation server."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from contracts import safe_id
from .io import artifact_path
from .persistence_flow import HORIZONS, load_presentation

PREFIX = '/api/mvp/v1'
STATIC = Path(__file__).parent/'static'


def registry_bundles(registry):
    root = Path(registry).absolute()
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Registry must be a real directory')
    bundles = {}
    for path in sorted(root.iterdir()):
        if path.name.startswith('.'):
            continue
        safe_id(path.name)
        if not path.is_dir() or path.is_symlink():
            raise ValueError('Registry entries must be bundle directories')
        bundle = load_presentation(artifact_path(root, path.name))
        identity = bundle['manifest']['bundle_id']
        if identity in bundles:
            raise ValueError('Duplicate registry bundle identity')
        bundles[identity] = bundle
    return bundles


def create_server(registry, host='127.0.0.1', port=8765):
    if host != '127.0.0.1':
        raise ValueError('Server binds only to 127.0.0.1')
    root = Path(registry).absolute()
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Existing registry directory required')

    class Handler(BaseHTTPRequestHandler):
        server_version = 'PersistenceLocal/1'

        def log_message(self, *args):
            pass

        def respond(self, status, obj, content_type='application/json; charset=utf-8'):
            body = obj if isinstance(obj, bytes) else json.dumps(obj, allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            host_header = self.headers.get('Host', '').split(':')[0]
            if host_header not in ('127.0.0.1', 'localhost'):
                return self.respond(403, {'error': 'Local Host required'})
            try:
                parts = urlsplit(self.path)
                path = unquote(parts.path)
                query = parse_qs(parts.query, keep_blank_values=True, strict_parsing=True, max_num_fields=8)
                if any(len(v) != 1 for v in query.values()):
                    raise ValueError('Duplicate query parameter')
                if path in ('/', '/app.js', '/style.css'):
                    if query:
                        raise ValueError('Static assets take no query')
                    name, mime = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css')}[path]
                    return self.respond(200, (STATIC/name).read_bytes(), mime+'; charset=utf-8')
                if not path.startswith(PREFIX+'/'):
                    return self.respond(404, {'error': 'Unknown route'})
                route = path[len(PREFIX)+1:].split('/')
                if route == ['health']:
                    if query:
                        raise ValueError('Health takes no query')
                    return self.respond(200, {'status': 'PASS', 'model': 'persistence', 'current_accuracy': 'UNVALIDATED'})
                if route[0] != 'bundles':
                    return self.respond(404, {'error': 'Unknown route'})
                # A request always re-verifies the artifacts; no stale trusted cache.
                try:
                    bundles = registry_bundles(root)
                except (ValueError, OSError, TypeError, KeyError) as exc:
                    return self.respond(409, {'error': 'Corrupt or incomplete registry bundle', 'detail': str(exc)})
                if route == ['bundles']:
                    if query:
                        raise ValueError('Bundle list takes no query')
                    return self.respond(200, [b['manifest'] for b in bundles.values()])
                identity = safe_id(route[1])
                if identity not in bundles:
                    return self.respond(404, {'error': 'Unknown bundle'})
                bundle = bundles[identity]
                if len(route) == 2:
                    if query:
                        raise ValueError('Bundle metadata takes no query')
                    return self.respond(200, bundle['manifest'])
                if route[2] != 'repositories':
                    return self.respond(404, {'error': 'Unknown route'})
                repos = sorted({r['repository_id'] for r in bundle['history']})
                if len(route) == 3:
                    if query:
                        raise ValueError('Repository list takes no query')
                    return self.respond(200, repos)
                repo = safe_id(route[3])
                if repo not in repos:
                    return self.respond(404, {'error': 'Unknown repository'})
                if len(route) != 5 or route[4] not in ('history', 'forecasts', 'evaluations'):
                    return self.respond(404, {'error': 'Unknown route'})
                resource = route[4]
                rows = [r for r in bundle[resource] if r['repository_id'] == repo]
                if resource == 'history':
                    if query:
                        raise ValueError('History takes no query')
                else:
                    summary = query.get('summary', ['false'])[0]
                    if 'summary' in query and (resource != 'evaluations' or summary != 'true'):
                        raise ValueError('summary=true is supported only for evaluations')
                    parameters = set(query) - {'summary'}
                    if parameters not in ({'horizon', 'horizon_unit'}, {'horizon', 'horizon_unit', 'model'}):
                        raise ValueError('Explicit horizon and horizon_unit required')
                    if query.get('model', ['persistence'])[0] != 'persistence':
                        raise ValueError('Only persistence is available')
                    unit, raw = query['horizon_unit'][0], query['horizon'][0]
                    if unit not in HORIZONS or raw not in [str(h) for h in HORIZONS[unit]]:
                        raise ValueError('Unregistered horizon/unit')
                    rows = [r for r in rows if r['horizon_unit'] == unit and r['horizon'] == int(raw)]
                    if not rows:
                        return self.respond(200, {'status': 'UNSUPPORTED_DATA', 'data': None,
                            'reason': 'Horizon/unit unavailable for this target bundle',
                            'horizon_unit': unit, 'horizon': int(raw)})
                    if summary == 'true':
                        rows = [r for r in bundle['evaluation_summary']
                                if r['horizon_unit'] == unit and r['horizon'] == int(raw)]
                return self.respond(200, rows)
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                return self.respond(422, {'error': str(exc)})
            except OSError:
                return self.respond(409, {'error': 'Artifact unavailable'})

        def mutation(self):
            self.close_connection = True
            self.respond(405, {'error': 'GET only'})

        do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = do_TRACE = do_CONNECT = mutation

    return ThreadingHTTPServer((host, port), Handler)


def serve(registry, host='127.0.0.1', port=8765):
    server = create_server(registry, host, port)
    print(f'Persistence dashboard: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return {'status': 'PASS'}
