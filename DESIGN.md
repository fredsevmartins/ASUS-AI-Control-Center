# ASUS AI Control Center design system

Direction: restrained workstation desktop application. System typography follows the host platform, as requested by the macOS quality reference; no remote fonts, imagery or network dependencies. The product identity comes from measured layout, clear runtime language and a blue action accent. Surfaces use solid fills rather than decorative glass. Mode: Operate.

## Tokens and typography

Source: the semantic token block in `web/style.css`. Existing gauge rendering and its theme-specific tokens remain intact.

| Role | Light | Dark |
| --- | --- | --- |
| Canvas | #f3f4f6 | #191c21 |
| Surface | #ffffff | #22262d |
| Primary text | #20252e | #edf0f5 |
| Secondary text | #596372 | #afb8c6 |
| Border | #dce0e6 | #3c434f |
| Accent text/focus | #365bc7 | #a6bdff |
| Positive text | #187452 | #8cd5b2 |
| Warning text | #835313 | #edc586 |
| Error text | #a73536 | #ffa5a5 |

Primary buttons use white text on #365bc7 in both themes. Status labels always carry words as well as color. Runtime-reported memory is distinct from system capacity. Missing values render Unavailable, Not verified, or an em dash, never a fabricated zero.

Type scale: page title 30px/650 (27px narrow), model name 22px/600, section titles 16px by default (18px Model Manager, 20px workspace cards), body 14px, supporting content 13px, metadata 12px, status 11px. Body line height 1.5; descriptions 1.6. Names wrap rather than truncate essential model identifiers. Use tabular numerals for telemetry. Tracking stays at or above -0.03em in new headings.

Spacing tokens: 4, 8, 12, 16, 24, 32, 48px. Panel padding 24px; model cards 26px (22px narrow); card gap 20px. Card radius 14px, controls 8px. Cards use a border without shadow; modal elevation is reserved for protected confirmation.

## Components and interactions

- Navigation: seven named destinations, active fill and `aria-current`; horizontally scrollable labels on mobile.
- Model card: process badge and runtime → name/type → memory/readiness → expandable identity details → explicit actions. Loaded cards use stronger outline. Uncertain state blocks actions and explains recovery.
- Filters: exclusive status selection, `aria-pressed`, name/runtime search and informative empty state.
- Capacity: native progress element for valid system measurements; unavailable capacity omits the bar.
- Operation feedback: persistent ready/busy/error state; busy uses an indeterminate native progress element. Never fabricate stage or percentage.
- Confirmation: accessible modal name/description, focus initially on Cancel, background inert, trapped Tab, Escape dismissal, restored trigger focus. Switch stop choices default unchecked.
- Settings: browser-local theme preference; no runtime mutation controls. Prototype entry preserves launch parameters.
- Prototype: persistent banner and simulated failure toggle. Fixture data never substitutes silently for live telemetry.

Breakpoints: 1500px three model columns; default two; 1000px one and stacked toolbar; 720px horizontal navigation and stacked telemetry/content. Existing 1150px telemetry rules remain. At 320px and 200% zoom, controls and essential model names must remain usable; browser verification is pending.

Motion: 140ms color/border feedback, existing 700ms gauge interpolation only when valid values change. No page entrance animation. Reduced-motion preference suppresses transitions and animations globally.

Accessibility target: WCAG 2.2 AA, 4.5:1 normal text, 3:1 large text and essential graphics, visible keyboard focus, named controls, 44px main navigation targets, status announcements without moving focus. Browser-native controls and system fonts are intentional. Rendered contrast and assistive-technology checks remain release gates.

## Intelligent Model Manager increment — 2026-11-03

The Astra shell, palette, gauges, layout and native disclosure pattern are retained. Cards add parameters, quantization, context, storage/model identifier, health time, readiness and runtime errors. Technical values carry source/confidence text; unknown values remain Unavailable. Loaded and Ready have distinct words. Runtime allocation is not presented as a proven model requirement. A known resident model whose readiness endpoint rejects requests can still be explicitly unloaded; uncertain identity blocks mutation.

Model details remain an inline disclosure, with technical evidence, allowlisted configuration, resource estimate, operational observations and recent operations. Rich metadata loads automatically with a controlled budget, and immediately on disclosure. Frontend details are refreshed after one minute or manual Refresh. Errors remain readable across status refreshes; failed action requests persist in the operation banner until review/Refresh.

Confirmation retains the existing protected modal, Cancel-first focus, inert background, Escape, focus return and Tab trap. The trap includes advanced disclosure summaries. Switch stop boxes start unchecked. Changing selection invalidates the previous plan and acknowledgement; asynchronous stale preflight responses are ignored. Available memory, requirement type and system reserve are always visible. Advanced disclosure holds loaded/selected model lists, projected reclamation, estimation assumptions, client risk and recovery limitations. A separate risk checkbox and valid unblocked plan enable Confirm; expired plans require review again.

Operation feedback displays observed workflow phases, without percentage estimates. Browser refresh leaves the backend job active. Demo Mode simulates detail, preflight, confirmation, failure and operation endpoints with no fetch calls. Asset Library displays structural completeness and inferred compatibility while preserving its non-executable boundary.

New evidence/plan styling uses existing semantic tokens in both themes, wraps long identifiers and stacks memory facts within the existing modal width. The mechanical design detector returned no findings. VM/DOM regressions are not rendered accessibility or visual evidence: desktop/mobile, both themes, 200% zoom, focus order, screen-reader announcements and contrast remain release gates because no browser surface was available.
