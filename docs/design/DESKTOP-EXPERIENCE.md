# Standalone desktop window investigation

Date: 2026-11-03. Status: **recommended approach documented; compatibility NOT VERIFIED**.

The simplest candidate is the already installed Chromium browser's application
window mode, selected through Python's existing `webbrowser` launcher. This needs
no Electron, webview package, new runtime, server modification or network binding
change. Chromium defines the `--app` switch for application mode in its
[official source](https://chromium.googlesource.com/chromium/chromium/+/master/chrome/common/chrome_switches.cc).
Python 3.12 documents URL substitution in a `BROWSER` command containing `%s` in
[the webbrowser documentation](https://docs.python.org/3.12/library/webbrowser.html).
Those contracts support the candidate; they do not establish this host's behavior.

A future checkout-only trial could select the browser with
`BROWSER='chromium --app=%s' python3 server.py`. This is a proposed command,
not an implemented or validated launch path. The existing server creates its
random loopback URL and supplies the session credential directly to the browser.
Do not substitute a saved URL, hardcode a token/port, print the expanded command,
or put a credential into a desktop file. Limit BROWSER to the application process;
do not change the global default browser. The existing authentication and
Host/Origin/session checks must remain enabled.

Read-only inspection confirms aarch64 and the presence of `/snap/bin/chromium`
and `/usr/bin/firefox`. A fresh random 127.0.0.1 bind failed with PermissionError;
Playwright is missing and computer-use inventory exposes no browser. Therefore
there is no evidence for a working app window on this Ubuntu ARM64 desktop,
including its Snap/session/window-manager integration. No browser or system
configuration was changed. The existing desktop shortcut, installer and Python
backend remain untouched.

Before implementing launch integration, validate with the guarded browser
fixture from TESTING.md on a separate random loopback port, synthetic session
credentials and blocked live runtime/NAS adapters. Verify a normal resizable
window with no address bar/tabs, all seven destinations, keyboard focus, both
themes, close/relaunch behavior and the existing authentication rejection checks.
Window closure may leave the Python backend running; document and verify its
existing process lifetime rather than introducing a new process supervisor.
Also check theme preference behavior when random ports produce new browser
origins. Keep the stable application and shortcut available throughout testing.

If that succeeds, a separately reviewed launch-only wrapper could set BROWSER
for the existing Python entry point, passing its authenticated URL through the
current mechanism. Preserve the original shortcut as the fallback. Do not use
fullscreen/kiosk as a substitute for an ordinary desktop window, disable browser
sandboxing, expose remote debugging, or relax loopback/authentication constraints.
No implementation is shipped because the user's compatibility gate remains open.
