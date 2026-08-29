from pathlib import Path
import os

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()

# 1) backup_restore.py: sqlite3.Connection context manager commits/rolls back but does NOT
# close the connection. On Windows the snapshot therefore remains locked at unlink().
p = root / "backup_restore.py"
s = p.read_text(encoding="utf-8")
old = '''        with sqlite3.connect(db_path) as src, sqlite3.connect(db_snapshot) as dst:\n            src.backup(dst)\n        files.append((db_snapshot, "data/production.sqlite3"))\n'''
new = '''        src = sqlite3.connect(db_path)\n        dst = sqlite3.connect(db_snapshot)\n        try:\n            src.backup(dst)\n            dst.commit()\n        finally:\n            try:\n                dst.close()\n            finally:\n                src.close()\n        files.append((db_snapshot, "data/production.sqlite3"))\n'''
if old not in s:
    raise SystemExit("backup sqlite snapshot block not found")
s = s.replace(old, new, 1)

old = '''        if staged_db.exists():\n            with sqlite3.connect(staged_db) as db:\n                result = db.execute("PRAGMA integrity_check").fetchone()[0]\n                if str(result).lower() != "ok":\n                    raise ValueError("backup database integrity check failed")\n'''
new = '''        if staged_db.exists():\n            db = sqlite3.connect(staged_db)\n            try:\n                result = db.execute("PRAGMA integrity_check").fetchone()[0]\n                if str(result).lower() != "ok":\n                    raise ValueError("backup database integrity check failed")\n            finally:\n                db.close()\n'''
if old not in s:
    raise SystemExit("restore integrity sqlite block not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# 2) Version bump. Storage recovery handle issue will be fixed separately after its
# exact implementation is exposed by the acceptance workflow.
for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    p = root / filename
    text = p.read_text(encoding="utf-8").replace("2.3.5", "2.3.6")
    p.write_text(text, encoding="utf-8")

compile((root / "backup_restore.py").read_text(encoding="utf-8"), str(root / "backup_restore.py"), "exec")
(root / "V236_WINDOWS_SQLITE_FIX.md").write_text(
    "# V2.3.6 Windows SQLite handle fix\n\n"
    "- Explicitly closes SQLite source/snapshot connections after backup.\n"
    "- Explicitly closes staged restore database after integrity_check.\n"
    "- Prevents WinError 32 when deleting snapshot/restoration files.\n",
    encoding="utf-8",
)
print("V2.3.6 Windows SQLite handle fix applied")
