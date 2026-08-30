import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from professional_canvas import ProfessionalPageCanvasWidget

app = QApplication.instance() or QApplication([])
widget = ProfessionalPageCanvasWidget()
widget.resize(1280, 800)
widget.show()
app.processEvents()
assert widget.objectName() == "ImpositionWorkspace"
assert widget.sheet_w.value() == 450
assert widget.sheet_h.value() == 320
assert widget.list.objectName() == "PageList"
assert widget.paper_preset.count() == 4
assert widget.crop_marks.isChecked()
assert widget.registration_marks.isChecked()
assert widget.color_bar.isChecked()
assert widget.canvas.scene() is not None
state = widget.export_state()
assert state["sheet"]["width_mm"] == 450
assert state["placements"] == []
preview = widget.grab()
assert not preview.isNull()
assert preview.width() == 1280
widget.close()
print("V2.4.20 PROFESSIONAL WORKSPACE PASS")
