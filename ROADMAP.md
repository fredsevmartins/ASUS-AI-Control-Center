# Prioritized roadmap

## Completed in this pass

- Add compact Overview utilization gauges and show available memory and GPU temperature when reported.

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

The existing Performance gauges were visually validated in Firefox on the GX10. The new Overview gauges and additional telemetry labels still need browser validation across themes and viewport sizes.

## Intelligent management increment — 2026-11-03

Completed on the development branch:

- Preserve the existing Astra interface and application shell, with evidence-rich cards, inline details, health timestamps/errors and NAS structural classification.
- Add dynamic structured Ollama metadata, controlled cached enrichment, SGLang configuration/identity inspection and non-generating readiness checks.
- Separate installed evidence, residency, readiness, lifecycle intent and uncertainty; retain missing values and explicit provenance.
- Require server-issued preflight, explicit confirmation, risk acknowledgement and exact stop selection; bind plans to current runtime evidence and recheck memory before target/recovery loads.
- Serialize lifecycle workers within and across Control Center instances, retain job phase/ID across browser refresh, and verify every selected previous model before claiming recovery.
- Use structured Ollama unload, skip unsafe restoration with partial target residency, bound NAS enumeration/JSON reads and make activity parsing bounded/malformed-record tolerant.
- Pass 46 mocked Python tests, three JavaScript suites and syntax/whitespace checks; document actual implementation and limits.

Next development phase, before release:

1. Validate read-only runtime inventory, deployed SGLang endpoint support and metadata on GX10. Do not upgrade or reconfigure services to satisfy readiness probes.
2. Run rendered desktop/mobile validation in both themes, keyboard/screen-reader testing, zoom, contrast and browser E2E with mocked adapters.
3. Calibrate memory estimates for actual context, KV dtype, parallelism and SGLang reservations; keep unknowns explicit and avoid treating size as an upper bound.
4. Add a bounded durable operation journal/log rotation and a crash-interruption report, without automatically resuming mutations after restart.
5. Add workload/connected-client evidence only through supported cheap interfaces. Busy remains unavailable until verified.
6. Isolate NAS filesystem discovery in a time-bounded worker and extend configuration variants without weakening its non-executable boundary.
7. Only after separate explicit approval, validate controlled load/unload/switch/recovery in a client interruption window. No such live approval was provided for this development pass.

Release assessment: implementation and mocked regression are ready for review; hardware integration and browser acceptance remain gates. The installed v5 application has not been overwritten and live runtimes/storage were not changed.
