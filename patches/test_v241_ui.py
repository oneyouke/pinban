import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication
from page_canvas import PageCanvasWidget, PageInfo, PageItem

app = QApplication.instance() or QApplication([])
w = PageCanvasWidget()
assert w.canvas is not None
assert w.list is not None
info = PageInfo('sample.pdf', 0, 595.0, 842.0)
item = w.canvas.add_page(info)
item.setSelected(True)
w.canvas.rotate_selected()
assert int(item.rotation()) == 90
w.canvas.toggle_lock_selected()
assert item.locked is True
w.canvas.toggle_lock_selected()
assert item.locked is False
w.canvas.delete_selected()
assert item.scene() is None
print('V2.4.1 page canvas UI smoke test passed')
