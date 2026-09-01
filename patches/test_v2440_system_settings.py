import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from pathlib import Path
from PySide6.QtWidgets import QApplication
from system_settings import DEFAULT_SYSTEM_SETTINGS, PAGE_SPECS, SETTING_KEY, SystemSettingsDialog, load_system_settings

class DB:
    def __init__(self): self.data={}
    def get_setting(self,key,default=None): return self.data.get(key,default)
    def set_setting(self,key,value): self.data[key]=value

app=QApplication.instance() or QApplication([]); db=DB(); dialog=SystemSettingsDialog(db)
assert len(PAGE_SPECS)==14 and dialog.stack.count()==14 and len(dialog.controls)>=80
dialog.controls["general.default_bleed"].setValue(5.0); dialog.controls["ui.theme"].setCurrentIndex(2); dialog._save()
assert db.data[SETTING_KEY]["general.default_bleed"]==5.0 and db.data[SETTING_KEY]["ui.theme"]=="cloud"
loaded=load_system_settings(db); assert loaded["general.default_bleed"]==5.0
dialog.categories.setCurrentRow(0); dialog.restore_page(); assert dialog.controls["general.default_bleed"].value()==DEFAULT_SYSTEM_SETTINGS["general.default_bleed"]
source=Path(__file__).with_name("app.py").read_text(encoding="utf-8")
assert "SystemSettingsDialog" in source and "系统设置…" in source and "show_system_settings" in source
dialog.deleteLater(); app.processEvents(); print("V2.4.40 SYSTEM SETTINGS PASS")
