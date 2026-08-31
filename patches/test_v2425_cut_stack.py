import tempfile
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from cut_stack import MM_TO_PT, export_cut_stack_pdf, plan_cut_stack, reconstruct_cut_sequence


def sample(path, pages):
    c = canvas.Canvas(str(path), pagesize=(90 * MM_TO_PT, 54 * MM_TO_PT))
    for page in range(1, pages + 1):
        c.setFont("Helvetica", 20); c.drawString(30, 70, f"PAGE-{page}"); c.showPage()
    c.save()


with tempfile.TemporaryDirectory(prefix="v2425-cut-stack-") as td:
    root = Path(td); source = root / "sequence.pdf"; sample(source, 19)
    simplex_output = root / "simplex-cut-stack.pdf"
    simplex = export_cut_stack_pdf(
        source, simplex_output, sheet_width_mm=210, sheet_height_mm=120,
        trim_width_mm=90, trim_height_mm=54, rows=2, columns=2,
        gap_x_mm=5, gap_y_mm=4, duplex=False, stack_order="row_major",
    )
    assert simplex["capacity"] == 4 and simplex["sheet_count"] == 5
    assert simplex["output_pages"] == 5 and simplex["blank_pages"] == 1
    reader = PdfReader(str(simplex_output)); assert len(reader.pages) == 5
    first = reader.pages[0].extract_text() or ""
    assert all(f"PAGE-{n}" in first for n in (1, 6, 11, 16))
    all_text = "\n".join(p.extract_text() or "" for p in reader.pages)
    for n in range(1, 20): assert all_text.count(f"PAGE-{n}\n") == 1

    duplex_plan = plan_cut_stack(
        15, sheet_width_mm=210, sheet_height_mm=70,
        trim_width_mm=90, trim_height_mm=54, rows=1, columns=2,
        gap_x_mm=5, gap_y_mm=0, duplex=True, flip="long_edge", stack_order="column_major",
    )
    assert reconstruct_cut_sequence(duplex_plan) == list(range(1, 16)) + [None]
    duplex_source = root / "duplex-sequence.pdf"; sample(duplex_source, 15)
    duplex_output = root / "duplex-cut-stack.pdf"
    duplex = export_cut_stack_pdf(
        duplex_source, duplex_output, sheet_width_mm=210, sheet_height_mm=70,
        trim_width_mm=90, trim_height_mm=54, rows=1, columns=2,
        gap_x_mm=5, gap_y_mm=0, duplex=True, flip="long_edge", stack_order="column_major",
    )
    duplex_reader = PdfReader(str(duplex_output))
    assert duplex["sheet_count"] == 4 and duplex["output_pages"] == 8
    assert all(f"PAGE-{n}" in (duplex_reader.pages[0].extract_text() or "") for n in (1, 9))
    assert all(f"PAGE-{n}" in (duplex_reader.pages[1].extract_text() or "") for n in (2, 10))
    duplex_text = "\n".join(p.extract_text() or "" for p in duplex_reader.pages)
    for n in range(1, 16): assert duplex_text.count(f"PAGE-{n}\n") == 1

    short_plan = plan_cut_stack(
        8, sheet_width_mm=210, sheet_height_mm=70,
        trim_width_mm=90, trim_height_mm=54, rows=1, columns=2,
        gap_x_mm=5, duplex=True, flip="short_edge",
    )
    assert reconstruct_cut_sequence(short_plan) == list(range(1, 9))
print("V2.4.25 CUT & STACK PRODUCTION PDF PASS")
