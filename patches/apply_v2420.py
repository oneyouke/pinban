from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent

for src, dst in (
    ("professional_canvas_v2420.py", "professional_canvas.py"),
    ("test_v2420_professional_workspace.py", "test_v2420_professional_workspace.py"),
):
    shutil.copy2(patch_root / src, root / dst)

p = root / "prepress_center.py"
s = p.read_text(encoding="utf-8")
old = "from page_canvas import PageCanvasWidget\n"
new = "from professional_canvas import ProfessionalPageCanvasWidget as PageCanvasWidget\n"
if new not in s:
    if old not in s:
        raise SystemExit("V2.4.19 page canvas import marker missing")
    s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    fp = root / filename
    fp.write_text(fp.read_text(encoding="utf-8").replace("2.4.19", "2.4.20"), encoding="utf-8")

for filename in ("professional_canvas.py", "prepress_center.py", "test_v2420_professional_workspace.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")

(root / "V2420_PROFESSIONAL_WORKSPACE.md").write_text(
    "# V2.4.20 Professional Imposition Workspace\n\n"
    "- Rebuilds the page/canvas screen as a three-pane production workspace.\n"
    "- Adds a compact command bar, job/page sidebar, millimetre rulers and a persistent inspector.\n"
    "- Adds one-click single-page auto imposition with rotation optimization and live utilization.\n"
    "- Keeps mixed imposition, duplex overlay, precise coordinates, undo/redo and workspace persistence.\n"
    "- Preserves the verified vector production export path introduced through V2.4.19.\n",
    encoding="utf-8",
)
print("V2.4.20 professional imposition workspace integrated")
