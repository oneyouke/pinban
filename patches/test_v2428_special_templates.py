import tempfile
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from special_templates import MM_TO_PT, build_special_plan, export_special_template_pdf, special_preset_choices


with tempfile.TemporaryDirectory(prefix="v2428-special-") as td:
    root=Path(td);source=root/"art.pdf"
    c=canvas.Canvas(str(source),pagesize=(90*MM_TO_PT,54*MM_TO_PT));c.drawString(20,50,"SPECIAL-ART");c.save()
    assert [key for key,_ in special_preset_choices()]==["envelope","paper_bag","ncr","foil","emboss","laser"]
    envelope=build_special_plan("envelope",width_mm=220,height_mm=110)
    assert envelope.canvas_width_mm>220 and envelope.canvas_height_mm>110
    assert envelope.spot_names==["CutContour","Crease"] and len(envelope.crease_lines)==4
    bag=build_special_plan("paper_bag",width_mm=180,height_mm=240)
    assert bag.parameters["gusset_mm"]>0 and len(bag.crease_lines)>=7
    ncr=build_special_plan("ncr",width_mm=210,height_mm=140,parts=4)
    assert len(ncr.page_labels)==4 and ncr.parameters["part_colors"]==["WHITE","PINK","YELLOW","BLUE"]
    for preset,spot in (("foil","Foil"),("emboss","Emboss"),("laser","LaserCut")):
        plan=build_special_plan(preset,width_mm=100,height_mm=70)
        assert plan.spot_names==[spot] and plan.process_rects[0][0]==spot
        output=root/f"{preset}.pdf";result=export_special_template_pdf(preset,output,source_pdf=source,width_mm=100,height_mm=70)
        assert result["output_pages"]==1 and result["source_artwork"]
        payload=output.read_bytes();assert b"/Separation" in payload and spot.encode() in payload
        assert "SPECIAL-ART" in (PdfReader(str(output)).pages[0].extract_text() or "")
    envelope_output=root/"envelope.pdf";export_special_template_pdf("envelope",envelope_output,width_mm=220,height_mm=110)
    ep=envelope_output.read_bytes();assert b"CutContour" in ep and b"Crease" in ep
    ncr_output=root/"ncr.pdf";result=export_special_template_pdf("ncr",ncr_output,source_pdf=source,width_mm=210,height_mm=140,parts=4)
    reader=PdfReader(str(ncr_output));assert result["output_pages"]==4 and len(reader.pages)==4
    assert "\n".join(p.extract_text() or "" for p in reader.pages).count("SPECIAL-ART")==4
print("V2.4.28 SPECIAL TEMPLATE LIBRARY PASS")
