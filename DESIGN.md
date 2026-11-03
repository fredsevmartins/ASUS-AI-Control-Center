---
name: ASUS AI Control Center
description: Midnight Blue and Graphite workstation instrumentation with restrained optical glass.
colors:
  bg: '#f5f7fa'
  surface: '#fff'
  raised: '#e9eef5'
  ink: '#222831'
  sub: '#526174'
  line: 'rgba(57,83,119,.18)'
  blue: '#407bbd'
  dark-history-blue: '#74b5e8'
  indigo: '#285e99'
  action: '#326ba8'
  action-hover: '#265689'
  accent-bg: 'rgba(64,123,189,.12)'
  nav-glass: 'rgba(238,243,250,.67)'
  instrument-glass: 'rgba(255,255,255,.56)'
  material: 'rgba(255,255,255,.52)'
  dialog-glass: 'rgba(248,251,255,.985)'
  edge: 'rgba(92,122,160,.24)'
  highlight: 'rgba(255,255,255,.94)'
  reflection: 'rgba(255,255,255,.48)'
  reflection-fade: 'rgba(255,255,255,.02)'
  green: '#197b56'
  warning: '#875713'
  danger: '#b93232'
  band-low: '#23966b'
  band-medium: '#bd801e'
  band-high: '#dc4c4c'
  dark-bg: '#0b1120'
  dark-surface: '#172235'
  dark-raised: '#222e40'
  dark-ink: '#f1f5f9'
  dark-sub: '#a8b8cc'
  dark-line: 'rgba(173,196,227,.16)'
  dark-indigo: '#91c4ed'
  dark-action-hover: '#3c79b9'
  dark-accent-bg: 'rgba(116,181,232,.13)'
  dark-nav-glass: 'rgba(12,20,35,.73)'
  dark-instrument-glass: 'rgba(25,40,62,.59)'
  dark-material: 'rgba(24,35,53,.58)'
  dark-dialog-glass: 'rgba(23,34,53,.985)'
  dark-edge: 'rgba(161,190,226,.19)'
  dark-highlight: 'rgba(216,234,255,.17)'
  dark-reflection: 'rgba(136,182,229,.09)'
  dark-reflection-fade: 'rgba(91,135,188,.01)'
  dark-green: '#70d1a6'
  dark-warning: '#efbd6d'
  dark-danger: '#ff9999'
  dark-band-low: '#54c797'
  dark-band-medium: '#e5a23b'
  dark-band-high: '#f07575'
typography:
  headline:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Ubuntu, sans-serif'
    fontSize: '29px'
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: '-.03em'
  title:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Ubuntu, sans-serif'
    fontSize: '19px'
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: '-.02em'
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Ubuntu, sans-serif'
    fontSize: '14px'
    lineHeight: 1.5
  label:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Ubuntu, sans-serif'
    fontSize: '10px'
    fontWeight: 650
rounded:
  badge: '6px'
  segment: '7px'
  quick-action: '8px'
  control: '9px'
  navigation: '11px'
  notice: '12px'
  card: '16px'
  panel: '18px'
  dialog: '22px'
  instrument: '24px'
spacing:
  compact: '4px'
  control: '8px'
  strip: '12px'
  grid: '14px'
  inset: '16px'
  card: '18px'
  panel: '20px'
  section: '24px'
components:
  button-primary:
    backgroundColor: '{colors.action}'
    textColor: '#fff'
    rounded: '{rounded.control}'
    padding: '7px 12px'
  button-primary-hover:
    backgroundColor: '{colors.action-hover}'
  model-card:
    rounded: '{rounded.card}'
    padding: '18px'
  panel:
    rounded: '{rounded.panel}'
    padding: '20px'
---

# Design System: ASUS AI Control Center

## Overview

**Creative North Star: "The Midnight Workstation"**

A precise desktop instrument with Midnight Blue, Graphite, illuminated edges and rounded optical layers. The user explicitly replaced the previous emerald and pale-green identity with a premium Liquid Glass-inspired direction. System typography, authored SVG stroke icons and compact observations keep the local workstation legible and deliberate. Glass supports hierarchy; operational evidence remains the content.

This is the active, implemented frontend design. The previous DESIGN.md, including its uncommitted guidance, is preserved in [PRE_MIDNIGHT_DESIGN.md](docs/design/PRE_MIDNIGHT_DESIGN.md). Earlier historical documents remain historical. The source of implementation truth is `web/style.css`, `web/index.html` and `web/app.js`; this document captures their shared rules. No new backend, runtime or launcher behavior belongs to this visual direction.

**Key Characteristics:**

- Dominant memory instrumentation, compact compute and supporting observations.
- Five material elevations with restrained reflections and blue interaction states.
- Light cool-neutral and dark Graphite appearances, with equal information hierarchy.
- Explicit uncertainty, provenance and separation of discovered assets from runtime registrations.

Visual acceptance is **PARTIAL**. The guarded, file-only Firefox Demo fixture validated six pages plus Model Details in both themes at widths 1440, 1024, 768, 390 and 320: 70 matrix screenshots plus confirmation evidence. The four-disk desktop strip is synthetic fixture data. No HTTP, NAS or runtime requests were made. The finish reviewer accepted four resolved corrections: narrow gauge collision, dialog ghosting, strip height and gauge alignment; this is a limited correction verdict, not complete release certification. See [MIDNIGHT_VISUAL_ACCEPTANCE.md](docs/design/MIDNIGHT_VISUAL_ACCEPTANCE.md) and [evidence](docs/design/evidence/midnight-glass/).

Full HTTP E2E is BLOCKED by loopback EPERM; Chromium sandbox launch is BLOCKED. The default local Playwright import is missing; the fixture run used an externally provisioned module via environment configuration. Chromium and real GX10 application acceptance remain unverified, including launch/authenticated application integration. No live readiness, inference, measured FPS, idle CPU or computed contrast claim follows from fixture screenshots.

## Colors

Midnight Blue carries interaction and data history; Graphite and cool neutral light carry the environment. Frontmatter records reusable values as authored; dark entries map to the corresponding `body.dark` overrides. Unoverridden CSS values, including the primary action blue, remain shared. The canvas history uses its own lighter dark-theme blue.

### Primary

- **Workstation Blue** (`action`): primary actions, with the theme-specific hover shade.
- **Optical Blue** (`indigo`): active navigation, links, focus outlines and accents; its lighter dark-theme counterpart preserves visibility.
- **History Blue** (`blue`): light memory history, legend and storage progress; the dark canvas uses `dark-history-blue`.

### Neutral

- **Cool Environment / Midnight Environment** (`bg`): static ambient gradient foundation.
- **White / Graphite Surface** (`surface`): opaque fallback and reduced-transparency surfaces.
- **Raised Neutral** (`raised`): hover and inactive-state separation.
- **Graphite Ink / Frost Ink** (`ink`), with subordinate `sub`: information hierarchy without pale-green tint.
- Material, edge, highlight and reflection colors carry the five elevations below.

### Semantic

Green remains a success/observed-state and low-utilization signal, not the brand accent. Amber identifies warnings and medium utilization; red identifies errors and high utilization. Gauge bands remain below 60%, 60–84%, and 85% or above. Utilization bands are not verified health or inference readiness. Status text accompanies color.

**The Evidence Rule.** Unknown readings remain unavailable; do not invent zero values or color an uncertain runtime as inference-ready.

## Typography

The local system stack is used throughout; there are no remote fonts. Normal body text uses the frontmatter body role. Page headlines use the headline role, falling to 26px at 720px and below; model names use the title role. Dialog headings are 22px; workspace titles are 16px. Operational controls and facts use 12px, navigation and principal instrument labels 13px, supporting observations 11px, and badges/compact telemetry 10px. The small brand descriptor remains 9px; 8px badges are removed.

Gauge values are tabular, weight 600, with tight tracking: memory scales from 36–52px, compute from 26–38px and becomes 28px in the narrow layout. The loaded-model count is 52px on desktop and 28px when moved below the gauges. Units and explanatory text remain visually subordinate. Use wrapping for long identifiers and evidence rather than clipping useful information.

## Layout

The desktop shell has a sticky 208px sidebar, 56px topbar and centered content capped at 1640px with 28px horizontal inset. The sidebar becomes 184px at 1100px and below. At 720px and below it becomes a top navigation strip with horizontal scrolling; content inset becomes 14px and principal controls have 44px minimum targets. Spacing is compact and varies by role; it is not a rigid multiples-only grid.

Overview places the instrument assembly above the 184px memory-history canvas, then a supporting strip of Runtime Status, Storage Health, Hardware Telemetry and Quick Actions. Above 1250px all four supporting modules share one row; from 601–1250px they use two columns; at 600px and below they use one. The full four-disk fixture measured 154px high on desktop after correction. This is an observed fixture result, not a fixed CSS height: errors, offline messages and extra content must grow naturally.

The wide instrument row uses memory/compute/compute/count proportions of 1.55/1/1/.72. At 1100px and below the model count becomes a horizontal row beneath the three gauges. At 600px and below memory spans the row above the two compute gauges. Memory has a maximum 310px visual width, compute 220px; their desktop visual canvases are each 174px high. SVG `xMidYMax meet` alignment keeps the arc geometry anchored to the bottom of its canvas. Narrow compute canvases become 120px high; memory remains 174px. Preserve clearance between readings, arcs, scales and captions.

Model Manager and the six planning workspace cards use three columns above 1100px, two from 721–1100px and one at 720px and below. Model cards lead with the name, align compact facts, and keep actions at the foot. NAS inventory uses compact rows with compatibility visible before the evidence disclosure; it stacks on small screens. Activity retains readable event rows. Settings groups appearance and connection/privacy facts in one surface.

## Elevation & Depth

Depth combines tonal separation, translucent fills, fine borders, static diagonal reflections and restrained shadows. Reflection gradients are backgrounds, never overlays across text. The five levels are structural, not five arbitrary shadow strengths:

| Level | Material | Treatment |
| --- | --- | --- |
| 0 | Environment | Two static radial ambient lights over the theme background; no animated decoration. |
| 1 | Navigation | Theme navigation glass, edge border and lateral shadow; 22px backdrop blur where supported. |
| 2 | Instrument assembly | Dedicated instrument glass, 24px corners, stronger panel shadow and inset highlight; 18px blur. Individual gauges share this assembly. |
| 3 | Secondary observations | Theme material fill, reflected edges, 18px panels/16px cards and shallow card shadows. No blanket blur on every card. |
| 4 | Dialog | Nearly opaque theme dialog glass (alpha .985), 22px corners and strongest shadow; 24px blur over a dimmed backdrop with 6px blur. |

Navigation fill alpha is .67 in light and .73 in dark; instrument fill is .56/.59; secondary material is .52/.58. These controlled differences make hierarchy visible while the dialog prevents background text ghosting. Card shadows are shallow, instrument shadows broader, and modal shadows broadest; exact theme shadow recipes remain centralized in CSS custom properties.

Backdrop blur is progressive enhancement via `@supports`, including the WebKit-prefixed declaration. Unsupported blur replaces the main navigation, instrument, panel, model/workspace card and dialog materials with opaque theme surfaces. Reduced transparency additionally removes backdrop blur and makes capacity strips opaque. Reduced motion disables animations, transitions and smooth scrolling; normal gauge updates may animate for .65s and control states transition for .16s. There are no continuous decorative animations. Forced colors uses system Canvas/CanvasText surfaces and borders, Highlight arcs/active borders and GrayText tracks. Canvas history is separately drawn; do not claim complete forced-color chart adaptation from those CSS rules.

Static gradients, limited blur regions and a canvas device-pixel-ratio cap of 2 reduce avoidable work. These are implementation choices, not benchmark evidence. Browser blur appearance and real desktop composition remain acceptance boundaries.

## Shapes

Rounded geometry progresses from small badges and controls to larger enclosing surfaces, using the frontmatter radius scale. Navigation/segmented enclosures are gently curved; model/workspace cards are 16px, panels 18px, dialogs 22px and the instrument assembly 24px. One-pixel material edges and inset highlights articulate the curves. Semicircular gauges retain rounded stroke ends. Avoid adding square industrial containers or oversized pill controls that conflict with these established silhouettes.

## Components

### Controls and navigation

Primary buttons use blue with white text, a subtle top highlight and a blue hover. Secondary/icon controls use the current material, an inset highlight and raised hover. Selected segments use material plus card shadow; active navigation uses a reflective material, edge and blue text. Hover and focus strengthen borders and shadows without lifting model cards. Global keyboard focus uses a 3px blue outline with 3px offset. Preserve disabled states and accessible pressed states.

### Gauges and history

Semicircular memory and compute gauges preserve existing telemetry calculations, unknown-state handling and semantic bands. Their scale ticks are presentation geometry. The memory chart remains a real GiB history on a fixed 0–128 GiB axis, with 16 GiB ticks and explicit clipping description above range. It uses a blue line, real timestamps, a five-second refresh cadence and existing pointer/touch and keyboard inspection, including arrow keys and Home/End. Keep the accessible selected-sample text and tooltip behavior.

### Cards and read-only Details

Compact model cards expose status, provenance-backed facts and deliberate lifecycle controls. Details remains a separate read-only inspector: identity, storage/context, configuration, resource, status and recent-operation evidence. Metadata retains value/source/confidence; current allocation and context take precedence over stale cached details. The dialog header stays visible while the evidence region scrolls. Opening makes the application inert and focuses Close; Tab cycles between Close and the evidence region, Escape closes, and focus returns to the Details trigger. Keep the inspector distinct from protected lifecycle confirmation and risk acknowledgement.

### Library, planning and supporting modules

NAS assets remain non-runnable, with compatibility and “No executable adapter” visible before opening native keyboard-operable evidence disclosures. The six workspace cards are planning presets with descriptions and requirements, not launchers. Runtime, storage and hardware observations retain independent uncertainty and errors. Quick Actions are navigation shortcuts. Activity excludes prompts/model outputs; Settings keeps runtime configuration read-only and theme preference local to the browser. Demo data must remain clearly representative.

## Do's and Don'ts

### Do:

- **Do** use blue for interaction and preserve the independent success/warning/error meanings.
- **Do** preserve memory prominence, aligned gauge geometry and intrinsic supporting-panel growth.
- **Do** keep provenance, unknown readings and compatibility visible at the decision point.
- **Do** retain focus visibility, reduced-motion/transparency fallbacks and explicit validation boundaries.

### Don't:

- **Don't** restore emerald primary actions or pale-green light surfaces.
- **Don't** apply blur to every card, animate ambient gradients or place reflections over text.
- **Don't** compress the strip by clipping disks, offline messages, errors or useful labels.
- **Don't** turn NAS discoveries or workspace planning cards into runnable models.
- **Don't** equate fixture visuals with HTTP authentication, live runtime readiness, Chromium/GX10 acceptance or measured performance.
