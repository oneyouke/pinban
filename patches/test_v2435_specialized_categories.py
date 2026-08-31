import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from production_modes import ProductionModeWorkspace

app = QApplication.instance() or QApplication([])
w = ProductionModeWorkspace(); w.resize(1100, 760); w.show(); app.processEvents()
expected_tail = ["信封拼版", "纸袋拼版", "烫金击凸", "激光切割", "证卡照片"]
assert len(w.mode_buttons) == 17
assert [b.text() for b in w.mode_buttons[-5:]] == expected_tail

presets = {12: "envelope", 13: "paper_bag", 14: "foil", 15: "laser"}
for index, preset in presets.items():
    w._set_mode(index); app.processEvents()
    assert w.single_page.special_section.isVisible()
    assert w.single_page.special_preset.currentData() == preset
    assert w.mode_buttons[index].isChecked()
w._set_mode(16); app.processEvents()
assert w.single_page.inspector_group == "basic"
assert "证卡照片" in w.single_page.workspace_title.text()
assert not w.grab().isNull()
w.hide(); w.deleteLater(); app.processEvents()
print("V2.4.35 SPECIALIZED CATEGORIES PASS")
