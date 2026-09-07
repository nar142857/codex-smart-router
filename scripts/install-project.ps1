param(
  [string]$Target = ".",
  [ValidateSet("terra","sol")]
  [string]$Root = "terra"
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = (Resolve-Path $Target).Path
$Python = Get-Command python -ErrorAction SilentlyContinue
if ($Python) {
  & python "$ScriptDir\install_global.py" --root $Root --codex-dir "$Target\.codex" --skills-dir "$Target\.agents\skills" --agents-md "$Target\AGENTS.md"
  exit $LASTEXITCODE
}
$Py = Get-Command py -ErrorAction SilentlyContinue
if ($Py) {
  & py -3 "$ScriptDir\install_global.py" --root $Root --codex-dir "$Target\.codex" --skills-dir "$Target\.agents\skills" --agents-md "$Target\AGENTS.md"
  exit $LASTEXITCODE
}
Write-Error "Python 3 is required for the safe merge installer."
exit 1
