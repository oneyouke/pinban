from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QSpinBox, QDoubleSpinBox, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QMessageBox
)

from production_planner import ProductionPlanInput, calculate_production_plan


class ProductionCalculatorPanel(QWidget):
    def __init__(self, page_canvas=None, parent=None):
        super().__init__(parent)
        self.page_canvas = page_canvas
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.order_qty = QSpinBox(); self.order_qty.setRange(0, 100000000); self.order_qty.setValue(1000)
        self.nup = QSpinBox(); self.nup.setRange(0, 100000); self.nup.setValue(8)
        self.spoilage = QDoubleSpinBox(); self.spoilage.setRange(0, 100); self.spoilage.setDecimals(2); self.spoilage.setValue(2.0); self.spoilage.setSuffix(' %')
        self.make_ready = QSpinBox(); self.make_ready.setRange(0, 1000000); self.make_ready.setValue(10)
        self.paper_cost = QDoubleSpinBox(); self.paper_cost.setRange(0, 1000000); self.paper_cost.setDecimals(4); self.paper_cost.setPrefix('¥ ')
        self.print_cost = QDoubleSpinBox(); self.print_cost.setRange(0, 1000000); self.print_cost.setDecimals(4); self.print_cost.setPrefix('¥ ')
        for label, widget in [
            ('订单数量', self.order_qty), ('每版数量', self.nup), ('废品率', self.spoilage),
            ('放数/开机废张', self.make_ready), ('纸张单张成本', self.paper_cost), ('印刷单张成本', self.print_cost),
        ]: form.addRow(label, widget)
        root.addLayout(form)

        row = QHBoxLayout()
        from_canvas = QPushButton('从当前画布统计每版数量'); from_canvas.clicked.connect(self.sync_from_canvas)
        calc = QPushButton('计算生产数据'); calc.clicked.connect(self.calculate)
        row.addWidget(from_canvas); row.addWidget(calc); row.addStretch(); root.addLayout(row)

        self.result = QLabel('填写参数后点击“计算生产数据”。')
        self.result.setWordWrap(True); root.addWidget(self.result)
        root.addStretch()

    def sync_from_canvas(self):
        if self.page_canvas is None or not hasattr(self.page_canvas, 'canvas'):
            QMessageBox.information(self, '生产计算', '当前没有可连接的拼版画布。'); return
        try:
            from page_canvas import PageItem
            count = sum(1 for item in self.page_canvas.canvas.scene().items()
                        if isinstance(item, PageItem) and getattr(item, 'side', 'front') == 'front')
        except Exception:
            count = 0
        self.nup.setValue(count)
        if count <= 0:
            QMessageBox.information(self, '生产计算', '当前画布没有正面版位。')

    def calculate(self):
        try:
            r = calculate_production_plan(ProductionPlanInput(
                order_quantity=self.order_qty.value(), pieces_per_sheet=self.nup.value(),
                spoilage_rate_percent=self.spoilage.value(), make_ready_sheets=self.make_ready.value(),
                paper_cost_per_sheet=self.paper_cost.value(), print_cost_per_sheet=self.print_cost.value(),
            ))
        except Exception as exc:
            QMessageBox.warning(self, '生产计算失败', str(exc)); return
        self.result.setText(
            f'理论印张：{r.theoretical_sheets}\n'
            f'废品率补偿：{r.spoilage_sheets} 张\n'
            f'放数/开机废张：{r.make_ready_sheets} 张\n'
            f'实际生产张数：{r.production_sheets} 张\n'
            f'预计成品数：{r.produced_pieces}\n'
            f'成品余量：{r.surplus_pieces}\n\n'
            f'纸张成本：¥ {r.paper_cost:.2f}\n'
            f'印刷成本：¥ {r.print_cost:.2f}\n'
            f'合计成本：¥ {r.total_cost:.2f}\n'
            f'订单单件成本：¥ {r.cost_per_order_piece:.4f}'
        )

    def export_state(self):
        return {
            'order_quantity': self.order_qty.value(), 'pieces_per_sheet': self.nup.value(),
            'spoilage_rate_percent': self.spoilage.value(), 'make_ready_sheets': self.make_ready.value(),
            'paper_cost_per_sheet': self.paper_cost.value(), 'print_cost_per_sheet': self.print_cost.value(),
        }

    def import_state(self, state):
        state = state or {}
        if 'order_quantity' in state: self.order_qty.setValue(int(state['order_quantity']))
        if 'pieces_per_sheet' in state: self.nup.setValue(int(state['pieces_per_sheet']))
        if 'spoilage_rate_percent' in state: self.spoilage.setValue(float(state['spoilage_rate_percent']))
        if 'make_ready_sheets' in state: self.make_ready.setValue(int(state['make_ready_sheets']))
        if 'paper_cost_per_sheet' in state: self.paper_cost.setValue(float(state['paper_cost_per_sheet']))
        if 'print_cost_per_sheet' in state: self.print_cost.setValue(float(state['print_cost_per_sheet']))
