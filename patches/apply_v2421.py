from pathlib import Path
import os
import shutil


root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
shutil.copy2(patch_root / "test_v2421_main_workspace.py", root / "test_v2421_main_workspace.py")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"V2.4.21 marker missing in {path.name}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


canvas = root / "professional_canvas.py"
replace_once(
    canvas,
    "    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame,\n",
    "    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame,\n",
)
replace_once(
    canvas,
    "        self.pages, self.thumbs, self.mix_entries = [], {}, []\n",
    "        self.pages, self.thumbs, self.mix_entries = [], {}, []\n        self.production_host = None\n",
)
replace_once(
    canvas,
    '            ("删除版位", QStyle.SP_DialogDiscardButton, self.canvas.delete_selected),\n',
    '            ("删除版位", QStyle.SP_DialogDiscardButton, self.canvas.delete_selected),\n'
    '            ("印前检查", QStyle.SP_DialogApplyButton, self._run_host_preflight),\n'
    '            ("导出生产 PDF", QStyle.SP_DialogSaveButton, self._export_host_pdf),\n'
    '            ("经典参数", QStyle.SP_FileDialogDetailedView, self._show_legacy_workspace),\n',
)
replace_once(
    canvas,
    "    def _apply_paper_preset(self, index):\n",
    '''    def bind_production_host(self, host):
        self.production_host = host
        self._sync_host_parameters()

    def import_pdf(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "导入 PDF", "", "PDF (*.pdf)")
        for path in paths:
            self._load_pdf(path)

    def _register_host_pdf(self, path):
        host = self.production_host
        if host is None or not hasattr(host, "_append_job_row"):
            return
        resolved = str(Path(path).resolve())
        existing = {str(Path(p).resolve()) for p in host.input_paths()}
        if resolved in existing:
            return
        info = next((p for p in self.pages if str(Path(p.path).resolve()) == resolved), None)
        quantity = host.default_quantity.value() if hasattr(host, "default_quantity") else 1
        host._append_job_row(
            path, quantity,
            info.width_mm if info else self.trim_w.value(),
            info.height_mm if info else self.trim_h.value(),
            self.bleed.value(),
        )

    def _sync_host_parameters(self):
        host = self.production_host
        if host is None:
            return
        mapping = (
            ("sheet_w", self.sheet_w.value()), ("sheet_h", self.sheet_h.value()),
            ("trim_w", self.trim_w.value()), ("trim_h", self.trim_h.value()),
            ("bleed", self.bleed.value()), ("gap_x", self.gap_x.value()),
            ("gap_y", self.gap_y.value()),
        )
        for name, value in mapping:
            target = getattr(host, name, None)
            if target is not None:
                target.setValue(value)
        if hasattr(host, "paper_combo"):
            host.paper_combo.setCurrentText("自定义")
        if hasattr(host, "auto_rotate"):
            host.auto_rotate.setChecked(self.auto_rotate.isChecked())
        if hasattr(host, "crop_marks"):
            host.crop_marks.setChecked(self.crop_marks.isChecked())
        if hasattr(host, "registration_marks"):
            host.registration_marks.setChecked(self.registration_marks.isChecked())
        if hasattr(host, "duplex"):
            host.duplex.setChecked(self.back_tab.isChecked())
        if hasattr(host, "_refresh_grid_info"):
            host._refresh_grid_info()

    def _prepare_host_job(self):
        host = self.production_host
        if host is None:
            QMessageBox.information(self, "生产操作", "当前画布未连接主生产任务。")
            return None
        seen = set()
        for info in self.pages:
            resolved = str(Path(info.path).resolve())
            if resolved not in seen:
                self._register_host_pdf(info.path)
                seen.add(resolved)
        self._sync_host_parameters()
        return host

    def _run_host_preflight(self):
        host = self._prepare_host_job()
        if host is not None:
            host.run_preflight()

    def _export_host_pdf(self):
        host = self._prepare_host_job()
        if host is not None:
            host.export_pdf()

    def _show_legacy_workspace(self):
        host = self._prepare_host_job()
        if host is not None and hasattr(host, "show_legacy_workspace"):
            host.show_legacy_workspace()

    def _apply_paper_preset(self, index):
''',
)
replace_once(
    canvas,
    "        if added:\n            self.file_summary.setText",
    "        if added:\n            self._register_host_pdf(path)\n            self.file_summary.setText",
)


app = root / "app.py"
replace_once(
    app,
    "    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QToolBar, QVBoxLayout, QWidget,\n",
    "    QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QToolBar, QVBoxLayout, QWidget,\n",
)
replace_once(
    app,
    "from prepress_center import PrepressImpositionCenter\n",
    "from prepress_center import PrepressImpositionCenter\nfrom professional_canvas import ProfessionalPageCanvasWidget\n",
)
replace_once(
    app,
    '        toolbar = QToolBar("主工具栏")\n',
    '        toolbar = QToolBar("主工具栏")\n        self.main_toolbar = toolbar\n',
)
replace_once(
    app,
    '            ("工作台", self.show_workspace),\n',
    '            ("专业拼版", self.show_professional_workspace),\n            ("工作台", self.show_workspace),\n',
)
replace_once(
    app,
    '        self.statusBar().addPermanentWidget(self.license_badge)\n',
    '''        self.statusBar().addPermanentWidget(self.license_badge)

        self.legacy_workspace = self.takeCentralWidget()
        self.workspace_stack = QStackedWidget()
        self.professional_workspace = ProfessionalPageCanvasWidget(self)
        self.professional_workspace.bind_production_host(self)
        self.workspace_stack.addWidget(self.professional_workspace)
        self.workspace_stack.addWidget(self.legacy_workspace)
        self.setCentralWidget(self.workspace_stack)
        self.workspace_stack.setCurrentWidget(self.professional_workspace)
        self.main_toolbar.setVisible(False)
''',
)
replace_once(
    app,
    "    def show_workspace(self):\n",
    '''    def show_professional_workspace(self):
        if hasattr(self, "workspace_stack"):
            self.workspace_stack.setCurrentWidget(self.professional_workspace)
            self.main_toolbar.setVisible(False)
            self.statusBar().showMessage("专业拼版工作区", 3000)

    def show_legacy_workspace(self):
        if hasattr(self, "workspace_stack"):
            self.professional_workspace._sync_host_parameters()
            self.workspace_stack.setCurrentWidget(self.legacy_workspace)
            self.main_toolbar.setVisible(True)
            self.statusBar().showMessage("经典参数工作区；点击工具栏“专业拼版”可返回", 5000)

    def show_workspace(self):
''',
)

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    path = root / filename
    path.write_text(path.read_text(encoding="utf-8").replace("2.4.20", "2.4.21"), encoding="utf-8")

for filename in ("professional_canvas.py", "app.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")

(root / "V2421_MAIN_WORKSPACE_FIX.md").write_text(
    "# V2.4.21 Main Workspace Fix\n\n"
    "- Makes the professional three-pane imposition workspace the startup screen.\n"
    "- Connects imported PDFs and visible settings to the established production pipeline.\n"
    "- Adds direct preflight and production PDF actions.\n"
    "- Keeps the legacy parameter workspace available through a one-click switch.\n",
    encoding="utf-8",
)
print("V2.4.21 professional workspace connected to main window")
