param([string]$Root = (Resolve-Path "$PSScriptRoot\.."))
$ErrorActionPreference = "Stop"
$expected = @(
  "README.md", "INSTALLATION_GUIDE.md", "docs\PROJECT_AUDIT.md",
  "frontend\index.html", "frontend\app.js", "extension\manifest.json",
  "release\SOVRIVA_Extension.zip"
)
foreach ($path in $expected) { if (!(Test-Path (Join-Path $Root $path))) { throw "Missing release item: $path" } }
$manifest = Get-Content (Join-Path $Root "extension\manifest.json") -Raw | ConvertFrom-Json
if ($manifest.manifest_version -ne 3) { throw "Extension is not Manifest V3" }
Write-Host "Release verification passed for source and extension artifacts."
