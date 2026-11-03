param(
  [string]$Root = (Resolve-Path "$PSScriptRoot\.."),
  [string]$Output = "$Root\release\SOVRIVA_Extension.zip"
)
$ErrorActionPreference = "Stop"
$extension = Join-Path $Root "extension"
if (!(Test-Path (Join-Path $extension "manifest.json"))) { throw "extension/manifest.json was not found" }
node --check (Join-Path $extension "background.js")
node --check (Join-Path $extension "popup.js")
New-Item -ItemType Directory -Force (Split-Path $Output) | Out-Null
if (Test-Path $Output) { Remove-Item $Output -Force }
Compress-Archive -Path (Join-Path $extension "*") -DestinationPath $Output -CompressionLevel Optimal
Write-Host "Created $Output"
