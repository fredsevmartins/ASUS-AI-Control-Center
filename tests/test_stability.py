import io
import json
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import core
import server


def result(code, stdout=''):
    return subprocess.CompletedProcess([], code, stdout, '')


class RuntimeStateTests(unittest.TestCase):
    def test_agreeing_observations(self):
        for results, expected in [([result(0, 'active'), result(0, 'true')], True),
                                  ([result(3, 'inactive'), result(0, 'false')], False)]:
            with self.subTest(expected=expected), patch.object(core, 'command', side_effect=results):
                self.assertIs(core.sglang_state(), expected)

    def test_missing_or_disagreeing_observations_are_unknown(self):
        cases = [[result(3, 'inactive'), result(1)],
                 [result(0, 'active'), result(0, 'false')],
                 [FileNotFoundError(), result(0, 'false')]]
        for results in cases:
            with self.subTest(results=results), patch.object(core, 'command', side_effect=results):
                self.assertIsNone(core.sglang_state())
        with patch.object(core, 'sglang_state', return_value=None):
            with self.assertRaises(RuntimeError):
                core.is_loaded({'runtime': 'SGLang'})

    def test_failed_switch_restores_and_verifies_stopped_model(self):
        old = {'name': 'old', 'key': 'old', 'runtime': 'Ollama'}
        target = {'name': 'new', 'key': 'new', 'runtime': 'Ollama'}
        def execute(row, load):
            if row is target:
                raise RuntimeError('load failed')
        with patch.object(core, 'execute', side_effect=execute) as operation, \
             patch.object(core, 'verify', return_value=True) as verify, \
             patch.object(core, 'is_loaded', side_effect=lambda r: r is old), \
             patch.object(core, 'log_event'):
            ok, message = core.swap_with_rollback([old], target)
        self.assertFalse(ok)
        self.assertIn('1 verified', message)
        self.assertIn('target may be partially loaded', message)
        self.assertEqual(operation.call_args_list[-1].args, (old, True))
        self.assertEqual(verify.call_args_list[-1].args, (old, True, 4))

    def test_cpu_excludes_guest_time(self):
        from io import StringIO
        server.CPU_SAMPLE = None
        with patch('builtins.open', side_effect=[StringIO('cpu 100 0 100 800 0 0 0 0 50 0\n'),
                                                  StringIO('cpu 150 0 100 850 0 0 0 0 100 0\n')]):
            self.assertIsNone(server.cpu_usage())
            self.assertEqual(server.cpu_usage(), 50.0)


class ApiTests(unittest.TestCase):
    def request(self, method, path, body=None, headers=None):
        handler = server.Handler.__new__(server.Handler)
        handler.path = path
        handler.server = SimpleNamespace(server_address=('127.0.0.1', 8765))
        handler.headers = {'Host': '127.0.0.1:8765', **(headers or {})}
        payload = (body or '').encode()
        if payload:
            handler.headers['Content-Length'] = str(len(payload))
        handler.rfile = io.BytesIO(payload)
        handler.wfile = io.BytesIO()
        response = {}
        handler.send_response = lambda status: response.update(status=status)
        handler.send_header = lambda *args: None
        handler.end_headers = lambda: None
        getattr(handler, 'do_' + method)()
        return response['status'], json.loads(handler.wfile.getvalue())

    def test_status_requires_token_and_returns_mocked_data(self):
        self.assertEqual(self.request('GET', '/api/status')[0], 403)
        with patch.object(server, 'telemetry', return_value={'history': []}):
            status, data = self.request('GET', '/api/status', headers={'X-Session-Token': server.TOKEN})
        self.assertEqual((status, data), (200, {'history': []}))

    def test_malformed_action_shapes_are_rejected(self):
        cases = ['[]', 'null', '{"action":"switch","target":"x","stops":[{}]}',
                 '{"action":"switch","target":"x","stops":["a","a"]}']
        with patch.object(server.threading, 'Thread') as thread:
            for body in cases:
                with self.subTest(body=body):
                    status, _ = self.request('POST', '/api/action', body,
                        {'X-Session-Token': server.TOKEN, 'Content-Type': 'application/json'})
                    self.assertEqual(status, 400)
            thread.assert_not_called()

    def test_worker_start_failure_releases_operation_lock(self):
        server.STATE.update(busy=False, job=None, message='Ready', error=None)
        try:
            server.PLANS['test-plan'] = {'action': 'load', 'target': 'x', 'stops': [], 'expires_at': server.time.time()+120, 'blocked': False}
            with patch.object(server.threading, 'Thread') as thread:
                thread.return_value.start.side_effect = RuntimeError('thread unavailable')
                status, _ = self.request('POST', '/api/action', '{"action":"load","target":"x","plan_id":"test-plan","confirmed":true,"acknowledge_risks":true}',
                    {'X-Session-Token': server.TOKEN, 'Content-Type': 'application/json'})
            self.assertEqual(status, 503)
            self.assertFalse(server.STATE['busy'])
            self.assertIsNone(server.STATE['job'])
        finally:
            server.STATE.update(busy=False, job=None, message='Ready', error=None)

    def test_invalid_operation_rejected_without_runtime_call(self):
        with patch.object(server, 'run_job') as job:
            status, _ = self.request('POST', '/api/action', '{"action":"delete","target":"x"}',
                                     {'X-Session-Token': server.TOKEN, 'Content-Type': 'application/json'})
        self.assertEqual(status, 400)
        job.assert_not_called()


if __name__ == '__main__':
    unittest.main()
