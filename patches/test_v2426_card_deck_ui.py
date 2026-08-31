import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton
from professional_canvas import ProfessionalPageCanvasWidget

app = QApplication.instance() or QApplication([])
widget = ProfessionalPageCanvasWidget()
assert widget.card_rows.value() == 1 and widget.card_columns.value() == 3
assert widget.card_common_back.isChecked()
assert widget.card_front_path.isReadOnly() and widget.card_back_path.isReadOnly()
labels = {button.text() for button in widget.findChildren(QPushButton)}
assert "导出卡牌正背生产 PDF" in labels
assert callable(widget._export_card_deck_pdf)
widget.close()
print("V2.4.26 CARD DECK UI PASS")
