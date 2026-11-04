# User guide

## What AI Control Center does

AI Control Center is a local desktop interface for observing your workstation and deliberately managing **already installed** local AI models. It centralizes monitoring and runtime controls; it is not a model marketplace or cloud platform.

## Overview

Use the large gauges for unified-memory usage, GPU utilization and CPU utilization. The model counter reflects observed resident models, not the number of currently active inference requests. The memory chart shows a bounded recent history sampled at the application's refresh interval.

Secondary modules show:
- Runtime Status: current Ollama and SGLang observations.
- Storage Health: configured local and NAS storage availability and use.
- Hardware Telemetry: selected measured values.
- Quick Actions: navigation shortcuts.

Unknown telemetry remains unknown; a zero GPU reading does not guarantee no other activity.

## Model Manager

Each model card shows the observed runtime and state, available metadata and explicit actions.

- **Details:** open read-only information including model metadata and source/provenance where available.
- **Load:** request a model load after a fresh preflight and explicit confirmation.
- **Unload:** unload the selected resident model, potentially interrupting clients.
- **Switch:** select precisely which other model(s) may be stopped to make room.

The preflight estimates memory requirements and preserves a system reserve, but does not guarantee capacity. Existing external clients may be using a model without being detectable by the dashboard. Recheck state before and after disruptive actions.

**State interpretation:**

| State | Meaning |
| --- | --- |
| Installed / Registered | Model is known to the runtime/catalog |
| Loaded / Resident | Runtime evidence indicates weights or a model process are present |
| Ready | Only when a supported readiness contract establishes it |
| Unverified | Insufficient evidence, unsupported safe endpoint or incomplete runtime observation |
| Unknown / Error | Discovery or operation could not be reliably determined |

**Loaded is not proof of inference readiness.**

## Model Library

The library distinguishes runtime-registered models from read-only NAS assets. A collection of safetensors, JSON or tokenizer files is not automatically a runnable model. Compatibility labels are conservative and missing model components remain explicit.

## Workspaces

Informational cards summarize coding, scientific research, general AI, image, video and voice use cases. These are planning presets, **not automatic launchers**.

## Activity

Shows recent local operation events and error feedback. Log history is bounded, and prompts/model outputs are not intentionally stored by the dashboard.

## Settings

Switch between light/dark themes and inspect local connection information. Some browser appearance preferences can reset when the random localhost origin changes on restart.

## Demo Mode

The separately labeled demo is synthetic and isolated from real runtime/model actions. Use it for interface checks, never to establish live runtime readiness.

## Security reminders

- Treat launch links/tokens as private.
- Keep the application on localhost, not a public host.
- Never run the desktop installer with sudo.
- Do not grant broad Docker or root permissions to solve discovery errors.
- Do not rely on the application to recover an interrupted inference job.

See [Installation](INSTALLATION.md) and [Security](../SECURITY.md).
