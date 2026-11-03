# Release checklist

- [ ] Install Rust/Tauri CLI, WebView2, and PyInstaller on a clean Windows 10/11 x64 machine.
- [ ] Bundle a pinned local Tesseract.js worker and include Apache-2.0 notice.
- [ ] Run unit, security, extension syntax, and Chromium acceptance tests.
- [ ] Verify no `data/sovriva.db`, tokens, archives, `.env`, or private keys enter release packages.
- [ ] Run `pwsh -File scripts/build-windows.ps1` and copy the generated NSIS installer to `release/SOVRIVA_Setup.exe`.
- [ ] Run `pwsh -File scripts/package-extension.ps1` to create `release/SOVRIVA_Extension.zip`.
- [ ] Test install, pairing, revoke, mode switching, deletion, and clean uninstall.
- [ ] Review license audit and limitations before presenting.
