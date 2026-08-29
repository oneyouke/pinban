from pathlib import Path
import tempfile

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from production_gate import run_enhanced_gate, extract_trim_boxes_mm, apply_vector_marks

class Job:
    def __init__(self, path): self.path = path

class Settings:
    sheet_width_mm = 320
    sheet_height_mm = 450
    print_marks = {'crop_marks': True, 'register_marks': True, 'color_bar': True, 'gripper_arrow': True}

summary = {'placements': [{'x_mm': 20, 'y_mm': 30, 'width_mm': 100, 'height_mm': 60}]}
assert extract_trim_boxes_mm(summary) == [(20.0,30.0,100.0,60.0)]

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    src = root / 'gate_source.pdf'
    c = canvas.Canvas(str(src), pagesize=A4)
    c.drawString(72, 720, 'V2.4.5 gate test')
    c.showPage(); c.save()

    gate = run_enhanced_gate([Job(src)])
    assert 'reports' in gate and isinstance(gate['blocking'], list)

    # The reportlab built-in font may be reported as unembedded; verify gate faithfully surfaces it.
    assert gate['ok'] == (len(gate['blocking']) == 0)

    out = root / 'marked.pdf'
    out.write_bytes(src.read_bytes())
    result = apply_vector_marks(out, Settings(), [Job(src)], summary, plate_no='A01')
    assert result['applied'] and result['trim_boxes'] == 1

    import fitz
    doc = fitz.open(out)
    assert len(doc) == 1
    assert doc[0].get_drawings(), 'production vector marks were not written'
    doc.close()

print('V2.4.5 production gate tests passed')
