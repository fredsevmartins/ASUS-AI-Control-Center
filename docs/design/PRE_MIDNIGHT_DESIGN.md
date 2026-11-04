---
name: ASUS AI Control Center
description: Layered desktop instrumentation and compact operational controls.
colors:
  bg: '#e9f0ef'
  surface: '#f6fbf9'
  ink: '#091d2b'
  sub: '#435e65'
  accent: '#087653'
  dark-bg: '#050b10'
  dark-surface: '#0d202d'
  dark-ink: '#e6f5ef'
  dark-sub: '#acc9c4'
  dark-accent: '#64e3bb'
typography:
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Ubuntu, sans-serif'
    fontSize: '14px'
    lineHeight: 1.5
rounded:
  control-radius: '9px'
  card-radius: '16px'
  panel-radius: '18px'
  dialog-radius: '22px'
---

# Premium desktop design

Mode: Operate. The existing six-page utility is presented as a calm desktop
instrument panel. System fonts, tabular readings, authored stroke icons and a
emerald interaction accent with deep-blue and black foundations establish a coherent identity without external assets.
The brief explicitly requests rounded glass materials inspired by professional
macOS utilities. No proprietary assets or new product features are introduced.

## Materials

The authoritative `Premium desktop materials` section in `web/style.css` replaces
the previous isolated premium overrides. Ambient blue-gray light falls behind
translucent content surfaces. The sidebar uses 24px blur; panels use 18px blur
with a readable translucent fallback. Fine edges and inset highlights separate
navigation, supporting panels, instrument surfaces and modal inspectors. Shadows
are restrained and offset. Dark mode has its own slate surfaces and light text.

Controls use consistent focus outlines, borders, disabled opacity and selected
materials. Model-card hover raises by 2px; reduced motion removes that transform
and transition. Focus within identifies the active card. No persistent model
selection interaction is added. Text selection, caret, scrollbars and native
color scheme follow the theme. Small screens retain 44px control targets.

## Page composition

| Page | Composition |
| --- | --- |
| Overview | Dominant Unified Memory semicircle, secondary GPU/CPU, numerical model count, 184px history, hardware readings and compact runtime/storage panels |
| Model Manager | Three compact card columns on wide screens, two below 1100px, one below 720px; model name leads; aligned facts and deliberate action footer |
| Model Library | NAS collection/component rows, summary counts and optional asset evidence; assets stay non-runnable. Runtime registrations remain in Model Manager. |
| Workspaces | Six compact cards in three/two/one responsive columns; visible planning descriptions and requirements |
| Activity | Rounded history surface with readable event rows and existing status differentiation |
| Settings | Grouped preference surface, aligned values and accessible theme control |

Gauge arcs retain existing calculations and unknown-value handling. Scale ticks
are presentation geometry only. Green is below 60%, amber is 60–84%, red begins
at 85%; bands indicate utilization, not verified health. No artificial readings.

Model Details is a separate inspector with identity, storage/context, configuration,
resource, status and recent-operation groups. Every metadata value retains its
source and confidence. The header remains visible while evidence scrolls. Close
and the evidence region participate in the focus trap; Escape restores the Details
button. Details retrieves metadata only. Protected lifecycle confirmation remains
separate and unchanged.

## Validation boundary

Implementation and mocked tests are complete for this pass. Rendered acceptance
is **BLOCKED**. No screenshots were available before the redesign or produced
in this environment. The authored design cannot be certified visually from source.
See [FINAL_VISUAL_ACCEPTANCE.md](docs/design/FINAL_VISUAL_ACCEPTANCE.md) for exact
attempts, screenshot commands and remaining gates. Earlier design history and
uncommitted documentation are preserved in
[PREVIOUS_DESIGN_HISTORY.md](docs/design/PREVIOUS_DESIGN_HISTORY.md); its square
surface and master-detail directions are superseded.

## Desktop window integration verification

The existing interface and its seven views remain unchanged in this launcher
pass. Chromium app mode requests 1440 × 960; Firefox retains browser chrome.
Window sizing, chrome, themes, high-DPI and input remain NOT VERIFIED in a real
GX10 session. Existing localized desktop/menu shortcuts were found read-only;
see [desktop experience](docs/design/DESKTOP-EXPERIENCE.md).

## Final UI consolidation

Emerald accents identify navigation, focus and primary actions; deep blue and black
anchor the dark surfaces. Light mode uses pale green neutrals with dark blue ink.
Semantic amber/red utilization and error colors remain distinct. Rounded surfaces,
translucent panels and offset shadows retain the existing glass material system.
Performance is removed from routes and markup; Overview owns gauges, keyboard and
pointer history inspection, hardware readings, storage and runtime observations.
Compact Model Manager cards and the protected Details/operation dialogs remain.
Library evidence is available through native keyboard-operable disclosures.
No launcher/backend/security changes belong to this UI pass. Rendered acceptance
is BLOCKED; see TESTING.md for the current evidence boundary.
