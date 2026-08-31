from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import CMYKColorSep
from reportlab.pdfgen import canvas


MM_TO_PT = 72.0 / 25.4


PRESETS = {
    "envelope": {"name": "西式信封", "width_mm": 220.0, "height_mm": 110.0, "parts": 1, "description": "侧翼、封口翼、底翼、CutContour 与 Crease"},
    "paper_bag": {"name": "纸袋", "width_mm": 180.0, "height_mm": 240.0, "parts": 1, "description": "前后幅、侧风琴、糊口、袋底、折线"},
    "ncr": {"name": "NCR 多联单", "width_mm": 210.0, "height_mm": 140.0, "parts": 3, "description": "白/粉/黄/蓝联序、联号与胶装边"},
    "foil": {"name": "烫金", "width_mm": 90.0, "height_mm": 54.0, "parts": 1, "description": "Foil 专色、0.10 mm 陷印、2 mm 安全距"},
    "emboss": {"name": "击凸", "width_mm": 90.0, "height_mm": 54.0, "parts": 1, "description": "Emboss 专色、0.40 mm 深度、2 mm 避让"},
    "laser": {"name": "激光切割", "width_mm": 100.0, "height_mm": 100.0, "parts": 1, "description": "LaserCut 专色、0.15 mm 切缝、1 mm 桥位"},
}


@dataclass(frozen=True)
class SpecialPlan:
    preset_id: str
    name: str
    finished_width_mm: float
    finished_height_mm: float
    canvas_width_mm: float
    canvas_height_mm: float
    body_rect_mm: tuple[float, float, float, float]
    cut_polygons: list[list[tuple[float, float]]]
    crease_lines: list[tuple[float, float, float, float]]
    process_rects: list[tuple[str, float, float, float, float]]
    spot_names: list[str]
    page_labels: list[str]
    parameters: dict


def special_preset_choices():
    return [(key, value["name"]) for key, value in PRESETS.items()]


def get_special_preset_defaults(preset_id):
    if preset_id not in PRESETS: raise ValueError("未知特种产品模板")
    return dict(PRESETS[preset_id])


def _validate_dimensions(width_mm, height_mm):
    width_mm, height_mm = float(width_mm), float(height_mm)
    if width_mm <= 0 or height_mm <= 0: raise ValueError("成品尺寸必须大于 0")
    if width_mm > 3000 or height_mm > 3000: raise ValueError("成品尺寸超过 3000 mm 限制")
    return width_mm, height_mm


def build_special_plan(preset_id, *, width_mm=None, height_mm=None, parts=None):
    defaults = get_special_preset_defaults(preset_id)
    width, height = _validate_dimensions(width_mm or defaults["width_mm"], height_mm or defaults["height_mm"])
    page_labels = [defaults["name"]]; cut, crease, process, spots = [], [], [], []
    parameters = {"description": defaults["description"]}
    margin = 10.0
    if preset_id == "envelope":
        side = max(12.0, min(30.0, height * .16)); seal = max(25.0, height * .32); bottom = max(30.0, height * .40)
        blank_w, blank_h = width + side * 2, height + seal + bottom
        body = (margin + side, margin + bottom, width, height)
        x, y, w, h = body
        outline = [(x-side,y),(x,y),(x,y-bottom),(x+w,y-bottom),(x+w,y),(x+w+side,y),(x+w+side,y+h),(x+w,y+h),(x+w,y+h+seal),(x,y+h+seal),(x,y+h),(x-side,y+h)]
        cut=[outline]; crease=[(x,y,x,y+h),(x+w,y,x+w,y+h),(x,y,x+w,y),(x,y+h,x+w,y+h)]; spots=["CutContour","Crease"]
        parameters.update({"side_flap_mm":side,"seal_flap_mm":seal,"bottom_flap_mm":bottom})
    elif preset_id == "paper_bag":
        depth=max(35.0,min(width*.45,90.0)); glue=max(12.0,min(25.0,width*.08)); top=max(20.0,height*.10); bottom=max(40.0,min(height*.28,90.0))
        blank_w=2*(width+depth)+glue; blank_h=height+top+bottom; body=(margin+glue,margin+bottom,blank_w-glue,height)
        x0,y0=margin,margin; cut=[[(x0,y0),(x0+blank_w,y0),(x0+blank_w,y0+blank_h),(x0,y0+blank_h)]]
        vertical=[glue,glue+depth,glue+depth+width,glue+2*depth+width,blank_w]
        crease=[(x0+v,y0,x0+v,y0+blank_h) for v in vertical]+[(x0,y0+bottom,x0+blank_w,y0+bottom),(x0,y0+bottom+height,x0+blank_w,y0+bottom+height)]
        spots=["CutContour","Crease"]; parameters.update({"gusset_mm":depth,"glue_tab_mm":glue,"top_fold_mm":top,"bottom_mm":bottom})
    elif preset_id == "ncr":
        part_count=int(parts or defaults["parts"])
        if part_count<2 or part_count>8: raise ValueError("NCR 联数必须在 2–8 之间")
        blank_w,blank_h=width,height; body=(margin,margin,width,height)
        colors=["WHITE","PINK","YELLOW","BLUE","GREEN","IVORY","GRAY","ORANGE"]
        page_labels=[f"NCR PART {i+1} / {colors[i]}" for i in range(part_count)]
        parameters.update({"parts":part_count,"part_colors":colors[:part_count],"glue_edge":"top","numbering_start":1})
    else:
        blank_w,blank_h=width,height; body=(margin,margin,width,height); inset=2.0
        spot={"foil":"Foil","emboss":"Emboss","laser":"LaserCut"}[preset_id]
        process=[(spot,margin+inset,margin+inset,width-2*inset,height-2*inset)]; spots=[spot]
        if preset_id=="foil": parameters.update({"trap_mm":.10,"safe_inset_mm":2.0,"minimum_line_mm":.20})
        elif preset_id=="emboss": parameters.update({"relief_depth_mm":.40,"clearance_mm":2.0,"minimum_line_mm":.30})
        else: parameters.update({"kerf_mm":.15,"minimum_bridge_mm":1.0,"minimum_radius_mm":.50})
    return SpecialPlan(preset_id,defaults["name"],width,height,blank_w+margin*2,blank_h+margin*2,body,cut,crease,process,spots,page_labels,parameters)


def _merge_source(page, source, rect):
    x,y,w,h=rect; sw,sh=float(source.mediabox.width),float(source.mediabox.height)
    scale=min(w*MM_TO_PT/sw,h*MM_TO_PT/sh); cw,ch=sw*scale,sh*scale
    tx=x*MM_TO_PT+(w*MM_TO_PT-cw)/2; ty=y*MM_TO_PT+(h*MM_TO_PT-ch)/2
    page.merge_transformed_page(source,Transformation().scale(scale).translate(tx,ty),over=True)


def _draw_poly(c, points):
    p=c.beginPath(); p.moveTo(points[0][0]*MM_TO_PT,points[0][1]*MM_TO_PT)
    for x,y in points[1:]: p.lineTo(x*MM_TO_PT,y*MM_TO_PT)
    p.close(); c.drawPath(p,stroke=1,fill=0)


def _overlay(plan, page_label):
    stream=BytesIO(); c=canvas.Canvas(stream,pagesize=(plan.canvas_width_mm*MM_TO_PT,plan.canvas_height_mm*MM_TO_PT),pageCompression=1)
    c.setLineWidth(.6)
    if plan.cut_polygons:
        c.setStrokeColor(CMYKColorSep(0,100,0,0,spotName="CutContour",density=1))
        for poly in plan.cut_polygons:_draw_poly(c,poly)
    if plan.crease_lines:
        c.setStrokeColor(CMYKColorSep(100,0,0,0,spotName="Crease",density=1));c.setDash(4,2)
        for x1,y1,x2,y2 in plan.crease_lines:c.line(x1*MM_TO_PT,y1*MM_TO_PT,x2*MM_TO_PT,y2*MM_TO_PT)
        c.setDash()
    for spot,x,y,w,h in plan.process_rects:
        c.setStrokeColor(CMYKColorSep(0,100,0,0,spotName=spot,density=1));c.setLineWidth(.8);c.rect(x*MM_TO_PT,y*MM_TO_PT,w*MM_TO_PT,h*MM_TO_PT,stroke=1,fill=0)
    x,y,w,h=plan.body_rect_mm;c.setStrokeColorCMYK(0,0,0,.45);c.setDash(2,2);c.rect(x*MM_TO_PT,y*MM_TO_PT,w*MM_TO_PT,h*MM_TO_PT,stroke=1,fill=0);c.setDash()
    c.setFillColorCMYK(0,0,0,1);c.setFont("Helvetica",7);c.drawString(5,5,f"SPECIAL TEMPLATE / {plan.preset_id.upper()} / {page_label}")
    c.save();stream.seek(0);return PdfReader(stream).pages[0]


def export_special_template_pdf(preset_id,output_path,*,source_pdf=None,width_mm=None,height_mm=None,parts=None):
    plan=build_special_plan(preset_id,width_mm=width_mm,height_mm=height_mm,parts=parts)
    source=None
    if source_pdf:
        reader=PdfReader(str(source_pdf))
        if not reader.pages:raise ValueError("画稿 PDF 没有页面")
        source=reader.pages[0]
    writer=PdfWriter();w=plan.canvas_width_mm*MM_TO_PT;h=plan.canvas_height_mm*MM_TO_PT
    for label in plan.page_labels:
        page=PageObject.create_blank_page(width=w,height=h)
        if source is not None:_merge_source(page,source,plan.body_rect_mm)
        page.merge_page(_overlay(plan,label));writer.add_page(page)
    writer.add_metadata({"/Title":plan.name+" - Special Template","/Subject":json_summary(plan),"/Creator":"Desktop Imposer Pro"})
    output_path=Path(output_path);output_path.parent.mkdir(parents=True,exist_ok=True);temporary=output_path.with_suffix(output_path.suffix+".tmp")
    with temporary.open("wb") as handle:writer.write(handle);handle.flush()
    temporary.replace(output_path);verified=PdfReader(str(output_path))
    if len(verified.pages)!=len(plan.page_labels):raise RuntimeError("特种模板输出页数校验失败")
    payload=output_path.read_bytes()
    for spot in plan.spot_names:
        if b"/Separation" not in payload or spot.encode("ascii") not in payload:raise RuntimeError(f"工艺专色写入失败：{spot}")
    return {**asdict(plan),"output":str(output_path),"output_pages":len(plan.page_labels),"source_artwork":source is not None}


def json_summary(plan):
    return "; ".join(f"{key}={value}" for key,value in plan.parameters.items())
