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

BASE = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(32)
PORT = int(os.environ.get('AI_MANAGER_PORT', '0'))
LOCK = threading.Lock()
STATE = {'busy': False, 'job': None, 'message': 'Ready', 'error': None}
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
        if path.startswith('/mnt/nas/') and not Path(path).is_mount():
            return {'name': label, 'online': False}
        st = os.statvfs(path)
        return {'name': label, 'online': True, 'total': st.f_blocks * st.f_frsize,
                'free': st.f_bavail * st.f_frsize}
    except OSError:
        return {'name': label, 'online': False}

def telemetry():
    rows, total, free, gpu, errors, _, _ = core.snapshot(False)
    out = {'models': rows, 'memory': {'total': total, 'available': free, 'used': total-free},
           'gpu': gpu, 'cpu': cpu_usage(), 'errors': errors, 'time': int(time.time()),
           'storage': [disk_info(str(Path.home()), 'ASUS system'),
                       disk_info('/mnt/ai-models', 'External NVMe'),
                       disk_info('/mnt/nas/AI-Models', 'NAS model library'),
                       disk_info('/mnt/nas/Storage', 'NAS archive')]}
    with LOCK:
        out['operation'] = dict(STATE)
        HISTORY.append({'time': out['time'], 'memory': out['memory']['used'], 'cpu': out['cpu']})
        out['history'] = list(HISTORY)
    return out

def activity():
    try:
        lines = core.LOG_PATH.read_text(encoding='utf8').splitlines()[-65:]
        return [json.loads(line) for line in reversed(lines) if line.strip()]
    except (OSError, json.JSONDecodeError):
        return []

def run_job(action, target, stops):
    global STATE
    ok = False
    try:
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
                ok, msg = core.swap_with_rollback([rows[s] for s in stops], rows[target])
            else:
                raise RuntimeError('Target already loaded.')
        else:
            desired = action == 'load'
            if core.is_loaded(rows[target]) == desired:
                raise RuntimeError('Model state changed; please refresh.')
            core.log_event(action, 'started', rows[target]['name'])
            core.execute(rows[target], desired)
            ok = core.verify(rows[target], desired, 150 if desired else 60)
            if not ok:
                raise RuntimeError('Command ran, but actual runtime state was not verified.')
            msg = f'{rows[target]["name"]}: {"loaded" if desired else "unloaded"} and verified.'
            core.log_event(action, 'verified', rows[target]['name'])
    except Exception as exc:
        msg = str(exc)
        core.log_event(action, 'failed', target, msg)
    with LOCK:
        STATE.update(busy=False, message=msg, error=None if ok else msg, job=None)

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
        return self.headers.get('X-Session-Token') == TOKEN
    def do_GET(self):
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
        return self.respond(404, {'error': 'Not found'})
    def do_POST(self):
        if urlparse(self.path).path != '/api/action':
            return self.respond(404, {'error': 'Not found'})
        if not self.authorized():
            return self.respond(403, {'error': 'Unauthorized'})
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
                    or any(not isinstance(stop, str) or not stop for stop in stops)
                    or len(stops) != len(set(stops))):
                raise ValueError('Invalid operation')
            with LOCK:
                if STATE['busy']:
                    return self.respond(409, {'error': 'An operation is already running'})
                STATE.update(busy=True, job=f'{action}: {target}', error=None, message='Operation started')
            try:
                threading.Thread(target=run_job, args=(action, target, stops), daemon=True).start()
            except RuntimeError:
                with LOCK:
                    STATE.update(busy=False, job=None, message='Could not start operation', error='Could not start operation')
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
