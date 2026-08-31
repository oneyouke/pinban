from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
shutil.copy2(patch_root / "test_v2431_branding_cleanup.py", root / "test_v2431_branding_cleanup.py")

def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text: return
    if old not in text: raise SystemExit(f"V2.4.31 marker missing: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

mode = root / "production_modes.py"
replace_once(
    mode,
    '        self.brand=QLabel("智印拼版 · PRODUCTION WORKSPACE"); self.brand.setObjectName("ModeBrand"); row.addWidget(self.brand)\n',
    '        self.brand=QLabel("智印拼版 · PRODUCTION WORKSPACE"); self.brand.setObjectName("ModeBrand"); self.brand.setVisible(False)\n',
    "remove visible brand block",
)
replace_once(
    mode,
    '        row.addStretch(); self.mode_hint=QLabel("单页生产工作台"); self.mode_hint.setStyleSheet("color:#8d9aab;padding-right:12px;"); row.addWidget(self.mode_hint)\n',
    '        row.addStretch(); self.mode_hint=QLabel("单页生产工作台"); self.mode_hint.setVisible(False)\n',
    "remove visible mode hint",
)

product = root / "product.py"
replace_once(product, 'VENDOR_NAME = "Your Company"\n', 'VENDOR_NAME = "云游客科技"\n', "vendor")
replace_once(product, 'SUPPORT_EMAIL = "support@example.com"\n', 'SUPPORT_EMAIL = "3120085127@qq.com"\n', "support email")

installer = root / "installer.iss"
replace_once(installer, '#define MyAppPublisher "Your Company"\n', '#define MyAppPublisher "云游客科技"\n', "Inno publisher")
nsis = root / "installer_nsis.nsi"
replace_once(nsis, '  !define APP_PUBLISHER "Desktop Imposer"\n', '  !define APP_PUBLISHER "云游客科技"\n', "NSIS publisher")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    version_path = root / filename
    version_path.write_text(version_path.read_text(encoding="utf-8").replace("2.4.30", "2.4.31"), encoding="utf-8")
for filename in ("production_modes.py", "product.py", "test_v2431_branding_cleanup.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")
(root / "V2431_BRANDING_CLEANUP.md").write_text("# V2.4.31 Branding Cleanup\n\nRemoved framed mode-bar labels and updated vendor/support identity.\n", encoding="utf-8")
print("V2.4.31 branding cleanup integrated")
