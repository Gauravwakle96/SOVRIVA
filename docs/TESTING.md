# Testing and acceptance

Fast checks:

```powershell
python -m compileall -q sovriva run.py
python -m unittest discover -s tests -v
node --check frontend/app.js
node --check extension/background.js
node --check extension/popup.js
pwsh -File scripts/package-extension.ps1
pwsh -File scripts/verify-release.ps1
```

Browser acceptance requires Chrome or Edge. Load `extension/`, start the API, generate a pairing code, pair from the popup, open the lab fixture, and inspect `/api/dashboard` plus Chrome's Network panel. The extension cannot claim verified DNR counts when Chrome does not expose match feedback.
