from pathlib import Path
import os
import shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent

# Product identity/version: ASCII-safe on Windows resources, shortcuts and uninstall entries.
p = root / "product.py"
s = p.read_text(encoding="utf-8")
s = s.replace('APP_NAME = "桌面拼版软件 Pro"', 'APP_NAME = "Desktop Imposer Pro"')
s = s.replace('APP_VERSION = "2.2.2"', 'APP_VERSION = "2.3.0"')
p.write_text(s, encoding="utf-8")

# Copy the standalone feature center module instead of embedding a huge Python string.
shutil.copy2(patch_root / "prepress_center.py", root / "prepress_center.py")

# Main UI integration.
p = root / "app.py"
s = p.read_text(encoding="utf-8")
if "from prepress_center import PrepressImpositionCenter" not in s:
    import_marker = "from health_check import run_health_checks\n"
    if import_marker not in s:
        raise SystemExit("app import marker not found")
    s = s.replace(import_marker, import_marker + "from prepress_center import PrepressImpositionCenter\n", 1)

# Add a Production menu entry using a conservative insertion around the existing menu creation.
if "印前与拼版中心…" not in s:
    menu_marker = '        production_menu = self.menuBar().addMenu("生产")\n'
    if menu_marker not in s:
        raise SystemExit("production menu marker not found")
    menu_insert = (
        menu_marker
        + '        center_act = QAction("印前与拼版中心…", self)\n'
        + '        center_act.triggered.connect(self.show_prepress_imposition_center)\n'
        + '        production_menu.addAction(center_act)\n'
        + '        production_menu.addSeparator()\n'
    )
    s = s.replace(menu_marker, menu_insert, 1)

if "def show_prepress_imposition_center" not in s:
    method_marker = "    def run_preflight(self):\n"
    if method_marker not in s:
        raise SystemExit("run_preflight marker not found")
    method = (
        "    def show_prepress_imposition_center(self):\n"
        "        dialog = PrepressImpositionCenter(self, self)\n"
        "        dialog.exec()\n\n"
    )
    s = s.replace(method_marker, method + method_marker, 1)

s = s.replace(
    'subtitle = QLabel("V2.1 商业发布强化版 · 权限/备份/审计/更新/恢复 · 生产全链路")',
    'subtitle = QLabel("V2.3 印前与智能拼版版 · 多格式/预检/混拼/折手/标记/变量数据/生产输出")',
)
p.write_text(s, encoding="utf-8")

# Installer identity/version; V2.2.2 already prepared a Unicode NSIS license file.
p = root / "installer_nsis.nsi"
s = p.read_text(encoding="utf-8")
s = s.replace('!define APP_NAME "桌面拼版软件 Pro"', '!define APP_NAME "Desktop Imposer Pro"')
s = s.replace('!define APP_VERSION "2.2.2"', '!define APP_VERSION "2.3.0"')
p.write_text(s, encoding="utf-8")

# Inno Setup fallback, when present.
p = root / "installer.iss"
if p.exists():
    s = p.read_text(encoding="utf-8")
    s = s.replace('#define MyAppName "桌面拼版软件 Pro"', '#define MyAppName "Desktop Imposer Pro"')
    s = s.replace('#define MyAppVersion "2.1.0"', '#define MyAppVersion "2.3.0"')
    p.write_text(s, encoding="utf-8")

# Package version.
p = root / "pyproject.toml"
s = p.read_text(encoding="utf-8").replace('version = "2.2.2"', 'version = "2.3.0"')
p.write_text(s, encoding="utf-8")

# Compile the new module before the rest of the build to fail fast on syntax errors.
compile((root / "prepress_center.py").read_text(encoding="utf-8"), str(root / "prepress_center.py"), "exec")
compile((root / "app.py").read_text(encoding="utf-8"), str(root / "app.py"), "exec")

(root / "V230_PREPRESS_IMPOSITION_CENTER.md").write_text(
    "# V2.3 Prepress & Imposition Center\n\n"
    "- Windows-facing product name standardized to Desktop Imposer Pro.\n"
    "- Adds a centralized prepress/imposition feature center.\n"
    "- Adds saddle-stitch and 8P/16P/24P/32P signature planning with creep metadata.\n"
    "- Professional PDF/X certification, font repair and RIP-grade separations remain provider-dependent.\n",
    encoding="utf-8",
)

print("V2.3.0 patch applied")
