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
import subprocess
import threading
import fcntl
from contextlib import contextmanager
import time
from urllib.request import Request
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.error import HTTPError
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
HEALTH_SUCCESS = {}
HEALTH_LOCK = threading.Lock()


@contextmanager
def lifecycle_lock():
    """Coordinate lifecycle workers across copies of this application (Linux)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(STATE_DIR / 'lifecycle.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another Control Center instance is running a lifecycle operation') from None
        yield
    finally:
        os.close(fd)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def runtime_http(origin, path, payload=None, timeout=2, health=False):
    origin = intel.local_url(origin)
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = Request(origin + path, data=data, headers={'Content-Type': 'application/json'})
    # Local APIs must not go through environment proxies or redirect elsewhere.
    with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=timeout) as response:
        if health:
            return response.status == 200
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
        STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        with LOG_PATH.open('a', encoding='utf-8') as f:
            f.write(json.dumps({'time': datetime.now(timezone.utc).isoformat(),
                                'operation': operation, 'stage': stage,
                                'model': model, 'detail': str(detail)[:500] if detail else None}, ensure_ascii=False) + '\n')
        LOG_PATH.chmod(0o600)
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


def sglang_state():
    """Return process state only when both independent observations agree."""
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
    if service_state is None or container_state is None or service_state != container_state:
        return None
    return service_state


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
    """Bounded metadata discovery; never follow links, read weights or recurse indefinitely.

    Scan 3 levels below share root. A directory with recognized weights is a
    model candidate; an index directory by itself is not a loadable model.
    """
    if not NAS_MODELS.is_mount():
        return [], 'NAS share is not mounted'
    found = []
    examined = 0
    metadata_reads = 0
    stack = [(NAS_MODELS, 0)]
    try:
        while stack and examined < MAX_NAS_ENTRIES:
            directory, depth = stack.pop()
            with os.scandir(directory) as iterator:
                # Consume only the remaining budget, including hidden entries.
                import itertools
                entries = list(itertools.islice(iterator, MAX_NAS_ENTRIES - examined))
            for item in entries:
                if examined >= MAX_NAS_ENTRIES:
                    break
                examined += 1
                if item.name.startswith(('.', '#')):
                    continue
                relative = str(Path(item.path).relative_to(NAS_MODELS))
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
                                # Reject file symlinks even if replaced after scandir.
                                fd = os.open(item.path, os.O_RDONLY | os.O_NOFOLLOW)
                                with os.fdopen(fd, 'r', encoding='utf8') as fp:
                                    value = json.loads(fp.read(262145))
                                if isinstance(value, dict):
                                    evidence['config'] = {k: value[k] for k in ('model_type', 'architectures', 'max_position_embeddings', 'quantization_config', 'weight_map') if k in value}
                            except (OSError, ValueError):
                                evidence['metadata_error'] = 'Unreadable or malformed metadata'
                        found.append(evidence)
                elif item.is_dir(follow_symlinks=False) and depth < 3:
                    stack.append((Path(item.path), depth + 1))
        return sorted(found, key=lambda x: x['path'].casefold()), ('NAS scan limit reached; results are partial' if examined >= MAX_NAS_ENTRIES else 'NAS inventory (read-only)')
    except (OSError, PermissionError) as exc:
        return found, f'NAS scan incomplete: {exc}'


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
                         ('Resident; inference not verified' if loaded else 'Not ready')}


def qwen_configuration():
    try:
        with QWEN_UNIT.open(encoding='utf8') as unit:
            text = unit.read(65536)
        config = intel.sglang_config(text)
        # Never guess a container port mapping. This adapter supports the existing
        # host-network unit, or an explicitly configured loopback origin.
        endpoint = os.environ.get('SGLANG_URL')
        if not endpoint and ('--network host' in text or '--network=host' in text):
            port = config.get('port')
            if port and port.isdigit():
                endpoint = 'http://127.0.0.1:' + port
        return config, intel.local_url(endpoint) if endpoint else None
    except (OSError, ValueError):
        return {}, None


def sglang_observation():
    process = sglang_state()
    config, endpoint = qwen_configuration()
    info, ready, reason, available = {}, None, None, False
    identity = config.get('model-path')
    if endpoint:
        try:
            info = runtime_http(endpoint, '/get_model_info', timeout=2)
            if not isinstance(info.get('model_path'), str):
                raise ValueError('SGLang metadata is missing model_path')
            available = True
            if not identity or info['model_path'] != identity:
                raise ValueError('SGLang endpoint model identity differs from the registered configuration')
            try:
                ready = runtime_http(endpoint, '/ready', timeout=2, health=True)
            except HTTPError as exc:
                if exc.code == 404:
                    reason = 'Non-generating /ready endpoint unsupported; inference readiness is unverified'
                else:
                    ready, reason = False, f'Readiness endpoint HTTP {exc.code}'
        except Exception as exc:
            reason = str(exc)[:300]
    else:
        reason = 'Local SGLang endpoint could not be established from existing configuration'
    identity_ok = bool(identity and info.get('model_path') == identity)
    loaded = process is True and identity_ok
    uncertain = process is None or (process is False and available) or (process is True and not identity_ok)
    state = ('unknown' if uncertain else 'unloaded' if process is False else
             'ready' if ready is True else 'error' if ready is False else 'loaded')
    health = health_record('sglang', available, loaded if not uncertain else None, ready, reason,
                           'active' if process is True else 'inactive' if process is False else 'unknown')
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
        return rows, errors + [f'Ollama unavailable: {exc}']
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
        state = 'unknown' if ps_error else 'loaded' if process else 'unloaded'
        row = {'name': name, 'runtime': 'Ollama', 'key': 'ollama:' + name, 'loaded': bool(process),
                     'installed': True if not model.get('_resident_only') or process else None,
                     'registration_observed': not model.get('_resident_only', False),
                     'uncertain': bool(ps_error), 'state': state, 'status': state.capitalize(),
                     'memory': human(metadata['loaded_bytes']['value']), 'metadata': metadata,
                     'embedding': ('embed' in name.lower() or 'nomic' in name.lower()),
                     'identity': model.get('digest'),
                     'health': health_record('ollama', not ps_error, None if ps_error else bool(process), None, ps_error),
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
            arch = info.get('general.architecture', '')
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
        return state
    models = intel.model_list(api('/api/ps', timeout=2))
    return any((m.get('name') or m.get('model')) == row['name'] for m in models)


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
            if is_loaded(row) == expected:
                if row['runtime'] == 'SGLang':
                    observed = sglang_observation()
                    if observed['state'] == ('ready' if expected else 'unloaded') and not observed['uncertain']:
                        return True
                else:
                    return True
        except Exception:
            pass
        time.sleep(2)
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
