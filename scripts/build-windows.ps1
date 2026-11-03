param(
  [string]$Root = (Resolve-Path "$PSScriptRoot\.."),
  [switch]$SkipInstaller
)
$ErrorActionPreference = "Stop"
Write-Host "SOVRIVA Windows build: verifying toolchain"
if (!$SkipInstaller -and !(Get-Command cargo -ErrorAction SilentlyContinue)) { throw "Rust/Cargo is required for the Tauri installer. Install rustup, then rerun this script." }
python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) { throw "PyInstaller is required to package the FastAPI sidecar. Run: python -m pip install -r requirements-build.txt" }
Push-Location $Root
try {
  python -m pip install -r requirements-build.txt
  npm install
  python -m PyInstaller --clean --noconfirm --onefile --add-data "frontend;frontend" --name sovriva-backend run.py
  New-Item -ItemType Directory -Force "src-tauri\binaries" | Out-Null
  if (Get-Command rustc -ErrorAction SilentlyContinue) {
    $target = rustc -vV | Select-String "host:" | ForEach-Object { ($_ -split " ")[1].Trim() }
    if (!$target) { throw "Could not determine Rust target triple" }
    Copy-Item "dist\sovriva-backend.exe" "src-tauri\binaries\sovriva-backend-$target.exe" -Force
  } elseif (!$SkipInstaller) {
    throw "Could not determine Rust target triple"
  } else {
    Write-Host "Cargo unavailable: sidecar executable created at dist\sovriva-backend.exe; Tauri copy deferred."
  }
  & "$PSScriptRoot\package-extension.ps1" -Root $Root
  if (!$SkipInstaller) {
    npx tauri build
    $installer = Get-ChildItem "src-tauri\target\release\bundle\nsis\*.exe" | Select-Object -First 1
    if (!$installer) { throw "Tauri build completed without an NSIS installer" }
    New-Item -ItemType Directory -Force "release" | Out-Null
    Copy-Item $installer.FullName "release\SOVRIVA_Setup.exe" -Force
    Write-Host "Created release\SOVRIVA_Setup.exe"
  }
  Write-Host "Windows build completed. Inspect src-tauri\target\release\bundle for the installer."
} finally { Pop-Location }
