from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from mix_optimizer import ProductSpec
from resource_matcher import PaperSpec, PressSpec, DEFAULT_PAPERS, DEFAULT_PRESSES, compare_resources


class ResourceMatchPanel(QWidget):
    def __init__(self, page_canvas, parent=None):
        super().__init__(parent)
        self.page_canvas = page_canvas
        self.results = []
        root = QVBoxLayout(self)

        top = QHBoxLayout()
        left = QVBoxLayout(); left.addWidget(QLabel('纸张库（名称 / 宽 mm / 高 mm）'))
        self.paper_table = QTableWidget(0, 3); self.paper_table.setHorizontalHeaderLabels(['名称','宽 mm','高 mm'])
        left.addWidget(self.paper_table)
        add_paper = QPushButton('新增纸张'); add_paper.clicked.connect(lambda: self._append_paper('新纸张', 450, 650))
        del_paper = QPushButton('删除选中纸张'); del_paper.clicked.connect(lambda: self._delete_rows(self.paper_table))
        row = QHBoxLayout(); row.addWidget(add_paper); row.addWidget(del_paper); left.addLayout(row)
        top.addLayout(left, 1)

        right = QVBoxLayout(); right.addWidget(QLabel('印刷机库（名称 / 最大宽 / 最大高 / 咬口 mm）'))
        self.press_table = QTableWidget(0, 4); self.press_table.setHorizontalHeaderLabels(['名称','最大宽 mm','最大高 mm','咬口 mm'])
        right.addWidget(self.press_table)
        add_press = QPushButton('新增印刷机'); add_press.clicked.connect(lambda: self._append_press('新印刷机', 530, 770, 8))
        del_press = QPushButton('删除选中印刷机'); del_press.clicked.connect(lambda: self._delete_rows(self.press_table))
        row = QHBoxLayout(); row.addWidget(add_press); row.addWidget(del_press); right.addLayout(row)
        top.addLayout(right, 1)
        root.addLayout(top, 1)

        action = QHBoxLayout()
        compare = QPushButton('比较全部纸张 / 印刷机'); compare.clicked.connect(self.compare_all)
        apply_best = QPushButton('应用最佳方案'); apply_best.clicked.connect(self.apply_selected)
        action.addWidget(compare); action.addWidget(apply_best)
        self.status = QLabel('先在“页面与画布”中建立混拼队列，再在这里比较资源。')
        action.addWidget(self.status, 1); root.addLayout(action)

        self.result_table = QTableWidget(0, 8)
        self.result_table.setHorizontalHeaderLabels(['纸张','印刷机','版面 mm','预计印张','总耗纸 m²','利用率','每版各款','策略'])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.doubleClicked.connect(lambda _idx: self.apply_selected())
        root.addWidget(self.result_table, 1)

        for p in DEFAULT_PAPERS: self._append_paper(p.name, p.width_mm, p.height_mm)
        for p in DEFAULT_PRESSES: self._append_press(p.name, p.max_width_mm, p.max_height_mm, p.gripper_mm)

    def _append_paper(self, name, w, h):
        r=self.paper_table.rowCount(); self.paper_table.insertRow(r)
        for c,v in enumerate((name,w,h)): self.paper_table.setItem(r,c,QTableWidgetItem(str(v)))

    def _append_press(self, name, w, h, g):
        r=self.press_table.rowCount(); self.press_table.insertRow(r)
        for c,v in enumerate((name,w,h,g)): self.press_table.setItem(r,c,QTableWidgetItem(str(v)))

    def _delete_rows(self, table):
        rows=sorted({i.row() for i in table.selectedIndexes()}, reverse=True)
        for r in rows: table.removeRow(r)

    def papers(self):
        out=[]
        for r in range(self.paper_table.rowCount()):
            try:
                out.append(PaperSpec(self.paper_table.item(r,0).text().strip(), float(self.paper_table.item(r,1).text()), float(self.paper_table.item(r,2).text())))
            except Exception: continue
        return out

    def presses(self):
        out=[]
        for r in range(self.press_table.rowCount()):
            try:
                out.append(PressSpec(self.press_table.item(r,0).text().strip(), float(self.press_table.item(r,1).text()), float(self.press_table.item(r,2).text()), float(self.press_table.item(r,3).text())))
            except Exception: continue
        return out

    def _specs(self):
        specs=[]
        for row in getattr(self.page_canvas,'mix_entries',[]) or []:
            idx=int(row.get('page_idx',-1))
            if 0 <= idx < len(self.page_canvas.pages):
                info=self.page_canvas.pages[idx]
                specs.append(ProductSpec(str(idx), info.width_mm, info.height_mm, int(row.get('quantity',1)), True))
        return specs

    def compare_all(self):
        specs=self._specs()
        if not specs:
            QMessageBox.information(self,'资源匹配','请先在“页面与画布”中把至少一个 PDF 页面加入混拼队列。'); return
        gap=max(0.0,float(self.page_canvas.snap.value()))
        margin=max(3.0,float(self.page_canvas.bleed.value()))
        self.results=compare_resources(specs,self.papers(),self.presses(),margin_mm=margin,gap_x_mm=gap,gap_y_mm=gap)
        self.result_table.setRowCount(0)
        for cand in self.results:
            r=self.result_table.rowCount(); self.result_table.insertRow(r)
            counts=', '.join(f'{k}:{v}' for k,v in sorted(cand.packed_by_key.items()))
            vals=[cand.paper.name,cand.press.name,f'{cand.sheet_width_mm:.0f}×{cand.sheet_height_mm:.0f}',str(cand.sheets_required),f'{cand.total_paper_area_mm2/1_000_000:.3f}',f'{cand.utilization*100:.1f}%',counts,cand.strategy]
            for c,v in enumerate(vals): self.result_table.setItem(r,c,QTableWidgetItem(v))
        if self.results:
            self.result_table.selectRow(0)
            best=self.results[0]
            self.status.setText(f'推荐：{best.paper.name} / {best.press.name} ｜ 预计 {best.sheets_required} 张 ｜ 总耗纸 {best.total_paper_area_mm2/1_000_000:.3f} m² ｜ 利用率 {best.utilization*100:.1f}%')
        else:
            self.status.setText('没有纸张/机器组合能完成当前混拼任务。')

    def apply_selected(self):
        if not self.results:
            self.compare_all()
            if not self.results: return
        row=self.result_table.currentRow()
        if row < 0 or row >= len(self.results): row=0
        cand=self.results[row]
        pc=self.page_canvas
        pc.sheet_w.setValue(cand.sheet_width_mm); pc.sheet_h.setValue(cand.sheet_height_mm); pc._apply_sheet()
        pc.canvas.clear_backside()
        for old in list(pc.canvas.scene().items()):
            if old.__class__.__name__=='PageItem' and getattr(old,'side','front')=='front': pc.canvas.scene().removeItem(old)
        source={}
        for mix in pc.mix_entries:
            idx=int(mix.get('page_idx',-1))
            if 0 <= idx < len(pc.pages):
                info=pc.pages[idx]; source[str(idx)]=(info,pc.thumbs.get((info.path,info.page_index)))
        for packed in cand.placements:
            if packed['key'] not in source: continue
            info,pix=source[packed['key']]
            item=pc.canvas.add_page(info,pix)
            if int(packed.get('rotation',0))==90:
                item.setRotation(90); item.setPos(float(packed['x_mm'])+float(packed['width_mm']),float(packed['y_mm']))
            else:
                item.setRotation(0); item.setPos(float(packed['x_mm']),float(packed['y_mm']))
            item.info.rotation=int(packed.get('rotation',0))
        pc.canvas.undo_stack.clear()
        self.status.setText(self.status.text() + ' ｜ 已应用到画布')

    def export_state(self):
        return {
            'papers':[{'name':p.name,'width_mm':p.width_mm,'height_mm':p.height_mm} for p in self.papers()],
            'presses':[{'name':p.name,'max_width_mm':p.max_width_mm,'max_height_mm':p.max_height_mm,'gripper_mm':p.gripper_mm} for p in self.presses()],
        }

    def import_state(self,state):
        state=state or {}; self.paper_table.setRowCount(0); self.press_table.setRowCount(0)
        for p in state.get('papers') or []: self._append_paper(p.get('name','纸张'),p.get('width_mm',450),p.get('height_mm',650))
        for p in state.get('presses') or []: self._append_press(p.get('name','印刷机'),p.get('max_width_mm',530),p.get('max_height_mm',770),p.get('gripper_mm',8))
        if self.paper_table.rowCount()==0:
            for p in DEFAULT_PAPERS: self._append_paper(p.name,p.width_mm,p.height_mm)
        if self.press_table.rowCount()==0:
            for p in DEFAULT_PRESSES: self._append_press(p.name,p.max_width_mm,p.max_height_mm,p.gripper_mm)
