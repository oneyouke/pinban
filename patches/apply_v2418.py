from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / "legacy_dict_contract_v2418.py", root / "legacy_dict_contract.py")
shutil.copy2(patch_root / "test_v2418_legacy_dict_contract.py", root / "test_v2418_legacy_dict_contract.py")

p = root / "layout_diagnostics.py"
s = p.read_text(encoding="utf-8")
marker = "from layout_contract import ALIASES, detect_layout_item_type\n"
addition = "from legacy_dict_contract import describe_legacy_dict_contract\n"
if addition not in s:
    if marker not in s:
        raise SystemExit("V2.4.17 diagnostics import marker missing")
    s = s.replace(marker, marker + addition, 1)

old = """        report['contract']['kind'] = 'legacy_dict'
        report['reasons'].append('生产引擎已公开 layout_override: dict 入口，但 dict 键结构未被类型注解描述')
        report['reasons'].append('必须确认真实键名/坐标单位/页码与任务索引语义后才能启用生产输出')
"""
new = """        report['contract']['kind'] = 'legacy_dict'
        report['contract']['declared_schema'] = describe_legacy_dict_contract()
        report['reasons'].append('生产引擎已公开 layout_override: dict 入口；V2.4.18 已声明候选键结构，但尚未由引擎确认')
        report['reasons'].append('必须由生产引擎显式确认 schema_id、毫米坐标和零基索引后才能启用生产输出')
"""
if old not in s:
    raise SystemExit("V2.4.17 legacy dict diagnostic block missing")
s = s.replace(old, new, 1)

line = "        if contract.get('fields'):\n            lines.append('  字段：' + ', '.join(contract['fields']))\n"
extra = """        schema = contract.get('declared_schema') or {}
        if schema:
            lines.append(f"  候选 schema：{schema.get('schema_id','')}")
            lines.append(f"  坐标单位：{schema.get('coordinate_unit','')}")
            lines.append(f"  索引基准：{schema.get('index_base','')}")
            lines.append('  必需键：' + ', '.join(schema.get('required_keys') or []))
"""
if extra not in s:
    if line not in s:
        raise SystemExit("diagnostic formatting marker missing")
    s = s.replace(line, line + extra, 1)
p.write_text(s, encoding="utf-8")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    fp = root / filename
    fp.write_text(fp.read_text(encoding="utf-8").replace("2.4.17", "2.4.18"), encoding="utf-8")

for filename in ("legacy_dict_contract.py", "layout_diagnostics.py", "test_v2418_legacy_dict_contract.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")

(root / "V2418_LEGACY_DICT_SCHEMA.md").write_text(
    "# V2.4.18 Explicit Legacy Dict Schema\n\n"
    "- Declares schema desktop-imposer.layout-override.v1.\n"
    "- Uses millimetre coordinates and zero-based page/job indexes.\n"
    "- Validates required keys and rotation values before any future engine submission.\n"
    "- Exposes the candidate schema in diagnostics.\n"
    "- Remains fail-closed until the production engine explicitly confirms this schema.\n",
    encoding="utf-8",
)
print("V2.4.18 explicit legacy dict schema integrated")
