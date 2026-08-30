from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QTimer, QLineF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter, QStyle,
    QToolButton, QVBoxLayout, QWidget, QGraphicsView,
)

from duplex import DuplexMode
from mix_optimizer import ProductSpec, optimize_mixed
from page_canvas import ImpositionCanvas, PageCanvasWidget, PageItem


WORKSPACE_STYLE = r"""
QWidget#ImpositionWorkspace { background:#edf1f6; color:#172033; }
QFrame#TopCommandBar { background:#ffffff; border-bottom:1px solid #d8dee8; }
QToolButton#CommandButton {
    background:transparent; border:0; border-right:1px solid #e3e7ee;
    border-radius:0; padding:8px 18px; min-width:72px; min-height:52px;
    color:#142b4a; font-size:13px; font-weight:600;
}
QToolButton#CommandButton:hover { background:#f2f7ff; color:#0b63ce; }
QToolButton#CommandButton:pressed { background:#e7f0ff; }
QFrame#Sidebar, QFrame#Inspector { background:#ffffff; border:0; }
QLabel#PaneTitle { font-size:14px; font-weight:700; color:#172033; padding:8px 4px; }
QLabel#SectionTitle { font-size:13px; font-weight:700; color:#27364a; }
QLabel#Muted { color:#748196; font-size:11px; }
QLineEdit#PageSearch {
    background:#f7f9fc; border:1px solid #d4dae4; border-radius:6px;
    min-height:30px; padding:0 9px;
}
QListWidget#PageList {
    background:#ffffff; border:0; outline:0; padding:3px;
}
QListWidget#PageList::item {
    border:1px solid #dce2eb; border-radius:7px; padding:8px; margin:4px 1px;
    color:#27364a;
}
QListWidget#PageList::item:selected {
    background:#eef5ff; border:2px solid #1769df; color:#172033;
}
QFrame#CanvasChrome { background:#f5f7fa; border-left:1px solid #d8dee8; border-right:1px solid #d8dee8; }
QPushButton#SideTab {
    border:1px solid #cfd6e2; border-radius:5px; background:#f8fafc;
    min-width:64px; min-height:27px; padding:0 12px; color:#536176;
}
QPushButton#SideTab:checked { background:#1266d8; color:white; border-color:#1266d8; }
QFrame#CanvasStatus { background:#ffffff; border-top:1px solid #d8dee8; }
QLabel#Utilization { color:#17833c; font-size:16px; font-weight:700; }
QLabel#ReadyStatus { color:#16843e; font-weight:700; }
QFrame#InspectorSection { background:#ffffff; border-bottom:1px solid #e0e5ec; }
QLabel#InspectorTitle { font-size:13px; font-weight:700; color:#253247; }
QDoubleSpinBox, QSpinBox, QComboBox {
    background:#ffffff; border:1px solid #cfd6e0; border-radius:5px;
    min-height:28px; padding:0 7px;
}
QCheckBox { spacing:7px; color:#344157; min-height:23px; }
QPushButton#SmallButton {
    background:#ffffff; border:1px solid #cbd3df; border-radius:5px;
    min-height:28px; padding:0 10px;
}
QPushButton#PrimaryButton {
    background:#1167dc; color:white; border:0; border-radius:6px;
    min-height:42px; font-size:14px; font-weight:700;
}
QPushButton#PrimaryButton:hover { background:#0d58bd; }
QLabel#MixStatus {
    background:#f5f8fc; border:1px solid #dce3ec; border-radius:5px;
    color:#536176; padding:7px;
}
QScrollArea { border:0; background:#ffffff; }
QSplitter::handle { background:#d8dee8; width:1px; }
"""


class ProfessionalCanvas(ImpositionCanvas):
    def __init__(self):
        super().__init__()
        self.setBackgroundBrush(QColor("#eef1f5"))
        self.setFrameShape(QFrame.NoFrame)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.sheet.setBrush(QColor("#ffffff"))
        self.sheet.setPen(QPen(QColor("#1769df"), 1.2))
        self.bleed_box.setPen(QPen(QColor("#ef77b7"), 0.7, Qt.DashLine))

    def drawBackground(self, painter: QPainter, rect):
        super().drawBackground(painter, rect)
        painter.save()
        minor = QPen(QColor(214, 220, 229, 150), 0)
        major = QPen(QColor(187, 196, 208, 180), 0)
        left = math.floor(rect.left() / 10.0) * 10
        top = math.floor(rect.top() / 10.0) * 10
        x = left
        while x <= rect.right():
            painter.setPen(major if int(round(x)) % 50 == 0 else minor)
            painter.drawLine(QLineF(x, rect.top(), x, rect.bottom()))
            x += 10
        y = top
        while y <= rect.bottom():
            painter.setPen(major if int(round(y)) % 50 == 0 else minor)
            painter.drawLine(QLineF(rect.left(), y, rect.right(), y))
            y += 10
        painter.restore()


class RulerWidget(QWidget):
    def __init__(self, canvas: ProfessionalCanvas, orientation: Qt.Orientation):
        super().__init__()
        self.canvas = canvas
        self.orientation = orientation
        if orientation == Qt.Horizontal:
            self.setFixedHeight(24)
        else:
            self.setFixedWidth(24)
            self.setMinimumHeight(40)
        self.setStyleSheet("background:#f7f9fc;border:0;color:#667085;")

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#f7f9fc"))
        p.setPen(QPen(QColor("#aeb7c5"), 1))
        font = QFont(self.font()); font.setPointSize(7); p.setFont(font)
        if self.orientation == Qt.Horizontal:
            p.drawLine(0, self.height()-1, self.width(), self.height()-1)
            start = self.canvas.mapToScene(0, 0).x()
            end = self.canvas.mapToScene(self.canvas.viewport().width(), 0).x()
            tick = math.floor(start / 10.0) * 10
            while tick <= end:
                x = self.canvas.mapFromScene(tick, 0).x()
                major = int(round(tick)) % 50 == 0
                p.drawLine(x, self.height()-1, x, self.height()-(10 if major else 5))
                if major: p.drawText(x+2, 2, 40, 12, Qt.AlignLeft, str(int(tick)))
                tick += 10
        else:
            p.drawLine(self.width()-1, 0, self.width()-1, self.height())
            start = self.canvas.mapToScene(0, 0).y()
            end = self.canvas.mapToScene(0, self.canvas.viewport().height()).y()
            tick = math.floor(start / 10.0) * 10
            while tick <= end:
                y = self.canvas.mapFromScene(0, tick).y()
                major = int(round(tick)) % 50 == 0
                p.drawLine(self.width()-1, y, self.width()-(10 if major else 5), y)
                if major:
                    p.save(); p.translate(2, y+32); p.rotate(-90)
                    p.drawText(0, 0, 40, 12, Qt.AlignLeft, str(int(tick))); p.restore()
                tick += 10


class InspectorSection(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("InspectorSection")
        outer = QVBoxLayout(self); outer.setContentsMargins(12, 8, 12, 10); outer.setSpacing(7)
        heading = QLabel(title); heading.setObjectName("InspectorTitle"); outer.addWidget(heading)
        self.form = QFormLayout(); self.form.setContentsMargins(0, 0, 0, 0)
        self.form.setHorizontalSpacing(8); self.form.setVerticalSpacing(6)
        self.form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        outer.addLayout(self.form)


class ProfessionalPageCanvasWidget(PageCanvasWidget):
    """Three-pane production workspace inspired by the supplied reference UI."""

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setObjectName("ImpositionWorkspace")
        self.setStyleSheet(WORKSPACE_STYLE)
        self.pages, self.thumbs, self.mix_entries = [], {}, []
        self.canvas = ProfessionalCanvas()
        self._status_pending = False

        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._build_command_bar())

        body = QSplitter(Qt.Horizontal); body.setChildrenCollapsible(False)
        body.addWidget(self._build_left_sidebar())
        body.addWidget(self._build_canvas_workspace())
        body.addWidget(self._build_inspector())
        body.setStretchFactor(0, 0); body.setStretchFactor(1, 1); body.setStretchFactor(2, 0)
        body.setSizes([250, 820, 285])
        root.addWidget(body, 1)

        self.canvas.scene().changed.connect(self._schedule_status_refresh)
        self.canvas.horizontalScrollBar().valueChanged.connect(self._update_rulers)
        self.canvas.verticalScrollBar().valueChanged.connect(self._update_rulers)
        self.canvas.undo_stack.indexChanged.connect(lambda _: self._schedule_status_refresh())
        self.list.itemSelectionChanged.connect(self._sync_selected_page)
        self._apply_sheet()
        self._refresh_status()

    def _command(self, text, icon, handler):
        button = QToolButton(); button.setObjectName("CommandButton")
        button.setText(text); button.setIcon(self.style().standardIcon(icon)); button.setIconSize(QSize(23, 23))
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon); button.clicked.connect(handler)
        return button

    def _build_command_bar(self):
        bar = QFrame(); bar.setObjectName("TopCommandBar")
        layout = QHBoxLayout(bar); layout.setContentsMargins(8, 0, 8, 0); layout.setSpacing(0)
        commands = [
            ("导入 PDF", QStyle.SP_DialogOpenButton, self.import_pdf),
            ("自动拼版", QStyle.SP_BrowserReload, self._auto_impose),
            ("生成反面", QStyle.SP_ArrowRight, self._generate_backside),
            ("撤销", QStyle.SP_ArrowBack, self.canvas.undo_stack.undo),
            ("重做", QStyle.SP_ArrowForward, self.canvas.undo_stack.redo),
            ("旋转 90°", QStyle.SP_BrowserReload, self.canvas.rotate_selected),
            ("删除版位", QStyle.SP_DialogDiscardButton, self.canvas.delete_selected),
        ]
        for text, icon, fn in commands: layout.addWidget(self._command(text, icon, fn))
        layout.addStretch(1)
        self.top_ready = QLabel("● 生产画布就绪"); self.top_ready.setObjectName("ReadyStatus")
        layout.addWidget(self.top_ready); layout.addSpacing(14)
        return bar

    def _build_left_sidebar(self):
        panel = QFrame(); panel.setObjectName("Sidebar"); panel.setMinimumWidth(220); panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel); layout.setContentsMargins(10, 8, 10, 8); layout.setSpacing(6)
        title_row = QHBoxLayout(); title = QLabel("作业文件"); title.setObjectName("PaneTitle")
        add = QToolButton(); add.setText("＋"); add.clicked.connect(self.import_pdf)
        title_row.addWidget(title); title_row.addStretch(); title_row.addWidget(add); layout.addLayout(title_row)
        self.file_summary = QLabel("尚未导入 PDF\n支持多文件、多页面和正反面")
        self.file_summary.setObjectName("Muted"); self.file_summary.setWordWrap(True); layout.addWidget(self.file_summary)
        divider = QFrame(); divider.setFrameShape(QFrame.HLine); divider.setStyleSheet("color:#e0e5ec;"); layout.addWidget(divider)
        page_title = QLabel("页面"); page_title.setObjectName("PaneTitle"); layout.addWidget(page_title)
        self.page_search = QLineEdit(); self.page_search.setObjectName("PageSearch")
        self.page_search.setPlaceholderText("搜索页面"); self.page_search.textChanged.connect(self._filter_pages)
        layout.addWidget(self.page_search)
        self.list = QListWidget(); self.list.setObjectName("PageList"); self.list.setIconSize(QSize(150, 105))
        self.list.setSpacing(3); self.list.itemDoubleClicked.connect(self.add_selected_page); layout.addWidget(self.list, 1)
        self.page_count = QLabel("共 0 页"); self.page_count.setObjectName("Muted"); layout.addWidget(self.page_count)
        return panel

    def _build_canvas_workspace(self):
        chrome = QFrame(); chrome.setObjectName("CanvasChrome")
        layout = QVBoxLayout(chrome); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        tabs = QFrame(); tabs.setStyleSheet("background:#ffffff;border-bottom:1px solid #d8dee8;")
        tab_layout = QHBoxLayout(tabs); tab_layout.setContentsMargins(10, 7, 10, 7); tab_layout.setSpacing(0)
        self.front_tab = QPushButton("正面"); self.front_tab.setObjectName("SideTab"); self.front_tab.setCheckable(True); self.front_tab.setChecked(True)
        self.back_tab = QPushButton("背面"); self.back_tab.setObjectName("SideTab"); self.back_tab.setCheckable(True)
        group = QButtonGroup(self); group.setExclusive(True); group.addButton(self.front_tab); group.addButton(self.back_tab)
        self.front_tab.clicked.connect(lambda: self.canvas.set_backside_visible(False))
        self.back_tab.clicked.connect(self._show_backside)
        tab_layout.addWidget(self.front_tab); tab_layout.addWidget(self.back_tab); tab_layout.addStretch()
        self.sheet_caption = QLabel("SRA3 · 450 × 320 mm"); self.sheet_caption.setObjectName("Muted"); tab_layout.addWidget(self.sheet_caption)
        layout.addWidget(tabs)

        ruler_top_row = QHBoxLayout(); ruler_top_row.setContentsMargins(0, 0, 0, 0); ruler_top_row.setSpacing(0)
        corner = QLabel("mm"); corner.setFixedSize(24, 24); corner.setAlignment(Qt.AlignCenter); corner.setObjectName("Muted")
        self.h_ruler = RulerWidget(self.canvas, Qt.Horizontal)
        ruler_top_row.addWidget(corner); ruler_top_row.addWidget(self.h_ruler, 1); layout.addLayout(ruler_top_row)
        canvas_row = QHBoxLayout(); canvas_row.setContentsMargins(0, 0, 0, 0); canvas_row.setSpacing(0)
        self.v_ruler = RulerWidget(self.canvas, Qt.Vertical); canvas_row.addWidget(self.v_ruler); canvas_row.addWidget(self.canvas, 1)
        layout.addLayout(canvas_row, 1)

        status = QFrame(); status.setObjectName("CanvasStatus")
        row = QHBoxLayout(status); row.setContentsMargins(12, 7, 12, 7)
        self.zoom_out = QPushButton("−"); self.zoom_out.setObjectName("SmallButton"); self.zoom_out.setFixedWidth(34)
        self.zoom_in = QPushButton("＋"); self.zoom_in.setObjectName("SmallButton"); self.zoom_in.setFixedWidth(34)
        self.zoom_label = QLabel("100%")
        self.zoom_out.clicked.connect(lambda: self._zoom(0.85)); self.zoom_in.clicked.connect(lambda: self._zoom(1.18))
        row.addWidget(self.zoom_out); row.addWidget(self.zoom_label); row.addWidget(self.zoom_in)
        row.addSpacing(18); row.addWidget(QLabel("利用率")); self.utilization = QLabel("0.0%"); self.utilization.setObjectName("Utilization"); row.addWidget(self.utilization)
        row.addStretch(); self.canvas_status = QLabel("等待导入页面"); self.canvas_status.setObjectName("ReadyStatus"); row.addWidget(self.canvas_status)
        layout.addWidget(status)
        return chrome

    def _dspin(self, value, minimum, maximum, suffix=" mm", decimals=1):
        w = QDoubleSpinBox(); w.setRange(minimum, maximum); w.setValue(value); w.setDecimals(decimals); w.setSuffix(suffix); return w

    def _build_inspector(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMinimumWidth(260); scroll.setMaximumWidth(330)
        panel = QFrame(); panel.setObjectName("Inspector")
        layout = QVBoxLayout(panel); layout.setContentsMargins(0, 0, 0, 10); layout.setSpacing(0)

        sheet = InspectorSection("纸张设置")
        self.paper_preset = QComboBox(); self.paper_preset.addItems(["SRA3 (450 × 320 mm)", "A3 (420 × 297 mm)", "SRA2 (640 × 450 mm)", "自定义"])
        self.sheet_w = self._dspin(450, 20, 3000); self.sheet_h = self._dspin(320, 20, 3000)
        self.paper_preset.currentIndexChanged.connect(self._apply_paper_preset)
        sheet.form.addRow("纸张尺寸", self.paper_preset); sheet.form.addRow("宽度", self.sheet_w); sheet.form.addRow("高度", self.sheet_h)
        layout.addWidget(sheet)

        product = InspectorSection("成品设置")
        self.trim_w = self._dspin(90, 1, 2000); self.trim_h = self._dspin(54, 1, 2000)
        self.bleed = self._dspin(3, 0, 50)
        product.form.addRow("成品宽度", self.trim_w); product.form.addRow("成品高度", self.trim_h); product.form.addRow("出血", self.bleed)
        layout.addWidget(product)

        params = InspectorSection("拼版参数")
        self.gap_x = self._dspin(5, 0, 200); self.gap_y = self._dspin(5, 0, 200)
        self.gripper = self._dspin(10, 0, 200); self.snap = self._dspin(1, .1, 50)
        self.auto_rotate = QCheckBox("旋转优化"); self.auto_rotate.setChecked(True)
        params.form.addRow("横向间距", self.gap_x); params.form.addRow("纵向间距", self.gap_y)
        params.form.addRow("咬口", self.gripper); params.form.addRow("吸附步长", self.snap); params.form.addRow("", self.auto_rotate)
        layout.addWidget(params)

        position = InspectorSection("选中版位")
        self.xpos = self._dspin(0, -3000, 3000, decimals=2); self.ypos = self._dspin(0, -3000, 3000, decimals=2)
        apply_pos = QPushButton("应用坐标"); apply_pos.setObjectName("SmallButton"); apply_pos.clicked.connect(self._apply_pos)
        position.form.addRow("X", self.xpos); position.form.addRow("Y", self.ypos); position.form.addRow("", apply_pos)
        layout.addWidget(position)

        marks = InspectorSection("印刷标记")
        self.crop_marks = QCheckBox("裁切线"); self.crop_marks.setChecked(True)
        self.registration_marks = QCheckBox("套准标记"); self.registration_marks.setChecked(True)
        self.color_bar = QCheckBox("色条"); self.color_bar.setChecked(True)
        self.info_text = QCheckBox("信息文字")
        for w in (self.crop_marks, self.registration_marks, self.color_bar, self.info_text): marks.form.addRow("", w)
        layout.addWidget(marks)

        duplex = InspectorSection("正反面与混拼")
        self.duplex_mode = QComboBox()
        self.duplex_mode.addItem("左右翻版", DuplexMode.LEFT_RIGHT.value); self.duplex_mode.addItem("天地翻版", DuplexMode.TOP_BOTTOM.value)
        self.duplex_mode.addItem("长边翻", DuplexMode.LONG_EDGE.value); self.duplex_mode.addItem("短边翻", DuplexMode.SHORT_EDGE.value)
        self.duplex_mode.addItem("自翻版 / 180°", DuplexMode.SELF_TURN.value)
        self.mix_qty = QSpinBox(); self.mix_qty.setRange(1, 10000000); self.mix_qty.setValue(100)
        add_mix = QPushButton("加入混拼队列"); add_mix.setObjectName("SmallButton"); add_mix.clicked.connect(self._add_mix_current)
        run_mix = QPushButton("最省纸混拼"); run_mix.setObjectName("SmallButton"); run_mix.clicked.connect(self._run_mixed_optimizer)
        duplex.form.addRow("反面方式", self.duplex_mode); duplex.form.addRow("需求数量", self.mix_qty); duplex.form.addRow("", add_mix); duplex.form.addRow("", run_mix)
        layout.addWidget(duplex)

        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
        recalc = QPushButton("重新计算拼版"); recalc.setObjectName("PrimaryButton"); recalc.clicked.connect(self._auto_impose)
        layout.addWidget(recalc); layout.addStretch()
        scroll.setWidget(panel); return scroll

    def _apply_paper_preset(self, index):
        sizes = {0:(450,320), 1:(420,297), 2:(640,450)}
        if index in sizes:
            w, h = sizes[index]; self.sheet_w.setValue(w); self.sheet_h.setValue(h); self._apply_sheet()

    def _filter_pages(self, text):
        query = text.strip().lower()
        for i in range(self.list.count()): self.list.item(i).setHidden(query not in self.list.item(i).text().lower())

    def _sync_selected_page(self):
        item = self.list.currentItem()
        if item is None: return
        idx = int(item.data(Qt.UserRole))
        if 0 <= idx < len(self.pages):
            info = self.pages[idx]; self.trim_w.setValue(info.width_mm); self.trim_h.setValue(info.height_mm)

    def _load_pdf(self, path):
        before = len(self.pages); super()._load_pdf(path)
        added = len(self.pages)-before
        if added:
            self.file_summary.setText(f"{Path(path).name}\n新增 {added} 页 · 已通过 PDF 读取")
            self.page_count.setText(f"共 {len(self.pages)} 页")
            if self.list.currentRow() < 0: self.list.setCurrentRow(0)
            self._refresh_status()

    def add_selected_page(self, item):
        super().add_selected_page(item); self._refresh_status()

    def _show_backside(self):
        self._generate_backside(); self.canvas.set_backside_visible(True); self._refresh_status()

    def _clear_front_items(self):
        self.canvas.clear_backside()
        for item in list(self.canvas.scene().items()):
            if isinstance(item, PageItem) and getattr(item, "side", "front") == "front": self.canvas.scene().removeItem(item)

    def _auto_impose(self):
        current = self.list.currentItem()
        if current is None:
            QMessageBox.information(self, "自动拼版", "请先导入 PDF 并选择一个页面。"); return
        idx = int(current.data(Qt.UserRole)); info = self.pages[idx]
        self._apply_sheet()
        sheet_w, sheet_h = self.sheet_w.value(), self.sheet_h.value()
        margin = max(self.bleed.value(), 0.0); gripper = max(self.gripper.value(), 0.0)
        avail_w = max(0.0, sheet_w-2*margin); avail_h = max(0.0, sheet_h-2*margin-gripper)
        gap_x, gap_y = self.gap_x.value(), self.gap_y.value()
        candidates = []
        for rotation, w, h in [(0, self.trim_w.value(), self.trim_h.value()), (90, self.trim_h.value(), self.trim_w.value())]:
            if rotation and not self.auto_rotate.isChecked(): continue
            cols = max(0, int((avail_w+gap_x)//(w+gap_x))); rows = max(0, int((avail_h+gap_y)//(h+gap_y)))
            candidates.append((cols*rows, rotation, w, h, cols, rows))
        count, rotation, footprint_w, footprint_h, cols, rows = max(candidates, default=(0,0,0,0,0,0))
        if count <= 0:
            QMessageBox.warning(self, "自动拼版", "当前成品尺寸无法放入所选纸张。"); return
        used_w = cols*footprint_w + max(0,cols-1)*gap_x; used_h = rows*footprint_h + max(0,rows-1)*gap_y
        start_x = margin + (avail_w-used_w)/2; start_y = margin + gripper + (avail_h-used_h)/2
        self._clear_front_items(); pix = self.thumbs.get((info.path, info.page_index))
        for row in range(rows):
            for col in range(cols):
                x = start_x + col*(footprint_w+gap_x); y = start_y + row*(footprint_h+gap_y)
                page = self.canvas.add_page(info, pix); page.setRotation(rotation)
                if rotation == 90: page.setPos(x+footprint_w, y)
                else: page.setPos(x, y)
                page.info.rotation = rotation
        self.canvas.undo_stack.clear(); self.canvas.fitInView(self.canvas.sceneRect(), Qt.KeepAspectRatio)
        self.canvas_status.setText(f"自动拼版完成 · {cols} × {rows} · {count} 件")
        self._refresh_status()

    def _run_mixed_optimizer(self):
        if not self.mix_entries:
            QMessageBox.information(self, "混拼", "请先选择页面并加入混拼队列。"); return
        specs, source_by_key = [], {}
        for row in self.mix_entries:
            idx = int(row["page_idx"])
            if not (0 <= idx < len(self.pages)): continue
            info = self.pages[idx]; key = str(idx); source_by_key[key] = (info, self.thumbs.get((info.path, info.page_index)))
            specs.append(ProductSpec(key, info.width_mm, info.height_mm, int(row["quantity"]), self.auto_rotate.isChecked()))
        self._apply_sheet()
        result = optimize_mixed(specs, self.sheet_w.value(), self.sheet_h.value(), margin_mm=max(self.bleed.value(), self.gripper.value()), gap_x_mm=self.gap_x.value(), gap_y_mm=self.gap_y.value())
        if not result.items:
            QMessageBox.warning(self, "混拼失败", "当前纸张尺寸无法容纳混拼队列中的产品。"); return
        self._clear_front_items()
        for packed in result.items:
            info, pix = source_by_key[packed.key]; item = self.canvas.add_page(info, pix)
            item.setRotation(int(packed.rotation)); item.info.rotation = int(packed.rotation)
            item.setPos(float(packed.x_mm)+float(packed.width_mm) if int(packed.rotation)==90 else float(packed.x_mm), float(packed.y_mm))
        self.canvas.undo_stack.clear(); self._refresh_mix_status(result); self._refresh_status()

    def _apply_sheet(self):
        self.canvas.snap_mm = self.snap.value(); self.canvas.set_sheet(self.sheet_w.value(), self.sheet_h.value(), self.bleed.value())
        if hasattr(self, "sheet_caption"):
            self.sheet_caption.setText(f"{self.paper_preset.currentText().split(' (')[0]} · {self.sheet_w.value():.0f} × {self.sheet_h.value():.0f} mm")
        self._update_rulers()

    def _zoom(self, factor):
        self.canvas.scale(factor, factor); self._update_rulers(); self._refresh_status()

    def _update_rulers(self, *_):
        if hasattr(self, "h_ruler"): self.h_ruler.update(); self.v_ruler.update()

    def _schedule_status_refresh(self, *_):
        if self._status_pending: return
        self._status_pending = True; QTimer.singleShot(0, self._refresh_status)

    def _refresh_status(self):
        self._status_pending = False
        items = [x for x in self.canvas.scene().items() if isinstance(x, PageItem) and getattr(x, "side", "front") == "front"]
        used = sum(max(0.0, x.sceneBoundingRect().width()) * max(0.0, x.sceneBoundingRect().height()) for x in items)
        sheet = max(1.0, self.sheet_w.value()*self.sheet_h.value())
        pct = min(999.9, used/sheet*100.0); self.utilization.setText(f"{pct:.1f}%")
        scale = self.canvas.transform().m11()*100; self.zoom_label.setText(f"{scale:.0f}%")
        if items:
            self.top_ready.setText("● 版面可生产"); self.canvas_status.setText(self.canvas_status.text() if "完成" in self.canvas_status.text() else f"画布 {len(items)} 个版位")
        else:
            self.top_ready.setText("● 等待版面"); self.canvas_status.setText("等待导入页面")
        self._update_rulers()
