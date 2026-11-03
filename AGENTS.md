# SOVRIVA contributor guidance

- Keep the product local-first: bind the API to `127.0.0.1`, do not add telemetry, and never store passwords, cookies, request bodies, or page text.
- Read `docs/PROJECT_AUDIT.md`, `docs/ARCHITECTURE.md`, and the relevant feature documentation before editing.
- Preserve source provenance for imported records. Never convert missing export data into a confirmed deletion.
- Keep ad blocking and tracker protection independent. Do not fabricate protection counters.
- Run `python -m compileall -q sovriva run.py`, the standard-library tests, and `node --check` on extension scripts after changes.
- Update `IMPLEMENTATION_STATUS.md` and the relevant documentation when behavior or limitations change.
