# Final candidate acceptance

Status: PARTIAL. The prototype is isolated; no production change or live model operation was made. The four non-Overview/Model Manager destinations are named, keyboard-reachable prototype placeholders, not implemented product views.

The mobile navigation scrolls horizontally with a trailing cue, and focus scrolls each button into view. The Details dialog uses a more opaque mobile surface and dimmer backdrop, a 44px close target, constrained viewport height and scrollable content. Its title receives initial focus; the two interactive/scrollable stops cycle, Escape closes, and focus returns to the trigger. A static directional rim and highlight improve depth; there is no animated distortion or WebGL.

Evidence: `evidence/final/{chromium,firefox}-{light,dark}-{1440,1024,768,390,320}-{overview,models,details}.png`. Viewport sizes are 1440×960, 1024×768, 768×1024, 390×844 and 320×720. Screenshots use deterministic file-only data and reduced motion. These are candidates, not approved baselines.

Browser computed-style and interaction tests: 20 passed across Chromium and Firefox. Checks cover tokens, alpha, radius, shadow, blur support, viewport overflow, responsive strip, focus visibility, six navigation items, scroll, active state, dialog bounds, focus cycle, Escape, restoration and reduced motion. Model cards are observed in the captured layouts; their column count is not independently asserted. Unsupported-blur and reduced-transparency fallbacks are implemented but not exercised in an unsupported engine. Snapshot gate: four expected failures, because no approved reference exists. No references were updated.

Rendered screenshot background spot samples with the theme text colors: primary and secondary ratios on the instrument and card respectively are Chromium dark 10.19/6.31 and 14.90/9.22, light 13.54/5.40 and 15.42/6.15; Firefox dark 10.22/6.33 and 14.90/9.22, light 13.53/5.40 and 15.43/6.16. These samples exceed 4.5:1 but do not cover every text, control, gradient, focus indicator or state. Native dialog semantics and keyboard behavior were tested automatically; no screen reader or physical touch device was tested. Do not treat this as full WCAG certification.

Python unittest: 119 passed. Existing JavaScript suites passed. Existing HTTP browser E2E fails in both engines because `#dashboard .overview-records [data-link="models"]` resolves to two controls; this is outside the isolated prototype. Syntax and `git diff --check` passed (untracked files are not included in git diff). The security scan ran but external scanning tools were unavailable; its raw findings are not a clean security verdict.

No CPU, GPU, frame-rate, high-DPI or ASUS GX10 performance measurements were made. Captures in both engines showed no obvious rendering failure at the sampled sizes. Blur and shadows still require target-device profiling. Production integration should wait for explicit visual approval, reference-image review, resolution of the existing E2E selector, comprehensive accessibility checks and target-device validation.

The final inspection also found and corrected gauge-value crowding at 768px and a narrow Model Manager heading collision. The final captures were regenerated and the 20 hybrid checks passed again. The existing file-only visual harness passed five groups in each engine after the refinements.
