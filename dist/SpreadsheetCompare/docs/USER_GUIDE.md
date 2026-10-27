# Engineer user guide

## Open and import

Open `SpreadsheetCompare.exe` from its distribution folder. Keep `_internal` alongside the executable. All spreadsheet data stays local.

The application is named **Spreadsheet Comparison Tool**. The portable executable is now `dist\SpreadsheetCompare\SpreadsheetCompare.exe`; `Launch Spreadsheet Compare.cmd` in the repository root starts it using a relative path. Preferences use the neutral `%LOCALAPPDATA%\SpreadsheetCompare` folder; settings saved under an older application identity are not automatically imported.

The application uses a dark theme throughout the main window, settings, column menu and file-selection dialogs. Green, red and amber result backgrounds distinguish added, removed and modified/review entries, with light text for readability.

1. Drop exactly one supported file into **ORIGINAL (A)** and one into **REVISED (B)**, or use each box's **Browse** button. Accepted formats: CSV, XLSX, and XLSM. The application never executes workbook macros or evaluates formulas.
2. Read the filename, sheet list and notices. Hover over the filename for its full path. Select **Input previews / key diagnostics** below the results to inspect raw input rows and import notices. Imports run in the background; comparison never starts automatically.
3. For CSV, automatic delimiter detection supports comma, semicolon and tab. Automatic encoding first tries UTF-8 BOM/UTF-8, then Windows cp1252 with a visible warning. If the preview is wrong, choose encoding/delimiter and press **Re-import**. Bad quoting or inconsistent column counts are reported rather than guessed.
4. Dropping or browsing a new file replaces that side after a successful import. **Clear** removes a side. **Swap A / B** reverses the comparison direction. **Reset** clears both inputs and restores mode defaults.

Files larger than 50 MB receive an import warning. Very large Excel files can take time and substantial RAM. The progress bar is indeterminate during operations without a measurable total. **Cancel** or Escape requests cancellation; some library loading/saving stages must finish before cancellation is observed.

## Choose a mode

| Mode | Use it for | Identity |
| --- | --- | --- |
| General — Cell by Cell | Revisions retaining worksheet layout | Worksheet name + cell address |
| General — Match Records | Registers whose rows may be reordered | Checked key columns |
| Engineering — PLC / Tag Records | PLC / SCADA tag exports and I/O schedules | Tag Name proposed, or manually checked keys |

Cell mode compares values and stored formula expressions by default. A row insertion can generate many cell-address differences; select Match Records when records should follow their IDs. Style and hyperlink checks are optional and available only for two Excel inputs. Formatting covers number formats, font (including strikethrough), fill, border, alignment and protection. It compares stored metadata, not a rendered screenshot of Excel.

Record modes require a table with unique column headers. Row 1 is the default header. Set separate A/B header rows in **Settings / Profiles** when needed, apply, and then map fields using the refreshed column list. Check one key for simple IDs or multiple keys for composite identities. Keys use exact header labels unless explicitly mapped. Leading zeros are preserved.

Before comparing, review duplicate-key and blank-key counts in the preview. Duplicate identities on either side quarantine **all records with that identity on both sides**. Blank identities also remain ambiguous. These rows appear as diagnostics, with source rows/context, and are excluded from confirmed added/removed/modified/unchanged counts. Fix the inputs or choose better composite keys to resolve them.

## Worksheets and differently labelled fields

**All matching sheets** compares exact shared worksheet names. Unpaired sheets existing only on one side appear as structural additions/removals; a worksheet rename is never inferred. Cells in unpaired sheets are excluded from top-line cell counts. Same-name sheets intentionally left out are listed as excluded notices.

Choose **Selected sheet pair**, then choose A and B sheets to compare differently named sheets. For CSV versus Excel the application selects this pairing mode: explicitly review and select the desired Excel worksheet. A CSV has one synthetic `CSV Data` sheet. For several manual pairs, open **Settings / Profiles → Worksheet pairs**, add each pair, and apply. The main screen then shows **Custom pairs**.

In **Settings / Profiles → Fields / ignores**, map Original column labels to Revised column labels. Mapping must be one-to-one; unmatched columns are structural changes rather than thousands of missing-value changes. Column mappings, keys and ignores apply to all selected worksheet pairs. Use separate comparisons/profiles when sheets have unrelated schemas. Keys available on the main screen must be present across selected pairs.

## Engineering review

Engineering mode proposes `Tag Name` when available. You may select other or composite keys. `Address`/`PLC Address`, `Data Type`, `I/O Device`, `Cluster Name`, scaling, units, deadband, format, comments and equipment fields receive specific categories.

The default ignored fields are `Project`, `OID`, `Unique ID`, `EDITCODE`, `LINKED`, and `TAGGENLINK`. These are shown beside the keys, can be changed in Settings, and are listed in the report. Critical engineering columns remain compared by default.

Address/type/device/scaling changes generate **Review** checks; these do not establish a defect or unsafe condition. Duplicate addresses are checked within the stored I/O device and cluster namespace. Identical addresses on different devices or clusters do not automatically conflict. If namespace fields are absent, checks share an unknown namespace and require interpretation. For intentional address reuse, list exact raw addresses under **Engineering exceptions**, or disable the duplicate-address check. Optional missing-scaling checks apply to every record and must be reviewed for engineering relevance.

Complex addresses such as `S7:[PLC1]DB620,Real48,1` remain intact. No PLC-address parsing or integer conversion occurs.

## Normalisation and local profiles

Defaults preserve differences: no trimming, case-sensitive values/keys, blank cells distinct from empty text, and numeric strings distinct from Excel numbers. In Settings you may enable trimming, case-insensitive matching, blank/empty/whitespace equivalence, and numeric equivalence. Numeric equivalence converts only simple decimal-looking strings without leading zeros: `1` may equal numeric 1, but `001` remains text. Literal `None` and `NaN` are always text, not blanks. Raw values remain visible; enabled normalisation is recorded in reports.

**Save as…** duplicates active dialog settings into a named local profile; press **OK** to commit. Built-in profiles can be reloaded, and **Reset to defaults** resets the selected mode. Preferences live at `%LOCALAPPDATA%\SpreadsheetCompare\profiles.json`. Malformed preferences fall back safely. Newly imported files cause worksheet and key revalidation. Recheck mappings and keys after changing files or profiles.

## Compare, inspect and export

Click **Compare**. The interface stays responsive during import/comparison/export; file/settings controls are temporarily disabled to keep the operation consistent. Select a result row to see raw values, their types, original/revised row numbers and complete row context.

The results grid shows **Original (A) Row**, **Original Value**, **Revised (B) Row**, **Updated Value**, **Original Entry (A)** and **Updated Entry (B)**. Source row numbers are 1-based and include the header row; CSV numbers refer to logical records, so quoted multiline fields still occupy one record. Row numbers can differ when records move. Full entries contain the complete original/revised table record, or the populated source row cells in cell mode. Scroll horizontally for the entry columns, hover for their full text, or select the result to read the expanded entries and source filenames below. Added/removed records leave the absent side empty. Excel and CSV exports include both source row numbers and both full entries.

Summary counts describe unique records or cells. One modified tag with three changed fields counts as **one modified record and three changed fields**. Added/removed record payloads do not inflate the changed-fields count. Structural sheet/column changes and warnings are separate. Imported informational notices appear in the results and Warnings report sheet but are not included in the warning total unless severity is Warning or Review.

Click column headings to sort. Search across result columns or filter status, worksheet, field, engineering category and severity. Ctrl+F focuses Search. Export buttons always write **all results**, regardless of filters. Choose a separate writable report filename; original inputs cannot be overwritten. Close an existing report in Excel before replacing it.

Open **Selected Statuses** to check any combination of statuses to display (for example, Added and Modified together). The menu stays open while you check or uncheck statuses. **Select all statuses** restores all rows, and **Clear selection** hides all rows. Every new comparison starts with all available statuses selected. Status choices combine with Search and the other filters; exports continue to include all results.

Use **Columns** above the grid (or right-click a column heading) to check which result columns are visible. The menu stays open so you can change several checkboxes. **Show all columns** restores the full view; at least one column stays visible. Your selection is remembered locally in `view.ini` alongside your profiles and survives new comparisons and restarts. These choices affect the viewing window only: search still includes hidden columns, and Excel/CSV reports retain every output column.

- **Excel:** Summary (settings/counts/interpretation), Differences, Added Records/Removed Records where applicable, Warnings and Structural Changes. Header rows are frozen and filtered; changes are coloured. Long values exceeding Excel's cell text limit are stored in numbered chunks on a Long Text sheet. Imported strings are literal text; no active formulas/hyperlinks are created.
- **CSV:** a flat UTF-8 BOM result list containing differences, structural changes and diagnostics. Text beginning with formula trigger characters, including after leading whitespace, is prefixed with an apostrophe to keep it inert in spreadsheet software. That protective apostrophe may be visible and is not part of the input value. CSV is not a full settings/summary archive; keep the Excel report for that purpose.

The suggested report name includes both input stems and the current local timestamp. Comparison times include the machine's timezone offset; set the workstation clock/timezone correctly.

## Troubleshooting

Unsupported `.xls`: save a copy as `.xlsx` or CSV in Excel first. Encrypted/corrupt Excel: repair or save an unencrypted copy. Missing key: reselect a key or map differently labelled columns. Missing headers: adjust the header-row settings. CSV encoding error: choose cp1252 or re-export UTF-8. Permission/locked report: close it in Excel or select another folder.

The application never uploads files and does not modify inputs. It does not compare macro code, calculate formulas, infer semantic row insertions, or reproduce Excel's conditional-formatting appearance. See [limitations](LIMITATIONS.md).
