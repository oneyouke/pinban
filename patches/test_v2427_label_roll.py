import tempfile
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from label_roll import MM_TO_PT, export_label_roll_pdf, plan_label_roll


with tempfile.TemporaryDirectory(prefix="v2427-label-roll-") as td:
    root = Path(td); source = root / "label.pdf"; output = root / "label-roll.pdf"
    c = canvas.Canvas(str(source), pagesize=(50*MM_TO_PT, 30*MM_TO_PT))
    c.setFont("Helvetica", 16); c.drawString(20, 40, "LABEL-ART"); c.save()
    plan = plan_label_roll(
        20, web_width_mm=160, repeat_length_mm=100,
        label_width_mm=50, label_height_mm=30, lanes=3,
        lane_gap_mm=5, repeat_gap_mm=4, direction="head_out", winding="outside",
    )
    assert plan.repeats_per_cycle == 3 and plan.capacity_per_cycle == 9
    assert plan.cycle_count == 3 and plan.blank_positions == 7
    assert [p.copy_number for p in plan.placements if p.output_page == 1] == list(range(1, 10))
    assert len(plan.slit_x_mm) == 2 and plan.cross_waste_mm == 0

    inner = plan_label_roll(
        20, web_width_mm=160, repeat_length_mm=100,
        label_width_mm=50, label_height_mm=30, lanes=3,
        lane_gap_mm=5, repeat_gap_mm=4, direction="tail_out", winding="inside",
    )
    assert inner.placements[0].repeat_cycle == 3 and inner.placements[0].copy_number == 19
    assert all(p.rotation == 180 for p in inner.placements)
    side = plan_label_roll(
        8, web_width_mm=140, repeat_length_mm=110,
        label_width_mm=50, label_height_mm=30, lanes=4,
        lane_gap_mm=5, repeat_gap_mm=5, direction="right_out", winding="outside",
    )
    assert all(p.rotation == 90 and p.width_mm == 30 and p.height_mm == 50 for p in side.placements)

    result = export_label_roll_pdf(
        source, output, quantity=20, web_width_mm=160, repeat_length_mm=100,
        label_width_mm=50, label_height_mm=30, lanes=3,
        lane_gap_mm=5, repeat_gap_mm=4, direction="head_out", winding="outside",
        draw_slit_lines=True, draw_die_lines=True,
    )
    reader = PdfReader(str(output)); assert result["output_pages"] == 3 and len(reader.pages) == 3
    all_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert all_text.count("LABEL-ART") == 20
    for number in range(1, 21): assert f"#{number}\n" in all_text
    payload = output.read_bytes(); assert b"/Separation" in payload and b"CutContour" in payload and b"SlitLine" in payload
print("V2.4.27 LABEL ROLL PRODUCTION PDF PASS")
