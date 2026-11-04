# Contributor instructions

This is a local-first control panel for an existing workstation. Preserve the v5 installation and runtime configuration. Never run model load, unload or switch operations during development without explicit approval; tests must mock runtime operations. Do not modify services, Docker, Ollama, NAS configuration, or model files. Keep the HTTP server bound to loopback and retain API authentication. Avoid destructive Git commands and direct pushes to main. Treat NAS weights as discovered assets, not runnable models. Document limitations and verify changes with the tests in TESTING.md.

## Model intelligence and lifecycle contracts

Keep metadata as explicit value/source/confidence records; absent data is not zero. Ollama residency is not proven inference readiness. Never replace non-generating SGLang probes with `/health` or `/health_generate` without auditing the deployed version and explicit approval for any inference. A missing `/ready` endpoint is an operational limitation, not permission to modify the runtime.

All external lifecycle requests must use a single-use preflight plan with explicit confirmation and risk acknowledgement. Revalidate identities, residency and capacity before mutation; preserve process and cross-instance locking. Recovery may act only on selected stops and must verify the previous selected state before reporting recovery. Do not automatically clean up a partially loaded target. Tests must mock all lifecycle adapters and keep advisory-lock files and logs in temporary directories. Run all suites in TESTING.md after meaningful changes; do not run the installer as validation.

## Integration validation and evidence

Read `docs/audits/INTEGRATION_VALIDATION_REPORT.md` as historical evidence, then recheck current environment access. Do not equate an image tag or upstream source with the deployed SGLang package/version. Unsupported or inaccessible non-generating readiness remains Unverified, with independent process/residency signals retained. Never substitute a generating health endpoint to satisfy acceptance.

Preserve independent Ollama installed/resident observations, unknown installation for orphan residents, metadata provenance and current allocation/context over cached details. Unknown target size or reclamation is not zero; enforce the system memory reserve even for unknown requirements. Recheck plan expiry in the worker and model identity before mutations.

Keep Host/Origin/session checks and runtime-origin restrictions intact. Runtime credentials must not be embedded in endpoint URLs. Never copy real session tokens or runtime credentials into logs, screenshots or reports; test tokens must be clearly synthetic and never valid in a live instance. Preserve the existing authenticated launch mechanism without exposing its token. The browser fixture must block all live runtime and NAS adapters. Start development on a separate random loopback port without replacing the stable application. Report browser/runtime tests as BLOCKED or NOT VERIFIED when prerequisites or permissions are missing; never count them as passed or classify the release READY while required acceptance gates remain unverified.
