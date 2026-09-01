import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from production_control import ProductionControlBar, estimate_production
from production_modes import ProductionModeWorkspace

r = estimate_production(quantity=10000, copies_per_sheet=8, speed_sph=10000,
    waste_percent=3, make_ready_sheets=50, batch_size=25, sheet_width_mm=596,
    sheet_height_mm=444, paper_gsm=105, machine_width_mm=745, machine_height_mm=605)
assert r.net_sheets == 1250 and r.waste_sheets == 38 and r.total_sheets == 1338
assert r.batches == 400 and not r.warnings and r.paper_weight_kg > 0
bad = estimate_production(quantity=1, copies_per_sheet=1, speed_sph=1, waste_percent=0,
    make_ready_sheets=0, batch_size=1, sheet_width_mm=1200, sheet_height_mm=900,
    paper_gsm=100, machine_width_mm=745, machine_height_mm=605)
assert bad.warnings

app = QApplication.instance() or QApplication([])
bar = ProductionControlBar(); assert bar.quantity.value() == 10000 and bar.simulation.isChecked()
bar.set_context("盒型拼版", 596, 444, 8); result = bar.calculate()
assert result.copies_per_sheet == 8 and "总纸" in bar.result.text()
workspace = ProductionModeWorkspace(); assert hasattr(workspace, "production_bar")
workspace._set_mode(1); workspace._simulate_production(); assert workspace.production_bar.mode_name == "书籍拼版"
workspace.deleteLater(); bar.deleteLater(); app.processEvents()
print("V2.4.38 PRODUCTION CONTROL PASS")
