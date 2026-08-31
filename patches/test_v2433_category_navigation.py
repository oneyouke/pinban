import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from production_modes import ProductionModeWorkspace

app = QApplication.instance() or QApplication([])
workspace = ProductionModeWorkspace(); workspace.resize(1600, 900); workspace.show(); app.processEvents()
expected = ["单页拼版", "书籍拼版", "盒型拼版", "标签拼版", "卡片拼版", "数码拼版", "特种拼版"]
assert [button.text() for button in workspace.mode_buttons] == expected

checks = {
    3: workspace.single_page.label_section,
    4: workspace.single_page.card_section,
    5: workspace.single_page.cut_stack_section,
    6: workspace.single_page.special_section,
}
for index, target in checks.items():
    workspace._set_mode(index); app.processEvents()
    assert workspace.stack.currentWidget() is workspace.single_page
    assert target.isVisible()
    assert sum(section.isVisible() for section in workspace.single_page._inspector_sections["production"]) == 1
    assert workspace.mode_buttons[index].isChecked()

workspace._set_mode(1); assert workspace.stack.currentWidget() is workspace.book
workspace._set_mode(2); assert workspace.stack.currentWidget() is workspace.box
workspace.hide(); workspace.deleteLater(); app.processEvents()
print("V2.4.33 CATEGORY NAVIGATION PASS")
