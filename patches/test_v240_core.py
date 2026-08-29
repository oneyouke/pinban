from v240_core import SheetSpec, ProductSpec, calculate_fit, recommend_orientation, calculate_production_plan, to_mm, from_mm


def main():
    assert abs(to_mm(1, 'in') - 25.4) < 1e-9
    assert abs(from_mm(25.4, 'in') - 1) < 1e-9

    sheet = SheetSpec(450, 320, margin_left_mm=10, margin_right_mm=10, margin_top_mm=10, margin_bottom_mm=10, gripper_mm=12, gripper_edge='bottom')
    product = ProductSpec(90, 54, bleed_mm=3, gap_x_mm=4, gap_y_mm=4)
    normal = calculate_fit(sheet, product)
    assert normal.cols == 4 and normal.rows == 4 and normal.count == 16, normal
    assert normal.fits

    recommendation = recommend_orientation(sheet, product)
    assert recommendation['normal']['count'] == 16
    assert recommendation['rotated']['count'] >= 0
    assert recommendation['recommended'] in ('normal', 'rotated')

    # Gripper is deducted from the selected edge only.
    vertical_gripper = SheetSpec(450, 320, margin_left_mm=10, margin_right_mm=10, margin_top_mm=10, margin_bottom_mm=10, gripper_mm=50, gripper_edge='left')
    result = calculate_fit(vertical_gripper, product)
    assert result.usable_width_mm == 380.0
    assert result.usable_height_mm == 300.0

    # Product too large => hard no-fit result instead of a negative grid.
    too_big = calculate_fit(sheet, ProductSpec(1000, 1000, bleed_mm=3))
    assert too_big.count == 0 and too_big.fits is False

    plan = calculate_production_plan(1000, 16, make_ready_sheets=20, waste_rate_percent=3)
    assert plan.base_sheets == 63
    assert plan.waste_sheets == 2
    assert plan.total_sheets == 85
    assert plan.gross_products == 1360
    assert plan.surplus_products == 360

    print('V2.4 CORE PASS')
    print(recommendation)
    print(plan.to_dict())


if __name__ == '__main__':
    main()
