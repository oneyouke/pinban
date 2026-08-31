import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from production_modes import ProductionModeWorkspace

app = QApplication.instance() or QApplication([])
w = ProductionModeWorkspace(); w.resize(1100, 760); w.show(); app.processEvents()
expected = ["单页拼版", "书籍拼版", "盒型拼版", "标签拼版", "卡片拼版", "数码拼版", "特种拼版", "商业印刷", "混合拼版", "票据联单", "大幅面", "可变数据"]
assert [button.text() for button in w.mode_buttons] == expected
assert w.mode_scroll.horizontalScrollBarPolicy().name == "ScrollBarAsNeeded"

for index in range(7, 12):
    w._set_mode(index); app.processEvents()
    assert w.stack.currentWidget() is w.single_page and w.mode_buttons[index].isChecked()
w._set_mode(9); app.processEvents()
assert w.single_page.special_preset.currentData() == "ncr"
assert w.single_page.special_section.isVisible()
w._set_mode(11); app.processEvents()
assert any(section.isVisible() for section in w.single_page._inspector_sections["output"])
assert not w.grab().isNull()
w.hide(); w.deleteLater(); app.processEvents()
print("V2.4.34 EXTENDED CATEGORIES PASS")
