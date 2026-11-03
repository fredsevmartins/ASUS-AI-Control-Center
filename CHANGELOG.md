# Changelog

## Unreleased — SGLang authentication diagnosis (2026-11-03)

- Trace the reported 401 to the unauthenticated `/get_model_info` request against the loopback private gateway; account for the service's security drop-in instead of treating the base-unit port as a direct runtime interface.
- Discover the existing gateway's published loopback bindings read-only. Use the existing compatibility bearer file in memory, with application-only `SGLANG_URL` and `SGLANG_API_KEY_FILE` overrides; preserve authentication, proxy/redirect restrictions and runtime infrastructure.
- Keep 401/403, transport failures, timeouts and unsupported readiness separate from explicit `/ready` rejection. Report Unverified when readiness is unknown; preserve independent systemd/container process evidence and conservative lifecycle guards.
- Add 17 Python regressions (63 total) and frontend process/authentication evidence coverage. Full automated suites pass; live endpoint/version/credential support and browser rendering remain unverified due to sandbox access restrictions.

## Unreleased — Intelligent model management (2026-11-03)

- Add provenance-aware runtime metadata, dynamic Ollama inventory/enrichment, SGLang configuration/identity inspection and non-generating readiness observations.
- Add explicit model states, independent health evidence and last successful check; preserve unknown/unverified inference readiness.
- Add expiring single-use preflight plans, memory/KV allowances, explicit risk confirmation, identity/state revalidation and exact authorized stop lists.
- Prevent lifecycle overlap across browser sessions and Control Center instances; expose operation IDs/phases and verify selected recovery state without automatic partial-target cleanup.
- Enhance Astra Model Manager cards, details and confirmation with evidence, resource uncertainty and persistent errors; preserve design tokens, charts, navigation and isolated demo behavior.
- Classify NAS structure/config/tokenizer/index assets without executable registration; bound enumeration and JSON reads. Use structured Ollama unload and empty embedding preload.
- Add 32 Python regressions (46 total), a frontend intelligence/confirmation suite, expanded prototype tests and complete architecture/security/testing documentation.
- Keep v5 installation, live services, model files, NAS paths and automations unchanged. Browser/hardware release validation remains outstanding.


## Unreleased

- Add compact Overview GPU and CPU gauges and show measured GPU temperature and available memory on the gauges.

- Add telemetry-driven semicircular memory, GPU and CPU gauges with unavailable states and reduced-motion support.

- Use a fixed 0–128 GiB memory scale in both charts, with 16 GiB ticks, local 24-hour timestamps, and sample tooltips.

- Render storage utilization using native progress values compatible with the existing content security policy; reject invalid capacity readings.
- Add GiB and time axes, sample inspection, keyboard access, and empty states to memory charts.

- Keep memory chart height stable across repeated redraws on high-density displays.
- Clarify that process state does not establish inference readiness and that workspace presets are informational.

- Reject malformed operation payloads before starting a worker, and recover if a worker cannot start.
- Explicitly warn when a failed switch may have left the target partially loaded.

- Redraw the memory timeline when its page becomes visible.
- Block SGLang operations if service or container state cannot be observed or they disagree; report degraded runtime checks.
- Exclude Linux guest counters already included in CPU user time.
- Add mocked state, rollback and API regression coverage and a frontend navigation regression check.
- Document architecture, safety constraints, test coverage and prioritized work.
