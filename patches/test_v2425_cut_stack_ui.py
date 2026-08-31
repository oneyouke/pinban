import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from professional_canvas import ProfessionalPageCanvasWidget


app = QApplication.instance() or QApplication([])
widget = ProfessionalPageCanvasWidget()
assert widget.cut_rows.value() == 2 and widget.cut_columns.value() == 2
assert widget.cut_order.count() == 2
assert widget.cut_duplex.isChecked() is False
labels = {button.text() for button in widget.findChildren(QPushButton)}
assert "导出切叠式生产 PDF" in labels
assert callable(widget._export_cut_stack_pdf)
widget.close()
print("V2.4.25 CUT & STACK UI PASS")
