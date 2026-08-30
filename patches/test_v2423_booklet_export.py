import tempfile
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from booklet_export import export_booklet_pdf, MM_TO_PT

with tempfile.TemporaryDirectory(prefix="v2423-booklet-") as td:
    root=Path(td); source=root/"book.pdf"; output=root/"book-imposed.pdf"
    c=canvas.Canvas(str(source),pagesize=(148*MM_TO_PT,210*MM_TO_PT))
    for page in range(1,15): c.setFont("Helvetica",24); c.drawString(40,100,f"PAGE-{page}"); c.showPage()
    c.save()
    result=export_booklet_pdf(source,output,binding="骑马订",sheet_width_mm=450,sheet_height_mm=320,creep_per_sheet_mm=.15,flip="长边翻",draw_fold_lines=True)
    reader=PdfReader(str(output))
    assert result["source_pages"]==14 and result["physical_sheets"]==4 and result["output_pages"]==8
    assert len(reader.pages)==8
    assert abs(float(reader.pages[0].mediabox.width)-450*MM_TO_PT)<.01
    assert "PAGE-1" in (reader.pages[0].extract_text() or "")
    assert "PAGE-2" in (reader.pages[1].extract_text() or "")
    all_text="\n".join(page.extract_text() or "" for page in reader.pages)
    for number in range(1,15): assert f"PAGE-{number}" in all_text
    assert output.stat().st_size>source.stat().st_size

    sections_output=root/"book-sections-imposed.pdf"
    sections=export_booklet_pdf(
        source,sections_output,binding="胶装 / 锁线分帖",signature_pages=8,
        sheet_width_mm=450,sheet_height_mm=320,spine_mm=4,
        creep_per_sheet_mm=.1,flip="短边翻",draw_fold_lines=False,
    )
    sections_reader=PdfReader(str(sections_output))
    assert sections["signature_count"]==2 and sections["physical_sheets"]==4
    assert sections["output_pages"]==8 and len(sections_reader.pages)==8
    assert sections_reader.pages[1].rotation==180
    assert "PAGE-1" in "\n".join(page.extract_text() or "" for page in sections_reader.pages)
print("V2.4.23 BOOKLET PRODUCTION PDF PASS")
