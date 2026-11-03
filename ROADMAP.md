# Prioritized roadmap

## Completed in this pass

- Add responsive memory, GPU and CPU gauges using observed telemetry and dynamic memory capacity.

- Show both memory charts with a fixed GiB scale, local timestamps, and sample inspection.

- Correct storage bar rendering under the existing content security policy and validate capacity values.
- Add memory chart axes and sample inspection with mouse, touch, and keyboard.

- Prevent high-density memory chart backing height from growing on repeated redraws, with a simulated canvas regression.
- Clarify process-state and informational workspace copy.

## P0 — safety and correctness

- Establish runtime-aware inference readiness without changing live configuration; distinguish process activity, API health and model readiness.
- Design safe failed-target recovery and resource-aware preflight, including unknown state, active clients and external changes. Never assume rollback succeeds.
- Bound status calls, make telemetry failure independent, protect against concurrent status sampling, and handle operation worker interruption.
- Strengthen local request security, review token exposure and restrict configurable runtime endpoints to the intended local trust boundary.

## P1 — reliable operation and observability

- Build mocked integration, API, browser E2E and visual regression suites; validate separately on GX10 with explicitly approved controlled operations.
- Provide operation stages, elapsed time, recovery outcomes and durable bounded history with rotation and malformed-record tolerance.
- Improve CPU, GPU and unified-memory telemetry and explain unavailable and unattributed values. Record model loading timings only when observed.
- Make NAS scans genuinely bounded, resilient and searchable with category and format filters. Add local and NAS capacity diagnostics.

## P2 — experience and capabilities

- Refine accessible responsive layouts, keyboard navigation, dialogs, model cards, progress feedback, chart interaction and consistent light/dark themes.
- Add configurable, persisted workspaces that remain non-executing until safe adapters and explicit action semantics are defined.
- Add compatibility analysis based on runtime-specific requirements and metadata, with explicit unknown results; file existence alone is not evidence of executability.
- Introduce supported multimodal runtime adapters only after defining readiness, resource preflight, recovery and permission boundaries. Do not modify runtime configuration.

The user confirmed that the earlier Memory Timeline renders in Firefox and that Overview and Performance display live telemetry on GX10. Browser validation of the new storage bars and chart interactions, responsive layouts, contrast, and both themes remains outstanding: this development sandbox cannot bind localhost and has no browser surface.
