from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from math import ceil
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)


PAPERS = (
    ("铜版纸 105g", 105), ("铜版纸 128g", 128), ("铜版纸 157g", 157),
    ("哑粉纸 157g", 157), ("双胶纸 80g", 80), ("双胶纸 100g", 100),
    ("白卡纸 250g", 250), ("白卡纸 300g", 300), ("灰底白板 350g", 350),
)

MACHINES = (
    ("海德堡 SM74（745×605）", 745, 605, 10500),
    ("海德堡 XL75（750×605）", 750, 605, 15000),
    ("小森 Lithrone 40（1020×720）", 1020, 720, 13000),
    ("罗兰 700（1040×740）", 1040, 740, 15000),
    ("数码印刷机（330×488）", 330, 488, 3600),
    ("宽幅喷墨机（1600×3200）", 1600, 3200, 120),
)

TEMPLATES = {
    "标准生产": dict(gripper=10.0, tail=3.0, move=1.0, waste=3.0, ready=50),
    "节省纸张": dict(gripper=8.0, tail=2.0, move=.5, waste=2.0, ready=30),
    "稳定走纸": dict(gripper=12.0, tail=5.0, move=1.0, waste=5.0, ready=100),
    "数码短版": dict(gripper=3.0, tail=3.0, move=.5, waste=1.0, ready=5),
}


@dataclass(frozen=True)
class ProductionEstimate:
    quantity: int
    copies_per_sheet: int
    net_sheets: int
    waste_sheets: int
    make_ready_sheets: int
    total_sheets: int
    batches: int
    runtime_minutes: float
    paper_weight_kg: float
    warnings: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


def estimate_production(*, quantity, copies_per_sheet, speed_sph, waste_percent,
                        make_ready_sheets, batch_size, sheet_width_mm,
                        sheet_height_mm, paper_gsm, machine_width_mm,
                        machine_height_mm):
    quantity, copies = max(0, int(quantity)), max(1, int(copies_per_sheet))
    speed, batch = max(1.0, float(speed_sph)), max(1, int(batch_size))
    net = ceil(quantity / copies) if quantity else 0
    waste = ceil(net * max(0.0, float(waste_percent)) / 100.0) if net else 0
    ready = max(0, int(make_ready_sheets)); total = net + waste + ready
    batches = ceil(quantity / batch) if quantity else 0
    runtime = total / speed * 60.0
    paper_kg = total * float(sheet_width_mm) * float(sheet_height_mm) / 1_000_000.0 * float(paper_gsm) / 1000.0
    fits = ((sheet_width_mm <= machine_width_mm and sheet_height_mm <= machine_height_mm) or
            (sheet_height_mm <= machine_width_mm and sheet_width_mm <= machine_height_mm))
    warnings = () if fits else (f"纸张 {sheet_width_mm:g}×{sheet_height_mm:g} mm 超出设备上限 {machine_width_mm:g}×{machine_height_mm:g} mm",)
    return ProductionEstimate(quantity, copies, net, waste, ready, total, batches,
                              round(runtime, 2), round(paper_kg, 3), warnings)


def _dspin(value, maximum=100.0, suffix=" mm"):
    w = QDoubleSpinBox(); w.setRange(0, maximum); w.setDecimals(1); w.setValue(value); w.setSuffix(suffix); w.setFixedWidth(92)
    return w


class ProductionControlBar(QFrame):
    apply_requested = Signal(dict)
    simulate_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("ProductionControlBar"); self.setMinimumWidth(1720)
        self.mode_name = "单页拼版"; self.sheet_width_mm = 450.0; self.sheet_height_mm = 320.0; self.copies_per_sheet = 1
        root = QVBoxLayout(self); root.setContentsMargins(10, 6, 10, 6); root.setSpacing(5)
        top = QHBoxLayout(); top.setSpacing(7)
        self.mode = QLabel("单页拼版"); self.mode.setObjectName("ProductionModeBadge"); top.addWidget(self.mode)
        self.paper = QComboBox()
        for name, gsm in PAPERS: self.paper.addItem(name, gsm)
        self.paper.setCurrentIndex(0); top.addWidget(QLabel("纸张")); top.addWidget(self.paper)
        self.quantity = QSpinBox(); self.quantity.setRange(1, 100_000_000); self.quantity.setValue(10000); self.quantity.setFixedWidth(102)
        top.addWidget(QLabel("印数")); top.addWidget(self.quantity)
        self.machine = QComboBox()
        for name, width, height, speed in MACHINES: self.machine.addItem(name, (width, height, speed))
        top.addWidget(QLabel("设备")); top.addWidget(self.machine)
        self.gripper = _dspin(10, 80); top.addWidget(QLabel("咬口")); top.addWidget(self.gripper)
        self.tail = _dspin(3, 80); top.addWidget(QLabel("底边")); top.addWidget(self.tail)
        self.template = QComboBox(); self.template.addItems(TEMPLATES.keys()); top.addWidget(QLabel("模板")); top.addWidget(self.template)
        self.move_step = _dspin(1, 50); top.addWidget(QLabel("移动")); top.addWidget(self.move_step)
        top.addStretch(); root.addLayout(top)

        bottom = QHBoxLayout(); bottom.setSpacing(7)
        self.simulation = QCheckBox("模拟机"); self.simulation.setChecked(True); bottom.addWidget(self.simulation)
        self.batch_size = QSpinBox(); self.batch_size.setRange(1, 10_000_000); self.batch_size.setValue(25); self.batch_size.setFixedWidth(92)
        bottom.addWidget(QLabel("排序/批次")); bottom.addWidget(self.batch_size)
        self.speed = QSpinBox(); self.speed.setRange(1, 100_000); self.speed.setValue(MACHINES[0][3]); self.speed.setSuffix(" 张/时"); self.speed.setFixedWidth(122)
        bottom.addWidget(QLabel("速度")); bottom.addWidget(self.speed)
        self.waste = _dspin(3, 50, "%"); bottom.addWidget(QLabel("放数")); bottom.addWidget(self.waste)
        self.make_ready = QSpinBox(); self.make_ready.setRange(0, 100000); self.make_ready.setValue(50); self.make_ready.setFixedWidth(82)
        bottom.addWidget(QLabel("调机纸")); bottom.addWidget(self.make_ready)
        apply_btn = QPushButton("应用参数"); apply_btn.setObjectName("ProductionSecondary"); apply_btn.clicked.connect(self.apply_parameters); bottom.addWidget(apply_btn)
        simulate_btn = QPushButton("生产模拟"); simulate_btn.setObjectName("ProductionPrimary"); simulate_btn.clicked.connect(self.simulate_requested.emit); bottom.addWidget(simulate_btn)
        export_btn = QPushButton("导出工单"); export_btn.setObjectName("ProductionSecondary"); export_btn.clicked.connect(self.export_work_order); bottom.addWidget(export_btn)
        self.result = QLabel("等待生产模拟"); self.result.setObjectName("ProductionEstimate"); bottom.addWidget(self.result, 1)
        root.addLayout(bottom)
        self.template.currentTextChanged.connect(self.apply_template)
        self.machine.currentIndexChanged.connect(self._machine_changed)

    def _machine_changed(self, _=None):
        self.speed.setValue(int(self.machine.currentData()[2]))

    def apply_template(self, name):
        preset = TEMPLATES.get(name)
        if not preset: return
        self.gripper.setValue(preset["gripper"]); self.tail.setValue(preset["tail"]); self.move_step.setValue(preset["move"])
        self.waste.setValue(preset["waste"]); self.make_ready.setValue(preset["ready"])

    def set_context(self, mode_name, sheet_width_mm, sheet_height_mm, copies_per_sheet):
        self.mode_name = str(mode_name); self.mode.setText(self.mode_name)
        self.sheet_width_mm, self.sheet_height_mm = float(sheet_width_mm), float(sheet_height_mm)
        self.copies_per_sheet = max(1, int(copies_per_sheet))

    def parameters(self):
        machine_w, machine_h, _ = self.machine.currentData()
        return {
            "mode": self.mode_name, "paper": self.paper.currentText(), "paper_gsm": int(self.paper.currentData()),
            "quantity": self.quantity.value(), "machine": self.machine.currentText(),
            "machine_width_mm": machine_w, "machine_height_mm": machine_h,
            "gripper_mm": self.gripper.value(), "tail_margin_mm": self.tail.value(),
            "template": self.template.currentText(), "move_step_mm": self.move_step.value(),
            "simulation": self.simulation.isChecked(), "batch_size": self.batch_size.value(),
            "speed_sph": self.speed.value(), "waste_percent": self.waste.value(),
            "make_ready_sheets": self.make_ready.value(), "sheet_width_mm": self.sheet_width_mm,
            "sheet_height_mm": self.sheet_height_mm, "copies_per_sheet": self.copies_per_sheet,
        }

    def apply_parameters(self):
        self.apply_requested.emit(self.parameters())

    def calculate(self):
        p = self.parameters()
        result = estimate_production(quantity=p["quantity"], copies_per_sheet=p["copies_per_sheet"], speed_sph=p["speed_sph"],
            waste_percent=p["waste_percent"], make_ready_sheets=p["make_ready_sheets"], batch_size=p["batch_size"],
            sheet_width_mm=p["sheet_width_mm"], sheet_height_mm=p["sheet_height_mm"], paper_gsm=p["paper_gsm"],
            machine_width_mm=p["machine_width_mm"], machine_height_mm=p["machine_height_mm"])
        warning = " · ⚠ " + result.warnings[0] if result.warnings else " · ✓ 设备适配"
        self.result.setText(f"{result.copies_per_sheet}版/张 · 净纸 {result.net_sheets} · 总纸 {result.total_sheets} · {result.batches}批 · {result.paper_weight_kg:.1f}kg · {result.runtime_minutes:.1f}分钟{warning}")
        self.result.setProperty("warning", bool(result.warnings)); self.result.style().unpolish(self.result); self.result.style().polish(self.result)
        return result

    def export_work_order(self):
        result = self.calculate(); path, _ = QFileDialog.getSaveFileName(self, "导出生产工单", "生产工单.json", "JSON (*.json)")
        if not path: return
        if not path.lower().endswith(".json"): path += ".json"
        payload = {"created_at": datetime.now().isoformat(timespec="seconds"), "parameters": self.parameters(), "estimate": result.to_dict()}
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        QMessageBox.information(self, "生产工单", f"工单已导出：\n{path}")
