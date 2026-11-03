---
name: ASUS AI Control Center
description: A precise, compact workstation utility inspired by native macOS applications.
colors:
  bg: "#f4f5f7"
  surface: "#ffffff"
  raised: "#f6f7f9"
  nav: "#eceef2"
  chrome: "rgba(244, 245, 247, .9)"
  ink: "#202329"
  sub: "#606772"
  line: "#dce0e6"
  indigo: "#245fc4"
  action: "#2463cf"
  action-hover: "#1d53b1"
  accent-bg: "#e3edfc"
  green: "#23704f"
  success-bg: "#e5f2eb"
  danger: "#b02f39"
  warning: "#875715"
  warning-bg: "#fcf2df"
  dark-bg: "#1b1d21"
  dark-surface: "#25282d"
  dark-raised: "#2c3036"
  dark-nav: "#212328"
  dark-chrome: "rgba(27, 29, 33, .92)"
  dark-ink: "#edf0f5"
  dark-sub: "#b0b7c2"
  dark-line: "#41464f"
  dark-indigo: "#91baff"
  dark-accent-bg: "#2b3c58"
  dark-green: "#91d7b2"
  dark-success-bg: "#293e34"
  dark-danger: "#ffa5ad"
  dark-warning: "#edc586"
  dark-warning-bg: "#403727"
typography:
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Ubuntu, sans-serif'
    fontSize: "14px"
    lineHeight: 1.5
  title:
    fontSize: "29px"
    fontWeight: 650
    letterSpacing: "-.03em"
  model-name:
    fontSize: "19px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "-.02em"
rounded:
  radius: "14px"
  control-radius: "8px"
spacing:
  space-1: "4px"
  space-2: "8px"
  space-3: "12px"
  space-4: "16px"
  space-6: "24px"
  space-8: "32px"
  space-12: "48px"
components:
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "#ffffff"
    rounded: "{rounded.control-radius}"
    padding: "7px 14px"
  button-primary-hover:
    backgroundColor: "{colors.action-hover}"
  model-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.radius}"
    padding: "20px"
---

# Design System: ASUS AI Control Center

## Overview

The direction is a polished native macOS utility: neutral light and dark surfaces, restrained blue accents, slight elevation, compact controls and readable operational evidence. System typography follows the host platform. ASUS AI identity comes from the brand mark, clear runtime language and the original semicircular gauges. No remote fonts or image assets are required.

This document records the final presentation in `web/style.css` and the chart/icon presentation in `web/app.js`. The semantic token block and trailing native-utility rules supersede earlier declarations in the stylesheet. The redesign is visual only; lifecycle behavior, metadata, available actions and backend contracts remain unchanged.

Validation evidence: 85 Python tests and all three JavaScript suites pass; the mechanical design detector returned `[]`. Source-level contrast samples range from 4.91:1 to 15.74:1. These are not rendered accessibility or visual certification. Browser checks are **NOT VERIFIED**: Playwright is missing, local socket access was denied and CUA exposed no usable browser surface. There are no screenshots. Desktop/mobile rendering, both themes, 200% zoom, focus order, screen-reader announcements and rendered contrast remain acceptance gates; this evidence does not establish release readiness.

## Colors

The frontmatter records the semantic CSS values. Dark entries correspond to `body.dark` overrides; action blue and its hover shade remain the same in both themes, with white button text. The legacy `--indigo` and `--violet` names both resolve to the same restrained blue; they do not introduce a purple accent.

Canvas, sidebar and raised surfaces are subtly different neutrals. Primary text uses `ink`; supporting text uses `sub`. Blue identifies actions, focus, navigation icons, telemetry arcs and selected model outlines. Green, amber and red express positive, attention and error states. Status always includes words; color alone must not imply readiness.

Canvas chart colors follow the same palette: labels use secondary text, the series uses accent blue, and selection uses `#1d53b1` in light mode or `#b9d2ff` in dark mode. Chart grid lines use `#e2e5eb` / `#41464f`; tooltips invert the primary text/surface relationship. These presentation values do not change chart sampling, scale or interaction.

## Typography

Use the system stack in the frontmatter without downloading fonts. Body text is 14px with a 1.5 line height. Page titles are 29px/650, falling to 26px at 720px and below. Section titles are generally 16px/600; workspace titles are 17px. Model names are 19px/600 with a 1.35 line height and wrap long identifiers rather than truncating them.

Navigation and model fact values use 13px; model descriptions, supporting labels and disclosure summaries use 12px; provenance and fact labels use 11px. Status pills use 11px, while compact badges and gauge scales use 10px. Supporting descriptions use 1.6–1.8 line heights where defined. Preserve source/confidence text when reducing card density.

Telemetry uses tabular numerals. The overview count is 44px/600; overview gauge values use `clamp(25px, 2.3vw, 32px)` and 13px units. Performance gauges retain their larger responsive value scale. Chart axis labels use a 12px system font. Heading tracking is restrained, typically between -.015em and -.03em.

## Layout

The application is a flex shell with a sticky 228px sidebar and a flexible main region. The top bar is 62px tall. Content is centered with a 1540px maximum width and padding of `32px clamp(20px, 3vw, 44px) 48px`. Panels use 24px padding; related dashboard grids use 18px gaps and 20px bottom spacing.

The overview has four equal columns, with no feature-card span. It changes to two columns at 1200px and below, then one at 420px and below. Overview gauges have a maximum visual width of 210px. The separate Performance gauge grid has three columns, changes to auto-fit columns with a 220px minimum at 1150px and below, and one column at 720px and below. The dashboard's two-column content region also stacks at 1150px.

Model cards use two equal columns by default, three at 1500px and above, and one at 1000px and below. Cards align to the top, use 18px gaps and 20px internal padding. Facts remain in two columns, with the final fact spanning both; gaps are 12px vertically and 16px horizontally. Expanded evidence stays within its own card. Actions wrap without hiding available controls.

Responsive rules:

- At 1000px and below, the sidebar narrows to 208px; the manager toolbar stacks, search becomes full width, and capacity content wraps.
- At 720px and below, navigation becomes a horizontal scrolling row above the content. The sidebar is full width and static; secondary sidebar content and navigation icons are hidden while destination labels remain. The top bar is 54px, the breadcrumb is hidden, and content padding is `24px 16px 40px`.
- At 720px and below, panel/settings padding is 20px, model-card padding is 18px, workspace and asset grids become one column, and quick actions retain two columns. Hero status is hidden; essential operational state remains in its dedicated components. Settings rows and detail rows can stack or wrap.
- At 420px and below, filters wrap into multiple rows, legends and runtime/disk rows wrap, and model fact column gaps shrink to 12px.

The modal is at most 560px wide, constrained to the viewport minus 32px, with a maximum height of 85dvh (85vh fallback) and internal scrolling. It uses 28px padding, reduced to 22px at 720px. Modal actions wrap on narrow screens. Long identifiers and evidence values use `overflow-wrap: anywhere`.

These are source-defined behaviors. Usability at 320px and 200% zoom requires rendered verification.

## Elevation & Depth

Solid neutral surfaces provide most separation. Dashboard panels, the capacity strip and selected navigation have gentle lift; model cards use a 1px border with no shadow. Loaded model cards strengthen that border with accent blue. A translucent top bar uses a 16px backdrop blur when supported. The protected modal uses stronger elevation over a `#11172066` scrim with 6px blur.

| Token | Light | Dark |
| --- | --- | --- |
| Panel shadow | `0 2px 5px #18243a06, 0 10px 28px #18243a05` | `0 2px 5px #00000012, 0 10px 28px #00000012` |
| Control shadow | `0 1px 3px #18243a12` | `0 1px 3px #00000024` |
| Modal/toast shadow | `0 24px 80px #10182740` | `0 24px 80px #00000070` |

Keep elevation subtle. Selected filters use a surface fill and control shadow; expanded model details use the raised neutral fill. Asset Library entries use divider rows rather than individually elevated cards.

## Shapes

Panels and model cards use 14px corners; primary controls and navigation use 8px corners. Segmented-control containers use 9px corners and their options use 6px. Detail disclosures use 8px corners; plan facts use 10px; modal cards use 16px. Status pills retain rounded ends and a small dot alongside their text.

The signature gauge remains a semicircle with rounded stroke caps and a 9px arc/track stroke. Preserve the gauge geometry and numeric center. Do not replace it with a full ring or a linear meter.

## Components

- **Navigation:** seven named destinations with `aria-current`, 44px minimum target height and 13px text on desktop. Active navigation uses a surface fill, control shadow and stronger weight. Hover uses the accent-tinted background. Mobile labels use 12px text and remain accessible through horizontal scrolling.
- **Buttons and fields:** primary actions use action blue, white text, 36px minimum height and `7px 14px` padding. Secondary actions use a bordered surface. Hover changes background/border; active buttons remove their shadow. Disabled buttons retain a not-allowed cursor and reduced opacity. Search is 38px tall with a neutral border, 8px corners and 13px text. Segmented options have 30px minimum height and `6px 12px` padding.
- **Keyboard focus:** interactive controls use a 3px accent outline offset by 3px. A visible-on-focus skip link leads into the content. Segmented controls allow focus outlines to escape the scrolling container. Preserve semantic buttons, inputs, native disclosures and accessible names.
- **Icons:** local inline SVGs use `currentColor`, no fill, a 1.6px stroke and rounded caps/joins. Standard icons are 20px; workspace icons are 24px. Workspace symbols use the same line-icon family as navigation and quick actions. Icons supplement labels rather than replacing essential text.
- **Gauges and charts:** retain original semicircular gauges, valid-value interpolation and unavailable states. Arc blue matches the chart series. Telemetry values and interaction semantics stay unchanged. Native progress elements represent valid capacity measurements; unavailable capacity omits the bar.
- **Model cards:** runtime/process state precedes name/type, compact facts, inline evidence disclosure and explicit actions. Preserve parameters, quantization, context, storage/model identity, health time, readiness, runtime errors, operational observations, resource estimates and recent operations. Technical values retain value/source/confidence records. Missing data remains Unavailable, Not verified or an em dash. Loaded and Ready remain distinct; runtime allocation is not proof of model requirement or inference readiness.
- **Model evidence and filters:** technical evidence uses a raised inset surface with readable separators. Search and exclusive status filters retain their existing behavior, `aria-pressed` state and informative empty state. Metadata loading remains budgeted, refreshes on disclosure and after one minute/manual Refresh, and prioritizes current allocation/context over cached details. Compact styling does not remove metadata or actions.
- **Operation feedback:** a persistent bordered status region exposes observed workflow phases and errors. Busy feedback uses native indeterminate progress without invented percentages. Failed action requests remain available until review/Refresh; refreshing the browser does not cancel the backend job.
- **Protected confirmation:** preserve the accessible name/description, Cancel-first focus, inert background, Tab trap including disclosure summaries, Escape dismissal and trigger-focus restoration. Stop choices begin unchecked. Selection changes invalidate the prior plan and acknowledgement; stale preflight responses are ignored. Capacity, requirement type and system reserve remain visible. Advanced details retain selection lists, projected reclamation, assumptions, client risk and recovery limitations. Confirm requires a valid unblocked single-use plan and separate risk acknowledgement; expired plans require review again.
- **Other surfaces:** Asset Library uses compact divider rows and retains its non-executable discovered-asset boundary. Workspace cards use modest line icons and 17px titles. Activity uses readable divided entries. Settings use an 850px maximum panel width and browser-local theme preference. Demo Mode retains its persistent banner and simulated failure toggle; representative data never silently replaces live observations.

Motion remains functional: 140ms background/border feedback on buttons and the existing 700ms gauge interpolation when valid readings change. There is no page entrance animation. `prefers-reduced-motion: reduce` suppresses gauge interpolation and reduces global transition/animation durations to effectively immediate changes.

## Do's and Don'ts

- **Do** preserve the neutral two-theme palette, restrained blue and slight elevation established here.
- **Do** keep compact cards complete: wrap identifiers and retain metadata provenance, warnings and all authorized actions.
- **Do** distinguish installed, resident, ready and unverified states. Unsupported non-generating readiness remains Unverified; independent process/residency evidence remains visible.
- **Do** preserve loopback binding, API authentication, Host/Origin/session checks, runtime-origin restrictions, lifecycle preflight/confirmation/risk acknowledgement, identity/capacity revalidation and locking. Recovery remains limited to selected stops and must verify their previous state before reporting success.
- **Do** use mocked adapters for tests and isolate browser fixtures from live runtime and NAS adapters. Keep credentials and real session tokens out of reports and screenshots.
- **Don't** run live load, unload or switch operations during development without explicit approval, change workstation services/configuration/model files, or substitute generating health endpoints for readiness evidence.
- **Don't** treat absent requirements or reclamation as zero, omit the system reserve, automatically clean up partially loaded targets, or present discovered NAS weights as runnable models.
- **Don't** remove the original semicircular gauges, introduce decorative gradients or remote visual dependencies, or use color alone to encode operational meaning.
- **Don't** count source inspection, contrast calculations or VM/DOM tests as rendered browser evidence. The accessibility target is WCAG 2.2 AA; browser and runtime acceptance remain NOT VERIFIED or BLOCKED when prerequisites are missing.
