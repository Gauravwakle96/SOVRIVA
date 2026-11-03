# SOVRIVA

## YOUR DIGITAL IDENTITY. YOUR CONTROL.

SOVRIVA is a local-first privacy intelligence workspace for understanding exported advertising records and verifying observable browser-protection changes. It combines a FastAPI + SQLite local engine, a premium dashboard, and a Chrome/Edge Manifest V3 extension.

## Current deliverables

- **Local dashboard/API:** `python run.py` then open `http://127.0.0.1:8765`.
- **Extension source:** `extension/`.
- **Tauri v2 Windows scaffold:** `src-tauri/` and `scripts/build-windows.ps1`; the packaged backend is produced at `dist/sovriva-backend.exe`.
- **Controlled privacy fixture:** `python scripts/lab_server.py`.
- **Extension package:** generated at `release/SOVRIVA_Extension.zip` by `pwsh -File scripts/package-extension.ps1`.
- **Video pitch package:** `pitch/SOVRIVA_VIDEO_PITCH.md` and `pitch/RECORDING_AND_EDITING_CHECKLIST.md`.

## What works locally

- Security-validated Google/Meta ZIP import using base64 JSON API transport.
- SQLite import history, duplicate SHA-256 detection, source records, coverage reports, deletion, and rollback-safe transactions.
- Deterministic explainable taxonomy normalization and confidence values.
- Profile Drift, cross-platform reconciliation, preference review, provenance inspection, and privacy-action verification.
- Authenticated extension pairing with five-minute one-time codes and revocable tokens.
- MV3 observation using `webRequest`; actual DNR blocking for a documented local domain corpus; independent ad/tracker switches and three modes.
- Local two-origin experiment fixture and browser-local OCR path using Tesseract.js when its worker is available.

## Run

The easiest Windows option is to double-click `Run-SOVRIVA.bat`. It installs the Python dependencies once, starts the local API, and opens the dashboard. Keep the command window open while using SOVRIVA.

```powershell
python -m pip install -r requirements.txt
python run.py
```

The API intentionally binds to loopback. No cloud account or paid service is required.

## Honest release status

The current environment has Node and Python but no Rust/Cargo or PyInstaller, so `SOVRIVA_Setup.exe` has not been generated here. Install Rust/Tauri prerequisites and PyInstaller, then run:

```powershell
python -m pip install pyinstaller
pwsh -File scripts/build-windows.ps1
```

See `IMPLEMENTATION_STATUS.md`, `INSTALLATION_GUIDE.md`, and `docs/RELEASE_CHECKLIST.md` for tested boundaries and known limitations.
