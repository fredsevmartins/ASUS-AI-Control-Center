#!/usr/bin/env python3
"""Localhost-only ASUS AI Model Manager v5. Never reconfigures existing runtimes."""
import json
import os
import secrets
import threading
import time
import webbrowser
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import core
import intelligence as intel

BASE = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(32)
PORT = int(os.environ.get('AI_MANAGER_PORT', '0'))
LOCK = threading.Lock()
SAMPLING_LOCK = threading.Lock()
STATE = {'busy': False, 'job': None, 'message': 'Ready', 'error': None}
PLANS = {}
PLAN_TTL = 120
HISTORY = deque(maxlen=180)
CPU_SAMPLE = None

def cpu_usage():
    global CPU_SAMPLE
    try:
        with open('/proc/stat', encoding='ascii') as f:
            vals = [int(x) for x in f.readline().split()[1:]]
        # guest and guest_nice are already included in user and nice.
        idle, total = vals[3] + vals[4], sum(vals[:8])
        prev = CPU_SAMPLE
        CPU_SAMPLE = (idle, total)
        if prev and total > prev[1]:
            return round(100 * (1 - (idle - prev[0]) / (total - prev[1])), 1)
    except (OSError, ValueError, IndexError):
        pass
    return None

def disk_info(path, label):
    try:
        if path.startswith('/mnt/') and not Path(path).is_mount():
            return {'name': label, 'online': False}
        st = os.statvfs(path)
        return {'name': label, 'online': True, 'total': st.f_blocks * st.f_frsize,
                'free': st.f_bavail * st.f_frsize}
    except OSError:
        return {'name': label, 'online': False}

def telemetry():
    # Concurrent tabs must not race CPU deltas or append out-of-order samples.
    with SAMPLING_LOCK:
        return _telemetry()


def _telemetry():
    rows, total, free, gpu, errors, _, _ = core.snapshot(False)
    out = {'models': rows, 'memory': {'total': total, 'available': free, 'used': total-free if total is not None and free is not None else None},
           'gpu': gpu, 'cpu': cpu_usage(), 'errors': errors, 'time': int(time.time()),
           'storage': [disk_info(str(Path.home()), 'ASUS system'),
                       disk_info('/mnt/ai-models', 'External NVMe'),
                       disk_info('/mnt/nas/AI-Models', 'NAS model library'),
                       disk_info('/mnt/nas/Storage', 'NAS archive')]}
    with LOCK:
        out['operation'] = dict(STATE)
        for row in rows:
            row['state'] = intel.model_state(row, STATE)
        HISTORY.append({'time': out['time'], 'memory': out['memory']['used'], 'cpu': out['cpu']})
        out['history'] = list(HISTORY)
    return out

def activity():
    try:
        with core.LOG_PATH.open('rb') as stream:
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - 131072))
            lines = stream.read(131072).decode('utf8', errors='replace').splitlines()[-65:]
        events = []
        for line in reversed(lines):
            try:
                event = json.loads(line)
                if isinstance(event, dict):
                    events.append(event)
            except json.JSONDecodeError:
                continue
        return events
    except (OSError, json.JSONDecodeError):
        return []

def prepare(action, target, stops):
    rows, total, available, _, errors, _, _ = core.snapshot(False, fresh=True)
    rows = [core.model_details(r) if r['key'] == target else r for r in rows]
    plan = intel.preflight(rows, total, available, errors, action, target, stops)
    return plan, {r['key']: r for r in rows}


def progress(phase, **detail):
    if phase not in intel.PHASES:
        raise ValueError('Invalid operation phase')
    with LOCK:
        STATE.update(phase=phase, updated_at=int(time.time()), **detail)


def check_load_memory(row):
    estimate = intel.runtime_requirement(row)['bytes']
    total, available = core.memory()
    if intel.positive(total) is None or intel.number(available) is None or available > total:
        raise RuntimeError('Available memory cannot be verified; loading blocked.')
    reserve = max(4 * intel.GIB, total * .05)
    if available < reserve or (estimate is not None and available < estimate + reserve):
        raise RuntimeError('Available memory changed or unload reclaimed less than expected; loading blocked.')


def _run_job(action, target, stops, confirmed_plan=None):
    global STATE
    ok = False
    try:
        progress('precheck')
        if confirmed_plan is not None:
            if confirmed_plan['expires_at'] <= time.time():
                raise RuntimeError('Preflight plan expired before execution; review a new preflight.')
            current, rows = prepare(action, target, stops)
            if current['blocked'] or current['fingerprint'] != confirmed_plan['fingerprint']:
                raise RuntimeError('Runtime state or memory changed after confirmation; review a new preflight.')
        else:
            rows = {r['key']: r for r in core.snapshot(False)[0]}
        if target not in rows:
            raise RuntimeError('Model no longer registered; refresh the dashboard.')
        if rows[target].get('uncertain'):
            raise RuntimeError('SGLang service and container disagree; action blocked.')
        if action == 'switch':
            if not isinstance(stops, list) or len(stops) != len(set(stops)):
                raise ValueError('Invalid stop list.')
            if target in stops or any(s not in rows or rows[s].get('uncertain') for s in stops):
                raise ValueError('Invalid model selection.')
            if not core.is_loaded(rows[target]):
                for s in stops:
                    if not core.is_loaded(rows[s]):
                        raise ValueError(f'Model is no longer loaded: {rows[s]["name"]}')
                ok, msg = core.swap_with_rollback([rows[s] for s in stops], rows[target], progress,
                                                  lambda: check_load_memory(rows[target]), check_load_memory)
            else:
                raise RuntimeError('Target already loaded.')
        else:
            desired = action == 'load'
            if core.is_loaded(rows[target]) == desired:
                raise RuntimeError('Model state changed; please refresh.')
            core.log_event(action, 'started', rows[target]['name'])
            if desired:
                check_load_memory(rows[target])
            progress('load' if desired else 'unload', model=target)
            core.execute(rows[target], desired)
            progress('readiness' if desired else 'verification')
            ok = core.verify(rows[target], desired, 150 if desired else 60)
            if not ok:
                raise RuntimeError('Command ran, but actual runtime state was not verified.')
            msg = f'{rows[target]["name"]}: {"resident" if desired else "unloaded"} and verified. Inference execution was not probed.'
            core.log_event(action, 'verified', rows[target]['name'])
    except Exception as exc:
        msg = str(exc)
        core.log_event(action, 'failed', target, msg)
    with LOCK:
        STATE.update(busy=False, message=msg, error=None if ok else msg, job=None,
                     phase='complete' if ok else 'failed', finished_at=int(time.time()))
    intel.CACHE.clear()

def run_job(action, target, stops, confirmed_plan=None):
    try:
        with core.lifecycle_lock():
            _run_job(action, target, stops, confirmed_plan)
    except Exception as exc:
        with LOCK:
            STATE.update(busy=False, job=None, phase='failed', error=str(exc), message=str(exc), finished_at=int(time.time()))


class Handler(BaseHTTPRequestHandler):
    server_version = 'ASUSModelManager/5.0'
    def log_message(self, fmt, *args):
        pass
    def respond(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode('utf8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def authorized(self):
        value = self.headers.get('X-Session-Token', '')
        return secrets.compare_digest(value.encode('utf8'), TOKEN.encode('utf8'))
    def local_request(self):
        """Reject DNS rebinding and cross-origin requests before reading bodies."""
        address = self.server.server_address
        expected_host = f'127.0.0.1:{address[1]}'
        if self.headers.get('Host') != expected_host:
            return False
        origin = self.headers.get('Origin')
        return ((origin is None or origin == 'http://' + expected_host)
                and self.headers.get('Sec-Fetch-Site') not in ('cross-site', 'same-site'))
    def do_GET(self):
        if not self.local_request():
            return self.respond(403, {'error': 'Local same-origin access required'})
        parsed = urlparse(self.path)
        if parsed.path == '/':
            if parse_qs(parsed.query).get('token', [''])[0] != TOKEN:
                return self.respond(403, {'error': 'Launch using the desktop shortcut.'})
            data = (BASE/'web/index.html').read_text().replace('__TOKEN__', TOKEN).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        if parsed.path in ('/style.css', '/app.js'):
            path = BASE/'web'/parsed.path[1:]
            data = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/css' if path.suffix == '.css' else 'text/javascript')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        if not self.authorized():
            return self.respond(403, {'error': 'Session token required'})
        if parsed.path == '/api/status':
            return self.respond(200, telemetry())
        if parsed.path == '/api/library':
            files, info = core._nas_scan()
            groups = core.group_nas_files(files)
            for g in groups:
                g['formats'] = sorted(g['formats'])
            return self.respond(200, {'files': files, 'groups': groups, 'status': info})
        if parsed.path == '/api/activity':
            return self.respond(200, activity())
        if parsed.path == '/api/model':
            key = parse_qs(parsed.query).get('key', [''])[0]
            rows = core.snapshot(False)[0]
            row = next((r for r in rows if r['key'] == key), None)
            if row is None:
                return self.respond(404, {'error': 'Model not registered'})
            detail = core.model_details(row)
            detail['recent_operations'] = [e for e in activity() if e.get('model') in (row['name'], key)][:8]
            return self.respond(200, detail)
        return self.respond(404, {'error': 'Not found'})
    def do_POST(self):
        if not self.local_request():
            return self.respond(403, {'error': 'Local same-origin access required'})
        path = urlparse(self.path).path
        if path not in ('/api/action', '/api/preflight'):
            return self.respond(404, {'error': 'Not found'})
        if not self.authorized():
            return self.respond(403, {'error': 'Unauthorized'})
        if self.headers.get('Transfer-Encoding'):
            return self.respond(400, {'error': 'Transfer encoding is unsupported'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.respond(415, {'error': 'JSON required'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length > 8192 or length <= 0:
                raise ValueError('Invalid body length')
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError('JSON object required')
            action, target, stops = body.get('action'), body.get('target'), body.get('stops', [])
            if (action not in ('load', 'unload', 'switch') or not isinstance(target, str)
                    or not target or not isinstance(stops, list)
                    or any(not isinstance(stop, str) or not stop or len(stop) > 512 for stop in stops)
                    or len(stops) > 128 or len(target) > 512
                    or len(stops) != len(set(stops)) or (action != 'switch' and stops)):
                raise ValueError('Invalid operation')
            if path == '/api/preflight':
                with LOCK:
                    if STATE['busy']:
                        return self.respond(409, {'error': 'An operation is already running'})
                plan, _ = prepare(action, target, stops)
                plan['id'] = secrets.token_urlsafe(24)
                plan['phase'] = 'confirmation'
                plan['expires_at'] = int(time.time()) + PLAN_TTL
                with LOCK:
                    # A plan never authorizes execution by itself.
                    for key in list(PLANS):
                        if PLANS[key]['expires_at'] <= time.time():
                            del PLANS[key]
                    if len(PLANS) >= 64:
                        del PLANS[next(iter(PLANS))]
                    PLANS[plan['id']] = plan
                return self.respond(200, plan)
            if body.get('confirmed') is not True or body.get('acknowledge_risks') is not True:
                raise ValueError('Explicit plan confirmation and risk acknowledgement required')
            plan_id = body.get('plan_id')
            if not isinstance(plan_id, str):
                raise ValueError('Preflight plan required')
            with LOCK:
                if STATE['busy']:
                    return self.respond(409, {'error': 'An operation is already running'})
                plan = PLANS.pop(plan_id, None)
                if not plan or plan['expires_at'] <= time.time() or plan['blocked']:
                    return self.respond(409, {'error': 'Plan expired, consumed or blocked; review a new preflight'})
                if any(plan[k] != v for k, v in [('action', action), ('target', target), ('stops', stops)]):
                    raise ValueError('Operation does not match the reviewed plan')
                STATE.clear()
                STATE.update(busy=True, job=f'{action}: {target}', id=secrets.token_urlsafe(16),
                             action=action, target=target, stops=stops, phase='precheck',
                             started_at=int(time.time()), error=None, message='Operation started')
            try:
                threading.Thread(target=run_job, args=(action, target, stops, plan), daemon=True).start()
            except RuntimeError:
                with LOCK:
                    STATE.update(busy=False, job=None, phase='failed', message='Could not start operation', error='Could not start operation')
                return self.respond(503, {'error': 'Could not start operation'})
            return self.respond(202, {'message': 'Accepted. Monitor the operation status.'})
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return self.respond(400, {'error': str(exc)})

def main():
    httpd = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    port = httpd.server_address[1]
    url = f'http://127.0.0.1:{port}/?token={TOKEN}'
    print(f'AI Model Manager v5 — local-only at http://127.0.0.1:{port} (Ctrl+C to stop)', flush=True)
    threading.Timer(0.65, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == '__main__':
    main()
