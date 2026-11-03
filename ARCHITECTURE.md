# Architecture and audit

The standard-library Python server binds to 127.0.0.1 on a random port and serves the static, English-language single-page interface. A random per-process token is embedded in the initial page and required by API requests. `server.py` samples telemetry on status requests, maintains a bounded in-memory history, serializes operations with a lock, and starts one worker thread per accepted operation. `core.py` discovers models, accesses runtimes, performs verification and logs operation metadata. There is no external frontend framework or build step.

Ollama uses its configured API endpoint for inventory, process state and loading, and its CLI for unloading. SGLang uses the existing `qwen38-control` script and observes the systemd service and Docker container. Both observations must agree for an actionable state. These process checks do not establish inference readiness. Docker is inspected only; no container configuration is changed. NAS scanning is read-only, skips symlinks, limits traversal to 1,800 entries and four directory levels, and groups recognized weight files as assets. Storage capacity comes from statvfs and mount checks. The installer copies files into the user's v5 directory; it was not run for this work.

Memory history is sampled on status requests, kept only in process memory and shared among browser sessions; it is not a fixed-rate hardware recorder. CPU comes from `/proc/stat`, memory from `/proc/meminfo`, and GPU metrics are best-effort `nvidia-smi` output. GB10 unified memory cannot be attributed reliably to an individual model here. Workspaces are informational presets.

## Audit findings

- SGLang process status is not inference readiness, and the Ollama process list does not prove a successful inference. A runtime-aware readiness probe is still needed.
- A failed target load can leave a partially loaded target; rollback restores selected models but does not remove that target. Recovery may fail for resource or client reasons and requires inspection; the failure message warns that the target may be partially loaded.
- Client usage and free-memory requirements are not reliably known; confirmation cannot guarantee a switch is safe. The job lock is process-local and does not prevent external runtime changes.
- Operation history is a local append-only file, read whole without rotation; malformed entries can hide the history. Runtime work is not durable across application termination.
- NAS enumeration sorts each directory before applying its entry cap, so a very large directory may still consume time and memory. Mount checks do not guarantee responsiveness.
- Status calls perform synchronous subprocess and network checks and can be slow or fail; GPU support varies by driver. `/proc/meminfo` failure currently fails status entirely.
- The token appears in the launch URL; browser history and local processes may expose it. Loopback and a token are not a boundary against a hostile local user. No LAN exposure is supported.
- Browser E2E, visual regression and real GX10 integration have not been validated in this environment.
