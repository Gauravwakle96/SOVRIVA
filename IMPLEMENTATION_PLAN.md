# Implementation plan

1. Audit the empty workspace and preserve the SOVRIVA identity.
2. Establish a loopback API, versioned SQLite schema, and secure import boundary.
3. Implement source-linked Google/Meta adapters and deterministic intelligence.
4. Expose evidence, drift, comparison, preference, and action-verification APIs.
5. Build the dashboard around real API data and explicit empty states.
6. Build an MV3 extension with local observation batching, DNR enforcement, pairing, modes, allowlists, and cosmetic filtering.
7. Add a controlled two-origin lab and release scripts.
8. Add Tauri sidecar packaging and verify Windows prerequisites before producing an installer.
9. Run unit/security/syntax checks, then conduct browser acceptance testing when Chromium is available.

The plan deliberately avoids copying complete competing extensions and keeps GPL-licensed Chroma material as reference only.
