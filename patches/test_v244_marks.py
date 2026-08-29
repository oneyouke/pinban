from pathlib import Path
import tempfile

from print_marks import MarkConfig, JobMarkInfo, crop_segments, registration_centers, color_bar_rects, info_lines, gripper_arrow, draw_on_fitz_page, mm

cfg = MarkConfig()
segments = crop_segments(20, 30, 100, 60, cfg)
assert len(segments) == 8
for a, b in segments:
    assert a != b

regs = registration_centers(650, 450, cfg)
assert len(regs) == 4
assert all(0 <= x <= 650 and 0 <= y <= 450 for x, y in regs)

bars = color_bar_rects(650, 450, cfg)
assert [b[-1] for b in bars] == ['C','M','Y','K']

lines = info_lines(JobMarkInfo(file_name='job.pdf', plate_no='A01', side='back', date_text='2026-08-29'), cfg)
assert 'job.pdf' in lines
assert 'PLATE A01' in lines
assert 'BACK' in lines
assert '2026-08-29' in lines

for edge in ('top','bottom','left','right'):
    c = MarkConfig(gripper_edge=edge)
    pts = gripper_arrow(650,450,c)
    assert len(pts) == 3

# Verify vector PDF drawing path when PyMuPDF is installed.
try:
    import fitz
except Exception:
    fitz = None

if fitz is not None:
    doc = fitz.open()
    page = doc.new_page(width=mm(650), height=mm(450))
    draw_on_fitz_page(page, 650, 450, [(20,30,100,60)], cfg, JobMarkInfo(file_name='job.pdf', plate_no='A01', side='FRONT', date_text='2026-08-29'))
    drawings = page.get_drawings()
    assert drawings, 'vector mark drawings missing'
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'marks.pdf'
        doc.save(out)
        assert out.stat().st_size > 0
    doc.close()

print('V2.4.4 print marks tests passed')
