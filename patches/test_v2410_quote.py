from pathlib import Path
import tempfile

from order_quote import OrderLine, calculate_order, export_quote_csv, export_quote_json

lines=[OrderLine('A','A款',1000,4),OrderLine('B','B款',500,2)]
r=calculate_order(lines,spoilage_percent=2,make_ready_sheets=10,paper_cost_per_sheet=0.8,print_cost_per_sheet=0.5,fixed_cost=50,markup_percent=20)
assert r.required_sheets == 250
assert r.actual_sheets == 265
assert r.total_order_pieces == 1500
assert r.quote_total > r.total_cost > 0
by={x['key']:x for x in r.lines}
assert by['A']['produced_pieces']==1060
assert by['A']['surplus_pieces']==60
assert by['B']['produced_pieces']==530
assert by['B']['surplus_pieces']==30
assert abs(sum(x['allocated_cost'] for x in r.lines)-r.total_cost) < 1e-6
with tempfile.TemporaryDirectory(prefix='报价测试_') as td:
    td=Path(td)
    c=export_quote_csv(td/'报价.csv',r); j=export_quote_json(td/'报价.json',r)
    assert c.exists() and c.stat().st_size > 0
    assert j.exists() and 'quote_total' in j.read_text(encoding='utf-8')
print('V2.4.10 quote tests passed')
