from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
shutil.copy2(patch_root / "test_v2434_extended_categories.py", root / "test_v2434_extended_categories.py")

def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text: return
    if old not in text: raise SystemExit(f"V2.4.34 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

canvas = root / "professional_canvas.py"
replace_once(canvas,
    '''        targets = {
            "label": ("标签拼版工作台", self.label_section),
            "card": ("卡片拼版工作台", self.card_section),
            "digital": ("数码切叠拼版工作台", self.cut_stack_section),
            "special": ("特种产品拼版工作台", self.special_section),
        }
        title, target = targets[category]; self.workspace_title.setText(title)
        self._set_inspector_group("production")
        for section in self._inspector_sections["production"]: section.setVisible(section is target)
''',
    '''        if category in {"commercial", "mixed", "large"}:
            self.workspace_title.setText({"commercial": "商业印刷拼版工作台", "mixed": "多品种混合拼版工作台", "large": "大幅面拼版工作台"}[category])
            self._set_inspector_group("basic"); return
        if category == "variable":
            self.workspace_title.setText("可变数据拼版工作台"); self._set_inspector_group("output"); return
        targets = {
            "label": ("标签拼版工作台", self.label_section),
            "card": ("卡片拼版工作台", self.card_section),
            "digital": ("数码切叠拼版工作台", self.cut_stack_section),
            "special": ("特种产品拼版工作台", self.special_section),
            "ticket": ("票据联单拼版工作台", self.special_section),
        }
        title, target = targets[category]; self.workspace_title.setText(title)
        if category == "ticket":
            index = self.special_preset.findData("ncr")
            if index >= 0: self.special_preset.setCurrentIndex(index)
        self._set_inspector_group("production")
        for section in self._inspector_sections["production"]: section.setVisible(section is target)
''', "extended category activation")

mode = root / "production_modes.py"
replace_once(mode,
    '    QSpinBox, QSplitter, QStackedWidget, QTableWidget, QTableWidgetItem,\n',
    '    QScrollArea, QSpinBox, QSplitter, QStackedWidget, QTableWidget, QTableWidgetItem,\n',
    "scroll area import")
replace_once(mode,
    '''        bar=QFrame(); bar.setObjectName("ModeBar"); self.mode_bar = bar; row=QHBoxLayout(bar); row.setContentsMargins(10,6,10,6)
''',
    '''        self.mode_scroll=QScrollArea(); self.mode_scroll.setObjectName("ModeScroller"); self.mode_scroll.setWidgetResizable(True); self.mode_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.mode_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded); self.mode_scroll.setFixedHeight(72)
        bar=QFrame(); bar.setObjectName("ModeBar"); self.mode_bar = bar; row=QHBoxLayout(bar); row.setContentsMargins(10,6,10,6); self.mode_scroll.setWidget(bar)
''', "scrollable mode bar")
replace_once(mode,
    '''        entries = (("单页拼版", 0), ("书籍拼版", 1), ("盒型拼版", 2), ("标签拼版", 0), ("卡片拼版", 0), ("数码拼版", 0), ("特种拼版", 0))
''',
    '''        entries = (("单页拼版", 0), ("书籍拼版", 1), ("盒型拼版", 2), ("标签拼版", 0), ("卡片拼版", 0), ("数码拼版", 0), ("特种拼版", 0), ("商业印刷", 0), ("混合拼版", 0), ("票据联单", 0), ("大幅面", 0), ("可变数据", 0))
''', "twelve categories")
replace_once(mode, '        root.addWidget(bar); root.addWidget(self.stack,1)\n', '        root.addWidget(self.mode_scroll); root.addWidget(self.stack,1)\n', "install mode scroller")
replace_once(mode,
    '''        routes = ((0, None), (1, None), (2, None), (0, "label"), (0, "card"), (0, "digital"), (0, "special"))
''',
    '''        routes = ((0, None), (1, None), (2, None), (0, "label"), (0, "card"), (0, "digital"), (0, "special"), (0, "commercial"), (0, "mixed"), (0, "ticket"), (0, "large"), (0, "variable"))
''', "extended routes")
replace_once(mode,
    '''        self.mode_hint.setText(("单页生产工作台", "书刊折手与装订", "包装刀模与异形套料", "卷筒标签与模切", "卡牌正背配对", "数码切叠与短版", "特种工艺模板")[index])
''',
    '''        self.mode_hint.setText(("单页生产工作台", "书刊折手与装订", "包装刀模与异形套料", "卷筒标签与模切", "卡牌正背配对", "数码切叠与短版", "特种工艺模板", "宣传单与名片", "多品种合版", "NCR 与流水票据", "海报与宽幅输出", "CSV/XLSX 逐件变量")[index])
''', "extended hints")

themes = root / "ui_themes.py"
replace_once(themes,
    '''QFrame#ModeBar {{ background:{p['surface']}; border-bottom:1px solid {p['border']}; }} QPushButton#ModeButton {{ color:{p['muted']}; background:transparent; border:0; border-bottom:2px solid transparent; padding:9px 22px; font-weight:700; }}
''',
    '''QScrollArea#ModeScroller {{ background:{p['surface']}; border:0; border-bottom:1px solid {p['border']}; }} QScrollArea#ModeScroller QWidget#qt_scrollarea_viewport {{ background:{p['surface']}; }}
QFrame#ModeBar {{ background:{p['surface']}; border:0; }} QPushButton#ModeButton {{ color:{p['muted']}; background:transparent; border:0; border-bottom:2px solid transparent; padding:9px 18px; font-weight:700; }}
''', "scrollable mode theme")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    path = root / filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.33", "2.4.34"), encoding="utf-8")
for filename in ("professional_canvas.py", "production_modes.py", "ui_themes.py", "test_v2434_extended_categories.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")
(root / "V2434_EXTENDED_CATEGORIES.md").write_text("# V2.4.34 Extended Categories\n\nAdds commercial, mixed, ticket, wide-format and variable-data production modes with responsive navigation.\n", encoding="utf-8")
print("V2.4.34 extended categories integrated")
