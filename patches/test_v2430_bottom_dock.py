import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from page_canvas import PageInfo
from professional_canvas import ProfessionalPageCanvasWidget

app = QApplication.instance() or QApplication([])
widget = ProfessionalPageCanvasWidget(); widget.resize(1280, 800); widget.show(); app.processEvents()
assert widget.bottom_dock.objectName() == "BottomDock"
assert widget.bottom_content.isVisible()
assert widget.bottom_pages.text() == "0"
assert widget.bottom_placements.text() == "0"

info = PageInfo("sample.pdf", 0, 90 * 72 / 25.4, 54 * 72 / 25.4)
item = widget.canvas.add_page(info); item.setPos(12, 18); item.setSelected(True)
widget._refresh_status(); app.processEvents()
assert widget.bottom_placements.text() == "1"
assert "sample.pdf" in widget.selected_name.text()
assert "12.00" in widget.selected_geometry.text() and "18.00" in widget.selected_geometry.text()
assert "90.00 × 54.00" in widget.selected_size.text()

widget.layer_crop.setChecked(False); assert not widget.crop_marks.isChecked()
widget.layer_crop.setChecked(True); assert widget.crop_marks.isChecked()
widget.bottom_toggle.click(); app.processEvents(); assert not widget.bottom_content.isVisible()
widget.bottom_toggle.click(); app.processEvents(); assert widget.bottom_content.isVisible()
assert not widget.grab().isNull()
widget.close()
print("V2.4.30 BOTTOM PRODUCTION DOCK PASS")
