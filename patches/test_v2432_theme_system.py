import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("DESKTOP_IMPOSER_DISABLE_SECURITY_UI", "1")

from PySide6.QtWidgets import QApplication
from app import MainWindow
from ui_themes import THEMES, app_style, mode_style, theme_choices, workspace_style

app = QApplication.instance() or QApplication([])
assert [key for key, _ in theme_choices()] == ["ocean", "graphite", "cloud", "warm"]
assert len({app_style(key) for key in THEMES}) == 4
assert all("QLabel { background:transparent" in app_style(key) for key in THEMES)

window = MainWindow(); window.resize(1280, 800); window.show(); app.processEvents()
assert len(window.theme_actions) == 4
for theme_id in THEMES:
    window.apply_ui_theme(theme_id, persist=False); app.processEvents()
    assert window._theme_id == theme_id
    assert window.professional_workspace.theme_id == theme_id
    assert window.professional_workspace.single_page.theme_id == theme_id
    assert window.professional_workspace.styleSheet() == mode_style(theme_id)
    assert window.professional_workspace.single_page.styleSheet() == workspace_style(theme_id)
    assert window.theme_actions[theme_id].isChecked()
    assert not window.grab().isNull()
window.close()
print("V2.4.32 MULTI THEME SYSTEM PASS")
