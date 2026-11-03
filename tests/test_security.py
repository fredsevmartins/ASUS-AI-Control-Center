"""Public-release security regressions; temporary files and mocked runtimes only."""
import io
import json
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

import core
import intelligence as intel
import server
from test_validation import request

TOKEN = 'security-fixture-only-never-a-live-token'


class FilesystemSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'
        self.state.mkdir(mode=0o700)
        self.log = self.state / 'operations.jsonl'
        self.patches = [patch.object(core, 'STATE_DIR', self.state), patch.object(core, 'LOG_PATH', self.log)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_log_symlink_cannot_append_or_chmod_target(self):
        victim = self.root / 'unrelated'
        victim.write_text('unchanged')
        victim.chmod(0o644)
        self.log.symlink_to(victim)
        core.log_event('load', 'fixture')
        self.assertEqual(victim.read_text(), 'unchanged')
        self.assertEqual(victim.stat().st_mode & 0o777, 0o644)
        self.assertEqual(server.activity(), [])

    def test_state_directory_symlink_is_rejected(self):
        self.state.rmdir()
        victim = self.root / 'other'
        victim.mkdir()
        self.state.symlink_to(victim, target_is_directory=True)
        core.log_event('load', 'fixture')
        self.assertFalse((victim / self.log.name).exists())
        with self.assertRaises(OSError):
            with core.lifecycle_lock():
                self.fail('Must not acquire redirected lock')

    def test_hardlink_and_fifo_state_files_are_rejected(self):
        victim = self.root / 'other'
        victim.write_text('unchanged')
        os.link(victim, self.log)
        core.log_event('load', 'fixture')
        self.assertEqual(victim.read_text(), 'unchanged')
        self.log.unlink()
        os.mkfifo(self.log)
        core.log_event('load', 'fixture')
        self.assertEqual(server.activity(), [])

    def test_permissive_state_directory_is_rejected(self):
        self.state.chmod(0o755)
        core.log_event('load', 'fixture')
        self.assertFalse(self.log.exists())
        with self.assertRaises(OSError):
            with core.lifecycle_lock():
                self.fail('Unsafe state directory')

    def test_new_log_is_private_and_all_fields_are_bounded(self):
        core.log_event('a'*1000, 'b'*1000, 'c'*1000, 'd'*1000)
        self.assertEqual(self.log.stat().st_mode & 0o777, 0o600)
        record = json.loads(self.log.read_text())
        for key in ('operation', 'stage', 'model', 'detail'):
            self.assertEqual(len(record[key]), 500)

    def scan(self):
        with patch.object(core, 'NAS_MODELS', self.root), patch.object(Path, 'is_mount', return_value=True):
            return core._nas_scan()

    def test_nas_directory_replacement_cannot_escape_root(self):
        folder = self.root / 'models'
        folder.mkdir()
        (folder / 'safe.gguf').write_bytes(b'fixture')
        # An unrelated temporary directory stands in for an off-share target.
        with tempfile.TemporaryDirectory() as outside:
            (Path(outside) / 'private.gguf').write_bytes(b'private fixture')
            real_scandir = os.scandir
            changed = False
            def racing_scandir(path):
                nonlocal changed
                if not changed:
                    changed = True
                    iterator = real_scandir(path)
                    entries = list(iterator)
                    iterator.close()
                    # Populate DirEntry type caches before replacing the path.
                    for entry in entries:
                        entry.is_dir(follow_symlinks=False)
                    folder.rename(self.root / 'moved')
                    folder.symlink_to(outside, target_is_directory=True)
                    class Entries:
                        def __enter__(self): return iter(entries)
                        def __exit__(self, *args): pass
                    return Entries()
                return real_scandir(path)
            with patch.object(core.os, 'scandir', side_effect=racing_scandir):
                files, status = self.scan()
            self.assertFalse(any('private' in f['path'] for f in files))

    def test_nas_metadata_replaced_with_fifo_is_nonblocking(self):
        config = self.root / 'config.json'
        config.write_text('{}')
        real_open = os.open
        def racing_open(path, flags, *args, **kwargs):
            if str(path) in ('config.json', str(config)):
                config.unlink()
                os.mkfifo(config)
                # Assert before opening: the old implementation would hang.
                self.assertTrue(flags & os.O_NONBLOCK)
            return real_open(path, flags, *args, **kwargs)
        with patch.object(core.os, 'open', side_effect=racing_open):
            files, _ = self.scan()
        self.assertEqual(files[0]['metadata_error'], 'Unreadable or malformed metadata')

    def test_nas_deep_json_is_rejected_and_scan_budget_holds(self):
        (self.root / 'config.json').write_text('['*1500 + '0' + ']'*1500)
        files, _ = self.scan()
        self.assertIn('metadata_error', files[0])
        for i in range(10):
            (self.root / f'{i}.gguf').write_bytes(b'fixture')
        with patch.object(core, 'MAX_NAS_ENTRIES', 3):
            files, status = self.scan()
        self.assertLessEqual(len(files), 3)
        self.assertIn('partial', status)


class HttpSecurityTests(unittest.TestCase):
    def setUp(self):
        p = patch.object(server, 'TOKEN', TOKEN)
        p.start()
        self.addCleanup(p.stop)
        self.headers = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}

    def test_unauthorized_lifecycle_never_reaches_adapters(self):
        with patch.object(server, 'prepare') as prepare, patch.object(server, 'run_job') as job:
            for path in ('/api/action', '/api/preflight'):
                for token in ('', 'invalid', '\u2713'):
                    result = request('POST', path, b'{}', {**self.headers, 'X-Session-Token': token})
                    self.assertEqual(result['status'], 403)
            prepare.assert_not_called()
            job.assert_not_called()

    def test_bad_lengths_deep_json_and_unknown_models(self):
        with patch.object(server, 'prepare') as prepare:
            for length, body in (('8193', b''), ('-1', b''), ('NaN', b''), ('10', b'{}'),
                                 ('3001', b'['*1500+b'0'+b']'*1500)):
                self.assertEqual(request('POST', '/api/preflight', body,
                    {**self.headers, 'Content-Length': length})['status'], 400)
            prepare.assert_not_called()
        with self.assertRaises(ValueError):
            intel.preflight([], 128*intel.GIB, 100*intel.GIB, [], 'load', '../../unregistered', [])

    def wire(self, raw):
        class Connection:
            def __init__(self): self.output = io.BytesIO(); self.timeout = None
            def settimeout(self, value): self.timeout = value
            def makefile(self, mode, *args): return io.BytesIO(raw)
            def sendall(self, data): self.output.write(data)
        connection = Connection()
        fake_server = SimpleNamespace(server_address=('127.0.0.1', 8765))
        with patch.object(server, 'telemetry', side_effect=AssertionError('No live telemetry')):
            server.Handler(connection, ('127.0.0.1', 1), fake_server)
        self.assertEqual(connection.timeout, 10)
        return connection.output.getvalue()

    def test_duplicate_security_headers_and_unsupported_methods(self):
        for header in ('Host', 'Origin', 'X-Session-Token', 'Content-Length', 'Sec-Fetch-Site'):
            raw = ('GET /api/status HTTP/1.1\r\nHost: 127.0.0.1:8765\r\n' +
                   f'{header}: invalid\r\n{header}: other\r\n\r\n').encode()
            self.assertIn(b' 403 ', self.wire(raw).split(b'\r\n')[0])
        for method in ('PUT', 'DELETE', 'PATCH', 'OPTIONS', 'TRACE', 'CONNECT', 'HEAD'):
            self.assertIn(b' 501 ', self.wire(f'{method} /api/action HTTP/1.1\r\nHost: 127.0.0.1:8765\r\n\r\n'.encode()).split(b'\r\n')[0])

    def test_path_traversal_and_security_headers(self):
        for path in ('/../core.py', '/%2e%2e/core.py', '/.git/config', '//etc/passwd', '/web/../../server.py'):
            response = request('GET', path, headers=self.headers)
            self.assertNotEqual(response['status'], 200)
        for path in ('/app.js', '/style.css', '/missing'):
            raw = self.wire(f'GET {path} HTTP/1.1\r\nHost: 127.0.0.1:8765\r\n\r\n'.encode())
            for header in (b'X-Content-Type-Options: nosniff', b'Referrer-Policy: no-referrer', b'Cache-Control: no-store'):
                self.assertIn(header, raw)

    def test_connection_limit_and_slot_release(self):
        httpd = server.LocalHTTPServer.__new__(server.LocalHTTPServer)
        httpd.slots = threading.BoundedSemaphore(1)
        httpd.shutdown_request = Mock()
        with patch.object(server.ThreadingHTTPServer, 'process_request') as dispatch:
            httpd.process_request('one', ('127.0.0.1', 1))
            httpd.process_request('two', ('127.0.0.1', 2))
            dispatch.assert_called_once()
            httpd.shutdown_request.assert_called_once_with('two')
        with patch.object(server.ThreadingHTTPServer, 'process_request_thread', side_effect=RuntimeError):
            with self.assertRaises(RuntimeError): httpd.process_request_thread('one', ('127.0.0.1', 1))
        self.assertTrue(httpd.slots.acquire(False))

    def test_thread_start_failure_releases_slot(self):
        httpd = server.LocalHTTPServer.__new__(server.LocalHTTPServer)
        httpd.slots = threading.BoundedSemaphore(1)
        with patch.object(server.ThreadingHTTPServer, 'process_request', side_effect=RuntimeError):
            with self.assertRaises(RuntimeError): httpd.process_request(None, None)
        self.assertTrue(httpd.slots.acquire(False))

    def test_startup_binds_only_loopback_and_keeps_token_out_of_stdout(self):
        fake = Mock(server_address=('127.0.0.1', 12345))
        fake.serve_forever.side_effect = KeyboardInterrupt
        with patch.object(server, 'LocalHTTPServer', return_value=fake) as factory, \
             patch.object(server.threading, 'Timer'), patch('sys.stdout', new_callable=io.StringIO) as output:
            server.main()
        self.assertEqual(factory.call_args.args[0][0], '127.0.0.1')
        self.assertNotIn(TOKEN, output.getvalue())

    def test_unsafe_runtime_destinations(self):
        for url in ('http://example.com:1234', 'http://127.0.0.1:1234@evil.example:80',
                    'http://127.0.0.1:1234/path', 'http://127.0.0.1:1234?secret=synthetic',
                    'file:///etc/passwd', 'http://[::ffff:192.0.2.1]:80'):
            with self.assertRaises(ValueError): intel.local_url(url)


if __name__ == '__main__':
    unittest.main()
