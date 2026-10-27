param([switch]$SkipTests)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
if ($env:OS -ne 'Windows_NT') { throw 'Windows builds must run on Windows.' }
$taskPython = Join-Path (Get-Location) '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run .\scripts\setup_windows.ps1 first.' }
if (-not $SkipTests) {
    & $taskPython -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed; build stopped.' }
}
$taskOriginalPath = $env:PATH
try {
    # Avoid collecting unrelated DLLs from MATLAB/Poppler/other developer tools.
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot;$(Split-Path $taskPython -Parent)"
    & $taskPython -m PyInstaller --noconfirm --clean --windowed --onedir --name WitthoftSpreadsheetCompare --paths src --exclude-module pandas --exclude-module numpy scripts/launcher.py
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
} finally {
    $env:PATH = $taskOriginalPath
}
$taskExe = Join-Path (Get-Location) 'dist\WitthoftSpreadsheetCompare\WitthoftSpreadsheetCompare.exe'
$taskSmoke = Join-Path (Get-Location) 'artifacts\packaged-smoke'
$taskRun = Start-Process -FilePath $taskExe -ArgumentList @('--self-test', "`"$taskSmoke`"") -WindowStyle Hidden -PassThru
if (-not $taskRun.WaitForExit(90000)) {
    $taskRun.Kill()
    throw 'Packaged GUI verification timed out.'
}
if ($taskRun.ExitCode -ne 0) { throw "Packaged GUI verification failed. See $taskSmoke\self-test.json" }
$taskEvidence = Get-Content -Raw -LiteralPath (Join-Path $taskSmoke 'self-test.json') | ConvertFrom-Json
if (-not $taskEvidence.passed) { throw 'Packaged GUI self-test did not pass.' }
Copy-Item -LiteralPath (Join-Path $taskSmoke 'Application.png') -Destination 'docs\application.png' -Force
Copy-Item -LiteralPath 'README.md' -Destination 'dist\WitthoftSpreadsheetCompare\README.md' -Force
Copy-Item -LiteralPath 'docs' -Destination 'dist\WitthoftSpreadsheetCompare\docs' -Recurse -Force
Write-Host 'Created dist\WitthoftSpreadsheetCompare\WitthoftSpreadsheetCompare.exe'
Write-Host 'Packaged Windows GUI self-test passed (all three modes, Excel and CSV export).'
Write-Host 'Distribute the entire WitthoftSpreadsheetCompare folder, including _internal.'
