# Contributor instructions

This is a local-first control panel for an existing workstation. Preserve the v5 installation and runtime configuration. Never run model load, unload or switch operations during development without explicit approval; tests must mock runtime operations. Do not modify services, Docker, Ollama, NAS configuration, or model files. Keep the HTTP server bound to loopback and retain API authentication. Avoid destructive Git commands and direct pushes to main. Treat NAS weights as discovered assets, not runnable models. Document limitations and verify changes with the tests in TESTING.md.

## Model intelligence and lifecycle contracts

Keep metadata as explicit value/source/confidence records; absent data is not zero. Ollama residency is not proven inference readiness. Never replace non-generating SGLang probes with `/health` or `/health_generate` without auditing the deployed version and explicit approval for any inference. A missing `/ready` endpoint is an operational limitation, not permission to modify the runtime.

All external lifecycle requests must use a single-use preflight plan with explicit confirmation and risk acknowledgement. Revalidate identities, residency and capacity before mutation; preserve process and cross-instance locking. Recovery may act only on selected stops and must verify the previous selected state before reporting recovery. Do not automatically clean up a partially loaded target. Tests must mock all lifecycle adapters and keep advisory-lock files and logs in temporary directories. Run all suites in TESTING.md after meaningful changes; do not run the installer as validation.
