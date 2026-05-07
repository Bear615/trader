$ErrorActionPreference = "Stop"

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Html = Join-Path $Here "mobile-preview.html"
$OutDir = Join-Path $Here "out"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$ChromeCandidates = @(
  "C:\Program Files\Google\Chrome\Application\chrome.exe",
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
  "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
  "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)

$Browser = $ChromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Browser) {
  throw "Chrome or Edge was not found in the standard install locations."
}

$Screens = @(
  "01-dashboard",
  "02-portfolio",
  "03-trades",
  "04-trade-detail",
  "05-ai-decisions",
  "06-ai-detail",
  "07-monitor",
  "08-backtest-setup",
  "09-backtest-results",
  "10-admin"
)

$FileUrl = "file:///" + (($Html -replace "\\", "/") -replace " ", "%20")

foreach ($Screen in $Screens) {
  $Png = Join-Path $OutDir "$Screen.png"
  $Url = "$FileUrl`?screen=$Screen"
  & $Browser `
    --headless=new `
    --disable-gpu `
    --hide-scrollbars `
    --force-device-scale-factor=1 `
    --window-size=390,844 `
    "--screenshot=$Png" `
    $Url | Out-Null
  if (-not (Test-Path $Png)) {
    throw "Screenshot failed for $Screen"
  }
}

$ContactHtml = Join-Path $Here "contact-sheet.html"
$ContactUrl = "file:///" + (($ContactHtml -replace "\\", "/") -replace " ", "%20")
$ContactPng = Join-Path $OutDir "00-contact-sheet.png"
& $Browser `
  --headless=new `
  --disable-gpu `
  --hide-scrollbars `
  --force-device-scale-factor=1 `
  --window-size=1240,1180 `
  "--screenshot=$ContactPng" `
  $ContactUrl | Out-Null
if (-not (Test-Path $ContactPng)) {
  throw "Screenshot failed for contact sheet"
}

Write-Host "Rendered $($Screens.Count) mobile previews plus contact sheet to $OutDir"
