# Desktop Imposer Pro V3.0 UI Prototype

## Run on Windows 10/11

Use Python 3.11 or 3.12 x64.

```powershell
cd v3
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-ui.txt
python run_ui.py
```

## Included in this first interface build

- Dark prepress-style main window based on the supplied reference layout.
- Top menu and toolbar, job name, imposition action and stock profile.
- Left navigation rail, contextual Basic/Booklet/Layout/Appearance tabs.
- Page-list dock with page search field.
- Center workspace tabs and a vector-drawn sheet preview.
- Right properties/layers inspector with page size, bleed, marks and color-profile controls.
- PDF open dialog, page count and first-page dimensions using PyMuPDF.
- Live preview updates for rows, columns, gaps, bleed and marks.
- Save current job settings to JSON.

## Important implementation boundary

This is the first runnable UI shell, not a production imposition/export engine. The canvas currently draws a schematic sheet layout and page labels; it does not yet place original PDF page content into an output PDF. Undo/redo, full booklet sequencing, color conversion, and production export must be connected to the audited V2.4 engine and validated with print-production regression fixtures before release.
