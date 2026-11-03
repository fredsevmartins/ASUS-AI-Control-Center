# Testing

## Required automated checks

Run from the repository root. These checks do not contact live runtimes or perform model operations:

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

Latest integration pass, starting at `9534fc0`: **85 Python tests passed**, all three JavaScript suites passed, and JavaScript/shell syntax and whitespace checks passed. No tests were skipped in the Python suite. The prior baseline was 63 Python tests; this pass adds 22 audit regressions. These results establish mocked contracts and source/DOM behavior, not live runtime compatibility or rendered accessibility.

`bash -n install.sh` checks syntax only. Never execute the installer as validation: it changes installed v5 files and the launcher.

## Automated coverage

| Area | Evidence |
| --- | --- |
| SGLang discovery/authentication | Independent systemd/container observations; model identity; 401/403 on metadata and readiness; unavailable transport; direct/wrapped timeout; 404/405/501 unsupported; explicit 503; authenticated GET success; stale last success; no generating fallback |
| SGLang interface/security | Drop-in replacement, inspected published loopback bindings, unknown mappings, remote origins/credentials in URLs rejected, existing credential file validation, response size bound, proxies/redirects disabled, no credentials or upstream error bodies returned |
| Ollama | Independent tags/ps failures, orphan residents with unknown installation, stored vs resident size, maximum vs active context, cached show/failures, incomplete/malformed architecture/digest data, identity conflicts and pre-mutation digest revalidation |
| Metadata | Explicit value/source/confidence, missing values retained, current allocation/context supersede cached details, inferred SGLang NVFP4/parameter labels |
| Preflight/authorization | Capacity and KV estimate, unknown requirements/reclamation, reserve enforcement, worker expiry recheck, stale fingerprints, exact selected stops, confirmation/risk acknowledgement, single-use/expired/tampered plans |
| Lifecycle/recovery | Mocked load/unload/switch and failures, worker startup failure, readiness failure, selected restoration, final recovery verification, partially loaded target retained, failed restoration, transient retry deadline and permanent failure fast exit |
| Concurrency/logging | Real simultaneous confirmation threads start one mocked worker, temporary advisory-lock contention, serialized sampling, bounded activity reads, malformed records, private temporary log directory/file |
| HTTP/security | In-memory handlers: session protection for every API, exact Host, Origin/Fetch Metadata rejection, Unicode invalid tokens, JSON/body/stop limits, transfer encoding rejected, static path allowlist, CSP/no-store/referrer headers |
| Frontend | Seven-view navigation source contract, storage validity/CSP markup, fixed 0–128 GiB charts, local times, sample selection, repeated high-DPI sizing, gauges/unavailable/decimal readings, filters/details, process/auth copy, preflight races, error retention, modal keyboard trapping and explicit stops |
| Demo isolation | Zero fetch calls for simulated status/details/library/preflight/actions; simulated failure leaves previous models unchanged; missing confirmation and reused plans rejected |
| NAS | Temporary bounded directory fixtures, symlinks ignored, malformed config and missing shards, structural classifications always non-runnable |

Python tests mock runtime operations and invoke API handlers without sockets. Lifecycle adapters, service/controller calls, inference and real model operations must never be used as unit-test fixtures. Logs and advisory locks must use temporary directories. JavaScript suites use VM/DOM/canvas harnesses and do not render a browser.

## Real-browser E2E acceptance

```sh
node tests/browser_e2e.mjs
AI_MANAGER_E2E_BROWSER=firefox node tests/browser_e2e.mjs
```

Use one command for an already provisioned Playwright browser. The application itself has no npm or Python package dependencies; this optional test runner requires an existing Playwright package and compatible browser binaries. It installs/downloads nothing. The runner exits 2 and prints BLOCKED for missing tooling/browser/socket access, 1 for assertion failure, and 0 only after passing its checks.

The runner launches `tests/browser_server.py` on a separate random loopback port with a synthetic token. Every runtime/NAS discovery and lifecycle entry point is patched to reject live access, and state/log paths are temporary. It exercises the actual application HTML/CSS/JavaScript in explicit Demo Mode, not the installed stable application. Never point the operation tests at a live server or remove the fixture guards.

The implemented acceptance cases cover all seven sections; light/dark themes; 1440, 390 and 320 pixel widths; DPR 2 and reduced-motion emulation; search/filter/details/provenance; gauges, canvas backing-size stability and timeline keyboard inspection; native storage progress; Cancel/Escape/focus restoration and Tab trapping; unchecked stop selection; risk acknowledgement; simulated switch and failure; Activity feedback; and intercepted connection failure. Document/session/Origin rejection runs over the fixture's real HTTP transport. Production lifecycle API paths are separately covered by mocked Python integration tests.

On success, screenshots and `results.json` go to `/tmp/asus-ai-browser-evidence` by default; set `AI_MANAGER_E2E_ARTIFACTS` to a writable evidence directory. The results explicitly state fixture-only coverage and no live runtime validation. No launch URL, real session token or runtime credential is captured.

**Current result: BLOCKED**, exit 2, because Playwright is not installed. No browser cases ran and no screenshots/results artifact were produced. The browser connector independently failed because its profile was already in use; the alternate computer-use browser inventory was empty. An isolated Firefox headless attempt failed because snap-confine lacks the required permitted capability; it produced no screenshot. Both the development app and the isolated fixture server failed to bind loopback with PermissionError. The mechanical Impeccable detector used degraded regex mode and returned `[]`; HTML parser modules and computed-contrast checks were unavailable. This is not rendered UI acceptance.

## Fresh GX10 observations and blocked checks

Verified read-only on this host during the current pass:

- Host `gx10-cbc7`, architecture `aarch64`, Python 3.12.3 and Node 22.23.1.
- `/proc/meminfo` reported 130,593,968,128 total bytes; available memory was a transient sample, not a model capacity calibration.
- `/mnt/nas/AI-Models` and `/mnt/nas/Storage` are mounts. `/mnt/ai-models` exists but is not a mount; it now reports offline.
- A bounded NAS metadata scan found 16 recognized asset files in four collections, all classified Requires additional configuration and non-runnable. No weights were read or modified.
- The base SGLang unit references `qwen38-dflash2:v1.2.3` and the registered Qwen identifier. The installed security drop-in starts existing gateway/network containers and attaches to the SGLang container. This is configuration evidence, not its running package version.
- Existing compatibility/gateway credential files are regular files with mode 0600. Contents were not printed or copied during diagnosis.
- Saved gateway rules require bearer authentication, contain no `/ready` exemption and do not rewrite paths/methods. Their current container mount could not be independently inspected.
- The Ollama CLI reports version 0.30.8. The running server version/inventory remain unverified. The supported GPU query returned unavailable.

Blocked by current sandbox permissions: systemd bus access, Docker socket inspection, Ollama `/api/version`, `/api/tags`, `/api/ps`, gateway HTTP probes and application loopback sockets. The user's reported active/resident SGLang state and `/ready` 404 were not independently reproduced here. Do not label these checks passed.

No service/container restart, model load/unload/switch, inference, runtime/NAS configuration change, weight modification or installer execution was performed.

## Remaining acceptance on the workstation

Run the fixture browser suite with working local sockets/tooling. Separately run the development application from the checkout on a random loopback port and inspect read-only status, details and library against the actual runtimes. Confirm current gateway bindings, SGLang package version and route implementation with authorized read-only access; do not rely on an image tag or upstream main branch as deployed-version evidence.

Confirm Ollama installed models match `/api/tags`, residents match `/api/ps`, provenance remains accurate and failures preserve independent evidence. Confirm authenticated metadata matches the registered SGLang model. Unsupported `/ready` must remain Loaded with Unverified inference readiness; auth/identity failures must retain process signals without claiming Ready. Never probe `/health` or `/health_generate` to resolve this gate without auditing the deployed implementation and separate approval for any inference.

Rendered acceptance still requires desktop/mobile, both themes, 200% zoom, touch/pointer chart interaction, keyboard focus and assistive technology, long identifiers and contrast. The harness automates part of that matrix; manual screen-reader/zoom/touch checks remain separate. Earlier user confirmation that charts/gauges rendered in Firefox is historical evidence and does not validate this revision.

Live lifecycle/recovery tests require separate explicit approval and an interruption window. Existing mocked adapters establish tested request/recovery contracts only. Memory estimates remain uncalibrated, connected clients cannot be reliably detected, process state does not prove inference readiness, and jobs/history are not crash-resumable. See the explicit release criteria in [the validation report](docs/audits/INTEGRATION_VALIDATION_REPORT.md).

## Premium visual refinement — 2026-11-03

This visual-only pass changes `web/style.css` and presentation code in `web/app.js`.
All 85 Python tests and all three JavaScript regression suites passed. Python,
JavaScript, installer shell syntax (without executing it), and diff whitespace
checks passed. No live lifecycle adapters or model operations were exercised.

Both Chromium and Firefox fixture commands remain **BLOCKED** (exit 2):
Playwright is not installed. A fresh socket probe also failed with PermissionError
before binding a random loopback port. The computer-use inventory returned no
apps or browsers. No development server replaced the stable application, and no
before/after screenshots could be captured.

The design detector returned `[]`; this does not establish rendered acceptance.
Calculated palette contrast for primary/secondary/accent text, warning text and
primary buttons ranged from 4.91:1 to 15.74:1 across the sampled light/dark pairs.
This is a source-color calculation, not a computed-style or rendered contrast audit.

Light/dark rendering, desktop and small-screen resizing, actual Firefox ARM64
rendering, focus visibility, dialog/loading-state readability and gauge appearance
remain **NOT VERIFIED** in a browser. Existing mocked focus, operation, gauge and
chart regressions pass, but cannot close these visual acceptance gates. Release
readiness remains withheld until the guarded browser suite and manual checks run
in an environment with the prerequisites described above.
