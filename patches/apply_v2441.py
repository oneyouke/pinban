from __future__ import annotations

import os
import py_compile
from pathlib import Path


root = Path(os.environ.get("APP_ROOT", Path(__file__).resolve().parents[1] / "build-src" / "Desktop-Imposer-Pro-V2.2"))
patch_root = Path(__file__).resolve().parent


def replace(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"V2.4.41 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


eula = """Desktop Imposer Pro 最终用户许可协议

生效日期：2026年9月1日

重要提示：请在安装或使用本软件前仔细阅读本协议。安装、激活或使用本软件，即表示用户同意接受本协议约束。本协议为商业发布候选文本，许可方应在首次正式销售前结合实际经营主体、销售地区和交易方式完成法律审阅。

一、许可方与联系方式
本软件由“云游客科技”提供许可。签约经营主体、注册地址及开票信息以用户购买时的订单、合同或发票所载信息为准。
技术支持及许可联系邮箱：3120085127@qq.com。

二、软件与授权
1. “软件”指 Desktop Imposer Pro 桌面拼版软件及其随附文档、更新和补丁。
2. 试用授权默认有效期为十四日，仅供评估，不得绕过试用限制。
3. 付费授权的期限、设备数量、用户数量、可用版本及维护服务以购买凭证或独立合同为准。
4. 在用户按约付款并遵守本协议的前提下，许可方授予用户有限的、非独占的、不可转让的使用许可。

三、使用限制
除适用法律明确允许外，用户不得转售、出租、出借、再许可、公开分发软件，不得规避授权控制，不得提供授权密钥给未获许可的第三方，也不得将软件用于侵犯他人知识产权或违反法律法规的活动。对为实现互操作性而依法享有的强制性权利，本协议不予排除。

四、客户文件与数据
软件默认在本地处理PDF、图片、项目参数和生产信息。软件可在本地保存项目路径、拼版参数、队列元数据、日志、文件哈希和许可证状态。支持包按设计不包含客户原稿和生产数据库，但用户在对外发送前仍应自行检查。隐私与数据处理细节见随软件提供的《隐私与数据流说明》。

五、更新与支持
更新、升级和技术支持的期限及范围以购买方案为准。许可方可以发布安全修复、兼容性更新或功能升级；重大版本升级可能需要另行购买。用户应在生产环境部署更新前完成备份和验证。

六、印刷生产责任
软件用于辅助拼版和印前风险检查。用户应对成品尺寸、页序、正背关系、出血、裁切线、专色、叠印、字体、图像分辨率、颜色管理、刀模和实际RIP输出进行打样与审批。除非另行集成并许可经过标准认证的专业引擎，软件内置预检不构成ISO PDF/X认证、ICC转换、透明度扁平化、陷印或RIP等价验证。

七、知识产权与第三方组件
软件及其自有代码、界面、文档和商标权益归许可方或相应权利人所有。软件包含若干第三方组件，其许可证和声明见 THIRD_PARTY_NOTICES.md；相关第三方权利不因本协议而改变。

八、有限保证
许可方将以合理商业努力确保软件基本符合随附文档，但不保证软件完全无错误、不中断或适合所有设备及生产流程。用户应维护原始文件、项目和输出文件的独立备份，并在批量生产前完成校样。

九、责任限制
在适用法律允许的最大范围内，任何一方均不对间接损失、利润损失、停产损失或数据丢失承担责任。许可方在本协议项下的累计责任原则上不超过引发索赔事项发生前十二个月内用户为相关软件授权实际支付的费用；因故意、重大过失或法律不得限制的责任除外。

十、终止
用户严重违反授权范围、侵犯知识产权或拒不支付到期费用时，许可方可以终止相关授权。授权终止后，用户应停止使用并删除无权继续保留的软件副本。关于知识产权、责任限制和争议解决的条款在终止后继续有效。

十一、适用法律与争议解决
本协议适用中华人民共和国大陆地区法律。争议应先友好协商；协商不成的，任一方可向购买凭证所载许可方经营主体住所地有管辖权的人民法院提起诉讼。消费者依法享有的强制性权利不受影响。

十二、完整协议
本协议、购买凭证、隐私说明及双方签署的补充协议共同构成双方关于软件授权的完整约定。补充协议与本协议不一致时，以双方签署的补充协议为准。
"""

notices = """# 第三方软件声明

Desktop Imposer Pro 使用下列第三方组件。每次正式构建均应从实际打包环境生成并归档 SBOM，同时随安装包保留对应版本的完整许可证文本。本清单不是第三方许可法律意见。

- **Qt for Python / PySide6** — LGPLv3/GPLv3 或 Qt Commercial。闭源商业发行必须选择并落实相应许可路径，包括适用时的动态链接、替换库和声明义务。
- **PyMuPDF** — AGPL 或 Artifex 商业许可。闭源商业发行前必须取得适用的商业许可，或移除/替换该组件并重新验证PDF缩略图功能。
- **pypdf** — BSD-3-Clause。
- **ReportLab** — BSD风格许可证；以最终打包版本附带文本为准。
- **Pillow** — HPND许可证。
- **openpyxl** — MIT许可证。
- **cryptography** — Apache-2.0 OR BSD-3-Clause。
- **Shapely** — BSD-3-Clause。
- **Python及标准库** — Python Software Foundation许可证及其随附声明。
- **SQLite** — Public Domain。
- **PyInstaller** — GPLv2及允许商业应用打包的特别例外；仅作为构建依赖使用。

商业发行负责人必须保存：依赖锁定记录、SBOM、完整许可证文本、Qt许可路径确认、PyMuPDF商业许可凭证或替代组件验收记录。
"""

product = root / "product.py"
replace(product, 'APP_ID = "com.yourcompany.desktopimposer.pro"', 'APP_ID = "com.yunyouke.desktopimposer.pro"', "commercial app id")
replace(product, 'APP_VERSION = "2.4.40"', 'APP_VERSION = "2.4.41"', "version")

for name in ("pyproject.toml", "installer_nsis.nsi"):
    path = root / name
    replace(path, "2.4.40", "2.4.41", f"{name} version")

(root / "EULA_TEMPLATE.txt").write_text(eula, encoding="utf-8")
(root / "EULA_NSIS.txt").write_text(eula, encoding="utf-16")
(root / "THIRD_PARTY_NOTICES.md").write_text(notices, encoding="utf-8")

sbom = root / "generate_sbom.py"
replace(
    sbom,
    'wanted = {"PySide6", "pypdf", "reportlab", "Pillow", "openpyxl", "cryptography"}',
    'wanted = {"PySide6", "pypdf", "reportlab", "Pillow", "openpyxl", "cryptography", "shapely", "PyMuPDF"}',
    "complete runtime SBOM",
)

gate = root / "release_gate.py"
replace(
    gate,
    'for required in ("PySide6", "pypdf", "reportlab", "Pillow", "openpyxl", "cryptography"):',
    'for required in ("PySide6", "pypdf", "reportlab", "Pillow", "openpyxl", "cryptography", "shapely", "PyMuPDF"):',
    "complete dependency gate",
)
insert = '''\nfor component in ("PySide6", "pypdf", "ReportLab", "Pillow", "openpyxl", "cryptography", "Shapely", "PyMuPDF"):\n    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")\n    if component.lower() not in notices.lower():\n        errors.append(f"第三方声明缺少 {component}")\n\nif not re.fullmatch(r"com\\.[a-z0-9.-]+", __import__("product").APP_ID):\n    errors.append("APP_ID 必须是有效的反向域名格式")\n'''
marker = '\nfor name in ("THIRD_PARTY_NOTICES.md", "EULA_TEMPLATE.txt", "COMMERCIAL_RELEASE_CHECKLIST.md"):'
replace(gate, marker, insert + marker, "license notice gate")

test_target = root / "test_v2441_commercial_release.py"
test_target.write_text((patch_root / "test_v2441_commercial_release.py").read_text(encoding="utf-8"), encoding="utf-8")
for name in ("product.py", "generate_sbom.py", "release_gate.py", "test_v2441_commercial_release.py"):
    py_compile.compile(str(root / name), doraise=True)

(root / "V2441_COMMERCIAL_RELEASE.md").write_text(
    "# V2.4.41 商业发布加固\n\n正式产品ID、中文EULA、完整运行时SBOM范围、第三方许可检查和可签名发布入口。\n",
    encoding="utf-8",
)
print("V2.4.41 commercial release hardening integrated")
