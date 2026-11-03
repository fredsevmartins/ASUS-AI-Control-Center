# Testing

Current UI evidence: [Final refinement](docs/design/LIQUID_GLASS_REFINEMENT.md). Earlier baseline: [Midnight visual acceptance](docs/design/MIDNIGHT_VISUAL_ACCEPTANCE.md). Firefox file-only Demo rendering is validated; Chromium and authenticated HTTP browser acceptance remain BLOCKED. Earlier emerald/browser-blocked sections below are historical.

## Required automated checks

Run from the repository root. These checks do not contact live runtimes or perform model operations:

```sh
python3 -m unittest discover -s tests -v
node tests/test_frontend.js
node tests/test_model_manager.js
node tests/test_model_intelligence.js
python3 -m py_compile tests/browser_server.py
node --check web/app.js
node --check tests/browser_e2e.mjs
node --check tests/browser_visual.mjs
bash -n install.sh
git diff --check
```

Latest integration pass, starting at `9534fc0`: **85 Python tests passed**, all three JavaScript suites passed, and JavaScript/shell syntax and whitespace checks passed. No tests were skipped in the Python suite. The prior baseline was 63 Python tests; this pass adds 22 audit regressions. These results establish mocked contracts and source/DOM behavior, not live runtime compatibility or rendered accessibility.

`bash -n install.sh` checks syntax only. Never execute the installer as validation: it changes installed v5 files and the launcher.

## Automated coverage

| Area | Evidence |
| --- | --- |
| SGLang discovery/authentication | Independent systemd/container observations; model identity; 401/403 on metadata and readiness; unavailable transport; direct/wrapped timeout; 404/405/501 unsupported; explicit 503; authenticated GET success; stale last success; no generating fallback |
| SGLang interface/security | Drop-in replacement, inspected published loopback bindings, unknown mappings, remote origins/credentials in URLs rejected, existing credential file validation, response size bound, proxies/redirects disabled, no credentials or upstream error bodies returned |
| Ollama | Independent tags/ps failures, orphan residents with unknown installation, stored vs resident size, maximum vs active context, cached show/failures, incomplete/malformed architecture/digest data, identity conflicts and pre-mutation digest revalidation |
| Metadata | Explicit value/source/confidence, missing values retained, current allocation/context supersede cached details, inferred SGLang NVFP4/parameter labels |
| Preflight/authorization | Capacity and KV estimate, unknown requirements/reclamation, reserve enforcement, worker expiry recheck, stale fingerprints, exact selected stops, confirmation/risk acknowledgement, single-use/expired/tampered plans |
| Lifecycle/recovery | Mocked load/unload/switch and failures, worker startup failure, readiness failure, selected restoration, final recovery verification, partially loaded target retained, failed restoration, transient retry deadline and permanent failure fast exit |
| Concurrency/logging | Real simultaneous confirmation threads start one mocked worker, temporary advisory-lock contention, serialized sampling, bounded activity reads, malformed records, private temporary log directory/file |
| HTTP/security | In-memory handlers: session protection for every API, exact Host, Origin/Fetch Metadata rejection, Unicode invalid tokens, JSON/body/stop limits, transfer encoding rejected, static path allowlist, CSP/no-store/referrer headers |
| Frontend | Seven-view navigation source contract, storage validity/CSP markup, fixed 0–128 GiB charts, local times, sample selection, repeated high-DPI sizing, gauges/unavailable/decimal readings, filters/details, process/auth copy, preflight races, error retention, modal keyboard trapping and explicit stops |
| Demo isolation | Zero fetch calls for simulated status/details/library/preflight/actions; simulated failure leaves previous models unchanged; missing confirmation and reused plans rejected |
| NAS | Temporary bounded directory fixtures, symlinks ignored, malformed config and missing shards, structural classifications always non-runnable |

Python tests mock runtime operations and invoke API handlers without sockets. Lifecycle adapters, service/controller calls, inference and real model operations must never be used as unit-test fixtures. Logs and advisory locks must use temporary directories. JavaScript suites use VM/DOM/canvas harnesses and do not render a browser.

## Real-browser E2E acceptance

```sh
node tests/browser_e2e.mjs
AI_MANAGER_E2E_BROWSER=firefox node tests/browser_e2e.mjs
```

Use one command for an already provisioned Playwright browser. The application itself has no npm or Python package dependencies; this optional test runner requires an existing Playwright package and compatible browser binaries. It installs/downloads nothing. The runner exits 2 and prints BLOCKED for missing tooling/browser/socket access, 1 for assertion failure, and 0 only after passing its checks.

The runner launches `tests/browser_server.py` on a separate random loopback port with a synthetic token. Every runtime/NAS discovery and lifecycle entry point is patched to reject live access, and state/log paths are temporary. It exercises the actual application HTML/CSS/JavaScript in explicit Demo Mode, not the installed stable application. Never point the operation tests at a live server or remove the fixture guards.

The implemented acceptance cases cover all seven sections; light/dark themes; 1440, 390 and 320 pixel widths; DPR 2 and reduced-motion emulation; search/filter/details/provenance; gauges, canvas backing-size stability and timeline keyboard inspection; native storage progress; Cancel/Escape/focus restoration and Tab trapping; unchecked stop selection; risk acknowledgement; simulated switch and failure; Activity feedback; and intercepted connection failure. Document/session/Origin rejection runs over the fixture's real HTTP transport. Production lifecycle API paths are separately covered by mocked Python integration tests.

On success, screenshots and `results.json` go to `/tmp/asus-ai-browser-evidence` by default; set `AI_MANAGER_E2E_ARTIFACTS` to a writable evidence directory. The results explicitly state fixture-only coverage and no live runtime validation. No launch URL, real session token or runtime credential is captured.

**Current result: BLOCKED**, exit 2, because Playwright is not installed. No browser cases ran and no screenshots/results artifact were produced. The browser connector independently failed because its profile was already in use; the alternate computer-use browser inventory was empty. An isolated Firefox headless attempt failed because snap-confine lacks the required permitted capability; it produced no screenshot. Both the development app and the isolated fixture server failed to bind loopback with PermissionError. The mechanical Impeccable detector used degraded regex mode and returned `[]`; HTML parser modules and computed-contrast checks were unavailable. This is not rendered UI acceptance.

## Fresh GX10 observations and blocked checks

Verified read-only on this host during the current pass:

- Host `gx10-cbc7`, architecture `aarch64`, Python 3.12.3 and Node 22.23.1.
- `/proc/meminfo` reported 130,593,968,128 total bytes; available memory was a transient sample, not a model capacity calibration.
- `/mnt/nas/AI-Models` and `/mnt/nas/Storage` are mounts. `/mnt/ai-models` exists but is not a mount; it now reports offline.
- A bounded NAS metadata scan found 16 recognized asset files in four collections, all classified Requires additional configuration and non-runnable. No weights were read or modified.
- The base SGLang unit references `qwen38-dflash2:v1.2.3` and the registered Qwen identifier. The installed security drop-in starts existing gateway/network containers and attaches to the SGLang container. This is configuration evidence, not its running package version.
- Existing compatibility/gateway credential files are regular files with mode 0600. Contents were not printed or copied during diagnosis.
- Saved gateway rules require bearer authentication, contain no `/ready` exemption and do not rewrite paths/methods. Their current container mount could not be independently inspected.
- The Ollama CLI reports version 0.30.8. The running server version/inventory remain unverified. The supported GPU query returned unavailable.

Blocked by current sandbox permissions: systemd bus access, Docker socket inspection, Ollama `/api/version`, `/api/tags`, `/api/ps`, gateway HTTP probes and application loopback sockets. The user's reported active/resident SGLang state and `/ready` 404 were not independently reproduced here. Do not label these checks passed.

No service/container restart, model load/unload/switch, inference, runtime/NAS configuration change, weight modification or installer execution was performed.

## Remaining acceptance on the workstation

Run the fixture browser suite with working local sockets/tooling. Separately run the development application from the checkout on a random loopback port and inspect read-only status, details and library against the actual runtimes. Confirm current gateway bindings, SGLang package version and route implementation with authorized read-only access; do not rely on an image tag or upstream main branch as deployed-version evidence.

Confirm Ollama installed models match `/api/tags`, residents match `/api/ps`, provenance remains accurate and failures preserve independent evidence. Confirm authenticated metadata matches the registered SGLang model. Unsupported `/ready` must remain Loaded with Unverified inference readiness; auth/identity failures must retain process signals without claiming Ready. Never probe `/health` or `/health_generate` to resolve this gate without auditing the deployed implementation and separate approval for any inference.

Rendered acceptance still requires desktop/mobile, both themes, 200% zoom, touch/pointer chart interaction, keyboard focus and assistive technology, long identifiers and contrast. The harness automates part of that matrix; manual screen-reader/zoom/touch checks remain separate. Earlier user confirmation that charts/gauges rendered in Firefox is historical evidence and does not validate this revision.

Live lifecycle/recovery tests require separate explicit approval and an interruption window. Existing mocked adapters establish tested request/recovery contracts only. Memory estimates remain uncalibrated, connected clients cannot be reliably detected, process state does not prove inference readiness, and jobs/history are not crash-resumable. See the explicit release criteria in [the validation report](docs/audits/INTEGRATION_VALIDATION_REPORT.md).

## Premium visual refinement — 2026-11-03

This visual-only pass changes `web/style.css` and presentation code in `web/app.js`.
All 85 Python tests and all three JavaScript regression suites passed. Python,
JavaScript, installer shell syntax (without executing it), and diff whitespace
checks passed. No live lifecycle adapters or model operations were exercised.

Both Chromium and Firefox fixture commands remain **BLOCKED** (exit 2):
Playwright is not installed. A fresh socket probe also failed with PermissionError
before binding a random loopback port. The computer-use inventory returned no
apps or browsers. No development server replaced the stable application, and no
before/after screenshots could be captured.

The design detector returned `[]`; this does not establish rendered acceptance.
Calculated palette contrast for primary/secondary/accent text, warning text and
primary buttons ranged from 4.91:1 to 15.74:1 across the sampled light/dark pairs.
This is a source-color calculation, not a computed-style or rendered contrast audit.

Light/dark rendering, desktop and small-screen resizing, actual Firefox ARM64
rendering, focus visibility, dialog/loading-state readability and gauge appearance
remain **NOT VERIFIED** in a browser. Existing mocked focus, operation, gauge and
chart regressions pass, but cannot close these visual acceptance gates. Release
readiness remains withheld until the guarded browser suite and manual checks run
in an environment with the prerequisites described above.


## Public release security pass — 2026-11-03

Run the focused security regressions and optional read-only repository scanner:

```sh
python3 -m unittest discover -s tests -p test_security.py -v
python3 tests/security_scan.py
```

The complete Python suite now passes **101 tests**, including 16 security cases.
All three existing JavaScript suites pass with additional metadata/attribute
injection and crafted Demo Mode destination checks. Python compilation, JS
syntax, installer shell syntax and whitespace checks pass. No installer ran.

The security suite uses temporary state and NAS stand-ins and mocked runtime
adapters. It covers state symlink/hardlink/FIFO rejection, private permissions,
bounded logs, NAS directory substitution, metadata FIFO/deep JSON, enumeration
budgets, missing/invalid authentication, duplicate headers, body limits,
unsupported HTTP methods, path traversal, invalid model selection, worker caps,
thread failure release, unsafe runtime destinations and loopback startup.
Complete handler parsing uses fake byte-stream connections, not network sockets.
Existing tests retain forged Host/Origin, concurrent confirmations, one-use plans,
recovery, SGLang/Ollama contracts and demo/live isolation coverage.

Three filesystem cases were also run against isolated original-HEAD source:
symlink logging and directory escape reproduced; the FIFO test detected missing
nonblocking flags before performing a potentially blocking open. All pass after
correction. Every reproduction uses synthetic temporary files only.

The scanner emits location/type/fingerprint records, never matched credential
values. It covers all locally available Git objects, not remote-only releases or
artifacts; signatures are heuristic and require private triage. No maintained
secret scanner was installed. See the audit for the initial 11-commit/99-blob
inventory and false-positive classification.

Both browser commands still exit **2 / BLOCKED** because Playwright is missing;
a fresh loopback socket probe was denied. Real transport, rendered appearance,
Firefox ARM64 and effective host/runtime permissions remain unverified. The
[security report](docs/audits/PUBLIC_RELEASE_SECURITY_AUDIT.md) records
**INCOMPLETE_AUDIT**, not a publication or deployment security certification.


## Desktop UI follow-up — 2026-11-03

The current follow-up refines the existing seven-page presentation, responsive
model-card widths, evidence spacing, gauge proportions, workspace footers,
dark-mode interaction feedback, long-content wrapping and mobile targets.
Appearance controls and Library view selection now expose their selected state.
The frontend suite checks restored and toggled appearance state on both controls.

Validation: **101 Python tests passed**, all three JavaScript suites passed;
Python browser-fixture compilation, application/runner JavaScript syntax,
installer shell syntax and `git diff --check` passed. The installer was not run.
The optional read-only security scanner completed with heuristic findings in
existing history/fixtures; this is not a new security certification.

Both prescribed real-browser commands exited **2 / BLOCKED** because Playwright
is missing. A fresh random loopback bind failed with PermissionError and the
computer-use inventory returned no apps/browsers. No screenshots were captured.
The Impeccable detector exited 2 in degraded regex mode with advisory
palette/type/radius findings, including legacy CSS literals; custom-property
resolution, selector matching and computed contrast were unavailable. Its result
is not a passing visual audit. Existing recorded color calculations are historical,
not a rendered audit of this follow-up.

Real light/dark rendering, Firefox ARM64, desktop/mobile/zoom, keyboard and screen
reader acceptance remain **NOT VERIFIED**; release readiness is withheld.
[Desktop-window investigation](docs/design/DESKTOP-EXPERIENCE.md) documents the
recommended candidate without modifying the installed shortcut or backend.
No live model operations, runtime/service/Docker/NAS changes or installation ran.

## Desktop launcher — 2026-11-03

Required additional checks:

```sh
python3 -m unittest discover -s tests -p test_desktop_launcher.py -v
python3 -m py_compile desktop_launcher.py desktop/install_desktop.py
```

The full suite passes **117 Python tests**, including 16 desktop launcher cases.
All three JavaScript suites, Python compilation, JS/shell syntax and whitespace
checks pass. Generated desktop-entry validation also passes. The optional
read-only security scanner completed; its heuristic history findings are not a
new security certification. Desktop tests mock browser processes, HTTP transport and backend
adapters; temporary directories contain all test lock/state files. They cover
first launch, repeated clicks, an existing owner, reopening after window close,
startup failure and timeout cleanup, missing/failing browsers, paths with spaces,
shutdown/restart, lock contention and authenticated single-use handoff/expiry.
Supervisor tests verify loopback binding, click coalescing and HTTP shutdown.
They do not establish actual process/window behavior in a desktop session.

Both prescribed browser commands again report **BLOCKED**, exit 2 (Playwright
missing). A fresh random loopback bind reports PermissionError. Chromium and
Firefox version commands fail in snap-confine; mounted package manifests report
156.0.8078.47 and 157.0.1-1 respectively. CUA inventories no apps/browsers.
No screenshots or real desktop acceptance evidence were produced. No installer
was run, no account launchers changed, and no runtime operations were performed.

Installation is blocked by the current checkout-/tmp-only write permissions.
Real first launch/double-click/window close/restart, window dimensions/chrome,
GNOME icon/menu integration, themes/navigation/gauges, high-DPI and keyboard/mouse
acceptance remain **NOT VERIFIED**. Run the exact workstation validation command
and checklist in [DESKTOP-EXPERIENCE.md](docs/design/DESKTOP-EXPERIENCE.md).

## Native utility composition — 2026-11-03

The frontend now uses memory-led monitoring, a master-detail model manager,
registered/NAS/component inventory regions, instrumentation, profile disclosures,
log rows and grouped preferences. The three existing JavaScript suites pass with
added selection/filter/refresh/escaping and DOM action-order checks. The browser
fixture now selects model rows before exercising the unchanged simulated actions;
its original preflight, risk, failure and recovery coverage is retained.

All 117 Python tests pass. Python/JavaScript/shell syntax and whitespace checks
pass. Both browser runs remain BLOCKED (exit 2: missing Playwright), a fresh random
loopback bind is denied, and fresh CUA inventory contains no apps/browsers.
No rendered screenshots or real desktop evidence exist for this redesign.
The detector used degraded regex mode and emitted advisory design-token findings;
computed CSS/contrast were not evaluated. Independent source review identified
and prompted fixes for dark-library responsive specificity, polling focus loss,
inspector navigation focus and visual/DOM action order. This is not visual approval.

Manual acceptance must include list/inspector independent scrolling, focus through
five-second refreshes, model selection/filter fallback, keyboard Arrow/Home/End,
Library-to-inspector navigation, profile disclosures, both themes, narrow and short
windows, 200% zoom, gauge/chart readability and computed contrast. Do not run any
live lifecycle operation to test presentation; use the guarded fixture in Demo Mode.
Backend, authentication, runtime and desktop-launcher behavior were not changed.

### Premium glass finalization (2026-11-03)

Socket-free validation: 117 Python tests and the three JavaScript suites pass. Gauge band boundary and unknown-value assertions, compact card states, and a mocked details request that cannot trigger lifecycle actions are covered. Browser acceptance is BLOCKED: Playwright is not installed and loopback socket creation is denied. Firefox and the standalone desktop window are NOT VERIFIED. The existing browser fixture still contains master-detail expectations and needs updating before it can validate this revision; no browser pass is claimed. Validate dialog keyboard/focus behavior, both themes, responsive layouts, and computed contrast when the fixture and browser prerequisites are available. No live model operations were performed.

## Glass visibility correction — 2026-11-03

The 117 Python tests, three JavaScript suites and prescribed compilation,
syntax and whitespace checks passed. The fixture now targets the compact cards
and details dialog instead of the retired master-detail rows, checks computed
surface radius, shadow, border and background in both themes at five widths,
checks grid columns and details focus return, and captures Overview and dialog
screenshots. These new browser assertions have **not run**.

Both prescribed browser commands returned **BLOCKED** (exit 2: Playwright is
not installed); a fresh loopback socket attempt was denied and the computer-use
inventory contained no browser or application. No previous screenshots were
available in the workspace. Actual Firefox appearance, comparison, glass,
contrast, responsive layout and modal/grid acceptance remain **NOT VERIFIED**.
The design detector ran in degraded regex mode with palette/type/radius
advisories; it cannot evaluate computed styles or contrast. No live runtime or
lifecycle operation was performed. Run the guarded fixture and compare its
screenshots with the prior Firefox images on a permitted workstation before
claiming visual acceptance or release readiness.

## Complete premium desktop implementation — 2026-11-03

117 Python tests and all three JavaScript suites pass; compilation, JS/shell syntax
and whitespace checks pass. Inspector group/provenance assertions are included.
The browser runner now captures all seven pages, both themes and five widths
(1440/1024/768/390/320), plus search, empty, details and confirmation at each size.
It also checks the inspector evidence-region keyboard focus path. These browser
assertions have NOT executed: both commands exit 2 because Playwright is absent;
fresh loopback, system-browser, cached ARM64 browser and connector attempts are
blocked. No screenshots exist for this pass. Exact commands, evidence boundaries
and remaining accessibility gates are in
[FINAL_VISUAL_ACCEPTANCE.md](docs/design/FINAL_VISUAL_ACCEPTANCE.md).

## Desktop launcher verification follow-up

119 Python tests pass, including 18 desktop cases. New mocked regressions verify
that Stop timeout/permission errors and empty socket replies cannot claim clean
shutdown. All three JavaScript suites, prescribed compilation and JS/shell syntax
checks, desktop-entry validation and whitespace checks pass. Neither installer
was executed. Existing executable menu and localized desktop entries were
inspected read-only; their execution/trust remain NOT VERIFIED.

Both browser fixture commands report BLOCKED (missing Playwright). Fresh random
loopback binding is denied; Firefox/Chromium fail in snap-confine; graphical
inventory is empty. No real first-launch, repeated-click, close/restart, chrome,
dimensions, theme or input acceptance is claimed. Exact workstation validation:

```sh
cd /home/frederico/Projetos/ASUS-AI-Control-Center && python3 desktop_launcher.py
```

Follow the manual checklist in `docs/design/DESKTOP-EXPERIENCE.md`; live lifecycle
operations remain excluded. Release readiness remains withheld.

## Final emerald UI consolidation

119 Python tests and all three JavaScript suites pass. Navigation regressions now
require exactly six sections, reject the retired Performance route in favor of
Overview, retain chart pointer/keyboard/high-DPI coverage, and verify six workspace
articles. Compact-card/details, lifecycle guards, metadata, authentication and
security regressions continue to pass. Backend and desktop launcher files were
not changed during this UI pass. Compilation, JS/shell syntax and whitespace
checks pass; no installer or live model operation ran.

The guarded browser matrix now targets six pages, Overview telemetry and workspace
columns. Both commands below returned exit 2 / BLOCKED because Playwright is not
installed. Fresh graphical inventory is empty. No screenshots, real visual
comparison, computed contrast, keyboard/screen-reader or responsive acceptance
are claimed. The design detector ran in degraded regex mode with advisory
palette/type/radius findings; computed styles and contrast were unavailable.

```sh
node tests/browser_e2e.mjs
AI_MANAGER_E2E_BROWSER=firefox node tests/browser_e2e.mjs
```

When available, review both themes and all five fixture widths, workspace cards,
NAS disclosure content, Overview hardware overflow, compact cards and modal focus.
Release readiness remains withheld pending rendered acceptance.


## Midnight Blue + Graphite validation — 2026-11-03

**Overall UI acceptance: PARTIAL. Firefox fixture visuals validated; Chromium app
and authenticated HTTP browser acceptance BLOCKED.** This supersedes earlier
statements that no browser rendering was possible. It does not change historical
runtime readiness evidence or claim the release is READY.

Final results: **119 Python tests**, all three JavaScript suites, Python fixture
compilation, JavaScript syntax (including both browser runners), shell syntax and
`git diff --check` pass. The optional local security scanner also completed; its
existing infrastructure/test-fixture findings are advisory evidence, not a clean
security audit. It does not establish absence of secrets.

New frontend source tests cover one light/dark token authority, distinct glass
materials and solid fallbacks, responsive four/two/one monitoring layout, blue
history, four measured hardware fields, two runtime counts/unknown states, four
storage observations and visible collection compatibility. Existing gauge
calculations, unknown values, Details read-only behavior, modal focus, model
filters and protected lifecycle tests remain enabled.

### Socket-free rendered validation

`tests/browser_visual.mjs` opens only the actual `web/index.html?demo=1` file in
explicit Demo Mode. A route guard rejects network requests; no server starts and
no runtime or NAS adapter exists in this path. Four storage records and two
Activity events are clearly synthetic fixtures. The runner opens and cancels
the existing protected operation dialog; it accepts no lifecycle operation.

With an already provisioned Playwright package and Firefox binary:

```sh
AI_MANAGER_E2E_BROWSER=firefox node tests/browser_visual.mjs
```

If package resolution or browser discovery needs an existing installation, set
`AI_MANAGER_E2E_PLAYWRIGHT_MODULE` to its `index.mjs` and
`AI_MANAGER_VISUAL_EXECUTABLE` to its browser executable. No download/install is
performed. `AI_MANAGER_VISUAL_ARTIFACTS` selects an evidence directory; the default
is `/tmp/asus-ai-midnight-visual`. Chromium uses its sandbox; the runner never
disables browser security to get a pass. Missing prerequisites exit 2/BLOCKED;
assertion failures exit 1; success exits 0.

The completed Firefox matrix has six pages plus Details in both themes at 1440,
1024, 768, 390 and 320px: **70 matrix screenshots plus one confirmation screenshot**.
Assertions verify no horizontal overflow; four/two/one secondary columns; four
storage states and three valid native progress bars; no clipped strip content;
154px desktop strip; aligned gauge headings and non-overlapping scale/captions;
184px chart; keyboard history inspection; reduced-motion computed transition;
model grid/filter/search; Details Tab/Escape/focus return; six workspaces; and
zero network requests or page errors. Final captures were inspected and the four
first-round issues corrected. Modal captures use the viewport after scrolling to
the top to avoid Firefox full-page/fixed-position capture artifacts.

[Evidence and correction verdict](docs/design/MIDNIGHT_VISUAL_ACCEPTANCE.md) links
25 retained screenshots and results. The entire 71-image run remains in the local
artifact directory. The mechanical detector ran once in degraded regex mode;
type/radius advisories against the old DESIGN.md were reconciled in the new design
document. Parser/computed contrast and assistive-technology validation remain
unverified.

### Remaining GX10 gates

Run the guarded HTTP fixture on an environment permitting random loopback sockets:

```sh
node tests/browser_e2e.mjs
AI_MANAGER_E2E_BROWSER=firefox node tests/browser_e2e.mjs
```

Use `AI_MANAGER_E2E_PLAYWRIGHT_MODULE` if an existing external package is needed.
Here the default import exits 2 (module not on the project import path); with the
provisioned package, both browser selections exit 2 because the fixture cannot
create a socket (EPERM). Chromium's separate sandboxed file-render attempt also
fails: crashpad `setsockopt: Operation not permitted`, process SIGTRAP. Browser
connector profile conflict and empty computer-use inventory were rechecked.
No security restriction was bypassed.

On the GX10, review those HTTP screenshots in Chromium and Firefox, open Details
with the keyboard, inspect library disclosures, and check the four-disk strip at
1440px and its narrower two/one-column layouts. Inspect high-DPI rendering,
computed text contrast, zoom and reduced transparency, and measure scrolling and
idle CPU in the actual Chromium application window. Never point simulated
operation tests at the stable app. No live load/unload/switch, readiness inference,
installation or launcher change is needed for visual acceptance.

## Final color and glass validation — 2026-11-04

All 119 Python regressions and three JavaScript suites pass. Updated frontend source contracts cover the requested neutral palette and inherited dark gauge tokens, replacing an assertion that required a redundant selector. No telemetry tests were removed. Syntax/compilation and whitespace checks pass; installer syntax only, never executed.

The existing socket-free Firefox fixture passes five groups with 71 screenshots: six pages and Details, both themes at 1440/1024/768/390/320px, plus cancelled confirmation. All requests are restricted to local frontend files; no backend or adapters run. The desktop supporting strip is 176.5px with larger text, four aligned columns and no clipping; previous baseline was 154px. History remains 184px. Manual inspection covers both Overview/Manager themes, Details, Library, Workspaces, Activity, Settings and narrower captures. Twenty selected images plus results are retained in `docs/design/evidence/liquid-glass/`; the full matrix is `/tmp/asus-ai-liquid-final`.

Reproduce with an already provisioned Playwright module and Firefox executable (no installation):

```sh
AI_MANAGER_E2E_BROWSER=firefox AI_MANAGER_VISUAL_ARTIFACTS=/tmp/asus-ai-liquid-final node tests/browser_visual.mjs
node tests/browser_materials.mjs
python3 tests/contrast_samples.py /tmp/asus-ai-liquid-materials
node --check tests/browser_materials.mjs
python3 -m py_compile tests/contrast_samples.py
```

Set `AI_MANAGER_E2E_PLAYWRIGHT_MODULE` and `AI_MANAGER_VISUAL_EXECUTABLE` as described above when needed. `AI_MANAGER_MATERIAL_ARTIFACTS` overrides the material audit directory; pass the same directory to the Python analyzer. Pixel analysis additionally requires already provisioned Pillow. The audit records computed fills/blur and hides text fill for background captures. Three pixels beneath each visible text rectangle are compared against computed foreground using WCAG luminance. Hit testing excludes clipped modal content. Disabled controls, canvas text, offscreen content and hover/focus states are outside this sample. Results are a bounded contrast measurement, not full WCAG certification.

The first sample found Light Mode green badges at 4.28–4.49:1. After changing semantic text green to #176F4E (gauge bands unchanged), 654 visible text rectangles pass 4.5:1, minimum 5.01:1. The final Firefox screenshot matrix also passes.

Both HTTP browser commands were rechecked with the provisioned package: **BLOCKED**, exit 2, loopback socket access denied. Sandboxed Chromium file rendering: **BLOCKED**, exit 2, browser could not launch. Runtime version/readiness and NAS access were not exercised by this frontend-only task. No stable application, service, launcher, authentication or runtime configuration changed.

Full UI acceptance remains **PARTIAL**. Chromium, authenticated HTTP delivery, actual reduced-transparency OS preference, forced colors, assistive technology, 200% zoom, all scroll/interaction-state contrast and performance require workstation validation. No release READY claim follows from the passing Firefox Demo fixture.
