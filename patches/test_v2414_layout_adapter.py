from layout_adapter import normalize_workspace_placements, unique_source_pages


def ws(placements):
    return {'page_canvas': {'sheet': {'width_mm': 320, 'height_mm': 450}, 'placements': placements}}


base = {
    'path': __file__, 'page_index': 0,
    'width_pt': 72.0, 'height_pt': 144.0,
    'x_mm': 10.0, 'y_mm': 20.0, 'rotation': 0,
}

sheet, rows = normalize_workspace_placements(ws([base]), require_files=True)
assert sheet == {'width_mm': 320.0, 'height_mm': 450.0}
assert abs(rows[0].width_mm - 25.4) < 1e-9
assert abs(rows[0].height_mm - 50.8) < 1e-9
assert unique_source_pages(rows) == [(rows[0].path, 0)]

rot = dict(base); rot['rotation'] = 90; rot['x_mm'] = 260.0; rot['y_mm'] = 20.0
_, rows = normalize_workspace_placements(ws([rot]), require_files=True)
assert rows[0].rotation == 90

bad = dict(base); bad['x_mm'] = 310.0
try:
    normalize_workspace_placements(ws([bad]), require_files=True)
except ValueError as exc:
    assert '超出纸张' in str(exc)
else:
    raise AssertionError('out-of-bounds placement must fail')

bad_rot = dict(base); bad_rot['rotation'] = 45
try:
    normalize_workspace_placements(ws([bad_rot]), require_files=True)
except ValueError as exc:
    assert '0/90/180/270' in str(exc)
else:
    raise AssertionError('unsupported rotation must fail')

print('V2.4.14 LAYOUT NORMALIZATION PASS')
