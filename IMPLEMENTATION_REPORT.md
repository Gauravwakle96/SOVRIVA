# Implementation report

## IMPLEMENTED_AND_TESTED

Loopback FastAPI/SQLite service, validated archive ingestion, provenance-preserving records, deterministic interest normalization, safe legacy HTML activity extraction, Profile Drift, cross-platform comparison, preference reviews, privacy-action verification, authenticated pairing, downloadable Markdown reports, MV3 source, DNR policy generation, independent controls, privacy modes, allowlists/custom domains, lab fixture, dashboard, and release scripts.

## IMPLEMENTED_AND_TESTED

The PyInstaller sidecar was built as `dist/sovriva-backend.exe` and launched successfully; `GET /api/health` returned HTTP 200 from the packaged executable.

## IMPLEMENTED_NOT_FULLY_TESTED

Tauri v2 desktop scaffold, Tauri sidecar integration, Chrome/Edge live extension execution, and local browser OCR path.

## PARTIALLY_IMPLEMENTED

Google/Meta parser coverage varies by export version; current adapters prioritize JSON. DNR telemetry is configuration/observation-oriented because production match feedback is restricted. The current domain corpus is intentionally small and hand-reviewed.

## NOT_IMPLEMENTED

Automatic Google Data Portability OAuth synchronization, automatic Meta consumer synchronization, encrypted database at rest, full filter-list subscriptions, and a generated installer in this environment.

## NOT_SUPPORTED_BY_PLATFORM

Universal ad removal, unrestricted blocked-request telemetry from ordinary MV3 extensions, and native mobile-app protection.
