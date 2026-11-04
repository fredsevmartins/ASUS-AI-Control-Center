# Midnight Titanium + Selective Optical Glass

An offline, synthetic prototype. Open `index.html?theme=dark` or `?theme=light` after checkout. Overview and Model Manager navigation and the read-only Details sample are prototype-only interactions; nothing connects to a runtime or NAS. `?view=models` and `?view=details` select capture states.

## Design and materials

Dark tokens: background #090E17, navigation #111A28, base #19273A, elevated #24364C, accent #4589D4, highlight #88C4F5, primary #F2F6FA, secondary #B7C5D6. Light: #EDF0F3, #E2E7ED, #FFFFFF, #F3F6F9, #2868B2, #71A5D8, #172333, #526174, respectively. Status uses separate green and explicit labels.

Optical panels use translucent color, backdrop blur, a static upper reflection, fine illuminated edges and inset/layered shadows. This is a CSS approximation of optical depth, not physical refraction. It does not distort content. Frosted cards use gentler blur and shadows; navigation uses a separate translucent fill. The already installed MIT-licensed @dpawlikowski/liquid-glass 0.3.0 was evaluated in Concept A but is not imported here: its displacement uses a duplicated scene and cannot accurately sample arbitrary live backdrop content. No additional dependency or continuous effect was added. CSS provides opaque fallback when backdrop-filter is unsupported and a reduced-transparency override where the preference is supported.

## Capture and testing

Run `npm ci`, then `npx playwright install chromium firefox` if browser binaries are absent. `node prototypes/liquid-glass/hybrid/capture.mjs` captures both engines, themes, three viewports, and Overview, Model Manager and Details into `evidence/`. Screenshots of A and B are in the parent evidence directory. No network requests are allowed by the capture route.

`npx playwright test tests/visual/hybrid.spec.mjs --grep-invert 'pending approved snapshot'` exercises computed styles, breakpoints, overflow, keyboard focus, modal opening/Escape and reduced motion. `npx playwright test tests/visual/hybrid.spec.mjs` additionally runs the pending snapshot gate; it fails until references are explicitly reviewed. After explicit approval only, `APPROVE_HYBRID_SNAPSHOTS=1 npx playwright test tests/visual/hybrid.spec.mjs --update-snapshots` creates references for review. Do not silently update them. Candidate full-page captures are not approved reference snapshots.

Chromium and Firefox rendered the prototype locally in both themes; this does not certify the packaged desktop browser or high-DPI rendering. Sampled Chromium screenshot background pixels at instrument and card locations, compared with the primary and secondary theme text colors, yielded 10.38:1/6.43:1 and 14.90:1/9.22:1 in dark; 13.54:1/5.40:1 and 15.42:1/6.15:1 in light. These are spot checks, not a comprehensive contrast audit: control, focus, all gradients, status and Firefox pixels require further measurement. Status has text labels, not color alone. Native dialog supports Escape and focus management; screen reader testing remains outstanding. Reduced motion is tested; the unsupported-backdrop and reduced-transparency paths are implemented but have not been executed in an engine lacking support.

No CPU, GPU, frame-rate or GX10 measurements were made. Blur and shadows have compositing costs; the CSS is static and limits stronger blur to two surfaces. Profile the actual app before integration. The visual detector ran in degraded regex mode because its parser dependencies were absent; it is not a clean accessibility or design audit.

## Final refinement, 2026-11-04

The narrow navigation is a horizontally scrollable list of six keyboard-focusable destinations with a trailing scroll cue that disappears at the end; focused items are scrolled into view. The four sections outside this isolated study show a prototype placeholder, not a live product page. At mobile widths the Details surface uses a 96% base fill and darker backdrop, a 44px close control, bounded height and scrollable content. Initial focus goes to the title; Tab cycles between Close and content, Escape closes, and native dialog focus restoration returns to the trigger. A static directional upper highlight adds depth without displacement or continuous animation.

Final captures are in `evidence/final/`: Chromium and Firefox, both themes, 1440×960, 1024×768, 768×1024, 390×844 and 320×720, for Overview, Model Manager and Details. The capture command above now writes there. The candidate snapshot gate remains pending. See [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md) for measured results and limits.
