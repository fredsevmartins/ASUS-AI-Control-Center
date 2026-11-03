# Changelog

## Unreleased

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
