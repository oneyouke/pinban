from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'build-src' / 'Desktop-Imposer-Pro-V2.2'

# app.py: background metadata loading + explicit CJK font.
p = ROOT / 'app.py'
s = p.read_text(encoding='utf-8')
s = s.replace('import tempfile\nfrom pathlib import Path\n', 'import tempfile\nfrom concurrent.futures import ThreadPoolExecutor\nfrom pathlib import Path\n')
s = s.replace('from PySide6.QtGui import QAction, QFont\n', 'from PySide6.QtGui import QAction, QFont, QFontDatabase\n')
s = s.replace(
'''        self._backup_timer = QTimer(self)\n        self._backup_timer.setInterval(60 * 60 * 1000)\n        self._backup_timer.timeout.connect(self._automatic_backup_tick)\n\n        self._build_ui()\n''',
'''        self._backup_timer = QTimer(self)\n        self._backup_timer.setInterval(60 * 60 * 1000)\n        self._backup_timer.timeout.connect(self._automatic_backup_tick)\n\n        self._inspect_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="source-inspect")\n        self._pending_inspections: dict[str, object] = {}\n        self._inspect_timer = QTimer(self)\n        self._inspect_timer.setInterval(80)\n        self._inspect_timer.timeout.connect(self._collect_source_inspections)\n        self._inspect_timer.start()\n\n        self._build_ui()\n''')
s = s.replace(
'''    def _append_job_row(self, path: str, quantity: int = 1, width_mm: float | None = None, height_mm: float | None = None, bleed_mm: float | None = None, name: str | None = None):\n        pages = "?"\n        source_w = width_mm if width_mm is not None else self.trim_w.value()\n        source_h = height_mm if height_mm is not None else self.trim_h.value()\n        try:\n            info = inspect_source(path, SOURCE_BOX_LABELS[self.source_box.currentText()])\n            pages = info["pages"]\n            if width_mm is None: source_w = info["width_mm"]\n            if height_mm is None: source_h = info["height_mm"]\n        except Exception:\n            pass\n        row = self.file_table.rowCount()\n''',
'''    def _append_job_row(self, path: str, quantity: int = 1, width_mm: float | None = None, height_mm: float | None = None, bleed_mm: float | None = None, name: str | None = None):\n        pages = "加载中…"\n        source_w = width_mm if width_mm is not None else self.trim_w.value()\n        source_h = height_mm if height_mm is not None else self.trim_h.value()\n        row = self.file_table.rowCount()\n''')
s = s.replace(
'''        self.file_table.setCellWidget(row, 2, qty); self.file_table.setCellWidget(row, 3, w)\n        self.file_table.setCellWidget(row, 4, h); self.file_table.setCellWidget(row, 5, bleed)\n''',
'''        self.file_table.setCellWidget(row, 2, qty); self.file_table.setCellWidget(row, 3, w)\n        self.file_table.setCellWidget(row, 4, h); self.file_table.setCellWidget(row, 5, bleed)\n\n        token = f"{row}:{id(file_item)}:{Path(path).resolve()}"\n        file_item.setData(Qt.UserRole + 2, token)\n        box_name = SOURCE_BOX_LABELS[self.source_box.currentText()]\n        future = self._inspect_executor.submit(inspect_source, path, box_name)\n        self._pending_inspections[token] = (future, width_mm is None, height_mm is None)\n''', 1)
s = s.replace(
'''    def _invalidate_layout(self, *_):\n''',
'''    def _collect_source_inspections(self):\n        if not self._pending_inspections:\n            return\n        completed = []\n        for token, payload in list(self._pending_inspections.items()):\n            future, update_w, update_h = payload\n            if not future.done():\n                continue\n            completed.append(token)\n            row = next((r for r in range(self.file_table.rowCount())\n                        if self.file_table.item(r, 0) and self.file_table.item(r, 0).data(Qt.UserRole + 2) == token), -1)\n            if row < 0:\n                continue\n            pages_item = self.file_table.item(row, 1)\n            try:\n                info = future.result()\n                if pages_item:\n                    pages_item.setText(str(info["pages"]))\n                    pages_item.setToolTip("后台解析完成")\n                if update_w:\n                    widget = self.file_table.cellWidget(row, 3)\n                    if widget: widget.setValue(float(info["width_mm"]))\n                if update_h:\n                    widget = self.file_table.cellWidget(row, 4)\n                    if widget: widget.setValue(float(info["height_mm"]))\n            except Exception as exc:\n                if pages_item:\n                    pages_item.setText("!")\n                    pages_item.setToolTip(f"读取失败：{exc}")\n        for token in completed:\n            self._pending_inspections.pop(token, None)\n        if completed:\n            self._refresh_grid_info()\n\n    def _invalidate_layout(self, *_):\n''', 1)
s = s.replace(
'''            except Exception:\n                path_item = self.file_table.item(row, 0)\n                if not path_item:\n                    counts.append(0)\n                    continue\n                info = inspect_source(path_item.data(Qt.UserRole), SOURCE_BOX_LABELS[self.source_box.currentText()])\n                counts.append(int(info["pages"]))\n''',
'''            except Exception:\n                counts.append(0)\n''', 1)
s = s.replace(
'''    app = QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setApplicationVersion(APP_VERSION); app.setStyleSheet(APP_STYLE)\n    font = QFont(); font.setPointSize(10); app.setFont(font)\n''',
'''    app = QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setApplicationVersion(APP_VERSION); app.setStyleSheet(APP_STYLE)\n    families = set(QFontDatabase.families())\n    preferred = ("Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑", "Segoe UI", "Arial")\n    family = next((name for name in preferred if name in families), app.font().family())\n    app.setFont(QFont(family, 10))\n''', 1)
p.write_text(s, encoding='utf-8')

# imposition.py: metadata-only basic preflight.
p = ROOT / 'imposition.py'
s = p.read_text(encoding='utf-8')
s = s.replace(
'''    lib = SourceLibrary()\n    expected_variable_items = 0\n    try:\n        for idx, job in enumerate(jobs, 1):\n            try:\n                job.validate()\n                pages = list(lib.add(job.path))\n            except Exception as exc:\n                errors.append(f"[{idx}] {Path(job.path).name}：无法读取：{exc}")\n                continue\n            if not pages:\n                errors.append(f"[{idx}] {Path(job.path).name}：没有可用页面")\n                continue\n\n            name = job.name or Path(job.path).stem\n            trim_w, trim_h, bleed = job.effective_trim(settings)\n            fw = trim_w + 2 * bleed\n            fh = trim_h + 2 * bleed\n\n            if settings.duplex and len(pages) % 2:\n                errors.append(f"[{idx}] {name}：双面模式要求偶数页，当前 {len(pages)} 页")\n            expected_variable_items += (len(pages) // 2 if settings.duplex else len(pages)) * job.quantity\n''',
'''    expected_variable_items = 0\n    try:\n        for idx, job in enumerate(jobs, 1):\n            try:\n                job.validate()\n                info = inspect_source(job.path, settings.source_box)\n                page_count = int(info["pages"])\n            except Exception as exc:\n                errors.append(f"[{idx}] {Path(job.path).name}：无法读取：{exc}")\n                continue\n            if page_count < 1:\n                errors.append(f"[{idx}] {Path(job.path).name}：没有可用页面")\n                continue\n\n            name = job.name or Path(job.path).stem\n            trim_w, trim_h, bleed = job.effective_trim(settings)\n            fw = trim_w + 2 * bleed\n            fh = trim_h + 2 * bleed\n\n            if settings.duplex and page_count % 2:\n                errors.append(f"[{idx}] {name}：双面模式要求偶数页，当前 {page_count} 页")\n            expected_variable_items += (page_count // 2 if settings.duplex else page_count) * job.quantity\n''', 1)
s = s.replace('missing_special_box = settings.source_box in {"trim", "bleed"} and not _box_exists(pages[0], settings.source_box)', 'missing_special_box = settings.source_box in {"trim", "bleed"} and not bool(info.get("requested_box_exists"))', 1)
start = s.index('            sample_pages = pages if len(pages) <= 20 else pages[:20]')
end = s.index('            # Deep PDF/raster production checks.', start)
s = s[:start] + '''            sw, sh = float(info["width_mm"]), float(info["height_mm"])\n            if settings.scale_mode == "actual":\n                matches = any(abs(sw - tw) <= settings.actual_size_tolerance_mm and abs(sh - th) <= settings.actual_size_tolerance_mm for tw, th in targets)\n                if not matches:\n                    errors.append(f"[{idx}] {name} 首页：1:1 尺寸 {sw:.2f}×{sh:.2f} mm 与目标含出血尺寸不符")\n            else:\n                ratios = [min(tw / sw, th / sh) for tw, th in targets]\n                scale = min(ratios, key=lambda r: abs(1.0 - r))\n                if scale < 0.80 or scale > 1.20:\n                    warnings.append(f"[{idx}] {name} 首页：预计缩放到 {scale * 100:.1f}%")\n\n''' + s[end:]
s = s.replace('sw0, sh0 = page_size_mm(pages[0], settings.source_box)', 'sw0, sh0 = float(info["width_mm"]), float(info["height_mm"])', 1)
old = '''            if settings.duplex:\n                for p in range(0, len(pages), 2):\n                    if p + 1 >= len(pages):\n                        break\n                    fw0, fh0 = page_size_mm(pages[p], settings.source_box)\n                    bw0, bh0 = page_size_mm(pages[p + 1], settings.source_box)\n                    if abs(fw0 - bw0) > 0.5 or abs(fh0 - bh0) > 0.5:\n                        warnings.append(\n                            f"[{idx}] {name}：正反页尺寸不一致（{fw0:.2f}×{fh0:.2f} vs {bw0:.2f}×{bh0:.2f} mm）"\n                        )\n                        break\n\n            infos.append(f"[{idx}] {name}：{len(pages)} 页 × 数量 {job.quantity}，成品 {trim_w:.2f}×{trim_h:.2f} mm，出血 {bleed:.2f} mm")\n'''
new = '''            if settings.duplex and page_count >= 2:\n                infos.append(f"[{idx}] {name}：双面页尺寸一致性将在生成/深度检查阶段验证")\n\n            infos.append(f"[{idx}] {name}：{page_count} 页 × 数量 {job.quantity}，成品 {trim_w:.2f}×{trim_h:.2f} mm，出血 {bleed:.2f} mm")\n'''
s = s.replace(old, new, 1)
s = s.replace('''    finally:\n        lib.close()\n''', '''    finally:\n        pass\n''', 1)
p.write_text(s, encoding='utf-8')

# Version bump.
for filename, old, new in [
    ('product.py', 'APP_VERSION = "2.2.0"', 'APP_VERSION = "2.2.1"'),
    ('pyproject.toml', 'version = "2.2.0"', 'version = "2.2.1"'),
    ('installer_nsis.nsi', '!define APP_VERSION "2.1.0"', '!define APP_VERSION "2.2.1"'),
]:
    p = ROOT / filename
    t = p.read_text(encoding='utf-8').replace(old, new)
    p.write_text(t, encoding='utf-8')

print('V2.2.1 patch applied')
