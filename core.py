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
import time
from urllib.request import Request, urlopen

OLLAMA = os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434').rstrip('/')
NAS_MODELS = Path('/mnt/nas/AI-Models')
QWEN_CONTROL = Path.home() / '.local/bin/qwen38-control'
QWEN_SERVICE = 'qwen38-sglang.service'
QWEN_NAME = 'Qwen 3.8-27B NVFP4'
MODEL_FILES = {'.gguf', '.safetensors', '.onnx', '.pt', '.pth', '.bin', '.ckpt'}
MAX_NAS_ENTRIES = 1800
STATE_DIR = Path.home() / '.local/state/asus-ai-model-manager'
LOG_PATH = STATE_DIR / 'operations.jsonl'


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
                                         'files': 0, 'bytes': 0, 'formats': set(), 'paths': []})
        group['files'] += 1
        group['bytes'] += f['size']
        group['formats'].add(f['format'])
        group['paths'].append(f['path'])
    return sorted(groups.values(), key=lambda g: (g['category'].casefold(), g['name'].casefold()))



def api(path, payload=None, timeout=8):
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = Request(OLLAMA + path, data=data, headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=timeout) as response:
        return json.load(response)


def command(args, timeout=12):
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)


def sglang_state():
    """Return process state only when both independent observations agree."""
    try:
        service = command(['systemctl', 'is-active', QWEN_SERVICE])
        value = service.stdout.strip()
        service_state = True if service.returncode == 0 and value == 'active' else (
            False if service.returncode == 3 and value in ('inactive', 'failed') else None)
    except (OSError, subprocess.TimeoutExpired):
        service_state = None
    try:
        container = command(['docker', 'inspect', '-f', '{{.State.Running}}', 'qwen38-sglang'])
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
    stack = [(NAS_MODELS, 0)]
    try:
        while stack and examined < MAX_NAS_ENTRIES:
            directory, depth = stack.pop()
            with os.scandir(directory) as iterator:
                entries = sorted(list(iterator), key=lambda e: e.name.casefold())
            for item in entries:
                if examined >= MAX_NAS_ENTRIES:
                    break
                examined += 1
                if item.name.startswith(('.', '#')):
                    continue
                relative = str(Path(item.path).relative_to(NAS_MODELS))
                if item.is_file(follow_symlinks=False) and Path(item.name).suffix.lower() in MODEL_FILES:
                    found.append({'path': relative, 'format': Path(item.name).suffix.lower()[1:].upper(), 'size': item.stat(follow_symlinks=False).st_size, 'kind': 'Weight file'})
                elif item.is_dir(follow_symlinks=False) and depth < 3:
                    stack.append((Path(item.path), depth + 1))
        return sorted(found, key=lambda x: x['path'].casefold()), ('NAS scan limit reached; results are partial' if examined >= MAX_NAS_ENTRIES else 'NAS inventory (read-only)')
    except (OSError, PermissionError) as exc:
        return found, f'NAS scan incomplete: {exc}'


def snapshot(include_nas=False):
    total, available = memory()
    errors = []
    running = sglang_state()
    qwen_status = 'Loaded / active' if running is True else ('Unloaded' if running is False else 'Check service')
    rows = [{'name': QWEN_NAME, 'runtime': 'SGLang', 'status': qwen_status, 'memory': 'Not available', 'key': 'sglang', 'loaded': running is True, 'uncertain': running is None}]
    if running is None:
        errors.append('SGLang process state could not be established; actions are blocked.')
    try:
        installed = api('/api/tags').get('models', [])
        ps = api('/api/ps').get('models', [])
        loaded = {m.get('name') or m.get('model'): m for m in ps}
        for m in installed:
            name = m.get('name') or m.get('model')
            if not name:
                continue
            process = loaded.get(name)
            rows.append({'name': name, 'runtime': 'Ollama', 'status': 'Loaded' if process else 'Unloaded',
                         'memory': human(process.get('size_vram') or process.get('size')) if process else '—',
                         'key': name, 'loaded': bool(process), 'embedding': ('embed' in name.lower() or 'nomic' in name.lower()), 'uncertain': False})
    except Exception as exc:
        errors.append(f'Ollama unavailable: {exc}')
    nas, nas_status = _nas_scan() if include_nas else (None, None)
    return rows, total, available, gpu_info(), errors, nas, nas_status


def is_loaded(row):
    if row['runtime'] == 'SGLang':
        state = sglang_state()
        if state is None:
            raise RuntimeError('SGLang state is uncertain; service and container must both be observable and agree.')
        return state
    models = api('/api/ps', timeout=15).get('models', [])
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
            api('/api/embed', {'model': row['name'], 'input': 'health check', 'keep_alive': -1}, timeout=600)
        else:
            api('/api/generate', {'model': row['name'], 'prompt': '', 'keep_alive': -1, 'stream': False}, timeout=600)
    else:
        out = command(['ollama', 'stop', row['name']], timeout=90)
        if out.returncode:
            raise RuntimeError((out.stderr or out.stdout).strip() or f'Ollama stop exited {out.returncode}')


def verify(row, expected, timeout=150):
    """Poll actual runtime state; a successful command alone is not readiness."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if is_loaded(row) == expected:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def swap_with_rollback(stops, target):
    """Best-effort compensating rollback; includes partially stopped model."""
    stopped = []
    attempted = None
    log_event('switch', 'started', target['name'], f'{len(stops)} stop(s) requested')
    try:
        for row in stops:
            attempted = row
            log_event('unload', 'started', row['name'])
            execute(row, False)
            if not verify(row, False, 45):
                raise RuntimeError(f'Unable to verify unload: {row["name"]}')
            stopped.append(row)
            attempted = None
            log_event('unload', 'verified', row['name'])
        log_event('load', 'started', target['name'])
        execute(target, True)
        if not verify(target, True, 120):
            raise RuntimeError(f'Unable to verify load: {target["name"]}')
        log_event('switch', 'completed', target['name'])
        return True, f'Loaded {target["name"]}. Unloaded: {", ".join(r["name"] for r in stopped)}.'
    except Exception as exc:
        log_event('switch', 'failed', target['name'], exc)
        problems = []
        restore = list(stopped)
        # A failed stop command can stop a model before returning an error.
        # Restore it only if it was active in the initial snapshot and is now down.
        if attempted is not None:
            try:
                if not is_loaded(attempted):
                    restore.append(attempted)
            except Exception as state_exc:
                problems.append(f'{attempted["name"]}: cannot establish state: {state_exc}')
        restored = 0
        for row in reversed(restore):
            try:
                log_event('rollback', 'started', row['name'])
                execute(row, True)
                if verify(row, True, 120):
                    restored += 1
                    log_event('rollback', 'verified', row['name'])
                else:
                    problems.append(f'{row["name"]}: restart not confirmed')
                    log_event('rollback', 'unverified', row['name'])
            except Exception as restoration_error:
                problems.append(f'{row["name"]}: {restoration_error}')
                log_event('rollback', 'failed', row['name'], restoration_error)
        return False, (f'Switch failed: {exc}\nThe target may be partially loaded; its state has not been cleaned up. '
                       f'Restoration attempted for {len(restore)} model(s); '
                       f'{restored} verified. '
                       + ('Restoration issues: ' + '; '.join(problems) if problems else 'No restoration errors detected.')
                       + '\nCheck the actual runtime state before relying on the services.')

