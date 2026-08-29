from __future__ import annotations

from dataclasses import dataclass, asdict
from math import ceil


@dataclass(frozen=True)
class ProductionPlanInput:
    order_quantity: int
    pieces_per_sheet: int
    spoilage_rate_percent: float = 0.0
    make_ready_sheets: int = 0
    paper_cost_per_sheet: float = 0.0
    print_cost_per_sheet: float = 0.0


@dataclass
class ProductionPlanResult:
    theoretical_sheets: int
    spoilage_sheets: int
    make_ready_sheets: int
    production_sheets: int
    produced_pieces: int
    surplus_pieces: int
    paper_cost: float
    print_cost: float
    total_cost: float
    cost_per_order_piece: float

    def to_dict(self):
        return asdict(self)


def calculate_production_plan(data: ProductionPlanInput) -> ProductionPlanResult:
    qty = max(0, int(data.order_quantity))
    nup = max(0, int(data.pieces_per_sheet))
    if qty > 0 and nup <= 0:
        raise ValueError('每版数量必须大于 0')
    if data.spoilage_rate_percent < 0:
        raise ValueError('废品率不能小于 0')
    if data.make_ready_sheets < 0:
        raise ValueError('放数不能小于 0')
    if data.paper_cost_per_sheet < 0 or data.print_cost_per_sheet < 0:
        raise ValueError('成本不能小于 0')

    theoretical = ceil(qty / nup) if qty and nup else 0
    spoilage = ceil(theoretical * float(data.spoilage_rate_percent) / 100.0) if theoretical else 0
    make_ready = int(data.make_ready_sheets)
    production = theoretical + spoilage + make_ready
    produced = production * nup
    surplus = max(0, produced - qty)
    paper_cost = production * float(data.paper_cost_per_sheet)
    print_cost = production * float(data.print_cost_per_sheet)
    total = paper_cost + print_cost
    cpp = total / qty if qty else 0.0
    return ProductionPlanResult(
        theoretical_sheets=theoretical,
        spoilage_sheets=spoilage,
        make_ready_sheets=make_ready,
        production_sheets=production,
        produced_pieces=produced,
        surplus_pieces=surplus,
        paper_cost=paper_cost,
        print_cost=print_cost,
        total_cost=total,
        cost_per_order_piece=cpp,
    )


def calculate_multi_product(order_quantities: dict[str, int], packed_per_sheet: dict[str, int],
                            spoilage_rate_percent: float = 0.0, make_ready_sheets: int = 0,
                            paper_cost_per_sheet: float = 0.0, print_cost_per_sheet: float = 0.0):
    if not order_quantities:
        return {'production_sheets': 0, 'per_product': {}, 'total_cost': 0.0}
    required = 0
    per_product = {}
    for key, qty in order_quantities.items():
        nup = int(packed_per_sheet.get(key, 0) or 0)
        if int(qty) > 0 and nup <= 0:
            raise ValueError(f'{key} 在当前大版没有版位')
        sheets = ceil(max(0, int(qty)) / nup) if nup else 0
        required = max(required, sheets)
        per_product[key] = {'order_quantity': int(qty), 'pieces_per_sheet': nup, 'theoretical_sheets': sheets}
    spoilage = ceil(required * max(0.0, float(spoilage_rate_percent)) / 100.0) if required else 0
    production = required + spoilage + max(0, int(make_ready_sheets))
    for key, row in per_product.items():
        produced = production * row['pieces_per_sheet']
        row['produced_pieces'] = produced
        row['surplus_pieces'] = max(0, produced - row['order_quantity'])
    total = production * (max(0.0, float(paper_cost_per_sheet)) + max(0.0, float(print_cost_per_sheet)))
    return {
        'theoretical_sheets': required,
        'spoilage_sheets': spoilage,
        'make_ready_sheets': max(0, int(make_ready_sheets)),
        'production_sheets': production,
        'per_product': per_product,
        'paper_cost': production * max(0.0, float(paper_cost_per_sheet)),
        'print_cost': production * max(0.0, float(print_cost_per_sheet)),
        'total_cost': total,
    }
