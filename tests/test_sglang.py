"""Mocked read-only SGLang transport/configuration; never contact live runtimes."""
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import core
import intelligence as intel


class SGLangHealthTests(unittest.TestCase):
    def setUp(self):
        core.HEALTH_SUCCESS.clear()
        self.cfg = {'model-path': 'fixture/Qwen-27B-NVFP4', 'port': '30000'}
        self.processes = {'running': True, 'service_status': 'active', 'container_status': 'running'}
        self.info = {'model_path': self.cfg['model-path']}

    def observe(self, responses, processes=None):
        with patch.object(core, 'sglang_process_observation', return_value=processes or self.processes), \
             patch.object(core, 'qwen_configuration', return_value=(self.cfg, 'http://127.0.0.1:30000')), \
             patch.object(core, 'sglang_auth_headers', return_value={}), \
             patch.object(core, 'runtime_http', side_effect=responses) as http:
            result = core.sglang_observation()
        self.assertLessEqual(http.call_count, 2)
        for call in http.call_args_list:
            self.assertIn(call.args[1], ('/get_model_info', '/ready'))
            self.assertEqual(call.kwargs['timeout'], 2)
            self.assertNotIn('payload', call.kwargs)
        return result

    def test_401_and_403_on_each_endpoint_are_not_runtime_failure(self):
        for code, status in ((401, 'authentication_required'), (403, 'access_denied')):
            for endpoint in ('metadata', 'readiness'):
                with self.subTest(code=code, endpoint=endpoint):
                    error = HTTPError('url', code, 'sensitive upstream text', {}, io.BytesIO(b'private body'))
                    responses = [error] if endpoint == 'metadata' else [self.info, error]
                    result = self.observe(responses)
                    h = result['health']
                    self.assertEqual(result['state'], 'unknown' if endpoint == 'metadata' else 'loaded')
                    self.assertEqual(result['uncertain'], endpoint == 'metadata')
                    self.assertIsNone(h['endpoint_health'])
                    self.assertEqual(h['runtime_available'], None if endpoint == 'metadata' else True)
                    self.assertEqual(h['service_status'], 'active')
                    self.assertEqual(h['container_status'], 'running')
                    self.assertNotIn('Not ready', h['readiness'])
                    self.assertEqual(h['probes'][endpoint]['status'], status)
                    self.assertEqual(h['probes'][endpoint]['http_status'], code)
                    self.assertIn(h['probes'][endpoint]['path'], h['failure_reason'])
                    self.assertNotIn('sensitive', json.dumps(result))
                    self.assertNotIn('private body', json.dumps(result))
                    if endpoint == 'metadata':
                        self.assertEqual(h['probes']['readiness']['status'], 'not_checked')
                        with self.assertRaises(ValueError):
                            intel.preflight([result], 128 * intel.GIB, 100 * intel.GIB, [], 'unload', 'sglang', [])

    def test_runtime_unavailable_does_not_erase_active_process(self):
        for error in (URLError(ConnectionRefusedError()), ConnectionRefusedError()):
            result = self.observe([error])
            self.assertIs(result['health']['runtime_available'], False)
            self.assertIsNone(result['health']['endpoint_health'])
            self.assertEqual(result['health']['probes']['metadata']['status'], 'unavailable')
            self.assertEqual(result['health']['service_status'], 'active')
            self.assertEqual(result['state'], 'unknown')
            self.assertEqual(result['health']['readiness'], 'Unverified')

    def test_metadata_and_readiness_timeouts(self):
        for error in (TimeoutError('private details'), URLError(TimeoutError('private details'))):
            for name in ('metadata', 'readiness'):
                with self.subTest(name=name, error=type(error).__name__):
                    result = self.observe([error] if name == 'metadata' else [self.info, error])
                    self.assertEqual(result['health']['probes'][name]['status'], 'timeout')
                    self.assertIsNone(result['health']['endpoint_health'])
                    self.assertNotIn('Not ready', result['health']['readiness'])
                    self.assertNotIn('private details', json.dumps(result))

    def test_unsupported_readiness_endpoint(self):
        for code in (404, 405, 501):
            result = self.observe([self.info, HTTPError('url', code, '', {}, None)])
            self.assertEqual(result['state'], 'loaded')
            self.assertEqual(result['health']['probes']['readiness']['status'], 'unsupported')
            self.assertIsNone(result['health']['endpoint_health'])
            self.assertIn('not verified', result['health']['readiness'])

    def test_only_explicit_readiness_503_reports_not_ready(self):
        for name in ('metadata', 'readiness'):
            for code in (302, 500, 502, 503):
                with self.subTest(name=name, code=code):
                    error = HTTPError('url', code, '', {}, None)
                    result = self.observe([error] if name == 'metadata' else [self.info, error])
                    if name == 'readiness' and code == 503:
                        self.assertEqual(result['state'], 'error')
                        self.assertIs(result['health']['endpoint_health'], False)
                        self.assertEqual(result['health']['readiness'], 'Not ready')
                    else:
                        self.assertIsNone(result['health']['endpoint_health'])
                        self.assertNotIn('Not ready', result['health']['readiness'])

    def test_service_active_but_container_unknown_cannot_claim_ready(self):
        processes = dict(self.processes, running=None, container_status='unknown')
        result = self.observe([self.info, True], processes)
        self.assertEqual(result['state'], 'unknown')
        self.assertEqual(result['health']['service_status'], 'active')
        self.assertIsNone(result['health']['endpoint_health'])
        self.assertIsNone(result['health']['last_success'])
        self.assertEqual(result['health']['readiness'], 'Unverified')

    def test_success_timestamp_retained_but_not_readiness_after_auth_failure(self):
        success = self.observe([self.info, True])
        self.assertEqual(success['state'], 'ready')
        last = success['health']['last_success']
        self.assertIsNotNone(last)
        failure = self.observe([HTTPError('url', 401, '', {}, None)])
        self.assertEqual(failure['health']['last_success'], last)
        self.assertIsNone(failure['health']['endpoint_health'])

    def test_identity_mismatch_never_probes_ready(self):
        result = self.observe([{'model_path': 'another/model'}])
        self.assertTrue(result['uncertain'])
        self.assertEqual(result['health']['probes']['metadata']['status'], 'identity_unverified')
        self.assertEqual(result['health']['probes']['readiness']['status'], 'not_checked')
        self.assertIsNone(result['health']['endpoint_health'])

    def test_systemd_signal_survives_docker_failure(self):
        with patch.object(core, 'command', side_effect=[subprocess.CompletedProcess([], 0, 'active', ''), OSError()]):
            processes = core.sglang_process_observation()
        self.assertEqual(processes, {'running': None, 'service_status': 'active', 'container_status': 'unknown'})

    def test_healthy_authenticated_endpoint_uses_only_bounded_gets(self):
        class Response(io.BytesIO):
            status = 200
        with tempfile.TemporaryDirectory() as directory:
            key = Path(directory) / 'fixture-key'
            key.write_text('fixture-only-bearer\n')
            requests = []
            def open_request(req, timeout):
                requests.append(req)
                self.assertEqual(timeout, 2)
                self.assertEqual(req.get_method(), 'GET')
                self.assertIsNone(req.data)
                self.assertEqual(req.get_header('Authorization'), 'Bearer fixture-only-bearer')
                return Response(json.dumps(self.info).encode() if req.full_url.endswith('/get_model_info') else b'')
            with patch.dict(core.os.environ, {'SGLANG_API_KEY_FILE': str(key)}), \
                 patch.object(core, 'sglang_process_observation', return_value=self.processes), \
                 patch.object(core, 'qwen_configuration', return_value=(self.cfg, 'http://127.0.0.1:30000')), \
                 patch.object(core, 'build_opener') as opener:
                opener.return_value.open.side_effect = open_request
                result = core.sglang_observation()
            self.assertEqual([r.full_url for r in requests], ['http://127.0.0.1:30000/get_model_info', 'http://127.0.0.1:30000/ready'])
            self.assertEqual(result['state'], 'ready')
            self.assertNotIn('fixture-only-bearer', json.dumps(result))
            self.assertNotIn(str(key), json.dumps(result))
            handlers = opener.call_args.args
            self.assertEqual(handlers[0].proxies, {})
            self.assertIsInstance(handlers[1], core.NoRedirect)

    def test_auth_file_failure_is_closed_and_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            key = Path(directory) / 'fixture-key'
            for content in ('', 'fixture\nAuthorization: injected', 'x' * 4097):
                key.write_text(content)
                with patch.dict(core.os.environ, {'SGLANG_API_KEY_FILE': str(key)}), \
                     patch.object(core, 'sglang_process_observation', return_value=self.processes), \
                     patch.object(core, 'qwen_configuration', return_value=(self.cfg, 'http://127.0.0.1:30000')), \
                     patch.object(core, 'runtime_http') as http:
                    result = core.sglang_observation()
                http.assert_not_called()
                self.assertEqual(result['health']['probes']['metadata']['status'], 'authentication_configuration_error')
                self.assertIsNone(result['health']['endpoint_health'])
                self.assertNotIn(str(key), json.dumps(result))
            with patch.dict(core.os.environ, {}, clear=True), patch.object(core, 'QWEN_API_KEY', key):
                key.write_text('fixture-only-bearer')
                self.assertEqual(core.sglang_auth_headers({'interface': 'private-gateway'}),
                                 {'Authorization': 'Bearer fixture-only-bearer'})
                self.assertEqual(core.sglang_auth_headers({}), {})

    def test_non_generating_probe_allowlist_and_unexpected_success_status(self):
        with patch.object(core, 'runtime_http') as http:
            for path in ('/health', '/health_generate', '/generate', '/server_info'):
                with self.assertRaises(ValueError):
                    core.sglang_probe('http://127.0.0.1:30000', path, {})
            http.assert_not_called()
        class Response(io.BytesIO):
            status = 204
        with patch.object(core, 'build_opener') as opener:
            opener.return_value.open.return_value = Response()
            value, probe, _ = core.sglang_probe('http://127.0.0.1:30000', '/ready', {}, health=True)
        self.assertIsNone(value)
        self.assertEqual(probe['status'], 'invalid_response')


class SGLangConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        directory = Path(self.temp.name)
        self.unit = directory / 'qwen.service'
        self.dropins = directory / 'dropins'
        self.dropins.mkdir()
        self.unit.write_text("[Service]\nExecStart=/bin/bash -c 'docker run --network host --model-path fixture/Qwen --api-key fixture-private --port 30000'\n")
        for name, value in (('QWEN_UNIT', self.unit), ('QWEN_DROPINS', self.dropins)):
            p = patch.object(core, name, value)
            p.start()
            self.addCleanup(p.stop)
        p = patch.dict(core.os.environ, {}, clear=True)
        p.start()
        self.addCleanup(p.stop)

    def gateway(self):
        (self.dropins / 'security-gateway.conf').write_text('[Service]\nExecStartPre=\nExecStartPre=/usr/bin/docker start qwen38-private-network qwen38-gateway\nExecStart=\nExecStart=/usr/bin/docker start -a qwen38-sglang\n')

    def test_original_host_network_and_secret_allowlist(self):
        with patch.object(core, 'command') as command:
            cfg, endpoint = core.qwen_configuration()
        self.assertEqual(endpoint, 'http://127.0.0.1:30000')
        self.assertNotIn('fixture-private', json.dumps(cfg))
        command.assert_not_called()

    def test_dropin_gateway_uses_published_loopback_not_stale_base_port(self):
        self.gateway()
        ports = {'30002/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '31000'}]}
        with patch.object(core, 'command', return_value=subprocess.CompletedProcess([], 0, json.dumps(ports), '')) as command:
            cfg, endpoint = core.qwen_configuration()
        self.assertEqual(endpoint, 'http://127.0.0.1:31000')
        self.assertEqual(cfg['interface'], 'private-gateway')
        command.assert_called_once_with(['docker', 'inspect', '-f', '{{json .NetworkSettings.Ports}}', 'qwen38-private-network'], timeout=2)

    def test_gateway_unknown_mapping_never_guesses_or_contacts_private_backend(self):
        self.gateway()
        for response in (subprocess.CompletedProcess([], 1, '', ''),
                         subprocess.CompletedProcess([], 0, '{"30002/tcp":[{"HostIp":"0.0.0.0","HostPort":"30000"}]}', ''),
                         subprocess.CompletedProcess([], 0, 'null', ''),
                         subprocess.CompletedProcess([], 0, '{}', ''), OSError()):
            with patch.object(core, 'command', side_effect=[response]):
                cfg, endpoint = core.qwen_configuration()
            self.assertIsNone(endpoint)
            self.assertEqual(cfg['model-path'], 'fixture/Qwen')

    def test_explicit_loopback_gateway_override_and_remote_rejection(self):
        self.gateway()
        for url, expected in (('http://localhost:31000', 'http://127.0.0.1:31000'),
                              ('http://10.1.2.3:30000', None),
                              ('http://user:fixture@127.0.0.1:30000', None)):
            with patch.dict(core.os.environ, {'SGLANG_URL': url}), patch.object(core, 'command') as command:
                _, endpoint = core.qwen_configuration()
            self.assertEqual(endpoint, expected)
            command.assert_not_called()

    def test_arbitrary_execstart_override_disables_base_port_inference(self):
        (self.dropins / 'other.conf').write_text('[Service]\nExecStart=\nExecStart=/usr/bin/docker start -a another-container\n')
        with patch.object(core, 'command') as command:
            _, endpoint = core.qwen_configuration()
        self.assertIsNone(endpoint)
        command.assert_not_called()
