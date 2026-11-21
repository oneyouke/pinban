# Desktop Imposer Pro V3.0 — UI Redesign Specification

## Product direction
Rebuild the desktop workspace around the supplied Quite Imposing Plus 5.4 reference screenshot. The screenshot is the primary visual and interaction reference. This is a native Windows desktop prepress application, not a web dashboard.

## Window composition
- Top menu: 文件、编辑、视图、工具、书册、窗口、帮助.
- Main toolbar: open file, open project, save, undo/redo, settings, current job name, prominent 拼版 action, configuration/profile selector, help.
- Left navigation rail: 基本、工具、页面、标记、图像、处理、印前、变量数据.
- Left control dock: context-sensitive tabs and parameter forms. Basic tabs: 基本、书册、版面、外观. A page-list panel is docked below the settings panel.
- Center workspace: tabs 预览、页面视图、拼版模板库. Preview toolbar includes fit, zoom, page navigation, pan, single-sheet/tile view, marks visibility.
- Right inspector: tabs 属性、层. Sections: 文件信息、页面尺寸、出血设置、标记设置、色彩管理. Sections can collapse.
- Bottom status bar: page count, sheet size, imposed count, zoom, readiness/errors.

## Interaction principles
- Preserve the dense, technical prepress workflow and dark neutral chrome shown in the reference.
- Central sheet preview is the visual focus; settings are editable in docks without modal dialogs for routine changes.
- Selecting a left-rail category changes the control dock while keeping the document and preview visible.
- Selecting a source page updates the right inspector. Selecting an imposed sheet shows sheet-level properties.
- Every numeric control has units and validation. Invalid dimensions, negative gaps, impossible margins, or unsupported combinations show inline errors.
- Preview updates after parameter changes; expensive recalculation is debounced and cancellable.
- Dock panels are resizable; preview zoom and panel sizes persist per user.
- All operations remain undoable where practical; destructive actions require confirmation.
- Keyboard navigation, tooltips, accessible labels, and 100%/125%/150% Windows DPI scaling are required.

## Basic imposition panel
Fields: finished page width/height, stock sheet width/height, orientation, imposition mode, copies per sheet, horizontal/vertical gap, top/bottom/left/right gripper and margins, bleed, creep allowance, auto-fit/adjust-to-sheet.
Initial modes: N-up, repeat/step-and-repeat, cut-stack, manual placement.
Provide common stock presets plus custom dimensions.

## Booklet panel
Modes: saddle stitch, perfect bound, signature/book sections. Settings: binding edge, sheet signature, page creep, shingling, duplex flip, blank-page insertion, reading direction. Preview must show ordered spreads and front/back sheets.

## Layout panel
Grid rows/columns, gutter, alignment, rotation, scaling policy, page order, mixed page sizes, auto-rotation, trim/bleed boxes, fit/fill behavior.

## Appearance panel
Background, page border, separation guides, page labels, sheet labels, rulers, guides, and preview overlays.

## Pages panel
PDF file list, thumbnails, page numbers, select/deselect, reorder, rotate, delete/extract, duplicate, range selection, search/filter, source-file grouping.

## Right-side properties
- File info: file name/path, media/trim/bleed sizes, page count, PDF version, modified date.
- Page dimensions: width/height with lock aspect ratio.
- Bleed: numeric value, use document bleed.
- Marks: crop marks, registration marks, color bars, page information, edit marks.
- Color: source RGB/CMYK profile, output CMYK profile, embed profile, preserve spot colors. Never silently convert colors.

## Output workflow
Export dialog must include output file, PDF standard/profile where supported, preserve vectors, embed fonts when permitted, page boxes, marks, output intent, duplex sequence, preflight summary, and a final preview. Never claim PDF/X compliance unless independently validated.

## Implementation architecture
Keep existing proven imposition/export logic where compatible, but replace the main workspace shell and dock arrangement. Separate UI widgets from document model, imposition engine, PDF renderer, marks engine, and export pipeline. Avoid coupling business logic to Qt widgets.

Suggested modules:
- app/main.py — application bootstrap
- app/ui/main_window.py — menus, toolbar, docks, status bar
- app/ui/navigation_rail.py — left category rail
- app/ui/control_dock.py — context-sensitive parameter tabs
- app/ui/page_list_dock.py — source files and thumbnails
- app/ui/preview_workspace.py — preview tabs and zoom toolbar
- app/ui/inspector_dock.py — right properties/layers
- app/ui/widgets/ — reusable unit fields, collapsible sections, color/profile selectors
- app/core/document.py — source document/page model
- app/core/imposition/ — N-up, repeat, booklet, cut-stack, manual layout
- app/core/geometry.py — sheet/page geometry and constraints
- app/core/marks/ — crop, registration, color bars, page info
- app/core/rendering/ — PDF preview rendering/cache
- app/core/export/ — vector-preserving PDF composition and validation
- app/presets/ — paper, stock, templates and saved profiles
- app/storage/ — project settings, recent files, SQLite
- tests/ui/ — dock layout and interaction tests
- tests/core/ — geometry, page order, duplex, bleed and export regression tests

## Acceptance criteria for the first UI milestone
1. Launches on Windows 10/11 with the reference four-region layout.
2. Menus, toolbar, navigation rail, left control dock, center preview tabs, right inspector and bottom status bar are present.
3. Dock panels can be resized, collapsed and restored.
4. Opening a PDF populates thumbnails and file/page metadata.
5. Selecting pages updates the inspector; changing sheet/page size updates the preview.
6. Zoom, fit, pan, marks visibility and page selection work.
7. No placeholder controls that look functional but do nothing.
8. Existing V2.4 regression tests remain green before replacing any production workflow.

## Compatibility and licensing gate
Before shipping a closed-source commercial Windows build, verify the exact licenses of Qt/PySide6, PDF rendering/composition dependencies, and all bundled libraries. Preserve the original PDF vectors, text, fonts, transparency and color information where technically supported; disclose any unsupported feature rather than rasterizing silently.
