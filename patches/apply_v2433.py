from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
shutil.copy2(patch_root / "test_v2433_category_navigation.py", root / "test_v2433_category_navigation.py")

def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text: return
    if old not in text: raise SystemExit(f"V2.4.33 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

canvas = root / "professional_canvas.py"
replace_once(canvas,
    '        title = QLabel("拼版工作台"); title.setObjectName("WorkspaceTitle"); layout.addWidget(title)\n',
    '        title = QLabel("单页拼版工作台"); title.setObjectName("WorkspaceTitle"); self.workspace_title = title; layout.addWidget(title)\n',
    "workspace title handle")
replace_once(canvas,
    '        layout.addWidget(cards); self._inspector_sections["production"].append(cards)\n',
    '        layout.addWidget(cards); self._inspector_sections["production"].append(cards); self.card_section = cards\n',
    "card section handle")
replace_once(canvas,
    '        layout.addWidget(labels); self._inspector_sections["production"].append(labels)\n',
    '        layout.addWidget(labels); self._inspector_sections["production"].append(labels); self.label_section = labels\n',
    "label section handle")
replace_once(canvas,
    '        self.special_preset.currentIndexChanged.connect(self._apply_special_preset); layout.addWidget(special); self._inspector_sections["production"].append(special); self._apply_special_preset()\n',
    '        self.special_preset.currentIndexChanged.connect(self._apply_special_preset); layout.addWidget(special); self._inspector_sections["production"].append(special); self.special_section = special; self._apply_special_preset()\n',
    "special section handle")
replace_once(canvas,
    '''    def _dspin(self, value, minimum, maximum, suffix=" mm", decimals=1):
''',
    '''    def activate_category(self, category=None):
        self.active_category = category
        if category is None:
            self.workspace_title.setText("单页拼版工作台")
            self._set_inspector_group("basic")
            return
        targets = {
            "label": ("标签拼版工作台", self.label_section),
            "card": ("卡片拼版工作台", self.card_section),
            "digital": ("数码切叠拼版工作台", self.cut_stack_section),
            "special": ("特种产品拼版工作台", self.special_section),
        }
        title, target = targets[category]; self.workspace_title.setText(title)
        self._set_inspector_group("production")
        for section in self._inspector_sections["production"]: section.setVisible(section is target)

    def _dspin(self, value, minimum, maximum, suffix=" mm", decimals=1):
''', "category activation")

mode = root / "production_modes.py"
replace_once(mode,
    '''        for index,(text,widget) in enumerate((("单页拼版",self.single_page),("书籍拼版",self.book),("盒型拼版",self.box))):
            button=QPushButton(text); button.setObjectName("ModeButton"); button.setCheckable(True); button.setChecked(index==0); button.clicked.connect(lambda checked=False,i=index:self._set_mode(i)); group.addButton(button); row.addWidget(button); self.mode_buttons.append(button); self.stack.addWidget(widget)
''',
    '''        entries = (("单页拼版", 0), ("书籍拼版", 1), ("盒型拼版", 2), ("标签拼版", 0), ("卡片拼版", 0), ("数码拼版", 0), ("特种拼版", 0))
        for index,(text,stack_index) in enumerate(entries):
            button=QPushButton(text); button.setObjectName("ModeButton"); button.setCheckable(True); button.setChecked(index==0); button.clicked.connect(lambda checked=False,i=index:self._set_mode(i)); group.addButton(button); row.addWidget(button); self.mode_buttons.append(button)
        for widget in (self.single_page, self.book, self.box): self.stack.addWidget(widget)
''', "seven category buttons")
replace_once(mode,
    '''    def _set_mode(self, index):
        self.stack.setCurrentIndex(index)
        self.mode_hint.setText(("单页生产工作台", "书刊折手与装订", "包装刀模与异形套料")[index])
''',
    '''    def _set_mode(self, index):
        routes = ((0, None), (1, None), (2, None), (0, "label"), (0, "card"), (0, "digital"), (0, "special"))
        stack_index, category = routes[index]; self.stack.setCurrentIndex(stack_index)
        for number, button in enumerate(self.mode_buttons): button.setChecked(number == index)
        if stack_index == 0: self.single_page.activate_category(category)
        self.mode_hint.setText(("单页生产工作台", "书刊折手与装订", "包装刀模与异形套料", "卷筒标签与模切", "卡牌正背配对", "数码切叠与短版", "特种工艺模板")[index])
''', "category routing")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    path = root / filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.32", "2.4.33"), encoding="utf-8")
for filename in ("professional_canvas.py", "production_modes.py", "test_v2433_category_navigation.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")
(root / "V2433_CATEGORY_NAVIGATION.md").write_text("# V2.4.33 Category Navigation\n\nPromotes label, card, digital and special production tools to first-level modes.\n", encoding="utf-8")
print("V2.4.33 category navigation integrated")
