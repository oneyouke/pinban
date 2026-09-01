from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import product


root = Path(__file__).resolve().parent
assert product.APP_VERSION == "2.4.41"
assert product.APP_ID == "com.yunyouke.desktopimposer.pro"
assert product.VENDOR_NAME == "云游客科技"
assert product.SUPPORT_EMAIL == "3120085127@qq.com"

eula = (root / "EULA_TEMPLATE.txt").read_text(encoding="utf-8")
assert "最终用户许可协议" in eula
assert "[LEGAL COMPANY NAME]" not in eula
assert "3120085127@qq.com" in eula

notices = (root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8").lower()
for component in ("pyside6", "pymupdf", "pypdf", "reportlab", "pillow", "openpyxl", "cryptography", "shapely"):
    assert component in notices, component

result = subprocess.run([sys.executable, str(root / "release_gate.py"), "--strict"], cwd=root, text=True, capture_output=True)
assert result.returncode == 0, result.stdout + result.stderr
assert "PASS" in result.stdout
print("V2.4.41 COMMERCIAL RELEASE PASS")
