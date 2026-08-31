import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("DESKTOP_IMPOSER_DISABLE_SECURITY_UI", "1")

from pathlib import Path
from PySide6.QtWidgets import QApplication
from production_modes import ProductionModeWorkspace
from ui_themes import THEMES, app_style, mode_style, theme_choices, workspace_style

app = QApplication.instance() or QApplication([])
assert [key for key, _ in theme_choices()] == ["ocean", "graphite", "cloud", "warm"]
assert len({app_style(key) for key in THEMES}) == 4
assert all("QLabel { background:transparent" in app_style(key) for key in THEMES)

source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
assert 'addMenu("界面皮肤")' in source and 'set_setting("ui.theme"' in source
window = ProductionModeWorkspace(); window.resize(1280, 800); window.show(); app.processEvents()
for theme_id in THEMES:
    window.apply_theme(theme_id); app.processEvents()
    assert window.theme_id == theme_id
    assert window.single_page.theme_id == theme_id
    assert window.styleSheet() == mode_style(theme_id)
    assert window.single_page.styleSheet() == workspace_style(theme_id)
    assert not window.grab().isNull()
window.hide(); window.deleteLater(); app.processEvents()
print("V2.4.32 MULTI THEME SYSTEM PASS")
