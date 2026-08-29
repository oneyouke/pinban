from pathlib import Path
import os
import shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent

# Install the V2.4 production/imposition math core and its regression test.
shutil.copy2(patch_root / "v240_core.py", root / "production_math.py")
shutil.copy2(patch_root / "test_v240_core.py", root / "test_v240_core.py")

# Version bump.
for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    p = root / filename
    text = p.read_text(encoding="utf-8").replace("2.3.7", "2.4.0")
    p.write_text(text, encoding="utf-8")

# Fail fast if the new core does not compile.
compile((root / "production_math.py").read_text(encoding="utf-8"), str(root / "production_math.py"), "exec")
compile((root / "test_v240_core.py").read_text(encoding="utf-8"), str(root / "test_v240_core.py"), "exec")

(root / "V240_PRO_IMPOSITION_CORE.md").write_text(
    "# V2.4 Professional Imposition Core\n\n"
    "First V2.4 delivery slice:\n"
    "- mm/cm/in/pt unit conversion.\n"
    "- Separate four-edge margins and gripper deduction.\n"
    "- Normal vs 90-degree fit calculation and recommendation.\n"
    "- Sheet utilization and remaining-edge calculations.\n"
    "- Production sheet calculation using order quantity, copies-per-sheet, make-ready and waste rate.\n"
    "- No rasterization or PDF-output changes in this slice; existing vector PDF output path remains untouched.\n",
    encoding="utf-8",
)
print("V2.4.0 professional imposition core applied")
