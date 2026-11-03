# Product
<!-- impeccable:product-schema 1 -->

## Platform
web

## Product purpose
ASUS AI Control Center manages an existing local AI workstation. Operators inspect hardware, registered runtimes and discovered NAS assets, and deliberately load, unload or switch registered models.

## Stack
Existing Python HTTP server and dependency-free HTML, CSS and JavaScript.

## Capabilities and constraints
Preserve the v5 installation, loopback binding, session authentication and existing runtime adapters. Development must never execute live model operations or modify services, Docker, Ollama, SGLang, NAS configuration or model files. NAS weights are discovered assets, not runnable models. Preserve the semicircular performance gauges. Clearly separate representative data from live readings. The interface is entirely English.

## Brand commitments
The user requests the precision and visual quality of sophisticated macOS desktop applications, with a distinct ASUS AI identity and restrained decoration.

## Evidence
web/index.html, web/style.css, web/app.js, core.py, server.py and TESTING.md. No screenshot assets exist in the supplied tree. User roles beyond workstation operator and additional readiness APIs are undecided.
