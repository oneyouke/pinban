from __future__ import annotations

import base64
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

PRODUCT_ID = "com.yourcompany.desktopimposer.pro"
SCHEMA_VERSION = 1
DEFAULT_FEATURES = ["core", "preflight", "hotfolder", "variable_data", "queue"]


def canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_payload(payload: dict, private_key_pem: bytes) -> str:
    key = serialization.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("所选私钥不是 Ed25519 私钥")
    return base64.b64encode(key.sign(canonical_bytes(payload))).decode("ascii")


class LicenseGenerator(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Desktop Imposer Pro · 许可证生成器")
        self.resize(680, 520)
        self.private_key_path = ""

        root = QWidget(self)
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)

        title = QLabel("商业许可证生成器")
        title.setStyleSheet("font-size:20px;font-weight:700")
        outer.addWidget(title)
        note = QLabel("私钥只在本机读取，不会写入许可证文件。客户机只需要安装生成的 .lic 文件。")
        note.setWordWrap(True)
        outer.addWidget(note)

        form = QFormLayout()
        self.private_edit = QLineEdit(); self.private_edit.setReadOnly(True)
        private_row = QWidget(); private_layout = QHBoxLayout(private_row); private_layout.setContentsMargins(0,0,0,0)
        private_btn = QPushButton("选择私钥…"); private_btn.clicked.connect(self.choose_private)
        private_layout.addWidget(self.private_edit, 1); private_layout.addWidget(private_btn)
        form.addRow("Ed25519 私钥", private_row)

        self.license_id = QLineEdit(f"LIC-{uuid.uuid4().hex[:12].upper()}")
        self.customer = QLineEdit()
        self.customer.setPlaceholderText("例如：某某印刷有限公司")
        self.edition = QComboBox(); self.edition.addItems(["Pro", "Enterprise", "Commercial"])
        self.machine = QLineEdit(); self.machine.setPlaceholderText("留空=不绑定机器；绑定时粘贴客户机指纹")

        self.permanent = QCheckBox("永久授权")
        self.permanent.setChecked(True)
        self.expires = QDateTimeEdit(QDateTime.currentDateTime().addYears(1))
        self.expires.setCalendarPopup(True)
        self.expires.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.expires.setEnabled(False)
        self.permanent.toggled.connect(lambda checked: self.expires.setEnabled(not checked))

        form.addRow("许可证编号", self.license_id)
        form.addRow("客户", self.customer)
        form.addRow("版本", self.edition)
        form.addRow("本机指纹", self.machine)
        form.addRow("", self.permanent)
        form.addRow("到期时间", self.expires)

        feature_box = QWidget(); fl = QHBoxLayout(feature_box); fl.setContentsMargins(0,0,0,0)
        self.feature_checks = []
        for feature in DEFAULT_FEATURES:
            cb = QCheckBox(feature); cb.setChecked(True); fl.addWidget(cb); self.feature_checks.append(cb)
        form.addRow("功能", feature_box)
        outer.addLayout(form)

        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet("background:#f4f6f8;padding:10px;border-radius:6px")
        outer.addWidget(self.summary)

        buttons = QHBoxLayout(); buttons.addStretch()
        new_id_btn = QPushButton("新编号"); new_id_btn.clicked.connect(self.new_id)
        create_btn = QPushButton("生成许可证…"); create_btn.clicked.connect(self.generate)
        create_btn.setStyleSheet("font-weight:700")
        buttons.addWidget(new_id_btn); buttons.addWidget(create_btn)
        outer.addLayout(buttons)

        for w in [self.license_id, self.customer, self.machine]:
            w.textChanged.connect(self.refresh_summary)
        self.edition.currentTextChanged.connect(self.refresh_summary)
        self.permanent.toggled.connect(self.refresh_summary)
        self.expires.dateTimeChanged.connect(self.refresh_summary)
        for cb in self.feature_checks:
            cb.toggled.connect(self.refresh_summary)
        self.refresh_summary()

    def choose_private(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择 Ed25519 私钥", "", "PEM 私钥 (*.pem *.key);;所有文件 (*)")
        if path:
            try:
                key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
                if not isinstance(key, Ed25519PrivateKey):
                    raise TypeError("不是 Ed25519 私钥")
                self.private_key_path = path
                self.private_edit.setText(path)
            except Exception as exc:
                QMessageBox.critical(self, "私钥无效", str(exc))

    def new_id(self) -> None:
        self.license_id.setText(f"LIC-{uuid.uuid4().hex[:12].upper()}")

    def expiry_text(self) -> str:
        if self.permanent.isChecked():
            return ""
        dt = self.expires.dateTime().toPython()
        if dt.tzinfo is None:
            dt = dt.astimezone()
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")

    def features(self) -> list[str]:
        return [cb.text() for cb in self.feature_checks if cb.isChecked()]

    def refresh_summary(self) -> None:
        expiry = "永久" if self.permanent.isChecked() else self.expires.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        machine = self.machine.text().strip() or "不绑定机器"
        self.summary.setText(
            f"客户：{self.customer.text().strip() or '-'}\n"
            f"许可证：{self.license_id.text().strip() or '-'} · {self.edition.currentText()}\n"
            f"到期：{expiry}\n机器：{machine}\n功能：{', '.join(self.features()) or '无'}"
        )

    def generate(self) -> None:
        try:
            if not self.private_key_path:
                raise ValueError("请先选择 Ed25519 私钥")
            license_id = self.license_id.text().strip()
            customer = self.customer.text().strip()
            if not license_id:
                raise ValueError("许可证编号不能为空")
            if not customer:
                raise ValueError("客户不能为空")
            features = self.features()
            if not features:
                raise ValueError("至少选择一个授权功能")

            payload = {
                "schema_version": SCHEMA_VERSION,
                "product_id": PRODUCT_ID,
                "license_id": license_id,
                "customer": customer,
                "edition": self.edition.currentText(),
                "issued_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "expires_at": self.expiry_text(),
                "machine_fingerprint": self.machine.text().strip(),
                "features": features,
            }
            signature = sign_payload(payload, Path(self.private_key_path).read_bytes())
            doc = {"payload": payload, "signature": signature}

            default_name = f"{license_id}.lic"
            path, _ = QFileDialog.getSaveFileName(self, "保存许可证", default_name, "许可证 (*.lic);;JSON (*.json)")
            if not path:
                return
            if not Path(path).suffix:
                path += ".lic"
            Path(path).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            QMessageBox.information(self, "生成成功", f"许可证已生成：\n{path}\n\n可在客户端“商业许可证 → 安装许可证…”中导入。")
        except Exception as exc:
            QMessageBox.critical(self, "生成失败", str(exc))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Imposer License Generator")
    win = LicenseGenerator(); win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
