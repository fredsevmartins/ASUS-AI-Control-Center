# Installation and first launch

> Target: Ubuntu 24.04 ARM64 desktop. The repository is currently private, so cloning requires authorized GitHub access. Commands below refer to the reviewed development branch, not an officially released binary.

## Prerequisites

- Python 3 available as <code>python3</code> (Ubuntu 24.04 ships Python 3.12).
- GNOME or another Linux desktop environment.
- Chromium (preferred for app-window mode) or Firefox.
- Git for cloning.
- Optional running Ollama/SGLang if you plan to inspect or control registered models.
- Optional NAS mounts for the model library; these mounts are **not created by the app**.

Do not install Docker, Ollama, SGLang, GPU drivers or additional sudo permissions as a side effect of installing the dashboard.

## 1. Get the code

~~~bash
git clone --branch dev/premium-control-center https://github.com/fredsevmartins/ASUS-AI-Control-Center.git
cd ASUS-AI-Control-Center
~~~

If already cloned:

~~~bash
cd ~/Projetos/ASUS-AI-Control-Center
git switch dev/premium-control-center
git pull --ff-only
~~~

Pull only after reviewing any local uncommitted changes.

## 2. Install the desktop shortcut (recommended)

~~~bash
python3 desktop/install_desktop.py
~~~

This **does not** install or alter AI runtimes. It installs user-level GNOME launcher entries, backs up previous matching shortcuts and uses the checkout directory as its executable path. Keep the directory in place. Do not run with sudo.

Launch **ASUS AI Control Center** from your Applications menu or desktop icon. If the desktop refuses to launch it, right-click the shortcut and select **Allow Launching**.

## 3. Run directly (no shortcut required)

~~~bash
python3 desktop_launcher.py
~~~

This uses Chromium app mode if available, otherwise Firefox with ordinary browser chrome. The server is loopback-only and reuses a per-user owner process if one exists.

You can request a browser:

~~~bash
ASUS_AI_BROWSER=chromium python3 desktop_launcher.py
ASUS_AI_BROWSER=firefox python3 desktop_launcher.py
~~~

The browser selection may be reused by an already running supervisor. Stop it before changing preference.

## 4. Stop the owned application backend

~~~bash
python3 desktop_launcher.py --stop
~~~

Closing a desktop window alone keeps the local application backend available. This stop command affects only the launcher-owned AI Control Center backend, not Ollama, SGLang or your other services.

## 5. Browser-only development session

~~~bash
AI_MANAGER_PORT=0 python3 server.py
~~~

The Python server chooses a random localhost port and opens a session-authenticated page. Keep the terminal open; use Ctrl+C to stop. Do not share the launch URL or session token.

## 6. Optional runtime discovery

The application inspects existing local Ollama and SGLang services. It does not install or reconfigure them.

- Ollama model metadata is read from fixed local APIs.
- An existing SGLang gateway may require its **existing** bearer-credential file.
- Keep runtime origins on HTTP loopback addresses. Do not bypass gateway authentication.
- Unknown states and unsupported readiness endpoints are displayed as unverified rather than fabricated.
- Real load/unload/switch actions can interrupt connected clients and require explicit confirmation.

Refer to [SECURITY.md](../SECURITY.md) before changing any runtime access setting.

## 7. Optional NAS library

The application expects the configured model library at <code>/mnt/nas/AI-Models</code> and can show storage information for <code>/mnt/nas/Storage</code>. These are environment-specific paths, not paths created by the installer. Without a mounted library, inventory will be unavailable; the dashboard can still be used for other functions.

NAS scanning is read-only and does not make assets executable.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Shortcut opens nothing | Run <code>python3 desktop_launcher.py</code> in a terminal to inspect the sanitized error; ensure Chromium or Firefox is installed |
| Chromium app window unavailable | Try <code>ASUS_AI_BROWSER=firefox python3 desktop_launcher.py</code> |
| Restarted launch URL says expired | Reopen from the desktop icon; single-use launch tickets cannot be reused |
| Port/socket permissions error | Verify access in the actual local user desktop session; do not expose a network port as a workaround |
| Models show Unverified | A registered/runtime process is not proof of readiness; inspect existing gateway/service permissions without weakening security |
| External NVMe OFFLINE | Verify the correct mount in your own system; the app does not mount storage |
| Appearance resets after restart | A random localhost port may change browser-origin preferences |
| Need to revert desktop shortcut | Restore the timestamped backup created by <code>desktop/install_desktop.py</code> |

## Developer tests

~~~bash
python3 -m unittest discover -s tests -v
node tests/test_frontend.js
node tests/test_model_manager.js
node tests/test_model_intelligence.js
~~~

Optional browser tests require the project-local test dependencies and available Chromium/Firefox binaries:

~~~bash
npm ci
npm run visual:existing
~~~

Fixture tests use synthetic data and must not contact live runtimes. Do not use legacy <code>install.sh</code> to test a development checkout; that script copies application files into a separate historical v5 installation.

See the [desktop experience specification](design/DESKTOP-EXPERIENCE.md) and [testing policy](../TESTING.md).
