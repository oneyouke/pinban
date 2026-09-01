from pathlib import Path
import os,shutil,py_compile

root=Path(os.environ.get("APP_ROOT",Path(__file__).resolve().parents[1]/"build-src"/"Desktop-Imposer-Pro-V2.2")); patch_root=Path(__file__).resolve().parent
shutil.copy2(patch_root/"system_settings_v2440.py",root/"system_settings.py"); shutil.copy2(patch_root/"test_v2440_system_settings.py",root/"test_v2440_system_settings.py")

def replace(path,old,new,label):
    text=path.read_text(encoding="utf-8")
    if old not in text: raise SystemExit(f"V2.4.40 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old,new,1),encoding="utf-8")

p=root/"app.py"
replace(p,"from ui_themes import app_style, normalize_theme, theme_choices\n","from ui_themes import app_style, normalize_theme, theme_choices\nfrom system_settings import SystemSettingsDialog, apply_system_settings, load_system_settings\n","settings import")
replace(p,"        self.apply_ui_theme(self._theme_id, persist=False)\n        self._connect_signals()\n","        self.apply_ui_theme(self._theme_id, persist=False)\n        apply_system_settings(self, load_system_settings(self.db), apply_theme=False)\n        self._connect_signals()\n","load saved settings")
replace(p,'        for title, handler in [("工作台…", self.show_workspace),', '        for title, handler in [("系统设置…", self.show_system_settings), ("工作台…", self.show_workspace),',"system menu action")
replace(p,"    def show_device_center(self):\n",'''    def show_system_settings(self):
        dialog=SystemSettingsDialog(self.db,self,self); dialog.exec()

    def show_device_center(self):
''',"settings dialog method")

style=root/"ui_themes.py"; text=style.read_text(encoding="utf-8")
marker="QTabWidget::pane {{ border:1px solid {p['border']}; background:{p['surface']}; }}"
if marker not in text: raise SystemExit("V2.4.40 marker missing in ui_themes.py")
extra=marker+"\nQListWidget#SettingsCategories {{ background:{p['surface2']}; border:1px solid {p['border']}; padding:5px; }} QListWidget#SettingsCategories::item {{ min-height:31px; padding:2px 8px; border-radius:4px; }} QListWidget#SettingsCategories::item:selected {{ background:{p['accent']}; color:white; }} QFrame#SettingsPanel {{ background:{p['surface']}; border:1px solid {p['border']}; }} QLabel#SettingsTitle {{ font-size:18px; font-weight:700; color:{p['text']}; padding:5px 4px; }}"
style.write_text(text.replace(marker,extra,1),encoding="utf-8")

for name in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/name; path.write_text(path.read_text(encoding="utf-8").replace("2.4.39","2.4.40"),encoding="utf-8")
for name in ("system_settings.py","app.py","ui_themes.py","test_v2440_system_settings.py"): py_compile.compile(str(root/name),doraise=True)
(root/"V2440_SYSTEM_SETTINGS.md").write_text("# V2.4.40 System Settings\n\nPersistent 14-category system settings dialog with immediate workspace application.\n",encoding="utf-8")
print("V2.4.40 system settings integrated")
