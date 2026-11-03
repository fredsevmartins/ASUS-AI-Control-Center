#!/usr/bin/env python3
"""ASUS AI Model Manager v4 — read-only discovery, opt-in runtime controls.

Python standard library only. Compatible with Ubuntu 24.04 ARM64.
Never reconfigures systemd, Docker, Ollama, or the NAS.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import shutil
import stat
import subprocess
import threading
import fcntl
from contextlib import contextmanager
import time
from urllib.request import Request
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.error import HTTPError, URLError
import intelligence as intel

OLLAMA = os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434').rstrip('/')
NAS_MODELS = Path('/mnt/nas/AI-Models')
QWEN_CONTROL = Path.home() / '.local/bin/qwen38-control'
QWEN_SERVICE = 'qwen38-sglang.service'
QWEN_NAME = 'Qwen 3.8-27B NVFP4'
MODEL_FILES = {'.gguf', '.safetensors', '.onnx', '.pt', '.pth', '.bin', '.ckpt'}
MAX_NAS_ENTRIES = 1800
STATE_DIR = Path.home() / '.local/state/asus-ai-model-manager'
LOG_PATH = STATE_DIR / 'operations.jsonl'
QWEN_UNIT = Path('/etc/systemd/system/qwen38-sglang.service')
QWEN_DROPINS = Path('/etc/systemd/system/qwen38-sglang.service.d')
QWEN_API_KEY = Path.home() / '.config/qwen38/api-key'
HEALTH_SUCCESS = {}
HEALTH_LOCK = threading.Lock()


@contextmanager
def state_file(name, flags, create=False):
    """Open private state through a pinned directory, never links or devices."""
    if create:
        STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory = os.open(STATE_DIR, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    fd = None
    try:
        info = os.fstat(directory)
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise OSError('Application state directory must be private and owned by the current user')
        fd = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=directory)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise OSError('Unsafe application state file')
        if create:
            os.fchmod(fd, 0o600)
        yield fd
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


@contextmanager
def lifecycle_lock():
    """Coordinate lifecycle workers across copies of this application (Linux)."""
    with state_file('lifecycle.lock', os.O_CREAT | os.O_RDWR, create=True) as fd:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another Control Center instance is running a lifecycle operation') from None
        yield


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def runtime_http(origin, path, payload=None, timeout=2, health=False, headers=None):
    origin = intel.local_url(origin)
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = Request(origin + path, data=data, headers={'Content-Type': 'application/json', **(headers or {})})
    # Local APIs must not go through environment proxies or redirect elsewhere.
    with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=timeout) as response:
        if health:
            if response.status != 200:
                raise ValueError('Unexpected readiness response')
            return True
        raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('Runtime metadata exceeds response limit')
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError('Malformed runtime response')
        return result


def log_event(operation, stage, model=None, detail=None):
    """Append bounded, non-sensitive operation metadata (never model prompts)."""
    try:
        record = {key: str(value)[:500] if value is not None else None for key, value in
                  (('operation', operation), ('stage', stage), ('model', model), ('detail', detail))}
        record['time'] = datetime.now(timezone.utc).isoformat()
        with state_file(LOG_PATH.name, os.O_CREAT | os.O_WRONLY | os.O_APPEND, create=True) as fd:
            os.write(fd, (json.dumps(record, ensure_ascii=False) + '\n').encode('utf8'))
    except OSError:
        pass


def classify_nas_file(relative):
    """Group weights into collections without claiming a runnable model."""
    parts = Path(relative).parts
    text = '/'.join(parts).lower()
    if text.startswith('video/'):
        category = 'Video generation'
    elif text.startswith('voice/'):
        category = 'Speech / audio'
    elif text.startswith('image/'):
        category = 'Image generation'
    elif 'embedding' in text:
        category = 'Embeddings'
    elif text.startswith(('llm/', 'huggingface/', 'ollama/')):
        category = 'Language / multimodal'
    else:
        category = 'Other model assets'
    if 'wan2.2' in text or 'wan_2' in text or 'wan2_2' in text:
        collection = 'Wan 2.2 (asset group)'
    elif 'qwen3-tts' in text:
        collection = 'Qwen3-TTS (asset group)'
    elif 'qwen_image' in text or 'qwen-image' in text or 'qwen_image' in text:
        collection = 'Qwen Image (asset group)'
    else:
        # Use the top-level subfolder; not automatically a complete model.
        collection = (parts[1] if len(parts) > 2 else parts[0]) if parts else 'Unclassified'
    return category, collection


def group_nas_files(files):
    """Aggregate by category and model collection, counting file sizes only."""
    groups = {}
    for f in files:
        category, name = classify_nas_file(f['path'])
        key = (category, name)
        group = groups.setdefault(key, {'category': category, 'name': name,
                                         'files': 0, 'bytes': 0, 'formats': set(), 'paths': [], 'evidence': []})
        group['files'] += 1
        group['bytes'] += f['size']
        group['formats'].add(f['format'])
        group['paths'].append(f['path'])
        group['evidence'].append(f)
    for group in groups.values():
        group.update(intel.nas_classification(group.pop('evidence')))
    return sorted(groups.values(), key=lambda g: (g['category'].casefold(), g['name'].casefold()))



def api(path, payload=None, timeout=8):
    return runtime_http(OLLAMA, path, payload, timeout)


def command(args, timeout=12):
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)


def sglang_process_observation():
    """Keep systemd and Docker evidence even when HTTP or the other check fails."""
    try:
        service = command(['systemctl', 'is-active', QWEN_SERVICE], timeout=2)
        value = service.stdout.strip()
        service_state = True if service.returncode == 0 and value == 'active' else (
            False if service.returncode == 3 and value in ('inactive', 'failed') else None)
    except (OSError, subprocess.TimeoutExpired):
        service_state = None
    try:
        container = command(['docker', 'inspect', '-f', '{{.State.Running}}', 'qwen38-sglang'], timeout=2)
        value = container.stdout.strip()
        container_state = (value == 'true') if container.returncode == 0 and value in ('true', 'false') else None
    except (OSError, subprocess.TimeoutExpired):
        container_state = None
    running = service_state if service_state is not None and service_state == container_state else None
    return {'running': running,
            'service_status': 'active' if service_state is True else 'inactive' if service_state is False else 'unknown',
            'container_status': 'running' if container_state is True else 'stopped' if container_state is False else 'unknown'}


def sglang_state():
    """Lifecycle consensus remains independent of HTTP authentication/readiness."""
    return sglang_process_observation()['running']


def human(value):
    return '—' if value is None else f'{value / 1024**3:.1f} GiB'


def memory():
    entries = {}
    with open('/proc/meminfo', encoding='ascii') as fp:
        for line in fp:
            key, value = line.split(':', 1)
            entries[key] = int(value.strip().split()[0]) * 1024
    return entries['MemTotal'], entries['MemAvailable']


def gpu_info():
    """Best-effort NVIDIA telemetry; '--query-gpu' isn't supported on all GB10 stacks."""
    if not shutil.which('nvidia-smi'):
        return 'GPU telemetry unavailable'
    try:
        out = command(['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], timeout=4)
        if out.returncode == 0 and out.stdout.strip():
            fields = [f.strip() for f in out.stdout.splitlines()[0].split(',')]
            return f'GPU: {fields[0]}% utilization · {fields[1]}°C' if len(fields) >= 2 else 'GPU telemetry unavailable'
    except (OSError, subprocess.TimeoutExpired):
        pass
    return 'GPU telemetry unavailable on this driver'


def _nas_scan():
    """Bounded read-only inventory, anchored to directory descriptors on Linux."""
    if not NAS_MODELS.is_mount():
        return [], 'NAS share is not mounted'
    found, examined, metadata_reads = [], 0, 0
    stack = [((), 0)]
    root = None
    try:
        root = os.open(NAS_MODELS, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        while stack and examined < MAX_NAS_ENTRIES:
            parts, depth = stack.pop()
            directory = os.dup(root)
            try:
                # Reopen each component relative to the pinned root. A renamed
                # ancestor cannot redirect traversal through a replacement link.
                for part in parts:
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                    os.close(directory)
                    directory = child
                with os.scandir(directory) as iterator:
                    import itertools
                    entries = list(itertools.islice(iterator, MAX_NAS_ENTRIES - examined))
                for item in entries:
                    examined += 1
                    if item.name.startswith(('.', '#')):
                        continue
                    relative = '/'.join((*parts, item.name))
                    if item.is_file(follow_symlinks=False):
                        suffix = Path(item.name).suffix.lower()
                        kind = ('Weight file' if suffix in MODEL_FILES else
                                'Weight index' if item.name.endswith(('.safetensors.index.json', '.bin.index.json')) else
                                'Configuration' if item.name in ('config.json', 'model_index.json', 'adapter_config.json') else
                                'Tokenizer' if item.name in ('tokenizer.json', 'tokenizer.model', 'tokenizer_config.json', 'vocab.json', 'merges.txt', 'special_tokens_map.json') else None)
                        if kind:
                            evidence = {'path': relative, 'format': suffix[1:].upper(),
                                        'size': item.stat(follow_symlinks=False).st_size, 'kind': kind}
                            if kind in ('Configuration', 'Weight index') and evidence['size'] <= 262144 and metadata_reads < 32:
                                try:
                                    metadata_reads += 1
                                    fd = os.open(item.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                                    with os.fdopen(fd, 'r', encoding='utf8') as fp:
                                        if not stat.S_ISREG(os.fstat(fp.fileno()).st_mode):
                                            raise ValueError('Not a regular metadata file')
                                        value = json.loads(fp.read(262145))
                                    if not isinstance(value, dict):
                                        raise ValueError('Metadata object required')
                                    evidence['config'] = {k: value[k] for k in ('model_type', 'architectures', 'max_position_embeddings', 'quantization_config', 'weight_map') if k in value}
                                except (OSError, ValueError, RecursionError):
                                    evidence['metadata_error'] = 'Unreadable or malformed metadata'
                            found.append(evidence)
                    elif item.is_dir(follow_symlinks=False) and depth < 3:
                        stack.append(((*parts, item.name), depth + 1))
            finally:
                os.close(directory)
        return sorted(found, key=lambda x: x['path'].casefold()), ('NAS scan limit reached; results are partial' if examined >= MAX_NAS_ENTRIES else 'NAS inventory (read-only)')
    except OSError:
        return found, 'NAS scan incomplete: directory unavailable or changed during scan'
    finally:
        if root is not None:
            os.close(root)


def health_record(key, available, loaded, ready, reason=None, service=None):
    now = datetime.now(timezone.utc).isoformat()
    with HEALTH_LOCK:
        if available and (ready is True or (key == 'ollama' and loaded is not None)):
            HEALTH_SUCCESS[key] = now
        last = HEALTH_SUCCESS.get(key)
    return {'runtime_available': available, 'service_status': service,
            'model_loaded': loaded, 'endpoint_health': ready,
            'checked_at': now, 'last_success': last, 'failure_reason': reason,
            'readiness': 'Ready to accept requests' if ready is True else
                         'Not ready' if ready is False else
                         'Resident; inference not verified' if loaded else 'Unverified'}


def qwen_configuration():
    config = {}
    try:
        with QWEN_UNIT.open(encoding='utf8') as unit:
            text = unit.read(65536)
        config = intel.sglang_config(text)
        # The base unit can be superseded by systemd drop-ins. Retain its
        # registered model metadata, but never treat its old port as effective.
        dropins = sorted(QWEN_DROPINS.glob('*.conf'))
        if len(dropins) > 16:
            return config, None
        sources = [text]
        for path in dropins:
            with path.open(encoding='utf8') as source:
                sources.append(source.read(65536))
        effective_start = None
        for source in sources:
            config.update(intel.sglang_config(source))
            for line in source.replace('\\\n', ' ').splitlines():
                if line.startswith('ExecStart='):
                    effective_start = line[len('ExecStart='):].strip()
        gateway = ('qwen38-private-network' in '\n'.join(sources[1:])
                   and 'qwen38-gateway' in '\n'.join(sources[1:])
                   and effective_start == '/usr/bin/docker start -a qwen38-sglang')
        if gateway:
            config['interface'] = 'private-gateway'
        endpoint = os.environ.get('SGLANG_URL')
        if not endpoint and gateway:
            # Inspect only published bindings; no full container environment or
            # command, and no access to the namespace-only SGLang backend.
            ports = command(['docker', 'inspect', '-f', '{{json .NetworkSettings.Ports}}',
                             'qwen38-private-network'], timeout=2)
            if ports.returncode == 0 and len(ports.stdout) <= 65536:
                bindings = json.loads(ports.stdout).get('30002/tcp') or []
                origins = sorted(intel.local_url('http://' + ('[' + b['HostIp'] + ']' if ':' in b['HostIp'] else b['HostIp'])
                                                + ':' + b['HostPort']) for b in bindings)
                endpoint = origins[0] if origins else None
        if not endpoint and not gateway and effective_start and ('--network host' in effective_start or '--network=host' in effective_start):
            port = config.get('port')
            if port and port.isdigit():
                endpoint = 'http://127.0.0.1:' + port
        return config, intel.local_url(endpoint) if endpoint else None
    except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.TimeoutExpired):
        return config, None


def sglang_auth_headers(config):
    """Read an existing bearer file in memory only; never scrape unit secrets."""
    explicit = os.environ.get('SGLANG_API_KEY_FILE')
    path = Path(explicit) if explicit else QWEN_API_KEY if config.get('interface') == 'private-gateway' else None
    if path is None:
        return {}
    try:
        # Nonblocking open plus fstat rejects FIFOs/devices, bounding secret reads.
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise ValueError()
            raw = source.read(4097)
        token = raw.decode('ascii').rstrip('\r\n')
        if len(raw) > 4096 or not token or any(ord(c) < 33 or ord(c) > 126 for c in token):
            raise ValueError()
        return {'Authorization': 'Bearer ' + token}
    except (OSError, ValueError):
        # Never interpolate paths, file contents, or raw exception messages.
        raise ValueError('SGLang authentication file unavailable or invalid; configure SGLANG_API_KEY_FILE') from None


def sglang_probe(endpoint, path, headers, health=False):
    """One allowlisted GET, no retries or generating fallback; safe diagnostics."""
    if path not in ('/get_model_info', '/ready'):
        raise ValueError('Unsupported monitoring endpoint')
    probe = {'path': path, 'status': 'ok', 'http_status': None}
    try:
        value = runtime_http(endpoint, path, timeout=2, health=health, headers=headers)
        probe['http_status'] = 200
        return value, probe, None
    except HTTPError as exc:
        probe['http_status'] = exc.code
        exc.close()  # Do not read or retain potentially sensitive error bodies.
        if exc.code in (401, 403):
            probe['status'] = 'authentication_required' if exc.code == 401 else 'access_denied'
            reason = ('Authentication required' if exc.code == 401 else 'Access denied') + f' at {path} (HTTP {exc.code}); inference readiness is unverified'
        elif exc.code in (404, 405, 501):
            probe['status'] = 'unsupported'
            reason = f'Non-generating {path} endpoint unsupported (HTTP {exc.code}); inference readiness is unverified'
        elif health and exc.code == 503:
            probe['status'] = 'not_ready'
            return False, probe, '/ready reports not ready (HTTP 503)'
        else:
            probe['status'] = 'http_error'
            reason = f'{path} HTTP {exc.code}; inference readiness is unverified'
    except (TimeoutError, URLError) as exc:
        timed_out = isinstance(exc, TimeoutError) or isinstance(getattr(exc, 'reason', None), TimeoutError)
        probe['status'] = 'timeout' if timed_out else 'unavailable'
        reason = f'{path} timed out; inference readiness is unverified' if timed_out else f'{path} unavailable; inference readiness is unverified'
    except OSError:
        probe['status'] = 'unavailable'
        reason = f'{path} unavailable; inference readiness is unverified'
    except Exception:
        probe['status'] = 'invalid_response'
        reason = f'{path} response could not be verified; inference readiness is unverified'
    return None, probe, reason


def sglang_observation():
    processes = sglang_process_observation()
    process = processes['running']
    config, endpoint = qwen_configuration()
    info, ready, reason, available = {}, None, None, None
    probes = {name: {'path': path, 'status': 'not_checked', 'http_status': None}
              for name, path in (('metadata', '/get_model_info'), ('readiness', '/ready'))}
    identity = config.get('model-path')
    if endpoint:
        try:
            headers = sglang_auth_headers(config)
        except ValueError:
            probes['metadata']['status'] = 'authentication_configuration_error'
            reason = 'SGLang authentication file unavailable or invalid; configure SGLANG_API_KEY_FILE'
        else:
            info, probes['metadata'], reason = sglang_probe(endpoint, '/get_model_info', headers)
            info = info if isinstance(info, dict) else {}
            if probes['metadata']['status'] == 'ok':
                available = True
                if not identity or info.get('model_path') != identity:
                    reason = 'SGLang endpoint model identity missing or differs from the registered configuration; inference readiness is unverified'
                    probes['metadata']['status'] = 'identity_unverified'
                else:
                    ready, probes['readiness'], reason = sglang_probe(endpoint, '/ready', headers, health=True)
            elif probes['metadata']['status'] == 'unavailable':
                available = False
    else:
        reason = 'Local SGLang endpoint could not be established from existing configuration; set SGLANG_URL to the existing published loopback origin'
    identity_ok = bool(identity and info.get('model_path') == identity)
    loaded = process is True and identity_ok
    uncertain = process is None or (process is False and available) or (process is True and not identity_ok)
    state = ('unknown' if uncertain else 'unloaded' if process is False else
             'ready' if ready is True else 'error' if ready is False else 'loaded')
    # Endpoint readiness cannot establish readiness of this registered service
    # while process/identity observations disagree or are missing.
    if uncertain:
        ready = None
        if reason is None:
            reason = 'SGLang process and endpoint observations do not agree; inference readiness is unverified'
    health = health_record('sglang', available, loaded if not uncertain else None, ready, reason,
                           processes['service_status'])
    health.update(container_status=processes['container_status'], process_running=process,
                  probes=probes, source='systemd and Docker process observations; loopback GET /get_model_info and /ready')
    metadata = intel.sglang_metadata(config, info if identity_ok else {})
    return {'name': QWEN_NAME, 'runtime': 'SGLang', 'key': 'sglang',
            'installed': True if loaded else None,
            'loaded': loaded, 'uncertain': uncertain, 'state': state, 'status': state.capitalize(),
            'memory': 'Unavailable', 'metadata': metadata, 'health': health,
            'identity': identity, 'runtime_config': {'endpoint': endpoint, **config}}


def discover_models():
    qwen = sglang_observation()
    rows, errors = [qwen], []
    if qwen['uncertain']:
        errors.append('SGLang state is uncertain; actions are blocked until observations agree.')
    try:
        installed = intel.model_list(api('/api/tags', timeout=2))
    except Exception as exc:
        # Installation and residency are independent observations. Never hide
        # running models merely because the installed-model index is unavailable.
        installed = []
        errors.append(f'Ollama unavailable: installed inventory: {exc}')
    try:
        processes = intel.model_list(api('/api/ps', timeout=2))
        loaded = {m.get('name') or m.get('model'): m for m in processes}
        ps_error = None
    except Exception as exc:
        loaded, ps_error = {}, f'Ollama loaded state unavailable: {exc}'
        errors.append(ps_error)
    # Include residents absent from tags: never silently omit a potential conflict.
    known = {m.get('name') or m.get('model') for m in installed}
    installed += [dict(m, _resident_only=True) for n, m in loaded.items() if n not in known]
    metadata_budget = 1
    for model in installed:
        name = model.get('name') or model.get('model')
        if not name:
            continue
        process = loaded.get(name)
        metadata = intel.ollama_metadata(model, process)
        identity = model.get('digest') if isinstance(model.get('digest'), str) else None
        resident_identity = process.get('digest') if process and isinstance(process.get('digest'), str) else None
        identity_error = ('Ollama registered and resident model identities disagree' if
                          identity and resident_identity and identity != resident_identity else None)
        observation_error = ps_error or identity_error
        state = 'unknown' if observation_error else 'loaded' if process else 'unloaded'
        row = {'name': name, 'runtime': 'Ollama', 'key': 'ollama:' + name, 'loaded': bool(process),
                     'installed': None if model.get('_resident_only') else True,
                     'registration_observed': not model.get('_resident_only', False),
                     'uncertain': bool(observation_error), 'state': state, 'status': state.capitalize(),
                     'memory': human(metadata['loaded_bytes']['value']), 'metadata': metadata,
                     'embedding': ('embed' in name.lower() or 'nomic' in name.lower()),
                     'identity': identity, 'resident_identity': resident_identity,
                     'health': health_record('ollama', not ps_error, None if observation_error else bool(process), None, observation_error),
                     'runtime_config': {'endpoint': OLLAMA}}
        cache_key = ('show', row['key'], row.get('identity'))
        if intel.CACHE.peek(cache_key, 300) is not None:
            row = model_details(row)
        elif metadata_budget:
            metadata_budget -= 1
            row = model_details(row)
        rows.append(row)
    return rows, errors


def model_details(row):
    if row['runtime'] != 'Ollama':
        return row
    result = dict(row)
    show = intel.CACHE.get(('show', row['key'], row.get('identity')), 300,
                           lambda: api('/api/show', {'model': row['name']}, timeout=2))
    if not isinstance(show, dict):
        show = {'_error': 'Malformed model information'}
    if show.get('_error'):
        result['metadata_error'] = show['_error']
    else:
        # Preserve installed and resident evidence without another polling pass.
        synthetic = {'name': row['name'], 'size': row['metadata']['weight_bytes']['value'],
                     'details': {}, '_resident_only': not row.get('registration_observed', True)}
        result['metadata'] = intel.ollama_metadata(synthetic, show=show)
        for k, v in row['metadata'].items():
            if result['metadata'][k]['value'] is None:
                result['metadata'][k] = v
        info = show.get('model_info', {})
        if isinstance(info, dict):
            arch = info.get('general.architecture')
            arch = arch if isinstance(arch, str) else ''
            heads = intel.positive(info.get(arch + '.attention.head_count'))
            embedding = intel.positive(info.get(arch + '.embedding_length'))
            result['kv_geometry'] = {'layers': info.get(arch + '.block_count'),
                                     'kv_heads': info.get(arch + '.attention.head_count_kv'),
                                     'head_dim': embedding / heads if embedding and heads else None}
        capabilities = show.get('capabilities')
        if isinstance(capabilities, list) and capabilities:
            result['embedding'] = 'embedding' in capabilities
            result['capabilities'] = intel.field(capabilities, 'Ollama /api/show')
    result['requirement'] = intel.runtime_requirement(result)
    return result


def snapshot(include_nas=False, fresh=False):
    errors = []
    try:
        total, available = memory()
    except (OSError, ValueError, KeyError) as exc:
        total, available = None, None
        errors.append(f'Memory unavailable: {exc}')
    if fresh:
        rows, runtime_errors = discover_models()
    else:
        result = intel.CACHE.get('inventory', 10, discover_models)
        if isinstance(result, dict) and '_error' in result:
            rows, runtime_errors = [], ['Runtime discovery unavailable: ' + result['_error']]
        else:
            rows, runtime_errors = result
    errors += runtime_errors
    nas, nas_status = _nas_scan() if include_nas else (None, None)
    return rows, total, available, gpu_info(), errors, nas, nas_status


def is_loaded(row):
    if row['runtime'] == 'SGLang':
        state = sglang_state()
        if state is None:
            raise RuntimeError('SGLang state is uncertain; service and container must both be observable and agree.')
        if state and row.get('identity'):
            observed = sglang_observation()
            if observed['uncertain'] or not observed['loaded'] or observed.get('identity') != row['identity']:
                raise RuntimeError('SGLang model identity changed or cannot be verified; refresh before operating.')
        return state
    models = intel.model_list(api('/api/ps', timeout=2))
    process = next((m for m in models if (m.get('name') or m.get('model')) == row['name']), None)
    if process and row.get('identity') and process.get('digest') != row['identity']:
        raise RuntimeError('Ollama model identity changed or cannot be verified; refresh before operating.')
    return process is not None


def execute(row, load):
    if row['runtime'] == 'SGLang':
        if not QWEN_CONTROL.is_file():
            raise RuntimeError(f'Missing existing controller: {QWEN_CONTROL}')
        out = command([str(QWEN_CONTROL), 'start' if load else 'stop'], timeout=240 if load else 90)
        if out.returncode:
            raise RuntimeError((out.stderr or out.stdout).strip() or f'Controller exited {out.returncode}')
    elif load:
        if row.get('embedding'):
            api('/api/embed', {'model': row['name'], 'input': [], 'keep_alive': -1}, timeout=600)
        else:
            api('/api/generate', {'model': row['name'], 'prompt': '', 'keep_alive': -1, 'stream': False}, timeout=600)
    else:
        api('/api/generate', {'model': row['name'], 'keep_alive': 0, 'stream': False}, timeout=90)


def verify(row, expected, timeout=150):
    """Poll actual runtime state; a successful command alone is not readiness."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if row['runtime'] == 'SGLang':
                observed = sglang_observation()
                if row.get('identity') and observed.get('identity') != row['identity']:
                    return False
                if observed['state'] == ('ready' if expected else 'unloaded') and not observed['uncertain']:
                    return True
                # Repeating permanent contract/authentication failures cannot
                # establish readiness. Transient observations alone retry.
                probes = observed.get('health', {}).get('probes', {})
                if expected and any(p.get('status') in ('unsupported', 'authentication_required', 'access_denied',
                                                        'authentication_configuration_error', 'identity_unverified')
                                    for p in probes.values()):
                    return False
            elif is_loaded(row) == expected:
                return True
        except Exception:
            pass
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(2, remaining))
    return False


def swap_with_rollback(stops, target, progress=None, before_load=None, before_restore=None):
    """Compensating recovery of authorized stops, with explicit state verification."""
    progress = progress or (lambda phase, **kw: None)
    stopped, attempted = [], None
    log_event('switch', 'started', target['name'], f'{len(stops)} stop(s) requested')
    try:
        for row in stops:
            if not is_loaded(row):
                raise RuntimeError(f'Model is no longer loaded: {row["name"]}')
            attempted = row
            progress('unload', model=row['key'])
            execute(row, False)
            if not verify(row, False, 45):
                raise RuntimeError(f'Unable to verify unload: {row["name"]}')
            stopped.append(row)
            attempted = None
            log_event('unload', 'verified', row['name'])
        if before_load:
            before_load()
        progress('load', model=target['key'])
        execute(target, True)
        progress('readiness', model=target['key'])
        if not verify(target, True, 120):
            raise RuntimeError(f'Unable to verify target residency/readiness: {target["name"]}')
        log_event('switch', 'completed', target['name'])
        return True, f'Loaded {target["name"]}. Runtime evidence verified; Ollama inference execution is not probed.'
    except Exception as exc:
        progress('failure', model=target['key'])
        log_event('switch', 'failed', target['name'], exc)
        progress('recovery', model=target['key'])
        problems, restore, restored = [], list(stopped), []
        if attempted is not None:
            try:
                if not is_loaded(attempted):
                    restore.append(attempted)
            except Exception as state_exc:
                problems.append(f'{attempted["name"]}: cannot establish state: {state_exc}')
        try:
            target_absent = not is_loaded(target)
        except Exception as state_exc:
            target_absent = False
            problems.append(f'Target state unavailable: {state_exc}')
        if not target_absent:
            problems.append('Target may be partially loaded; restoration skipped to avoid additional memory pressure. Target cleanup requires a new explicit operation.')
        else:
            for row in reversed(restore):
                try:
                    log_event('rollback', 'started', row['name'])
                    if before_restore:
                        before_restore(row)
                    execute(row, True)
                    if verify(row, True, 120):
                        restored.append(row)
                        log_event('rollback', 'verified', row['name'])
                    else:
                        problems.append(f'{row["name"]}: restart not confirmed')
                except Exception as error:
                    problems.append(f'{row["name"]}: {error}')
        progress('verification', model=target['key'])
        # Verify again after all restoration commands: residency may change during recovery.
        verified = []
        for row in stops:
            try:
                if verify(row, True, 4):
                    verified.append(row['name'])
                else:
                    problems.append(f'{row["name"]}: final recovery verification failed')
            except Exception as error:
                problems.append(f'{row["name"]}: {error}')
        try:
            target_absent = not is_loaded(target)
        except Exception:
            target_absent = False
        recovered = target_absent and len(verified) == len(stops) and not problems
        recovery = {'verified': recovered, 'restored': [r['name'] for r in restored if r['name'] in verified],
                    'verified_previous': verified, 'issues': problems, 'target_absent': target_absent}
        progress('verification', recovery=recovery)
        log_event('rollback', 'verified' if recovered else 'incomplete', target['name'], json.dumps(recovery))
        return False, (f'Switch failed: {exc}. The target may be partially loaded; it is never automatically removed. '
                       f'{len(verified)} verified previous model(s). '
                       + ('Previous selected state verified.' if recovered else 'Recovery incomplete: ' + '; '.join(problems))
                       + ' Check actual runtime state before relying on services.')
