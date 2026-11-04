# Prioritized roadmap

## Current integration assessment

**PARTIAL**, based on the integration pass starting at `9534fc0` on `dev/premium-control-center`. Automated contracts pass; live runtime and browser acceptance remain blocked. See [the validation report](docs/audits/INTEGRATION_VALIDATION_REPORT.md) and [TESTING.md](TESTING.md). Historical Firefox observations are not acceptance evidence for the current revision.

## Completed on the development branch

- Preserve the seven-section Astra interface, light/dark tokens, semicircular gauges, fixed GiB timelines, search/filter/details, protected confirmation and explicit demo isolation.
- Add provenance-aware metadata and independent installed, resident, process and readiness evidence. Unknown values remain unknown; orphan Ollama residents are not marked verified installed.
- Discover the existing private SGLang gateway without bypassing authentication or changing infrastructure. Unsupported non-generating readiness stays Unverified; permanent contract failures end verification promptly.
- Preserve dynamic Ollama discovery when tags or process observations fail independently; block digest conflicts and revalidate identities before operations.
- Require expiring single-use preflight plans, explicit risk acknowledgement, exact stop selection, fresh worker checks, memory reserve even for unknown requirements, and honest unknown reclamation.
- Protect process/cross-instance lifecycle concurrency, verify only selected recovery state, retain partially loaded targets and serialize telemetry sampling.
- Add exact Host/Origin/session/input guards; preserve loopback-only runtime origins, redirect/proxy restrictions, fixed subprocess arguments and credential-safe diagnostics.
- Correct cached residency metadata, decimal GPU readings, persistent Activity errors and unmounted external-storage reporting.
- Pass 85 mocked Python tests, three JavaScript suites and syntax/whitespace checks. Add a guarded real-browser fixture runner; its current execution is BLOCKED, not passed.
- Verify local NAS mounts and a bounded 16-asset/four-collection metadata inventory read-only, with no executable NAS registration.

## P0 — remaining release gates

1. Obtain working read-only access in the validation environment to confirm actual SGLang package/version/routes, gateway exposure/authentication, Ollama server inventory and current model identity/residency. Do not change the runtimes or permissions to force readiness success.
2. Run fixture browser acceptance with existing Playwright/browser tooling and working loopback sockets. Validate the live development dashboard separately in Firefox or another supported browser.
3. Complete desktop/mobile light/dark, 200% zoom, keyboard/screen-reader, touch and rendered-contrast checks. Fix verified defects while retaining the existing design.
4. Keep SGLang inference readiness UNVERIFIED if no supported non-generating contract is available. This is an acceptable honest status, not permission to infer Ready or invoke generating health checks.
5. Reassess every acceptance criterion with actual evidence before changing PARTIAL to READY or READY_WITH_LIMITATIONS.

## P1 — reliability beyond the current tested contracts

- Calibrate model memory allowances for context, KV dtype, parallelism and runtime reservations; do not represent model weight size as an allocation bound.
- Add a bounded durable operation journal/log rotation and a crash-interruption report. Do not automatically resume mutations after restart.
- Isolate NAS filesystem calls in a time-bounded worker so a hung mount cannot hold an HTTP worker indefinitely.
- Define workload/client-use evidence only through supported cheap interfaces. Unknown busy state must remain explicit.
- Only with separate explicit approval, perform controlled load/unload/switch/recovery validation during a client interruption window. No such live-operation approval is included in this development scope.

## P2 — maintainability and optional capabilities

- Extract the compressed frontend into small local modules with explicit static-routing/CSP tests; prefer keyed DOM updates that preserve focus.
- Extend searchable NAS metadata and structural compatibility hints without creating runnable adapters from discovered weights.
- Add persisted workspace planning only after defining safe adapter and confirmation semantics; current presets remain informational.
- Add multimodal runtime adapters only with readiness, capacity, recovery and permission contracts. Do not reconfigure live runtimes as part of UI development.
