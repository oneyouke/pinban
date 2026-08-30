import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from production_modes import ProductionModeWorkspace, load_die_contour
from booklet import saddle_stitch

app = QApplication.instance() or QApplication([])
workspace = ProductionModeWorkspace()
assert workspace.stack.count() == 3
assert [b.text() for b in workspace.mode_buttons] == ["单页拼版", "书籍拼版", "盒型拼版"]
assert workspace.stack.currentWidget() is workspace.single_page
workspace.mode_buttons[1].click(); assert workspace.stack.currentWidget() is workspace.book
workspace.book.total_pages.setValue(20); workspace.book.binding.setCurrentText("骑马订"); workspace.book.calculate()
assert len(workspace.book.plan) == len(saddle_stitch(20, workspace.book.creep.value()))
assert workspace.book.preview.front is not None and workspace.book.preview.back is not None
workspace.mode_buttons[2].click(); assert workspace.stack.currentWidget() is workspace.box
workspace.box.points = [(0,0),(90,0),(90,54),(0,54)]; workspace.box.quantity.setValue(4); workspace.box.calculate()
assert workspace.box.plan and len(workspace.box.plan.placements) == 4
workspace.resize(1280,800); workspace.show(); app.processEvents(); assert not workspace.grab().isNull()
workspace.close()
print("V2.4.22 PRODUCTION MODES PASS")
