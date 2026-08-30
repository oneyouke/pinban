from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
for src, dst in (("production_modes_v2422.py","production_modes.py"),("test_v2422_production_modes.py","test_v2422_production_modes.py")):
    shutil.copy2(patch_root/src, root/dst)

app = root/"app.py"; text=app.read_text(encoding="utf-8")
old="from professional_canvas import ProfessionalPageCanvasWidget\n"
new="from production_modes import ProductionModeWorkspace\n"
if new not in text:
    if old not in text: raise SystemExit("V2.4.21 professional workspace import marker missing")
    text=text.replace(old,new,1)
old="self.professional_workspace = ProfessionalPageCanvasWidget(self)"
new="self.professional_workspace = ProductionModeWorkspace(self)"
if new not in text:
    if old not in text: raise SystemExit("V2.4.21 professional workspace construction marker missing")
    text=text.replace(old,new,1)
app.write_text(text,encoding="utf-8")

for filename in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.21","2.4.22"),encoding="utf-8")
for filename in ("production_modes.py","app.py","test_v2422_production_modes.py"):
    compile((root/filename).read_text(encoding="utf-8"),str(root/filename),"exec")
(root/"V2422_PRODUCTION_MODES.md").write_text("# V2.4.22 Production Modes\n\n- Adds top-level single-page, book and box imposition modes.\n- Adds book signatures, saddle stitch, flip method, fold lines, spine and creep previews.\n- Adds PDF/SVG/DXF/JSON die import, polygon nesting, bleed and CutContour previews.\n",encoding="utf-8")
print("V2.4.22 production modes integrated")
