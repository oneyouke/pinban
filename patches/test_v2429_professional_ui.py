import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from professional_canvas import ProfessionalPageCanvasWidget

app = QApplication.instance() or QApplication([])
widget = ProfessionalPageCanvasWidget()
widget.resize(1280, 760); widget.show(); app.processEvents()

assert widget.objectName() == "ImpositionWorkspace"
assert [button.text() for button in widget.inspector_tabs] == ["基本", "工艺", "输出"]
assert widget.inspector_group == "basic"
assert not widget.sheet_section.isHidden()
assert widget.cut_stack_section.isHidden()
widget.inspector_tabs[1].click(); app.processEvents()
assert widget.inspector_group == "production"
assert widget.sheet_section.isHidden()
assert not widget.cut_stack_section.isHidden()
widget.inspector_tabs[2].click(); app.processEvents()
assert widget.inspector_group == "output"
assert not widget.marks_section.isHidden()
assert widget.canvas_tools.objectName() == "CanvasTools"
assert widget.status_pages.text() == "页面 0"
assert widget.status_placements.text() == "版位 0"
assert "#181c22" in widget.styleSheet()
assert not widget.grab().isNull()
widget.close()
print("V2.4.29 PROFESSIONAL UI PASS")
