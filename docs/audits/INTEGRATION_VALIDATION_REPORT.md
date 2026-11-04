# ASUS AI Control Center — Integration validation report

Date: 2026-11-03. Branch: `dev/premium-control-center`. Starting and current HEAD: `9534fc083e91cf54ba20c6e426389b80532b8199` (`Fix authenticated SGLang discovery and readiness reporting`). This report covers the additional working-tree implementation, not a deployment of the installed v5 application.

## Executive summary

**Final classification: PARTIAL. SGLang inference readiness: UNVERIFIED.**

Engineering changes are implemented and the required socket-free suites pass: 85 Python tests, three JavaScript suites and syntax/whitespace checks. This pass adds 22 Python audit regressions plus frontend coverage and a guarded browser acceptance runner. Confirmed inventory, metadata, capacity, authorization and telemetry defects were corrected.

Current runtime integration and rendered acceptance cannot be signed off. Fresh attempts were denied access to the systemd bus, Docker socket and loopback sockets. Playwright is unavailable, the browser connector has a profile conflict, no alternate browser surface is exposed, and isolated Firefox cannot launch under the available snap capabilities. No blocked check is counted as passed. No inference, live model lifecycle action, service/container restart, runtime/NAS configuration change, weight modification, installer execution or push was performed.

## Initial state and audit scope

The working tree was clean at the reference commit, with no subsequent commits. All existing commits were preserved. Reviewed the backend, frontend, intelligence/lifecycle code, all test suites, contributor instructions, architecture/security/testing/roadmap documents and product/design/handoff/audit notes.

The application retains its Python standard-library server, authenticated loopback API, dependency-free seven-section frontend, existing SGLang controller, fixed Ollama API adapters and bounded read-only NAS discovery. Workspaces remain informational. The installed stable application and runtime ownership are separate from this checkout.

## Root causes and implemented corrections

| Finding | Root cause | Correction and regression evidence |
| --- | --- | --- |
| SGLang `/ready` 404 | The requested route is unsupported or unavailable through the deployed contract; the exact running implementation could not be inspected | Preserve Loaded with Unverified readiness when process/identity evidence agrees. Fail lifecycle verification promptly on unsupported/authentication/identity contracts; retry transient observations within the deadline. No generating fallback. `test_sglang.py`, `test_validation.py` and frontend state fixtures |
| Earlier metadata 401 | The pre-reference implementation sent unauthenticated `/get_model_info` and inferred a direct interface from the superseded base unit | Already corrected at `9534fc0`; preserved and rechecked in the audit. The installed security drop-in and saved gateway authentication rules remain consistent with that diagnosis. Current live credential acceptance was not reproduced |
| Ollama residents disappeared on tags failure | `discover_models()` returned before calling `/api/ps` | Always observe installed and resident lists independently; retain observable residents and the installed-inventory error |
| Orphan resident marked installed | A resident process was used as installation proof | `installed: null` and independent `registration_observed: false`; no stored-weight size inferred from process allocation |
| Incomplete metadata could break details | Optional architecture/digest values were assumed to be strings/hashable | Validate optional types and preserve otherwise valid inventory/provenance |
| Stale details could replace current residency | Cached detail metadata overrode fresh allocation/context | Fresh allocation/context, including missing values, take precedence; descriptive cache enrichment remains available |
| Weak capacity handling for unknown sizes | Unknown target estimates skipped the reserve check; unknown selected allocation became zero | Enforce reserve in preflight and immediately before loads/restoration. Public unknown reclamation remains null; projection counts no unverified release and includes a warning |
| Model replacement after review | Residency checks used model name/process state without a fresh identity check | Block conflicting installed/resident digests, bind resident identity in fingerprints, revalidate Ollama digest and SGLang model identity before operations |
| Delayed worker could outlive plan authorization | Expiry was checked on HTTP acceptance but not again in the worker | Reject expired plans before fresh discovery/mutation |
| Missing local origin/host checks | Session token was the principal request gate | Add exact Host, supplied Origin and Fetch Metadata checks; retain token authentication with constant-time comparison, JSON/selection bounds and unsupported transfer-encoding rejection |
| Telemetry inconsistency | Simultaneous requests could race CPU deltas/history; NVMe path did not require a mount; GPU parser accepted integers only | Serialize sampling, require mounts under `/mnt/`, and support decimal GPU readings |
| Activity errors disappeared; empty view used blocked inline styling | Only a temporary toast reported refresh failures, and empty-state markup conflicted with CSP | Retain error/retry guidance in the section and remove inline styling; behavioral regressions cover both states |

## SGLang runtime compatibility and endpoint contracts

Fresh read-only configuration evidence:

- The base unit registers `RadixArk/Qwen3.8-27B-NVFP4`, served name `qwen3.8-27b`, static memory fraction 0.50 and image reference `qwen38-dflash2:v1.2.3`.
- The installed `security-gateway.conf` replaces the launch with starts of the existing private-network/gateway containers and an attachment to the existing SGLang container. The base host-network flags are not proof of effective container settings.
- Existing compatibility and gateway credential files are regular mode-0600 files. No credential contents were printed or copied for diagnosis.
- Saved HAProxy configurations require one valid bearer Authorization header, return 401 for missing/invalid authentication, have no `/ready` exemption and do not rewrite paths/methods. These saved files do not prove the active container mount or current publication.
- The local serving overlay identifies its build provenance but does not include the deployed HTTP entrypoint. Its image tag is a serving-image release identifier, not verified SGLang package SemVer.

**Actual running SGLang package version, image ID, route inventory, active gateway mount and accepted credentials: NOT VERIFIED / BLOCKED.** Docker inspection was denied. The user's current Loaded/active/running/resident observation and `/ready` 404 remain supplied evidence, not independently reproduced results from this pass.

The adapter's contract matrix is deliberately conservative:

| Interface/signal | Meaning | Authentication/safety | Current deployment evidence |
| --- | --- | --- | --- |
| `systemctl is-active` | Service process signal | Fixed read-only command | Command denied here; active reported by user |
| Docker running state | Container process signal | Fixed limited inspect | Socket denied here; running reported by user |
| `/get_model_info` | Model identity/configuration, combined with process evidence for the adapter's Loaded state | Authenticated metadata GET; no inference | Previous 401 correction and current identity success reported; safe fixture contracts pass |
| `/ready` | Request-acceptance readiness only if the deployed route supports that contract | Identity-gated authenticated GET; 200/503 handling; no generating fallback | 404 reported by user; preserve Unverified |
| `/health`, `/health_generate` | Version-dependent health; can generate a token | Never called by this application or this audit | Deployed implementation not audited; inference not authorized |
| `/server_info` and aliases | Potentially sensitive configuration/scheduler information | Excluded from monitoring | Not requested |

The [official SGLang HTTP implementation](https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/entrypoints/http_server.py) was reviewed for contract guidance: model-info is distinct from the health-generation handler. Upstream source is not evidence of the installed version. No supported non-generating substitute for the user's missing readiness endpoint has been established for this deployment. An unsupported endpoint is an operational limitation, not permission to upgrade/configure the runtime or claim Ready.

401/403, timeout, unsupported route, unavailable transport and other HTTP errors have separate probe outcomes. They do not independently prove a failed model runtime. A matching endpoint's `/ready` 503 supplies an explicit negative readiness signal; only matching identity, agreeing active processes and a successful supported readiness probe can report Ready. Last historical success never replaces current evidence.

Monitoring makes at most two GETs per observation with two-second I/O timeouts, no immediate retry and a shared ten-second inventory cache. Lifecycle verification performs one observation per iteration, fails fast on permanent contract failures and caps sleeps by two seconds/remaining deadline. Individual I/O calls may extend beyond the nominal overall verification deadline; a slow streaming response or hung filesystem is not covered by a hard end-to-end deadline.

## Ollama and model intelligence

The [official installed-model contract](https://docs.ollama.com/api/tags), [resident-model contract](https://docs.ollama.com/api/ps) and [official model-information reference](https://github.com/ollama/ollama/blob/main/docs/api.md) were checked. Installed metadata, resident allocation and show metadata remain separate; runtime residency alone is not an inference probe.

Live `/api/version`, `/api/tags` and `/api/ps` failed because socket access is denied, so no actual installed-model list or per-model metadata is claimed. The local CLI reported 0.30.8; that is not verification of the running server version.

Automated fixtures verify installed-vs-loaded separation, independent failures, orphan residents, conflicting digests, incomplete metadata, maximum-vs-active context, show/failure caching, allocation-vs-stored size and identity checks. Every technical metadata value retains `{value, source, confidence}`. Verified runtime/configuration labels, inferred identifiers, estimated requirements and unavailable values remain explicit.

For SGLang, the configured name/identifier is configuration evidence; 27B and NVFP4 remain inferred unless independently reported. Architecture, effective context, measured allocation and filesystem storage location are not invented. A configured Hugging Face identifier is not a verified weights directory. Ollama storage paths remain unavailable rather than exposing generated Modelfiles or assuming blob locations.

## Switching, recovery and operation safety

Reviewed and exercised production preflight/API/worker/recovery paths with mocked adapters. Tests cover insufficient and unknown memory, exact stop selections, explicit confirmation and risk acknowledgement, 120-second expiring single-use plans, delayed worker expiry, changed fingerprints, concurrent confirmations, worker startup failure and advisory-lock contention in temporary state.

Selected stops and target state/identity are checked before commands. Memory is sampled before target and recovery loads. Failures cover unload, load, readiness, partial target, failed restoration and final recovery verification. Recovery acts only on authorized selected stops, avoids restoring under uncertain/partial target pressure, verifies the previous selected state and never automatically removes the target. Logs are bounded per record and activity read; malformed records are tolerated. Log growth/rotation and crash-resumable operations remain limitations.

No live load/unload/switch was performed. The tested contracts do not prove external clients are idle, that the runtime cannot evict models, or that an actual recovery will succeed on this hardware.

## Automated commands and results

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | PASS: 85 tests; no skips |
| `node tests/test_frontend.js` | PASS: navigation, storage, charts, gauges and telemetry regressions |
| `node tests/test_model_manager.js` | PASS: prototype isolation, selection, failure and operation guards |
| `node tests/test_model_intelligence.js` | PASS: evidence/state/details/cache precedence, confirmation races and focus guards |
| `python3 -m py_compile tests/browser_server.py` | PASS: syntax only |
| `node --check web/app.js` | PASS: syntax only |
| `node --check tests/browser_e2e.mjs` | PASS: syntax only |
| `bash -n install.sh` | PASS: syntax only; installer not executed |
| `git diff --check` | PASS |
| `node tests/browser_e2e.mjs` | BLOCKED, exit 2: Playwright not installed; no browser assertions ran |
| `AI_MANAGER_PORT=0 python3 server.py` | BLOCKED: socket creation denied; development app could not start |
| `python3 tests/browser_server.py` | BLOCKED: fixture socket creation denied |
| Isolated Firefox headless, temporary profile, local explicit demo page | BLOCKED: snap-confine capability failure; no screenshot |
| Impeccable detector over changed UI | Degraded regex check returned `[]`; parser/computed-contrast checks unavailable |

The new `tests/test_validation.py` contains 22 regressions. Existing SGLang 401/403/unavailable/timeout/unsupported/authenticated fixtures and mocked switching/recovery suites remain enabled. No live adapter is used for failure injection. Advisory-lock/log tests write only to temporary directories.

## Actual ASUS GX10 evidence

| Observation | Result and evidence boundary |
| --- | --- |
| Host/architecture | Verified locally: `gx10-cbc7`, `aarch64` |
| Toolchain | Verified: Python 3.12.3; Node 22.23.1 |
| System memory | `/proc/meminfo`: 130,593,968,128 total bytes; sampled available 57,056,841,728 bytes. This transient sample is not model capacity calibration |
| NAS mounts | `/mnt/nas/AI-Models` and `/mnt/nas/Storage` verified mounted |
| External NVMe | `/mnt/ai-models` exists but is not a mount; corrected application behavior reports offline |
| NAS library scan | Read-only bounded scan completed: 16 recognized assets, four collections, all Requires additional configuration and non-runnable. No weight contents read |
| GPU query | Supported query attempted; application reports unavailable on this driver. No valid utilization/temperature reading obtained |
| systemd/Docker | Read-only commands attempted; bus/socket access denied. Current live process states unverified here |
| Ollama/gateway HTTP | Socket operations denied. Actual model inventory, metadata, readiness and credential acceptance unverified |

These are direct local observations, not browser evidence. They do not independently verify the full advertised hardware configuration, CUDA execution, model inference or NAS throughput.

## Browser and UI evidence

No current-revision rendered browser acceptance passed. The Chrome connector reports an existing profile conflict; it was not stopped or modified. The alternate computer-use inventory exposes no browser. An independent Firefox launch with an isolated temporary profile failed its snap capability check. No screenshot exists from these attempts.

Implemented `tests/browser_e2e.mjs` and `tests/browser_server.py` for future non-disruptive execution. They use an isolated random loopback port, synthetic token, temporary state and guards against every live runtime/NAS adapter. Browser interactions use the application's explicit demo mode; the offline case intercepts all API calls. The runner downloads nothing and produces PASS evidence only after assertions complete.

The implemented cases cover all seven sections, light/dark themes, 1440/390/320 widths, DPR 2, reduced-motion emulation, gauges, timeline keyboard/tap selection and backing-size stability, storage progress, search/filter/empty states, details/provenance, modal Cancel/Escape/Tab/focus behavior, explicit stops and risk acknowledgement, simulated switch/failure, Activity and offline action protection. Document/session/Origin rejection uses the isolated real HTTP fixture. This suite is syntax-checked but **not execution-validated in this environment**. It does not replace the Python production-API integration tests or a live read-only dashboard check.

When runnable, screenshots and `results.json` are written to `/tmp/asus-ai-browser-evidence` or `AI_MANAGER_E2E_ARTIFACTS`. No browser artifacts were generated in this pass. Rendered contrast, actual 200% zoom/reflow, full assistive technology and real touch behavior remain manual acceptance gates. Earlier user Firefox observations are historical evidence only.

## Security assessment

Verified by source and automated regressions: loopback binding is preserved; every API still requires a session token; exact Host/Origin and Fetch Metadata rejection occurs before body parsing/discovery; inputs/stop selections are bounded; static routes do not expose arbitrary repository files; document CSP, no-store and no-referrer protections remain; runtime origins reject remote destinations, credentials, paths/queries and redirects/proxies; subprocesses use fixed argument vectors without shell interpolation.

Runtime credentials stay in bounded in-memory reads and are excluded from health payloads, upstream error bodies and logs. Existing credential-file mode was inspected without printing contents. The browser fixture's token is synthetic and never valid in a live process. No new administrative permission, sudo rule, Docker membership, gateway route, network exposure or authentication bypass was introduced.

Real HTTP transport and active gateway security remain BLOCKED, not certified. Remaining risks include launch tokens in local URLs/history, hostile local users/processes, external scheduler/client races, absent reliable client detection, uncalibrated per-model memory, non-durable operations, unrotated logs and potentially blocking NAS filesystem calls. This is a source/mocked audit, not an independent penetration test.

## Files modified

| Files | Purpose |
| --- | --- |
| `core.py` | Independent inventory, installation/identity handling and bounded verification behavior |
| `intelligence.py` | Optional metadata validation, resident identity fingerprint, reserve and honest reclamation estimates |
| `server.py` | Host/Origin/session/input guards, worker expiry, sampling lock and mount-aware storage |
| `web/app.js`, `web/index.html` | Fresh residency metadata, registration/readiness copy, decimal telemetry and persistent Activity errors |
| `tests/test_validation.py` | New audit/security/concurrency/lifecycle regressions |
| `tests/test_frontend.js`, `tests/test_model_intelligence.js` | Decimal telemetry, cache precedence, registration and SGLang 401/404 UI regressions |
| `tests/test_stability.py`, `tests/test_intelligence.py` | Updated request/clock fixtures preserving intended checks |
| `tests/browser_e2e.mjs`, `tests/browser_server.py` | New guarded real-browser fixture harness |
| `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `CHANGELOG.md`, `TESTING.md`, `SECURITY.md` | Current behavior, safety contracts, exact evidence and open gates |
| `docs/audits/INTEGRATION_VALIDATION_REPORT.md` | This audit and explicit acceptance classification |

## Acceptance criteria and remaining work

| Release criterion | Assessment |
| --- | --- |
| All required automated tests pass | Socket-free suites PASS; required browser E2E remains BLOCKED |
| Accurate SGLang state reporting | PASS in fixtures, including active/resident plus unsupported readiness; live state/version/routes BLOCKED. Inference readiness UNVERIFIED |
| Accurate Ollama state reporting | PASS in independent-failure/metadata/identity fixtures; live server inventory BLOCKED |
| Authentication/security preserved | PASS by source/in-memory regressions and local credential modes; active gateway/real HTTP validation BLOCKED |
| Metadata provenance correct | PASS in fixtures; actual runtime fields NOT VERIFIED |
| Model Manager operational states accurate | PASS in VM/DOM fixtures; rendered/live acceptance BLOCKED |
| Existing controls functional under tested contracts | PASS in mocked API/preflight/worker/recovery tests; live operations NOT PERFORMED and separately approval-gated |
| Browser acceptance passes | BLOCKED; no screenshots or executed browser assertions |
| No confirmed critical defects remain | No known unresolved critical defect in the tested scope; full release sign-off withheld for missing evidence |
| Documentation reflects actual behavior | Updated with explicit verified/blocked/unverified boundaries |

To close the remaining non-disruptive scope, run the guarded browser suite with existing compatible tooling and permitted loopback sockets; start the checkout's development app separately from stable v5; validate the read-only dashboard against actual SGLang/Ollama responses; inspect the deployed package/routes and active gateway contract with permitted read-only Docker/systemd access; and complete manual theme/reflow/accessibility checks. Keep readiness Unverified if the runtime has no supported non-generating endpoint. Do not change infrastructure, add privileges or invoke inference to manufacture a pass.

Any later live load/unload/switch/recovery or inference exercise requires separate explicit approval. Missing evidence prevents READY or READY_WITH_LIMITATIONS under the requested acceptance gates, even though the implementation and socket-free regressions are complete for this pass.

## Git status and delivery

Branch remains `dev/premium-control-center`; HEAD remains `9534fc083e91cf54ba20c6e426389b80532b8199`. Changes are retained in the working tree, including this report and the new tests. No commit was created because `.git` is read-only under the session filesystem policy. No existing commit/history was removed, no force operation was used and nothing was pushed.
