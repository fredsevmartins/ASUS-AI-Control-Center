# Implementation roadmap, acceptance and Codex handoff

## Architectural decision

Retain the dependency-free HTML/CSS/JavaScript frontend for this iteration. Seven small views and an existing authenticated API do not justify a framework migration for appearance. The shared tokens, semantic HTML and render helpers support the requested redesign without changing deployment, CSP or runtime adapters.

The principal maintenance problem is compressed source and mixed rendering/state/network responsibilities. Next, format the original source and extract the API client, prototype fixtures, modal controller, model card rendering and telemetry utilities into small local modules. Keep that change separate from behavioral changes; the server currently allowlists only app.js and style.css, so splitting browser assets needs deliberate static routing tests. Prefer DOM updates keyed by model ID over replacing all cards every five seconds.

A framework would add build tooling, dependency updates, artifact packaging, asset routing/CSP validation and migration of canvas lifecycles and focus behavior. It may become worthwhile with substantially richer workspace editing, routing or complex concurrent operation views. It is not a visual prerequisite. Approximate planning estimates for one engineer, excluding hardware integration: 2–4 days for modularization and browser tests; 1–2 weeks for production design hardening; 2–4 weeks for a framework migration with parity tests. These are scope estimates, not commitments.

## Prototype and review

Open `web/index.html?demo=1` in a browser via a loopback-only static server rooted in `web`, for example `python3 -m http.server 8765 --bind 127.0.0.1 --directory web`, then visit `http://127.0.0.1:8765/?demo=1`. This serves static files only, with no runtime API. A direct file URL may work subject to browser local-storage policy. Do not run install.sh to preview.

Within an authenticated running app, Settings → Open interactive prototype preserves the launch query parameters and adds demo=1. Demo mode intercepts status, library, activity and action requests before fetch. Unknown requests fail closed. Do not remove demo=1 while evaluating operations against a real app.

Representative fixtures: loaded SGLang model, unloaded Ollama model, loaded embedding model and an uncertain example. These are not assertions about installed models. Use search/filters, details, theme switching and all seven views. Switch with one checked stop target; verify another loaded model remains active. Toggle “Simulate next load failure,” then confirm a load/switch and inspect persistent feedback and Activity. Simulated progress completes after approximately 2.4 seconds. No model inference is executed. History charts show a fixed representative session; changing loaded state does not synthesize model memory or readiness.

## Roadmap

1. Current iteration: audit, shared theme system, seven-surface styling, Settings, Model Manager interactions, isolated prototype and safety regression checks.
2. Browser verification: desktop 1440px and narrow 390px/320px in both themes; 200% zoom, keyboard-only and reduced motion; capture Overview, Model Manager, switch dialog, failure and Performance. Resolve overflow, contrast and focus issues before deployment.
3. Maintainability: format/extract modules, keyed updates, consolidate superseded legacy CSS, introduce browser fixture testing with all runtime endpoints mocked. Preserve telemetry tests.
4. Backend capability proposals, separately scoped: readiness checks with defined semantics, model capacity estimates with provenance, client visibility, operation stage events and durable recovery. No UI should claim these exist until the API supports them.
5. Controlled target-workstation validation only with explicit approval for each live operational exercise; check active clients first. No installation, service reconfiguration or direct push to main is included.

## Acceptance criteria

- All seven named English-language views work; no external assets or network dependencies are required.
- Semicircular gauges, valid/unavailable behavior and timeline keyboard interactions remain functional.
- Model cards distinguish process state, readiness and runtime memory; system memory is not presented as per-model allocation.
- Search matches model/runtime; filters, expanded details and empty states work.
- Connection failure, uncertain state, in-flight submission and busy operation block model actions.
- Every load/unload/switch requires explicit confirmation. Stop selection is opt-in and does not include unchecked models.
- Dialog supports keyboard entry, Cancel focus, Tab wrapping, Escape, inert background and focus restoration.
- Busy, failure and recovery guidance remain visible beyond a toast. No fabricated readiness or percentage.
- Prototype sends zero network requests, labels its data, simulates selection/failure and does not access NAS.
- API token handling, loopback binding, server serialization, v5 paths and runtime configuration remain unchanged.
- Automated suites in TESTING.md pass. Browser accessibility and screenshot evidence are required before visual acceptance; currently pending.

## Instructions for the next Codex session

Read AGENTS.md, PRODUCT.md, DESIGN.md, this file and TESTING.md. Stay on dev/premium-control-center. Inspect git diff first: uncommitted changes to CHANGELOG.md, ROADMAP.md, TESTING.md, tests/test_frontend.js and all three web files existed before this redesign. Do not revert them or broadly stage unrelated files. Preserve current gauges and telemetry work.

Review the prototype using mocked/static serving only. Never call /api/action against the live workstation for verification. Do not change core.py, server.py, installation, model files or runtime/service/NAS settings without a separately authorized task. Run the prescribed tests and record exact limitations. Prioritize browser verification and incremental DOM reconciliation before adding features or a framework.

## Review evidence

Independent static review scored the six reported fixes resolved: polling summary focus, dialog focus return, LIVE badge contrast, first connection failure feedback, reported glyph icons and initial Overview copy. The badge token pairs calculate to 4.93:1 in light mode and 6.67:1 in dark mode. This is a targeted source review, not whole-interface visual approval. Documentation discrepancies were reconciled and narrow dark-mode card padding aligned with light mode.


## Desktop UI follow-up — 2026-11-03

The existing neutral visual system is retained and refined in place. Review the
updated DESIGN.md and [desktop-window investigation](DESKTOP-EXPERIENCE.md).
The two-column model layout now lasts until 1760px, avoiding cramped intermediate
three-column cards. Shared controls, sticky chrome, mobile target sizes, metadata
spacing, workspace footers and long-content handling are refined. Appearance
controls and Library selection announce their state. Backend and launch files
are unchanged; no dependencies were added.

The current tree started clean on dev/premium-control-center. All 101 Python
cases and three JavaScript suites pass. Browser acceptance is BLOCKED by missing
Playwright, denied loopback sockets and absent computer-use surfaces. No visual
sign-off or READY classification is claimed. Detector findings remain advisory
maintenance debt in the layered stylesheet and design-document ramps; avoid
assuming its regex fallback resolves the cascade. Test on the guarded fixture
before deployment, with manual zoom, Firefox and assistive-technology checks.
