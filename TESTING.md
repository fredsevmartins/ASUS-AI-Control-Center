# Testing

Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
node tests/test_frontend.js
node --check web/app.js
```

Python tests mock runtime operations and exercise API handlers without opening sockets. The frontend regressions cover Performance navigation, storage percentages and invalid values, CSP-compatible progress markup, gauge telemetry validation, independent unavailable values, GPU temperature parsing, and CSS theme, responsive, and reduced-motion rules, fixed GiB axis ticks and byte-to-GiB mapping, local timestamps, empty state, resizing, theme drawing, high-density redraw sizing, and simulated pointer and keyboard sample selection on both charts. They are not browser rendering tests. No test should load, unload or switch live models. Tests do not change services or NAS files.

The current sandbox forbids localhost sockets, so browser E2E, screenshot regression, and real HTTP integration could not be run here. Hardware, runtime readiness, long-running operations and recovery require validation on the target machine. Read-only checks should precede any controlled runtime operation, which requires explicit approval and no active clients. Do not run `install.sh` merely to test: it changes the installed v5 files and launcher.

On the GX10, Firefox previously confirmed the Memory Timeline rendered and Overview and Performance displayed live telemetry. Recheck the updated storage bars, chart tooltip, keyboard and touch interaction, resizing, contrast, and both themes in a real browser. Storage used is total minus space available to the current user; reserved blocks may be included in used space.

Both charts use a fixed 0–128 GiB scale; samples above 128 GiB are clipped visually and identified in the sample details. History is held in the server process (up to 180 status samples), survives page navigation, and is lost on server restart. The UI requests status every five seconds, though actual sampling can be affected by delays and other sessions.

The gauges use current API readings and show unavailable for missing or out-of-range values. Memory capacity is supplied by telemetry and may differ from nominal installed memory. The automated gauge layout and theme checks inspect markup and CSS; they do not verify rendered contrast, animation, or screen-reader behavior. Validate those in a real browser at desktop and mobile widths, in both themes and with reduced motion.

The user visually validated the existing Performance gauges in Firefox on the GX10. Validate the new compact Overview gauges and telemetry details in both themes and at multiple widths; automated checks do not test rendered layout.

## Premium Model Manager prototype

Run `node tests/test_model_manager.js` in addition to the commands above. This suite verifies zero-network prototype routing, explicit switch stop selection, busy rejection, simulated failure retention and stale/uncertain/submitting action guards. It evaluates JavaScript in a VM; it is not a rendered browser test.

See `docs/design/IMPLEMENTATION-HANDOFF.md` for the static loopback-only prototype workflow and browser acceptance matrix. All demo data and operations are labeled and simulated. The current environment again rejected localhost socket creation; Chromium failed during snap initialization, and the browser connector required unavailable approval. Screenshots, rendered contrast, focus behavior and responsive layout remain unverified here. The design detector ran in regex fallback mode because parser modules are missing; an empty findings list does not validate contrast.

## Intelligent model management — 2026-11-03

Full regression commands (all required):

```sh
python3 -m unittest discover -s tests -v
node tests/test_frontend.js
node tests/test_model_manager.js
node tests/test_model_intelligence.js
node --check web/app.js
bash -n install.sh
git diff --check
```

Baseline at `b980f88`: 14 Python tests, the existing frontend and prototype suites, and JavaScript syntax passed before editing. Current evidence: 46 Python tests and all three JavaScript suites pass; JavaScript/shell syntax and whitespace checks pass. The Impeccable mechanical detector returned `[]` for the changed web targets. These results do not establish rendered contrast or browser behavior.

New Python fixtures cover structured Ollama metadata/provenance, maximum vs active context, show caching/failure caching, malformed/missing responses, unavailable runtime/process information, orphan residents, SGLang model identity, `/ready` rejection/unsupported/timeout, last successful health check retention, readiness-required verification, loopback restrictions, redirect rejection, memory preflight, insufficiency, unknown requirements, KV calculation, stale fingerprints and unrelated metadata enrichment, plan expiry/selection binding/reuse, overlapping requests, advisory locks, worker startup failure, failed loads/unloads/readiness, partial targets, successful/failed restoration and final recovery verification. NAS fixtures cover bounded scans, file symlinks, malformed config and missing shards without touching NAS. Activity parsing tolerates corrupt records and system-memory failure does not remove model inventory.

The API integration test uses in-memory handlers and mocked runtime adapters through preflight → confirmed switch → refreshed status. It asserts that the unselected model remains active and that the operation reaches Complete. No sockets are opened. Advisory-lock tests write only to temporary directories. Mocked execute tests verify structured unload and empty embedding preload request shapes without performing them.

`test_model_intelligence.js` uses a VM and DOM harness to verify escaped model names/errors, provenance, cards, action validity, filters, details, unknown estimates, blocked plans, explicit acknowledgement, selection invalidation, stale asynchronous preflight responses, failure feedback and Tab wrapping including advanced disclosure summaries. Prototype tests also reject missing confirmation and reused plans, and assert zero fetch calls for status, details, library, preflight and actions. Existing tests retain navigation, gauges, memory charts, theme, responsive CSS and reduced-motion checks.

### Outstanding release gates

No browser surfaces were exposed by the browser connector. This sandbox also rejects local runtime sockets. Browser screenshots/E2E, rendered themes/contrast, responsive layouts, focus restoration, assistive technology, real HTTP transport, installed Ollama inventory, actual SGLang version/endpoint support and GX10 memory calibration remain unverified. No live lifecycle action, service change, NAS scan or installer execution was performed for validation.

On GX10, first perform read-only checks: confirm installed inventory matches `/api/tags`, residents match `/api/ps`, provenance is accurate, endpoint identity matches the registered service and `/ready` is supported without generation. Verify that an unsupported `/ready` remains Loaded/unverified rather than Ready. Review both themes at desktop/mobile widths and 200% zoom, search/filter empty states, details, keyboard dialog order, stale/blocked preflight, explicit stop selection and risk acknowledgement. Demo Mode should produce no network traffic even when simulating failure.

Any subsequent live load/unload/switch test requires a separate explicit approval and a client interruption window. Do not infer that approval from this development request. Do not install/update runtimes or change service configuration to make a test pass. If the deployed SGLang lacks safe readiness support, document it and keep conservative failure behavior.

## SGLang authentication regression — 2026-11-03

Run every command in the full regression block above. Current result: 63 Python tests, all three JavaScript suites, JavaScript and shell syntax, and whitespace checks pass. The mechanical UI detector reports `[]` for `web/app.js`; this does not establish rendered accessibility or contrast.

`tests/test_sglang.py` adds mocked regressions for 401 and 403 on both `/get_model_info` and `/ready`, connection refusal/unavailable runtime, direct and urllib-wrapped timeouts, service active with unknown readiness/container state, healthy authenticated metadata plus readiness, and unsupported `/ready` (404/405/501). It distinguishes `/ready` 503 from gateway/server errors, verifies matching identity before readiness, retains historical success without claiming current readiness, and blocks preflight when identity is unverified.

Configuration/transport fixtures verify that the installed gateway-style `ExecStart` replacement prevents stale base-port inference, only inspected published loopback bindings are selected, unknown/remote bindings fail closed, explicit local origins work, proxies/redirects stay disabled, and only the two allowlisted non-generating GETs run with two-second I/O timeouts. Authentication fixtures use temporary files with synthetic tokens, test the default compatibility-file selection and explicit file override, reject empty/oversized/header-injection content, assert no network calls on invalid credentials, and assert credentials, paths and upstream error text/bodies are absent from observation results. No real credentials are read by the tests. Frontend regressions check that an active service/running container remains visible beside Unverified readiness and a 401 explanation, with model actions unavailable when identity is unknown.

Read-only diagnosis inspected the base unit, security drop-ins, saved HAProxy configuration and saved deployment evidence. The exact request producing the reported 401 is identified from the old request order and configured origin: `GET http://127.0.0.1:30000/get_model_info`, before `/ready`. Saved gateway rules require a bearer header even for monitoring; saved loopback publication maps that interface to the private gateway. These are configuration observations, not a new live reproduction. systemd bus, Docker socket and loopback HTTP access are denied here; deployed SGLang version, current gateway bindings/mount, accepted credentials and `/ready` support remain unverified. No service/container restart, runtime reconfiguration, inference, lifecycle action, NAS access or installer execution was used for validation.

On the target workstation, refresh the development application's Model Manager using its existing launch/session authentication. Inspect process signals separately from `health.probes.metadata` and `health.probes.readiness`. For the recognized gateway deployment the application uses the existing compatibility file at `~/.config/qwen38/api-key`; if another existing credential is required, set the application-only `SGLANG_API_KEY_FILE` to its path. If Docker binding inspection is unavailable, set application-only `SGLANG_URL` to the already published HTTP loopback gateway origin. Never paste a key into a URL, command argument, screenshot, log or bug report. Do not change gateway/runtime settings or expose the backend to make discovery work.

A successful authenticated metadata response must match the registered model before readiness is attempted. Expect Ready only for `/ready` 200 with agreeing active processes; expect Loaded/unverified for unsupported readiness, and Unknown/Unverified with preserved process signals if metadata access cannot be verified. Recheck both themes and narrow widths for the added process facts. Real inference readiness and live lifecycle/recovery validation remain separate release gates; this assignment does not authorize inference or model operations.
