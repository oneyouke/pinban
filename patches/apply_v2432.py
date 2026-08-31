from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
for src, dst in (("ui_themes_v2432.py", "ui_themes.py"), ("test_v2432_theme_system.py", "test_v2432_theme_system.py")):
    shutil.copy2(patch_root / src, root / dst)

def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text: return
    if old not in text: raise SystemExit(f"V2.4.32 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

# Professional single-page canvas.
ui = root / "professional_canvas.py"
replace_once(ui, "from page_canvas import ImpositionCanvas, PageCanvasWidget, PageItem\n", "from page_canvas import ImpositionCanvas, PageCanvasWidget, PageItem\nfrom ui_themes import normalize_theme, theme_palette, workspace_style\n", "theme import")
replace_once(ui, '''        super().__init__()
        self.setBackgroundBrush(QColor("#181c22"))
''', '''        super().__init__()
        self.theme_id = "ocean"; self._grid_minor = QColor("#334354"); self._grid_major = QColor("#52687f")
        self.setBackgroundBrush(QColor("#181c22"))
''', "canvas theme state")
replace_once(ui, '''    def drawBackground(self, painter: QPainter, rect):
''', '''    def apply_theme(self, theme_id):
        self.theme_id = normalize_theme(theme_id); palette = theme_palette(self.theme_id)
        self.setBackgroundBrush(QColor(palette["canvas"])); self.sheet.setBrush(QColor("#ffffff"))
        self.sheet.setPen(QPen(QColor(palette["sheet_edge"]), 1.2)); self.bleed_box.setPen(QPen(QColor("#ef77b7"), .7, Qt.DashLine))
        self._grid_minor = QColor(palette["grid_minor"]); self._grid_major = QColor(palette["grid_major"]); self.viewport().update()

    def drawBackground(self, painter: QPainter, rect):
''', "canvas apply theme")
replace_once(ui, '''        minor = QPen(QColor(214, 220, 229, 150), 0)
        major = QPen(QColor(187, 196, 208, 180), 0)
''', '''        minor = QPen(self._grid_minor, 0)
        major = QPen(self._grid_major, 0)
''', "theme grid")
replace_once(ui, '''        self.canvas = canvas
        self.orientation = orientation
''', '''        self.canvas = canvas
        self.orientation = orientation; self.theme_id = "ocean"; self._background = QColor("#1d2b3b"); self._ticks = QColor("#91a4b8")
''', "ruler theme state")
replace_once(ui, '        self.setStyleSheet("background:#242a32;border:0;color:#9aa6b6;")\n', '        self.setStyleSheet("background:transparent;border:0;")\n', "ruler transparent")
replace_once(ui, '''    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#242a32"))
        p.setPen(QPen(QColor("#6e7989"), 1))
''', '''    def apply_theme(self, theme_id):
        self.theme_id = normalize_theme(theme_id); palette = theme_palette(self.theme_id)
        self._background = QColor(palette["surface2"]); self._ticks = QColor(palette["muted"]); self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), self._background)
        p.setPen(QPen(self._ticks, 1))
''', "ruler painting")
replace_once(ui, '''        self.setObjectName("ImpositionWorkspace")
        self.setStyleSheet(WORKSPACE_STYLE)
''', '''        self.setObjectName("ImpositionWorkspace")
        self.theme_id = "ocean"; self.setStyleSheet(workspace_style(self.theme_id))
''', "workspace initial theme")
replace_once(ui, '''    def _command(self, text, icon, handler):
''', '''    def apply_theme(self, theme_id):
        self.theme_id = normalize_theme(theme_id); self.setStyleSheet(workspace_style(self.theme_id))
        self.canvas.apply_theme(self.theme_id); self.h_ruler.apply_theme(self.theme_id); self.v_ruler.apply_theme(self.theme_id)
        self.update()

    def _command(self, text, icon, handler):
''', "workspace apply theme")
replace_once(ui, '        divider = QFrame(); divider.setFrameShape(QFrame.HLine); divider.setStyleSheet("color:#e0e5ec;"); layout.addWidget(divider)\n', '        divider = QFrame(); divider.setObjectName("Divider"); divider.setFrameShape(QFrame.HLine); layout.addWidget(divider)\n', "themed divider")

# Book/box mode workspace and previews.
mode = root / "production_modes.py"
replace_once(mode, "from professional_canvas import ProfessionalPageCanvasWidget\n", "from professional_canvas import ProfessionalPageCanvasWidget\nfrom ui_themes import mode_style, normalize_theme, theme_palette\n", "mode theme import")
replace_once(mode, '''        self.flip = "长边翻"

    def set_spreads''', '''        self.flip = "长边翻"; self.theme_id = "ocean"

    def set_theme(self, theme_id):
        self.theme_id = normalize_theme(theme_id); self.update()

    def set_spreads''', "book preview theme")
replace_once(mode, '''        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#181c22"))
''', '''        painter = QPainter(self); palette = theme_palette(self.theme_id)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(palette["canvas"]))
''', "book preview background")
replace_once(mode, '            painter.setPen(QPen(QColor("#1769df"), 2)); painter.setBrush(QColor("white")); painter.drawRect(rect)\n            painter.setPen(QColor("#d8dee9")); painter.drawText', '            painter.setPen(QPen(QColor(palette["sheet_edge"]), 2)); painter.setBrush(QColor("white")); painter.drawRect(rect)\n            painter.setPen(QColor(palette["text"])); painter.drawText', "book preview palette")
replace_once(mode, '        self.summary = QLabel(); self.summary.setWordWrap(True); self.summary.setStyleSheet("color:#536176;background:#f5f8fc;padding:8px;border-radius:5px;"); left.addWidget(self.summary)\n', '        self.summary = QLabel(); self.summary.setObjectName("ModeSummary"); self.summary.setWordWrap(True); left.addWidget(self.summary)\n', "book summary")
replace_once(mode, '''    def set_plan(self, points, plan, sheet_w, sheet_h, bleed, sheet_no=1):
''', '''    def set_theme(self, theme_id):
        self.theme_id = normalize_theme(theme_id); self.update()

    def set_plan(self, points, plan, sheet_w, sheet_h, bleed, sheet_no=1):
''', "die preview apply theme")
replace_once(mode, '        self.points, self.plan = [], None; self.sheet_w, self.sheet_h = 650., 450.; self.bleed = 3.; self.sheet_no = 1\n', '        self.points, self.plan = [], None; self.sheet_w, self.sheet_h = 650., 450.; self.bleed = 3.; self.sheet_no = 1; self.theme_id = "ocean"\n', "die preview state")
replace_once(mode, '        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing); painter.fillRect(self.rect(), QColor("#181c22"))\n', '        painter = QPainter(self); palette = theme_palette(self.theme_id); painter.setRenderHint(QPainter.Antialiasing); painter.fillRect(self.rect(), QColor(palette["canvas"]))\n', "die preview background")
replace_once(mode, '        painter.setBrush(QColor("white")); painter.setPen(QPen(QColor("#1769df"),2)); painter.drawRect(sheet)\n', '        painter.setBrush(QColor("white")); painter.setPen(QPen(QColor(palette["sheet_edge"]),2)); painter.drawRect(sheet)\n', "die preview edge")
replace_once(mode, '        self.summary=QLabel("导入刀模后计算"); self.summary.setWordWrap(True); self.summary.setStyleSheet("color:#536176;background:#f5f8fc;padding:8px;border-radius:5px;"); left.addWidget(self.summary); left.addStretch(); split.addWidget(controls)\n', '        self.summary=QLabel("导入刀模后计算"); self.summary.setObjectName("ModeSummary"); self.summary.setWordWrap(True); left.addWidget(self.summary); left.addStretch(); split.addWidget(controls)\n', "box summary")
replace_once(mode, '        super().__init__(parent); self.setObjectName("ImpositionWorkspace"); self.setStyleSheet(MODE_STYLE); self.production_host=None\n', '        super().__init__(parent); self.setObjectName("ImpositionWorkspace"); self.theme_id = "ocean"; self.setStyleSheet(mode_style(self.theme_id)); self.production_host=None\n', "mode initial theme")
replace_once(mode, '''    def _set_mode(self, index):
''', '''    def apply_theme(self, theme_id):
        self.theme_id = normalize_theme(theme_id); self.setStyleSheet(mode_style(self.theme_id)); self.single_page.apply_theme(self.theme_id)
        self.book.preview.set_theme(self.theme_id); self.box.preview.set_theme(self.theme_id); self.update()

    def _set_mode(self, index):
''', "mode apply theme")

# Main menu, persistence and application-wide style.
app = root / "app.py"
replace_once(app, "from PySide6.QtGui import QAction, QFont, QFontDatabase\n", "from PySide6.QtGui import QAction, QActionGroup, QFont, QFontDatabase\n", "action group import")
replace_once(app, "from production_modes import ProductionModeWorkspace\n", "from production_modes import ProductionModeWorkspace\nfrom ui_themes import app_style, normalize_theme, theme_choices\n", "app theme import")
replace_once(app, '''        self.db = ProductionDB()
        self._previous_clean_shutdown''', '''        self.db = ProductionDB()
        self._theme_id = normalize_theme(self.db.get_setting("ui.theme", "ocean"))
        self._previous_clean_shutdown''', "stored theme")
replace_once(app, '''        self._build_ui()
        self._connect_signals()
''', '''        self._build_ui()
        self.apply_ui_theme(self._theme_id, persist=False)
        self._connect_signals()
''', "apply startup theme")
old = '''        system_menu = self.menuBar().addMenu("系统")
        for title, handler in [("工作台…", self.show_workspace), ("用户与权限…", self.show_users), ("创建备份…", self.create_backup_ui), ("恢复备份…", self.restore_backup_ui), ("自动备份设置…", self.configure_automatic_backup), ("系统健康检查…", self.show_health_check)]:
            act = QAction(title, self); act.triggered.connect(handler); system_menu.addAction(act)

        help_menu'''
new = '''        system_menu = self.menuBar().addMenu("系统")
        for title, handler in [("工作台…", self.show_workspace), ("用户与权限…", self.show_users), ("创建备份…", self.create_backup_ui), ("恢复备份…", self.restore_backup_ui), ("自动备份设置…", self.configure_automatic_backup), ("系统健康检查…", self.show_health_check)]:
            act = QAction(title, self); act.triggered.connect(handler); system_menu.addAction(act)
        system_menu.addSeparator(); theme_menu = system_menu.addMenu("界面皮肤"); self.theme_actions = {}; theme_group = QActionGroup(self); theme_group.setExclusive(True)
        for theme_id, theme_name in theme_choices():
            act = QAction(theme_name, self); act.setCheckable(True); act.setData(theme_id); act.setChecked(theme_id == self._theme_id)
            act.triggered.connect(lambda checked=False, value=theme_id: self.apply_ui_theme(value)); theme_group.addAction(act); theme_menu.addAction(act); self.theme_actions[theme_id] = act

        help_menu'''
replace_once(app, old, new, "theme menu")
replace_once(app, '''    @staticmethod
    def _section(text: str) -> QLabel:
''', '''    def apply_ui_theme(self, theme_id, persist=True):
        self._theme_id = normalize_theme(theme_id); instance = QApplication.instance()
        if instance is not None: instance.setStyleSheet(app_style(self._theme_id))
        if hasattr(self, "professional_workspace"): self.professional_workspace.apply_theme(self._theme_id)
        if hasattr(self, "theme_actions"):
            for key, action in self.theme_actions.items(): action.setChecked(key == self._theme_id)
        if persist and hasattr(self, "db"): self.db.set_setting("ui.theme", self._theme_id)

    @staticmethod
    def _section(text: str) -> QLabel:
''', "apply app theme method")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    version = root / filename; version.write_text(version.read_text(encoding="utf-8").replace("2.4.31", "2.4.32"), encoding="utf-8")
for filename in ("ui_themes.py", "professional_canvas.py", "production_modes.py", "app.py", "test_v2432_theme_system.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")
(root / "V2432_MULTI_THEME_UI.md").write_text("# V2.4.32 Multi-theme UI\n\nFour coordinated persisted skins covering the application, imposition workspaces, previews and controls.\n", encoding="utf-8")
print("V2.4.32 multi-theme UI integrated")
