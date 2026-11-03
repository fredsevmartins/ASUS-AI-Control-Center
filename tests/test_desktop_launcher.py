"""Socket-free launcher contracts; no real browser, runtime or NAS access."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import desktop_launcher as app

spec = importlib.util.spec_from_file_location('desktop_install', Path(__file__).resolve().parents[1] / 'desktop/install_desktop.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class DesktopTests(unittest.TestCase):
    def test_chromium_app_size_no_session_token(self):
        with patch.object(app.shutil, 'which', side_effect=lambda n: '/snap/bin/chromium' if n == 'chromium' else None):
            with patch.dict(app.os.environ, {'ASUS_AI_BROWSER': 'auto'}):
                command = app.browser_command('http://127.0.0.1:1234/?launch=synthetic')
        self.assertIn('--window-size=1440,960', command)
        self.assertTrue(command[1].startswith('--app='))
        self.assertNotIn('token=', ' '.join(command))
        self.assertNotIn('--kiosk', command)

    def test_firefox_fallback(self):
        with patch.object(app.shutil, 'which', side_effect=lambda n: '/usr/bin/firefox' if n == 'firefox' else None):
            with patch.dict(app.os.environ, {'ASUS_AI_BROWSER': 'auto'}):
                command = app.browser_command('synthetic')
        self.assertIn('--new-window', command)
        self.assertFalse(any(arg.startswith('--app') for arg in command))

    def test_browser_unavailable(self):
        with patch.object(app.shutil, 'which', return_value=None):
            self.assertRaises(RuntimeError, app.browser_command, 'synthetic')

    def test_first_launch(self):
        with patch.object(app, 'request', side_effect=[OSError(), 'OK']), patch.object(app.subprocess, 'Popen') as spawn:
            self.assertEqual(app.launch(Path('/synthetic path')), 'OK')
        self.assertEqual(spawn.call_count, 1)
        self.assertTrue(spawn.call_args.kwargs['start_new_session'])

    def test_repeat_existing_backend_and_reopen_after_window_close(self):
        with patch.object(app, 'request', return_value='OK'), patch.object(app.subprocess, 'Popen') as spawn:
            for _ in range(3):
                self.assertEqual(app.launch(Path('/synthetic path')), 'OK')
        spawn.assert_not_called()

    def test_startup_failure(self):
        child = Mock()
        child.poll.return_value = 1
        with patch.object(app, 'request', side_effect=OSError()), patch.object(app.subprocess, 'Popen', return_value=child):
            self.assertRaisesRegex(RuntimeError, 'startup failed', app.launch, Path('/synthetic'))

    def test_timeout_cleans_owned_child(self):
        child = Mock()
        child.poll.return_value = None
        with patch.object(app, 'request', side_effect=OSError()), patch.object(app.subprocess, 'Popen', return_value=child), patch.object(app, 'TIMEOUT', 0):
            self.assertRaisesRegex(RuntimeError, 'timed out', app.launch, Path('/synthetic'))
        child.terminate.assert_called_once()
        child.wait.assert_called_once()

    def test_stop_and_restart(self):
        with patch.object(app, 'request', side_effect=['OK', OSError(), 'OK']) as request, patch.object(app.subprocess, 'Popen') as spawn:
            self.assertEqual(app.launch(Path('/synthetic'), 'STOP'), 'OK')
            self.assertEqual(app.launch(Path('/synthetic')), 'OK')
        self.assertEqual(request.call_args_list[0].args[1], 'STOP')
        self.assertEqual(spawn.call_count, 1)

    def test_stop_absent_does_not_start(self):
        with patch.object(app, 'request', side_effect=OSError()), patch.object(app.subprocess, 'Popen') as spawn:
            self.assertEqual(app.launch(Path('/synthetic'), 'STOP'), 'OK')
        spawn.assert_not_called()

    def test_ticket_single_use_expiry(self):
        tickets = app.Tickets()
        ticket = tickets.issue()
        self.assertTrue(tickets.consume(ticket))
        self.assertFalse(tickets.consume(ticket))
        with patch.object(app.time, 'monotonic', return_value=0):
            expired = tickets.issue()
        self.assertFalse(tickets.consume(expired))

    def test_handoff_retains_host_auth_handler(self):
        class Base:
            def local_request(self): return self.allowed
            def respond(self, code, body): return code
            def do_GET(self): return self.path
        backend = Mock(Handler=Base, TOKEN='SYNTHETIC-NOT-LIVE')
        tickets = app.Tickets()
        handler = app.desktop_handler(backend, tickets)()
        ticket = tickets.issue()
        handler.path = '/?launch=' + ticket
        handler.allowed = False
        self.assertEqual(handler.do_GET(), 403)
        handler.allowed = True
        self.assertEqual(handler.do_GET(), '/?token=SYNTHETIC-NOT-LIVE')
        handler.path = '/?launch=' + ticket
        self.assertEqual(handler.do_GET(), 403)
        handler.path = '/api/status'
        self.assertEqual(handler.do_GET(), '/api/status')

    def test_private_state_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'asus-ai-control-center').symlink_to(root, target_is_directory=True)
            with patch.dict(app.os.environ, {'XDG_RUNTIME_DIR': temp}):
                self.assertRaises(RuntimeError, app.private_directory)

    def run_supervisor(self, commands, browser_exit=None):
        backend = Mock()
        backend.LOCK = __import__('threading').Lock()
        backend.STATE = {'busy': False}
        backend.Handler = type('Handler', (), {})
        httpd = backend.LocalHTTPServer.return_value
        httpd.server_address = ('127.0.0.1', 12345)
        control = Mock()
        clients = []
        for command in commands:
            client = Mock()
            client.__enter__ = Mock(return_value=client)
            client.__exit__ = Mock(return_value=False)
            client.recv.return_value = command.encode()
            clients.append(client)
        control.accept.side_effect = [(c, None) for c in clients]
        proc = Mock()
        proc.poll.return_value = browser_exit
        proc.wait.return_value = browser_exit or 0
        probe = Mock()
        probe.getresponse.return_value.status = 200
        with tempfile.TemporaryDirectory() as temp, patch.dict(app.sys.modules, {'server': backend}), patch.object(app.socket, 'socket', return_value=control), patch.object(app.threading, 'Thread'), patch.object(app.signal, 'signal'), patch.object(app.http.client, 'HTTPConnection', return_value=probe), patch.object(app, 'browser_command', return_value=['synthetic-browser']), patch.object(app.subprocess, 'Popen', return_value=proc) as spawn:
            app.serve(Path(temp))
        return backend, httpd, clients, spawn

    def test_supervisor_debounces_and_closes_cleanly(self):
        backend, httpd, clients, spawn = self.run_supervisor(['OPEN', 'OPEN', 'STOP'])
        self.assertEqual(spawn.call_count, 1)
        backend.LocalHTTPServer.assert_called_once()
        self.assertEqual(backend.LocalHTTPServer.call_args.args[0], ('127.0.0.1', 0))
        for client in clients:
            client.sendall.assert_called_with(b'OK')
        httpd.shutdown.assert_called_once()
        httpd.server_close.assert_called_once()

    def test_first_browser_failure_closes_backend(self):
        _, httpd, clients, _ = self.run_supervisor(['OPEN'], browser_exit=1)
        self.assertIn(b'Browser startup failed', clients[0].sendall.call_args.args[0])
        httpd.shutdown.assert_called_once()
        httpd.server_close.assert_called_once()

    def test_competing_supervisor_does_not_bind(self):
        backend = Mock()
        with tempfile.TemporaryDirectory() as temp, patch.dict(app.sys.modules, {'server': backend}), patch.object(app.fcntl, 'flock', side_effect=BlockingIOError):
            app.serve(Path(temp))
        backend.LocalHTTPServer.assert_not_called()

    def test_launcher_spaces_and_no_token(self):
        with patch.object(installer, 'BASE', Path('/tmp/checkout with spaces')):
            entry = installer.entry()
        self.assertIn('"/tmp/checkout with spaces/desktop_launcher.py"', entry)
        self.assertIn('Terminal=false', entry)
        self.assertIn(' --stop', entry)
        self.assertNotIn('token', entry)
        self.assertIn('%%', installer.exec_quote('/tmp/100%'))
