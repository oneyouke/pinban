import os, tempfile
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from booklet_export import export_booklet_pdf
from box_export import export_box_pdf
from nesting import NestPlan, NestPlacement
from production_modes import BookImpositionWidget, BoxImpositionWidget

app = QApplication.instance() or QApplication([])
book_ui=BookImpositionWidget(); box_ui=BoxImpositionWidget()
assert book_ui.color_bar.isChecked() and box_ui.color_bar.isChecked()

with tempfile.TemporaryDirectory(prefix="v2437-colorbar-") as td:
    root=Path(td); source=root/"book.pdf"; c=canvas.Canvas(str(source),pagesize=(200,300))
    for i in range(4): c.drawString(50,150,f"PAGE {i+1}"); c.showPage()
    c.save()
    book_out=root/"book-output.pdf"
    book=export_booklet_pdf(source,book_out,draw_color_bar=True)
    assert book["color_bar"] is True and len(PdfReader(str(book_out)).pages)==2

    die=root/"die.svg"; die.write_text('<svg xmlns="http://www.w3.org/2000/svg"><polygon points="0,0 80,0 80,50 0,50"/></svg>',encoding="utf-8")
    plan=NestPlan([NestPlacement("box",0,10,10,0,1)],1,[.25]); box_out=root/"box-output.pdf"
    box=export_box_pdf(die,[(0,0),(80,0),(80,50),(0,50)],plan,box_out,sheet_width_mm=200,sheet_height_mm=150,draw_color_bar=True)
    assert box["color_bar"] is True and len(PdfReader(str(box_out)).pages)==1

book_ui.deleteLater(); box_ui.deleteLater(); app.processEvents()
print("V2.4.37 PDF COLOR BARS PASS")
