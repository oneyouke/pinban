import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtWidgets import QApplication,QPushButton
from professional_canvas import ProfessionalPageCanvasWidget
app=QApplication.instance() or QApplication([]);widget=ProfessionalPageCanvasWidget()
assert widget.special_preset.count()==6 and widget.special_preset.currentData()=="envelope"
assert widget.special_width.value()==220 and widget.special_height.value()==110 and widget.special_parts.value()==3
labels={button.text() for button in widget.findChildren(QPushButton)}
assert "导出特种工艺模板 PDF" in labels and "载入模板参数" in labels
assert callable(widget._export_special_template_pdf)
widget.close();print("V2.4.28 SPECIAL TEMPLATE UI PASS")
