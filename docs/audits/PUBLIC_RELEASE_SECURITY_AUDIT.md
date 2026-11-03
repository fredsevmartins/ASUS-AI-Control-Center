# Public release security audit

Date: 2026-11-03. Audited branch: `dev/premium-control-center`, starting HEAD `94b01f4`. Corrections described below are working-tree changes, not changes to the installed application. The initial working tree was clean; the premium redesign was already committed and is preserved.

## Executive summary and decision

**INCOMPLETE_AUDIT** for the complete publication decision. No confirmed P0 or P1 vulnerability or live credential was found in the inspected source and local Git objects. Four P2 weaknesses were corrected and covered with isolated regressions. This is not a claim of complete security.

The inspected local source/history has no identified secret-based publication blocker. However, remote tags, releases, uploaded artifacts, security settings and effective workstation privilege rules could not all be verified. The GitHub connector confirmed private visibility and two branches; it did not expose the remaining controls. Browser/real-socket acceptance is blocked. Keep the repository private until the publication checklist is completed. No visibility, service, container, NAS, credential or installed-application change was made.

Publishing source does not open a workstation port. Deployment safety is a separate decision: the application is a same-user loopback utility, not a sandbox for hostile local users and not a network management server. The current `main` branch is an older implementation and must not be presented as the audited release.

## Threat model

| Actor / condition | Actual exposure |
| --- | --- |
| Internet reader of the public repository | Can read committed source, history and published metadata; gains no network route to the workstation merely from publication. |
| Malicious website | Can attempt browser connections to loopback; exact Host/Origin/Fetch Metadata checks, no CORS, session token and JSON requirements prevent demonstrated lifecycle authorization. Browser connection pressure is still possible depending on browser protections. |
| Untrusted local process | Can reach loopback and forge HTTP headers. It still needs the session token for APIs; connection exhaustion does not require a token. |
| Same-user compromise or malicious browser extension | May obtain the launch token, modify user-owned code or access files directly. This application cannot isolate itself from its own OS account. |
| Writer to the model share | Can influence discovered metadata and race filesystem entries. Scanning must not follow replacement links or open devices. |
| Compromised application process | Inherits the user's filesystem, NAS and existing runtime privileges. Read-only application code is not an OS-enforced read-only mount. |
| Administrator / Docker-capable account | May have host-wide authority independently of this application; exact effective permissions remain unverified. |

## Scope and methodology

Reviewed backend (`server.py`, `core.py`, `intelligence.py`), frontend HTML/CSS/JavaScript, installer, tests, tracked configuration and all documentation. Read the integration report as historical evidence, then rechecked current access. Used source tracing, a redacted heuristic scanner, Git object inspection, metadata-only host observations, mocked HTTP byte streams, temporary filesystem race fixtures and regression suites. No unrelated NAS directory was enumerated; tests use temporary synthetic files. No inference, real model lifecycle call, generating health endpoint, installer execution or network scan occurred.

`tests/security_scan.py` is a dependency-free, read-only audit utility. It scans repository files, all locally stored blobs/commits/tags (including unreachable objects), refs/reflogs and selected Git metadata. Output contains location, type and truncated SHA-256 fingerprint, never matched credential text. Patterns cover private-key markers, common provider tokens, credential URLs, literal credential assignments and selected infrastructure identifiers. This is heuristic coverage, not proof that arbitrary secrets are absent. Gitleaks, TruffleHog, detect-secrets, Bandit and pip-audit were unavailable; none was installed.

## Repository and Git history findings

- Local database: 11 commits, 99 blobs and 32 trees; non-shallow repository. `git fsck --full --no-reflogs` completed successfully. Two local branches and matching remote-tracking refs; no local tags. All locally stored blob/commit/tag contents were scanned, not only HEAD. Largest blob: 42,553 bytes. No model weights, archives, vendored dependencies or executable binaries identified in tracked source. No tracked symlinks, submodules, Git LFS configuration or GitHub workflow files. No active non-sample executable Git hook was found locally.
- GitHub metadata confirmed private visibility, default branch `main`, and branch names `main` / `dev/premium-control-center`; pagination exhausted. Remote branch content equivalence, tags, release assets, workflow artifacts/logs, forks and deleted server-side objects were not independently established. CLI GitHub access failed; available connector metadata did not include secret-scanning, push-protection, branch-protection or private vulnerability reporting settings.
- All initial literal credential hits were synthetic browser fixture tokens or intentionally invalid runtime URL fixtures. Examples: `tests/browser_e2e.mjs:13` fingerprint `sha256:932c07544150`, `tests/browser_server.py:18` fingerprint `sha256:b7191f546f1c`; credential URL fixtures in `tests/test_intelligence.py` and `tests/test_sglang.py` have fingerprints `sha256:7f8183fd094a` and `sha256:48ad5a736dfe`. Historical copies have the same fingerprints. No valid credentials were copied into this report.
- **P3 PUB-01 — infrastructure/privacy identifiers:** README contained a personal checkout path, replaced with `/path/to/ASUS-AI-Control-Center`. Historical commits still contain that path. Historical audit/test documentation includes a host identifier; service names, mount paths, configured model identifiers and two commit-author identities are also discoverable. These are privacy disclosures, not authentication secrets or a demonstrated route to the host. Owner review before publication is required; no history rewrite was performed. Evidence: scanner infrastructure hits, README diff and existing integration report. Status: current README corrected; historical/privacy review outstanding.
- The old `main` tip (`a7a34de`) lacks the later Host/Origin guards, single-use preflight/locking and readiness protections. Old versions also contain the logging and NAS weaknesses corrected here. Public code history does not execute itself, but users installing old `main` would not receive these fixes. Publish a reviewed current release through the normal branch/PR process; do not recommend historical commits for installation.
- `.gitignore` now additionally excludes common private-key containers, operation logs, lifecycle lock and generated browser reports. Ignore rules do not remove already tracked files or protect against `git add -f`.

No confirmed exposed live secret requires rotation based on this evidence. If a subsequent scan finds a valid secret, revoke/rotate it before publication, assess its historical exposure and only then plan an explicitly approved history cleanup. Deleting a current file alone is insufficient.

## Confirmed application findings and corrections

| ID / severity | Component and root cause | Exploitation prerequisites and effect | Smallest correction | Evidence / verification |
| --- | --- | --- | --- | --- |
| FS-01 / P2 | `core.log_event`, `server.activity`, state/lock handling used pathname opens; logging followed links and chmodded after writing. | Attacker can plant/replace state entries, normally requiring same-user access or unsafe existing directory permissions. Can append to or change mode of a user-writable target, redirect activity reads, or hang on a FIFO. No demonstrated remote privilege escalation. | Pin final state directory with `O_DIRECTORY|O_NOFOLLOW`; require current ownership and private directory permissions; open relative files with `O_NOFOLLOW|O_NONBLOCK`, require regular/current-owner/single-link files; create logs at 0600 before writing; bound all record fields. Locks use the same helper. | `tests/test_security.py`, `FilesystemSecurityTests`: symlink, hardlink, FIFO, permissive directory and bounded-log cases PASS. Symlink append reproduced against original HEAD, then rejected after correction. |
| NAS-01 / P2 | `_nas_scan` checked a directory entry but later reopened its pathname. | Share writer races replacement with a directory symlink, then an authenticated operator scans. Can enumerate recognized filenames and selected JSON metadata outside the intended root, limited by application account access. Does not provide arbitrary file download or execute weights. | Pin the root descriptor; reopen each relative component with directory/no-follow flags; open JSON relative to its pinned directory. | Directory-replacement regression exposed a synthetic off-root filename on original HEAD and rejects it after correction. PASS. |
| NAS-02 / P2 | JSON metadata file could become a FIFO/device after `is_file`/stat. | Share writer races replacement before an authorized scan; FIFO open could indefinitely occupy a request worker. | Nonblocking no-follow open, descriptor regular-file validation, bounded read, malformed/non-object/recursive JSON handling. | FIFO test checks nonblocking flags before opening, so the vulnerable baseline is detected without hanging. Baseline failed, corrected test PASS. No actual NAS file touched. |
| HTTP-01 / P2 | Unbounded `ThreadingHTTPServer` workers and no accepted-connection timeout. | Local socket access, or browser connections allowed by the browser, can hold incomplete requests without an API token and allocate threads. | `LocalHTTPServer`: at most 16 active request threads, excess connections closed before thread creation, 10-second socket inactivity timeout, slot release on failure and shutdown. | Mock dispatch, timeout setup, slot release and loopback startup tests PASS. Real-socket load behavior BLOCKED. This bounds resources; it does not prevent an attacker continuously occupying all 16 slots. |
| HTTP-02 / P3 | Duplicate security headers, incomplete body handling and response policy inconsistency. | Crafted authenticated/loopback requests exploit ambiguity or malformed input; no proven lifecycle bypass. | Reject repeated Host/Origin/token/length/type/encoding/Fetch Metadata headers; require exact body length; handle recursive JSON; nosniff/no-referrer/no-store on all response paths; CSP `form-action 'none'`. | In-memory full handler byte-stream tests and existing validation suites PASS. Classified as hardening, not a proven authorization bypass. |

The filesystem fixes are Linux-specific standard-library calls, compatible with the stated Ubuntu ARM64 target. Existing state directories with permissions broader than 0700 now fail closed; no existing directory was chmodded automatically. An operator should inspect and explicitly approve any permission repair if necessary. Trusted parent directories and the OS account remain part of the trust boundary. Descriptor anchoring does not stop an administrator changing mounts or an already compromised account from reading files directly.

## Backend security assessment

Authentication uses a fresh `secrets.token_urlsafe(32)` per process and constant-time API comparison. Every runtime/status/detail/library/activity API requires the token. The main document requires the launch token; only fixed CSS and JavaScript assets are unauthenticated. No arbitrary static path mapping, file upload, model import, hidden admin endpoint, pickle/YAML deserialization or shell-evaluated model name was found.

Requests require exact `127.0.0.1:<port>` Host. Supplied Origin must match; cross-site/same-site Fetch Metadata is rejected. Missing Origin is allowed for non-browser clients, so these headers are not substitutes for authentication. No CORS permission is emitted. Unsupported methods return 501 without dispatching lifecycle code. POST bodies are capped at 8192 bytes, identifiers/stops are bounded and checked against current inventory. Forged Host/Origin, missing/invalid tokens, malformed JSON, duplicate headers, unsupported methods and traversal paths are covered by tests.

Lifecycle mutation requires an exact unexpired single-use preflight, explicit confirmation and risk acknowledgement. In-process state locking and cross-instance advisory locking remain intact. Worker expiry, fresh identities/residency/capacity and reserve checks remain intact. Recovery only acts on selected stops; partially loaded targets are never automatically removed. External client/runtime races remain unavoidable and are not represented as a transactional guarantee.

Runtime destinations require literal HTTP loopback origins and explicit ports; credentials, remote addresses, paths, queries and fragments are rejected. Environment proxies and redirects are disabled. Metadata reads are limited to 2 MiB; credential reads are bounded separately. No endpoint change or generating probe was used. A missing SGLang `/ready` remains Unverified.

**Remaining P2 operational risk SESSION-01:** the authenticated launch URL remains in browser history and may be visible to browser launch helpers, extensions, screen capture or same-user process inspection. The token is also necessarily in authenticated document memory. A stolen token authorizes the API, including deliberate plan confirmation. Prerequisite: token exposure/local compromise, not merely source publication. No-referrer, no-store, suppressed access logs and no token in startup stdout reduce leakage; theme is the only localStorage value. The existing launch mechanism was preserved. Treat launch URLs as credentials and restart the app if one is exposed. A redesigned token bootstrap is out of this minimal audit scope and would need compatibility review.

Errors can include runtime/model names and controller diagnostic text for the authenticated operator and private log. No confirmed secret-bearing error was observed; control local helper output and do not include secrets in runtime errors. Logs are record/read bounded but not rotated. Runtime socket inactivity timeouts are not end-to-end deadlines; slow peers, mounts and external subprocess behavior remain availability limits.

## Frontend assessment

Model names, keys, provenance, errors, operation messages, library paths and activity data pass through `escapeHTML` or textContent. Dynamic numeric telemetry is derived from local numeric observations. No eval, remote scripts, remote fonts, external navigation destination from model metadata or unsafe dynamic event-handler construction was found. CSP restricts scripts/styles/connections to self and blocks framing, objects, base changes and forms. Synthetic tag/attribute payload tests pass; real-browser CSP/XSS execution remains NOT VERIFIED.

Demo Mode is chosen at document initialization and routes the shared request function to simulation before fetch. Existing tests cover simulated status/details/library/preflight/actions/failures and zero network calls; new crafted URL/query cases also make zero fetch calls. Demo is a UI isolation mechanism, not a second server authorization domain: a person holding the live session token can independently call live APIs or reload without `demo=1`. They still require valid live preflight/confirmation. No claim is made that the demo query revokes the live token. The guarded browser fixture forbids live runtime and NAS adapters regardless of query mode.

No application HTML, CSS or frontend behavior changed in this security pass; only frontend regression tests expanded. The premium appearance is preserved.

## Privilege and system assessment

Read-only observations: the existing controller is a regular mode-0700 file. Its source dispatches fixed start/stop/status cases, sets one fixed service name and uses `sudo -n /usr/bin/systemctl` for start/stop; no eval was found. Backend subprocess calls use argument arrays, never `shell=True`. Model identifiers are passed as JSON to fixed Ollama routes. The controller path is user-owned and user-controlled; this is not a safe privilege boundary against that same user's compromise.

The service's readable base/drop-in configuration retains the registered model metadata and replaces startup with the existing private-network/gateway containers and attachment to the existing model container. Base image tags are not evidence of a deployed package/version. Relevant unit/config ownership appeared mapped in this sandbox, so authoritative host ownership could not be certified. The credential file's mode was observed as 0600; its contents were not inspected or printed. Home and `.local` metadata limited traversal; `.local/bin` was group-writable but its private parent restricts unrelated users. Effective group/ACL access requires workstation review.

`systemctl is-active`, limited Docker inspect and `sudo -n -l` failed. The named sudoers file was unreadable. Docker socket mode was 0660, but access/daemon behavior could not be established from mode alone. Active HAProxy bindings/rules, accepted credential, container mounts and deployed SGLang/Ollama versions remain NOT VERIFIED. No privilege escalation or controller action was attempted.

Proposed administrator-only checks/changes, **not applied**:

1. Verify effective sudo rules permit at most `/usr/bin/systemctl start qwen38-sglang.service` and `/usr/bin/systemctl stop qwen38-sglang.service` for the intended operator; avoid wildcard arguments, sudo shell/controller execution, unrestricted Docker or `SETENV`. Keep `env_reset` and a trusted `secure_path`. Tightening rules may break the existing controller; review with the service owner before changing them.
2. Verify service units/drop-ins, gateway configuration and privileged executables are root-owned and not writable by untrusted groups. Keep user-owned controller ancestors private. Do not move/change the running service as part of this audit.
3. Determine whether the account has root-equivalent Docker daemon authority. The app uses fixed inspect operations, but account compromise can use any authority granted by the daemon. Removing group/socket access may break existing workflows; any least-privilege replacement requires separate design and approval. See [Docker's security guidance](https://docs.docker.com/engine/security/).
4. Verify the gateway publishes loopback only and authenticates metadata and readiness without a generating-health exception. Do not weaken authentication to make probes pass.

## NAS assessment

Only mount metadata for the two specified shares was checked; both appeared mounted. No personal files, weight contents or unrelated directories were scanned. The application only inventories the model share; the archive share receives statvfs capacity checks, not directory enumeration.

Inventory retains 1800 examined entries (including hidden entries), at most three levels below root, 32 JSON reads of at most 262145 characters each after a 262144-byte eligibility check. All weights use stat only. JSON parsing is limited to selected metadata fields, never model deserialization. Discovered symlinks are skipped and replacement directory/file links now fail closed. Results expose relative recognized filenames, file sizes and selected configuration to authenticated API clients. There is no download, write, delete or executable adapter for NAS assets.

A hung mount may still block kernel filesystem calls. The new HTTP cap limits thread growth, not mount latency. A compromised process can use whatever NAS access the OS account already has, including writes if the mount/account permits them; the application does not install an OS sandbox. NAS credentials, share ACLs and write permissions were not inspected or altered. Consider a separately approved read-only identity/mount for inventory if the operational environment requires stronger containment; changing existing mounts could disrupt model workflows.

## Installer and supply chain

`install.sh` uses local source files, Python syntax compilation and user-local install paths. No download, remote shell, package install, sudo, service modification, credential copy, model deletion or backup cleanup exists. It creates a dated v5 backup before replacing installed files and leaves v4 separate. `bash -n install.sh` passed; the installer was not executed, including in temporary fixtures.

The installer assumes a trusted checkout, HOME, PATH and user-owned destination/desktop directories. It is not hardened against a same-user attacker replacing destination symlinks. The generated desktop Exec line is not quoted for spaces/special characters in HOME; that is a portability/trusted-environment limitation, not a demonstrated external injection path on this workstation. Backup names have second granularity and updates are not atomic; avoid concurrent installs. Never run it with sudo or point it at a shared/untrusted checkout. No installed files/backups were changed.

There are no pip/npm runtime dependencies, vendored libraries, lockfiles, submodules or CI workflows in the inspected tree. Optional Playwright is test tooling and is missing; it was not downloaded. The deployed Docker images, SGLang, Ollama, driver and browser are external dependencies, not bundled artifacts, and their effective versions/CVEs remain NOT VERIFIED.

Observed Python: 3.12.3; Ubuntu package revision for Python/stdlib: `3.12.3-1ubuntu0.17`. This matches the fixed Noble revision in [Ubuntu USN-8744-1](https://ubuntu.com/security/notices/USN-8744-1) and is newer than the revision in [USN-8509-1](https://lists.ubuntu.com/archives/ubuntu-security-announce/2026-July/010856.html). Thus a bare upstream `3.12.3` string alone does not establish vulnerability. These specific advisories were checked, not every OS CVE. Observed OpenSSL/libssl package revision: `3.0.13-0ubuntu3.16`, also listed on the [official package page](https://packages.ubuntu.com/noble/openssl); this is package evidence, not an exhaustive vulnerability clearance. Node v22.23.1 is test tooling. The Firefox deb is a snap transition package, not the running browser version. No system package upgrade occurred.

Python explicitly cautions that [http.server provides only basic security checks](https://docs.python.org/3.12/library/security_warnings.html). The custom handler's loopback/authentication restrictions are essential; do not expose it through a proxy, tunnel or LAN bind.

## Validation results

| Check | Result and scope |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | PASS: 101 tests, including 16 new security tests; no skips. Runtime operations mocked; state/logs temporary. |
| `python3 -m unittest discover -s tests -p test_security.py -v` | PASS: 16 new security tests. Includes complete HTTP parsing over fake byte-stream connections, not real sockets. |
| Original-HEAD filesystem reproductions | Three targeted regressions fail on isolated copies of original source and pass on corrected source; no real private file accessed. |
| Three existing JavaScript suites | PASS, including expanded model metadata/attribute injection and crafted demo destination tests. VM/DOM evidence only. |
| Python compile, JavaScript syntax, shell syntax, `git diff --check` | PASS. Installer not executed. |
| Repository/history scan | Completed locally; heuristic hits triaged as fixtures/privacy identifiers; no confirmed live secret. |
| Chromium and Firefox browser suites | BLOCKED, exit 2: Playwright missing. No screenshot or browser assertion passed. A fresh browser-connector attempt also failed because its profile was already in use; the profile was not changed. |
| Random loopback bind | BLOCKED: PermissionError at socket creation. No stable instance replaced. |
| systemd / Docker / effective sudo policy | BLOCKED / NOT VERIFIED. Readable controller/config metadata is not effective-policy proof. |
| Remote settings/tags/releases/artifacts | NOT VERIFIED beyond private repository metadata and branch names. |

## Required actions before publication

1. Review and commit these corrections on the development branch; merge via the normal reviewed process before presenting `main` as current. No commit, push or visibility change was performed here.
2. Run a reputable maintained secret scanner locally against all fetched refs and history; review any matches privately. Verify remote tags, releases, artifacts, workflow logs and any relevant fork/PR refs. Do not upload private source to an arbitrary scanning service.
3. Review commit-author identities and historical host/path disclosures. Decide whether those privacy details are acceptable. History rewriting requires separate approval and coordination; no live-secret rotation is currently mandated by a confirmed discovery.
4. Verify GitHub security settings: private vulnerability reporting, available secret scanning/push protection, protected release/default branch and required checks. Their current state is unknown; none was changed.
5. Run guarded browser suites with provisioned Chromium/Firefox and permitted loopback sockets. Check actual Firefox ARM64 behavior and transport protections without pointing tests at the installed application.
6. Have an administrator verify exact sudo rules, trusted executable/config ownership, Docker authority and authenticated loopback gateway exposure. Audit actual deployed runtime versions against vendor advisories. No live lifecycle/inference action is needed to inspect these contracts.
7. Inspect state-directory permissions if fail-closed locking/logging is reported after deployment; do not automatically broaden permissions. Keep launch URLs private and approve any installation separately.

**Final recommendation: INCOMPLETE_AUDIT.** The authorized application remediation and isolated validation are complete, but the missing remote-publication and deployment evidence prevents a defensible whole-project publication approval. The repository remains private. Source-publication risk and workstation deployment risk must be signed off separately.
