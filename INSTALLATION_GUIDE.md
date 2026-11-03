# SOVRIVA installation guide

## Development run

1. Install Python 3.11+.
2. Open PowerShell in the SOVRIVA directory.
3. Run `python -m pip install -r requirements.txt`.
4. Run `python run.py`.
5. Open `http://127.0.0.1:8765`.

## Windows desktop installer

The backend sidecar is available as `dist/sovriva-backend.exe`. The complete release installer is produced on a Windows build machine with Rust/Tauri, WebView2, and PyInstaller installed. Run `pwsh -File scripts/build-windows.ps1`, then use `release/SOVRIVA_Setup.exe`; the current workspace does not contain that installer because Cargo/Rust is unavailable.

## Chrome / Edge extension

1. Run `pwsh -File scripts/package-extension.ps1` or obtain `release/SOVRIVA_Extension.zip`.
2. Extract the ZIP to a folder; do not load the ZIP directly.
3. Open `chrome://extensions` (Chrome) or `edge://extensions` (Edge).
4. Enable **Developer mode**.
5. Select **Load unpacked** and choose the extracted `SOVRIVA_Extension` directory.
6. Start the SOVRIVA desktop/API application.
7. In SOVRIVA → **Live Browser Monitor**, generate a pairing code.
8. Open the extension popup and enter the six-digit code.
9. Confirm the popup says **Connected**. Revoke tokens from the desktop connection panel.

After editing extension files, return to the browser extensions page and select **Reload**.

## Uninstallation

Remove the desktop application through Windows Settings. Remove the unpacked extension from the browser extensions page. Use SOVRIVA Settings → delete all local data before uninstalling if records must be removed.
## Run without the Windows installer

The Tauri installer is optional. From the extracted SOVRIVA folder, double-click `Run-SOVRIVA.bat`. The script installs the Python dependencies once, opens `http://127.0.0.1:8765`, and keeps the local service running in the command window. Close that window to stop SOVRIVA.

To load the browser extension, open `chrome://extensions` or `edge://extensions`, enable **Developer mode**, choose **Load unpacked**, and select the `extension` folder. Do not select the ZIP file.
