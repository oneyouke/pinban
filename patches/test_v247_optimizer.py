from mix_optimizer import ProductSpec, optimize_mixed

specs = [
    ProductSpec('A', 90, 54, quantity=100),
    ProductSpec('B', 120, 80, quantity=50),
]
r = optimize_mixed(specs, 650, 450, margin_mm=10, gap_x_mm=3, gap_y_mm=3)
assert r.items, 'optimizer returned no placements'
assert r.utilization > 0
assert r.requested_ratio == {'A': 2, 'B': 1}, r.requested_ratio
assert all(0 <= i.x_mm <= 650 and 0 <= i.y_mm <= 450 for i in r.items)
assert all(i.x_mm + i.width_mm <= 650.001 and i.y_mm + i.height_mm <= 450.001 for i in r.items)
assert set(r.packed_by_key).issubset({'A','B'})
assert r.strategy

# Rotation must help or at least remain valid on a narrow sheet.
specs2 = [ProductSpec('C', 180, 90, quantity=1, allow_rotate=True)]
r2 = optimize_mixed(specs2, 120, 220, margin_mm=5, gap_x_mm=0, gap_y_mm=0)
assert r2.items, 'rotated placement should fit'
assert r2.items[0].rotation in (0, 90)

# Impossible items should not be placed outside the sheet.
r3 = optimize_mixed([ProductSpec('X', 1000, 1000, 1)], 300, 300)
assert not r3.items
assert r3.utilization == 0

print('V2.4.7 mixed optimizer tests passed', r.strategy, f'{r.utilization:.3f}', r.packed_by_key)
