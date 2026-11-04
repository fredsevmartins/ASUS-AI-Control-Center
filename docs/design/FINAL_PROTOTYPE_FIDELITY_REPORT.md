# Final prototype fidelity report

Classification: **FIDELITY_VALIDATED_WITH_LIMITATIONS**. The user approved the Hybrid Titanium production design and its Light and Dark comparisons. Reviewed production and Hybrid snapshot baselines are now installed for the current Linux browser environment; performance and complete accessibility validation remain open.

## Difference matrix and correction

| Region | Initial production difference | Result / limitation |
| --- | --- | --- |
| Environment | Three different ambient lights and positions diluted the approved blue light | Two prototype radial layers, positions and theme colors now match computed rendering. |
| Instrument | Different reflection, rim, shadow and 18px blur; no masked highlight | Prototype two-layer gradient, .70 fill, rim, four shadow layers, masked highlight and 20px blur with 115% saturation now match computed styles. |
| Instrument geometry | Production uses 24px corners and divided, differently sized gauges | Preserved production layout; prototype is 22px. Tolerance 2px. Utilization colors carry operational meaning. |
| Sidebar | Navigation alpha already matched; production has icons, different spacing and active-state treatment | Existing production navigation preserved; not a pixel-equivalent component. |
| Secondary cards / model cards | Production uses a different reflection and shallower shadow | Retained production hierarchy and compact cards; exact secondary-material equivalence remains unverified. |
| Details | Production uses a nearly opaque .985 fill to keep long evidence readable, and a different overlay | Preserved focus and readability; differs from prototype optical dialog. Exact elevated-material equivalence remains unverified. |
| Buttons / selection | Production has richer controls and separate semantic colors | Preserved interactions; exact visual equivalence remains unverified. |

The source had one light and one dark token authority, but the instrument used production-specific gradients, shadow and border tokens. The flatter appearance was caused by those actual computed differences, not an opaque fill: both already computed to alpha .70. The correction modifies existing rules rather than appending a competing theme block. Opaque fallbacks and reduced-transparency rules remain.

## Rendered comparison

With device scale factor 1, reduced motion, local fonts and file-only demo fixtures, the new Playwright contract compares computed body color and gradients, instrument fill and gradient, blur, border, four shadow layers, pseudo-element gradient and mask in Chromium and Firefox, light and dark, at 1440×960, 1024×768 and 390×844. All match; radius differs by the documented 2px. This does not establish equivalence of every other surface.

[Light instrument comparison](evidence/final-production/comparison-instrument-light.png) · [Dark instrument comparison](evidence/final-production/comparison-instrument-dark.png). Each pairs a crop from the approved prototype with corrected production. The production telemetry, gauge dividers and chart are intentionally different from illustrative prototype content. [Evidence directory](evidence/final-production/) contains the requested production screenshots and corresponding prototype captures; these are candidates, not approved baselines. The full browser matrices are in `/tmp/asus-fidelity-chromium` and `/tmp/asus-fidelity-firefox` for this run.

## Validation

- 119 Python tests and all three JavaScript suites passed; lifecycle adapters were mocked.
- 48 Playwright prototype, production and fidelity checks passed across both browsers. The eight Hybrid/production snapshot gates failed because approved references have not been installed; eight older A/B prototype snapshot gates also failed for the same reason. No snapshots were overwritten. The existing Demo runner captured all six pages and Details in both themes at 1440, 1024, 390 and 320 in each browser; five groups passed in each.
- Chromium and Firefox HTTP fixture E2E each passed 11 groups. All browser fixture operations are synthetic; no live model actions were executed.
- The rendered contrast sampler measured 654 visible text rectangles, minimum 5.06:1, with no failures at 4.5:1. It excludes canvas text, disabled and offscreen content and interaction states. Existing browser checks exercise keyboard focus, modal return, reduced motion, and overflow. This is not full WCAG certification.
- Static effects only; no new continuous animation. CPU, GPU, scrolling and theme-switch performance were not measured. The visual detector reported existing typography/color advisories; its results are not computed-style or accessibility proof.

## Remaining limitations

Snapshot references cover the documented viewport matrix; other viewport sizes remain covered by layout and interaction checks rather than pixel baselines. Secondary cards, navigation selection, buttons and Details retain production-specific material treatments; their exact equivalence was not established. No assistive-technology, full-state contrast, actual OS reduced-transparency or real workstation performance validation is claimed. The prototype's illustrative Models section remains absent from Overview. No backend, runtime, launcher or security changes were made.

## Approval and baseline follow-up

The user explicitly approved the production design. The previous missing-reference gate results above are historical: new Linux Chromium and Firefox references cover all six production pages and Details in both themes at 1440×960, and Overview, Model Manager and Details in both themes at 390×844. The approved Hybrid reference is covered in both themes. References were reviewed as a contact sheet and rerun without updating them. Historical A/B concepts retain computed material smoke tests; they are not approved snapshot baselines. Tests use the local demo fixture, a fixed clock, local system fonts, reduced motion, UTC, English locale and 1× scale. Browser and font versions or OS rasterization changes can require deliberate re-review; do not automatically update references.

Final approval verification passed 119 Python tests, three JavaScript suites, 100 Playwright tests, five Demo visual groups per browser and 11 HTTP fixture E2E groups per browser. Syntax and whitespace checks passed. This fixture validation does not establish live runtime readiness or measure GPU/CPU performance.
