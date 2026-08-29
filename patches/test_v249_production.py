from production_planner import ProductionPlanInput, calculate_production_plan, calculate_multi_product

r = calculate_production_plan(ProductionPlanInput(
    order_quantity=1000, pieces_per_sheet=8, spoilage_rate_percent=2.0,
    make_ready_sheets=10, paper_cost_per_sheet=0.8, print_cost_per_sheet=0.5,
))
assert r.theoretical_sheets == 125
assert r.spoilage_sheets == 3
assert r.production_sheets == 138
assert r.produced_pieces == 1104
assert r.surplus_pieces == 104
assert abs(r.paper_cost - 110.4) < 1e-9
assert abs(r.print_cost - 69.0) < 1e-9
assert abs(r.total_cost - 179.4) < 1e-9

m = calculate_multi_product(
    {'A': 1000, 'B': 500}, {'A': 8, 'B': 4},
    spoilage_rate_percent=2.0, make_ready_sheets=5,
    paper_cost_per_sheet=1.0, print_cost_per_sheet=0.5,
)
assert m['theoretical_sheets'] == 125
assert m['spoilage_sheets'] == 3
assert m['production_sheets'] == 133
assert m['per_product']['A']['produced_pieces'] == 1064
assert m['per_product']['B']['produced_pieces'] == 532
assert m['total_cost'] == 199.5

try:
    calculate_production_plan(ProductionPlanInput(order_quantity=10, pieces_per_sheet=0))
except ValueError:
    pass
else:
    raise AssertionError('zero n-up must fail')

print('V2.4.9 production planner tests passed')
