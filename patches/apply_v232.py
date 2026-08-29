from pathlib import Path
import os
import shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / "enhanced_preflight.py", root / "enhanced_preflight.py")

p = root / "prepress_center.py"
s = p.read_text(encoding="utf-8")

s = s.replace("from PySide6.QtCore import Qt, QRectF\n", "from PySide6.QtCore import Qt, QRectF, QTimer\n", 1)
s = s.replace("import json\n", "import json\nfrom concurrent.futures import ThreadPoolExecutor\n", 1)
if "from enhanced_preflight import scan_paths" not in s:
    s = s.replace("from booklet import saddle_stitch, perfect_bound_sections\n", "from booklet import saddle_stitch, perfect_bound_sections\nfrom enhanced_preflight import scan_paths\n", 1)

old_tabs = '''        tabs.addTab(self._quick_actions_tab(), "快捷工作流")
        tabs.addTab(self._ruler_tab(), "版面标尺")
        tabs.addTab(self._capability_tab(), "功能总览")
        tabs.addTab(self._booklet_tab(), "折手规划")
'''
new_tabs = '''        tabs.addTab(self._quick_actions_tab(), "快捷工作流")
        tabs.addTab(self._preflight_tab(), "智能印前检查")
        tabs.addTab(self._ruler_tab(), "版面标尺")
        tabs.addTab(self._capability_tab(), "功能总览")
        tabs.addTab(self._booklet_tab(), "折手规划")
'''
if old_tabs not in s:
    raise SystemExit("V2.3.2 tab marker not found")
s = s.replace(old_tabs, new_tabs, 1)

marker = "    def _ruler_tab(self):\n"
if marker not in s:
    raise SystemExit("V2.3.2 ruler marker not found")
method = r'''    def _preflight_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("最低图片 DPI"))
        self.pf_dpi = QDoubleSpinBox(); self.pf_dpi.setRange(72, 1200); self.pf_dpi.setValue(250); self.pf_dpi.setDecimals(0)
        controls.addWidget(self.pf_dpi)
        controls.addWidget(QLabel("最小出血"))
        self.pf_bleed = QDoubleSpinBox(); self.pf_bleed.setRange(0, 20); self.pf_bleed.setValue(2.5); self.pf_bleed.setDecimals(1); self.pf_bleed.setSuffix(" mm")
        controls.addWidget(self.pf_bleed)
        run = QPushButton("检查当前文件"); run.clicked.connect(self._start_enhanced_preflight)
        export = QPushButton("导出预检报告"); export.clicked.connect(self._export_preflight_report)
        controls.addWidget(run); controls.addWidget(export); controls.addStretch()
        layout.addLayout(controls)

        self.pf_summary = QLabel("尚未执行检查")
        self.pf_summary.setWordWrap(True)
        layout.addWidget(self.pf_summary)

        self.pf_table = QTableWidget(0, 6)
        self.pf_table.setHorizontalHeaderLabels(["级别", "文件", "页", "类别", "问题", "优化建议"])
        self.pf_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.pf_table, 1)

        self._pf_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="preflight")
        self._pf_future = None
        self._pf_reports = []
        self._pf_timer = QTimer(self)
        self._pf_timer.setInterval(120)
        self._pf_timer.timeout.connect(self._collect_enhanced_preflight)
        self._pf_timer.start()
        return w

    @staticmethod
    def _job_path(job):
        for attr in ("path", "file_path", "source_path", "filename", "source"):
            value = getattr(job, attr, None)
            if value:
                return str(value)
        if isinstance(job, (str, Path)):
            return str(job)
        return None

    def _current_source_paths(self):
        try:
            jobs = self.host.input_jobs()
        except Exception:
            jobs = []
        paths = []
        for job in jobs:
            p = self._job_path(job)
            if p and Path(p).exists():
                paths.append(p)
        return paths

    def _start_enhanced_preflight(self):
        if self._pf_future is not None and not self._pf_future.done():
            self.pf_summary.setText("印前检查正在后台运行…")
            return
        paths = self._current_source_paths()
        if not paths:
            QMessageBox.warning(self, "印前检查", "请先在主界面添加待生产文件。")
            return
        self.pf_summary.setText(f"正在后台检查 {len(paths)} 个文件；界面可继续操作…")
        self.pf_table.setRowCount(0)
        self._pf_future = self._pf_executor.submit(
            scan_paths, paths,
            min_dpi=float(self.pf_dpi.value()),
            min_bleed_mm=float(self.pf_bleed.value()),
        )

    def _collect_enhanced_preflight(self):
        future = self._pf_future
        if future is None or not future.done():
            return
        self._pf_future = None
        try:
            reports = future.result()
        except Exception as exc:
            QMessageBox.critical(self, "印前检查失败", str(exc))
            self.pf_summary.setText("检查失败")
            return
        self._pf_reports = reports
        counts = {"error": 0, "warning": 0, "info": 0}
        self.pf_table.setRowCount(0)
        for report in reports:
            file_name = Path(report.path).name
            for issue in report.issues:
                counts[issue.severity] = counts.get(issue.severity, 0) + 1
                row = self.pf_table.rowCount(); self.pf_table.insertRow(row)
                level = {"error": "错误", "warning": "警告", "info": "提示"}.get(issue.severity, issue.severity)
                vals = [level, file_name, issue.page or "-", issue.category, issue.message, issue.suggestion]
                for col, val in enumerate(vals):
                    self.pf_table.setItem(row, col, QTableWidgetItem(str(val)))
        self.pf_table.resizeColumnsToContents()
        self.pf_summary.setText(
            f"检查完成：{len(reports)} 个文件 · 错误 {counts['error']} · 警告 {counts['warning']} · 提示 {counts['info']}。"
            "错误项建议在拼版前处理；警告项需人工确认生产意图。"
        )

    def _export_preflight_report(self):
        if not self._pf_reports:
            QMessageBox.information(self, "导出预检报告", "请先执行一次智能印前检查。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出预检报告", "印前检查报告.json", "JSON (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        payload = {
            "min_dpi": self.pf_dpi.value(),
            "min_bleed_mm": self.pf_bleed.value(),
            "reports": [r.to_dict() for r in self._pf_reports],
            "note": "内置预检属于生产风险筛查，不等同于认证 PDF/X/PitStop/RIP 预检。",
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        QMessageBox.information(self, "导出完成", f"预检报告已导出：\n{path}")

'''
s = s.replace(marker, method + marker, 1)
p.write_text(s, encoding="utf-8")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    p = root / filename
    text = p.read_text(encoding="utf-8").replace("2.3.1", "2.3.2")
    p.write_text(text, encoding="utf-8")

compile((root / "enhanced_preflight.py").read_text(encoding="utf-8"), str(root / "enhanced_preflight.py"), "exec")
compile((root / "prepress_center.py").read_text(encoding="utf-8"), str(root / "prepress_center.py"), "exec")

(root / "V232_ENHANCED_PREFLIGHT.md").write_text(
    "# V2.3.2 Enhanced Preflight\n\n"
    "- Background preflight to keep the UI responsive on large PDFs.\n"
    "- Checks page boxes/bleed, page-size consistency, font embedding, RGB, spot-color resources, overprint/transparency risks and approximate effective image DPI.\n"
    "- Risk grading plus actionable optimization suggestions and JSON report export.\n"
    "- Built-in checks are advisory; certified PDF/X, font repair and deep separation fixes still require professional providers.\n",
    encoding="utf-8",
)
print("V2.3.2 enhanced preflight patch applied")
