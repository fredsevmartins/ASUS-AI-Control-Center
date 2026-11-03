#!/usr/bin/env python3
"""User-session desktop supervisor. No runtime mutations or persisted credentials."""
import argparse
import fcntl
import http.client
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
from urllib.parse import parse_qs, urlparse

BASE = Path(__file__).resolve().parent
TIMEOUT = 15


def private_directory():
    root = Path(os.environ.get('XDG_RUNTIME_DIR', f'/tmp/asus-ai-{os.getuid()}'))
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise RuntimeError('User runtime directory must be private and owned by you.')
    path = root / 'asus-ai-control-center'
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise RuntimeError('Desktop runtime directory must be private and owned by you.')
    return path


def browser_command(url):
    preference = os.environ.get('ASUS_AI_BROWSER', 'auto')
    if preference not in ('auto', 'chromium', 'firefox'):
        raise RuntimeError('ASUS_AI_BROWSER must be auto, chromium or firefox.')
    if preference != 'firefox':
        for name in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable'):
            executable = shutil.which(name)
            if executable:
                return [executable, '--app=' + url, '--window-size=1440,960',
                        '--class=asus-ai-control-center']
    if preference != 'chromium' and shutil.which('firefox'):
        return [shutil.which('firefox'), '--new-window', url, '--width', '1440', '--height', '960']
    raise RuntimeError('No supported browser found. Install or enable Chromium or Firefox.')


class Tickets:
    def __init__(self):
        self.values = {}
        self.lock = threading.Lock()

    def issue(self):
        with self.lock:
            now = time.monotonic()
            self.values = {k: v for k, v in self.values.items() if v > now}
            ticket = secrets.token_urlsafe(32)
            self.values[ticket] = now + 30
            return ticket

    def consume(self, ticket):
        with self.lock:
            return self.values.pop(ticket, 0) > time.monotonic()


def desktop_handler(backend, tickets):
    class DesktopHandler(backend.Handler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == '/' and 'launch' in parse_qs(parsed.query):
                if not self.local_request():
                    return self.respond(403, {'error': 'Local same-origin access required'})
                ticket = parse_qs(parsed.query)['launch'][0]
                if not tickets.consume(ticket):
                    return self.respond(403, {'error': 'Launch expired. Reopen using the desktop icon.'})
                # Render through the existing authenticated handler. The session token
                # never enters process arguments, disk state or browser history.
                self.path = '/?token=' + backend.TOKEN
            return super().do_GET()
    return DesktopHandler


def request(path, command):
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(4)
        client.connect(str(path / 'control.sock'))
        client.sendall(command.encode('ascii'))
        return client.recv(512).decode('utf8')


def serve(path):
    import server as backend
    flags = os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW
    fd = os.open(path / 'owner.lock', flags, 0o600)
    with os.fdopen(fd, 'w') as lock:
        if os.fstat(lock.fileno()).st_nlink != 1:
            raise RuntimeError('Unsafe desktop lock.')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        browser_command('about:blank')  # Fail before starting a backend.
        tickets = Tickets()
        httpd = backend.LocalHTTPServer(('127.0.0.1', 0), desktop_handler(backend, tickets))
        thread = threading.Thread(target=httpd.serve_forever, kwargs={'poll_interval': .1}, daemon=True)
        control = socket.socket(socket.AF_UNIX)
        endpoint = path / 'control.sock'
        stop = threading.Event()
        children = []
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: stop.set())
        try:
            endpoint.unlink(missing_ok=True)
            control.bind(str(endpoint))
            control.listen(8)
            control.settimeout(.25)
            thread.start()
            # Probe static content only; never trigger telemetry/runtime adapters.
            probe = http.client.HTTPConnection('127.0.0.1', httpd.server_address[1], timeout=3)
            try:
                probe.request('GET', '/style.css')
                response = probe.getresponse()
                if response.status != 200:
                    raise RuntimeError('Backend readiness check failed.')
                response.read()
            finally:
                probe.close()
            last_open = float('-inf')
            while not stop.is_set():
                children[:] = [p for p in children if p.poll() is None]
                try:
                    client, _ = control.accept()
                except socket.timeout:
                    continue
                with client:
                    client.settimeout(4)
                    try:
                        command = client.recv(16).decode('ascii')
                        if command == 'STOP':
                            with backend.LOCK:
                                busy = backend.STATE['busy']
                            if busy:
                                result = 'An operation is active; wait before stopping the desktop backend.'
                            else:
                                stop.set()
                                result = 'OK'
                        elif command == 'OPEN':
                            result = 'OK'
                            if time.monotonic() - last_open > 2:
                                url = f'http://127.0.0.1:{httpd.server_address[1]}/?launch={tickets.issue()}'
                                proc = subprocess.Popen(browser_command(url), stdin=subprocess.DEVNULL,
                                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                children.append(proc)
                                try:
                                    code = proc.wait(timeout=.8)
                                    if code:
                                        result = 'Browser startup failed. Check browser permissions or try ASUS_AI_BROWSER=firefox.'
                                        if last_open == float('-inf'):
                                            stop.set()
                                except subprocess.TimeoutExpired:
                                    pass
                                if result == 'OK':
                                    last_open = time.monotonic()
                        elif command == 'PING':
                            result = 'OK' if thread.is_alive() else 'Backend stopped.'
                        else:
                            result = 'Unsupported desktop command.'
                        client.sendall(result.encode('utf8'))
                    except (OSError, ValueError):
                        if last_open == float('-inf'):
                            stop.set()
                        try:
                            client.sendall(b'Desktop browser launch failed. Check browser availability.')
                        except OSError:
                            pass
        finally:
            control.close()
            endpoint.unlink(missing_ok=True)
            if thread.is_alive():
                httpd.shutdown()
                thread.join(timeout=3)
            httpd.server_close()
            # Browser processes may belong to an existing user browser session.
            # Never terminate them. Backend lifetime intentionally survives window close.


def launch(path, command='OPEN'):
    try:
        return request(path, command)
    except (OSError, TimeoutError):
        if command == 'STOP':
            return 'OK'
    child = subprocess.Popen([sys.executable, str(BASE / 'desktop_launcher.py'), '--serve'],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        try:
            return request(path, command)
        except (OSError, TimeoutError):
            if child.poll() not in (None, 0):
                raise RuntimeError('Backend startup failed. Check local socket permissions and Python installation.')
            time.sleep(.1)
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=3)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
    raise RuntimeError('Desktop startup timed out after 15 seconds.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--stop', action='store_true', help='Stop the launcher-owned backend')
    args = parser.parse_args()
    os.umask(0o077)
    try:
        path = private_directory()
        if args.serve:
            serve(path)
        else:
            browser_command('about:blank') if not args.stop else None
            result = launch(path, 'STOP' if args.stop else 'OPEN')
            if result != 'OK':
                raise RuntimeError(result)
        return 0
    except (OSError, RuntimeError) as exc:
        message = str(exc) if isinstance(exc, RuntimeError) else 'Desktop startup failed: filesystem or local socket access unavailable.'
        print(message, file=sys.stderr)
        if not args.serve and shutil.which('zenity'):
            subprocess.run(['zenity', '--error', '--title=ASUS AI Control Center', '--text=' + message], check=False)
        return 1


if __name__ == '__main__':
    sys.exit(main())
