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
