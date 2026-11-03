# Desktop experience

Date: 2026-11-03. Implementation complete in the checkout; installation and real
GX10 desktop acceptance **BLOCKED / NOT VERIFIED**. This is not a READY release.

## Mechanism and environment evidence

`desktop_launcher.py` uses installed Chromium/Chrome `--app` with an initial
1440 × 960 window request. It does not use kiosk, Electron, a new browser package,
a custom profile or system services. Chromium's supported switches are recorded
in its [official source](https://chromium.googlesource.com/chromium/chromium/+/master/chrome/common/chrome_switches.cc).
Firefox falls back to `--new-window` with width/height hints, following
[Mozilla's command-line documentation](https://firefox-source-docs.mozilla.org/browser/CommandLineParameters.html).
Firefox chrome remains visible; no Chromium-style Firefox app flag is used.

Fresh inspection found aarch64, Python 3.12.3, `/snap/bin/chromium`,
`/usr/bin/firefox`, `/usr/bin/zenity`, DISPLAY `:1`, and an X11 session indicator.
The mounted Snap manifests report Chromium **156.0.8078.47** and Firefox
**157.0.1-1**. These are package metadata, not verified running versions: both
`--version` executions failed in snap-confine due to missing permitted capability
`cap_dac_override`. No Chrome executable was found. A fresh random loopback bind
failed with PermissionError. Computer-use returned no apps or browsers.

The existing menu entry points directly at
`~/.local/share/asus-ai-model-manager-v5/server.py`; it starts a fresh backend on
every invocation. The stable files and that installed shortcut were not changed.
No matching Control Center desktop file was present in `~/Desktop` at inspection.

## Startup and shutdown

The desktop entry runs Python without a terminal. The short-lived launcher
contacts a private Unix control socket. If absent, it starts a detached supervisor
with a 15-second startup deadline (individual socket calls are bounded). A
per-user `flock` elects exactly one owner even during concurrent starts. The owner
hosts the existing `server.LocalHTTPServer` and handler on a random **127.0.0.1**
port in the same process; there is no additional backend child to orphan.
A static CSS HTTP probe checks transport readiness without querying runtimes.

Clicks within two seconds are coalesced. Later clicks reuse the same backend but
may open another window; reliably focusing an existing Chromium app window is
not implemented. Independently started stable v5 servers are neither adopted nor
terminated: they lack the private control protocol and must remain undisturbed.

Closing the browser retains the backend, matching the existing application's
lifetime. Reopen with the icon. Use the menu entry's **Stop ASUS AI Control Center**
action or `python3 desktop_launcher.py --stop` to shut down the owned backend.
Stop refuses while the application's operation state is busy. SIGINT/SIGTERM
also close the HTTP/control sockets and release the lock. Browser sessions are
never killed. Restart generates a fresh session token and random port.
There is no logout service integration; stop explicitly when finished.

Missing browsers, immediate browser failures and backend startup failures produce
a Zenity error dialog when available, otherwise a stderr message. Initial browser
failure shuts down the newly started backend. A browser command handing off to
an existing process can return success without proving a window opened. Failures
after that handoff cannot be reliably detected here.

## Installation (user account only)

Run from a normal GX10 terminal, after the acceptance checks below:

```sh
cd /home/frederico/Projetos/ASUS-AI-Control-Center
python3 desktop/install_desktop.py
```

This dedicated installer writes menu and desktop entries with the exact name
**ASUS AI Control Center**, the bundled gauge icon and executable permissions.
It points at this checkout, so keep the checkout at this path. It preserves
existing matching launchers as timestamped `.backup-*` files and leaves the v5
installation and differently named legacy shortcuts intact. It attempts GNOME's
trusted metadata; if necessary, right-click the icon and choose **Allow Launching**.
No sudo or packages are needed. Do not use legacy `install.sh` for this integration.
The current workspace may write only inside the checkout and `/tmp`, so account
installation could not be performed here. Neither installer was run as validation.

To restore: stop this backend, restore the timestamped menu/desktop backups, and
remove only the newly created desktop entry if no previous one existed. The
stable v5 application remains available throughout.

## Security

The supervisor imports the unchanged backend, preserving fresh session tokens,
Host/Origin/Fetch Metadata checks, API session authentication, CSP, request
validation and runtime restrictions. The desktop-only handler accepts a random
single-use launch ticket for 30 seconds and renders via the existing authenticated
handler after validating the local request. Only this short-lived ticket is in
browser arguments/history; the reusable session token exists in backend memory
and the authenticated page, never launcher arguments, desktop files, logs or
browser configuration. Same-user process observers could race to redeem a ticket
before the browser; it remains a temporary bearer credential. It is not safe to
share launch links. Browser extensions with page access remain within the browser
trust boundary. No dedicated profile or extension policy is imposed.

Control files live in a private owner-checked runtime directory; no token is
written there. Socket access is restricted by directory permissions. Existing
lock paths reject symlinks and multiple hardlinks. HTTP remains loopback only.
No runtime lifecycle, credentials, services, Docker, NAS or weight files changed.

## Compatibility and known limitations

- Chromium app mode is requested, **not visually verified** on this GX10. Hidden
  tabs/address/bookmarks controls, initial dimensions, minimize/maximize, resizing,
  GNOME grouping and high-DPI behavior remain acceptance gates.
- Firefox is a conventional separate browser window, with chrome visible.
- `ASUS_AI_BROWSER=firefox python3 desktop_launcher.py` selects the fallback;
  stop an existing supervisor first to change its browser preference. Set
  `ASUS_AI_BROWSER=chromium` to require a Chromium-family browser.
- Refreshing/restoring a consumed launch URL is rejected. Reopen using the icon.
  An expired ticket likewise requires a fresh launch. This deliberately avoids
  persisting the reusable credential for refresh/session restore.
- The existing random-port design means browser-origin theme preferences may reset
  after backend restart. Light/dark controls continue to work within the session.
- The existing seven views, gauges, Model Manager, themes and responsive CSS are
  unchanged. Actual rendering, keyboard/mouse interaction and high-DPI remain
  unverified; unit tests do not establish desktop appearance.

## Validation and troubleshooting

Run the automated suites in `TESTING.md` first, including the guarded browser
fixture, which blocks all live runtime/NAS adapters. No installer is a test.
Then the exact real desktop launch command is:

```sh
cd /home/frederico/Projetos/ASUS-AI-Control-Center && python3 desktop_launcher.py
```

This opens the actual checkout with read-only discovery; do not request model
operations. Verify 1440 × 960 sizing or screen-constrained sizing, no Chromium
chrome, normal window controls, resizing/high-DPI, both themes, all seven views,
Model Manager and gauges. Double-click repeatedly, close/reopen, stop and restart.
Check only process names/PIDs (not full browser command lines containing tickets)
and confirm one `desktop_launcher.py --serve` owner. Independently running v5
processes are expected to remain separate. Confirm unauthenticated API rejection
with synthetic fixtures, never copy a real token into a report or screenshot.

For Snap errors, test browser startup in the actual desktop session. This launcher
does not bypass Snap/browser sandboxes. For startup timeout, check Python and
local socket permissions; stale control sockets are replaced under the owner lock.
If no dialog appears, run the launch command in a terminal to see sanitized error
feedback. Never make the server public to work around socket restrictions.
