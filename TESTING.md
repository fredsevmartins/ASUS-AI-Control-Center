# Testing

Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
node tests/test_frontend.js
node --check web/app.js
```

Python tests mock runtime operations and exercise API handlers without opening sockets. The frontend regressions check that navigating to Performance makes the chart visible before requesting a redraw and that repeated high-density canvas redraws retain the intended height; they are not browser rendering tests. No test should load, unload or switch live models. Tests do not change services or NAS files.

The current sandbox forbids localhost sockets, so browser E2E, screenshot regression, and real HTTP integration could not be run here. Hardware, runtime readiness, long-running operations and recovery require validation on the target machine. Read-only checks should precede any controlled runtime operation, which requires explicit approval and no active clients. Do not run `install.sh` merely to test: it changes the installed v5 files and launcher.
