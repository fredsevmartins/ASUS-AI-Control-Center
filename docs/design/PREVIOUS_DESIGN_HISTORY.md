---
name: ASUS AI Control Center
description: A compact professional desktop utility with persistent model selection and integrated instrumentation.
colors:
  bg: '#f2f2f3'
  surface: '#fcfcfd'
  raised: '#eeeeef'
  nav: '#e8e8ea'
  line: '#d5d5d9'
  ink: '#252529'
  sub: '#626269'
  accent: '#215caa'
  selection: '#dce9f9'
  dark-bg: '#202124'
  dark-surface: '#26272b'
  dark-raised: '#2c2d32'
  dark-nav: '#242529'
  dark-line: '#42434a'
  dark-ink: '#ececf0'
  dark-sub: '#b5b6c0'
  dark-accent: '#9bc4ff'
  dark-selection: '#304463'
typography:
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Ubuntu, sans-serif'
    fontSize: '13px'
    lineHeight: 1.5
  title:
    fontSize: '24px'
    fontWeight: 650
    letterSpacing: '-.025em'
rounded:
  control-radius: '5px'
  workspace-radius: '0'
---

# Professional desktop utility

## Direction and audit

This redesign replaces the dashboard composition with an operational desktop
workspace. Previously four equally weighted metrics, repeated rounded model
cards, generous card padding and icon-led presets weakened the distinction
between monitoring, selection and action. The revised system assigns each page
a structure appropriate to its task, while preserving the backend, authentication,
model operations, metadata evidence and installed/checkout launcher work.

The design follows the navigation/content/inspector separation described in
Apple's [split-view guidance](https://developer.apple.com/design/human-interface-guidelines/split-views)
and restrained hierarchical navigation from its
[sidebar guidance](https://developer.apple.com/design/human-interface-guidelines/sidebars).
These principles inform the composition; proprietary assets and exact application
interfaces are not reproduced. The brief explicitly chooses solid neutral surfaces,
not floating glass. System fonts and authored consistent stroke icons keep the
application self-contained. No new framework, font download or image dependency.

Mode: **Operate**. The primary workflow is selecting a registered model, assessing
current evidence and deliberately requesting an existing operation. Persistent
selection, visible runtime state and precise actions take precedence over decoration.

## Composition

- **Navigation:** 202px integrated neutral sidebar (180px on smaller desktops),
  34px rows, 17px stroke icons and a pale blue selection. The device identity sits
  quietly at the bottom. A 46px toolbar carries refresh and appearance controls.
- **Overview:** a shared instrument surface leads with Unified Memory, GPU,
  CPU and Models Loaded. Memory has the widest arc (up to 360px) and a 56px
  reading; GPU/CPU arcs remain visible (up to 280px). The monitoring region
  targets roughly 70–75% of the initial dashboard emphasis at desktop sizes.
  Memory history sits below in a 184px canvas, preserving its GiB axis, local
  timestamps, pointer/touch tooltips, keyboard sample selection and five-second
  updates. Runtime names, loaded counts and states sit side by side in a compact
  section. Storage retains every discovered record, capacity, used percentage,
  progress and textual online/offline state. All four shortcuts form a small
  wrapping action toolbar. No telemetry or discovery logic changes.
- **Model Manager:** one list and one selected inspector. List rows show name,
  runtime, state and resource indication. Search/filter apply to the list; the
  selection survives telemetry refresh, falling back to the first visible result
  when filtering removes it. Empty results clear the inspector. Selecting a row
  retrieves existing metadata through the existing cached details request.
  The inspector retains state, installation, readiness, provenance, process
  observations, technical details, resource requirements and recent operations.
  Load/Unload/Switch controls are visually prominent below the model identity and
  retain the existing protected confirmation/preflight flow. The list remains
  visible while the inspector scrolls independently.
- **Model Library:** registered-model rows lead to the existing manager inspector;
  NAS assets remain a separate read-only inventory with Collections and Model
  components views. Aligned name/type/resource columns and alternating surfaces
  replace tile cards. Component view remains the existing bounded weight-file
  inventory; it does not claim to enumerate every runtime component or make assets
  runnable. Classifications, missing components and compatibility evidence remain.
- **Performance:** three aligned semicircular instruments, a wide time-series
  region with adjacent hardware readings, and storage records below. Thin
  dividers establish analytical regions without decorative cards.
- **Workspaces:** six compact native disclosure rows. Opening a profile reveals
  its existing suggestion/requirement. Profiles remain informational and never
  launch a runtime or change the selected model automatically.
- **Activity:** alternating log rows with operation/stage, model/time and detail.
  The refresh control, empty state and retry feedback remain.
- **Settings:** separate Appearance and Connection/privacy preference groups,
  divided by rules rather than enclosing cards. Existing theme persistence and
  prototype link behavior remain.

## Visual grammar

The final `Professional desktop workspace` block in `web/style.css` defines the
new composition and supersedes legacy presentation rules. Light and dark colors
are listed above. Surfaces use 1px dividers; application regions have square edges,
controls 5px corners and status labels 4px corners. Broad card shadows, decorative
background blur and overview metric icons are removed. Protected modals retain
subtle depth to communicate interruption. Blue identifies selection, focus and
telemetry; operational warnings retain text and their existing semantic colors.

Body text is 13px; controls and row values 12px; supporting source/status text
11px, with metadata provenance 10px. Page titles are 24px, selected model titles
21px and primary memory readings 38px. Numerical readings use tabular figures.
Names and evidence wrap; no identifier is silently truncated. Text hierarchy uses
size and weight rather than oversized whitespace. Long-content and actual font
legibility still require rendered acceptance.

## Interaction and responsive behavior

Model rows are native buttons with `aria-pressed`, an inspector relationship and
keyboard ArrowUp/ArrowDown/Home/End selection. Tab retains normal button behavior.
Refresh restores row/action/disclosure focus and list/inspector scroll positions;
registered-library focus is restored when its rows refresh. Selecting a different
model resets the inspector scroll and opens its details. Existing modal focus
protection, Escape/Cancel, selected stops and explicit risk acknowledgement stay
intact. Selection does not authorize any model operation.

Below 1100px the sidebar and spacing tighten. Overview moves Models Loaded to an inline row below 1100px; below 850px its
runtime and storage sections stack. Below 600px memory spans the instrument
row above paired GPU/CPU gauges, with two columns of shortcuts. At 720px and below,
navigation becomes the existing horizontal strip; controls gain 44px targets.
Model selection becomes a bounded 220px-high list above the inspector, which
flows with the document. Library columns collapse to readable records. No
horizontal scroll is intentionally required. Zoom and short-window behavior need
actual browser validation, especially the independently scrolling desktop panes.

## Evidence and limitations — 2026-11-03

All **117 Python tests** and all three JavaScript suites pass, including new
master-detail selection, filtering, refresh persistence and escaping assertions.
Browser acceptance scripts now select models through the list and retain the
existing simulated lifecycle assertions. Syntax/compilation and whitespace checks
pass. No backend, lifecycle, authentication or desktop-launcher file was modified
by this redesign; previous uncommitted launcher work remains intact.

Rendered acceptance is **BLOCKED / NOT VERIFIED**: both browser commands exit 2
because Playwright is missing; a fresh random loopback bind is denied; CUA exposes
no windows or browsers. No screenshots were produced. The design detector ran in
degraded regex mode without computed styles or contrast and reports advisory
legacy palette/type/radius findings. It cannot certify the result. Independent
finish review is source-only, not a visual approval.

Required next acceptance: both themes at 1440px and 320/390px; short desktop
windows; high-DPI and 200% zoom; all seven pages with long names and unavailable
metadata; master-list keyboard selection and polling focus/scroll retention;
modal keyboard return and disabled controls; library columns; gauges/charts;
computed contrast and screen-reader behavior. Existing desktop launcher/browser
chrome limitations remain documented in `docs/design/DESKTOP-EXPERIENCE.md`.
Do not label the release visually verified or READY until these gates pass.

## Overview hierarchy refinement — 2026-11-03

This scoped follow-up changes Overview markup and dashboard-scoped CSS only;
application JavaScript, Performance instruments, backend and runtime configuration
are unchanged. Existing uncommitted work is preserved. Neutral theme tokens and
native typography carry through both appearances. Thin separators group the
instruments, shallow history, operational records and action toolbar without
adding oversized cards. All storage records remain visible, so no disclosure is
needed and no capacity/status information is hidden.

Validation: 117 Python tests and all three JavaScript regression suites passed;
Python compilation, application/browser-runner JS syntax, installer syntax-only
and diff whitespace checks passed. The read-only security scanner completed.
The browser fixture now checks Overview at 1440/1024/768/390/320px in both themes,
visible instrument SVGs, chart height and keyboard selection, storage progress,
and all four shortcuts plus both runtime/storage navigation links.

Both browser runs are **BLOCKED** because Playwright is absent. A fresh local
socket check failed with PermissionError before bind. These new browser checks
have not executed; no rendered responsive, contrast, tooltip, zoom or assistive
technology acceptance is claimed. The approximate visual-emphasis target is a
composition intent, not a measured rendered result. Large storage inventories
and runtime error text may extend the secondary region rather than hide evidence.
The layout detector reports no findings in degraded regex mode; computed styles
and contrast were unavailable. Live runtime compatibility remains **NOT VERIFIED**;
no model operations, service changes or installer execution occurred.

## Premium glass finalization — 2026-11-03

This section supersedes the master-detail and square-surface direction above. Compact model cards form a three-column grid, reducing to two columns at 1100px and one at 720px. Cards present current state, runtime, parameters, quantization, allocation when available and deliberate action buttons. Details opens a separate scrollable dialog with provenance and operational evidence; Escape and Close restore focus. Lifecycle confirmation remains separate.

The radius scale is 8px for small controls, 10px for buttons and inputs, 14px for cards, 18px for panels and 20px for dialogs. The sidebar uses a translucent neutral surface with blur and a solid fallback; cards use a restrained shadow and dialogs form the highest elevation. Neutral light and dark themes retain blue interaction accents. Gauges use green below 60%, amber from 60% to below 85%, and red from 85% to 100%; numeric readings remain visible and unavailable values remain neutral. These bands describe utilization, not hardware health.

Rendered acceptance is BLOCKED: Playwright is unavailable and loopback socket creation is denied. The design detector operated in degraded regex mode, with legacy palette and type advisories; computed contrast was not assessed. Firefox, standalone window, responsive appearance and assistive technology require validation on a permitted workstation.

## Glass visibility correction — 2026-11-03

This section supersedes the earlier square Overview surface description. The
instrument group is an 18px rounded, translucent raised surface with subtle
separators, layered shadows and a fine border. Memory Usage, Runtime Status,
Storage Health and Quick Actions use separate compact 18px glass surfaces. A
light environmental gradient and dark counterpart provide material behind the
surfaces; 14px backdrop blur has translucent-color fallbacks. Instrument
headings, values and arc weights establish hierarchy without changing measured
values or utilization bands. Model cards retain the compact grid and separate
details dialog, with explicit ordering of heading, facts and actions.

Diagnosis: the late workspace reset removed the background, border, shadow,
radius and blur from `.glass`, `.panel`, `.gauge-card` and `.metric`, including
more-specific dark selectors. The subsequent premium block restored only a
radius to panels; it did not restore their material, and the instrument wrapper
remained a square opaque strip. The previous inspector's flex `order` rules
also placed compact card facts before the model title. Scoped Overview rules and
explicit card ordering now supersede those conflicts. The document loads the
stylesheet, but static responses lack an explicit cache policy; a versioned
stylesheet URL prompts retrieval of this revision. No browser cache was
inspected, so caching is a possible contributor rather than a proven cause.

These are implementation descriptions, not visual acceptance. No previous
screenshots were available in the workspace and no browser could be reached in
this environment. Firefox rendering, comparison, light/dark contrast, responsive
composition, model grid and dialog remain **NOT VERIFIED** until the guarded
browser fixture and manual screenshot comparison run on a permitted workstation.
