from pathlib import Path
import os

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()

# --- imposition.py ---
p = root / 'imposition.py'
s = p.read_text(encoding='utf-8')
old = '''    def _normalize_page(self, page):\n        p = copy.deepcopy(page)\n        try:\n            if int(p.get("/Rotate", 0) or 0) % 360:\n                p.transfer_rotation_to_content()\n        except Exception:\n            pass\n        return p\n'''
new = '''    def _normalize_page(self, page):\n        # Avoid deep-copying every page in large PDFs. Reader-backed PageObjects are\n        # safe to reuse for the common unrotated case; only rotated pages need a\n        # private copy before transfer_rotation_to_content() mutates them.\n        try:\n            rotation = int(page.get("/Rotate", 0) or 0) % 360\n        except Exception:\n            rotation = 0\n        if not rotation:\n            return page\n        p = copy.deepcopy(page)\n        try:\n            p.transfer_rotation_to_content()\n        except Exception:\n            pass\n        return p\n'''
if old not in s:
    raise SystemExit('SourceLibrary normalize block not found; V2.2.2 patch cannot apply safely')
s = s.replace(old, new, 1)

old = '''def _smart_impose_jobs(\n    loaded_jobs: list[tuple[InputJob, list]],\n    output_path: str | Path,\n    settings: ImpositionSettings,\n    library: SourceLibrary,\n    layout_override: dict | None = None,\n) -> dict:\n'''
new = '''def _smart_impose_jobs(\n    loaded_jobs: list[tuple[InputJob, list]],\n    output_path: str | Path,\n    settings: ImpositionSettings,\n    library: SourceLibrary,\n    layout_override: dict | None = None,\n    preview_sheet_limit: int | None = None,\n) -> dict:\n'''
if old not in s:
    raise SystemExit('smart impose signature not found')
s = s.replace(old, new, 1)

old = '    for sheet_idx, placements in enumerate(packed.sheets, 1):\n'
new = '''    rendered_sheets = packed.sheets[:preview_sheet_limit] if preview_sheet_limit else packed.sheets\n    for sheet_idx, placements in enumerate(rendered_sheets, 1):\n'''
if old not in s:
    raise SystemExit('smart sheet loop not found')
s = s.replace(old, new, 1)

old = 'def impose_jobs(jobs: Sequence[InputJob], output_path: str | Path, settings: ImpositionSettings, layout_override: dict | None = None) -> dict:\n'
new = '''def impose_jobs(\n    jobs: Sequence[InputJob],\n    output_path: str | Path,\n    settings: ImpositionSettings,\n    layout_override: dict | None = None,\n    preview_sheet_limit: int | None = None,\n) -> dict:\n'''
if old not in s:
    raise SystemExit('impose_jobs signature not found')
s = s.replace(old, new, 1)

old = '            return _smart_impose_jobs(loaded_jobs, output_path, settings, library, layout_override=layout_override)\n'
new = '''            return _smart_impose_jobs(\n                loaded_jobs, output_path, settings, library, layout_override=layout_override,\n                preview_sheet_limit=preview_sheet_limit,\n            )\n'''
if old not in s:
    raise SystemExit('smart impose dispatch not found')
s = s.replace(old, new, 1)

old = '''            for sheet_index in range(sheet_count):\n                front = writer.add_blank_page(width=sheet_w_pt, height=sheet_h_pt)\n'''
new = '''            render_sheet_count = min(sheet_count, preview_sheet_limit) if preview_sheet_limit else sheet_count\n            for sheet_index in range(render_sheet_count):\n                front = writer.add_blank_page(width=sheet_w_pt, height=sheet_h_pt)\n'''
if old not in s:
    raise SystemExit('duplex sheet loop not found')
s = s.replace(old, new, 1)

old = '''            for sheet_index in range(sheet_count):\n                dest = writer.add_blank_page(width=sheet_w_pt, height=sheet_h_pt)\n'''
new = '''            render_sheet_count = min(sheet_count, preview_sheet_limit) if preview_sheet_limit else sheet_count\n            for sheet_index in range(render_sheet_count):\n                dest = writer.add_blank_page(width=sheet_w_pt, height=sheet_h_pt)\n'''
if old not in s:
    raise SystemExit('simplex sheet loop not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# --- app.py: background, first-sheet preview ---
p = root / 'app.py'
s = p.read_text(encoding='utf-8')
old = '''        self._inspect_timer.start()\n\n        self._build_ui()\n'''
new = '''        self._inspect_timer.start()\n\n        # Keep preview merge/write work off the Qt event loop. Preview renders only\n        # the first imposed sheet while retaining the full calculated sheet count.\n        self._preview_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="impose-preview")\n        self._preview_future = None\n        self._preview_target_path: str | None = None\n        self._preview_timer = QTimer(self)\n        self._preview_timer.setInterval(100)\n        self._preview_timer.timeout.connect(self._collect_preview_result)\n        self._preview_timer.start()\n\n        self._build_ui()\n'''
if old not in s:
    raise SystemExit('preview executor insertion point not found')
s = s.replace(old, new, 1)

start = s.find('    def _run_impose(self, output_path: str):\n')
end = s.find('    def export_pdf(self):\n', start)
if start < 0 or end < 0:
    raise SystemExit('preview methods block not found')
replacement = '''    def _run_impose(self, output_path: str, *, preview_sheet_limit: int | None = None):\n        jobs = self.input_jobs()\n        if not jobs:\n            raise ValueError("请先添加至少一个 PDF 或图片文件")\n        return impose_jobs(\n            jobs, output_path, self._settings(), layout_override=self._layout_override,\n            preview_sheet_limit=preview_sheet_limit,\n        )\n\n    @staticmethod\n    def _run_preview_worker(jobs, output_path, settings, layout_override):\n        return impose_jobs(\n            jobs, output_path, settings, layout_override=layout_override,\n            preview_sheet_limit=1,\n        )\n\n    def generate_preview(self):\n        if self._preview_future is not None and not self._preview_future.done():\n            self.statusBar().showMessage("预览正在后台生成，请稍候…", 3000)\n            return\n        try:\n            jobs = self.input_jobs()\n            if not jobs:\n                raise ValueError("请先添加至少一个 PDF 或图片文件")\n            fd, path = tempfile.mkstemp(prefix="desktop_imposer_preview_", suffix=".pdf")\n            os.close(fd)\n            self._preview_target_path = path\n            self.preview_status.setText("正在后台生成首张拼版预览…")\n            self.statusBar().showMessage("正在后台生成拼版预览；界面可继续操作")\n            self._preview_future = self._preview_executor.submit(\n                self._run_preview_worker, jobs, path, self._settings(), self._layout_override\n            )\n        except Exception as exc:\n            QMessageBox.critical(self, "生成预览失败", str(exc))\n\n    def _collect_preview_result(self):\n        future = self._preview_future\n        if future is None or not future.done():\n            return\n        self._preview_future = None\n        path = self._preview_target_path\n        self._preview_target_path = None\n        try:\n            summary = future.result()\n            if not path:\n                raise RuntimeError("预览临时文件丢失")\n            old_path = self._preview_path\n            self._preview_path = path\n            self._pdf_doc.close()\n            error = self._pdf_doc.load(path)\n            if error != QPdfDocument.Error.None_:\n                raise RuntimeError(f"预览 PDF 加载失败：{error}")\n            if old_path and old_path != path:\n                try:\n                    os.unlink(old_path)\n                except Exception:\n                    pass\n            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)\n            mode = "双面" if summary["duplex"] else "单面"\n            if summary.get("smart_mixed_sizes"):\n                manual = " · 手工版位" if summary.get("manual_layout") else ""\n                layout = f"异尺寸 · 利用率{summary['utilization_percent']:.1f}%{manual}"\n            else:\n                layout = f"{summary['rows']}×{summary['cols']}"\n            suffix = " · 首张快速预览" if summary.get("sheet_count", 0) > 1 else ""\n            self.preview_status.setText(\n                f"{summary['job_count']}款 · {layout} · {summary['sheet_count']}张纸 · "\n                f"混拼省{summary['sheets_saved_by_mixing']}张 · {mode}{suffix}"\n            )\n            self.statusBar().showMessage("预览已更新", 5000)\n        except Exception as exc:\n            if path:\n                try:\n                    os.unlink(path)\n                except Exception:\n                    pass\n            QMessageBox.critical(self, "生成预览失败", str(exc))\n\n'''
s = s[:start] + replacement + s[end:]
p.write_text(s, encoding='utf-8')

# --- installer: deterministic Unicode license page ---
p = root / 'installer_nsis.nsi'
s = p.read_text(encoding='utf-8')
s = s.replace('!insertmacro MUI_PAGE_LICENSE "EULA_TEMPLATE.txt"', '!insertmacro MUI_PAGE_LICENSE "EULA_NSIS.txt"')
s = s.replace('!insertmacro MUI_LANGUAGE "SimpChinese"\n!insertmacro MUI_LANGUAGE "English"', '!insertmacro MUI_LANGUAGE "SimpChinese"')
s = s.replace('!define APP_VERSION "2.2.1"', '!define APP_VERSION "2.2.2"')
p.write_text(s, encoding='utf-8')

# Python's utf-16 writer emits BOM. NSIS Unicode license page then reads the file
# deterministically instead of depending on the Windows ANSI code page.
eula_text = (root / 'EULA_TEMPLATE.txt').read_text(encoding='utf-8-sig')
(root / 'EULA_NSIS.txt').write_text(eula_text, encoding='utf-16')

# Version bump.
for filename in ('product.py', 'pyproject.toml'):
    p = root / filename
    text = p.read_text(encoding='utf-8').replace('2.2.1', '2.2.2')
    p.write_text(text, encoding='utf-8')

(root / 'V222_ENCODING_PERFORMANCE_FIX.md').write_text('''# V2.2.2 Encoding & Imposition Performance Fix\n\n- NSIS license page uses UTF-16 with BOM and Simplified Chinese installer UI.\n- Large PDF imposition no longer deep-copies every unrotated source page.\n- Preview generation runs off the Qt UI thread.\n- Preview renders only the first imposed sheet while still calculating the full job summary.\n- Full production export remains complete and unchanged in output scope.\n''', encoding='utf-8')

print('V2.2.2 patch applied')
