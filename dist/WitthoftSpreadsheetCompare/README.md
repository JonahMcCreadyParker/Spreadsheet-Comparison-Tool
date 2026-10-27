# Witthoft Engineering — Spreadsheet Comparison Tool

An offline Windows desktop application for comparing `.csv`, `.xlsx`, and read-only `.xlsm` inputs. The original [implementation handoff](Witthoft_Spreadsheet_Comparison_Tool_Codex_Handoff.md) remains intact.

For committing the complete portable application to GitHub and installing it on another Windows device, see [GitHub deployment instructions](docs/GITHUB_DEPLOYMENT.md).

## Start the packaged application

Double-click `dist\WitthoftSpreadsheetCompare\WitthoftSpreadsheetCompare.exe`. No terminal, Python installation, network connection, or Excel installation is needed. When copying to another workstation, copy **the entire `WitthoftSpreadsheetCompare` folder**, including `_internal`, rather than just the `.exe`. This is an unsigned portable application, not an installer.

Drop Original A and Revised B into the two file boxes, select a comparison mode and sheets, choose keys for record modes, and click **Compare**. Filter or search the results and export Excel or CSV. Reports always include all results. See the [engineer user guide](docs/USER_GUIDE.md).

## Working features

- **General — Cell by Cell:** same-name worksheets and cell addresses; formula expressions by default, optional styles and hyperlinks, structural sheet/merged-range changes.
- **General — Match Records:** unique single/composite keys, order-independent matching, field mappings, configurable header rows, structural column changes, explicit duplicate/blank-key diagnostics.
- **Engineering — PLC / Tag Records:** proposed `Tag Name` key, configurable administrative exclusions, address/type/device/scaling categories, namespace-aware possible duplicate-address checks and exceptions, optional scaling completeness checks.
- Drag/drop, Browse, replacement, Clear, Swap, Reset, explicit worksheet pairs, first-row previews, duplicate/blank-key counts, named local profiles, worker threads with cooperative cancellation, sortable/filterable model/view results and raw row context.
- Timestamped Excel reports with Summary, Differences, Added/Removed Records, Warnings, Structural Changes; UTF-8 BOM CSV reports; literal Excel text and protected CSV text; atomic report replacement and source-overwrite protection.

## Development setup (PowerShell)

Current directory for every command below:

```powershell
Set-Location 'C:\Users\Jonah\Documents\Spreadsheet_Comparison_Tool'
```

This Windows machine has **64-bit Python 3.13.9**, which was used for validation. Source supports Python 3.12–3.13; 3.12 was not tested here. The tested environment is pinned in `requirements-lock.txt`, including transitive packages. Direct application dependencies are also pinned in `pyproject.toml`; test/build dependencies are in `requirements-dev.txt`.

```powershell
.\scripts\setup_windows.ps1
.\.venv\Scripts\python.exe -m witthoft_compare
.\.venv\Scripts\python.exe -m pytest -q
.\scripts\build_windows.ps1
```

If script execution is restricted, use a process-local override:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

Manual equivalent setup:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m witthoft_compare
```

Use `setup_windows.ps1 -PythonVersion 3.12` for a fresh environment with Python 3.12 installed. The installer needs internet access to obtain packages; the application itself uses no network services. No pandas conversion is used on imported identifiers: the canonical engine uses text-preserving dictionaries and openpyxl. pandas is available as requested by the handoff but excluded, together with NumPy, from the executable because it is unnecessary at runtime.

## Windows executable and verification

The build script runs pytest, creates a PyInstaller `--windowed --onedir` build with an isolated DLL-discovery PATH, then launches the packaged GUI self-test. A failing packaged check fails the build:

```text
dist\WitthoftSpreadsheetCompare\WitthoftSpreadsheetCompare.exe
```

The build runs on Windows, because PyInstaller bundles the active operating system's runtime. Qt's platform plugin is collected by the PySide6 PyInstaller hooks. Reference: [Qt deployment with PyInstaller](https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html), [PyInstaller operating mode](https://www.pyinstaller.org/en/stable/operating-mode.html).

Run the **actual packaged GUI** against synthetic files using its unattended diagnostic mode (visible GUI; preferences are not touched):

```powershell
$taskExe = Join-Path (Get-Location) 'dist\WitthoftSpreadsheetCompare\WitthoftSpreadsheetCompare.exe'
$taskRun = Start-Process -FilePath $taskExe -ArgumentList '--self-test artifacts\packaged-smoke' -WindowStyle Hidden -Wait -PassThru
$taskRun.ExitCode
Get-Content .\artifacts\packaged-smoke\self-test.json
```

It imports synthetic PlantSCADA-style CSVs and Excel workbooks, operates all three GUI modes and explicit mixed CSV/Excel pairing, checks stored formula differences, exports Excel and CSV, reopens the Excel report, checks unchanged source hashes, saves `Application.png`, and exits with 0 on success. Development equivalent:

```powershell
.\.venv\Scripts\python.exe -m witthoft_compare --self-test artifacts\development-smoke
```

See [validation results](docs/VALIDATION.md), [architecture](docs/ARCHITECTURE.md), and [specific limitations](docs/LIMITATIONS.md). The real `ST045_dump.csv` / `ST045GT_dump.csv` files were not supplied; no results are claimed for those files.
