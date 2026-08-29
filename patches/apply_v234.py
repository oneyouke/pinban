from pathlib import Path
import os
import shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / "full_acceptance_runner.py", root / "test_full_acceptance.py")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    p = root / filename
    text = p.read_text(encoding="utf-8").replace("2.3.3", "2.3.4")
    p.write_text(text, encoding="utf-8")

compile((root / "test_full_acceptance.py").read_text(encoding="utf-8"), str(root / "test_full_acceptance.py"), "exec")

(root / "V234_FULL_ACCEPTANCE_GATE.md").write_text(
    "# V2.3.4 Full Acceptance Gate\n\n"
    "- Runs every built-in test_*.py regression script on Windows.\n"
    "- Includes installation smoke and the V2.3.3 Unicode-path production PDF export test.\n"
    "- Produces JSON and Markdown acceptance reports.\n"
    "- CI fails if any automated regression fails.\n"
    "- RIP/CTP, certified PDF/X, real spot-color separations, paper-fold and other physical/provider validations remain explicitly manual/external.\n",
    encoding="utf-8",
)
print("V2.3.4 full acceptance gate applied")
