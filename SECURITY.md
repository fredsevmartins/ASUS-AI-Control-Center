# Security and operational safety

The server binds to loopback and uses a random per-process token for API access. The initial URL contains that token; do not share it or expose the server via LAN forwarding or a reverse proxy. The token does not protect against hostile processes or users on the same machine. Static assets are public on the local port; responses use a restrictive CSP for the main document. The Ollama endpoint can be overridden by `OLLAMA_HOST`, so its destination is part of the local configuration and trust boundary.

Model operations can interrupt clients and consume substantial shared memory. Actions require UI confirmation but cannot detect all clients or protect against changes made outside this process. SGLang process state is not inference readiness. Recovery is best effort; verify runtime state before relying on it. NAS discovery reads metadata only and does not establish that a model can run. Do not alter runtime configuration or model files through this application.

Report security issues privately to the repository maintainer; avoid including tokens, prompts or sensitive paths in reports. Operation logs include model names and error details, and are stored under the user's local state directory.
