"""Runtime fixtures only. No inference, services, Docker changes or live sockets."""
from contextlib import nullcontext
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import core
import intelligence as intel
import server
import test_stability as stability

G = intel.GIB


def row(key='target', loaded=False, weight=4*G):
    return {'key': key, 'name': key, 'runtime': 'Ollama', 'loaded': loaded,
            'state': 'loaded' if loaded else 'unloaded', 'uncertain': False,
            'metadata': {'weight_bytes': intel.field(weight, 'fixture'),
                         'loaded_bytes': intel.field(8*G if loaded else None, 'fixture')}}


class IntelligenceTests(unittest.TestCase):
    def setUp(self):
        intel.CACHE.clear()
        core.HEALTH_SUCCESS.clear()

    def test_metadata_provenance_and_active_vs_maximum_context(self):
        metadata = intel.ollama_metadata({'name': 'model', 'size': 10, 'details': {'family': 'qwen', 'quantization_level': 'Q4'}},
            {'size': 20, 'context_length': 4096}, {'model_info': {'general.architecture': 'qwen', 'qwen.context_length': 131072}})
        self.assertEqual(metadata['configured_context']['value'], 4096)
        self.assertEqual(metadata['context_window']['value'], 131072)
        self.assertEqual(metadata['quantization']['source'], 'Ollama /api/tags')
        self.assertEqual(metadata['storage']['confidence'], 'Unavailable')
        self.assertEqual(metadata['loaded_bytes']['value'], 20)

    def test_missing_and_malformed_metadata(self):
        for payload in ({}, {'details': []}, {'model_info': []}):
            m = intel.ollama_metadata({'name': 'x'}, show=payload)
            self.assertIsNone(m['parameters']['value'])
        for payload in ([], {}, {'models': [{}]}, {'models': 'bad'}):
            with self.assertRaises(ValueError):
                intel.model_list(payload)
        for invalid in (None, True, float('nan'), -1, '100', 10**400):
            self.assertIsNone(intel.number(invalid))
        self.assertEqual(intel.field({'malformed': 'metadata'})['confidence'], 'Unavailable')
        self.assertEqual(intel.field([{}])['confidence'], 'Unavailable')

    def test_discovery_keeps_installed_models_when_ps_unavailable(self):
        with patch.object(core, 'sglang_observation', return_value=dict(row('sglang'), runtime='SGLang')), \
             patch.object(core, 'api', side_effect=[{'models': [{'name': 'installed'}]}, TimeoutError('timeout')]):
            rows, errors = core.discover_models()
        self.assertTrue(rows[-1]['uncertain'])
        self.assertEqual(rows[-1]['state'], 'unknown')
        self.assertIn('timeout', errors[0])

    def test_runtime_unavailable_and_orphan_resident(self):
        with patch.object(core, 'sglang_observation', return_value=row('sglang')), patch.object(core, 'api', side_effect=OSError('offline')):
            rows, errors = core.discover_models()
            self.assertEqual(len(rows), 1)
            self.assertTrue(errors)
        with patch.object(core, 'sglang_observation', return_value=row('sglang')), \
             patch.object(core, 'api', side_effect=[{'models': []}, {'models': [{'name': 'orphan'}]}]):
            rows, _ = core.discover_models()
            self.assertTrue(rows[-1]['loaded'])

    def test_show_discovery_is_cached_and_never_generates(self):
        model = row()
        with patch.object(core, 'api', return_value={'details': {'parameter_size': '8B'}}) as api:
            first = core.model_details(model)
            core.model_details(model)
            api.assert_called_once_with('/api/show', {'model': 'target'}, timeout=2)
            self.assertEqual(first['metadata']['parameters']['value'], '8B')
        intel.CACHE.clear()
        with patch.object(core, 'api', side_effect=TimeoutError('timeout')) as api:
            self.assertIn('timeout', core.model_details(model)['metadata_error'])
            core.model_details(model)
            self.assertEqual(api.call_count, 1)

    def test_sglang_identity_readiness_and_timeout(self):
        cfg = {'model-path': 'Org/Qwen-27B-NVFP4', 'port': '30000'}
        def observe(side_effect, process=True):
            processes = {'running': process, 'service_status': 'active' if process else 'inactive',
                         'container_status': 'running' if process else 'stopped'}
            with patch.object(core, 'sglang_process_observation', return_value=processes), \
                 patch.object(core, 'sglang_auth_headers', return_value={}), \
                 patch.object(core, 'qwen_configuration', return_value=(cfg, 'http://127.0.0.1:30000')), \
                 patch.object(core, 'runtime_http', side_effect=side_effect) as api:
                result = core.sglang_observation()
                self.assertFalse(any('/health' in str(c) or '/generate' in str(c) for c in api.call_args_list))
                return result
        result = observe([{'model_path': cfg['model-path'], 'architectures': ['Qwen']}, True])
        self.assertEqual(result['state'], 'ready')
        self.assertEqual(result['metadata']['parameters']['confidence'], 'Inferred from filename')
        self.assertEqual(result['metadata']['architecture']['confidence'], 'Verified from runtime')
        last = result['health']['last_success']
        result = observe([{'model_path': cfg['model-path']}, TimeoutError('health timeout')])
        self.assertEqual(result['health']['last_success'], last)
        self.assertNotEqual(result['state'], 'ready')
        result = observe([{'model_path': 'wrong'}])
        self.assertTrue(result['uncertain'])
        result = observe([{'model_path': cfg['model-path']}, HTTPError('url', 404, '', {}, None)])
        self.assertEqual(result['state'], 'loaded')
        self.assertIn('unsupported', result['health']['failure_reason'])
        self.assertTrue(observe([{'model_path': cfg['model-path']}, True], process=False)['uncertain'])

    def test_sglang_verification_requires_readiness(self):
        with patch.object(core, 'is_loaded', return_value=True), \
             patch.object(core, 'sglang_observation', return_value={'state': 'loaded', 'uncertain': False}), \
             patch.object(core.time, 'sleep'), patch.object(core.time, 'monotonic', side_effect=[0, 0, 2, 2]):
            self.assertFalse(core.verify({'runtime': 'SGLang'}, True, 1))

    def test_loopback_security_no_redirects(self):
        for url in ('http://192.168.1.2:11434', 'https://127.0.0.1:1', 'http://evil:1', 'http://127.0.0.1:1/path',
                    'http://user:secret@127.0.0.1:1', 'http://127.0.0.1:1?x=1'):
            with self.assertRaises(ValueError):
                intel.local_url(url)
        self.assertEqual(intel.local_url('http://localhost:11434'), 'http://127.0.0.1:11434')
        self.assertIsNone(core.NoRedirect().redirect_request(None, None, 302, '', {}, 'http://elsewhere'))

    def test_resource_preflight_and_unknowns(self):
        target, old = row(), row('old', True)
        plan = intel.preflight([target, old], 128*G, 20*G, [], 'switch', 'target', ['old'])
        self.assertFalse(plan['blocked'])
        self.assertGreater(plan['requirement']['bytes'], 4*G)
        self.assertEqual(plan['estimated_release_bytes'], 8*G)
        self.assertTrue(intel.preflight([target], 128*G, G, [], 'load', 'target', [])['blocked'])
        unknown = row(weight=None)
        plan = intel.preflight([unknown], 128*G, 100*G, [], 'load', 'target', [])
        self.assertIsNone(plan['requirement']['bytes'])
        self.assertTrue(any('unknown' in w for w in plan['warnings']))
        self.assertTrue(intel.preflight([target], None, None, [], 'load', 'target', [])['blocked'])
        self.assertTrue(intel.preflight([target], 128*G, 100*G, ['offline'], 'load', 'target', [])['blocked'])
        for stops in (['target'], ['missing']):
            with self.assertRaises(ValueError):
                intel.preflight([target], 128*G, 100*G, [], 'switch', 'target', stops)

    def test_kv_estimate_and_invalid_state(self):
        target = row()
        target['kv_geometry'] = {'layers': 32, 'kv_heads': 8, 'head_dim': 128}
        target['metadata']['configured_context'] = intel.field(131072, 'fixture')
        self.assertGreater(intel.runtime_requirement(target)['kv_bytes'], G)
        self.assertEqual(intel.model_state(target, {'busy': True, 'phase': 'load', 'model': 'target'}), 'starting')
        self.assertNotIn('starting', intel.TRANSITIONS['ready'])
        self.assertEqual(intel.model_state(row(loaded=True), {'busy': True, 'phase': 'unload', 'model': 'target'}), 'stopping')

    def test_nas_weights_do_not_prove_completeness(self):
        files = [{'path': 'llm/model/x.safetensors', 'format': 'SAFETENSORS', 'size': 10, 'kind': 'Weight file'}]
        self.assertFalse(intel.nas_classification(files)['runnable'])
        self.assertEqual(intel.nas_classification(files)['classification'], 'Requires additional configuration')
        files += [{'path': 'llm/model/config.json', 'size': 10, 'kind': 'Configuration', 'config': {'model_type': 'qwen'}},
                  {'path': 'llm/model/tokenizer.json', 'size': 10, 'kind': 'Tokenizer'}]
        self.assertEqual(intel.nas_classification(files)['classification'], 'Complete model (structure only)')
        files[0]['path'] = 'llm/model/model-00001-of-00002.safetensors'
        self.assertEqual(intel.nas_classification(files)['classification'], 'Requires additional configuration')
        files += [{'path': 'llm/model/model.safetensors.index.json', 'size': 10, 'kind': 'Weight index',
                   'config': {'weight_map': {'x': 'model-00001-of-00002.safetensors', 'y': 'missing.safetensors'}}}]
        self.assertEqual(intel.nas_classification(files)['classification'], 'Requires additional configuration')

    def test_nas_scan_bounded_and_symlinks_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'x.safetensors').write_bytes(b'x')
            (root/'link.safetensors').symlink_to(root/'x.safetensors')
            (root/'config.json').write_text('{bad json')
            with patch.object(core, 'NAS_MODELS', root), patch.object(Path, 'is_mount', return_value=True):
                files, _ = core._nas_scan()
                self.assertEqual(len(files), 2)
                self.assertTrue(any('metadata_error' in f for f in files))
                with patch.object(core, 'MAX_NAS_ENTRIES', 1):
                    files, status = core._nas_scan()
                    self.assertLessEqual(len(files), 1)
                    self.assertIn('partial', status)

    def test_process_lock_blocks_another_worker(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(core, 'STATE_DIR', Path(directory)):
            with core.lifecycle_lock():
                with self.assertRaisesRegex(RuntimeError, 'Another Control Center'):
                    with core.lifecycle_lock():
                        self.fail('Second worker acquired lock')
            with core.lifecycle_lock():
                pass

    def test_unload_uses_supported_api_without_cli(self):
        with patch.object(core, 'api') as api, patch.object(core, 'command') as command:
            core.execute(row(), False)
            api.assert_called_once_with('/api/generate', {'model': 'target', 'keep_alive': 0, 'stream': False}, timeout=90)
            command.assert_not_called()

    def test_embedding_preload_has_no_health_prompt(self):
        model = dict(row(), embedding=True)
        with patch.object(core, 'api') as api:
            core.execute(model, True)
            self.assertEqual(api.call_args.args[1]['input'], [])

    def test_independent_memory_failure(self):
        with patch.object(core, 'memory', side_effect=OSError('unavailable')), \
             patch.object(core, 'discover_models', return_value=([row()], [])), patch.object(core, 'gpu_info', return_value='unavailable'):
            result = core.snapshot(fresh=True)
            self.assertIsNone(result[1])
            self.assertTrue(result[0])
            self.assertIn('Memory unavailable', result[4][0])


    def test_fingerprint_ignores_unrelated_enrichment_but_tracks_residency(self):
        target, other = row(), row('other')
        before = intel.fingerprint([target, other], 'target')
        other['metadata']['architecture'] = intel.field('Qwen', 'Ollama /api/show')
        self.assertEqual(intel.fingerprint([target, other], 'target'), before)
        other['loaded'] = True
        self.assertNotEqual(intel.fingerprint([target, other], 'target'), before)

    def test_orphan_resident_size_is_not_weight_size(self):
        metadata = intel.ollama_metadata({'name': 'orphan', 'size': 10*G, '_resident_only': True}, {'size': 10*G})
        self.assertIsNone(metadata['weight_bytes']['value'])
        self.assertEqual(metadata['loaded_bytes']['value'], 10*G)
        self.assertEqual(metadata['name']['source'], 'Ollama /api/ps')

    def test_activity_tolerates_corrupt_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'events.jsonl'
            path.write_text('bad\n{}\n{"operation":"load"}\n[]\n')
            with patch.object(core, 'LOG_PATH', path):
                events = server.activity()
                self.assertEqual(len(events), 2)
                self.assertEqual(events[0]['operation'], 'load')



class PlanApiTests(unittest.TestCase):
    request = stability.ApiTests.request
    def setUp(self):
        server.STATE.update(busy=False)
        server.PLANS.clear()
        self.headers = {'X-Session-Token': server.TOKEN, 'Content-Type': 'application/json'}

    def post(self, path, data):
        return self.request('POST', path, json.dumps(data), self.headers.copy())

    def plan(self):
        payload = {'action': 'load', 'target': 'target', 'stops': []}
        with patch.object(server, 'prepare', return_value=({'blocked': False, **payload}, {})):
            status, plan = self.post('/api/preflight', payload)
        self.assertEqual(status, 200)
        return {**payload, 'plan_id': plan['id'], 'confirmed': True, 'acknowledge_risks': True}

    def test_confirmation_single_use_and_overlap(self):
        payload = self.plan()
        with patch.object(server.threading, 'Thread') as thread:
            self.assertEqual(self.post('/api/action', {**payload, 'confirmed': False})[0], 400)
            thread.assert_not_called()
            self.assertEqual(self.post('/api/action', payload)[0], 202)
            self.assertEqual(self.post('/api/action', payload)[0], 409)
            server.STATE['busy'] = False
            self.assertEqual(self.post('/api/action', payload)[0], 409)
            self.assertEqual(thread.call_count, 1)

    def test_expired_and_tampered_plan(self):
        payload = self.plan()
        server.PLANS[payload['plan_id']]['expires_at'] = 0
        self.assertEqual(self.post('/api/action', payload)[0], 409)
        payload = self.plan()
        self.assertEqual(self.post('/api/action', {**payload, 'target': 'other'})[0], 400)

    def test_stale_worker_never_executes(self):
        with patch.object(core, 'lifecycle_lock', return_value=nullcontext()), \
             patch.object(server, 'prepare', return_value=({'blocked': False, 'fingerprint': 'new'}, {})), \
             patch.object(core, 'execute') as execute, patch.object(core, 'log_event'):
            server.run_job('load', 'target', [], {'fingerprint': 'old', 'expires_at': server.time.time() + 120})
            execute.assert_not_called()
            self.assertEqual(server.STATE['phase'], 'failed')

    def test_memory_rechecked_before_loading(self):
        with patch.object(core, 'memory', return_value=(128*G, G)):
            with self.assertRaisesRegex(RuntimeError, 'memory changed'):
                server.check_load_memory(row())

    def test_complete_mocked_switch_and_refreshed_status(self):
        models = [row(), row('old', True), row('untouched', True)]
        models[0]['metadata']['weight_bytes']['value'] = 2*G
        def snapshot(*args, **kwargs):
            return models, 128*G, 100*G, '', [], None, None
        def execute(model, load):
            model['loaded'] = load
            model['state'] = 'loaded' if load else 'unloaded'
        operation = {'action': 'switch', 'target': 'target', 'stops': ['old']}
        with patch.object(core, 'snapshot', side_effect=snapshot), \
             patch.object(core, 'model_details', side_effect=lambda r: r), \
             patch.object(core, 'lifecycle_lock', return_value=nullcontext()), \
             patch.object(core, 'memory', return_value=(128*G, 100*G)), \
             patch.object(core, 'execute', side_effect=execute) as execute_mock, \
             patch.object(core, 'is_loaded', side_effect=lambda r: r['loaded']), \
             patch.object(core, 'verify', side_effect=lambda r, expected, timeout: r['loaded'] == expected), \
             patch.object(core, 'log_event'), patch.object(server, 'disk_info', return_value={}), \
             patch.object(server, 'cpu_usage', return_value=None):
            status, plan = self.post('/api/preflight', operation)
            self.assertEqual(status, 200)
            self.assertFalse(plan['blocked'])
            with patch.object(server.threading, 'Thread') as thread:
                thread.return_value.start.side_effect = lambda: server.run_job('switch', 'target', ['old'], plan)
                status, _ = self.post('/api/action', dict(operation, plan_id=plan['id'], confirmed=True, acknowledge_risks=True))
            self.assertEqual(status, 202)
            status, refreshed = self.request('GET', '/api/status', headers=self.headers)
            self.assertEqual(status, 200)
            self.assertFalse(refreshed['operation']['busy'])
            self.assertEqual(refreshed['operation']['phase'], 'complete')
            self.assertTrue(models[0]['loaded'])
            self.assertFalse(models[1]['loaded'])
            self.assertTrue(models[2]['loaded'])
            self.assertEqual([c.args[0]['key'] for c in execute_mock.call_args_list], ['old', 'target'])

    def test_details_endpoint_requires_auth_and_registration(self):
        self.assertEqual(self.request('GET', '/api/model?key=target')[0], 403)
        with patch.object(core, 'snapshot', return_value=([row()], 0, 0, '', [], None, None)), \
             patch.object(core, 'model_details', side_effect=lambda r: r), patch.object(server, 'activity', return_value=[]):
            self.assertEqual(self.request('GET', '/api/model?key=missing', headers=self.headers)[0], 404)
            status, detail = self.request('GET', '/api/model?key=target', headers=self.headers)
            self.assertEqual(status, 200)
            self.assertEqual(detail['recent_operations'], [])



class RecoveryTests(unittest.TestCase):
    def exercise(self, load_error=True, unload_error=False, partial=False, verify_results=None):
        old, target = row('old', True), row()
        loaded = {'old'}
        events = []
        def execute(model, load):
            if load:
                loaded.add(model['key'])
                if model is target and load_error:
                    if not partial:
                        loaded.remove('target')
                    raise RuntimeError('failed load')
            else:
                loaded.discard(model['key'])
                if unload_error:
                    raise RuntimeError('failed unload')
        def verify(model, expected, timeout):
            if verify_results is not None:
                return verify_results.pop(0)
            return (model['key'] in loaded) == expected
        with patch.object(core, 'execute', side_effect=execute) as operations, \
             patch.object(core, 'is_loaded', side_effect=lambda m: m['key'] in loaded), \
             patch.object(core, 'verify', side_effect=verify), patch.object(core, 'log_event'):
            ok, message = core.swap_with_rollback([old], target, lambda p, **k: events.append((p, k)))
        return ok, message, events, operations

    def test_success(self):
        ok, _, events, _ = self.exercise(load_error=False)
        self.assertTrue(ok)
        self.assertEqual([p for p, _ in events], ['unload', 'load', 'readiness'])

    def test_failed_load_verified_recovery(self):
        ok, message, events, _ = self.exercise()
        self.assertFalse(ok)
        self.assertIn('Previous selected state verified', message)
        self.assertTrue(events[-1][1]['recovery']['verified'])

    def test_failed_unload_restores_partially_stopped(self):
        ok, message, _, _ = self.exercise(unload_error=True)
        self.assertFalse(ok)
        self.assertIn('1 verified', message)

    def test_partial_target_never_unloaded_or_claimed_restored(self):
        ok, message, events, operations = self.exercise(partial=True)
        self.assertFalse(ok)
        self.assertIn('Recovery incomplete', message)
        self.assertEqual(operations.call_count, 2)
        self.assertFalse(events[-1][1]['recovery']['verified'])

    def test_failed_readiness_and_recovery_verification(self):
        ok, message, events, _ = self.exercise(verify_results=[True, True, False])
        self.assertFalse(ok)
        self.assertIn('final recovery verification failed', message)
        self.assertFalse(events[-1][1]['recovery']['verified'])

    def test_readiness_failure_retains_partial_target(self):
        ok, message, events, _ = self.exercise(load_error=False, verify_results=[True, False])
        self.assertFalse(ok)
        self.assertIn('readiness', message)
        self.assertFalse(events[-1][1]['recovery']['target_absent'])

    def test_failed_restoration_and_unavailable_state(self):
        old, target = row('old', True), row()
        def execute(model, load):
            if load:
                raise RuntimeError('restart failed')
        with patch.object(core, 'execute', side_effect=execute), \
             patch.object(core, 'is_loaded', side_effect=[True, False, False]), \
             patch.object(core, 'verify', return_value=True), patch.object(core, 'log_event'):
            ok, message = core.swap_with_rollback([old], target)
        self.assertFalse(ok)
        self.assertIn('Recovery incomplete', message)
        self.assertIn('restart failed', message)



if __name__ == '__main__':
    unittest.main()
