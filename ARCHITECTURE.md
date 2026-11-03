# Architecture and audit

## Baseline — 2026-11-03

Work began on `dev/premium-control-center` at `b980f88`, with a clean working tree. AGENTS.md, PRODUCT.md, DESIGN.md, ROADMAP.md and TESTING.md were reviewed before editing. Baseline: 14 Python tests, both existing JavaScript suites and JavaScript syntax checks passed. The existing dependency-free Python/HTML/CSS/JavaScript architecture and Astra Model Manager design were retained.

The original status tuple, telemetry/history fields, navigation, charts, gauges, storage views, runtime controller and demo routing remain. Model rows now add evidence, health and explicit state fields. Ollama keys are namespaced as `ollama:<runtime model name>` to avoid collisions with the registered `sglang` controller; callers must use the key returned by inventory, not construct one.

The existing local unit was read, never executed or modified. Its base configuration registers model identifier `RadixArk/Qwen3.8-27B-NVFP4`, served name `qwen3.8-27b`, and static memory fraction 0.50. Its original host-network launch on port 30000 is overridden by `qwen38-sglang.service.d/security-gateway.conf`, which starts the existing private-network/gateway containers and attaches to the existing SGLang container. Base-unit flags describe registered configuration, not proven effective container settings, runtime availability, measured memory or model installation. Live API responses and actual installed Ollama models could not be verified in this sandbox.

## Components and contracts

- `server.py`: loopback HTTP server, session token, telemetry/history, authenticated detail/preflight APIs, expiring plans, process-local operation state and worker scheduling.
- `core.py`: existing runtime controllers, read-only runtime discovery, health observations, bounded NAS enumeration, lifecycle verification and compensating recovery.
- `intelligence.py`: provenance records, metadata normalization, bounded cache, state/intent projection, fingerprints, memory estimates, preflight and structural asset classification. Standard library only.
- `web/app.js` / `web/style.css`: existing application shell and charts, enhanced evidence cards/details, protected switch confirmation and phase feedback. No framework or build step.

| Interface | Behavior |
| --- | --- |
| `GET /api/status` | Existing telemetry plus enriched models and operation ID, phase, timestamps and recovery result when present |
| `GET /api/model?key=…` | Registered model evidence, allowlisted runtime configuration, requirement estimate and up to eight recent operations |
| `GET /api/library` | Read-only asset/configuration/tokenizer/index files and classified collections; never returns an executable NAS adapter |
| `GET /api/activity` | Latest 65 valid records from a bounded 128 KiB log tail; corrupt records skipped |
| `POST /api/preflight` | `{action, target, stops}`; read-only plan, warnings, estimates, blocked reasons, fingerprint, ID and expiry |
| `POST /api/action` | Same selection plus `plan_id`, `confirmed: true`, `acknowledge_risks: true`; consumes exactly that plan and returns 202, or rejects stale/blocked/overlapping requests |

All API routes require the existing session token. Plans last 120 seconds, are single use, and are limited to 64 in memory. A worker recomputes preflight under a Linux advisory lifecycle lock before any mutation. The fingerprint binds runtime identities, residency, state, configuration, active allocations/context and target sizing evidence. Background enrichment of unrelated descriptive fields does not invalidate a plan. The process-local busy flag rejects overlap before scheduling; `flock` on the existing user state directory coordinates workers from separate copies of this application. External clients do not honor these locks.

Refreshing a browser does not cancel a worker or clear its ID/phase. Terminating the server does: there is no crash-resumable operation journal, and restarting requires a fresh observation and confirmation. The installer was updated to package `intelligence.py`; it was not run.

## Runtime metadata and health

Ollama uses supported structured APIs: `/api/tags` for installation evidence and stored size, `/api/ps` for residency, reported runtime allocation and active context, and `/api/show` for technical metadata, capabilities and maximum context. Inventory/health observations are cached for ten seconds across browser sessions. One uncached `/api/show` lookup is allowed per inventory refresh; cached fields accumulate automatically, and opening Details or preflighting a target requests its metadata immediately. Show responses and failures are cached for five minutes, bounded to 128 entries. Missing process information retains installed rows as Unknown, and resident models absent from tags remain visible as potential conflicts. Their reported allocation is never reused as stored weight size.

SGLang reads allowlisted flags from `/etc/systemd/system/qwen38-sglang.service` and up to 16 sorted `.conf` drop-ins (up to 64 KiB each). It respects `ExecStart` replacement when choosing an interface; this is a narrow adapter for the installed unit, not a general systemd interpreter. For the recognized private gateway drop-in, it inspects only `qwen38-private-network`'s published `30002/tcp` bindings and accepts literal loopback host bindings. It never dials the namespace-only backend or guesses its mapping from the base unit. If publication cannot be inspected, endpoint discovery remains unknown. An explicit HTTP loopback `SGLANG_URL` takes precedence; the original host-network port inference applies only when the effective launch still specifies host networking. Other unit search paths, runtime/transient drop-ins and arbitrary launch wrappers are not resolved.

For this recognized gateway setup, the adapter reads the existing compatibility credential at `~/.config/qwen38/api-key` in memory only. `SGLANG_API_KEY_FILE` can point the application to another existing bearer file, including for an explicitly configured origin. The application never writes credentials, scrapes secrets from service commands, returns the credential path/value, or logs headers. Reads are limited to 4 KiB and regular files; missing, unreadable or invalid configured credentials fail closed before HTTP. The key is sent as an Authorization bearer header only to the validated loopback origin. There is no unauthenticated retry or alternate backend fallback.

Monitoring performs at most two GETs per observation: `/get_model_info`, then `/ready` only after model identity matches the registered configuration. Each probe records its path, outcome and HTTP status. Authentication required (401), access denied (403), unavailable transport, timeout, unsupported endpoint (404/405/501), malformed responses and other HTTP failures are distinct outcomes. They leave inference readiness unverified. A matching endpoint's `/ready` 503 is an explicit negative readiness signal; 200 establishes readiness only alongside agreeing active process observations. Authentication failures do not prove that the model runtime is unavailable. A gateway response alone does not prove backend availability.

Service and container observations remain independent of HTTP and of one another. Health exposes systemd `service_status`, Docker `container_status` and their tri-state `process_running` consensus; cards show both process signals even when metadata authentication fails. The existing `sglang_state()` lifecycle contract still requires agreement. Missing identity keeps model state Unknown and blocks mutation; matching identity with unsupported or inaccessible readiness remains Loaded with unverified readiness. `/health` and `/health_generate` are deliberately unused because behavior varies by version and `/health` can generate a token. `/server_info` is not polled: it can expose sensitive configuration and involve scheduler work. Full runtime configuration, secrets and environment variables are never returned.

### GX10 authentication regression diagnosis — 2026-11-03

The previous adapter derived `http://127.0.0.1:30000` from the base unit, ignoring its security drop-in, and sent an unauthenticated `GET /get_model_info`. Therefore the reported 401 originates from `http://127.0.0.1:30000/get_model_info`; the old code exits before requesting `/ready` when that first request fails. This identifies the request from source/configuration, not a successful live reproduction in this sandbox.

Read-only inspection found the installed drop-in starts `qwen38-private-network` and `qwen38-gateway` before attaching to `qwen38-sglang`. Saved HAProxy configuration in `~/qwen38-ondemand/haproxy-original.cfg` and the local security deployment workspace requires exactly one valid bearer Authorization header and denies missing/invalid authentication with 401 before forwarding. It has no unauthenticated readiness exemption. Saved deployment arguments publish the gateway on host loopback, including port 30000; that port is a gateway interface rather than evidence of direct SGLang access. The old URL can therefore reach the intended gateway while using the wrong authentication contract. The fix discovers current bindings rather than depending on those saved arguments.

The regression combined missing authentication, stale interface assumptions and a presentation error: missing loaded/ready evidence fell through to “Not ready.” It now reports Unknown/Unverified when identity/readiness cannot be established and retains independent process evidence. Saved configuration and deployment evidence do not establish the current running gateway mount, backend SGLang version, credential validity or `/ready` support. systemd bus, Docker socket and loopback HTTP access were denied in this sandbox. No runtime configuration was changed and no credential contents were printed or copied during investigation.

Read-only HTTP calls and service/container observations use two-second I/O/command timeouts. JSON responses are limited to 2 MiB; redirects, environment proxies, non-HTTP schemes, DNS destinations other than normalized localhost and non-loopback addresses are rejected. A cache failure does not fail independent memory telemetry. Readiness retries occur only within a lifecycle verification deadline, with two-second intervals. A verification iteration can extend beyond the nominal deadline by its bounded individual calls; these are I/O timeouts, not a hard end-to-end wall-clock guarantee.

Official interface references: [Ollama running models](https://docs.ollama.com/api/ps), [Ollama model details](https://docs.ollama.com/api-reference/show-model-details), [Ollama API reference](https://github.com/ollama/ollama/blob/main/docs/api.md), [SGLang native APIs](https://docs.sglang.io/docs/basic_usage/native_api), [SGLang endpoint implementation](https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/entrypoints/http_server.py). Deployed versions may differ; missing endpoints remain explicitly unverified rather than triggering a runtime upgrade.

Every technical metadata value is `{value, source, confidence}`. Confidence is Verified from runtime, Verified from configuration, Inferred from filename, Estimated or Unavailable. NVFP4 and parameter count inferred from a configured model identifier remain inferred. An HF identifier is not a verified filesystem path. Ollama blob paths, SGLang measured memory and unsupported fields remain unavailable.

## Readiness state machine

`intelligence.STATES`, `TRANSITIONS` and `model_state()` define the state vocabulary and permitted lifecycle intent overlays. Stable observations may change directly when external clients act; observations do not replay invented lifecycle events.

| State | Evidence / behavior |
| --- | --- |
| Installed | Installation evidence is tracked independently by `installed`; a tags entry does not imply residency |
| Unloaded | Ollama process list excludes the model, or agreeing SGLang process observations are inactive without a responding model endpoint |
| Starting | This application's active load phase, projected over a compatible observed state |
| Loaded | Ollama resident in `/api/ps`, or SGLang active with matching endpoint identity; inference execution not established |
| Ready | SGLang matching identity and successful non-generating `/ready`, with agreeing active process observations |
| Busy | Reserved for verified workload evidence; these adapters cannot reliably detect connected clients and do not fabricate Busy |
| Stopping | This application's active unload phase |
| Error | Explicit `/ready` 503 with matching identity and agreeing active processes; a verifiably resident model can still be unloaded |
| Unknown | Missing/malformed observations or disagreeing process/endpoint identities; mutations blocked |

Health records distinguish runtime availability (including unknown), process signals, loaded state, endpoint health, observation time, last successful check, per-endpoint outcomes and failure reason. Last success survives failures in process memory but never substitutes for current readiness. Unknown readiness is “Unverified” or “Resident; inference not verified,” never “Not ready.” Ollama reports Loaded, never Ready on process-list evidence alone. A successful explicit Ollama preload plus residency verifies loading, not a real inference. Unsupported SGLang `/ready` leaves Loaded with unverified readiness; SGLang load verification fails conservatively instead of claiming Ready. No inference prompts are used for monitoring.

## Memory planning and switching

Measured system memory comes from `/proc/meminfo`; runtime-reported model allocations, stored sizes, estimated requirements and unknowns remain separate. GB10 unified memory cannot be reliably attributed to individual models here. A runtime allocation is an uncertain reclaim estimate, not guaranteed free memory.

Target planning allowance: `1.5 × stored model size + max(4 GiB, 2 × KV estimate)`. When active context, layers, KV heads and head dimension are available, single-context FP16 KV is `2 × layers × KV heads × head dimension × context × 2 bytes`. Without that geometry/context, the extra allowance is `max(4 GiB, 0.5 × stored size)`. Keep a further system reserve of `max(4 GiB, 5% of physical memory)`. This is an intentionally conservative heuristic, not a calibrated upper bound; parallelism, multimodal buffers, MoE, runtime reservations and large unseen context settings can exceed it. No default active context is invented.

Projected memory adds only reported allocations of explicitly selected stops, capped at physical memory. Incomplete runtime inventory, missing system memory or insufficient estimated capacity blocks loading. Unknown target requirements require visible risk acknowledgement and may still fail; they are not represented as zero. Memory is sampled again immediately before loading and before each recovery load. NAS sizes are never load candidates.

Workflow: `PRECHECK → CONFIRMATION → UNLOAD → LOAD → READINESS → COMPLETE`. Confirmation is an independently stored read-only plan; the worker starts at a fresh PRECHECK. Only switch uses selected stops. Unload uses the supported Ollama empty generate request with `keep_alive: 0`; embedding preload uses an empty input array, not a health prompt. The existing SGLang controller remains the sole lifecycle adapter. No percentages are invented.

Failure: `FAILURE → RECOVERY → VERIFICATION → FAILED`. Recovery considers only authorized selected stops, including a stop that changed state before returning an error. If the target is present or its state cannot be established, restoration is skipped to avoid additional pressure. The target is never automatically unloaded. Otherwise selected models are restored with memory checks; every selected previous model is finally verified again, and target absence is checked. Only that verified selected state is reported as recovered. Recovery does not claim to restore unselected/external client state or guarantee uninterrupted requests. Single load/unload failure reports an error and requires inspection; it has no implicit cleanup operation.

## NAS discovery and other limits

The scanner never writes NAS files, reads weight contents or follows discovered symlinks. It bounds traversal to 1,800 examined directory entries and four levels; directory enumeration now consumes only the remaining budget instead of sorting an unbounded directory. At most 32 configuration/index JSON files, each at most 256 KiB, are read. Recognized tokenizers are inventoried by filename without reading their contents. Index references, numbered shard sets, config and tokenizer presence support structural classification: Complete model (structure only), Model components, Requires additional configuration, Unsupported assets or Unknown assets. Completeness is not tensor validation or runtime compatibility. All groups remain `runnable: false`. Compatibility hints identify their inference source. Partial scans can miss components; NAS filesystem calls can still block on a hung mount and are not a hard time-bounded worker.

CPU/memory history remains request-sampled, bounded to 180 points and lost on restart. Telemetry, GPU support, client detection and configured vs effective memory remain best effort. Operation logs still grow without rotation, though activity reads are bounded and malformed-record tolerant. The lock coordinates only this application, not Ollama's scheduler or other runtime clients. Tokens remain in launch URLs and memory. Loopback authentication is not a boundary against a hostile local user.

Release evidence is in TESTING.md. Browser rendering, real installed-model inventory, deployed endpoint support and hardware memory estimates remain unvalidated in this sandbox; no live lifecycle action or installer execution was performed.
