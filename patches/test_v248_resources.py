from mix_optimizer import ProductSpec
from resource_matcher import PaperSpec, PressSpec, compare_resources, best_resource_match

specs = [ProductSpec('A', 90, 50, 100, True), ProductSpec('B', 60, 40, 50, True)]
papers = [PaperSpec('small', 320, 450), PaperSpec('large', 520, 760)]
presses = [PressSpec('digital', 330, 488, 3), PressSpec('offset', 530, 770, 8)]
rows = compare_resources(specs, papers, presses, margin_mm=5, gap_x_mm=2, gap_y_mm=2)
assert rows, 'no resource candidates'
assert all(r.sheets_required > 0 for r in rows)
assert all(r.total_paper_area_mm2 > 0 for r in rows)
assert all(r.packed_by_key.get('A', 0) > 0 and r.packed_by_key.get('B', 0) > 0 for r in rows)
# Unsupported paper/press combinations must be filtered.
assert not any(r.paper.name == 'large' and r.press.name == 'digital' for r in rows)
best = best_resource_match(specs, papers, presses, margin_mm=5, gap_x_mm=2, gap_y_mm=2)
assert best is not None
assert best.total_paper_area_mm2 == min(r.total_paper_area_mm2 for r in rows)
# Rotated sheet orientation is allowed when compatible.
assert all(r.sheet_width_mm > 0 and r.sheet_height_mm > 0 for r in rows)
print('V2.4.8 resource matcher tests passed', best.paper.name, best.press.name, best.sheets_required)
