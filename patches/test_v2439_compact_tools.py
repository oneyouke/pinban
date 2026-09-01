import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from page_canvas import PageInfo, PageItem
from professional_canvas import ProfessionalCanvas, ProfessionalPageCanvasWidget

app=QApplication.instance() or QApplication([])
canvas=ProfessionalCanvas(); info=PageInfo("demo.pdf",0,120,80)
a=canvas.add_page(info); b=canvas.add_page(info); a.setSelected(True); b.setSelected(True)
assert canvas.group_selected() == 2
a.setSelected(False); b.setSelected(False); a.setSelected(True)
assert len(canvas.selected_pages()) == 2
assert canvas.duplicate_selected() == 2
assert canvas.ungroup_selected() >= 2
canvas.set_grid_visible(False); assert canvas.grid_visible is False

widget=ProfessionalPageCanvasWidget()
required={"open","save","order","export","info","duplicate","group","ungroup","grid","undo","redo","rotate","align_left","align_top","center_h","center_v","distribute_h","distribute_v","crop","registration","color","barcode","qr","refresh","favorite"}
assert required.issubset(widget.compact_actions)
assert len(widget.compact_actions) >= 25
widget.compact_actions["grid"].setChecked(False); assert widget.canvas.grid_visible is False
widget.deleteLater(); canvas.deleteLater(); app.processEvents()
print("V2.4.39 COMPACT TOOLS PASS")
