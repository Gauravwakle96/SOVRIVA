# Implementation status

Updated: 2026-11-03

## IMPLEMENTED_AND_TESTED

- Loopback FastAPI service and SQLite schema.
- ZIP path traversal, unsafe suffix, checksum, archive/member/expanded-size validation.
- Google/Meta format detection and JSON source preservation.
- Duplicate import detection using SHA-256.
- Profile normalization, Profile Drift uncertainty handling, cross-platform matching, preference outcomes.
- Evidence provenance API and dashboard inspection.
- Privacy action creation and evidence-limited verification.
- MV3 manifest and JavaScript syntax validation.
- DNR policy generation for documented ad/tracker domains.
- Extension pairing code/token flow and observation authentication.
- Local two-origin lab fixture.
- `release/SOVRIVA_Extension.zip` generated, ZIP integrity checked, and release source verification passed.
- API smoke-tested on loopback: health, demo seed, pairing, authenticated observation ingestion, unauthorized rejection, and complete deletion.
- PyInstaller sidecar `dist/sovriva-backend.exe` built and its packaged `/api/health` endpoint smoke-tested successfully.
- Downloadable Markdown profile reports and safe legacy Google HTML activity extraction.
- Extension allowlist and custom-domain policy controls with input normalization.
- Fast interaction path: dashboard paints from primary data first, and extension policy sync is debounced and skips unchanged DNR policies.
- Presentation-ready dashboard layer: animated import surface, evidence-led architecture pipeline, presentation mode with `P` shortcut, reduced-motion support, and restrained page-entry/hover motion.

## IMPLEMENTED_NOT_FULLY_TESTED

- Dashboard interactions and responsive presentation: API-backed, but full Chromium Playwright coverage is not installed in this environment.
- Live extension behavior: source and policy logic are implemented; Chrome/Edge execution requires a locally installed browser.
- Tauri sidecar lifecycle scaffold: sidecar executable is built; Rust/Tauri installer compilation remains unavailable in this environment.
- Local Tesseract.js OCR: browser path is implemented; the worker is loaded from a CDN in development and should be bundled for offline release.

## PARTIALLY_IMPLEMENTED

- Google archive support handles common JSON activity/history structures and safe anchor extraction from legacy activity HTML; other HTML structures remain unsupported.
- Meta parser accepts common JSON advertising/activity records but export schemas vary and require additional fixtures.
- Protection telemetry reports observed/classified/configured values; verified DNR match feedback is not claimed.
- Windows installer scripts are prepared; PyInstaller sidecar is built, but Cargo/Tauri and WebView2 are still required for the NSIS installer.

## NOT_IMPLEMENTED

- Google Data Portability OAuth connector and automatic recurring sync.
- Official Meta consumer automatic synchronization.
- Production-grade encrypted database at rest and Windows DPAPI secret vault.
- Complete filter-list subscription management.

## NOT_SUPPORTED_BY_PLATFORM

- Universal ad removal, especially ads served from a platform's own first-party infrastructure.
- Unrestricted production DNR blocked-request telemetry in ordinary MV3 extensions.
- Native mobile-app tracking protection from a browser extension.
