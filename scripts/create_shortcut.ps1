$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path $PSScriptRoot -Parent
$taskExecutable = Join-Path $taskProjectRoot 'dist\SpreadsheetCompare\SpreadsheetCompare.exe'
if (-not (Test-Path -LiteralPath $taskExecutable -PathType Leaf)) {
    throw 'Application executable not found. Pull the complete distribution or build it first.'
}
$taskShortcutPath = Join-Path $taskProjectRoot 'Spreadsheet Comparison Tool.lnk'
$taskShell = New-Object -ComObject WScript.Shell
$taskShortcut = $taskShell.CreateShortcut($taskShortcutPath)
$taskShortcut.TargetPath = $taskExecutable
$taskShortcut.WorkingDirectory = Split-Path $taskExecutable -Parent
$taskShortcut.IconLocation = "$taskExecutable,0"
$taskShortcut.Description = 'Open Spreadsheet Comparison Tool'
$taskShortcut.Save()
Write-Output "Created shortcut: $taskShortcutPath"
