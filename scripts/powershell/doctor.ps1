# Read-only Spec Kit diagnostic. Usage: .\doctor.ps1 [-Json] [-Help]
param(
    [switch]$Json,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'
$pythonCommand = $env:PYTHON
if (-not $pythonCommand) {
    if (Get-Command python3 -ErrorAction SilentlyContinue) { $pythonCommand = 'python3' }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $pythonCommand = 'python' }
    else { Write-Error 'Project Health Check requires Python 3; set PYTHON to its executable.'; exit 2 }
}
$engine = Join-Path $PSScriptRoot '../doctor.py'
$engineArguments = @('-B', $engine)
if ($Json) { $engineArguments += '--json' }
if ($Help) { $engineArguments += '--help' }
& $pythonCommand @engineArguments
exit $LASTEXITCODE
