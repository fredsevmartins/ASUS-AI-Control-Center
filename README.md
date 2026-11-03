# ASUS AI Control Center v5

Local-first workstation dashboard for the ASUS GX10 (ARM64 Ubuntu). macOS-inspired design built with zero external web dependencies. The UI is English-only; it is served on a random **localhost-only** HTTP port and opens in the default browser. No cloud services, CDNs, remote calls, Python packages, npm build, or desktop environment replacements required.

## Install

```bash
cd ~/Downloads
unzip -o ASUS-AI-Model-Manager-v5.zip
bash ai-model-manager-v5/install.sh
```

Open **ASUS AI Control Center v5** from the desktop or application menu. Keep the launcher running as long as you use the panel. To start from a terminal: `python3 ~/.local/share/asus-ai-model-manager-v5/server.py`.

## Safety / scope

- Installs **alongside** v4; does not replace its launcher or scripts.
- Uses existing `~/.local/bin/qwen38-control` for SGLang; no new sudo permissions.
- Calls Ollama's local API and the existing Ollama CLI; does not pull, delete, or migrate models.
- NAS inventory is read-only and scans at most 1,800 directory entries to depth 4, ignoring symlinks.
- All writes to runtimes require explicit UI confirmation; switch can ask which active models to stop.
- Rollback is best effort. Busy indicator reports running work; health is not inferred solely from service activation.
- Workspaces are **informational presets** in v5, not one-click execution.
- Metrics are sampled while the UI is open; they are ephemeral and not retained across runs.
- GPU memory is unified on GB10. `nvidia-smi` data may be unavailable. SGLang process memory is not individually measured.
- **Local security:** ephemeral random browser token for API calls; bound to `127.0.0.1` only. Do not expose the port using a reverse proxy.

## Test

```bash
cd ~/Downloads/ai-model-manager-v5
python3 -m unittest discover -s tests -v
```

The tests use fake processes and never invoke live systemd/Ollama actions. Verify read-only dashboard first, then optionally perform a controlled model load/unload with no active clients. Real hardware integration and UI E2E are not validated by these tests.

## Additional hardening before wider use

For production-grade automation: runtime-aware readiness probes, persisted job state, background service ownership, clear client-use detection, cancellation handling, model memory attribution, local socket or stricter API authentication, and real-browser E2E coverage are needed.
