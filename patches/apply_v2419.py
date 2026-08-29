from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent

for src, dst in (
    ("legacy_layout_bridge_v2419.py", "legacy_layout_bridge.py"),
    ("batch_executor_v2419.py", "batch_executor.py"),
    ("test_v2419_legacy_layout_bridge.py", "test_v2419_legacy_layout_bridge.py"),
):
    shutil.copy2(patch_root / src, root / dst)

p = root / "layout_diagnostics.py"
s = p.read_text(encoding="utf-8")
marker = "from legacy_dict_contract import describe_legacy_dict_contract\n"
addition = "from legacy_layout_bridge import verify_legacy_engine_contract, LegacyLayoutBridgeError\n"
if addition not in s:
    if marker not in s:
        raise SystemExit("V2.4.18 diagnostics import marker missing")
    s = s.replace(marker, marker + addition, 1)

old = """        report['contract']['kind'] = 'legacy_dict'
        report['contract']['declared_schema'] = describe_legacy_dict_contract()
        report['reasons'].append('生产引擎已公开 layout_override: dict 入口；V2.4.18 已声明候选键结构，但尚未由引擎确认')
        report['reasons'].append('必须由生产引擎显式确认 schema_id、毫米坐标和零基索引后才能启用生产输出')
        return report
"""
new = """        report['contract']['kind'] = 'legacy_dict'
        try:
            verified = verify_legacy_engine_contract(impose_jobs, atomic_export)
        except LegacyLayoutBridgeError as exc:
            report['contract']['declared_schema'] = describe_legacy_dict_contract()
            report['reasons'].append('旧式 dict 引擎契约核验失败：' + str(exc))
            return report
        report['status'] = 'READY'
        report['contract']['kind'] = 'verified_legacy_dict'
        report['contract']['verified_schema'] = verified
        report['reasons'].append('已从生产引擎实现核验 sheets/job_index/unit_index/毫米坐标/版位尺寸契约')
        return report
"""
if old not in s:
    raise SystemExit("V2.4.18 legacy diagnostic block missing")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    fp = root / filename
    fp.write_text(fp.read_text(encoding="utf-8").replace("2.4.18", "2.4.19"), encoding="utf-8")

for filename in ("legacy_layout_bridge.py", "batch_executor.py", "layout_diagnostics.py", "test_v2419_legacy_layout_bridge.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")

(root / "V2419_VERIFIED_MANUAL_LAYOUT.md").write_text(
    "# V2.4.19 Verified Manual Layout Production\n\n"
    "- Verifies the real legacy engine contract at runtime before output.\n"
    "- Bridges workspace placements to sheets/job_index/unit_index/footprint fields.\n"
    "- Uses millimetres, zero-based indexes and rotation-aware footprint dimensions.\n"
    "- Fixes batch source-job construction so page indexes are not mistaken for quantities.\n"
    "- Keeps all invalid, incomplete, duplicate or engine-mismatched layouts fail-closed.\n",
    encoding="utf-8",
)
print("V2.4.19 verified manual layout production integrated")
