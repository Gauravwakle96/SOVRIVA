param(
  [Parameter(Mandatory = $true)]
  [string]$VoiceFile,
  [string]$Output = "pitch/SOVRIVA_Pitch_Final.mp4"
)

$ErrorActionPreference = "Stop"
$draft = Join-Path $PSScriptRoot "SOVRIVA_Pitch_Visual_Draft.mp4"
if (!(Test-Path $draft)) { throw "Visual draft not found: $draft" }
if (!(Test-Path $VoiceFile)) { throw "Voice recording not found: $VoiceFile" }

ffmpeg -y -i $draft -i $VoiceFile `
  -filter_complex "[1:a]loudnorm=I=-16:LRA=7:TP=-1.5,apad[voice]" `
  -map 0:v:0 -map "[voice]" -t 163 `
  -c:v copy -c:a aac -b:a 160k -shortest $Output

Write-Host "Created $Output"
