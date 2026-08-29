from pathlib import Path
import os

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()

# --- app.py: restore visible/clickable spin-box arrow buttons globally ---
p = root / "app.py"
s = p.read_text(encoding="utf-8")
old = "app = QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setApplicationVersion(APP_VERSION); app.setStyleSheet(APP_STYLE)"
new = '''app = QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setApplicationVersion(APP_VERSION); app.setStyleSheet(APP_STYLE + r"""
QSpinBox, QDoubleSpinBox {
    padding-right: 24px;
}
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    min-height: 12px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    min-height: 12px;
}
""")'''
if old not in s:
    raise SystemExit("QApplication style marker not found for V2.3.1")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# --- prepress_center.py: add an interactive millimetre ruler page ---
p = root / "prepress_center.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    "from PySide6.QtWidgets import (\n",
    "from PySide6.QtCore import Qt, QRectF\nfrom PySide6.QtGui import QPainter, QPen, QFont\nfrom PySide6.QtWidgets import (\n",
    1,
)

widget_marker = "\n\nclass PrepressImpositionCenter(QDialog):\n"
if widget_marker not in s:
    raise SystemExit("Prepress center class marker not found")

ruler_code = r'''

class RulerWidget(QWidget):
    """Simple production ruler in millimetres for sheet/plate visual checking."""
    def __init__(self, orientation, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.length_mm = 320.0
        self.setMinimumSize(28, 28)
        if orientation == Qt.Horizontal:
            self.setFixedHeight(34)
        else:
            self.setFixedWidth(44)

    def set_length_mm(self, value):
        self.length_mm = max(1.0, float(value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().base())
        painter.setPen(QPen(self.palette().text().color(), 1))
        painter.setFont(QFont(self.font().family(), 7))

        if self.orientation == Qt.Horizontal:
            usable = max(1, self.width() - 8)
            px_per_mm = usable / self.length_mm
            baseline = self.height() - 1
            painter.drawLine(4, baseline, self.width() - 4, baseline)
            for mm in range(0, int(self.length_mm) + 1):
                x = 4 + mm * px_per_mm
                if x > self.width() - 4:
                    break
                major = (mm % 10 == 0)
                medium = (mm % 5 == 0)
                tick = 13 if major else (8 if medium else 4)
                painter.drawLine(int(x), baseline, int(x), baseline - tick)
                if major:
                    painter.drawText(int(x) + 2, 10, str(mm))
        else:
            usable = max(1, self.height() - 8)
            px_per_mm = usable / self.length_mm
            baseline = self.width() - 1
            painter.drawLine(baseline, 4, baseline, self.height() - 4)
            for mm in range(0, int(self.length_mm) + 1):
                y = 4 + mm * px_per_mm
                if y > self.height() - 4:
                    break
                major = (mm % 10 == 0)
                medium = (mm % 5 == 0)
                tick = 13 if major else (8 if medium else 4)
                painter.drawLine(baseline, int(y), baseline - tick, int(y))
                if major:
                    painter.save()
                    painter.translate(9, int(y) + 2)
                    painter.rotate(-90)
                    painter.drawText(0, 0, str(mm))
                    painter.restore()


class SheetPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sheet_w_mm = 320.0
        self.sheet_h_mm = 450.0
        self.setMinimumSize(420, 420)

    def set_sheet_mm(self, width_mm, height_mm):
        self.sheet_w_mm = max(1.0, float(width_mm))
        self.sheet_h_mm = max(1.0, float(height_mm))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())
        margin = 20
        aw = max(1, self.width() - margin * 2)
        ah = max(1, self.height() - margin * 2)
        scale = min(aw / self.sheet_w_mm, ah / self.sheet_h_mm)
        w = self.sheet_w_mm * scale
        h = self.sheet_h_mm * scale
        x = (self.width() - w) / 2
        y = (self.height() - h) / 2
        rect = QRectF(x, y, w, h)
        painter.fillRect(rect, self.palette().base())
        painter.setPen(QPen(self.palette().text().color(), 1))
        painter.drawRect(rect)
        painter.drawText(rect.adjusted(10, 10, -10, -10), Qt.AlignTop | Qt.AlignLeft,
                         f"大版 {self.sheet_w_mm:.1f} × {self.sheet_h_mm:.1f} mm")
'''
s = s.replace(widget_marker, ruler_code + widget_marker, 1)

old_tabs = '''        tabs.addTab(self._quick_actions_tab(), "快捷工作流")
        tabs.addTab(self._capability_tab(), "功能总览")
        tabs.addTab(self._booklet_tab(), "折手规划")
'''
new_tabs = '''        tabs.addTab(self._quick_actions_tab(), "快捷工作流")
        tabs.addTab(self._ruler_tab(), "版面标尺")
        tabs.addTab(self._capability_tab(), "功能总览")
        tabs.addTab(self._booklet_tab(), "折手规划")
'''
if old_tabs not in s:
    raise SystemExit("Prepress center tabs marker not found")
s = s.replace(old_tabs, new_tabs, 1)

method_marker = "    def _capability_tab(self):\n"
if method_marker not in s:
    raise SystemExit("Capability tab marker not found")
ruler_method = r'''    def _ruler_tab(self):
        w = QWidget()
        outer = QVBoxLayout(w)

        form = QHBoxLayout()
        form.addWidget(QLabel("大版宽"))
        self.ruler_w = QDoubleSpinBox()
        self.ruler_w.setRange(10, 5000)
        self.ruler_w.setDecimals(1)
        self.ruler_w.setSuffix(" mm")
        self.ruler_w.setValue(float(getattr(getattr(self.host, "sheet_w", None), "value", lambda: 320.0)()))
        form.addWidget(self.ruler_w)
        form.addWidget(QLabel("大版高"))
        self.ruler_h = QDoubleSpinBox()
        self.ruler_h.setRange(10, 5000)
        self.ruler_h.setDecimals(1)
        self.ruler_h.setSuffix(" mm")
        self.ruler_h.setValue(float(getattr(getattr(self.host, "sheet_h", None), "value", lambda: 450.0)()))
        form.addWidget(self.ruler_h)
        sync = QPushButton("读取主界面纸张尺寸")
        sync.clicked.connect(self._sync_ruler_from_host)
        form.addWidget(sync)
        form.addStretch()
        outer.addLayout(form)

        self.h_ruler = RulerWidget(Qt.Horizontal)
        self.v_ruler = RulerWidget(Qt.Vertical)
        self.sheet_preview = SheetPreview()

        body = QHBoxLayout()
        body.addWidget(self.v_ruler)
        center = QVBoxLayout()
        center.addWidget(self.h_ruler)
        center.addWidget(self.sheet_preview, 1)
        body.addLayout(center, 1)
        outer.addLayout(body, 1)

        self.ruler_w.valueChanged.connect(self._update_rulers)
        self.ruler_h.valueChanged.connect(self._update_rulers)
        self._update_rulers()
        return w

    def _sync_ruler_from_host(self):
        if hasattr(self.host, "sheet_w"):
            self.ruler_w.setValue(float(self.host.sheet_w.value()))
        if hasattr(self.host, "sheet_h"):
            self.ruler_h.setValue(float(self.host.sheet_h.value()))
        self._update_rulers()

    def _update_rulers(self, *_):
        width_mm = self.ruler_w.value()
        height_mm = self.ruler_h.value()
        self.h_ruler.set_length_mm(width_mm)
        self.v_ruler.set_length_mm(height_mm)
        self.sheet_preview.set_sheet_mm(width_mm, height_mm)

'''
s = s.replace(method_marker, ruler_method + method_marker, 1)
p.write_text(s, encoding="utf-8")

# --- versions ---
for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    p = root / filename
    text = p.read_text(encoding="utf-8").replace("2.3.0", "2.3.1")
    p.write_text(text, encoding="utf-8")

compile((root / "prepress_center.py").read_text(encoding="utf-8"), str(root / "prepress_center.py"), "exec")
compile((root / "app.py").read_text(encoding="utf-8"), str(root / "app.py"), "exec")

(root / "V231_UI_RULER_FIX.md").write_text(
    "# V2.3.1 UI controls and ruler fix\n\n"
    "- Restores visible/clickable QSpinBox and QDoubleSpinBox arrow buttons globally.\n"
    "- Adds horizontal and vertical millimetre rulers to the Prepress & Imposition Center.\n"
    "- Adds a sheet-size preview and sync-from-main-window action.\n",
    encoding="utf-8",
)
print("V2.3.1 UI/ruler patch applied")
