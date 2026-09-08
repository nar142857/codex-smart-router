param(
  [string]$Ref = "main",
  [string]$Repo = "nar142857/codex-smart-router"
)

$ErrorActionPreference = "Stop"
if ($Repo -notmatch '^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$') { throw "Invalid repository: $Repo" }
if ($Ref -notmatch '^[A-Za-z0-9._/-]+$') { throw "Invalid ref: $Ref" }

$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-smart-router-" + [guid]::NewGuid())
$Archive = Join-Path $TempDir "router.zip"

try {
  New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
  Write-Host "Downloading Codex Smart Router ($Repo@$Ref)..."
  Invoke-WebRequest -Uri "https://github.com/$Repo/archive/$Ref.zip" -OutFile $Archive
  Expand-Archive -Path $Archive -DestinationPath $TempDir -Force
  $Bundle = Get-ChildItem -Path $TempDir -Directory | Select-Object -First 1
  if ($null -eq $Bundle -or -not (Test-Path (Join-Path $Bundle.FullName "scripts\install-global.ps1"))) {
    throw "Downloaded archive does not contain the installer"
  }
  & (Join-Path $Bundle.FullName "scripts\install-global.ps1")
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
  if (Test-Path $TempDir) { Remove-Item -Path $TempDir -Recurse -Force }
}

Write-Host "Temporary installer files removed. Restart Codex to load the new global routing rules."
