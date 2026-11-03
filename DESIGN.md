---
name: ASUS AI Control Center
description: Layered desktop instrumentation and compact operational controls.
colors:
  bg: '#e9edf2'
  surface: '#f9fbfd'
  ink: '#202c3c'
  sub: '#536276'
  accent: '#245f9e'
  dark-bg: '#191f28'
  dark-surface: '#29323e'
  dark-ink: '#edf2f8'
  dark-sub: '#bac7d7'
  dark-accent: '#a2cbff'
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

Mode: Operate. The existing seven-page utility is presented as a calm desktop
instrument panel. System fonts, tabular readings, authored stroke icons and a
cool blue interaction accent establish a coherent identity without external assets.
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
| Overview | Dominant Unified Memory semicircle, secondary GPU/CPU, numerical model count, 184px history and compact runtime/storage panels |
| Model Manager | Three compact card columns on wide screens, two below 1100px, one below 720px; model name leads; aligned facts and deliberate action footer |
| Model Library | Raised registered inventory and separate NAS inventory, readable row hierarchy and component/collection controls; assets stay non-runnable |
| Performance | Three equal instrument surfaces, history/hardware regions and storage panel |
| Workspaces | One rounded disclosure group; existing informational profiles and requirements |
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
