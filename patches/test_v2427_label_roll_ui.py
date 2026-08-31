import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton
from professional_canvas import ProfessionalPageCanvasWidget

app = QApplication.instance() or QApplication([])
widget = ProfessionalPageCanvasWidget()
assert widget.label_web_width.value() == 330
assert widget.label_repeat_length.value() == 254
assert widget.label_lanes.value() == 3 and widget.label_quantity.value() == 1000
assert widget.label_direction.count() == 4 and widget.label_winding.count() == 2
assert widget.label_slit_lines.isChecked() and widget.label_die_lines.isChecked()
labels = {button.text() for button in widget.findChildren(QPushButton)}
assert "导出卷筒标签生产 PDF" in labels
assert callable(widget._export_label_roll_pdf)
widget.close()
print("V2.4.27 LABEL ROLL UI PASS")
