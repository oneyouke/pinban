from pathlib import Path
import os, shutil, py_compile

root=Path(os.environ.get("APP_ROOT",Path(__file__).resolve().parents[1]/"build-src"/"Desktop-Imposer-Pro-V2.2"))
patch_root=Path(__file__).resolve().parent
for name in ("production_control_v2438.py","test_v2438_production_control.py"):
    target="production_control.py" if name.startswith("production_control") else name
    shutil.copy2(patch_root/name,root/target)

def replace(path,old,new,label):
    text=path.read_text(encoding="utf-8")
    if old not in text: raise SystemExit(f"V2.4.38 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old,new,1),encoding="utf-8")

p=root/"production_modes.py"
replace(p,"from professional_canvas import ProfessionalPageCanvasWidget\n","from professional_canvas import ProfessionalPageCanvasWidget\nfrom production_control import ProductionControlBar\n","production control import")
replace(p,"        root.addWidget(self.mode_scroll); root.addWidget(self.stack,1)\n","""        self.production_scroll=QScrollArea(); self.production_scroll.setObjectName("ProductionScroller"); self.production_scroll.setWidgetResizable(True)
        self.production_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.production_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded); self.production_scroll.setFixedHeight(94)
        self.production_bar=ProductionControlBar(self.production_scroll); self.production_scroll.setWidget(self.production_bar)
        self.production_bar.simulate_requested.connect(self._simulate_production)
        self.production_bar.apply_requested.connect(self._apply_production_parameters)
        root.addWidget(self.mode_scroll); root.addWidget(self.production_scroll); root.addWidget(self.stack,1)
        self._update_production_context(0, "单页拼版")
""","production control bar")
replace(p,"        self.mode_hint.setText((\"单页生产工作台\", \"书刊折手与装订\", \"包装刀模与异形套料\", \"卷筒标签与模切\", \"卡牌正背配对\", \"数码切叠与短版\", \"特种工艺模板\", \"宣传单与名片\", \"多品种合版\", \"NCR 与流水票据\", \"海报与宽幅输出\", \"CSV/XLSX 逐件变量\", \"信封展开模板\", \"纸袋展开模板\", \"烫金与击凸专版\", \"激光切割刀线\", \"证件照与卡证\")[index])\n","""        mode_names=("单页拼版", "书籍拼版", "盒型拼版", "标签拼版", "卡片拼版", "数码拼版", "特种拼版", "商业印刷", "混合拼版", "票据联单", "大幅面", "可变数据", "信封拼版", "纸袋拼版", "烫金击凸", "激光切割", "证卡照片")
        self.mode_hint.setText(("单页生产工作台", "书刊折手与装订", "包装刀模与异形套料", "卷筒标签与模切", "卡牌正背配对", "数码切叠与短版", "特种工艺模板", "宣传单与名片", "多品种合版", "NCR 与流水票据", "海报与宽幅输出", "CSV/XLSX 逐件变量", "信封展开模板", "纸袋展开模板", "烫金与击凸专版", "激光切割刀线", "证件照与卡证")[index])
        self._update_production_context(stack_index, mode_names[index])

    def _update_production_context(self, stack_index=None, mode_name=None):
        stack_index = self.stack.currentIndex() if stack_index is None else stack_index
        mode_name = mode_name or self.production_bar.mode_name
        if stack_index == 1:
            width, height = self.book.sheet_w.value(), self.book.sheet_h.value(); copies = 1
        elif stack_index == 2:
            width, height = self.box.sheet_w.value(), self.box.sheet_h.value()
            copies = max(1, round(len(self.box.plan.placements)/max(1,self.box.plan.sheet_count))) if self.box.plan else 1
        else:
            width, height = self.single_page.sheet_w.value(), self.single_page.sheet_h.value()
            items=[x for x in self.single_page.canvas.scene().items() if hasattr(x,"info") and getattr(x,"side","front")=="front"]
            copies=max(1,len(items))
        self.production_bar.set_context(mode_name,width,height,copies)

    def _simulate_production(self):
        self._update_production_context(); return self.production_bar.calculate()

    def _apply_production_parameters(self, parameters):
        if self.stack.currentIndex()==0:
            self.single_page.gripper.setValue(float(parameters["gripper_mm"]))
            self.single_page.snap.setValue(float(parameters["move_step_mm"]))
            self.single_page.canvas.snap_mm=float(parameters["move_step_mm"])
            self.single_page._apply_sheet()
        self._simulate_production()
""","production mode sync")

style=root/"ui_themes.py"
text=style.read_text(encoding="utf-8")
marker="QWidget#ProductionModes, QWidget#ImpositionWorkspace {{ background:{p['window']}; color:{p['text']}; }}"
if marker not in text: raise SystemExit("V2.4.38 marker missing in ui_themes.py")
text=text.replace(marker,marker+'\nQFrame#ProductionControlBar {{ background:{p[\'surface\']}; border-bottom:1px solid {p[\'border\']}; }}\nQLabel#ProductionModeBadge {{ color:{p[\'accent\']}; font-weight:700; padding:4px 8px; background:{p[\'selected\']}; border-radius:4px; }}\nQPushButton#ProductionPrimary {{ background:{p[\'accent\']}; color:white; border:0; border-radius:4px; padding:5px 12px; font-weight:700; }}\nQPushButton#ProductionSecondary {{ background:{p[\'surface2\']}; color:{p[\'text\']}; border:1px solid {p[\'border\']}; border-radius:4px; padding:4px 10px; }}\nQLabel#ProductionEstimate {{ color:{p[\'success\']}; font-weight:700; padding-left:8px; }}\nQLabel#ProductionEstimate[warning="true"] {{ color:{p[\'warning\']}; }}',1)
style.write_text(text,encoding="utf-8")

for name in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/name; t=path.read_text(encoding="utf-8"); t=t.replace("2.4.37","2.4.38"); path.write_text(t,encoding="utf-8")
for name in ("production_control.py","production_modes.py","ui_themes.py","test_v2438_production_control.py"):
    py_compile.compile(str(root/name),doraise=True)
(root/"V2438_PRODUCTION_CONTROL.md").write_text("# V2.4.38 Production Control\n\nShared production parameter bar, machine validation, simulation and work-order export.\n",encoding="utf-8")
print("V2.4.38 production control integrated")
