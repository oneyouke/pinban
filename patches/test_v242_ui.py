import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtWidgets import QApplication
from page_canvas import PageCanvasWidget, PageInfo, PageItem

app=QApplication.instance() or QApplication([])
w=PageCanvasWidget()
assert abs(w.canvas.sheet.rect().width()-650)<0.01
assert abs(w.canvas.sheet.rect().height()-450)<0.01

info=PageInfo('dummy.pdf',0,72*100/25.4,72*50/25.4)
a=w.canvas.add_page(info)
b=w.canvas.add_page(info)
c=w.canvas.add_page(info)
for x in (a,b,c): x.setSelected(True)

w.canvas.snap_mm=1.0
w.canvas.set_selected_position(12.4,18.6)
assert abs(a.x()-12.0)<0.01 and abs(a.y()-19.0)<0.01
w.canvas.undo_stack.undo()
w.canvas.undo_stack.redo()
assert abs(a.x()-12.0)<0.01 and abs(a.y()-19.0)<0.01

b.setPos(50,30); c.setPos(100,40)
w.canvas.align_left()
assert abs(a.x()-12.0)<0.01 and abs(b.x()-12.0)<0.01 and abs(c.x()-12.0)<0.01

b.setPos(50,30); c.setPos(100,40)
w.canvas.distribute_horizontal()
xs=sorted(round(x.x(),2) for x in (a,b,c))
assert xs[0] <= xs[1] <= xs[2]

w.canvas.center_horizontal()
assert all(0 <= x.x() <= 650 for x in (a,b,c))
w.canvas.center_vertical()
assert all(0 <= x.y() <= 450 for x in (a,b,c))

w.canvas.set_sheet(700,500,5)
assert abs(w.canvas.sheet.rect().width()-700)<0.01
assert abs(w.canvas.bleed_box.rect().x()-5)<0.01
assert abs(w.canvas.bleed_box.rect().width()-690)<0.01
print('V2.4.2 UI canvas tests passed')
