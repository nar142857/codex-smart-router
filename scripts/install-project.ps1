param(
  [string]$Target = ".",
  [ValidateSet("astra","sol")]
  [string]$Root = "astra"
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BundleDir = Split-Path -Parent $ScriptDir
$Target = (Resolve-Path $Target).Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path "$Target\.codex\agents" | Out-Null
New-Item -ItemType Directory -Force -Path "$Target\.agents\skills" | Out-Null
if (Test-Path "$Target\.codex\config.toml") { Copy-Item "$Target\.codex\config.toml" "$Target\.codex\config.toml.bak-$Stamp" }
if (Test-Path "$Target\AGENTS.md") { Copy-Item "$Target\AGENTS.md" "$Target\AGENTS.md.bak-$Stamp" }
Copy-Item "$BundleDir\global\.codex\agents\*.toml" "$Target\.codex\agents\" -Force
if (Test-Path "$Target\.agents\skills\smart-router") { Remove-Item "$Target\.agents\skills\smart-router" -Recurse -Force }
Copy-Item "$BundleDir\global\.agents\skills\smart-router" "$Target\.agents\skills\smart-router" -Recurse
if ($Root -eq "sol") {
  Copy-Item "$BundleDir\fallbacks\config-root-sol.toml" "$Target\.codex\config.toml" -Force
} else {
  Copy-Item "$BundleDir\global\.codex\config.toml" "$Target\.codex\config.toml" -Force
}
if (-not (Test-Path "$Target\AGENTS.md")) {
  Copy-Item "$BundleDir\project-template\AGENTS.md" "$Target\AGENTS.md"
} else {
  Add-Content "$Target\AGENTS.md" @'

<!-- SMART-ROUTER:PROJECT -->
## Smart Router
Use `$smart-router` for non-trivial engineering tasks.
Prefer Luna for exploration/research/tests, Terra for normal implementation, Sol for hard work/review, and Astra primarily for orchestration/high-risk review.
Do not mechanically spawn all roles for small tasks.
'@
}
Write-Host "Installed project-scoped Smart Router into: $Target"
Write-Host "Restart/reopen the project in Codex."
