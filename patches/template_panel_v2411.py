from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox,
    QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from template_store import load_library, upsert_template, delete_template, get_template, export_template, import_template


class TemplateManagerPanel(QWidget):
    def __init__(self, capture_workspace, apply_workspace, parent=None):
        super().__init__(parent)
        self.capture_workspace = capture_workspace
        self.apply_workspace = apply_workspace
        root = QHBoxLayout(self)

        left = QVBoxLayout()
        self.list = QListWidget(); self.list.currentTextChanged.connect(self._load_meta)
        left.addWidget(QLabel('生产模板'))
        left.addWidget(self.list, 1)
        refresh = QPushButton('刷新'); refresh.clicked.connect(self.refresh)
        left.addWidget(refresh)
        root.addLayout(left, 1)

        right = QVBoxLayout()
        self.name = QLineEdit(); self.name.setPlaceholderText('模板名称')
        self.category = QLineEdit(); self.category.setPlaceholderText('分类，例如：名片 / 画册 / 标签')
        self.notes = QTextEdit(); self.notes.setPlaceholderText('备注、工艺说明、适用机器等')
        right.addWidget(QLabel('名称')); right.addWidget(self.name)
        right.addWidget(QLabel('分类')); right.addWidget(self.category)
        right.addWidget(QLabel('备注')); right.addWidget(self.notes, 1)

        row1 = QHBoxLayout()
        save = QPushButton('保存/覆盖当前模板'); save.clicked.connect(self.save_current)
        apply_btn = QPushButton('应用所选模板'); apply_btn.clicked.connect(self.apply_current)
        delete_btn = QPushButton('删除所选模板'); delete_btn.clicked.connect(self.delete_current)
        row1.addWidget(save); row1.addWidget(apply_btn); row1.addWidget(delete_btn)
        right.addLayout(row1)

        row2 = QHBoxLayout()
        export_btn = QPushButton('导出模板 JSON'); export_btn.clicked.connect(self.export_current)
        import_btn = QPushButton('导入模板 JSON'); import_btn.clicked.connect(self.import_file)
        row2.addWidget(export_btn); row2.addWidget(import_btn); row2.addStretch()
        right.addLayout(row2)

        note = QLabel('模板保存工作区参数和源 PDF 引用，不复制 PDF 文件内容。应用模板后可继续编辑、预检并走原矢量生产 PDF 输出链路。')
        note.setWordWrap(True); right.addWidget(note)
        root.addLayout(right, 2)
        self.refresh()

    def refresh(self):
        selected = self.list.currentItem().text() if self.list.currentItem() else ''
        self.list.clear()
        for row in load_library().get('templates', []):
            self.list.addItem(str(row.get('name') or ''))
        matches = self.list.findItems(selected, 0) if selected else []
        if matches: self.list.setCurrentItem(matches[0])

    def _load_meta(self, name):
        row = get_template(name) if name else None
        if not row: return
        self.name.setText(str(row.get('name') or ''))
        self.category.setText(str(row.get('category') or ''))
        self.notes.setPlainText(str(row.get('notes') or ''))

    def save_current(self):
        name = self.name.text().strip()
        if not name:
            QMessageBox.information(self, '模板', '请输入模板名称。'); return
        workspace = self.capture_workspace()
        upsert_template(name, workspace, category=self.category.text(), notes=self.notes.toPlainText())
        self.refresh()
        QMessageBox.information(self, '模板', f'模板已保存：{name}')

    def apply_current(self):
        item = self.list.currentItem()
        if item is None:
            QMessageBox.information(self, '模板', '请选择模板。'); return
        row = get_template(item.text())
        if row is None: return
        self.apply_workspace(row.get('workspace') or {})
        QMessageBox.information(self, '模板', f'已应用模板：{item.text()}')

    def delete_current(self):
        item = self.list.currentItem()
        if item is None: return
        if delete_template(item.text()): self.refresh()

    def export_current(self):
        item = self.list.currentItem()
        if item is None:
            QMessageBox.information(self, '模板', '请选择模板。'); return
        path, _ = QFileDialog.getSaveFileName(self, '导出模板', item.text() + '.json', 'JSON (*.json)')
        if not path: return
        export_template(item.text(), path)

    def import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, '导入模板', '', 'JSON (*.json)')
        if not path: return
        try:
            row = import_template(path, overwrite=True)
        except Exception as exc:
            QMessageBox.critical(self, '模板导入失败', str(exc)); return
        self.refresh(); self.name.setText(str(row.get('name') or ''))
