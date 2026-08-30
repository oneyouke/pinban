import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("DESKTOP_IMPOSER_DISABLE_SECURITY_UI", "1")

from PySide6.QtWidgets import QApplication
from app import MainWindow

app = QApplication.instance() or QApplication([])
window = MainWindow()
assert window.workspace_stack.currentWidget() is window.professional_workspace
assert window.professional_workspace.objectName() == "ImpositionWorkspace"
assert not window.main_toolbar.isVisible()
assert window.professional_workspace.production_host is window
window.show_legacy_workspace()
assert window.workspace_stack.currentWidget() is window.legacy_workspace
window.show_professional_workspace()
assert window.workspace_stack.currentWidget() is window.professional_workspace
window.close()
print("V2.4.21 MAIN WORKSPACE PASS")
