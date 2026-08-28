from pathlib import Path
import os
import shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent

PREPRESS_CENTER = 'from __future__ import annotations\n\nimport json\nfrom pathlib import Path\n\nfrom PySide6.QtWidgets import (\n    QComboBox, QDialog, QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout,\n    QLabel, QMessageBox, QPushButton, QSpinBox, QTabWidget, QTableWidget,\n    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget\n)\n\nfrom booklet import saddle_stitch, perfect_bound_sections\n\n\nCAPABILITY_GROUPS = {\n    "文件导入与预检": [\n        ("多格式导入", "PDF / TIFF / PS / EPS / AI（AI/EPS/PS 依赖转换 Provider）"),\n        ("印刷预检", "字体、RGB/CMYK、图片 DPI、PDF/X、专色/白墨/刀线风险筛查"),\n        ("页面管理", "尺寸/旋转/页面框/出血；高级逐页编辑继续由页面编辑模块扩展"),\n    ],\n    "智能拼版排布": [\n        ("自动拼版", "按成品、出血、边距、叼口、间距自动排版"),\n        ("混拼", "异尺寸、异数量活件混排 + 利用率统计"),\n        ("手动自由拼版", "拖拽、旋转、吸附、对齐、撤销/重做"),\n        ("间距设置", "横纵刀缝、出血、不可印区域"),\n    ],\n    "折手 / 画册": [\n        ("骑马钉", "4P 倍数自动补白与正反页序"),\n        ("胶装 / 锁线", "8P/16P/24P/32P 分帖规划"),\n        ("爬移补偿", "按每张纸 creep 值生成补偿元数据"),\n        ("正反配对", "折手页序表可直接核对正反版"),\n    ],\n    "标记与辅助线": [\n        ("印刷标记", "裁切线、套准线、中心标、色标、密度阶、折线"),\n        ("工艺标记", "刀线/白墨/光油等通过专色与 Provider 工作流"),\n        ("版信息", "订单号、客户、版次、利用率、流水号、二维码"),\n        ("叼口", "叼口 / 拖梢 / 左右规参与可印区域计算"),\n    ],\n    "输出导出": [\n        ("生产 PDF", "复合 PDF 基线；PDF/X 标准认证需专业 Provider"),\n        ("PS / TIFF", "通过 RIP/转换 Provider 或 Hot Folder 输出"),\n        ("拼版样稿", "快速首张预览 PDF"),\n        ("工单报告", "纸张利用率、版数量、页数、版面清单"),\n    ],\n    "高级功能": [\n        ("嵌套拼版", "多边形碰撞与多纸张 nesting 基线"),\n        ("模板保存", "项目参数、拼版模板 JSON"),\n        ("专色处理", "专色识别/保留风险检查；合并需专业 PDF Provider"),\n        ("可变数据", "CSV/XLSX + QR/流水号模板"),\n        ("折页预览", "当前为页序/正反核对；3D 预览列入后续图形模块"),\n        ("纸张利用率", "自动计算利用率与节省纸张数量"),\n    ],\n}\n\n\nclass PrepressImpositionCenter(QDialog):\n    def __init__(self, host, parent=None):\n        super().__init__(parent or host)\n        self.host = host\n        self.setWindowTitle("印前与拼版中心")\n        self.resize(980, 720)\n\n        root = QVBoxLayout(self)\n        title = QLabel("Desktop Imposer Pro · 印前与拼版中心")\n        title.setStyleSheet("font-size:18px;font-weight:700;")\n        root.addWidget(title)\n        note = QLabel(\n            "说明：内置功能提供生产风险筛查与拼版基线；缺失字体修复、PDF/X 认证、"\n            "深度叠印/透明度修复、真正分色 PS/TIFF 输出需对接专业印前/RIP Provider。"\n        )\n        note.setWordWrap(True)\n        root.addWidget(note)\n\n        tabs = QTabWidget()\n        root.addWidget(tabs, 1)\n        tabs.addTab(self._quick_actions_tab(), "快捷工作流")\n        tabs.addTab(self._capability_tab(), "功能总览")\n        tabs.addTab(self._booklet_tab(), "折手规划")\n\n        close_btn = QPushButton("关闭")\n        close_btn.clicked.connect(self.accept)\n        row = QHBoxLayout()\n        row.addStretch()\n        row.addWidget(close_btn)\n        root.addLayout(row)\n\n    def _button(self, text, method_name):\n        btn = QPushButton(text)\n        btn.clicked.connect(lambda: getattr(self.host, method_name)())\n        return btn\n\n    def _quick_actions_tab(self):\n        w = QWidget()\n        layout = QVBoxLayout(w)\n        groups = [\n            ("文件导入与预检", [\n                ("添加印刷文件", "add_files"),\n                ("读取第一页尺寸", "read_first_page_size"),\n                ("运行印前检查", "run_preflight"),\n                ("导入订单表", "import_order_sheet"),\n            ]),\n            ("智能拼版", [\n                ("生成快速拼版预览", "generate_preview"),\n                ("手工自由拼版", "edit_layout"),\n                ("正反版透明叠加", "show_duplex_overlay"),\n                ("导出版面清单", "export_layout_manifest"),\n            ]),\n            ("生产输出", [\n                ("导出生产 PDF", "export_pdf"),\n                ("保存参数模板", "save_template"),\n                ("加载参数模板", "load_template"),\n                ("打开生产队列", "show_queue"),\n            ]),\n        ]\n        for name, buttons in groups:\n            lab = QLabel(name)\n            lab.setStyleSheet("font-weight:700;margin-top:8px;")\n            layout.addWidget(lab)\n            row = QHBoxLayout()\n            for text, method in buttons:\n                row.addWidget(self._button(text, method))\n            layout.addLayout(row)\n\n        tip = QTextEdit()\n        tip.setReadOnly(True)\n        tip.setPlainText(\n            "推荐流程：\\n"\n            "1) 添加 PDF/TIFF/AI/EPS/PS → 2) 印前检查 → 3) 设置纸张/成品/出血/叼口 → "\n            "4) 自动或混拼 → 5) 需要时进入手工版位 → 6) 快速预览 → 7) 导出生产 PDF / 队列 / RIP Hot Folder。\\n\\n"\n            "大文件建议先用‘快速拼版预览’核对首张版，再执行完整生产导出。"\n        )\n        layout.addWidget(tip)\n        return w\n\n    def _capability_tab(self):\n        w = QWidget()\n        layout = QVBoxLayout(w)\n        table = QTableWidget(0, 3)\n        table.setHorizontalHeaderLabels(["模块", "功能", "当前实现/边界"])\n        table.horizontalHeader().setStretchLastSection(True)\n        for group, items in CAPABILITY_GROUPS.items():\n            for name, detail in items:\n                r = table.rowCount()\n                table.insertRow(r)\n                table.setItem(r, 0, QTableWidgetItem(group))\n                table.setItem(r, 1, QTableWidgetItem(name))\n                table.setItem(r, 2, QTableWidgetItem(detail))\n        table.resizeColumnsToContents()\n        layout.addWidget(table)\n        return w\n\n    def _booklet_tab(self):\n        w = QWidget()\n        layout = QVBoxLayout(w)\n        form = QFormLayout()\n        self.pages = QSpinBox(); self.pages.setRange(1, 20000); self.pages.setValue(32)\n        self.mode = QComboBox(); self.mode.addItems(["骑马钉", "胶装/锁线 8P", "胶装/锁线 16P", "胶装/锁线 24P", "胶装/锁线 32P"])\n        self.creep = QDoubleSpinBox(); self.creep.setRange(0, 10); self.creep.setDecimals(3); self.creep.setSuffix(" mm/张")\n        form.addRow("总页数", self.pages)\n        form.addRow("折手方式", self.mode)\n        form.addRow("爬移补偿", self.creep)\n        layout.addLayout(form)\n\n        row = QHBoxLayout()\n        calc = QPushButton("计算折手页序"); calc.clicked.connect(self._calculate_booklet)\n        export = QPushButton("导出页序 JSON"); export.clicked.connect(self._export_booklet)\n        row.addWidget(calc); row.addWidget(export); row.addStretch()\n        layout.addLayout(row)\n\n        self.booklet_table = QTableWidget(0, 7)\n        self.booklet_table.setHorizontalHeaderLabels(["帖", "张", "面", "左页", "右页", "爬移 mm", "说明"])\n        self.booklet_table.horizontalHeader().setStretchLastSection(True)\n        layout.addWidget(self.booklet_table, 1)\n        self._last_booklet = []\n        self._calculate_booklet()\n        return w\n\n    def _calculate_booklet(self):\n        pages = self.pages.value(); creep = self.creep.value(); text = self.mode.currentText()\n        if text == "骑马钉":\n            sections = [saddle_stitch(pages, creep)]\n        else:\n            signature_pages = int(text.split()[-1].replace("P", ""))\n            sections = perfect_bound_sections(pages, signature_pages, creep)\n        rows = []\n        for sig_no, spreads in enumerate(sections, 1):\n            for spread in spreads:\n                rows.append({\n                    "signature": getattr(spread, "signature", sig_no), "sheet": spread.sheet,\n                    "side": spread.side, "left": spread.left, "right": spread.right,\n                    "creep_mm": spread.creep_mm,\n                })\n        self._last_booklet = rows\n        self.booklet_table.setRowCount(0)\n        for item in rows:\n            r = self.booklet_table.rowCount(); self.booklet_table.insertRow(r)\n            vals = [\n                item["signature"], item["sheet"], "正面" if item["side"] == "front" else "反面",\n                item["left"] if item["left"] is not None else "白页",\n                item["right"] if item["right"] is not None else "白页",\n                f'{item["creep_mm"]:.3f}',\n                "自动补白" if item["left"] is None or item["right"] is None else "",\n            ]\n            for c, val in enumerate(vals):\n                self.booklet_table.setItem(r, c, QTableWidgetItem(str(val)))\n\n    def _export_booklet(self):\n        if not self._last_booklet:\n            self._calculate_booklet()\n        path, _ = QFileDialog.getSaveFileName(self, "导出折手页序", "折手页序.json", "JSON (*.json)")\n        if not path:\n            return\n        if not path.lower().endswith(".json"):\n            path += ".json"\n        payload = {\n            "page_count": self.pages.value(), "mode": self.mode.currentText(),\n            "creep_per_sheet_mm": self.creep.value(), "spreads": self._last_booklet,\n        }\n        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")\n        QMessageBox.information(self, "导出完成", f"折手页序已导出：\\n{path}")\n'

p = root / "product.py"
s = p.read_text(encoding="utf-8")
s = s.replace('APP_NAME = "桌面拼版软件 Pro"', 'APP_NAME = "Desktop Imposer Pro"')
s = s.replace('APP_VERSION = "2.2.2"', 'APP_VERSION = "2.3.0"')
p.write_text(s, encoding="utf-8")

(root / "prepress_center.py").write_text(PREPRESS_CENTER, encoding="utf-8")

p = root / "app.py"
s = p.read_text(encoding="utf-8")
if "from prepress_center import PrepressImpositionCenter" not in s:
    marker = "from health_check import run_health_checks\n"
    if marker not in s:
        raise SystemExit("app import marker not found")
    s = s.replace(marker, marker + "from prepress_center import PrepressImpositionCenter\n", 1)

old = '''        production_menu = self.menuBar().addMenu("生产")
        for title, handler in [("导出生产 PDF…", self.export_pdf), ("加入生产队列…", self.enqueue_current), ("生产队列…", self.show_queue)]:
            act = QAction(title, self); act.triggered.connect(handler); production_menu.addAction(act)
'''
new = '''        production_menu = self.menuBar().addMenu("生产")
        center_act = QAction("印前与拼版中心…", self)
        center_act.triggered.connect(self.show_prepress_imposition_center)
        production_menu.addAction(center_act)
        production_menu.addSeparator()
        for title, handler in [("导出生产 PDF…", self.export_pdf), ("加入生产队列…", self.enqueue_current), ("生产队列…", self.show_queue)]:
            act = QAction(title, self); act.triggered.connect(handler); production_menu.addAction(act)
'''
if old not in s:
    raise SystemExit("production menu block not found")
s = s.replace(old, new, 1)
s = s.replace(
    'subtitle = QLabel("V2.1 商业发布强化版 · 权限/备份/审计/更新/恢复 · 生产全链路")',
    'subtitle = QLabel("V2.3 印前与智能拼版版 · 多格式/预检/混拼/折手/标记/变量数据/生产输出")'
)
marker = "    def run_preflight(self):\n"
if marker not in s:
    raise SystemExit("run_preflight marker not found")
method = '''    def show_prepress_imposition_center(self):
        dialog = PrepressImpositionCenter(self, self)
        dialog.exec()

'''
s = s.replace(marker, method + marker, 1)
p.write_text(s, encoding="utf-8")

p = root / "installer_nsis.nsi"
s = p.read_text(encoding="utf-8")
s = s.replace('!define APP_NAME "桌面拼版软件 Pro"', '!define APP_NAME "Desktop Imposer Pro"')
s = s.replace('!define APP_VERSION "2.2.2"', '!define APP_VERSION "2.3.0"')
p.write_text(s, encoding="utf-8")

p = root / "installer.iss"
if p.exists():
    s = p.read_text(encoding="utf-8")
    s = s.replace('#define MyAppName "桌面拼版软件 Pro"', '#define MyAppName "Desktop Imposer Pro"')
    p.write_text(s, encoding="utf-8")

p = root / "pyproject.toml"
s = p.read_text(encoding="utf-8").replace('version = "2.2.2"', 'version = "2.3.0"')
p.write_text(s, encoding="utf-8")

(root / "V230_PREPRESS_IMPOSITION_CENTER.md").write_text(
    "# V2.3 Prepress & Imposition Center\n\n"
    "- Product/installer display name standardized to ASCII `Desktop Imposer Pro` to avoid Windows resource/shortcut mojibake.\n"
    "- New Prepress & Imposition Center with quick access to import, preflight, mixed imposition, manual layout, duplex overlay, templates and production export.\n"
    "- Interactive booklet/signature planner for saddle stitch and 8P/16P/24P/32P sections with blank-page padding and creep metadata.\n"
    "- Capability matrix documents built-in vs provider-dependent production features.\n"
    "- Professional PDF/X certification, deep font repair, deep overprint/transparency remediation and native RIP-grade PS/TIFF separation remain provider-dependent.\n",
    encoding="utf-8",
)
print("V2.3.0 patch applied")
