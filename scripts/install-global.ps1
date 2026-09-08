param(
  [string]$DefaultModel,
  [ValidateSet("low", "medium", "high", "xhigh", "max", "ultra")]
  [string]$DefaultReasoningEffort
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallArgs = @()
if ($DefaultModel) {
  $InstallArgs += "--default-model", $DefaultModel
  if ($DefaultReasoningEffort) { $InstallArgs += "--default-reasoning-effort", $DefaultReasoningEffort }
} elseif ($DefaultReasoningEffort) {
  Write-Error "-DefaultReasoningEffort requires -DefaultModel"
  exit 2
}
$Python = Get-Command python -ErrorAction SilentlyContinue
if ($Python) {
  & python "$ScriptDir\install_global.py" @InstallArgs
  exit $LASTEXITCODE
}
$Py = Get-Command py -ErrorAction SilentlyContinue
if ($Py) {
  & py -3 "$ScriptDir\install_global.py" @InstallArgs
  exit $LASTEXITCODE
}
Write-Error "Python 3 is required for the safe merge installer."
exit 1
