from __future__ import annotations


THEMES = {
    "ocean": {
        "name": "深海蓝", "dark": True,
        "window": "#111923", "surface": "#172230", "surface2": "#1d2b3b", "canvas": "#181c22",
        "input": "#101923", "border": "#30445a", "text": "#e6edf5", "muted": "#91a4b8",
        "accent": "#2f8cff", "accent_hover": "#57a3ff", "selected": "#173f6c", "success": "#4fd17b",
        "warning": "#f0b34f", "danger": "#ff6b75", "sheet_edge": "#2f8cff", "grid_minor": "#334354", "grid_major": "#52687f",
    },
    "graphite": {
        "name": "石墨黑", "dark": True,
        "window": "#161719", "surface": "#202226", "surface2": "#292c31", "canvas": "#181c22",
        "input": "#15171a", "border": "#41454d", "text": "#eeeeef", "muted": "#a2a5aa",
        "accent": "#8b7cf6", "accent_hover": "#a99df8", "selected": "#39335f", "success": "#62cf8b",
        "warning": "#e8b45b", "danger": "#ef6d78", "sheet_edge": "#8b7cf6", "grid_minor": "#383b40", "grid_major": "#5a5f67",
    },
    "cloud": {
        "name": "云雾浅色", "dark": False,
        "window": "#eef2f6", "surface": "#ffffff", "surface2": "#f5f7fa", "canvas": "#dde4eb",
        "input": "#ffffff", "border": "#cbd4df", "text": "#182433", "muted": "#68778a",
        "accent": "#1769d8", "accent_hover": "#0f5fc9", "selected": "#e3efff", "success": "#18864b",
        "warning": "#b66b11", "danger": "#c83b49", "sheet_edge": "#1769d8", "grid_minor": "#cbd4df", "grid_major": "#aab7c5",
    },
    "warm": {
        "name": "暖灰护眼", "dark": False,
        "window": "#eeeae3", "surface": "#faf8f3", "surface2": "#f2eee7", "canvas": "#d9d3ca",
        "input": "#fffdf8", "border": "#cbc2b5", "text": "#302d29", "muted": "#786f65",
        "accent": "#b05c3b", "accent_hover": "#96482d", "selected": "#f3dfd4", "success": "#3f8058",
        "warning": "#a66a23", "danger": "#b94c50", "sheet_edge": "#b05c3b", "grid_minor": "#c7c0b7", "grid_major": "#a89f94",
    },
}


def normalize_theme(theme_id):
    return theme_id if theme_id in THEMES else "ocean"


def theme_choices():
    return [(key, value["name"]) for key, value in THEMES.items()]


def theme_palette(theme_id):
    return dict(THEMES[normalize_theme(theme_id)])


def app_style(theme_id):
    p = theme_palette(theme_id)
    return f"""
QMainWindow, QDialog, QWidget {{ background:{p['window']}; color:{p['text']}; font-size:13px; }}
QLabel {{ background:transparent; color:{p['text']}; }}
QMenuBar {{ background:{p['surface']}; color:{p['text']}; border-bottom:1px solid {p['border']}; padding:2px; }}
QMenuBar::item {{ background:transparent; padding:6px 10px; border-radius:4px; }}
QMenuBar::item:selected {{ background:{p['selected']}; color:{p['accent']}; }}
QMenu {{ background:{p['surface']}; color:{p['text']}; border:1px solid {p['border']}; padding:5px; }}
QMenu::item {{ padding:7px 28px 7px 10px; border-radius:4px; }} QMenu::item:selected {{ background:{p['selected']}; color:{p['accent']}; }}
QMenu::separator {{ height:1px; background:{p['border']}; margin:4px 8px; }}
QToolBar {{ background:{p['surface']}; border-bottom:1px solid {p['border']}; spacing:2px; padding:3px; }}
QStatusBar {{ background:{p['surface']}; color:{p['muted']}; border-top:1px solid {p['border']}; }}
QFrame#Panel {{ background:{p['surface']}; border:1px solid {p['border']}; border-radius:8px; }}
QLabel#Title {{ color:{p['text']}; font-size:19px; font-weight:700; }} QLabel#Section {{ color:{p['muted']}; font-size:13px; font-weight:700; }}
QPushButton {{ min-height:31px; padding:0 12px; color:{p['text']}; border:1px solid {p['border']}; border-radius:5px; background:{p['surface2']}; }}
QPushButton:hover {{ color:{p['accent']}; border-color:{p['accent']}; background:{p['selected']}; }}
QPushButton:pressed {{ background:{p['selected']}; }} QPushButton:disabled {{ color:{p['muted']}; background:{p['surface2']}; }}
QPushButton#Primary {{ background:{p['accent']}; color:white; border:0; font-weight:700; }} QPushButton#Primary:hover {{ background:{p['accent_hover']}; color:white; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ background:{p['input']}; color:{p['text']}; border:1px solid {p['border']}; border-radius:5px; min-height:28px; padding:0 7px; selection-background-color:{p['accent']}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border:1px solid {p['accent']}; }}
QComboBox QAbstractItemView {{ background:{p['surface']}; color:{p['text']}; border:1px solid {p['border']}; selection-background-color:{p['selected']}; selection-color:{p['accent']}; }}
QCheckBox, QRadioButton {{ background:transparent; color:{p['text']}; spacing:7px; }}
QTableWidget, QListWidget, QTreeWidget {{ background:{p['input']}; alternate-background-color:{p['surface2']}; color:{p['text']}; border:1px solid {p['border']}; gridline-color:{p['border']}; selection-background-color:{p['selected']}; selection-color:{p['text']}; }}
QHeaderView::section {{ background:{p['surface2']}; color:{p['muted']}; border:0; border-right:1px solid {p['border']}; border-bottom:1px solid {p['border']}; padding:6px; font-weight:700; }}
QTabWidget::pane {{ border:1px solid {p['border']}; background:{p['surface']}; }} QTabBar::tab {{ color:{p['muted']}; background:{p['surface2']}; padding:7px 12px; border-bottom:2px solid transparent; }}
QTabBar::tab:selected {{ color:{p['accent']}; background:{p['surface']}; border-bottom-color:{p['accent']}; }}
QScrollArea {{ background:{p['surface']}; border:0; }} QSplitter::handle {{ background:{p['border']}; width:1px; height:1px; }}
QScrollBar:vertical {{ background:{p['window']}; width:10px; }} QScrollBar::handle:vertical {{ background:{p['border']}; border-radius:4px; min-height:28px; }}
QScrollBar:horizontal {{ background:{p['window']}; height:10px; }} QScrollBar::handle:horizontal {{ background:{p['border']}; border-radius:4px; min-width:28px; }}
QPdfView {{ background:{p['canvas']}; border:1px solid {p['border']}; }} QToolTip {{ background:{p['surface']}; color:{p['text']}; border:1px solid {p['border']}; }}
"""


def workspace_style(theme_id):
    p = theme_palette(theme_id)
    return f"""
QWidget#ImpositionWorkspace {{ background:{p['window']}; color:{p['text']}; }} QLabel {{ background:transparent; color:{p['text']}; }}
QFrame#TopCommandBar {{ background:{p['surface']}; border-bottom:1px solid {p['border']}; }} QLabel#WorkspaceTitle {{ color:{p['text']}; font-size:14px; font-weight:700; padding:0 12px; }}
QToolButton#CommandButton {{ background:transparent; border:0; border-right:1px solid {p['border']}; padding:5px 9px; min-width:54px; min-height:50px; color:{p['muted']}; font-size:11px; font-weight:600; }}
QToolButton#CommandButton:hover {{ background:{p['selected']}; color:{p['accent']}; }}
QFrame#Sidebar, QFrame#Inspector {{ background:{p['surface']}; border:0; }} QLabel#PaneTitle {{ font-size:13px; font-weight:700; color:{p['text']}; padding:6px 3px; }}
QLabel#Muted {{ color:{p['muted']}; font-size:11px; }} QFrame#PaneTabs, QFrame#InspectorTabs {{ background:{p['surface2']}; border-bottom:1px solid {p['border']}; }}
QPushButton#PaneTab, QPushButton#InspectorTab {{ color:{p['muted']}; background:transparent; border:0; border-bottom:2px solid transparent; min-height:32px; padding:0 13px; font-weight:700; }}
QPushButton#PaneTab:checked, QPushButton#InspectorTab:checked {{ color:{p['accent']}; border-bottom-color:{p['accent']}; background:{p['selected']}; }}
QLineEdit#PageSearch {{ background:{p['input']}; color:{p['text']}; border:1px solid {p['border']}; border-radius:5px; min-height:29px; padding:0 9px; }}
QListWidget#PageList {{ background:{p['window']}; color:{p['text']}; border:0; outline:0; padding:3px; }} QListWidget#PageList::item {{ background:{p['surface']}; border:1px solid {p['border']}; border-radius:5px; padding:7px; margin:3px 1px; color:{p['text']}; }}
QListWidget#PageList::item:selected {{ background:{p['selected']}; border:1px solid {p['accent']}; }}
QFrame#CanvasChrome {{ background:{p['canvas']}; border-left:1px solid {p['border']}; border-right:1px solid {p['border']}; }} QFrame#CanvasHeader {{ background:{p['surface']}; border-bottom:1px solid {p['border']}; }}
QPushButton#SideTab {{ border:0; border-bottom:2px solid transparent; background:transparent; min-width:62px; min-height:30px; padding:0 12px; color:{p['muted']}; font-weight:700; }}
QPushButton#SideTab:checked {{ background:{p['selected']}; color:{p['accent']}; border-bottom-color:{p['accent']}; }}
QFrame#CanvasTools {{ background:{p['surface']}; border-left:1px solid {p['border']}; }} QToolButton#CanvasTool {{ background:transparent; border:0; color:{p['muted']}; min-width:42px; min-height:45px; font-size:10px; }} QToolButton#CanvasTool:hover {{ background:{p['selected']}; color:{p['accent']}; }}
QFrame#CanvasStatus {{ background:{p['surface']}; border-top:1px solid {p['border']}; }} QLabel#MetricLabel {{ color:{p['muted']}; background:{p['input']}; border:1px solid {p['border']}; border-radius:4px; padding:4px 9px; }}
QLabel#Utilization, QLabel#ReadyStatus {{ color:{p['success']}; font-weight:700; }} QLabel#Utilization {{ font-size:15px; }}
QFrame#InspectorSection {{ background:{p['surface']}; border-bottom:1px solid {p['border']}; }} QLabel#InspectorTitle {{ font-size:12px; font-weight:700; color:{p['text']}; }}
QFrame#Divider {{ color:{p['border']}; background:{p['border']}; max-height:1px; border:0; }}
QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit {{ background:{p['input']}; color:{p['text']}; border:1px solid {p['border']}; border-radius:4px; min-height:27px; padding:0 6px; selection-background-color:{p['accent']}; }}
QComboBox QAbstractItemView {{ background:{p['surface']}; color:{p['text']}; selection-background-color:{p['selected']}; }} QCheckBox {{ background:transparent; color:{p['text']}; spacing:7px; min-height:22px; }}
QPushButton#SmallButton {{ background:{p['surface2']}; color:{p['text']}; border:1px solid {p['border']}; border-radius:4px; min-height:28px; padding:0 10px; }} QPushButton#SmallButton:hover {{ border-color:{p['accent']}; color:{p['accent']}; }}
QPushButton#PrimaryButton {{ background:{p['accent']}; color:white; border:0; border-radius:5px; min-height:38px; font-size:13px; font-weight:700; }} QPushButton#PrimaryButton:hover {{ background:{p['accent_hover']}; }}
QLabel#MixStatus {{ background:{p['input']}; border:1px solid {p['border']}; border-radius:4px; color:{p['muted']}; padding:7px; }} QScrollArea {{ border:0; background:{p['surface']}; }}
QFrame#BottomDock {{ background:{p['window']}; border-top:1px solid {p['border']}; }} QFrame#BottomDockHeader, QFrame#DockCard {{ background:{p['surface']}; border:0; }} QFrame#DockCard {{ border-right:1px solid {p['border']}; }}
QLabel#BottomDockTitle {{ color:{p['text']}; font-size:12px; font-weight:700; padding-left:8px; }} QToolButton#DockToggle {{ color:{p['muted']}; background:transparent; border:0; min-width:34px; min-height:25px; }}
QLabel#DockTitle {{ color:{p['accent']}; font-size:11px; font-weight:700; }} QLabel#DockValue {{ color:{p['muted']}; font-size:11px; }} QLabel#DockStrong {{ color:{p['success']}; font-size:18px; font-weight:700; }}
QScrollBar:vertical {{ background:{p['window']}; width:10px; }} QScrollBar::handle:vertical {{ background:{p['border']}; border-radius:4px; min-height:28px; }} QSplitter::handle {{ background:{p['border']}; width:1px; }}
/* compatibility anchor: #181c22 */
"""


def mode_style(theme_id):
    p = theme_palette(theme_id)
    return f"""
QWidget#ProductionModes, QWidget#ImpositionWorkspace {{ background:{p['window']}; color:{p['text']}; }} QLabel {{ background:transparent; color:{p['text']}; }}
QFrame#ModeBar {{ background:{p['surface']}; border-bottom:1px solid {p['border']}; }} QPushButton#ModeButton {{ color:{p['muted']}; background:transparent; border:0; border-bottom:2px solid transparent; padding:9px 22px; font-weight:700; }}
QPushButton#ModeButton:checked {{ color:{p['accent']}; background:{p['selected']}; border-bottom-color:{p['accent']}; }}
QFrame#ModePanel {{ background:{p['surface']}; border:0; color:{p['text']}; }} QLabel#ModeTitle {{ color:{p['text']}; font-size:17px; font-weight:700; }}
QLabel#ModeSummary {{ color:{p['muted']}; background:{p['surface2']}; border:1px solid {p['border']}; border-radius:5px; padding:8px; }}
QPushButton#PrimaryMode {{ background:{p['accent']}; color:white; border:0; border-radius:5px; min-height:38px; font-weight:700; }} QPushButton#PrimaryMode:hover {{ background:{p['accent_hover']}; }}
QPushButton#SecondaryMode {{ background:{p['surface2']}; color:{p['text']}; border:1px solid {p['border']}; border-radius:5px; min-height:32px; }} QPushButton#SecondaryMode:hover {{ color:{p['accent']}; border-color:{p['accent']}; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ background:{p['input']}; color:{p['text']}; border:1px solid {p['border']}; border-radius:4px; min-height:28px; padding:0 6px; selection-background-color:{p['accent']}; }}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{ background:{p['surface2']}; color:{p['muted']}; border-color:{p['border']}; }}
QComboBox QAbstractItemView {{ background:{p['surface']}; color:{p['text']}; selection-background-color:{p['selected']}; }} QCheckBox {{ background:transparent; color:{p['text']}; }}
QTableWidget {{ background:{p['input']}; alternate-background-color:{p['surface2']}; color:{p['text']}; border:1px solid {p['border']}; gridline-color:{p['border']}; selection-background-color:{p['selected']}; }}
QHeaderView::section {{ background:{p['surface2']}; color:{p['muted']}; border:0; border-right:1px solid {p['border']}; border-bottom:1px solid {p['border']}; padding:6px; }}
QScrollArea, QAbstractScrollArea::corner {{ background:{p['window']}; border:0; }} QScrollBar:vertical {{ background:{p['window']}; width:10px; }} QScrollBar::handle:vertical {{ background:{p['border']}; min-height:28px; border-radius:4px; }} QSplitter::handle {{ background:{p['border']}; width:1px; }}
/* compatibility anchor: #181c22 */
"""
