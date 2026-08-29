from pathlib import Path
import tempfile

from template_store import load_library, upsert_template, get_template, delete_template, export_template, import_template

workspace = {
    'schema_version': 1,
    'app_version': '2.4.11',
    'page_canvas': {'sheet': {'width_mm': 650, 'height_mm': 450}, 'placements': [{'path': '源文件.pdf', 'page_index': 0, 'x_mm': 10, 'y_mm': 20}]},
    'resources': {'papers': [{'name': '大度对开', 'width_mm': 889, 'height_mm': 597}]},
    'print_marks': {'crop_marks': True, 'gripper_edge': 'top'},
    'production': {'order_quantity': 10000, 'waste_rate_percent': 3.0},
    'order_quote': {'markup_percent': 20.0},
}

with tempfile.TemporaryDirectory(prefix='模板测试_') as td:
    root = Path(td)
    lib = root / '模板库.json'
    row = upsert_template('名片标准版', workspace, category='名片', notes='650x450', path=lib)
    assert row['name'] == '名片标准版'
    data = load_library(lib)
    assert len(data['templates']) == 1
    got = get_template('名片标准版', lib)
    assert got['workspace']['page_canvas']['sheet']['width_mm'] == 650

    # Upsert must overwrite in place rather than duplicate names.
    updated = dict(workspace)
    updated['production'] = {'order_quantity': 20000}
    upsert_template('名片标准版', updated, category='名片', notes='新版', path=lib)
    assert len(load_library(lib)['templates']) == 1
    assert get_template('名片标准版', lib)['workspace']['production']['order_quantity'] == 20000

    exported = export_template('名片标准版', root / '导出模板.json', lib)
    other_lib = root / '导入库.json'
    imported = import_template(exported, other_lib)
    assert imported['name'] == '名片标准版'
    assert get_template('名片标准版', other_lib)['workspace']['print_marks']['crop_marks'] is True

    assert delete_template('名片标准版', other_lib) is True
    assert get_template('名片标准版', other_lib) is None

print('V2.4.11 template tests passed')
