$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\pythonw.exe -m spreadsheet_compare
if ($LASTEXITCODE -ne 0) { throw 'Application startup failed. Run python -m spreadsheet_compare for diagnostics.' }
