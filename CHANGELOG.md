# Changelog

## Unreleased — Midnight Blue + Graphite glass redesign (2026-11-03)

- Replace pale-green/emerald identity with independently authored neutral light and midnight/graphite dark themes; consolidate five competing token layers into one theme pair and remove obsolete purple, flat utility, Performance and master-detail CSS.
- Add layered translucent materials, static reflections, illuminated edges and distinct navigation/instrument/secondary/dialog elevations. Limit blur to selected layers; retain solid, reduced-transparency, reduced-motion and forced-colors fallbacks.
- Align semicircular instruments while keeping memory largest; preserve calculations, utilization bands, unknown values and the 184px real-GiB keyboard-inspectable history, now blue.
- Put Runtime, Storage, Hardware and Quick Actions in one four-column desktop strip, two columns at medium widths and one on narrow screens. Correct four-disk fixture height from 248px to 154px without clipping; show concise GiB capacity with full utilization on hover/native progress.
- Restyle compact model cards, strengthen the read-only Details reading layer, surface existing NAS compatibility and unify workspaces, Activity and Settings. Preserve all lifecycle/authentication/backend behavior.
- Add a guarded socket-free Firefox visual runner and responsive/source regressions. Final 119 Python tests, all three JavaScript suites, syntax and whitespace checks pass. Capture 71 real Firefox Demo screenshots; retain 25 plus results; inspect, correct and revalidate four rendered defects.
- UI acceptance PARTIAL: Firefox fixture visuals validated; Chromium app and authenticated HTTP browser acceptance remain BLOCKED by environment permissions. No live model operations or infrastructure/launcher changes. See `docs/design/MIDNIGHT_VISUAL_ACCEPTANCE.md`.

## Unreleased — Public release security audit (2026-11-03)

- Reject linked, non-regular or unsafe-owner state/log files and pin state/NAS directory traversal; prevent NAS directory-swap escape and blocking FIFO metadata opens.
- Bound all operation-log fields; cap HTTP workers at 16 with 10-second socket inactivity timeouts and reliable slot release.
- Reject duplicate security headers and incomplete/recursive JSON requests; extend response security headers and CSP form restrictions.
- Add 16 isolated security regressions (101 Python tests total), expand frontend injection/demo tests and provide a redacted local repository/history scanner.
- Document verified evidence and remaining remote/host/browser gaps in the public release audit. Classification: INCOMPLETE_AUDIT; no visibility, installation, runtime or privileged configuration change.

## Unreleased — Complete integration audit (2026-11-03)

- Preserve independent Ollama installed/resident discovery across failures; keep orphan installation unknown, reject identity conflicts and tolerate malformed optional metadata.
- Revalidate model identities and worker plan expiry; enforce the system reserve for unknown-size targets and retain unknown reclamation instead of displaying zero.
- Stop SGLang verification promptly for unsupported/authentication contracts; retain Unverified readiness and bounded transient retries without generating probes.
- Add Host/Origin/Fetch Metadata guards, constant-time session comparison, transfer-encoding rejection and bounded stop identifiers.
- Serialize telemetry, mark unmounted external storage offline, parse decimal GPU readings, preserve current allocation/context over cached details and retain Activity errors with CSP-compatible empty markup.
- Add 22 integration/security/concurrency regressions (85 Python tests total) and extend frontend regressions. Add an isolated fixture browser runner; its execution is BLOCKED by missing Playwright and loopback access, not passed.
- Refresh contributor, architecture, security, testing and roadmap documentation and add `docs/audits/INTEGRATION_VALIDATION_REPORT.md`. Release classification remains PARTIAL; SGLang inference readiness remains UNVERIFIED without a supported safe endpoint.

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

## 2026-11-03 — Desktop launcher integration

- Added a user-session Chromium app-window launcher with Firefox normal-window
  fallback, bounded startup, private control socket, duplicate-owner locking,
  repeated-click coalescing, backend reuse and explicit Stop action.
- Added single-use expiring browser handoff tickets without placing reusable
  session tokens in browser arguments or persistent launcher configuration.
- Added a dedicated SVG icon and checkout-only user desktop/menu installer with
  timestamped backups; stable v5 files and the legacy installer are unchanged.
- Added mocked launcher lifecycle/security regressions and desktop documentation.
- Installation and actual graphical acceptance remain blocked by workspace write,
  loopback, Snap and browser-tooling restrictions; no claim of hidden chrome or
  release readiness. Refresh requires reopening from the icon.

## 2026-11-03 — Professional desktop frontend composition

- Replaced equal-weight overview cards with integrated memory instrumentation and
  compact secondary telemetry; tightened navigation and application chrome.
- Replaced model card grids with persistent selection and a single inspector,
  retaining evidence, details and existing protected actions.
- Added aligned registered/NAS inventory presentation and component view labeling;
  changed workspaces to disclosures, Activity to log rows and Settings to groups.
- Refined solid light/dark surfaces and responsive desktop/mobile composition.
- Extended mocked frontend and browser-fixture assertions. Rendered acceptance
  remains blocked; backend and previous desktop launcher work are unchanged.

### Premium glass UI finalization — 2026-11-03

- Added restrained rounded, layered surfaces and utilization-colored gauges with neutral unavailable states.
- Replaced the model inspector with compact responsive cards and a separate metadata details dialog. Existing lifecycle confirmations remain in place.
- Socket-free Python and JavaScript suites pass; browser and standalone validation remain blocked as documented in TESTING.md.

## Complete premium desktop presentation — 2026-11-03

- Unified environmental background, translucent navigation and rounded materials
  across all seven pages, with distinct light/dark tokens.
- Refined semicircular scale ticks without changing telemetry or utilization bands.
- Compact model cards with stronger name hierarchy, aligned facts/action footers
  and focus state; grouped metadata inspector with keyboard-scrollable evidence.
- Refined NAS records, performance panels, workspace disclosures, activity and
  grouped preferences; preserved operational and authentication contracts.
- Expanded guarded screenshot matrix; source-review cascade defects corrected.
- 117 Python tests and three JS suites pass. Visual acceptance remains BLOCKED;
  classification IMPLEMENTED_NOT_VISUALLY_VALIDATED. No screenshots fabricated.

## Desktop launch verification follow-up — 2026-11-03

- Preserve the existing Chromium app-window / Firefox fallback implementation and
  premium frontend; verify existing localized desktop/menu shortcut presence.
- Report unreachable-owner and empty control replies as shutdown errors instead
  of treating a timeout as successful shutdown.
- Add two mocked regressions: 119 Python tests and three JavaScript suites pass.
  Real desktop/browser acceptance remains BLOCKED / NOT VERIFIED; no installation
  or AI runtime changes were performed.

## Final emerald UI consolidation — 2026-11-03

- Apply emerald accents and deep-blue/black foundations to shared light/dark
  materials, controls, chart traces and status surfaces.
- Remove Performance; retain gauges, history, hardware and storage in Overview.
- Preserve compact model cards and Details; simplify Library to NAS rows with
  optional evidence and render six responsive workspace planning cards.
- Update six-page navigation and guarded browser coverage. All 119 Python tests
  and three JavaScript suites pass; real rendered acceptance remains blocked.
- Preserve backend, runtime adapters, NAS protections and desktop launcher.
