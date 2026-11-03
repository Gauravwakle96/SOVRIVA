# Troubleshooting

- **Port occupied:** SOVRIVA intentionally uses `127.0.0.1:8765`; stop the other local service or set `SOVRIVA_PORT` to a free port and update the extension source before pairing.
- **Extension says desktop unavailable:** confirm `python run.py` is running, reload the extension, and pair again if its token was revoked.
- **Archive rejected:** use the original Google Takeout or Meta Accounts Center ZIP; unsafe paths, executable members, malformed ZIPs, and oversized archives are rejected.
- **No blocked count:** this is expected when Chrome does not expose reliable DNR match feedback. Inspect active rule count and the controlled lab server instead.
- **OCR cannot load:** development OCR loads Tesseract.js from its CDN. Offline release builds must bundle a pinned worker.
- **Installer build fails:** install Cargo/Rust, Tauri CLI, WebView2, and PyInstaller; the script fails rather than producing a misleading partial installer.
