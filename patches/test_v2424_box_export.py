import tempfile
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from box_export import MM_TO_PT, export_box_pdf
from nesting import NestItem, NestPlacement, NestPlan, nest_polygons_multi_sheet


with tempfile.TemporaryDirectory(prefix="v2424-box-") as td:
    root = Path(td)
    source = root / "box-art.pdf"
    output = root / "box-imposed.pdf"
    c = canvas.Canvas(str(source), pagesize=(100 * MM_TO_PT, 60 * MM_TO_PT))
    c.setFont("Helvetica", 18)
    c.drawCentredString(50 * MM_TO_PT, 30 * MM_TO_PT, "BOX-ART")
    c.rect(0, 0, 100 * MM_TO_PT, 60 * MM_TO_PT)
    c.save()
    contour = [(0, 0), (100, 0), (100, 60), (0, 60)]
    item = NestItem("box", contour, 5, (0,))
    plan = nest_polygons_multi_sheet([item], 220, 140, 8, 2)
    assert plan.sheet_count == 2 and len(plan.placements) == 5
    result = export_box_pdf(
        source, contour, plan, output,
        sheet_width_mm=220, sheet_height_mm=140,
        bleed_mm=3, spot_name="CutContour",
    )
    reader = PdfReader(str(output))
    assert result["sheet_count"] == 2 and result["placement_count"] == 5
    assert result["vector_artwork"] is True and result["spot_name"] == "CutContour"
    assert len(reader.pages) == 2
    assert abs(float(reader.pages[0].mediabox.width) - 220 * MM_TO_PT) < .01
    all_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert all_text.count("BOX-ART") == 5
    payload = output.read_bytes()
    assert b"/Separation" in payload and b"CutContour" in payload
    assert output.stat().st_size > source.stat().st_size

    rotated_output = root / "box-rotated.pdf"
    rotated_plan = NestPlan([
        NestPlacement("box", 0, 0, 0, 90, 1),
        NestPlacement("box", 1, 70, 0, 270, 1),
    ], 1, [.39])
    rotated = export_box_pdf(
        source, contour, rotated_plan, rotated_output,
        sheet_width_mm=140, sheet_height_mm=110,
        bleed_mm=0, spot_name="刀线专色",
    )
    assert rotated["spot_name"] == "刀线专色"
    assert "\n".join(page.extract_text() or "" for page in PdfReader(str(rotated_output)).pages).count("BOX-ART") == 2

    vector_source = root / "box-contour.json"
    vector_source.write_text("{}", encoding="utf-8")
    vector_output = root / "box-contour-only.pdf"
    vector = export_box_pdf(
        vector_source, contour, rotated_plan, vector_output,
        sheet_width_mm=140, sheet_height_mm=110,
        bleed_mm=3, spot_name="CutContour",
    )
    assert vector["vector_artwork"] is False
    assert b"/Separation" in vector_output.read_bytes()
print("V2.4.24 BOX COMPOSITE PRODUCTION PDF PASS")
