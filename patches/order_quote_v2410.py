from __future__ import annotations

from dataclasses import dataclass, asdict
from math import ceil
import csv, json
from pathlib import Path


@dataclass
class OrderLine:
    key: str
    name: str
    quantity: int
    pieces_per_sheet: int


@dataclass
class QuoteResult:
    required_sheets: int
    actual_sheets: int
    total_cost: float
    markup_percent: float
    quote_total: float
    total_order_pieces: int
    quote_per_piece: float
    lines: list[dict]

    def to_dict(self):
        return asdict(self)


def calculate_order(lines: list[OrderLine], *, spoilage_percent: float = 0.0,
                    make_ready_sheets: int = 0, paper_cost_per_sheet: float = 0.0,
                    print_cost_per_sheet: float = 0.0, fixed_cost: float = 0.0,
                    markup_percent: float = 0.0) -> QuoteResult:
    clean = [x for x in lines if int(x.quantity) > 0 and int(x.pieces_per_sheet) > 0]
    required = max((ceil(int(x.quantity) / int(x.pieces_per_sheet)) for x in clean), default=0)
    spoilage = ceil(required * max(0.0, float(spoilage_percent)) / 100.0)
    actual = required + spoilage + max(0, int(make_ready_sheets))
    variable_cost = actual * (max(0.0, float(paper_cost_per_sheet)) + max(0.0, float(print_cost_per_sheet)))
    total_cost = variable_cost + max(0.0, float(fixed_cost))
    quote_total = total_cost * (1.0 + max(0.0, float(markup_percent)) / 100.0)
    total_pieces = sum(int(x.quantity) for x in clean)
    rows = []
    for x in clean:
        produced = actual * int(x.pieces_per_sheet)
        qty = int(x.quantity)
        share = qty / total_pieces if total_pieces else 0.0
        rows.append({
            'key': x.key, 'name': x.name, 'order_quantity': qty,
            'pieces_per_sheet': int(x.pieces_per_sheet), 'produced_pieces': produced,
            'surplus_pieces': max(0, produced - qty),
            'allocated_cost': total_cost * share, 'allocated_quote': quote_total * share,
            'quote_per_piece': (quote_total * share / qty) if qty else 0.0,
        })
    return QuoteResult(required, actual, total_cost, float(markup_percent), quote_total,
                       total_pieces, quote_total / total_pieces if total_pieces else 0.0, rows)


def export_quote_json(path: str | Path, result: QuoteResult):
    p = Path(path)
    p.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding='utf-8')
    return p


def export_quote_csv(path: str | Path, result: QuoteResult):
    p = Path(path)
    fields = ['key','name','order_quantity','pieces_per_sheet','produced_pieces','surplus_pieces','allocated_cost','allocated_quote','quote_per_piece']
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(result.lines)
        w.writerow({'name':'TOTAL','order_quantity':result.total_order_pieces,
                    'allocated_cost':result.total_cost,'allocated_quote':result.quote_total,
                    'quote_per_piece':result.quote_per_piece})
    return p
