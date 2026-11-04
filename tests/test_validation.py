"""Integration audit regressions. All runtime traffic/lifecycle calls are mocked."""
import io
import json
from pathlib import Path
import stat
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import core
import intelligence as intel
import server

NativeThread = threading.Thread
G = intel.GIB


def model(name='fixture', loaded=False, weight=4 * G):
    return {'key': name, 'name': name, 'runtime': 'Ollama', 'loaded': loaded,
            'uncertain': False, 'state': 'loaded' if loaded else 'unloaded',
            'metadata': {'weight_bytes': intel.field(weight, 'fixture')}}


def request(method, path, body=b'', headers=None):
    handler = server.Handler.__new__(server.Handler)
    handler.path = path
    handler.server = SimpleNamespace(server_address=('127.0.0.1', 8765))
    handler.headers = {'Host': '127.0.0.1:8765', **(headers or {})}
    handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
    response = {'headers': {}}
    handler.send_response = lambda code: response.update(status=code)
    handler.send_header = lambda k, v: response['headers'].update({k: v})
    handler.end_headers = lambda: None
    getattr(handler, 'do_' + method)()
    response['body'] = handler.wfile.getvalue()
    return response


class OllamaAuditTests(unittest.TestCase):
    def setUp(self):
        intel.CACHE.clear()

    def discover(self, tags, processes, show=None):
        calls = []
        def api(path, *args, **kwargs):
            calls.append(path)
            self.assertIn(path, ('/api/tags', '/api/ps', '/api/show'))
            value = {'/api/tags': tags, '/api/ps': processes, '/api/show': show or {}}[path]
            if isinstance(value, Exception):
                raise value
            return value
        with patch.object(core, 'sglang_observation', return_value=dict(model('sglang'), runtime='SGLang')), \
             patch.object(core, 'api', side_effect=api):
            rows, errors = core.discover_models()
        return rows[1:], errors, calls

    def test_installed_index_failure_keeps_resident_models(self):
        rows, errors, calls = self.discover(OSError('offline'), {'models': [{'name': 'resident', 'digest': 'd', 'size': 9 * G}]})
        self.assertEqual(len(rows), 1)
        resident = rows[0]
        self.assertTrue(resident['loaded'])
        self.assertIsNone(resident['installed'])
        self.assertFalse(resident['registration_observed'])
        self.assertIsNone(resident['metadata']['weight_bytes']['value'])
        self.assertEqual(resident['metadata']['loaded_bytes']['value'], 9 * G)
        self.assertEqual(resident['health']['readiness'], 'Resident; inference not verified')
        self.assertIn('/api/ps', calls)
        self.assertTrue(errors)

    def test_resident_absent_from_tags_is_not_verified_installed(self):
        rows, _, _ = self.discover({'models': []}, {'models': [{'name': 'resident'}]})
        self.assertTrue(rows[0]['loaded'])
        self.assertIsNone(rows[0]['installed'])

    def test_process_failure_keeps_installed_rows_unknown(self):
        rows, errors, _ = self.discover({'models': [{'name': 'installed', 'size': 4 * G}]}, {'models': 'invalid'})
        self.assertTrue(rows[0]['installed'])
        self.assertTrue(rows[0]['uncertain'])
        self.assertEqual(rows[0]['state'], 'unknown')
        self.assertIsNone(rows[0]['health']['model_loaded'])
        self.assertTrue(errors)

    def test_both_observations_fail_without_invented_models(self):
        rows, errors, calls = self.discover(OSError('tags offline'), OSError('ps offline'))
        self.assertEqual(rows, [])
        self.assertEqual(len(errors), 2)
        self.assertEqual(calls, ['/api/tags', '/api/ps'])

    def test_digest_conflict_is_visible_and_blocks_operations(self):
        rows, _, _ = self.discover({'models': [{'name': 'model', 'digest': 'installed'}]},
                                   {'models': [{'name': 'model', 'digest': 'resident'}]})
        self.assertTrue(rows[0]['loaded'])
        self.assertTrue(rows[0]['uncertain'])
        self.assertEqual(rows[0]['resident_identity'], 'resident')
        with self.assertRaises(ValueError):
            intel.preflight(rows, 128 * G, 100 * G, [], 'unload', rows[0]['key'], [])

    def test_incomplete_metadata_preserves_provenance_and_memory(self):
        rows, _, _ = self.discover({'models': [{'name': 'model', 'digest': {'invalid': True}, 'size': 4 * G}]},
                                   {'models': [{'name': 'model', 'size': 7 * G, 'context_length': 4096}]},
                                   {'model_info': {'general.architecture': 42}, 'details': []})
        m = rows[0]['metadata']
        self.assertIsNone(rows[0]['identity'])
        self.assertIsNone(m['architecture']['value'])
        self.assertEqual(m['loaded_bytes']['value'], 7 * G)
        self.assertEqual(m['weight_bytes']['value'], 4 * G)
        self.assertEqual(m['configured_context']['value'], 4096)
        self.assertEqual(m['loaded_bytes']['source'], 'Ollama /api/ps size (runtime allocation, shared-memory attribution uncertain)')
        for value in m.values():
            self.assertEqual(set(value), {'value', 'source', 'confidence'})
            self.assertIn(value['confidence'], intel.CONFIDENCE)

    def test_mutation_state_check_revalidates_digest(self):
        for digest in ('changed', None):
            with patch.object(core, 'api', return_value={'models': [{'name': 'model', 'digest': digest}]}):
                with self.assertRaisesRegex(RuntimeError, 'identity changed'):
                    core.is_loaded({'runtime': 'Ollama', 'name': 'model', 'identity': 'reviewed'})


class SecurityAuditTests(unittest.TestCase):
    def setUp(self):
        self.headers = {'X-Session-Token': server.TOKEN, 'Content-Type': 'application/json'}

    def test_host_origin_and_fetch_site_rejected_before_preflight(self):
        invalid = [{'Host': 'attacker.example:8765'}, {'Host': '127.0.0.1:9999'},
                   {'Origin': 'http://attacker.example'}, {'Origin': 'null'},
                   {'Origin': 'http://127.0.0.1:9999'}, {'Sec-Fetch-Site': 'cross-site'},
                   {'Sec-Fetch-Site': 'same-site'}]
        with patch.object(server, 'prepare') as prepare, patch.object(core, 'execute') as execute:
            for extra in invalid:
                response = request('POST', '/api/preflight', headers={**self.headers, **extra})
                self.assertEqual(response['status'], 403)
            prepare.assert_not_called()
            execute.assert_not_called()

    def test_all_read_apis_require_session_even_with_valid_origin(self):
        with patch.object(core, 'snapshot') as snapshot, patch.object(core, '_nas_scan') as nas:
            for path in ('/api/status', '/api/model?key=x', '/api/library', '/api/activity'):
                for token in ('', 'wrong', '\u2713'):
                    response = request('GET', path, headers={'X-Session-Token': token, 'Origin': 'http://127.0.0.1:8765'})
                    self.assertEqual(response['status'], 403)
            snapshot.assert_not_called()
            nas.assert_not_called()

    def test_main_document_security_headers_and_static_allowlist(self):
        response = request('GET', '/?token=' + server.TOKEN)
        self.assertEqual(response['status'], 200)
        self.assertIn("frame-ancestors 'none'", response['headers']['Content-Security-Policy'])
        self.assertEqual(response['headers']['Referrer-Policy'], 'no-referrer')
        self.assertEqual(response['headers']['Cache-Control'], 'no-store')
        self.assertEqual(request('GET', '/')['status'], 403)
        for path in ('/../core.py', '/core.py', '/AGENTS.md', '/.git/config'):
            self.assertEqual(request('GET', path, headers=self.headers)['status'], 404)

    def test_transfer_encoding_and_invalid_payloads_cannot_create_workers(self):
        with patch.object(server.threading, 'Thread') as worker, patch.object(server, 'prepare') as prepare:
            for body in (b'[]', b'null', b'{', json.dumps({'action': 'load', 'target': 'x', 'stops': ['x' * 513]}).encode()):
                response = request('POST', '/api/action', body, {**self.headers, 'Content-Length': str(len(body))})
                self.assertEqual(response['status'], 400)
            response = request('POST', '/api/action', headers={**self.headers, 'Transfer-Encoding': 'chunked'})
            self.assertEqual(response['status'], 400)
            worker.assert_not_called()
            prepare.assert_not_called()


class LifecycleAndTelemetryAuditTests(unittest.TestCase):
    def setUp(self):
        self.previous = dict(server.STATE)
        self.plans = dict(server.PLANS)
        server.PLANS.clear()
        server.STATE.update(busy=False)
        self.addCleanup(self.restore)

    def restore(self):
        server.STATE.clear()
        server.STATE.update(self.previous)
        server.PLANS.clear()
        server.PLANS.update(self.plans)

    def test_unknown_requirement_still_enforces_reserve(self):
        target = model(weight=None)
        plan = intel.preflight([target], 128 * G, G, [], 'load', target['key'], [])
        self.assertTrue(plan['blocked'])
        with patch.object(core, 'memory', return_value=(128 * G, G)):
            with self.assertRaises(RuntimeError):
                server.check_load_memory(target)

    def test_unknown_selected_allocation_is_not_displayed_as_zero(self):
        target, old = model(), model('old', True)
        plan = intel.preflight([target, old], 128 * G, 100 * G, [], 'switch', target['key'], [old['key']])
        self.assertIsNone(plan['estimated_release_bytes'])
        self.assertEqual(plan['projected_available_bytes'], 100 * G)
        self.assertTrue(any('no unverified memory reclamation' in w for w in plan['warnings']))

    def test_worker_rechecks_plan_expiry_before_any_runtime_read_or_mutation(self):
        with patch.object(core, 'lifecycle_lock') as lock, patch.object(server, 'prepare') as prepare, \
             patch.object(core, 'execute') as execute, patch.object(core, 'log_event'):
            lock.return_value.__enter__.return_value = None
            server.run_job('load', 'fixture', [], {'expires_at': 0})
        prepare.assert_not_called()
        execute.assert_not_called()
        self.assertIn('expired before execution', server.STATE['error'])

    def test_invalid_memory_cannot_authorize_unknown_size_load(self):
        for memory in ((None, None), (128 * G, -1), (128 * G, 129 * G)):
            with patch.object(core, 'memory', return_value=memory):
                with self.assertRaises(RuntimeError):
                    server.check_load_memory(model(weight=None))

    def test_sglang_identity_revalidated_independently_of_readiness(self):
        target = {'runtime': 'SGLang', 'identity': 'registered'}
        with patch.object(core, 'sglang_state', return_value=True), \
             patch.object(core, 'sglang_observation', return_value={'loaded': True, 'uncertain': False, 'identity': 'different'}):
            with self.assertRaisesRegex(RuntimeError, 'identity changed'):
                core.is_loaded(target)
        with patch.object(core, 'sglang_state', return_value=True), \
             patch.object(core, 'sglang_observation', return_value={'loaded': True, 'uncertain': False, 'identity': 'registered', 'state': 'loaded'}):
            self.assertTrue(core.is_loaded(target))

    def test_unsupported_readiness_fails_fast_without_retries(self):
        for status in ('unsupported', 'authentication_required', 'access_denied'):
            with patch.object(core, 'is_loaded', return_value=True), \
                 patch.object(core, 'sglang_observation', return_value={'state': 'loaded', 'uncertain': False,
                    'health': {'probes': {'readiness': {'status': status}}}}) as observe, \
                 patch.object(core.time, 'sleep') as sleep:
                self.assertFalse(core.verify({'runtime': 'SGLang'}, True, 150))
                observe.assert_called_once()
                sleep.assert_not_called()

    def test_transient_readiness_retries_with_remaining_deadline(self):
        with patch.object(core, 'is_loaded', return_value=True), \
             patch.object(core, 'sglang_observation', side_effect=[{'state': 'loaded', 'uncertain': False},
                                                                 {'state': 'ready', 'uncertain': False}]) as observe, \
             patch.object(core.time, 'monotonic', side_effect=[0, 0, .1, .5]), \
             patch.object(core.time, 'sleep') as sleep:
            self.assertTrue(core.verify({'runtime': 'SGLang'}, True, 1))
            self.assertEqual(observe.call_count, 2)
            sleep.assert_called_once_with(.9)

    def test_concurrent_confirmations_start_only_one_worker(self):
        server.PLANS['fixture-plan'] = {'action': 'load', 'target': 'fixture', 'stops': [],
                                        'expires_at': time.time() + 120, 'blocked': False}
        body = json.dumps({'action': 'load', 'target': 'fixture', 'stops': [], 'plan_id': 'fixture-plan',
                           'confirmed': True, 'acknowledge_risks': True}).encode()
        barrier, results = threading.Barrier(3), []
        def confirm():
            barrier.wait(timeout=3)
            results.append(request('POST', '/api/action', body, {'X-Session-Token': server.TOKEN,
                           'Content-Type': 'application/json', 'Content-Length': str(len(body))})['status'])
        with patch.object(server.threading, 'Thread') as worker:
            threads = [NativeThread(target=confirm) for _ in range(2)]
            for t in threads:
                t.start()
            barrier.wait(timeout=3)
            for t in threads:
                t.join(timeout=3)
            self.assertEqual(sorted(results), [202, 409])
            worker.assert_called_once()

    def test_sampling_is_serialized(self):
        active, maximum = 0, 0
        guard = threading.Lock()
        def sample():
            nonlocal active, maximum
            with guard:
                active += 1
                maximum = max(maximum, active)
            time.sleep(.01)
            with guard:
                active -= 1
            return {}
        with patch.object(server, '_telemetry', side_effect=sample):
            threads = [NativeThread(target=server.telemetry) for _ in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=3)
        self.assertEqual(maximum, 1)

    def test_unmounted_external_storage_is_not_the_system_disk(self):
        with patch.object(Path, 'is_mount', return_value=False), patch.object(server.os, 'statvfs') as statvfs:
            self.assertFalse(server.disk_info('/mnt/ai-models', 'External NVMe')['online'])
            statvfs.assert_not_called()

    def test_operation_log_uses_private_temporary_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'state'
            path = root / 'operations.jsonl'
            with patch.object(core, 'STATE_DIR', root), patch.object(core, 'LOG_PATH', path):
                core.log_event('load', 'fixture', 'fixture', 'x' * 1000)
                self.assertEqual(len(server.activity()[0]['detail']), 500)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


if __name__ == '__main__':
    unittest.main()
