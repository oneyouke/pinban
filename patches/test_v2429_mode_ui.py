import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from production_modes import ProductionModeWorkspace

app = QApplication.instance() or QApplication([])
workspace = ProductionModeWorkspace()
workspace.resize(1280, 800); workspace.show(); app.processEvents()
assert workspace.brand.text() == "智印拼版 · PRODUCTION WORKSPACE"
assert workspace.mode_bar.objectName() == "ModeBar"
assert workspace.mode_hint.text() == "单页生产工作台"
workspace.mode_buttons[1].click(); app.processEvents(); assert workspace.mode_hint.text() == "书刊折手与装订"
workspace.mode_buttons[2].click(); app.processEvents(); assert workspace.mode_hint.text() == "包装刀模与异形套料"
assert "#181c22" in workspace.styleSheet()
assert not workspace.grab().isNull()
workspace.close()
print("V2.4.29 MODE UI PASS")
