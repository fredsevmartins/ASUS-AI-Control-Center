# Midnight Blue + Graphite — visual acceptance

Date: 2026-11-03. Branch: `dev/premium-control-center`.

**Final classification: PARTIAL.** Real Firefox Demo visuals are validated.
Chromium application-window and authenticated HTTP browser acceptance remain
BLOCKED. No release READY claim, runtime-readiness claim or live model operation.

## Implemented scope

Frontend only: `web/style.css`, `web/index.html`, and presentation portions of
`web/app.js`. Tests: `tests/test_frontend.js`, `tests/browser_e2e.mjs`, and new
`tests/browser_visual.mjs`. Documentation: `DESIGN.md`, `TESTING.md`,
`CHANGELOG.md`, this report, retained evidence and the pre-redesign design archive.

The light theme uses neutral #F5F7FA, translucent white and graphite #222831.
The independently designed dark theme uses #0B1120 and #172235. Blue is the
interaction/history identity; operational green, amber and red retain semantic
roles. Five elevation levels distinguish environment, navigation, instruments,
secondary surfaces and dialogs. Static reflections, alpha, illuminated edges and
soft offset shadows complement progressive blur.

Unified Memory remains largest; GPU/CPU retain semicircles and unchanged
calculations and band boundaries. History retains its 184px height, real GiB,
0–128 axis, five-second observations, keyboard/pointer inspection and tooltips.
The four secondary modules share one desktop row above 1250px, two columns from
601–1250px and one at 600px and below. The full four-disk fixture measures 154px at
1440px in both themes. Content can grow for long names/errors; there is no forced
height or clipping. Only duplicate hardware fields already shown by gauges were
removed from the compact hardware list; memory used/available, GPU temperature
and CPU utilization remain there. Runtime counts, uncertainty and all disks remain.

Model cards stay compact in three/two/one columns; Details remains read-only with
its existing focus trap/return. NAS collection compatibility is exposed before
existing expandable evidence; assets are never executable registrations. Six
informational workspaces, Activity and grouped Settings share the same materials.

## CSS conflicts removed

The starting dirty stylesheet had five `:root` and five `body.dark` token blocks,
plus stacked purple-card, native-utility, square master-detail, emerald-glass and
final override layers. The replacement has one light and one dark token authority,
component styles and ordered responsive/accessibility sections. Opaque inherited
backgrounds, old green primary hover/borders, forced square/no-shadow surfaces,
retired Performance selectors and unused master-detail/layout selectors are gone.
Stylesheet size falls from 77,035 to 28,931 bytes (647 to 373 lines).

Existing unrelated dirty files were left intact. The entire starting DESIGN.md,
including prior uncommitted guidance, is archived in
[PRE_MIDNIGHT_DESIGN.md](PRE_MIDNIGHT_DESIGN.md); its old emerald direction is
historical. The current authoritative design is [DESIGN.md](../../DESIGN.md).

## Rendered evidence

The real Firefox binary opened local application files in explicit Demo Mode.
The fixture blocked every network request and started no server. All storage,
model and Activity evidence is synthetic. No real session token or runtime
credential appears in these images. These captures do not validate HTTP headers,
CSP delivery, authentication or any runtime adapter.

The run covers six pages and Details, both themes, widths 1440/1024/768/390/320:
70 matrix images plus one cancelled confirmation. [Results](evidence/midnight-glass/results.json)
contain geometry and guard assertions. 25 selected captures are retained here;
all 71 images remain in `/tmp/asus-ai-midnight-visual` for this session.

| Surface | Light | Dark |
| --- | --- | --- |
| Overview | [1440px](evidence/midnight-glass/dashboard-light-1440.png) | [1440px](evidence/midnight-glass/dashboard-dark-1440.png) |
| Model Manager | [1440px](evidence/midnight-glass/models-light-1440.png) | [1440px](evidence/midnight-glass/models-dark-1440.png) |
| Model Details | [1440px](evidence/midnight-glass/details-light-1440.png) | [1440px](evidence/midnight-glass/details-dark-1440.png) |
| Model Library | [1440px](evidence/midnight-glass/library-light-1440.png) | [1440px](evidence/midnight-glass/library-dark-1440.png) |
| Workspaces | [1440px](evidence/midnight-glass/workspaces-light-1440.png) | [1440px](evidence/midnight-glass/workspaces-dark-1440.png) |
| Activity | [1440px](evidence/midnight-glass/activity-light-1440.png) | [1440px](evidence/midnight-glass/activity-dark-1440.png) |
| Settings | [1440px](evidence/midnight-glass/settings-light-1440.png) | [1440px](evidence/midnight-glass/settings-dark-1440.png) |
| Two-column strip | [1024px](evidence/midnight-glass/dashboard-light-1024.png) | [768px](evidence/midnight-glass/dashboard-dark-768.png) |
| Narrow strip | [320px](evidence/midnight-glass/dashboard-light-320.png) | [390px](evidence/midnight-glass/dashboard-dark-390.png) |
| Narrow Details | [390px](evidence/midnight-glass/details-light-390.png) | [390px](evidence/midnight-glass/details-dark-390.png) |

[Protected confirmation](evidence/midnight-glass/confirmation-dark-1440.png) was
opened and cancelled; no operation was accepted. Four more strip images are in
the same evidence directory.

## Inspection, corrections and verdict

First-round browser screenshots exposed four defects. One correction batch and
a complete repeated matrix followed. An independent finish reviewer inspected
both rounds. Its final **ship** verdict covers the four scored fixes only:

| Finding | Final correction | Verdict |
| --- | --- | --- |
| 320px compute captions collided with scales | Separate vertical space and bottom-aligned SVG anatomy | Resolved |
| Model text ghosted through Details | 98.5% reading layer with elevated reflective shell | Resolved |
| Four-disk strip stretched all panels to 248px; badges 8px | Concise capacity rows, readable 10px status; strip 154px | Resolved |
| Gauge headings/scales followed different rhythms | Shared 174px canvas, larger memory arc, narrow compute 120px | Resolved |

The mobile modal's initial full-page image also contained a Firefox
fixed-position/scrolled-document capture artifact. Final modal captures scroll
to the top and capture the viewport. No such artifact is treated as UI evidence.

## Automated results and performance

- 119 Python tests pass; all three JavaScript suites pass.
- Python fixture compilation, both browser-runner/app JavaScript syntax, shell
  syntax and whitespace checks pass. The installer was not run.
- Five file-browser acceptance groups pass: responsive pages/Details, strip data
  and geometry, gauges/history/reduced-motion, model/keyboard/workspace behavior,
  and cancelled protected confirmation. No page errors or network requests.
- Local security scanner completed with its existing advisory infrastructure and
  synthetic-fixture findings; it is not a clean-audit verdict.
- Mechanical design detector ran once in degraded regex mode. It reported type
  and radius mismatches against the old DESIGN.md; the final design document
  records the actual authored system. Computed contrast was not evaluated.

Static gradients replace continuous decorative animation. Blur is limited to
navigation, the single instrument surface, modal and modal backdrop. Secondary
cards use layered alpha/reflections without individual backdrop filters. No
framework, dependency, polling increase or animation loop was added. Actual
scroll FPS, GPU cost and idle CPU in the Chromium app window are NOT VERIFIED.

## Remaining limits and reproduction

The ordinary HTTP runner could not import Playwright from the project. An
already provisioned external Playwright module enabled Firefox file rendering;
with that module, the authenticated fixture still fails to create its random
loopback socket (EPERM). Chromium with its sandbox intact exits SIGTRAP after
crashpad `setsockopt: Operation not permitted`. The browser connector reports an
existing-profile conflict; computer-use inventory is empty. No security bypass,
service change or browser-profile deletion was used.

Reproduction commands, provisioned-module/executable environment options and
remaining GX10 acceptance steps are in [TESTING.md](../../TESTING.md#midnight-blue--graphite-validation--2026-11-03).
Firefox file rendering does not establish Chromium compatibility, authenticated
HTTP delivery, screen-reader behavior, computed contrast, high-DPI performance or
actual runtime readiness. Reduced-transparency and forced-colors fallbacks are
implemented; their OS/browser-specific rendering still needs workstation review.

## Git state

Work stays uncommitted on `dev/premium-control-center`; no push or visibility
change. The checkout was already dirty in 12 files at the start, including README,
desktop launcher/tests and desktop-experience documentation. Those unrelated
changes remain. This pass touches the three web files, the two existing frontend
browser/test files, DESIGN/TESTING/CHANGELOG and adds the visual runner, report,
pre-redesign archive and evidence. No backend, launcher, service, runtime or NAS
configuration was changed by this pass.
