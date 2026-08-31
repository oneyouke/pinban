from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
shutil.copy2(patch_root / "test_v2435_specialized_categories.py", root / "test_v2435_specialized_categories.py")

def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text: return
    if old not in text: raise SystemExit(f"V2.4.35 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

canvas = root / "professional_canvas.py"
replace_once(canvas,
    '''        if category in {"commercial", "mixed", "large"}:
            self.workspace_title.setText({"commercial": "商业印刷拼版工作台", "mixed": "多品种混合拼版工作台", "large": "大幅面拼版工作台"}[category])
''',
    '''        if category in {"commercial", "mixed", "large", "photo"}:
            self.workspace_title.setText({"commercial": "商业印刷拼版工作台", "mixed": "多品种混合拼版工作台", "large": "大幅面拼版工作台", "photo": "证卡照片拼版工作台"}[category])
''', "photo category")
replace_once(canvas,
    '''            "ticket": ("票据联单拼版工作台", self.special_section),
        }
        title, target = targets[category]; self.workspace_title.setText(title)
        if category == "ticket":
            index = self.special_preset.findData("ncr")
            if index >= 0: self.special_preset.setCurrentIndex(index)
''',
    '''            "ticket": ("票据联单拼版工作台", self.special_section),
            "envelope": ("信封拼版工作台", self.special_section),
            "paper_bag": ("纸袋拼版工作台", self.special_section),
            "finishing": ("烫金击凸拼版工作台", self.special_section),
            "laser": ("激光切割拼版工作台", self.special_section),
        }
        title, target = targets[category]; self.workspace_title.setText(title)
        preset = {"ticket": "ncr", "envelope": "envelope", "paper_bag": "paper_bag", "finishing": "foil", "laser": "laser"}.get(category)
        if preset:
            index = self.special_preset.findData(preset)
            if index >= 0: self.special_preset.setCurrentIndex(index)
''', "specialized presets")

mode = root / "production_modes.py"
replace_once(mode,
    '''        entries = (("单页拼版", 0), ("书籍拼版", 1), ("盒型拼版", 2), ("标签拼版", 0), ("卡片拼版", 0), ("数码拼版", 0), ("特种拼版", 0), ("商业印刷", 0), ("混合拼版", 0), ("票据联单", 0), ("大幅面", 0), ("可变数据", 0))
''',
    '''        entries = (("单页拼版", 0), ("书籍拼版", 1), ("盒型拼版", 2), ("标签拼版", 0), ("卡片拼版", 0), ("数码拼版", 0), ("特种拼版", 0), ("商业印刷", 0), ("混合拼版", 0), ("票据联单", 0), ("大幅面", 0), ("可变数据", 0), ("信封拼版", 0), ("纸袋拼版", 0), ("烫金击凸", 0), ("激光切割", 0), ("证卡照片", 0))
''', "seventeen categories")
replace_once(mode,
    '''        routes = ((0, None), (1, None), (2, None), (0, "label"), (0, "card"), (0, "digital"), (0, "special"), (0, "commercial"), (0, "mixed"), (0, "ticket"), (0, "large"), (0, "variable"))
''',
    '''        routes = ((0, None), (1, None), (2, None), (0, "label"), (0, "card"), (0, "digital"), (0, "special"), (0, "commercial"), (0, "mixed"), (0, "ticket"), (0, "large"), (0, "variable"), (0, "envelope"), (0, "paper_bag"), (0, "finishing"), (0, "laser"), (0, "photo"))
''', "specialized routes")
replace_once(mode,
    '''        self.mode_hint.setText(("单页生产工作台", "书刊折手与装订", "包装刀模与异形套料", "卷筒标签与模切", "卡牌正背配对", "数码切叠与短版", "特种工艺模板", "宣传单与名片", "多品种合版", "NCR 与流水票据", "海报与宽幅输出", "CSV/XLSX 逐件变量")[index])
''',
    '''        self.mode_hint.setText(("单页生产工作台", "书刊折手与装订", "包装刀模与异形套料", "卷筒标签与模切", "卡牌正背配对", "数码切叠与短版", "特种工艺模板", "宣传单与名片", "多品种合版", "NCR 与流水票据", "海报与宽幅输出", "CSV/XLSX 逐件变量", "信封展开模板", "纸袋展开模板", "烫金与击凸专版", "激光切割刀线", "证件照与卡证")[index])
''', "specialized hints")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    path = root / filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.34", "2.4.35"), encoding="utf-8")
for filename in ("professional_canvas.py", "production_modes.py", "test_v2435_specialized_categories.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")
(root / "V2435_SPECIALIZED_CATEGORIES.md").write_text("# V2.4.35 Specialized Categories\n\nAdds envelope, paper bag, finishing, laser-cut and photo/card production modes with automatic presets.\n", encoding="utf-8")
print("V2.4.35 specialized categories integrated")
