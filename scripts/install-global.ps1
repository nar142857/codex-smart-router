$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command python -ErrorAction SilentlyContinue
if ($Python) {
  & python "$ScriptDir\install_global.py"
  exit $LASTEXITCODE
}
$Py = Get-Command py -ErrorAction SilentlyContinue
if ($Py) {
  & py -3 "$ScriptDir\install_global.py"
  exit $LASTEXITCODE
}
Write-Error "Python 3 is required for the safe merge installer."
exit 1
