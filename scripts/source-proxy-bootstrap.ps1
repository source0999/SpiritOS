$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(Mandatory = $true)]
        [string[]]$CommandArgs
    )

    & $Command @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $CommandArgs"
    }
}

Write-Host "== Source proxy bootstrap =="
Write-Host "Repo: $RepoRoot"

Write-Host "`n== Node environment =="
Invoke-Checked -Command node -CommandArgs @("--version")
Invoke-Checked -Command npm -CommandArgs @("--version")
Invoke-Checked -Command npm -CommandArgs @("install")

Write-Host "`n== Python environment =="
$PythonExe = py -3.13 -c "import sys; print(sys.executable)"
if ($LASTEXITCODE -ne 0) {
    throw "Unable to locate Python 3.13 via py launcher."
}
Write-Host "Python: $PythonExe"
$VenvDir = if ($env:SOURCE_PROXY_VENV) { $env:SOURCE_PROXY_VENV } else { ".venv-source-proxy-windows" }
Invoke-Checked -Command $PythonExe -CommandArgs @("-m", "venv", $VenvDir)
$VenvPython = Join-Path $RepoRoot "$VenvDir\Scripts\python.exe"
Invoke-Checked -Command $VenvPython -CommandArgs @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked -Command $VenvPython -CommandArgs @("-m", "pip", "install", "-r", "requirements.txt")

Write-Host "`n== Compatibility probe =="
Invoke-Checked -Command $VenvPython -CommandArgs @("-c", "import importlib.metadata as metadata; import fastapi, litellm, pynvml; print('fastapi', fastapi.__version__); print('litellm', metadata.version('litellm')); print('pynvml ready')")

Write-Host "`nBootstrap complete."
