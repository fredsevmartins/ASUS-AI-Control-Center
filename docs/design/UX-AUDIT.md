# UX audit and prioritized improvements

Scope: working tree on `dev/premium-control-center`, 3 November 2026. Source inspection of all frontend surfaces, API schema, existing regression tests and architecture notes. No screenshots were present. This is a source-based heuristic audit; neither a usability study nor a rendered accessibility certification. Existing uncommitted gauge and timeline work is retained.

| Priority | Finding and user consequence | Evidence | Response |
| --- | --- | --- | --- |
| P0 | Lost telemetry leaves actionable model cards showing old state | update() previously cleared gauges only | Disable actions on connection failure and mark telemetry stale; recheck before confirmation |
| P0 | Switch can interrupt clients; runtime state is not inference readiness | process checks in core.py; no client-count/readiness API | Explicit unchecked stop selection, uncertainty guards, readiness disclaimer, recovery warning |
| P1 | Dialog has no accessible role, focus placement, Escape or focus containment | original modal markup and handlers | Labeled dialog, inert background, initial Cancel focus, Tab loop, Escape and focus return |
| P1 | Busy/failure feedback depends on temporary toast and header | renderStatus / operation object | Persistent operation panel, indeterminate progress, recovery instructions |
| P1 | Small dense model cards flatten name, runtime, state and actions | original 14px model headings and 11px metadata | Large cards, clear process badge, runtime label, memory/readiness facts, progressive details |
| P1 | Rapid confirmation can submit twice before polling catches up | original action handler | Submission guard and disabled action buttons; server lock unchanged |
| P1 | No safe representative evaluation path | app immediately calls live endpoints | Explicit demo mode intercepts every request before fetch, persistent prototype banner |
| P2 | Settings absent from six-item navigation | index.html | Browser-local appearance and read-only connection information |
| P2 | Narrow navigation hides text; labels rely on glyph interpretation | original 720px CSS | Horizontally scrollable, named navigation at small widths; SVG desktop icons |
| P2 | Low hierarchy and inconsistent color treatment | many small 10–12px labels, purple fills/gradients, hard-coded dark overrides | Semantic theme tokens, neutral surfaces, fewer accent uses, larger metadata |
| P2 | Search only matches model name and lacks status segmentation | original renderModels | Search name/runtime; All, Loaded, Unloaded and Needs attention filters |
| P2 | Cognitive load from repeated decorative headings and nested cards | eyebrow, glass panel around cards | Remove eyebrow and surrounding Model Manager panel; prioritize task content |
| P3 | Repeated innerHTML rendering can disturb focus | five-second renderModels refresh | Preserve expanded details and action focus; broader DOM reconciliation remains follow-up |

## Workflow evaluation

Overview answers “What is happening?” through the preserved memory/GPU/CPU gauges, timeline, runtime inventory and storage. Model Manager answers “What can I safely change?” Library remains a read-only inventory of assets. Performance retains the established semicircular gauges and keyboard-inspectable timeline. Workspaces remain planning presets rather than launchers. Activity records operation metadata and recovery messages. Settings exposes appearance and explains the connection boundary without inventing runtime configuration controls.

Load/unload flow: inspect process state and available memory → review model details → select action → review impact → explicitly confirm → monitor persistent status → inspect Activity after a failure. Switch flow adds opt-in selection of individual loaded models to stop; unchecked models remain active. Confirmation cannot promise sufficient memory or absence of active clients.

## Unresolved evidence gaps

Rendered contrast, zoom/reflow, screen-reader behavior, touch behavior and desktop/mobile screenshots require a browser on the workstation. Actual readiness, model-specific memory requirements, client use, stage percentages and reliable rollback are unavailable in the current API. The prototype failure path intentionally leaves previous models unchanged; real best-effort recovery can behave differently. No claim of production-ready inference health is made.
