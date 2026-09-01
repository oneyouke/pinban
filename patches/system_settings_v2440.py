from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFontComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QSplitter, QStackedWidget,
    QVBoxLayout, QWidget,
)

from ui_themes import theme_choices


SETTING_KEY = "system.settings.v1"

DEFAULT_SYSTEM_SETTINGS = {
    "ui.theme":"ocean", "ui.font_family":"Microsoft YaHei UI", "ui.font_size":10,
    "general.zoom_center":True, "general.remember_values":True, "general.restore_quantity":False, "general.default_quantity":1,
    "general.default_bleed":3.0, "general.import_bleed":3.0, "general.max_font_size":0,
    "general.sample_types":"92*52  212*142  5*5", "general.pdf_import_version":"不限制",
    "general.output_pdf_version":"PDF 1.5", "general.show_overlap":False,
    "general.multi_thread":True, "general.continuous_preview":False, "general.compress_pdf":True,
    "general.hide_blank_pages":True, "general.reference_only":False, "general.add_labels":True,
    "general.label_distance":10.0, "general.hide_template_grid":True, "general.overlap_alert":True,
    "general.filename":"{订单号}-{客户名称}-{样本信息}-{拼版尺寸}-{纸张克重}",
    "blue.enabled":True, "blue.color":"淡蓝", "blue.opacity":22, "blue.line_width":0.3,
    "placement.snap":1.0, "placement.auto_rotate":True, "placement.allow_overlap":False,
    "placement.lock_new":False, "placement.show_coordinates":True, "placement.move_step":1.0,
    "paper.default":"铜版纸 105g", "paper.width":450.0, "paper.height":320.0,
    "paper.grain":"不限纸纹", "paper.custom_presets":"SRA3=450x320; 对开=787x1092",
    "press.default":"海德堡 SM74（745×605）", "press.plate":"CTP 热敏版", "press.gripper":10.0,
    "press.tail":3.0, "press.max_width":745.0, "press.max_height":605.0, "press.speed":10500,
    "grammage.default":105, "grammage.list":"80,100,105,128,157,200,250,300,350", "grammage.caliper":0.10, "grammage.warn_mismatch":True,
    "large.enabled":True, "large.tile_overlap":10.0, "large.roll_width":1600.0, "large.max_length":3200.0, "large.add_tile_labels":True,
    "book.trim":"210×285 mm", "book.signature":16, "book.binding":"胶装 / 锁线分帖", "book.flip":"长边翻", "book.creep":0.10,
    "finishing.lamination":"无", "finishing.foil_spot":"Foil", "finishing.emboss_spot":"Emboss", "finishing.uv_spot":"SpotUV", "finishing.die_spot":"CutContour", "finishing.export_layers":True,
    "signature.fold_lines":True, "signature.fold_width":0.25, "signature.fold_color":"品红", "signature.show_page_numbers":True, "signature.auto_spine":True, "signature.safe_inset":3.0,
    "shortcut.import":"Ctrl+I", "shortcut.export":"Ctrl+E", "shortcut.preflight":"F8", "shortcut.auto_impose":"F9", "shortcut.rotate":"R", "shortcut.group":"Ctrl+G", "shortcut.ungroup":"Ctrl+Shift+G", "shortcut.settings":"Ctrl+,",
    "qr.enabled":False, "qr.level":"M", "qr.size":12.0, "qr.content":"{订单号}|{客户名称}|{版次}", "qr.position":"右下角", "qr.quiet_zone":2.0,
    "die.spot":"CutContour", "die.bleed":3.0, "die.line_width":0.2, "die.overprint":True, "die.validate_closed":True, "die.allow_rotation":True,
    "preflight.fonts":True, "preflight.colors":True, "preflight.images":True, "preflight.pdfx":False, "preflight.min_dpi":300,
    "cut.crop_marks":True, "cut.registration":True, "cut.color_bar":True, "cut.mark_length":5.0, "cut.mark_offset":2.0,
}


PAGE_SPECS = (
    ("基本参数", (
        ("check","general.zoom_center","鼠标放大缩小改变中心位置"), ("check","general.remember_values","记住上次输入参数"),
        ("check","general.restore_quantity","打开项目时恢复印刷数量"), ("spin","general.default_quantity","导入文件默认数量",1,100000000,""), ("double","general.default_bleed","默认成品出血",0,50," mm"),
        ("double","general.import_bleed","导入文件默认出血",0,50," mm"), ("font","ui.font_family","界面字体"),
        ("spin","ui.font_size","界面字号",8,24," pt"), ("spin","general.max_font_size","显示字号最大限制",0,200,""),
        ("text","general.sample_types","样本类型选项"), ("combo","general.pdf_import_version","导入 PDF 版本要求",("不限制","PDF 1.4","PDF 1.5","PDF/X-1a","PDF/X-4")),
        ("combo","general.output_pdf_version","输出 PDF 版本",("PDF 1.4","PDF 1.5","PDF 1.6","PDF/X-1a","PDF/X-4")),
        ("combo_data","ui.theme","界面皮肤",tuple(theme_choices())), ("check","general.show_overlap","显示重叠区域"),
        ("check","general.multi_thread","多线程模式生成 PDF"), ("check","general.continuous_preview","连续界面显示实时尺寸"),
        ("check","general.compress_pdf","输出不要自定义印数"), ("check","general.hide_blank_pages","导入画册时隐藏界面"),
        ("check","general.reference_only","只保留拼版区域参考线"), ("check","general.add_labels","版头添加文字和色标"),
        ("double","general.label_distance","版头距离版边",0,100," mm"), ("check","general.hide_template_grid","不显示模板网格"),
        ("check","general.overlap_alert","超过拼版区域提醒"), ("text","general.filename","输出文件命名格式"),
    )),
    ("蓝纸设置", (("check","blue.enabled","显示蓝纸/安全区域"),("combo","blue.color","蓝纸颜色",("淡蓝","青色","灰蓝","自定义")),("spin","blue.opacity","填充透明度",0,100,"%"),("double","blue.line_width","参考线宽度",0.1,5," mm"))),
    ("版位设置", (("double","placement.snap","吸附步长",0.1,50," mm"),("double","placement.move_step","键盘移动步长",0.1,50," mm"),("check","placement.auto_rotate","自动旋转优化"),("check","placement.allow_overlap","允许版位重叠"),("check","placement.lock_new","新建版位默认锁定"),("check","placement.show_coordinates","显示版位坐标"))),
    ("用纸设置", (("combo","paper.default","默认纸张",("铜版纸 105g","铜版纸 157g","双胶纸 80g","白卡纸 300g","自定义")),("double","paper.width","默认纸宽",20,5000," mm"),("double","paper.height","默认纸高",20,5000," mm"),("combo","paper.grain","纸纹方向",("不限纸纹","长纹","短纹")),("text","paper.custom_presets","自定义纸张预设"))),
    ("印刷机/版材", (("combo","press.default","默认印刷机",("海德堡 SM74（745×605）","海德堡 XL75（750×605）","小森 Lithrone 40（1020×720）","罗兰 700（1040×740）","数码印刷机（330×488）")),("combo","press.plate","版材类型",("CTP 热敏版","CTP 紫激光版","免处理版","数码无版")),("double","press.gripper","默认咬口",0,100," mm"),("double","press.tail","默认底边",0,100," mm"),("double","press.max_width","设备最大宽度",100,5000," mm"),("double","press.max_height","设备最大高度",100,5000," mm"),("spin","press.speed","设备速度",1,100000," 张/时"))),
    ("纸张克重", (("spin","grammage.default","默认克重",20,1000," g/m²"),("text","grammage.list","常用克重列表"),("double","grammage.caliper","默认纸张厚度",0.01,2," mm"),("check","grammage.warn_mismatch","纸张克重不匹配时警告"))),
    ("大纸设置", (("check","large.enabled","启用大幅面分块"),("double","large.tile_overlap","分块搭接",0,100," mm"),("double","large.roll_width","卷材宽度",100,10000," mm"),("double","large.max_length","最大输出长度",100,50000," mm"),("check","large.add_tile_labels","分块添加编号"))),
    ("开本设置", (("combo","book.trim","默认成品尺寸",("210×285 mm","210×297 mm","185×260 mm","148×210 mm","自定义")),("spin","book.signature","默认每帖页数",4,64," 页"),("combo","book.binding","装订方式",("骑马订","胶装 / 锁线分帖","锁线精装")),("combo","book.flip","翻页方式",("长边翻","短边翻","天地翻")),("double","book.creep","爬移补偿",0,10," mm/张"))),
    ("后加工设置", (("combo","finishing.lamination","覆膜",("无","哑膜","光膜","触感膜")),("text","finishing.foil_spot","烫金专色名"),("text","finishing.emboss_spot","击凸专色名"),("text","finishing.uv_spot","局部 UV 专色名"),("text","finishing.die_spot","刀线专色名"),("check","finishing.export_layers","按工艺分层输出"))),
    ("折手设置", (("check","signature.fold_lines","显示折手线"),("double","signature.fold_width","折手线宽度",0.1,5," pt"),("combo","signature.fold_color","折手线颜色",("品红","青色","黑色","专色")),("check","signature.show_page_numbers","显示折手页码"),("check","signature.auto_spine","自动计算书脊"),("double","signature.safe_inset","页面安全边",0,50," mm"))),
    ("快捷键设置", (("text","shortcut.import","导入文件"),("text","shortcut.export","导出 PDF"),("text","shortcut.preflight","印前检查"),("text","shortcut.auto_impose","自动拼版"),("text","shortcut.rotate","旋转版位"),("text","shortcut.group","群组"),("text","shortcut.ungroup","解组"),("text","shortcut.settings","系统设置"))),
    ("二维码设置", (("check","qr.enabled","默认启用版级二维码"),("combo","qr.level","纠错等级",("L","M","Q","H")),("double","qr.size","二维码尺寸",3,100," mm"),("text","qr.content","二维码内容模板"),("combo","qr.position","位置",("左上角","右上角","左下角","右下角")),("double","qr.quiet_zone","静区",0,20," mm"))),
    ("刀模设置", (("text","die.spot","刀线专色名"),("double","die.bleed","刀模出血",0,50," mm"),("double","die.line_width","刀线宽度",0.1,5," pt"),("check","die.overprint","刀线叠印"),("check","die.validate_closed","检查轮廓闭合"),("check","die.allow_rotation","异形套料允许旋转"))),
    ("预检与裁切", (("check","preflight.fonts","检查字体嵌入"),("check","preflight.colors","检查颜色空间"),("check","preflight.images","检查图像分辨率"),("check","preflight.pdfx","检查 PDF/X"),("spin","preflight.min_dpi","最低图像分辨率",72,2400," dpi"),("check","cut.crop_marks","默认输出裁切线"),("check","cut.registration","默认输出套准标"),("check","cut.color_bar","默认输出 CMYK 色标"),("double","cut.mark_length","裁切线长度",1,30," mm"),("double","cut.mark_offset","裁切线偏移",0,30," mm"))),
)


def load_system_settings(db):
    values=deepcopy(DEFAULT_SYSTEM_SETTINGS); saved=db.get_setting(SETTING_KEY,{}) if db is not None else {}
    if isinstance(saved,dict): values.update(saved)
    return values


def apply_system_settings(host, values, *, apply_theme=True):
    def checked(obj,name,key):
        w=getattr(obj,name,None)
        if w is not None and hasattr(w,"setChecked"): w.setChecked(bool(values.get(key)))
    def number(obj,name,key):
        w=getattr(obj,name,None)
        if w is not None and hasattr(w,"setValue"): w.setValue(float(values.get(key,0)))
    if apply_theme and hasattr(host,"apply_ui_theme"): host.apply_ui_theme(values.get("ui.theme","ocean"))
    app=QApplication.instance(); family=str(values.get("ui.font_family") or ""); size=int(values.get("ui.font_size",10))
    if app is not None and family: app.setFont(QFont(family,size))
    number(host,"bleed","general.default_bleed"); number(host,"default_quantity","general.default_quantity")
    checked(host,"crop_marks","cut.crop_marks"); checked(host,"registration_marks","cut.registration")
    checked(host,"sheet_info","general.add_labels"); checked(host,"barcode_enabled","qr.enabled")
    checked(host,"preflight_fonts","preflight.fonts"); checked(host,"preflight_colors","preflight.colors"); checked(host,"preflight_images","preflight.images"); checked(host,"preflight_pdfx","preflight.pdfx")
    number(host,"min_image_dpi","preflight.min_dpi"); number(host,"mark_len","cut.mark_length"); number(host,"mark_offset","cut.mark_offset")
    workspace=getattr(host,"professional_workspace",None); single=getattr(workspace,"single_page",None)
    if single is not None:
        number(single,"bleed","general.default_bleed"); number(single,"snap","placement.snap"); number(single,"gripper","press.gripper")
        checked(single,"auto_rotate","placement.auto_rotate"); checked(single,"crop_marks","cut.crop_marks"); checked(single,"registration_marks","cut.registration"); checked(single,"color_bar","cut.color_bar"); checked(single,"info_text","general.add_labels")
        if hasattr(single,"canvas"): single.canvas.snap_mm=float(values.get("placement.snap",1)); single.canvas.set_grid_visible(not bool(values.get("general.hide_template_grid",False)))
    if workspace is not None:
        for mode in (getattr(workspace,"book",None),getattr(workspace,"box",None)): checked(mode,"color_bar","cut.color_bar") if mode is not None else None
        book=getattr(workspace,"book",None)
        if book is not None:
            number(book,"safe_inset","signature.safe_inset"); number(book,"creep","book.creep"); checked(book,"fold_lines","signature.fold_lines"); checked(book,"auto_spine","signature.auto_spine")
        box=getattr(workspace,"box",None)
        if box is not None: number(box,"bleed","die.bleed")
        bar=getattr(workspace,"production_bar",None)
        if bar is not None:
            for combo,key in ((bar.paper,"paper.default"),(bar.machine,"press.default")):
                i=combo.findText(str(values.get(key,""))); combo.setCurrentIndex(i if i>=0 else combo.currentIndex())
            bar.gripper.setValue(float(values.get("press.gripper",10))); bar.tail.setValue(float(values.get("press.tail",3))); bar.speed.setValue(int(values.get("press.speed",10500)))


class SystemSettingsDialog(QDialog):
    def __init__(self, db, host=None, parent=None):
        super().__init__(parent or host); self.db=db; self.host=host; self.controls={}; self.page_keys=[]
        self.setWindowTitle("系统设置"); self.resize(980,700); self.setMinimumSize(820,600)
        root=QVBoxLayout(self); split=QSplitter(Qt.Horizontal); root.addWidget(split,1)
        self.categories=QListWidget(); self.categories.setObjectName("SettingsCategories"); self.categories.setFixedWidth(185); split.addWidget(self.categories)
        right=QFrame(); right.setObjectName("SettingsPanel"); right_l=QVBoxLayout(right); self.page_title=QLabel(); self.page_title.setObjectName("SettingsTitle"); right_l.addWidget(self.page_title)
        self.stack=QStackedWidget(); right_l.addWidget(self.stack,1)
        restore_row=QHBoxLayout(); restore_page=QPushButton("恢复本页默认"); restore_all=QPushButton("恢复全部默认"); restore_page.clicked.connect(self.restore_page); restore_all.clicked.connect(self.restore_all); restore_row.addWidget(restore_page); restore_row.addWidget(restore_all); restore_row.addStretch(); right_l.addLayout(restore_row)
        split.addWidget(right); split.setStretchFactor(1,1)
        for title,specs in PAGE_SPECS: self._add_page(title,specs)
        self.categories.currentRowChanged.connect(self._select_page); self.categories.setCurrentRow(0)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel|QDialogButtonBox.Apply); buttons.accepted.connect(self._accept); buttons.rejected.connect(self.reject); buttons.button(QDialogButtonBox.Apply).clicked.connect(self._save); root.addWidget(buttons)
        self.load_values(load_system_settings(db))

    def _widget(self,spec):
        kind,key,label,*args=spec; default=DEFAULT_SYSTEM_SETTINGS[key]
        if kind=="check": w=QCheckBox(); w.setChecked(bool(default))
        elif kind=="text": w=QLineEdit(str(default))
        elif kind=="font": w=QFontComboBox(); w.setCurrentFont(QFont(str(default)))
        elif kind in ("combo","combo_data"):
            w=QComboBox()
            if kind=="combo": w.addItems(args[0])
            else:
                for data,text in args[0]: w.addItem(text,data)
        elif kind=="spin": w=QSpinBox(); w.setRange(int(args[0]),int(args[1])); w.setSuffix(str(args[2])); w.setValue(int(default))
        elif kind=="double": w=QDoubleSpinBox(); w.setRange(float(args[0]),float(args[1])); w.setDecimals(2); w.setSuffix(str(args[2])); w.setValue(float(default))
        self.controls[key]=w; return label,w,key

    def _add_page(self,title,specs):
        self.categories.addItem("›  "+title); scroll=QScrollArea(); scroll.setWidgetResizable(True); body=QWidget(); form=QFormLayout(body); keys=[]
        form.setContentsMargins(18,14,24,18); form.setHorizontalSpacing(20); form.setVerticalSpacing(10)
        for spec in specs:
            label,w,key=self._widget(spec); form.addRow(label,w); keys.append(key)
        form.addRow(QLabel("")); scroll.setWidget(body); self.stack.addWidget(scroll); self.page_keys.append(keys)

    def _select_page(self,index):
        if index<0:return
        self.stack.setCurrentIndex(index); self.page_title.setText(PAGE_SPECS[index][0])

    def _get(self,key):
        w=self.controls[key]
        if isinstance(w,QCheckBox): return w.isChecked()
        if isinstance(w,(QSpinBox,QDoubleSpinBox)): return w.value()
        if isinstance(w,QFontComboBox): return w.currentFont().family()
        if isinstance(w,QComboBox): return w.currentData() if w.currentData() is not None else w.currentText()
        return w.text()

    def _set(self,key,value):
        w=self.controls[key]
        if isinstance(w,QCheckBox): w.setChecked(bool(value))
        elif isinstance(w,QSpinBox): w.setValue(int(value))
        elif isinstance(w,QDoubleSpinBox): w.setValue(float(value))
        elif isinstance(w,QFontComboBox): w.setCurrentFont(QFont(str(value)))
        elif isinstance(w,QComboBox):
            i=w.findData(value); i=i if i>=0 else w.findText(str(value)); w.setCurrentIndex(i if i>=0 else 0)
        else: w.setText(str(value))

    def values(self): return {key:self._get(key) for key in self.controls}
    def load_values(self,values):
        for key in self.controls: self._set(key,values.get(key,DEFAULT_SYSTEM_SETTINGS[key]))
    def restore_page(self):
        index=self.stack.currentIndex()
        for key in self.page_keys[index]: self._set(key,DEFAULT_SYSTEM_SETTINGS[key])
    def restore_all(self): self.load_values(DEFAULT_SYSTEM_SETTINGS)
    def _save(self):
        values=self.values(); self.db.set_setting(SETTING_KEY,values)
        if self.host is not None: apply_system_settings(self.host,values)
        return values
    def _accept(self): self._save(); self.accept()
