from pathlib import Path
import os, shutil, py_compile

root=Path(os.environ.get("APP_ROOT",Path(__file__).resolve().parents[1]/"build-src"/"Desktop-Imposer-Pro-V2.2"))
patch_root=Path(__file__).resolve().parent
shutil.copy2(patch_root/"test_v2439_compact_tools.py",root/"test_v2439_compact_tools.py")

def replace(path,old,new,label):
    text=path.read_text(encoding="utf-8")
    if old not in text: raise SystemExit(f"V2.4.39 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old,new,1),encoding="utf-8")

p=root/"professional_canvas.py"
replace(p,'        self.theme_id = "ocean"; self._grid_minor = QColor("#334354"); self._grid_major = QColor("#52687f")\n','        self.theme_id = "ocean"; self._grid_minor = QColor("#334354"); self._grid_major = QColor("#52687f")\n        self.grid_visible = True; self._next_group_id = 1\n',"canvas tool state")
replace(p,"        super().drawBackground(painter, rect)\n        painter.save()\n","        super().drawBackground(painter, rect)\n        if not self.grid_visible: return\n        painter.save()\n","grid visibility")
replace(p,"\n\nclass RulerWidget(QWidget):\n",'''\n
    def set_grid_visible(self, visible):
        self.grid_visible=bool(visible); self.viewport().update()

    def selected_pages(self):
        selected=super().selected_pages(); groups={getattr(item,"compact_group",None) for item in selected}; groups.discard(None)
        if not groups: return selected
        result=[]
        for item in self.scene().items():
            if isinstance(item,PageItem) and (item in selected or getattr(item,"compact_group",None) in groups): result.append(item)
        return result

    def group_selected(self):
        items=super().selected_pages()
        if len(items)<2: return 0
        group_id=self._next_group_id; self._next_group_id += 1
        for item in items: item.compact_group=group_id; item.setToolTip(item.toolTip().split("\\n群组：")[0]+f"\\n群组：{group_id}")
        return len(items)

    def ungroup_selected(self):
        items=self.selected_pages()
        for item in items:
            item.compact_group=None; item.setToolTip(item.toolTip().split("\\n群组：")[0])
        return len(items)

    def duplicate_selected(self):
        sources=list(self.selected_pages())
        for item in self.scene().selectedItems(): item.setSelected(False)
        for source in sources:
            item=PageItem(source.info,source.pixmap); item.side=getattr(source,"side","front"); item.setPos(source.x()+5,source.y()+5)
            item.setRotation(source.rotation()); item.setZValue(source.zValue()+1); self.scene().addItem(item); item.setSelected(True)
        return len(sources)

    def bring_forward(self):
        for item in self.selected_pages(): item.setZValue(item.zValue()+1)

    def send_backward(self):
        for item in self.selected_pages(): item.setZValue(max(-80,item.zValue()-1))


class RulerWidget(QWidget):
''',"compact canvas operations")
replace(p,"        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)\n        root.addWidget(self._build_command_bar())\n","        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)\n        root.addWidget(self._build_compact_toolbar())\n        root.addWidget(self._build_command_bar())\n","compact toolbar placement")
replace(p,"    def _build_command_bar(self):\n",'''    def _mini_tool(self, key, text, tooltip, handler, checkable=False, checked=False):
        button=QToolButton(); button.setObjectName("MiniTool"); button.setText(text); button.setToolTip(tooltip); button.setAccessibleName(tooltip)
        button.setCheckable(checkable); button.setChecked(checked)
        if checkable: button.toggled.connect(handler)
        else: button.clicked.connect(handler)
        self.compact_actions[key]=button; return button

    def _host_action(self, name, fallback=None):
        fn=getattr(self.production_host,name,None) if self.production_host is not None else None
        if callable(fn): return fn()
        if callable(fallback): return fallback()
        QMessageBox.information(self,"快捷工具",f"“{name}”需要在主程序窗口中使用。")

    def _toggle_mark(self, local_name, host_name, checked):
        local=getattr(self,local_name,None)
        if local is not None and local.isChecked()!=bool(checked): local.setChecked(bool(checked))
        host=getattr(self.production_host,host_name,None) if self.production_host is not None else None
        if host is not None and hasattr(host,"setChecked"): host.setChecked(bool(checked))

    def _selection_info(self):
        items=self.canvas.selected_pages()
        if not items: QMessageBox.information(self,"版位信息","当前没有选中版位。"); return
        bounds=[x.sceneBoundingRect() for x in items]
        QMessageBox.information(self,"版位信息",f"选中 {len(items)} 个版位\\n范围：{min(r.left() for r in bounds):.2f}, {min(r.top() for r in bounds):.2f} — {max(r.right() for r in bounds):.2f}, {max(r.bottom() for r in bounds):.2f} mm")

    def _toggle_barcode(self, name, checked):
        host=getattr(self.production_host,name,None) if self.production_host is not None else None
        if host is not None and hasattr(host,"setChecked"): host.setChecked(bool(checked))

    def _build_compact_toolbar(self):
        scroll=QScrollArea(); scroll.setObjectName("MiniToolScroller"); scroll.setWidgetResizable(True); scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded); scroll.setFixedHeight(42)
        bar=QFrame(); bar.setObjectName("MiniToolBar"); bar.setMinimumWidth(1110); row=QHBoxLayout(bar); row.setContentsMargins(4,2,4,2); row.setSpacing(1)
        self.compact_actions={}
        tools=(
            ("open","📂","打开项目",lambda:self._host_action("open_project",self.import_pdf),False,False),
            ("save","💾","保存项目",lambda:self._host_action("save_project"),False,False),
            ("order","订单","导入订单表",lambda:self._host_action("import_order_sheet"),False,False),
            ("export","PDF","输出拼版文件",self._export_host_pdf,False,False),
            ("info","ⓘ","查看选中版位信息",self._selection_info,False,False),
            ("fit","▣","画布适合窗口",lambda:self.canvas.fitInView(self.canvas.sceneRect(),Qt.KeepAspectRatio),False,False),
            ("duplicate","⧉","复制选中版位",self.canvas.duplicate_selected,False,False),
            ("delete","⌫","删除选中版位",self.canvas.delete_selected,False,False),
            ("grid","#","显示/隐藏网格",self.canvas.set_grid_visible,True,True),
            ("undo","↶","撤销",self.canvas.undo_stack.undo,False,False),
            ("redo","↷","重做",self.canvas.undo_stack.redo,False,False),
            ("group","群组","群组选中版位",self.canvas.group_selected,False,False),
            ("ungroup","解组","解组选中版位",self.canvas.ungroup_selected,False,False),
            ("finishing","后工","打开后加工参数",lambda:self.activate_category("finishing"),False,False),
            ("rotate","↻","旋转 90°",self.canvas.rotate_selected,False,False),
            ("forward","↑层","上移一层",self.canvas.bring_forward,False,False),
            ("backward","↓层","下移一层",self.canvas.send_backward,False,False),
            ("align_left","╞","左对齐",self.canvas.align_left,False,False),
            ("align_top","╥","顶对齐",self.canvas.align_top,False,False),
            ("center_h","↔","水平居中",self.canvas.center_horizontal,False,False),
            ("center_v","↕","垂直居中",self.canvas.center_vertical,False,False),
            ("distribute_h","⋯H","水平等距",self.canvas.distribute_horizontal,False,False),
            ("distribute_v","⋮V","垂直等距",self.canvas.distribute_vertical,False,False),
            ("crop","裁","裁切线",lambda v:self._toggle_mark("crop_marks","crop_marks",v),True,True),
            ("registration","准","套准标记",lambda v:self._toggle_mark("registration_marks","registration_marks",v),True,True),
            ("color","色","CMYK 色条",lambda v:self._toggle_mark("color_bar","color_bar",v),True,True),
            ("text","字","版面信息文字",lambda v:self._toggle_mark("info_text","sheet_info",v),True,False),
            ("barcode","条","订单 Code128 条码",lambda v:self._toggle_barcode("barcode_enabled",v),True,False),
            ("qr","QR","版级二维码",lambda v:self._toggle_barcode("qr_enabled",v),True,False),
            ("refresh","⟳","刷新版面状态",self._refresh_status,False,False),
            ("favorite","☆","保存为参数模板",lambda:self._host_action("save_template"),False,False),
        )
        for args in tools: row.addWidget(self._mini_tool(*args))
        row.addStretch(); scroll.setWidget(bar); self.compact_toolbar=scroll; return scroll

    def _build_command_bar(self):
''',"compact toolbar implementation")

style=root/"ui_themes.py"; text=style.read_text(encoding="utf-8")
marker="QFrame#TopCommandBar {{ background:{p['surface']}; border-bottom:1px solid {p['border']}; }}"
if marker not in text: raise SystemExit("V2.4.39 marker missing in ui_themes.py")
addition=marker+"\nQScrollArea#MiniToolScroller {{ background:{p['surface2']}; border:0; border-bottom:1px solid {p['border']}; }} QFrame#MiniToolBar {{ background:{p['surface2']}; border:0; }}\nQToolButton#MiniTool {{ background:transparent; color:{p['text']}; border:1px solid transparent; border-radius:3px; min-width:28px; min-height:28px; padding:1px 4px; font-weight:600; }} QToolButton#MiniTool:hover {{ color:{p['accent']}; background:{p['selected']}; border-color:{p['border']}; }} QToolButton#MiniTool:checked {{ color:white; background:{p['accent']}; }}"
style.write_text(text.replace(marker,addition,1),encoding="utf-8")

for name in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/name; t=path.read_text(encoding="utf-8").replace("2.4.38","2.4.39"); path.write_text(t,encoding="utf-8")
for name in ("professional_canvas.py","ui_themes.py","test_v2439_compact_tools.py"):
    py_compile.compile(str(root/name),doraise=True)
(root/"V2439_COMPACT_TOOLS.md").write_text("# V2.4.39 Compact Tools\n\nFunctional compact toolbar with project, canvas, grouping, alignment, marks and barcode shortcuts.\n",encoding="utf-8")
print("V2.4.39 compact tools integrated")
