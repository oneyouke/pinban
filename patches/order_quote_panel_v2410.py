from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QTableWidget,QTableWidgetItem,QPushButton,
    QDoubleSpinBox,QSpinBox,QLabel,QFileDialog,QMessageBox
)
from order_quote import OrderLine, calculate_order, export_quote_csv, export_quote_json


class OrderQuotePanel(QWidget):
    def __init__(self,page_canvas=None,parent=None):
        super().__init__(parent); self.page_canvas=page_canvas; self.last_result=None
        root=QVBoxLayout(self)
        self.table=QTableWidget(0,4); self.table.setHorizontalHeaderLabels(['款号/名称','订单数量','每版拼数','备注'])
        root.addWidget(self.table,1)
        row=QHBoxLayout()
        for text,fn in [('新增一款',self.add_row),('删除选中',self.remove_selected),('从当前画布统计拼数',self.from_canvas)]:
            b=QPushButton(text); b.clicked.connect(fn); row.addWidget(b)
        row.addStretch(); root.addLayout(row)
        form=QFormLayout()
        self.spoilage=QDoubleSpinBox(); self.spoilage.setRange(0,100); self.spoilage.setDecimals(2); self.spoilage.setSuffix(' %')
        self.make_ready=QSpinBox(); self.make_ready.setRange(0,1000000)
        self.paper=QDoubleSpinBox(); self.paper.setRange(0,1e9); self.paper.setDecimals(4)
        self.printc=QDoubleSpinBox(); self.printc.setRange(0,1e9); self.printc.setDecimals(4)
        self.fixed=QDoubleSpinBox(); self.fixed.setRange(0,1e9); self.fixed.setDecimals(2)
        self.markup=QDoubleSpinBox(); self.markup.setRange(0,10000); self.markup.setDecimals(2); self.markup.setSuffix(' %')
        for label,w in [('废品率',self.spoilage),('放数/开机废张',self.make_ready),('纸张单张成本',self.paper),('印刷单张成本',self.printc),('固定成本',self.fixed),('加价率',self.markup)]: form.addRow(label,w)
        root.addLayout(form)
        calc=QPushButton('计算订单与报价'); calc.clicked.connect(self.calculate); root.addWidget(calc)
        self.summary=QLabel('尚未计算'); self.summary.setWordWrap(True); root.addWidget(self.summary)
        er=QHBoxLayout();
        c=QPushButton('导出 CSV 明细'); c.clicked.connect(self.export_csv); j=QPushButton('导出 JSON 明细'); j.clicked.connect(self.export_json)
        er.addWidget(c); er.addWidget(j); er.addStretch(); root.addLayout(er)
        self.add_row()

    def add_row(self,name='产品',qty=1000,pps=1,note=''):
        r=self.table.rowCount(); self.table.insertRow(r)
        vals=[name,str(qty),str(pps),note]
        for c,v in enumerate(vals): self.table.setItem(r,c,QTableWidgetItem(v))

    def remove_selected(self):
        rows=sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows: self.table.removeRow(r)

    def _lines(self):
        out=[]
        for r in range(self.table.rowCount()):
            name=(self.table.item(r,0).text().strip() if self.table.item(r,0) else '') or f'产品{r+1}'
            try: qty=int(float(self.table.item(r,1).text()))
            except Exception: qty=0
            try: pps=int(float(self.table.item(r,2).text()))
            except Exception: pps=0
            if qty>0 and pps>0: out.append(OrderLine(str(r),name,qty,pps))
        return out

    def from_canvas(self):
        if self.page_canvas is None: return
        counts={}
        try:
            from page_canvas import PageItem
            for item in self.page_canvas.canvas.scene().items():
                if isinstance(item,PageItem) and getattr(item,'side','front')=='front':
                    key=f'{Path(item.info.path).name} P{item.info.page_index+1}'
                    counts[key]=counts.get(key,0)+1
        except Exception as exc:
            QMessageBox.warning(self,'统计失败',str(exc)); return
        self.table.setRowCount(0)
        for name,pps in counts.items(): self.add_row(name,1000,pps,'来自当前画布')
        if not counts: self.add_row()

    def calculate(self):
        lines=self._lines()
        self.last_result=calculate_order(lines,spoilage_percent=self.spoilage.value(),make_ready_sheets=self.make_ready.value(),paper_cost_per_sheet=self.paper.value(),print_cost_per_sheet=self.printc.value(),fixed_cost=self.fixed.value(),markup_percent=self.markup.value())
        r=self.last_result
        detail='；'.join(f"{x['name']} 产出{x['produced_pieces']} / 余{x['surplus_pieces']} / 报价{x['allocated_quote']:.2f}" for x in r.lines)
        self.summary.setText(f'理论印张 {r.required_sheets} ｜ 实际印张 {r.actual_sheets} ｜ 成本 {r.total_cost:.2f} ｜ 报价 {r.quote_total:.2f} ｜ 单件报价 {r.quote_per_piece:.4f}\n{detail}')

    def export_csv(self):
        if self.last_result is None: self.calculate()
        path,_=QFileDialog.getSaveFileName(self,'导出成本报价明细','成本报价.csv','CSV (*.csv)')
        if path: export_quote_csv(path,self.last_result)

    def export_json(self):
        if self.last_result is None: self.calculate()
        path,_=QFileDialog.getSaveFileName(self,'导出成本报价明细','成本报价.json','JSON (*.json)')
        if path: export_quote_json(path,self.last_result)

    def export_state(self):
        rows=[]
        for r in range(self.table.rowCount()):
            rows.append([self.table.item(r,c).text() if self.table.item(r,c) else '' for c in range(4)])
        return {'rows':rows,'spoilage':self.spoilage.value(),'make_ready':self.make_ready.value(),'paper':self.paper.value(),'print':self.printc.value(),'fixed':self.fixed.value(),'markup':self.markup.value()}

    def import_state(self,state):
        state=state or {}; self.table.setRowCount(0)
        for row in state.get('rows') or []:
            vals=list(row)+['']*4; self.add_row(vals[0],vals[1],vals[2],vals[3])
        if self.table.rowCount()==0: self.add_row()
        for key,w in [('spoilage',self.spoilage),('make_ready',self.make_ready),('paper',self.paper),('print',self.printc),('fixed',self.fixed),('markup',self.markup)]:
            if key in state: w.setValue(float(state[key]))
