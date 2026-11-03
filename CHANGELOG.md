# Changelog

## Unreleased

- Reject malformed operation payloads before starting a worker, and recover if a worker cannot start.
- Explicitly warn when a failed switch may have left the target partially loaded.

- Redraw the memory timeline when its page becomes visible.
- Block SGLang operations if service or container state cannot be observed or they disagree; report degraded runtime checks.
- Exclude Linux guest counters already included in CPU user time.
- Add mocked state, rollback and API regression coverage and a frontend navigation regression check.
- Document architecture, safety constraints, test coverage and prioritized work.
