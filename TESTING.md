# Testing

Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
node tests/test_frontend.js
node --check web/app.js
```

Python tests mock runtime operations and exercise API handlers without opening sockets. The frontend regressions cover Performance navigation, storage percentages and invalid values, CSP-compatible progress markup, gauge telemetry validation and CSS theme, responsive, and reduced-motion rules, fixed GiB axis ticks and byte-to-GiB mapping, local timestamps, empty state, resizing, theme drawing, high-density redraw sizing, and simulated pointer and keyboard sample selection on both charts. They are not browser rendering tests. No test should load, unload or switch live models. Tests do not change services or NAS files.

The current sandbox forbids localhost sockets, so browser E2E, screenshot regression, and real HTTP integration could not be run here. Hardware, runtime readiness, long-running operations and recovery require validation on the target machine. Read-only checks should precede any controlled runtime operation, which requires explicit approval and no active clients. Do not run `install.sh` merely to test: it changes the installed v5 files and launcher.

On the GX10, Firefox previously confirmed the Memory Timeline rendered and Overview and Performance displayed live telemetry. Recheck the updated storage bars, chart tooltip, keyboard and touch interaction, resizing, contrast, and both themes in a real browser. Storage used is total minus space available to the current user; reserved blocks may be included in used space.

Both charts use a fixed 0–128 GiB scale; samples above 128 GiB are clipped visually and identified in the sample details. History is held in the server process (up to 180 status samples), survives page navigation, and is lost on server restart. The UI requests status every five seconds, though actual sampling can be affected by delays and other sessions.

The gauges use current API readings and show unavailable for missing or out-of-range values. Memory capacity is supplied by telemetry and may differ from nominal installed memory. The automated gauge layout and theme checks inspect markup and CSS; they do not verify rendered contrast, animation, or screen-reader behavior. Validate those in a real browser at desktop and mobile widths, in both themes and with reduced motion.
