from pathlib import Path
import os

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()

p = root / "production_service.py"
s = p.read_text(encoding="utf-8")
old = '''        stage = "同步临时文件"\n        with tmp.open("rb") as f:\n            os.fsync(f.fileno())\n'''
new = '''        stage = "同步临时文件"\n        # Windows requires a writable file descriptor for fsync().\n        # Open read/write after PDF generation is complete, flush Python buffers,\n        # then sync the underlying descriptor before the atomic commit.\n        with tmp.open("r+b") as f:\n            f.flush()\n            os.fsync(f.fileno())\n'''
if old not in s:
    raise SystemExit("V2.3.5 fsync marker not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    p = root / filename
    text = p.read_text(encoding="utf-8").replace("2.3.4", "2.3.5")
    p.write_text(text, encoding="utf-8")

compile((root / "production_service.py").read_text(encoding="utf-8"), str(root / "production_service.py"), "exec")

(root / "V235_WINDOWS_ACCEPTANCE_FIX.md").write_text(
    "# V2.3.5 Windows acceptance fixes\n\n"
    "- Fix Windows PDF export fsync failure caused by syncing a read-only descriptor.\n"
    "- Full acceptance is rerun after the fix.\n"
    "- SQLite backup handle issue remains a blocking acceptance item until explicitly fixed.\n",
    encoding="utf-8",
)
print("V2.3.5 Windows fsync fix applied")
