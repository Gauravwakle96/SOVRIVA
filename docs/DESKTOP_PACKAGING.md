# Desktop packaging

`src-tauri/` contains the Tauri v2 configuration, shell sidecar permissions, Rust entry point, and NSIS target. `scripts/build-windows.ps1`:

1. installs Python requirements;
2. builds `run.py` into `sovriva-backend.exe` with PyInstaller;
3. copies it to the target-triple sidecar location;
4. packages the extension;
5. invokes `cargo tauri build`.

The sidecar is now buildable as `dist/sovriva-backend.exe` and has passed a packaged health smoke test. The current machine still does not have Cargo/Rust, so the Tauri installer is not claimed as built. Install build requirements with `python -m pip install -r requirements-build.txt` and install Rust/Tauri prerequisites before running the script. The expected installer location after a successful build is `src-tauri/target/release/bundle/nsis/`, copied to `release/SOVRIVA_Setup.exe` by the script.
