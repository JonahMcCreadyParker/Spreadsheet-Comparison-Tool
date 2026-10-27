# Witthoft Engineering — Spreadsheet Comparison Tool
## Codex implementation instructions and acceptance specification

**Document status:** Implementation handoff  
**Project:** Witthoft Engineering Spreadsheet Comparison Tool  
**Application type:** Offline Windows desktop GUI application  
**Primary input files:** `.csv`, `.xlsx`  
**Additional read-only input:** `.xlsm` (desirable; no macro execution)  
**Recommended stack:** Python 3.12, PySide6, pandas, openpyxl, PyInstaller, pytest  
**Primary deliverables:** Fully working source code, tests, user guide, and a Windows `.exe` build process.

---

## 1. Instructions to Codex — read first

You are acting as a software engineer implementing a production-use internal comparison application for Witthoft Engineering. **Build the functioning application, not merely a proposal, mock-up, or pseudocode.**

1. Inspect the current workspace and any repository content before writing or modifying files. Preserve unrelated user files. If the repository already has a meaningful structure, adapt these instructions to it.
2. Implement an **offline Windows graphical application** that imports two spreadsheets (CSV and/or native Excel), compares them in selectable modes, displays differences, and exports a useful report.
3. Use **PySide6** for the GUI, **pandas** where useful for tabular processing, **openpyxl** for Excel metadata/formulas/styles and `.xlsx` exports, and **PyInstaller** to produce a Windows executable. Keep the comparison engine independent of the GUI.
4. Provide three modes in a prominent **drop-down selection**: **General — Cell by Cell**, **General — Match Records**, and **Engineering — PLC / Tag Records**.
5. Provide two obvious **drag-and-drop file boxes**, one for the **Original (A)** and one for the **Revised (B)**. Also provide Browse buttons, file replacement, and clear/remove actions.
6. Use conservative comparison semantics: do not silently assume a row has been added/deleted when its alignment is uncertain, do not report a renamed worksheet as a confirmed rename without evidence, and do not interpret an address change as necessarily wrong.
7. Create tests using small representative sample files with known differences, and verify the GUI imports and compares files without exceptions.
8. Document exactly how to install dependencies, run development mode, run tests, and build a Windows `.exe`. **If executing outside Windows, do not claim a Windows executable has been tested or built.**
9. Work independently through implementation, validation, bug fixes, and documentation. Ask for clarification only if a truly blocking requirement is missing; otherwise use the sensible defaults specified here and record any assumptions.
10. At completion, report implemented functionality, test results, executable location (if built), any limitations, and exact commands needed to reproduce the build.

### Non-negotiable acceptance outcome

An engineer must be able to **drag in any two supported files**, choose a comparison mode from the drop-down, click **Compare**, view accurate differences, filter them, and export an Excel report **without opening a terminal or uploading data to a website** when running the packaged application.

---

## 2. Intended use and core workflows

This is a **general spreadsheet comparison tool**, with an optional, specialised **engineering-record comparison** profile.

Typical inputs:

- Two versions of an Excel workbook used for an I/O schedule, equipment register, control-system design, or general office spreadsheet.
- Two CSV exports from a SCADA or PLC engineering database.
- One CSV and one Excel worksheet containing similar tabular information.
- Two workbooks with multiple worksheets and different ordering of records.

**Workflow A — ordinary spreadsheet:** Original Excel workbook -> Revised Excel workbook -> `General — Cell by Cell` -> compare common sheet/cell addresses -> examine modifications -> export.

**Workflow B — records in any order:** Original CSV -> Revised CSV -> `General — Match Records` -> user selects the primary key column(s) -> compare records independently of their order -> export.

**Workflow C — engineering database:** Original SCADA CSV -> Revised SCADA CSV -> `Engineering — PLC / Tag Records` -> `Tag Name` automatically proposed as match key -> categorised additions/removals/changes -> targeted engineering warnings -> export.

---

## 3. User interface (Windows GUI)

Use a modern, readable PySide6 layout with responsive resizing, proper tab order, keyboard accessibility, and a progress indicator. A suggested main screen:

```text
+--------------------------------------------------------------------------+
| WITTHOFT ENGINEERING  |  Spreadsheet Comparison Tool                     |
+--------------------------------------------------------------------------+
| ORIGINAL (A)                        | REVISED (B)                         |
| +--------------------------------+  | +--------------------------------+   |
| | DROP CSV / XLSX FILE HERE      |  | | DROP CSV / XLSX FILE HERE      |   |
| | or [Browse...]                 |  | | or [Browse...]                 |   |
| +--------------------------------+  | +--------------------------------+   |
| Filename, file type, sheet count   | Filename, file type, sheet count    |
+--------------------------------------------------------------------------+
| Comparison Mode: [ General — Cell by Cell                         v ]     |
| Sheets: [All matching sheets v]  | Match Key: [Tag Name v] [Settings...]  |
| [ ] Include formatting   [ ] Include hyperlinks   [ ] Include formulas  |
| [Compare]    [Cancel]    [Swap A/B]    [Reset]                            |
+--------------------------------------------------------------------------+
| ADDED:  ##   REMOVED:  ##   MODIFIED RECORDS/CELLS: ##   WARNINGS: ##    |
| Filter [All statuses v] Search [________________]  [Export Excel] [CSV] |
+--------------------------------------------------------------------------+
| Status | Sheet | Record key / Cell | Field | Original | Revised | Notes  |
| ... sortable, filterable, resizable result grid ...                       |
+--------------------------------------------------------------------------+
| Status / progress bar / errors                                             |
+--------------------------------------------------------------------------+
```

### 3.1 File input interaction

- Two independent `QFrame`/`QWidget` drag-and-drop targets (with `setAcceptDrops(True)`, `dragEnterEvent`, `dropEvent`). Support Windows Explorer file drag-and-drop, **one file per input zone**. Clearly display which side is Original and Revised.
- Clicking Browse opens `QFileDialog`, filtering supported formats. Warn on unsupported files or if multiple files are dropped in one target; do not silently choose the wrong file.
- Show each full path (tooltip if truncated), filename, extension, imported sheet list, and any import warnings.
- Optional convenience: dragging two files onto the application window can populate A and B if both are empty; deterministic order and visual confirmation required. This is optional, not a dependency.
- Provide **Swap Files**, Clear, and Reset. Swapping reverses added/removed classifications and updates labels.
- Do not automatically launch a compare when a file is dropped. Wait for explicit user confirmation.
- Files must remain local; no HTTP requests, cloud services, analytics, or telemetry.

### 3.2 Mode drop-down (required)

Use `QComboBox` containing exactly these initial options:

1. **General — Cell by Cell**: compare common worksheet names and cell addresses; best for layout-preserving revisions.
2. **General — Match Records**: compare tables by user-selected identity columns, ignoring row reordering; best for registers.
3. **Engineering — PLC / Tag Records**: a preset of the record-matching engine with configurable tag matching, engineering-oriented fields, ignore rules, and warnings.

Changing the mode must visibly update the relevant controls and help text. Never present disabled controls as if they are active. Remember the last mode/settings locally for convenience, but don't silently reuse a match key that is invalid for the newly selected files.

### 3.3 Worksheet selection and preview

- For `.xlsx`/`.xlsm`, list sheets by name, with ability to compare **all matching sheets** or select specific sheet pair(s). If different sheet names exist, show clearly as **only in A** / **only in B**; optional manual pairing for renamed sheets.
- For CSV, expose a synthetic single sheet named after the file (or `CSV Data`), with CSV treated as a plain table.
- When importing CSV and XLSX together in record modes, require/select an Excel worksheet, and map the CSV to that sheet explicitly.
- Display a first-few-rows preview, column names, and duplicate-key/blank-key counts before comparing in record modes.
- In cell mode, do not claim a CSV contains formatting, formulas, hyperlinks or multiple sheets.

### 3.4 Results viewer

- Summary strip showing unique **Added records/cells**, **Removed records/cells**, **Modified records/cells**, **Changed fields**, **Unchanged (optional)**, **Warnings**, and **Errors**. Labels must match counting semantics and avoid double counting.
- Sortable and searchable differences table. Filters for status, sheet, column/field, engineering category, and severity.
- Columns: `Status`, `Worksheet`, `Record Key or Cell`, `Field`, `Original Value`, `Revised Value`, `Category`, `Severity`, and `Notes` (hide irrelevant fields based on mode).
- Clicking a result should reveal both relevant original/revised context values, with row index/cell address where available.
- For large result sets, use Qt model/view (`QAbstractTableModel` + `QSortFilterProxyModel`), not thousands of embedded row widgets.
- Long operations occur in a `QThread`/worker (or comparable Qt pattern). Keep GUI responsive, show progress where measurable, support cancellation between processing stages, and show actionable error messages.

---

## 4. Supported file formats and import rules

### CSV

- Support `.csv` with correct quoted fields, embedded delimiters/newlines, and UTF-8 BOM. Offer encoding detection/fallback and user-selectable encoding (`utf-8-sig`, `utf-8`, `cp1252`); report when fallback is used.
- Auto-suggest delimiter (comma, semicolon, tab) with preview and override controls if needed.
- **Preserve identifiers as text**, including leading zeros, hex-like values, PLC addresses, IDs, and dates that might otherwise auto-convert. Do not silently convert `00123` to `123` or empty to `NaN`.
- Distinguish empty, blank/whitespace, and non-empty values through an explicitly chosen normalisation policy.
- Do not interpret CSV text that begins `=` as an executable formula.

### Excel

- Read `.xlsx` (and ideally `.xlsm`) with `openpyxl`. Compare formula **expressions**, not cached/evaluated results, by default. Do **not** evaluate Excel formulas or run macros.
- Optionally support `data_only` cached values as an explicitly labelled view when available; cached values can be stale or absent.
- Capture cell value, formula text, number format, font (including strike-through), fill, border, alignment, protection, and hyperlink target. Some advanced Excel visual behaviour (e.g. conditional formatting's rendered appearance, themes and embedded shapes) may not be reproduced; document clearly.
- Read-only importing: never overwrite or alter the source workbooks. Treat `.xlsm` macros as untrusted data; do not execute them.
- Support blank sheets, merged cells and sparse worksheets gracefully, without comparing the entire 1,048,576 x 16,384 theoretical Excel grid.
- `.xls` legacy binary format is out of scope for version 1. Show an actionable unsupported-format message rather than crashing.

### Robustness and safety

- Validate paths, size, extension, permissions, CSV structure, and worksheet availability. Handle missing/unreadable/corrupted files gracefully.
- Provide warnings for huge inputs; do not freeze the UI. Avoid quadratic matching algorithms for large record tables.
- Avoid any network, external database or background upload. Never execute formulas or macros found in inputs.

---

## 5. Precise comparison semantics

### 5.1 Mode 1 — General: Cell by Cell

Use worksheet-name matching by default. Compare each populated cell (and optionally styled/linked otherwise-empty cells) at the **same address**, e.g. `H15` against `H15`.

Classify:

- **Added cell:** empty/nonexistent in A, populated in B.
- **Removed cell:** populated in A, empty/nonexistent in B.
- **Modified cell:** both populated but compared values/formulas differ; or selected metadata differs.
- **Unchanged cell:** compared attributes equivalent.
- **Added/removed worksheet:** sheet exists only in one workbook. Summarise separately and expose affected cells where useful, without counting them twice in the top-line summaries.

Default checks: cell value and formula expression. Optional toggles: formulas, hyperlink target, number format, fill, font (including strikethrough), border, alignment and other style attributes. **Visual formatting changes** should be a separate difference category, not conflated with value changes.

A row insertion may cascade into multiple cell-address differences. State this prominently, and direct users to **General — Match Records** for table-style comparisons; do not imply the algorithm can infer semantic row insertions from cell-coordinate differences.

### 5.2 Mode 2 — General: Match Records

Treat the selected worksheet / CSV as a table with header row (default first row; configurable header row). Compare **records by user-selected one or more key columns**. The order of the records must not matter.

- Preselect exact matching common column names when possible; provide manual mapping when column labels differ or case/spacing differs.
- Let users choose single or composite keys. Reject/report a missing key column.
- Handle blank keys and duplicate keys **explicitly**: show an Ambiguous/Unmatched diagnostic category. Do not pair duplicate keys arbitrarily and generate untrustworthy modifications.
- Match unique keys and classify each as Added (B-only), Removed (A-only), Modified (shared key with one or more changed fields), or Unchanged.
- Compare shared columns and report columns added/removed separately. A column change should not silently become thousands of individual missing data values without a clear structural change category.
- Store source row numbers for traceability but do not use them as identity in this mode.
- Offer normalisation switches: trim leading/trailing whitespace, case-sensitive vs insensitive comparison, blank == empty, and numeric equivalence where safe. Defaults should **preserve differences**; any enabled normalisation must be visible in reports.

### 5.3 Mode 3 — Engineering: PLC / Tag Records

Build **on the General — Match Records engine**, with a practical preset for SCADA tag CSV exports and PLC-style registers. It must still support manual field mapping/configuration for other engineering databases.

**Default match key:** `Tag Name` (when present; request another key if absent). A tag matched by name can be moved to another row without being considered added/removed.

**Engineering fields to prioritise when present:**

| Source column / possible label | Classification |
|---|---|
| `Tag Name` | Record identity |
| `Address` (sometimes called PLC Address) | PLC address / mapping |
| `I/O Device` | Device/interface |
| `Data Type` | Data type |
| `Equipment` | Equipment association |
| `Item Name` | Equipment/item name |
| `Comment` | Description |
| `Eng Units` | Engineering units |
| `Raw Zero Scale`, `Raw Full Scale` | Raw scaling |
| `Eng Zero Scale`, `Eng Full Scale` | Engineering scaling |
| `Deadband` | Deadband |
| `Format` | Display formatting |
| `Cluster Name` | Cluster / namespace |
| `Historize`, `Write Roles` | Operational/configuration properties |

**Administrative fields offered as preselected 'Ignore' options** (configurable, not hard-coded exclusions): `Project`, `OID`, `Unique ID`, `EDITCODE`, `LINKED`, `TAGGENLINK` and project-specific identifiers. All user-selected ignores must be listed in the exported report. Leave critical engineering columns compared by default.

Engineering results should be grouped or filterable by:

- Tag added/removed.
- PLC address changed.
- Data type changed.
- I/O device or cluster changed.
- Raw/engineering scaling changed.
- Units, deadband, or format changed.
- Description, equipment association, or other metadata changed.

**Warnings (clearly labelled as checks, not necessarily defects):**

- Duplicate tag identifiers within an import.
- Missing/blank tag identifiers.
- Duplicate address **within the relevant device/cluster namespace** when rules indicate a possible conflict; provide a configurable exception mechanism. Do not flag identical numeric addresses across unrelated devices as automatically invalid.
- Changed address for an existing tag.
- Changed type or scaling; classify as requiring engineering review, not automatically unsafe.
- Missing scaling limits, if an optional data-quality rule is enabled.

**Important:** Preserve complex addresses such as `S7:[PLC1]DB620,Real48,1` **verbatim**, unless the user enables and can inspect a particular parsing rule. Do not attempt to coerce them into plain integers or infer addresses from them. Provide a raw-value comparison and show the original/revised string.

### 5.4 Counts and semantics

Do not mix **number of modified tags** with **number of differing fields**. Example: one tag with five changed fields is **one modified record and five field differences**. Similarly, administrative changes ignored by the profile should not inflate engineering change counts.

Reports and summary labels must clearly describe:

- number of sheets compared;
- added, removed, modified records/cells;
- total individual field/attribute differences;
- ignored fields;
- warnings/ambiguities;
- applied normalisation options.

### 5.5 Blank values and string fidelity

- Do not discard strings with leading zeros or distinguishable PLC addresses.
- Do not silently treat a blank cell, literal string `None`, string `NaN`, and number 0 as equal.
- Ensure numeric and text handling is defined and tested. A spreadsheet number `1` and CSV string `1` may be equivalent in an explicitly enabled numeric-equivalence mode, but must not cause miscomparison of identifiers such as `001`.
- Show the original raw values, with any normalised view separately labelled.

---

## 6. Comparison profiles and settings

Provide a **Settings** section/dialog for reusable local profiles:

- Built-in: `General — Cell by Cell`.
- Built-in: `General — Match Records`.
- Built-in: `Engineering — PLC / Tag Records`.
- Users can duplicate and save named presets, e.g. `PlantSCADA Tag Export` or `I/O Schedule`.
- Profiles store mode, match key(s), source-field mappings, ignored columns, normalisation switches, and engineering validation toggles.
- Save preferences to local application configuration (JSON or `QSettings`), not inside the input files. Ensure malformed settings recover safely to defaults.
- Include **Reset to defaults** and a readable summary of active comparison settings in the final report.

In the engineering mode, the mode selection drop-down remains accessible at all times; users should never be locked into engineering-only logic.

---

## 7. Report export requirements

### 7.1 Required: `.xlsx` comparison report

Generate a separate, timestamped Excel workbook, e.g. `Comparison_ST045_to_ST045GT_2026-10-27_104500.xlsx` (actual timestamp at export, sanitized filename).

Include these sheets where applicable:

1. **Summary** — input filenames, comparison timestamp, mode, sheet mapping, match key, settings, counts, warnings, and a concise interpretation guide.
2. **Differences** — one row per changed field/cell/attribute, with status, sheet, key/cell address, original value, revised value, category, severity, and original/revised row references.
3. **Added Records** — records present only in B (record modes).
4. **Removed Records** — records present only in A (record modes).
5. **Warnings** — duplicate/blank keys, possible duplicate addresses, unsupported attributes and ambiguities.
6. **Structural Changes** — added/removed sheets and columns where applicable.

Quality requirements:

- Excel autofilters; frozen header; legible widths/wrapping; consistent colours (green added, red removed, amber modified, grey unchanged); dates/times unambiguous.
- Export the full dataset of differences even if the GUI table is filtered, **or** offer an explicit choice for `All Results` vs `Filtered Results`.
- No automatic modification of source files.
- Escape/force **untrusted imported text** as literal cell content so a CSV field beginning `=`, `+`, `-`, or `@` cannot be turned into a spreadsheet formula. Test this for both CSV and Excel report exports. Do not create active links or executable formula payloads from imported values.
- The report should indicate if a feature was excluded or not comparable (e.g. formatting when one input was CSV).

### 7.2 Required: `.csv` export

A flat difference list with the same key columns and UTF-8 BOM for easy Excel opening. Prevent formula injection on opening exported CSVs; document any protective prefixes as needed.

### 7.3 Nice to have (not a blocker for version 1)

Printable PDF executive summary, multi-format reports, and saved comparison sessions.

---

## 8. Suggested code architecture

Keep the GUI separate from the file-import/compare/export logic so it can be unit tested without a desktop session.

```text
witthoft-spreadsheet-compare/
├── README.md
├── pyproject.toml                   # or requirements.txt with pinned/compatible versions
├── requirements-dev.txt
├── .gitignore
├── src/
│   └── witthoft_compare/
│       ├── __init__.py
│       ├── __main__.py              # python -m witthoft_compare
│       ├── app.py                   # QApplication / startup
│       ├── gui/
│       │   ├── main_window.py
│       │   ├── drop_zone.py
│       │   ├── results_model.py
│       │   ├── settings_dialog.py
│       │   └── comparison_worker.py
│       ├── core/
│       │   ├── models.py            # canonical source/record/difference objects
│       │   ├── import_csv.py
│       │   ├── import_excel.py
│       │   ├── sheet_mapping.py
│       │   ├── cell_compare.py
│       │   ├── record_compare.py
│       │   ├── engineering_rules.py
│       │   ├── normalisation.py
│       │   └── compare_service.py
│       ├── reporting/
│       │   ├── excel_report.py
│       │   └── csv_report.py
│       └── config/
│           └── profiles.py
├── tests/
│   ├── fixtures/
│   ├── test_import_csv.py
│   ├── test_import_excel.py
│   ├── test_cell_compare.py
│   ├── test_record_compare.py
│   ├── test_engineering_rules.py
│   ├── test_exports.py
│   └── test_gui_smoke.py
├── scripts/
│   ├── setup_windows.ps1
│   ├── run_windows.ps1
│   └── build_windows.ps1
└── docs/
    ├── USER_GUIDE.md
    ├── ARCHITECTURE.md
    └── LIMITATIONS.md
```

Adapt layout if the repository already has a sensible architecture. Use small data models/dataclasses or typed structures for `WorkbookSnapshot`, `SheetSnapshot`, `Record`, `CellSnapshot`, `Difference`, `Warning`, `ComparisonSettings`, and `ComparisonResult`.

Engine guidance:

- Provide a single orchestrator `compare(original, revised, settings) -> ComparisonResult` that the GUI and tests share.
- Importers create consistent canonical structures. Keep source file paths, original addresses/row numbers, and raw values for provenance.
- Use dictionaries/hash maps for record matching to support near-linear comparisons when keys are unique.
- Distinguish errors from warnings and uncertainty; never silently drop unmatched records.
- Use logging for diagnostics, with care not to log sensitive plant information unnecessarily. Do not log entire input datasets by default.
- Keep processing and UI code decoupled to support future additions (e.g. more file formats or mapping conventions).

---

## 9. Sample engineering input specification

The user previously compared the following two **PlantSCADA-style CSV exports**:

- `ST045_dump.csv` — nominal original file.
- `ST045GT_dump.csv` — nominal revised file.

**These samples may not be available in the Codex working directory.** If supplied separately, use them for manual end-to-end verification; otherwise generate synthetic tests with their documented schema. Do not fabricate actual comparison results if the files are not present.

Actual known column names in this example:

```text
Equipment,Item Name,Tag Name,Cluster Name,I/O Device,Data Type,Address,
Comment,Deadband,Eng Units,Format,Raw Zero Scale,Raw Full Scale,
Eng Zero Scale,Eng Full Scale,Custom 1,Custom 2,Custom 3,Custom 4,
Custom 5,Custom 6,Custom 7,Custom 8,Write Roles,Historize,Project,
EDITCODE,LINKED,OID,REF1,REF2,CUSTOM,TAGGENLINK,Unique ID
```

Relevant characteristics:

- `Tag Name` provides record identity.
- `Address` is the PLC/instrument communication address, sometimes a complex string (e.g. `S7:[PLC1]DB620,Real48,1`).
- `I/O Device` identifies the logical device; `Data Type` includes values such as `REAL` and `LONG`.
- Scaling columns often contain numeric-looking text.
- Some fields such as `Project`, `OID` and `Unique ID` change across exports while not indicating an engineering configuration change; allow them to be ignored by default in the engineering preset, with the full list visible and overridable.

Do **not** hard-code ST045 identifiers, row counts, date stamps or proprietary tag naming schemes into the application. The tool must work with unrelated files and future projects.

---

## 10. Testing specification — implement and run

Use `pytest` for the engine, importers and exporters, plus a GUI smoke test (can run headless with Qt platform offscreen if necessary). Create fixtures instead of relying solely on private production exports.

Required test scenarios:

1. **CSV equality:** two identical CSV files produce no changes.
2. **CSV column quoting:** fields containing comma, quote, newline import correctly.
3. **CSV fidelity:** leading zeros in IDs, complex S7/PLC addresses, empty vs whitespace, UTF-8 BOM and Windows encoding.
4. **Different order:** two CSV files with identical unique records in different orders show zero changes in record mode.
5. **Added/removed records:** one added, one removed and one modified record reported with accurate counts.
6. **One record, multiple fields:** one modified tag with three changed fields reports one modified tag and three field differences.
7. **Duplicate/blank keys:** no arbitrary pairing, clear ambiguity warnings.
8. **Composite key:** match correctly on `(Plant, Tag Name)` or another configured composite key.
9. **Workbook sheets:** same-name sheets compared; added/removed worksheets correctly flagged; extra/missing columns identified in record mode.
10. **Formula differences:** `=SUM(A1:A10)` vs `=SUM(A1:A11)` detected as formula change without evaluation.
11. **Formatting changes:** strikethrough toggled on/off, hyperlink destination changed, number format changed; flags only when selected.
12. **Mixed formats:** CSV vs XLSX sheet in record mode, with explicit sheet selection and correct normalisation.
13. **Engineering profile:** `Address`, `Data Type`, `I/O Device` and scaling change categories; ignored `Project`/`OID` excluded from engineering change count.
14. **Address namespace:** duplicate address under separate devices not automatically a collision; suspicious reuse within same namespace flagged under configurable rule.
15. **Unsafe exports:** text starting `=HYPERLINK(...)`, `+`, `-`, `@` remains inert in exported `.xlsx` and is protected in exported CSV.
16. **Bad inputs:** nonexistent files, corrupt Excel, invalid CSV encoding, missing key, unsupported `.xls` produce user-friendly errors.
17. **GUI smoke:** Browse/drop handler, mode change, Compare button enablement, worker completion, results rendering and report export.
18. **Export validation:** generated workbook opens with openpyxl, has correct sheets/counts and is not the source file.
19. **Scale test:** synthetic files with 10,000+ records compare in reasonable time, without blocking the GUI.
20. **Cross-platform build honesty:** tests/build notes distinguish code tested in development environment from real Windows executable verified on Windows.

Also verify that the input files' checksums do not change after comparison and export.

---

## 11. Developer setup and Windows packaging

Set up a virtual environment and a reproducible dependency list. Target **Windows 10/11**, 64-bit Python 3.12 unless an installed environment requires compatible adjustment. Use a recent compatible set of PySide6, pandas, openpyxl, pytest and PyInstaller versions; pin them after testing.

Expected commands (update to actual project structure):

```powershell
# From the project root (PowerShell)
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -r requirements-dev.txt

# Start the development application
python -m witthoft_compare

# Run tests
python -m pytest -q

# Build distributable Windows application
.\scripts\build_windows.ps1
```

Packaging requirements:

- Use PyInstaller with all required runtime Qt platform plugins and assets. Prefer `--windowed` so no console pops up for engineers.
- Aim for `dist/WitthoftSpreadsheetCompare/WitthoftSpreadsheetCompare.exe` (one-folder build) as initial reliable output; consider `--onefile` when proven stable.
- Provide a branded name; application icon only if available or separately created. No dependence on a commercial icon pack or online service.
- Ensure the packaged executable does not require Python installed on the target workstation.
- Run and verify the executable **on a Windows computer** if access permits; otherwise supply the build script and document this remaining verification item.
- Handle Windows file paths, OneDrive folders, spaces in names, read-only inputs, and long paths where feasible.
- Provide a `README.md` for developers and `docs/USER_GUIDE.md` for engineers, including screenshots if practical.

---

## 12. Build sequence for Codex

Complete the following in order; do not stop after a scaffold:

**Phase 1 — Foundation**

1. Inspect/create project folder, environment, dependencies, logging and data models.
2. Implement CSV and Excel importers, file validation, and synthetic test fixtures.
3. Implement the pure record and cell comparison engines with deterministic outputs and comprehensive unit tests.

**Phase 2 — Engineering profile**

4. Implement the PLC/tag mode as a configurable preset layered on the record engine.
5. Add priority engineering classifications, ignored administrative columns, and relevant warning rules.
6. Add tests matching the ST045-style schema.

**Phase 3 — GUI**

7. Implement the two drag-and-drop boxes and Browse buttons; file previews and Excel sheet selection.
8. Implement the mode drop-down, key selector, settings/preferences and responsive Compare/Cancel workflow.
9. Implement the result summary, sortable/filterable table, and meaningful detail view.

**Phase 4 — Reporting and validation**

10. Implement `.xlsx` and `.csv` exports with safe escaping and reliable counts.
11. Run all tests, resolve failures, verify source files remain untouched, and manually exercise sample use cases.
12. Build with PyInstaller and verify the Windows GUI executable if running on Windows.
13. Write complete run, build, deployment and usage documentation.

Do not substitute partial generated source snippets for actual project files. If blocked by unavailable Windows tooling, complete all platform-independent code and scripts and clearly state the limitation.

---

## 13. Definition of done / user acceptance checklist

- [ ] Application runs as an offline Windows desktop GUI.
- [ ] Two distinct file drop targets accept CSV and XLSX via Explorer drag-and-drop and Browse.
- [ ] Original/Revised are clearly distinguished, with Swap and Replace/Clear controls.
- [ ] Mode drop-down offers all three required comparison modes.
- [ ] CSV import maintains identifiers, correct encoding and quoted field structure.
- [ ] Excel import supports multiple worksheets, formula expression comparison and optional formatting/hyperlinks.
- [ ] General cell mode compares cells/worksheet structure accurately.
- [ ] General record mode matches by user-selected unique/composite keys and ignores row order.
- [ ] Engineering mode defaults to `Tag Name` when present and highlights address, datatype, device and scaling changes.
- [ ] Project/OID/Unique ID exclusions are configurable, shown to the user, and reflected in exports.
- [ ] Duplicate/blank keys are flagged rather than mismatched silently.
- [ ] Differences are presented in a clear, searchable, sortable, filterable GUI table.
- [ ] Engineering counts separate modified tags from individual changed fields.
- [ ] Reports can be exported to Excel and CSV with sensible names, categories and source references.
- [ ] Untrusted imported cell content cannot become an executable formula in the reports.
- [ ] Sources are never modified and no external service receives spreadsheet data.
- [ ] App remains responsive during large comparisons and errors are handled cleanly.
- [ ] Unit/integration tests cover major workflows and pass.
- [ ] README, user guide and documented Windows build process are complete.
- [ ] A Windows `.exe` is successfully created and tested when Windows access is available; otherwise deliver a reproducible Windows build script.

---

## 14. Priorities and scope control

**Must deliver for v1:** Windows GUI, file drag/drop, `.csv`/`.xlsx` import, all three selection modes, correctness of matching/differences, basic engineering preset, filtering/search, report export, tests and packaging instructions.

**Should deliver in v1 if feasible:** `.xlsm` read-only import; composite keys; configurable field mapping and profiles; formatting/hyperlink checks; background progress and cancellation; worksheet pairing.

**Defer if necessary:** PDF reporting, automatic semantic row alignment without keys, OCR/scanned documents, full Excel calculation/evaluation engine, macro comparison/execution, network collaboration and database integration.

If time is limited, prioritise **accurate comparisons and an operational end-to-end application** over cosmetic design and speculative features. Do not mark unfinished advanced features as complete.

---

## 15. Final response format for Codex

When the application has been implemented, provide:

1. **Implemented:** concise list of working features and comparison modes.
2. **Files created/modified:** main file paths and brief descriptions.
3. **How to run:** exact command and current directory.
4. **How to build Windows executable:** exact command, expected output path, and whether the build was actually tested on Windows.
5. **Testing:** number of tests and pass/fail results, including any skipped tests.
6. **Known limitations:** specific remaining gaps, not generic assurances.
7. **How an engineer uses it:** drop A and B, select the mode/key, compare, filter, export.

**Begin implementation now.**
