# SOVRIVA project audit

## Baseline

The workspace was inspected before implementation. It contained only `.opencode/omnirush.json`; it was not a Git repository (`git status` and `git branch` returned “not a git repository”). There were no frontend files, backend files, database models, extension files, tests, package manifests, build scripts, authentication, or uncommitted application changes to preserve.

## Resulting architecture

- **Backend:** Python 3.13-compatible FastAPI service in `sovriva/api.py`.
- **Persistence:** SQLite in `data/sovriva.db` during development; packaged builds should use the Windows app-data directory.
- **Frontend:** dependency-light HTML/CSS/JavaScript dashboard in `frontend/` so it runs without Node or cloud services.
- **Extension:** standalone MV3 JavaScript extension in `extension/`.
- **Desktop:** Tauri v2 scaffold in `src-tauri/` with a PyInstaller FastAPI sidecar build script.
- **Tests:** `tests/` uses the standard library so checks run without downloading a test framework.

## Working functionality before this change

None. No original SOVRIVA implementation existed in the workspace.

## Reused versus independently developed

The implementation uses repository concepts and public API knowledge as documented in `docs/OPEN_SOURCE_LICENSE_AUDIT.md`; it does not copy source files from Blocky, Chroma, FP Radar, or the other references. Profile Drift, provenance, reconciliation, and action verification are SOVRIVA-owned algorithms.

## Remaining migration risks

- The Tauri scaffold requires Rust/Cargo, Tauri CLI, WebView2, and PyInstaller before an installer can be built.
- The no-build dashboard should be migrated to the project's eventual React/TypeScript shell only if that shell is introduced deliberately; it should not be replaced with a template.
