# Security and operational safety

The server binds to loopback and uses a random per-process token for API access. The initial URL contains that token; do not share it or expose the server via LAN forwarding or a reverse proxy. The token does not protect against hostile processes or users on the same machine. Static assets are public on the local port; responses use a restrictive CSP for the main document. The Ollama endpoint can be overridden by `OLLAMA_HOST`, so its destination is part of the local configuration and trust boundary.

All requests require the exact `127.0.0.1:<application port>` Host, preventing arbitrary DNS names from reaching the application through rebinding. A supplied Origin must match that exact HTTP origin; cross-site and same-site Fetch Metadata requests are rejected. API authentication remains mandatory and uses constant-time token comparison. Browser requests from another loopback port are not trusted merely because they are local. There is no CORS opt-in. Operation POSTs require bounded JSON, reject transfer encoding and validate selections before creating workers. These guards are regression-tested through in-memory handlers; live HTTP/browser transport is currently blocked in this sandbox.

Model operations can interrupt clients and consume substantial shared memory. Actions require UI confirmation but cannot detect all clients or protect against changes made outside this process. SGLang process state is not inference readiness. Recovery is best effort; verify runtime state before relying on it. NAS discovery reads metadata only and does not establish that a model can run. Do not alter runtime configuration or model files through this application.

Report security issues privately to the repository maintainer; avoid including tokens, prompts or sensitive paths in reports. Operation logs include model names and error details, and are stored under the user's local state directory.

## Intelligent management boundaries

All status/detail/library/preflight APIs remain authenticated. A preflight request is read-only and never authorizes execution alone. A lifecycle request must confirm an exact, unexpired, single-use plan and acknowledge memory uncertainty and client interruption. The worker verifies current identities/residency/configuration and capacity before executing. Stops cannot contain the target or models outside inventory, and non-switch actions cannot contain stops. Request bodies are bounded and target selection is allowlisted against runtime discovery.

Runtime HTTP origins now accept only HTTP literal loopback addresses (localhost is normalized), explicit ports and no credentials, path, query or fragment. Environment proxies and redirects are disabled. A remote `OLLAMA_HOST` is rejected; this deliberately narrows the earlier configurable destination to the local-first trust boundary. `SGLANG_URL`, when needed, has the same restriction. No runtime listening address is changed. The existing backend remains bound to `127.0.0.1` with its random session token and CSP.

Monitoring uses metadata/process-list requests and the non-generating SGLang `/ready`. It never calls health-generation, flush-cache, weight-update or arbitrary Docker APIs. Service/container state is observed with fixed argument vectors. The only SGLang mutations remain the existing fixed controller's start/stop actions after confirmation. Ollama lifecycle uses structured fixed API payloads; unload no longer invokes its CLI. No shell input is constructed from model names. A Linux advisory lock prevents concurrent lifecycle workers across this application's instances; it does not control other clients or runtime schedulers.

Recovery is limited to authorized stops and verifies them before claiming their previous selected state. If target absence is uncertain, it reports incomplete recovery and avoids adding memory pressure. No automatic target cleanup, deletion, NAS import, backup change or runtime reconfiguration is performed. External automatic evictions and client activity remain outside this application's authority.

NAS JSON reads are size/count bounded, weight files are never opened, and discovered symlinks are skipped. Structural classification and inferred compatibility never create an executable model. Traversal now pins the model root and opens each directory component and JSON file relative to directory descriptors with no-follow flags. Metadata files must be regular and are opened nonblocking. This rejects replacement symlinks/FIFOs, but cannot guarantee responsiveness of a hung mount or isolate the process from its OS account privileges.

No elevated privileges were requested or added. On the installed workstation, the app requires existing user access to Ollama HTTP, read access to the registered SGLang unit, existing read permission for the fixed Docker inspect command, and the pre-existing controller's ability to start/stop its one service. It also needs write access to its existing private user state directory for logs and the lifecycle lock. Missing permissions must produce unavailable/blocked/error states; do not add sudo rules, Docker group membership or new service permissions automatically. Tests mock these interfaces and use temporary lock/log paths.

Plans/jobs/last-health-success are in process memory and do not survive application termination. Operation logs still need rotation. Tokens in launch URLs, local-process visibility, external clients, unknown busy state, uncertain per-model memory and incomplete recovery remain operational limits; do not expose this application through a proxy or LAN forwarding.

## Integration audit — 2026-11-03

The existing private SGLang gateway remains the authenticated boundary. Discovery reads only its published loopback bindings and never falls back to its namespace-only backend. The recognized deployment reads its existing compatibility key file in memory; application-only `SGLANG_API_KEY_FILE` may select another existing file. Reads are limited to regular files and 4 KiB; invalid/unreadable credentials fail before HTTP, without unauthenticated retries. Credential paths/values, request headers and upstream error bodies are not returned in health records. The local compatibility and gateway files were observed as mode 0600, without printing contents. Credential acceptance and active container mounts remain unverified because runtime access is denied.

Readiness authentication errors and missing endpoints do not justify weakening security or calling a generating endpoint. Model identity is revalidated separately from readiness. Conflicting Ollama registered/resident digests block mutation; SGLang requires matching endpoint identity and agreeing process evidence. The worker rechecks plan expiry before runtime discovery/mutation. Unknown requirements/reclamation never bypass the system memory reserve.

The browser E2E server uses a clearly synthetic session token, temporary state, and guards that reject every runtime/NAS discovery and lifecycle entry point. Its actual application interactions use explicit Demo Mode, and its offline test intercepts API requests. It never substitutes a live server for missing fixture support. The runner reports BLOCKED when Playwright/browser/socket prerequisites fail; it must not be counted as security or browser validation.

Current evidence: 85 Python tests and all JavaScript suites pass; no live model or service operation was performed. Remaining risks include existing launch-token exposure to local history/processes, local-user access, external scheduler races, absent client detection, uncalibrated memory estimates, non-durable jobs, unrotated logs and potentially blocking NAS filesystem calls. This source/mocked audit is not an independent penetration test or a live runtime security certification. See [the validation report](docs/audits/INTEGRATION_VALIDATION_REPORT.md) for acceptance gates.


## Public release audit — 2026-11-03

The [public release security audit](docs/audits/PUBLIC_RELEASE_SECURITY_AUDIT.md)
classifies the overall decision as **INCOMPLETE_AUDIT**. No live secret or P0/P1
issue was confirmed within inspected local source/history. Remote artifacts and
security settings, effective host privilege policy and real browser/transport
acceptance still lack sufficient evidence. Publishing code does not create a
route to the workstation. Do not use older `main` as the audited release.

Application corrections pin private state files and NAS traversal to directory
descriptors, reject links/devices, bound log fields, cap HTTP request workers at
16 and apply a 10-second socket inactivity timeout. Duplicate security headers
and incomplete bodies are rejected; response policies cover static/error paths.
State directories must be owned by the running account and private (0700);
unsafe existing state fails closed without an automatic permission change.
These limits do not prevent sustained local denial of service or a hung mount.

The authenticated launch URL remains a credential. Same-user processes or
browser extensions may obtain it; Demo Mode does not revoke a live token.
Only theme preference is stored in localStorage. Keep URLs out of tickets,
screenshots and shared browser history; restart the app after token exposure.

Current isolated evidence: 101 Python tests, all three JavaScript suites and
syntax/whitespace checks pass. Chromium/Firefox fixture execution remains
BLOCKED. No installer, live model operation or privileged configuration change
was performed. See the audit for exact prerequisites, findings, residual risks
and administrator-only recommendations.
