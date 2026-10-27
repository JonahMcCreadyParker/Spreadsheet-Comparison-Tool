param([string]$PythonVersion = "3.13")
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & py "-$PythonVersion" -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed. Install 64-bit Python 3.12 or 3.13.' }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Pinned dependency installation failed.' }
& .\.venv\Scripts\python.exe -m pip install --no-deps -e .
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
Write-Host 'Ready. Run .\scripts\run_windows.ps1'
