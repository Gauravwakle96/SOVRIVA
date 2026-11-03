param([int]$Port = 8765)
$env:SOVRIVA_PORT = $Port
python (Join-Path $PSScriptRoot "..\run.py")
