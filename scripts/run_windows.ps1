$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\pythonw.exe -m witthoft_compare
if ($LASTEXITCODE -ne 0) { throw 'Application startup failed. Run python -m witthoft_compare for diagnostics.' }
