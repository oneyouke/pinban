from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QMessageBox, QPushButton, QSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from booklet import saddle_stitch, perfect_bound_sections

CAPABILITY_GROUPS = {
    "文件导入与预检": [
        ("多格式导入", "PDF / TIFF / PS / EPS / AI；AI/EPS/PS 依赖转换 Provider"),
        ("印刷预检", "字体、RGB/CMYK、图片 DPI、PDF/X、专色/白墨/刀线风险筛查"),
        ("页面管理", "尺寸、旋转、页面框、出血；逐页高级编辑继续由页面编辑模块扩展"),
    ],
    "智能拼版排布": [
        ("自动拼版", "按成品、出血、边距、叼口、间距自动排版"),
        ("混拼", "异尺寸、异数量活件混排 + 利用率统计"),
        ("手动自由拼版", "拖拽、旋转、吸附、对齐、撤销/重做"),
        ("间距设置", "横纵刀缝、出血、不可印区域"),
    ],
    "折手 / 画册": [
        ("骑马钉", "4P 倍数自动补白与正反页序"),
        ("胶装 / 锁线", "8P/16P/24P/32P 分帖规划"),
        ("爬移补偿", "按每张纸 creep 值生成补偿元数据"),
        ("正反配对", "折手页序表用于核对正反版"),
    ],
    "标记与辅助线": [
        ("印刷标记", "裁切线、套准线、中心标、色标、密度阶、折线"),
        ("工艺标记", "刀线/白墨/光油等通过专色与 Provider 工作流"),
        ("版信息", "订单号、客户、版次、利用率、流水号、二维码"),
        ("叼口", "叼口 / 拖梢 / 左右规参与可印区域计算"),
    ],
    "输出导出": [
        ("生产 PDF", "复合 PDF 基线；PDF/X 标准认证需专业 Provider"),
        ("PS / TIFF", "通过 RIP/转换 Provider 或 Hot Folder 输出"),
        ("拼版样稿", "快速首张预览 PDF"),
        ("工单报告", "纸张利用率、版数量、页数、版面清单"),
    ],
    "高级功能": [
        ("嵌套拼版", "多边形碰撞与多纸张 nesting 基线"),
        ("模板保存", "项目参数、拼版模板 JSON"),
        ("专色处理", "专色识别/保留风险检查；合并需专业 PDF Provider"),
        ("可变数据", "CSV/XLSX + QR/流水号模板"),
        ("折页预览", "当前为页序/正反核对；3D 预览列入后续图形模块"),
        ("纸张利用率", "自动计算利用率与节省纸张数量"),
    ],
}


class PrepressImpositionCenter(QDialog):
    def __init__(self, host, parent=None):
        super().__init__(parent or host)
        self.host = host
        self.setWindowTitle("印前与拼版中心")
        self.resize(980, 720)

        root = QVBoxLayout(self)
        title = QLabel("Desktop Imposer Pro - 印前与拼版中心")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        root.addWidget(title)

        note = QLabel(
            "内置功能提供生产风险筛查与拼版基线；缺失字体修复、PDF/X 认证、"
            "深度叠印/透明度修复、真正分色 PS/TIFF 输出需对接专业印前/RIP Provider。"
        )
        note.setWordWrap(True)
        root.addWidget(note)

        tabs = QTabWidget()
        root.addWidget(tabs, 1)
        tabs.addTab(self._quick_actions_tab(), "快捷工作流")
        tabs.addTab(self._capability_tab(), "功能总览")
        tabs.addTab(self._booklet_tab(), "折手规划")

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close_btn)
        root.addLayout(row)

    def _button(self, text, method_name):
        btn = QPushButton(text)
        btn.clicked.connect(lambda: getattr(self.host, method_name)())
        return btn

    def _quick_actions_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        groups = [
            ("文件导入与预检", [
                ("添加印刷文件", "add_files"),
                ("读取第一页尺寸", "read_first_page_size"),
                ("运行印前检查", "run_preflight"),
                ("导入订单表", "import_order_sheet"),
            ]),
            ("智能拼版", [
                ("生成快速拼版预览", "generate_preview"),
                ("手工自由拼版", "edit_layout"),
                ("正反版透明叠加", "show_duplex_overlay"),
                ("导出版面清单", "export_layout_manifest"),
            ]),
            ("生产输出", [
                ("导出生产 PDF", "export_pdf"),
                ("保存参数模板", "save_template"),
                ("加载参数模板", "load_template"),
                ("打开生产队列", "show_queue"),
            ]),
        ]
        for name, buttons in groups:
            lab = QLabel(name)
            lab.setStyleSheet("font-weight:700;margin-top:8px;")
            layout.addWidget(lab)
            row = QHBoxLayout()
            for text, method in buttons:
                row.addWidget(self._button(text, method))
            layout.addLayout(row)

        tip = QTextEdit()
        tip.setReadOnly(True)
        tip.setPlainText(
            "推荐流程：\n"
            "1) 添加 PDF/TIFF/AI/EPS/PS -> 2) 印前检查 -> 3) 设置纸张/成品/出血/叼口 -> "
            "4) 自动或混拼 -> 5) 需要时进入手工版位 -> 6) 快速预览 -> 7) 导出生产 PDF / 队列 / RIP Hot Folder。\n\n"
            "大文件建议先用快速拼版预览核对首张版，再执行完整生产导出。"
        )
        layout.addWidget(tip)
        return w

    def _capability_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["模块", "功能", "当前实现/边界"])
        table.horizontalHeader().setStretchLastSection(True)
        for group, items in CAPABILITY_GROUPS.items():
            for name, detail in items:
                r = table.rowCount()
                table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem(group))
                table.setItem(r, 1, QTableWidgetItem(name))
                table.setItem(r, 2, QTableWidgetItem(detail))
        table.resizeColumnsToContents()
        layout.addWidget(table)
        return w

    def _booklet_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        form = QFormLayout()
        self.pages = QSpinBox(); self.pages.setRange(1, 20000); self.pages.setValue(32)
        self.mode = QComboBox(); self.mode.addItems(["骑马钉", "胶装/锁线 8P", "胶装/锁线 16P", "胶装/锁线 24P", "胶装/锁线 32P"])
        self.creep = QDoubleSpinBox(); self.creep.setRange(0, 10); self.creep.setDecimals(3); self.creep.setSuffix(" mm/张")
        form.addRow("总页数", self.pages)
        form.addRow("折手方式", self.mode)
        form.addRow("爬移补偿", self.creep)
        layout.addLayout(form)

        row = QHBoxLayout()
        calc = QPushButton("计算折手页序"); calc.clicked.connect(self._calculate_booklet)
        export = QPushButton("导出页序 JSON"); export.clicked.connect(self._export_booklet)
        row.addWidget(calc); row.addWidget(export); row.addStretch()
        layout.addLayout(row)

        self.booklet_table = QTableWidget(0, 7)
        self.booklet_table.setHorizontalHeaderLabels(["帖", "张", "面", "左页", "右页", "爬移 mm", "说明"])
        self.booklet_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.booklet_table, 1)
        self._last_booklet = []
        self._calculate_booklet()
        return w

    def _calculate_booklet(self):
        pages = self.pages.value()
        creep = self.creep.value()
        text = self.mode.currentText()
        if text == "骑马钉":
            sections = [saddle_stitch(pages, creep)]
        else:
            signature_pages = int(text.split()[-1].replace("P", ""))
            sections = perfect_bound_sections(pages, signature_pages, creep)

        rows = []
        for sig_no, spreads in enumerate(sections, 1):
            for spread in spreads:
                rows.append({
                    "signature": getattr(spread, "signature", sig_no),
                    "sheet": spread.sheet,
                    "side": spread.side,
                    "left": spread.left,
                    "right": spread.right,
                    "creep_mm": spread.creep_mm,
                })
        self._last_booklet = rows
        self.booklet_table.setRowCount(0)
        for item in rows:
            r = self.booklet_table.rowCount()
            self.booklet_table.insertRow(r)
            vals = [
                item["signature"], item["sheet"], "正面" if item["side"] == "front" else "反面",
                item["left"] if item["left"] is not None else "白页",
                item["right"] if item["right"] is not None else "白页",
                f'{item["creep_mm"]:.3f}',
                "自动补白" if item["left"] is None or item["right"] is None else "",
            ]
            for c, val in enumerate(vals):
                self.booklet_table.setItem(r, c, QTableWidgetItem(str(val)))

    def _export_booklet(self):
        if not self._last_booklet:
            self._calculate_booklet()
        path, _ = QFileDialog.getSaveFileName(self, "导出折手页序", "折手页序.json", "JSON (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        payload = {
            "page_count": self.pages.value(),
            "mode": self.mode.currentText(),
            "creep_per_sheet_mm": self.creep.value(),
            "spreads": self._last_booklet,
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        QMessageBox.information(self, "导出完成", f"折手页序已导出：\n{path}")
