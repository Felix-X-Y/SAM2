param(
    [switch]$Smoke,
    [string]$Image,
    [string]$Prompts,
    [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$scriptPath = Join-Path $PSScriptRoot 'run_image.py'
if ($Smoke) {
    & $pythonPath $scriptPath --smoke --output $Output
} else {
    if (-not $Image -or -not $Prompts) { throw 'Provide Image and Prompts, or use -Smoke.' }
    & $pythonPath $scriptPath --image $Image --prompts $Prompts --output $Output
}
if ($LASTEXITCODE -ne 0) { throw "Inference failed (exit $LASTEXITCODE); preserve the error output." }
