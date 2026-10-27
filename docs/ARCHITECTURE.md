# Architecture and developer notes

`src/witthoft_compare` contains independent core, reporting, config and GUI packages. `python -m witthoft_compare` starts the application; `scripts/launcher.py` is the PyInstaller entry point.

## Data flow

`import_service.import_file` validates paths/extensions and dispatches to text-preserving CSV import or openpyxl Excel import. Importers return `WorkbookSnapshot` / `SheetSnapshot` / `CellSnapshot` objects. Snapshots preserve file paths, original values, formula flags, supported cell metadata, merged ranges and import notices. Sources are opened for reading only. Excel imports discard external workbook link contents and do not preserve or execute macros.

`compare_service.compare(original, revised, settings) → ComparisonResult` resolves sheet pairs and dispatches to cell or record comparison. Inputs are not mutated. Result settings are copied so the exported report captures the comparison's actual configuration, including resolved worksheet pairs and excluded metadata. `normalisation.py` produces typed comparison keys; raw values are never overwritten with normalised values.

Cell comparisons iterate the sorted union of represented sparse cells. Excel defaults are compared for cells not instantiated on one side. Value/formula and each selected metadata attribute produce separate difference rows while each changed cell increments a unique-cell count once. Sheet/merge changes remain separate structural entries. CSV's absence of Excel metadata is explicitly reported and those checks are excluded.

Record comparison reads table headers from a configurable row, builds hash maps of typed composite keys, quarantines duplicated and blank identities, and compares unique shared records. Match construction and field comparison are linear in record count × field count; deterministic sorting for presentation adds O(n log n). Source rows are provenance only. Structural columns are compared once, not as repeated missing values. Added/removed records retain full raw payloads; modified fields retain both row contexts. Engineering rules layer categories and advisory validations onto this same engine.

## GUI concurrency and results

`gui/main_window.py` coordinates QWidget controls and immutable operation settings. `drop_zone.py` handles local-file URLs, Browse and one-file validation. `comparison_worker.Worker` executes imports, previews, comparison and export in QThread workers. Progress is delivered through Qt signals. A thread-safe event supports cooperative cancellation without terminating threads. Only the GUI thread mutates widgets.

The result grid uses `QAbstractTableModel` and `QSortFilterProxyModel`. Text search and five exact filters apply only to the viewer. Exports deliberately use the full `ComparisonResult`. Selecting a proxy-model row maps back to the source result to show full raw context.

`settings_dialog.py` edits normalisation, header rows, mapping/ignore lists, worksheet pairs, engineering rules and named profile copies. Profiles are stored as JSON in local application configuration with type validation, safe fallback and atomic replacement. Input files never contain application settings.

## Reports

Reporting is GUI-independent. All strings written to XLSX are explicitly assigned string cell type, preventing execution of imported formula expressions. CSV exports prefix possible formula trigger strings with an apostrophe. All result columns (including keys/sheet names/notes) receive protection. Long XLSX strings are chunked on an auxiliary sheet; XML-forbidden control characters are visibly escaped. Report writers reject resolved/hard-linked source targets and write a temporary file in the destination folder before atomic replacement. Cancellation before commit preserves an existing report.

## Validation and extension points

Tests use synthetic, small real CSV/Excel fixtures plus a 12,000-record scale case and Qt GUI tests. `self_test.py` exercises the actual packaged GUI against disposable fixtures and emits JSON, reports and a screenshot for deployment validation. No private production inputs were available.

Potential future extensions: cached-value view, per-sheet schemas, advanced Excel visuals, optional PDF summary, session saving and streamed import/reporting for very large datasets. Keep any such feature separate from conservative key matching and formula safety.
