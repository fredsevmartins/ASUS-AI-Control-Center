"""Isolated E2E server. No runtime adapter, model operation or NAS access allowed.

Invoked only by browser_e2e.mjs, never as the installed app. The token is a
synthetic fixture value with no validity in a live Control Center instance.
"""
from contextlib import ExitStack
import json
from pathlib import Path
import signal
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core
import server

FIXTURE_TOKEN = 'browser-fixture-only-not-a-live-session'


def forbidden(*args, **kwargs):
    raise AssertionError('Live runtime access is forbidden in the browser fixture')


def main():
    def terminate(*args):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminate)
    with tempfile.TemporaryDirectory(prefix='asus-ai-browser-') as directory, ExitStack() as stack:
        for name in ('execute', 'command', 'runtime_http', 'api', '_nas_scan', 'snapshot'):
            stack.enter_context(patch.object(core, name, side_effect=forbidden))
        stack.enter_context(patch.object(core, 'STATE_DIR', Path(directory)))
        stack.enter_context(patch.object(core, 'LOG_PATH', Path(directory) / 'operations.jsonl'))
        stack.enter_context(patch.object(server, 'TOKEN', FIXTURE_TOKEN))
        httpd = server.LocalHTTPServer(('127.0.0.1', 0), server.Handler)
        try:
            # This output contains only a port; no credentials or launch URLs.
            print(json.dumps({'port': httpd.server_address[1]}), flush=True)
            httpd.serve_forever(poll_interval=.1)
        finally:
            httpd.server_close()


if __name__ == '__main__':
    main()
