"""Read-only model evidence and conservative planning; no runtime mutation."""
import copy
import hashlib
import ipaddress
import json
import math
import re
import threading
import time
from urllib.parse import urlsplit

GIB = 1024 ** 3
CONFIDENCE = ('Verified from runtime', 'Verified from configuration', 'Inferred from filename', 'Estimated', 'Unavailable')
FIELDS = ('name', 'runtime', 'family', 'parameters', 'architecture', 'quantization',
          'format', 'weight_bytes', 'storage', 'context_window', 'configured_context',
          'loaded_bytes', 'compatibility')
# Observations may move directly between stable states (external clients also act).
STATES = ('installed', 'unloaded', 'starting', 'loaded', 'ready', 'busy', 'stopping', 'error', 'unknown')
# Lifecycle intents are distinct from externally observed stable states.
TRANSITIONS = {
    'installed': {'unloaded', 'starting', 'unknown'},
    'unloaded': {'starting', 'loaded', 'ready', 'unknown', 'error'},
    'starting': {'loaded', 'ready', 'error', 'unknown', 'stopping'},
    'loaded': {'ready', 'busy', 'stopping', 'unloaded', 'error', 'unknown'},
    'ready': {'busy', 'loaded', 'stopping', 'unloaded', 'error', 'unknown'},
    'busy': {'ready', 'loaded', 'stopping', 'error', 'unknown'},
    'stopping': {'unloaded', 'error', 'unknown', 'loaded', 'ready'},
    'error': {'unknown', 'unloaded', 'loaded', 'ready'},
    'unknown': set(STATES) - {'unknown'},
}


def model_state(row, operation=None):
    """Project a known lifecycle intent over read-only observations."""
    state = row.get('state', 'unknown')
    if operation and operation.get('busy'):
        if row['key'] == operation.get('model'):
            intent = {'load': 'starting', 'unload': 'stopping'}.get(operation.get('phase'))
            if intent and (intent in TRANSITIONS[state] or state == intent):
                return intent
    return state
PHASES = ('precheck', 'confirmation', 'unload', 'load', 'readiness', 'complete',
          'failure', 'recovery', 'verification', 'failed')


def field(value=None, source=None, confidence='Verified from runtime'):
    if (isinstance(value, dict) or isinstance(value, bool)
            or (isinstance(value, list) and any(not isinstance(v, str) for v in value))
            or (isinstance(value, (int, float)) and number(value) is None)):
        value = None
    if value is None or value == '' or value == []:
        return {'value': None, 'source': source, 'confidence': 'Unavailable'}
    return {'value': value, 'source': source, 'confidence': confidence}


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 2**63 - 1 and math.isfinite(value) else None


def positive(value):
    n = number(value)
    return n if n is not None and n > 0 else None


def local_url(url):
    """Literal loopback only: no DNS, credentials, redirects, proxy or remote host."""
    p = urlsplit(url)
    try:
        host = '127.0.0.1' if p.hostname == 'localhost' else p.hostname
        valid = ipaddress.ip_address(host).is_loopback
        port = p.port
    except (ValueError, TypeError):
        valid, port = False, None
    if p.scheme != 'http' or not valid or not port or p.username or p.password or p.path not in ('', '/') or p.query or p.fragment:
        raise ValueError('Runtime endpoint must be an HTTP loopback origin with an explicit port')
    return f'http://[{host}]:{port}' if ':' in host else f'http://{host}:{port}'


class Cache:
    """Bounded, serialized cache, including failures, to avoid polling storms."""
    def __init__(self, limit=128):
        self.values = {}
        self.lock = threading.RLock()
        self.limit = limit

    def get(self, key, ttl, loader):
        with self.lock:
            cached = self.values.get(key)
            if cached and time.monotonic() - cached[0] < ttl:
                return copy.deepcopy(cached[1])
            try:
                result = loader()
            except Exception as exc:
                result = {'_error': str(exc)[:300]}
            if len(self.values) >= self.limit:
                self.values.pop(next(iter(self.values)))
            self.values[key] = (time.monotonic(), result)
            return copy.deepcopy(result)

    def clear(self):
        with self.lock:
            self.values.clear()

    def peek(self, key, ttl):
        with self.lock:
            cached = self.values.get(key)
            return copy.deepcopy(cached[1]) if cached and time.monotonic() - cached[0] < ttl else None


CACHE = Cache()


def model_list(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('models'), list):
        raise ValueError('Malformed runtime model list')
    models = payload['models']
    if any(not isinstance(m, dict) or not isinstance(m.get('name') or m.get('model'), str) for m in models):
        raise ValueError('Malformed runtime model entry')
    return models


def ollama_metadata(model, process=None, show=None):
    show = show if isinstance(show, dict) else {}
    details = model.get('details') if isinstance(model.get('details'), dict) else {}
    extra = show.get('details') if isinstance(show.get('details'), dict) else {}
    info = show.get('model_info') if isinstance(show.get('model_info'), dict) else {}
    result = {k: field() for k in FIELDS}
    resident_only = model.get('_resident_only', False)
    source = 'Ollama /api/ps' if resident_only else 'Ollama /api/tags'
    result.update(name=field(model.get('name') or model.get('model'), source),
                  runtime=field('Ollama', source),
                  weight_bytes=field(None if resident_only else positive(model.get('size')), 'Ollama /api/tags size (stored model)'),
                  compatibility=field('Resident model; installed registration unavailable' if resident_only else 'Registered with Ollama; execution not tested', source))
    for target, key in [('family', 'family'), ('parameters', 'parameter_size'), ('format', 'format'), ('quantization', 'quantization_level')]:
        result[target] = field(extra.get(key) or details.get(key), 'Ollama /api/show' if extra.get(key) else source)
    architecture = info.get('general.architecture')
    result['architecture'] = field(architecture, 'Ollama /api/show model_info')
    result['context_window'] = field(positive(info.get(str(architecture) + '.context_length')), 'Ollama /api/show model_info (maximum)')
    result['parameters'] = result['parameters'] if result['parameters']['value'] else field(positive(info.get('general.parameter_count')), 'Ollama /api/show model_info')
    # Do not disclose or infer blob storage from generated Modelfile strings.
    if process:
        result['configured_context'] = field(positive(process.get('context_length')), 'Ollama /api/ps (active context)')
        result['loaded_bytes'] = field(positive(process.get('size')), 'Ollama /api/ps size (runtime allocation, shared-memory attribution uncertain)')
    return result


def sglang_config(text):
    """Read allowlisted flags only, never evaluate service shell or expose secrets."""
    result = {}
    for flag in ('model-path', 'served-model-name', 'port', 'context-length', 'quantization', 'load-format', 'mem-fraction-static'):
        match = re.search(r'--' + flag + r'(?:=|\s+)([^\s\\\'\"]+)', text)
        if match:
            result[flag] = match.group(1)
    return result


def sglang_metadata(config, info=None):
    info = info if isinstance(info, dict) else {}
    result = {k: field() for k in FIELDS}
    result['runtime'] = field('SGLang', 'registered adapter', 'Verified from configuration')
    for target, key in [('storage', 'model-path'), ('configured_context', 'context-length'), ('quantization', 'quantization'), ('format', 'load-format')]:
        value = config.get(key)
        if target == 'configured_context':
            value = int(value) if value and value.isdigit() else None
        result[target] = field(value, 'qwen38-sglang.service --' + key, 'Verified from configuration')
    result['name'] = field(config.get('served-model-name') or config.get('model-path'), 'qwen38-sglang.service', 'Verified from configuration')
    for target, key in [('storage', 'model_path'), ('architecture', 'architectures'), ('context_window', 'context_length'), ('format', 'load_format')]:
        if info.get(key) is not None:
            result[target] = field(info[key], 'SGLang /get_model_info')
    result['compatibility'] = field('Registered SGLang controller; readiness checked separately', 'registered adapter', 'Verified from configuration')
    # A model identifier is not a verified local filesystem location or quantization.
    path = config.get('model-path', '')
    if not result['quantization']['value'] and re.search(r'(?i)nvfp4', path):
        result['quantization'] = field('NVFP4', 'configured model identifier', 'Inferred from filename')
    match = re.search(r'(?i)(\d+(?:\.\d+)?)[b](?:[-/]|$)', path)
    if match:
        result['parameters'] = field(match.group(1) + 'B', 'configured model identifier', 'Inferred from filename')
    return result


def runtime_requirement(row):
    """Planning allowance, not a capacity guarantee. No fixed weight=RAM claim."""
    meta = row.get('metadata', {})
    weight = positive(meta.get('weight_bytes', {}).get('value'))
    if weight is None:
        return {'bytes': None, 'kind': 'Unknown requirement', 'confidence': 'Unavailable',
                'method': 'Weight size and KV-cache geometry are unavailable.'}
    info = row.get('kv_geometry', {})
    context = positive(meta.get('configured_context', {}).get('value'))
    layers, heads, dim = (positive(info.get(k)) for k in ('layers', 'kv_heads', 'head_dim'))
    kv = 2 * layers * heads * dim * context * 2 if all((layers, heads, dim, context)) else None
    # 50% overhead plus at least 4 GiB for unknown KV/context/parallelism.
    allowance = max(4 * GIB, kv * 2) if kv else max(4 * GIB, weight * .5)
    return {'bytes': math.ceil(weight * 1.5 + allowance), 'kind': 'Estimated runtime requirement',
            'confidence': 'Estimated', 'kv_bytes': kv,
            'method': '1.5 × stored size + max(4 GiB, 2 × FP16 KV for one context). '
                      'Without active KV geometry: max(4 GiB, 0.5 × stored size). '
                      'Parallel clients, multimodal buffers and runtime reservations may exceed this allowance.'}


def fingerprint(rows, target=None):
    # Enriching unrelated descriptive metadata must not invalidate confirmation.
    # All residency/identity/configuration evidence and target sizing remain bound.
    evidence = [(r['key'], r.get('loaded'), r.get('uncertain'), r.get('state'), r.get('identity'),
                 r.get('runtime_config'), r.get('metadata') if r['key'] == target else
                 {k: r.get('metadata', {}).get(k, {}).get('value') for k in ('configured_context', 'loaded_bytes')},
                 r.get('kv_geometry') if r['key'] == target else None) for r in rows]
    return hashlib.sha256(json.dumps(sorted(evidence, key=lambda x: x[0]), sort_keys=True).encode()).hexdigest()


def preflight(rows, total, available, errors, action, target, stops):
    by_key = {r['key']: r for r in rows}
    if target not in by_key:
        raise ValueError('Model no longer registered; refresh the dashboard.')
    if action != 'switch' and stops or target in stops or any(s not in by_key for s in stops):
        raise ValueError('Invalid stop selection')
    row = by_key[target]
    if row.get('uncertain') or row.get('state') in ('starting', 'stopping', 'unknown', 'busy') or (row.get('state') == 'error' and action != 'unload'):
        raise ValueError('Target state is uncertain; refresh before operating.')
    if bool(row['loaded']) == (action != 'unload'):
        raise ValueError('Model state changed; refresh before operating.')
    if any(not by_key[s]['loaded'] or by_key[s].get('uncertain') for s in stops):
        raise ValueError('A selected model is no longer verifiably loaded')
    estimate = runtime_requirement(row)
    loaded = [r for r in rows if r.get('loaded')]
    released = sum(positive(by_key[s].get('metadata', {}).get('loaded_bytes', {}).get('value')) or 0 for s in stops)
    reserve = max(4 * GIB, total * .05) if positive(total) else 4 * GIB
    projected = min(total, available + released) if positive(total) and number(available) is not None else None
    reasons = []
    if action != 'unload':
        if errors or any(r.get('uncertain') for r in rows):
            reasons.append('Runtime inventory is incomplete; loaded-model conflicts cannot be established.')
        if projected is None:
            reasons.append('Available unified memory is unavailable.')
        elif estimate['bytes'] is not None and projected < estimate['bytes'] + reserve:
            reasons.append('Insufficient estimated memory, including the system reserve. Select explicit stops or reduce other usage.')
    warnings = ['Connected clients cannot be reliably detected. Unloading may interrupt active requests.',
                'External clients and runtime schedulers may change model residency or evict models independently.',
                'Memory estimates and reclaimed allocations are uncertain; available memory is checked again before loading.']
    if estimate['bytes'] is None and action != 'unload':
        warnings.append('Target runtime requirement is unknown. Confirmation accepts the risk of allocation failure.')
    if action == 'switch':
        warnings.append('Recovery restores only selected models and verifies them. A partially loaded target is never automatically removed; recovery may be incomplete.')
    return {'action': action, 'target': target, 'target_name': row['name'], 'runtime': row['runtime'], 'stops': stops,
            'loaded_models': [{'key': r['key'], 'name': r['name'], 'runtime': r['runtime']} for r in loaded],
            'available_bytes': available, 'total_bytes': total, 'estimated_release_bytes': released,
            'projected_available_bytes': projected, 'reserve_bytes': reserve, 'requirement': estimate,
            'blocked': bool(reasons), 'reasons': reasons, 'warnings': warnings,
            'expected_outcome': 'Target unloaded' if action == 'unload' else 'Target resident; readiness reported according to available runtime evidence',
            'fingerprint': fingerprint(rows, target)}


def nas_classification(files):
    """Structural completeness only; never authorizes an executable adapter."""
    directories = {}
    for item in files:
        directory = item['path'].rsplit('/', 1)[0] if '/' in item['path'] else ''
        directories.setdefault(directory, []).append(item)
    candidates, missing, metadata = [], [], {k: field() for k in FIELDS}
    for directory, items in directories.items():
        weights = [x for x in items if x.get('kind', 'Weight file') == 'Weight file']
        config = next((x for x in items if x['path'].endswith('/config.json') or x['path'] == 'config.json'), {})
        conf = config.get('config', {})
        names = {x['path'].rsplit('/', 1)[-1] for x in items}
        tokenizer = bool({'tokenizer.json', 'tokenizer.model'} & names)
        indexes = [x for x in items if x.get('kind') == 'Weight index']
        shards = [x for x in weights if re.search(r'-\d{5}-of-\d{5}', x['path'])]
        shard_sets = {}
        for shard in shards:
            match = re.search(r'^(.*)-(\d{5})-of-(\d{5})(.*)$', shard['path'])
            if match:
                shard_sets.setdefault((match[1], int(match[3]), match[4]), set()).add(int(match[2]))
        shards_complete = all(parts == set(range(1, total + 1)) for (_, total, _), parts in shard_sets.items() if total <= 1800)
        if any(total > 1800 for _, total, _ in shard_sets):
            shards_complete = False
        indexed = False
        if indexes:
            maps = [x.get('config', {}).get('weight_map') for x in indexes]
            indexed = all(isinstance(m, dict) and m and all(isinstance(v, str) and v in names for v in m.values()) for m in maps)
        complete = bool(weights and isinstance(conf.get('model_type'), str) and conf['model_type'] and tokenizer and
                        (not shards or (indexes and indexed and shards_complete)) and (not indexes or indexed))
        if complete:
            candidates.append(directory)
        if weights and not complete:
            missing.append(directory + ': configuration, tokenizer, shard index or referenced shards not established')
        if conf:
            source = config['path']
            for key, value in [('family', conf.get('model_type')), ('architecture', conf.get('architectures')), ('context_window', conf.get('max_position_embeddings'))]:
                metadata[key] = field(value, source, 'Verified from configuration')
    weights = [x for x in files if x.get('kind', 'Weight file') == 'Weight file']
    if candidates and not missing:
        classification = 'Complete model (structure only)'
    elif any(x['path'].endswith('adapter_config.json') for x in files) or (not weights and files):
        classification = 'Model components'
    elif weights and all(x.get('format') in ('ONNX', 'PT', 'PTH', 'CKPT') for x in weights):
        classification = 'Unsupported assets'
    elif weights:
        classification = 'Requires additional configuration'
    else:
        classification = 'Unknown assets'
    metadata['weight_bytes'] = field(sum(x['size'] for x in weights), 'read-only filesystem stat', 'Verified from configuration')
    metadata['compatibility'] = field('Unverified; no NAS runtime adapter. Weights are never executable by discovery.', 'structural file inspection', 'Verified from configuration')
    formats = {x.get('format') for x in weights}
    hint = ('GGUF may be compatible with an Ollama import, subject to architecture support and explicit registration.'
            if 'GGUF' in formats else
            'Hugging Face layout may suit SGLang; architecture, quantization and hardware support remain unverified.'
            if candidates else 'No compatible executable runtime has been established for these assets.')
    return {'classification': classification, 'classification_source': 'Read-only directory structure; contents and architecture support not validated',
            'classification_confidence': 'Estimated', 'compatibility_hint': field(hint, 'file formats and directory layout', 'Inferred from filename'),
            'missing_components': missing, 'metadata': metadata, 'runnable': False}
