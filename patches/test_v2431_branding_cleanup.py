import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("DESKTOP_IMPOSER_DISABLE_SECURITY_UI", "1")

from PySide6.QtWidgets import QApplication, QMessageBox
from app import MainWindow
from production_modes import ProductionModeWorkspace
from product import SUPPORT_EMAIL, VENDOR_NAME

app = QApplication.instance() or QApplication([])
workspace = ProductionModeWorkspace(); workspace.resize(1280, 800); workspace.show(); app.processEvents()
bar_layout = workspace.mode_bar.layout()
assert bar_layout.indexOf(workspace.brand) == -1
assert bar_layout.indexOf(workspace.mode_hint) == -1
assert workspace.brand.isHidden() and workspace.mode_hint.isHidden()
assert [button.text() for button in workspace.mode_buttons] == ["单页拼版", "书籍拼版", "盒型拼版"]
workspace.close()

assert VENDOR_NAME == "云游客科技"
assert SUPPORT_EMAIL == "3120085127@qq.com"
captured = {}
original = QMessageBox.information
QMessageBox.information = lambda parent, title, message, *args: captured.update(title=title, message=message) or QMessageBox.Ok
try:
    window = MainWindow(); window.about_commercial()
    assert captured["title"] == "关于"
    assert "厂商：云游客科技" in captured["message"]
    assert "支持：3120085127@qq.com" in captured["message"]
    assert "Your Company" not in captured["message"] and "support@example.com" not in captured["message"]
    window.close()
finally:
    QMessageBox.information = original
print("V2.4.31 BRANDING CLEANUP PASS")
