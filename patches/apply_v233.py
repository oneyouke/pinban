from pathlib import Path
import os

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()

# Robust production export on Windows: diagnose stage, avoid overwriting inputs,
# and fall back to a unique output name when the selected PDF is locked/open.
p = root / "production_service.py"
s = p.read_text(encoding="utf-8")

if "def _unique_unlocked_destination" not in s:
    marker = "\ndef atomic_production_export(jobs: Sequence[InputJob], output_path: str | Path, settings: ImpositionSettings,\n"
    if marker not in s:
        raise SystemExit("atomic_production_export marker not found")
    helper = r'''

def _unique_unlocked_destination(dst: Path) -> Path:
    """Return a sibling PDF path that does not currently exist."""
    stem = dst.stem
    suffix = dst.suffix or ".pdf"
    for index in range(1, 1000):
        candidate = dst.with_name(f"{stem} ({index}){suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError("目标目录中同名输出过多，请更换文件名后重试")


def _commit_pdf(tmp: Path, dst: Path) -> tuple[Path, str | None]:
    """Atomically commit where possible; if Windows has dst locked, save beside it."""
    try:
        os.replace(tmp, dst)
        return dst, None
    except PermissionError as exc:
        alternate = _unique_unlocked_destination(dst)
        try:
            os.replace(tmp, alternate)
        except Exception:
            raise PermissionError(
                f"目标 PDF 正被其他程序占用，且备用文件也无法写入：{dst}。"
                "请关闭 Acrobat/浏览器/PDF 预览窗格后重试。"
            ) from exc
        return alternate, f"原目标文件被占用，已自动另存为：{alternate.name}"
    except OSError as exc:
        # Some sync/network folders return a generic OSError instead of PermissionError.
        alternate = _unique_unlocked_destination(dst)
        try:
            os.replace(tmp, alternate)
        except Exception:
            raise OSError(f"无法提交生产 PDF 到目标目录：{dst}；系统错误：{exc}") from exc
        return alternate, f"原目标路径无法覆盖，已自动另存为：{alternate.name}"
'''
    s = s.replace(marker, helper + marker, 1)

old = '''    dst = Path(output_path)\n    if dst.suffix.lower() != ".pdf":\n        dst = dst.with_suffix(".pdf")\n    dst.parent.mkdir(parents=True, exist_ok=True)\n\n    preflight = preflight_report or run_preflight(jobs, settings)\n'''
new = '''    dst = Path(output_path).expanduser()\n    if dst.suffix.lower() != ".pdf":\n        dst = dst.with_suffix(".pdf")\n    try:\n        dst = dst.resolve(strict=False)\n    except Exception:\n        dst = dst.absolute()\n    dst.parent.mkdir(parents=True, exist_ok=True)\n\n    # Never allow a production export to overwrite one of its own source files.\n    input_paths = set()\n    for job in jobs:\n        try:\n            input_paths.add(Path(job.path).resolve(strict=False))\n        except Exception:\n            pass\n    if dst in input_paths:\n        raise ValueError("输出 PDF 不能覆盖正在使用的源文件，请选择其他文件名")\n\n    stage = "印前检查"\n    preflight = preflight_report or run_preflight(jobs, settings)\n'''
if old not in s:
    raise SystemExit("production export setup block not found")
s = s.replace(old, new, 1)

old = '''    inputs = input_manifest(jobs)\n    fd, tmp_name = tempfile.mkstemp(prefix=f".{dst.stem}.", suffix=".partial.pdf", dir=str(dst.parent))\n    os.close(fd)\n    tmp = Path(tmp_name)\n    committed = False\n    try:\n        summary = impose_jobs(jobs, tmp, settings, layout_override=layout_override)\n        check = validate_pdf_output(tmp, expected_pages=int(summary.get("output_pages") or 0) or None)\n        digest = sha256_file(tmp)\n        with tmp.open("rb") as f:\n            os.fsync(f.fileno())\n        os.replace(tmp, dst)\n        committed = True\n\n        manifest = {\n'''
new = '''    stage = "读取源文件清单"\n    inputs = input_manifest(jobs)\n    try:\n        fd, tmp_name = tempfile.mkstemp(prefix=f".{dst.stem}.", suffix=".partial.pdf", dir=str(dst.parent))\n        os.close(fd)\n    except Exception as exc:\n        raise RuntimeError(f"目标目录不可写：{dst.parent}；{exc}") from exc\n    tmp = Path(tmp_name)\n    committed = False\n    actual_dst = dst\n    commit_warning = None\n    try:\n        stage = "拼版生成"\n        summary = impose_jobs(jobs, tmp, settings, layout_override=layout_override)\n        stage = "PDF 完整性校验"\n        check = validate_pdf_output(tmp, expected_pages=int(summary.get("output_pages") or 0) or None)\n        stage = "计算 SHA-256"\n        digest = sha256_file(tmp)\n        stage = "同步临时文件"\n        with tmp.open("rb") as f:\n            os.fsync(f.fileno())\n        stage = "提交目标文件"\n        actual_dst, commit_warning = _commit_pdf(tmp, dst)\n        committed = True\n\n        manifest = {\n'''
if old not in s:
    raise SystemExit("production export core block not found")
s = s.replace(old, new, 1)

s = s.replace('            "output": str(dst.resolve()),\n', '            "output": str(actual_dst.resolve()),\n', 1)
s = s.replace('            "record_warnings": [],\n', '            "record_warnings": ([commit_warning] if commit_warning else []),\n', 1)
s = s.replace('                sidecar = dst.with_suffix(dst.suffix + ".production.json")\n', '                sidecar = actual_dst.with_suffix(actual_dst.suffix + ".production.json")\n', 1)
s = s.replace('                    "output": str(dst), "sha256": digest, "pages": check["page_count"],\n', '                    "output": str(actual_dst), "sha256": digest, "pages": check["page_count"],\n', 1)

# Improve the failure message with the exact export stage.
old = '''        if committed:\n            # Defensive path: a post-commit bookkeeping exception should not be reported as a failed PDF export.\n            return {\n                "schema_version": 1, "app": APP_NAME, "app_version": APP_VERSION,\n                "created_at": utc_now(), "output": str(dst.resolve()),\n                "output_sha256": sha256_file(dst), "output_size_bytes": dst.stat().st_size,\n                "output_pages": validate_pdf_output(dst)["page_count"],\n                "inputs": inputs, "summary": summary, "preflight": preflight,\n                "settings": settings.to_dict(), "manual_layout": bool(layout_override),\n                "record_warnings": [f"生产 PDF 已提交，但后续记录步骤发生错误：{exc}"],\n            }\n        raise\n'''
new = '''        if committed:\n            # Defensive path: a post-commit bookkeeping exception should not be reported as a failed PDF export.\n            return {\n                "schema_version": 1, "app": APP_NAME, "app_version": APP_VERSION,\n                "created_at": utc_now(), "output": str(actual_dst.resolve()),\n                "output_sha256": sha256_file(actual_dst), "output_size_bytes": actual_dst.stat().st_size,\n                "output_pages": validate_pdf_output(actual_dst)["page_count"],\n                "inputs": inputs, "summary": summary, "preflight": preflight,\n                "settings": settings.to_dict(), "manual_layout": bool(layout_override),\n                "record_warnings": ([commit_warning] if commit_warning else []) + [f"生产 PDF 已提交，但后续记录步骤发生错误：{exc}"],\n            }\n        raise RuntimeError(f"生产 PDF 导出失败（阶段：{stage}）：{exc}") from exc\n'''
if old not in s:
    raise SystemExit("production export exception block not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# UI must display the actual output path, especially when a locked target caused an auto-rename.
p = root / "app.py"
s = p.read_text(encoding="utf-8")
old = '''            summary = manifest["summary"]\n            mode = "双面" if summary["duplex"] else "单面"\n'''
new = '''            summary = manifest["summary"]\n            actual_path = manifest.get("output") or path\n            record_warnings = list(manifest.get("record_warnings") or [])\n            mode = "双面" if summary["duplex"] else "单面"\n'''
if old not in s:
    raise SystemExit("export UI summary marker not found")
s = s.replace(old, new, 1)
s = s.replace('                f"SHA-256：{manifest[\'output_sha256\'][:20]}…\\n\\n{path}\\n\\n"\n', '                f"SHA-256：{manifest[\'output_sha256\'][:20]}…\\n\\n{actual_path}\\n\\n"\n', 1)
s = s.replace('            self.statusBar().showMessage(f"已安全导出：{path}", 8000)\n', '            if record_warnings:\n                QMessageBox.warning(self, "导出提示", "\\n".join(record_warnings))\n            self.statusBar().showMessage(f"已安全导出：{actual_path}", 8000)\n', 1)
p.write_text(s, encoding="utf-8")

# Add a focused export smoke test executed by the Windows CI after dependencies are installed.
test = root / "test_export_v233.py"
test.write_text(r'''from pathlib import Path
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from imposition import InputJob, ImpositionSettings
from production_service import atomic_production_export, validate_pdf_output

with tempfile.TemporaryDirectory(prefix="拼版导出测试_") as td:
    root = Path(td)
    src = root / "源文件 测试.pdf"
    c = canvas.Canvas(str(src), pagesize=A4)
    c.drawString(72, 720, "Desktop Imposer export smoke test")
    c.showPage(); c.save()

    out_dir = root / "桌面 输出"
    out = out_dir / "拼版输出.pdf"
    settings = ImpositionSettings(sheet_width_mm=320, sheet_height_mm=450)
    manifest = atomic_production_export([InputJob(src, 1)], out, settings, write_manifest=True)
    actual = Path(manifest["output"])
    assert actual.exists(), actual
    assert validate_pdf_output(actual)["page_count"] >= 1
    assert actual.with_suffix(actual.suffix + ".production.json").exists()
    print("V2.3.3 export smoke OK", actual)
''', encoding="utf-8")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    p = root / filename
    text = p.read_text(encoding="utf-8").replace("2.3.2", "2.3.3")
    p.write_text(text, encoding="utf-8")

compile((root / "production_service.py").read_text(encoding="utf-8"), str(root / "production_service.py"), "exec")
compile((root / "app.py").read_text(encoding="utf-8"), str(root / "app.py"), "exec")
compile(test.read_text(encoding="utf-8"), str(test), "exec")

(root / "V233_PDF_EXPORT_FIX.md").write_text(
    "# V2.3.3 PDF export reliability fix\n\n"
    "- Reports the exact failed export stage instead of a generic failure.\n"
    "- Refuses to overwrite an active source file.\n"
    "- If an existing target PDF is locked by Acrobat/preview/sync software, automatically saves to a unique sibling filename.\n"
    "- UI reports the actual output path and any fallback warning.\n"
    "- Adds a real Windows CI production-export smoke test using Unicode paths.\n",
    encoding="utf-8",
)
print("V2.3.3 PDF export reliability patch applied")
