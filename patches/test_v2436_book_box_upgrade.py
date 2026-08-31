import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from production_modes import BookImpositionWidget, BoxImpositionWidget

app = QApplication.instance() or QApplication([])

book = BookImpositionWidget(); book.binding.setCurrentText("胶装 / 锁线分帖")
book.total_pages.setValue(65); book.signature_pages.setCurrentText("16")
book.paper_caliper.setValue(.10); book.auto_spine.setChecked(True); book.calculate(); app.processEvents()
assert book.spine.value() == 3.25
assert "5 帖" in book.summary.text() and "补白 3 页" in book.summary.text()
assert book.safe_inset.value() == 3.0 and book.table.columnCount() == 8

box = BoxImpositionWidget(); box.points=[(0,0),(80,0),(80,50),(0,50)]; box.source_path="sample.svg"
box.quantity.setValue(8); box.sheet_w.setValue(320); box.sheet_h.setValue(220); box.margin.setValue(12)
box.grain.setCurrentIndex(1); box.calculate(); app.processEvents()
assert box.plan is not None and all(p.x_mm >= 12 and p.y_mm >= 12 for p in box.plan.placements)
assert all(p.rotation in (0,180) for p in box.plan.placements)
assert "有效版心" in box.summary.text() and "废料率" in box.summary.text()
book.deleteLater(); box.deleteLater(); app.processEvents()
print("V2.4.36 BOOK BOX UPGRADE PASS")
