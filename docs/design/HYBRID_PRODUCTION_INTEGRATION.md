# Hybrid production integration

Status: **PARTIAL**, 2026-11-04. Production frontend rendered against isolated synthetic Demo data; this is not a deployment or live-runtime validation. Candidate screenshot references have not been approved.

## Design and implementation

The approved Hybrid prototype informed the material treatment, not the production data model. `web/style.css` centralizes theme values and applies static gradients, translucent fills, borders, inset and layered shadows and backdrop blur to the existing instrument, cards, navigation and dialogs. The mobile Details dialog uses a darker backdrop, bounded viewport height and a 44px close target. Unsupported blur and reduced transparency have opaque fallbacks; reduced motion disables transitions. No WebGL, refraction engine, remote assets or prototype fixtures were added to the application.

| Token | Dark | Light |
|---|---|---|
| Background | #090E17 | #EDF0F3 |
| Navigation | #111A28 | #E2E7ED |
| Base | #19273A | #FFFFFF |
| Elevated | #24364C | #F3F6F9 |
| Accent | #4589D4 | #2868B2 |
| Highlight | #88C4F5 | #71A5D8 |
| Primary text | #F2F6FA | #172333 |
| Secondary text | #B7C5D6 | #526174 |

Status colors and existing thresholds remain independent. The production Overview retains memory history, instrument calculations and four monitoring modules, and does not add the prototype's sample Models section. Model Manager retains real model identities, metadata, actions and preflight. Other four pages retain their existing content. The read-only inspector retains provenance and existing focus logic. No application JavaScript, backend, lifecycle, runtime configuration, authentication or CSP was changed.

The HTTP E2E selector previously matched both the Runtime Status link and the Quick Actions link. It now scopes to the monitoring panel header; Quick Actions remain separately exercised. This was a test ambiguity, not duplicate accessible names or a lifecycle defect.

## Evidence and tests

- 119 Python tests and three JavaScript suites pass. Compilation, JavaScript and shell syntax and `git diff --check` pass.
- Guarded HTTP E2E: 11 groups pass in each of Chromium and Firefox, including Demo operations simulated by the fixture. No live operations were performed.
- File-only production visual harness: five groups pass in each engine; its route blocks network requests. Candidate captures are in [evidence/hybrid-production](evidence/hybrid-production/), grouped by engine, theme, page and width. The requested 1440×960, 1024×768, 390×844 and 320×720 dimensions include all six pages, Details and confirmation. Earlier 768 and 1440 confirmation files are additional exploratory captures. Charts include synthetic history but timestamps vary; images are review candidates, not deterministic snapshot references.
- Hybrid prototype checks: 20 pass across Chromium and Firefox (excluding its pending snapshot gate).
- Production Playwright computed-style and interaction checks: 16 pass across both engines. They verify palette, translucency when supported, blur, borders, radii, shadows, grid breakpoints, modal bounds, keyboard trap/restoration and overflow. The unsupported-filter branch is conditional and was not exercised on an unsupported engine. Reduced motion is checked by the visual harness.
- Candidate screenshot gate is deliberately pending: no reviewed production baselines are installed. It fails until references are reviewed and installed. No snapshot update was used. Existing prototype checks are separate from production acceptance.

## Accessibility and performance limits

Automated keyboard tests cover Details, confirmation and chart inspection, and responsive tests cover viewport overflow. Status labels accompany colors. Screenshot inspection covered desktop Overview and mobile cards and Details, not a comprehensive visual or assistive-technology audit. A Firefox rendered-background spot check sampled 654 visible text rectangles, with a minimum estimated ratio of 5.09:1 and no failures at 4.5:1. It does not cover all text, controls, gradients, interaction states, canvas, screen readers, physical touch or unsupported blur; these remain unverified. The mechanical design detector reported advisory type-ramp and color findings; these are not a clean accessibility audit. No GX10 idle CPU, GPU attribution, frame rate, scrolling, theme-switch latency or rendering stability measurements were made. Static CSS reduces continuous work but does not establish measured performance.

## Files and acceptance

Changes: `web/style.css`, `tests/browser_e2e.mjs`, `tests/browser_visual.mjs`, `tests/test_frontend.js`, `tests/visual/production.spec.mjs`, this report, README, DESIGN, TESTING, CHANGELOG and candidate evidence. Existing untracked prototype, package configuration and `.gitignore` work predated integration and was preserved. Review candidate images and establish approved stable references, complete contrast and assistive-technology checks, and profile on GX10 before final acceptance. Current visual coverage and fixture tests do not establish live runtime correctness or target-device performance.
