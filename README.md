# ASUS AI Control Center v5

Local-first workstation dashboard for the ASUS GX10 (Ubuntu ARM64). The Python standard-library backend and dependency-free HTML/CSS/JavaScript frontend provide Overview, Model Manager, Model Library, Performance, Workspaces, Activity and Settings. The interface is English-only and uses local assets.

The development assessment is **PARTIAL**: automated regressions pass, but live runtime and rendered browser acceptance are blocked in the development sandbox. See [the integration validation report](docs/audits/INTEGRATION_VALIDATION_REPORT.md) for evidence and release gates. SGLang inference readiness remains **UNVERIFIED** when its safe readiness endpoint is unsupported.

## Run development alongside the installed application

```sh
cd /path/to/ASUS-AI-Control-Center
git switch dev/premium-control-center
AI_MANAGER_PORT=0 python3 server.py
```

The development server binds to a random `127.0.0.1` port and opens its authenticated launch page in the default browser. It does not replace the installed v5 files or launcher. Keep its terminal open while using it. Do not run `install.sh` for development validation; the installer updates the installed application. The stable application remains available through its existing desktop shortcut or `python3 ~/.local/share/asus-ai-model-manager-v5/server.py`.

Never share the launch URL, session token or runtime credentials. Do not expose the application through a reverse proxy, forwarding or LAN binding.

## Runtime discovery and safety

- Ollama `/api/tags`, `/api/ps` and `/api/show` supply independent installation, residency and metadata evidence. A failed installed inventory does not hide observable residents. Residency alone never means inference Ready.
- SGLang keeps systemd, container, model identity and endpoint readiness separate. Its private gateway requires bearer authentication. The recognized gateway setup uses the existing `~/.config/qwen38/api-key` compatibility file in memory only.
- If necessary, set application-only `SGLANG_URL` to an already published HTTP loopback gateway origin and `SGLANG_API_KEY_FILE` to an existing credential file. No key belongs in a URL or command argument. Missing bindings/credentials fail closed; discovery never bypasses the gateway or changes the runtime.
- `/get_model_info` identifies the model; `/ready` is tried only after identity matches. Unsupported `/ready`, authentication failure and timeout leave readiness Unverified. Monitoring never calls `/health`, `/health_generate` or inference endpoints.
- Model operations require an exact, unexpired single-use preflight plan, explicit confirmation and risk acknowledgement. Only explicitly selected models may be stopped. Memory estimates are conservative heuristics, not measured model requirements; the system reserve applies even when target size is unknown.
- The existing SGLang controller and fixed Ollama APIs remain the lifecycle adapters. No model pulls, deletions, migration, runtime configuration changes or automatic partial-target cleanup are supported. Recovery is limited to selected stops and verifies its result.
- NAS discovery reads bounded metadata and file sizes, never weights. All discovered assets remain non-runnable. Workspaces are informational presets.
- CPU/memory history is bounded, sampled while the application is open and lost on restart. Unified GB10 memory cannot reliably be attributed to individual models. GPU telemetry may be unavailable.

## Tests

```sh
python3 -m unittest discover -s tests -v
node tests/test_frontend.js
node tests/test_model_manager.js
node tests/test_model_intelligence.js
python3 -m py_compile tests/browser_server.py
node --check web/app.js
node --check tests/browser_e2e.mjs
bash -n install.sh
git diff --check
```

Current result: **101 Python tests and all three JavaScript suites pass**. Runtime operations are mocked and lock/log tests use temporary directories.

Real-browser acceptance is a separate required release gate:

```sh
node tests/browser_e2e.mjs
# With an already provisioned Firefox Playwright browser:
AI_MANAGER_E2E_BROWSER=firefox node tests/browser_e2e.mjs
```

The optional test tooling requires an existing Playwright package and compatible browser. The runner downloads nothing, starts an isolated loopback fixture server, exercises the explicit demo mode and forbids live runtime/NAS adapters. It exits **2 / BLOCKED** if prerequisites are unavailable; blocked checks are not passes. See [TESTING.md](TESTING.md) for coverage, artifacts and hardware validation boundaries.

See [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md), [ROADMAP.md](ROADMAP.md) and [AGENTS.md](AGENTS.md) for implementation contracts, risks and contributor constraints. Live load/unload/switch or inference validation requires separate explicit approval and an appropriate client interruption window.


## Public release security status

The [public release security audit](docs/audits/PUBLIC_RELEASE_SECURITY_AUDIT.md)
is **INCOMPLETE_AUDIT**: local source/history inspection found no confirmed live
secret, and application hardening passes isolated regression tests, but remote
publication artifacts/settings and effective workstation/browser protections
remain unverified. The repository remains private. Publishing source does not
expose a loopback workstation service by itself.

The audited development branch includes safe state-file/NAS traversal and
bounded HTTP workers; older `main` lacks these and earlier lifecycle protections.
Review and merge the audited changes before distributing a release. Keep the
checkout and installation paths trusted, and never run the installer with sudo.
See [SECURITY.md](SECURITY.md) for the local-process, launch-token and NAS trust
boundaries. No installed application or host configuration was changed by the audit.
