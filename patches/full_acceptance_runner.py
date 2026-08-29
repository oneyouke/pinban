from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "release"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

MANUAL_CHECKS = [
    {"id": "import-eps-tiff", "area": "文件导入", "item": "PDF/TIFF/EPS 实际样本不丢页、不花版", "status": "manual_required", "reason": "需真实生产样本及转换 Provider"},
    {"id": "page-edit", "area": "页面编辑", "item": "删除/新增空白页/单页旋转/单页出血修改", "status": "manual_required", "reason": "当前版本尚未完成完整页级编辑器"},
    {"id": "nested-imposition", "area": "嵌套拼版", "item": "小版再拼大版，双层出血和标记校验", "status": "manual_required", "reason": "需具体嵌套工作流样本验收"},
    {"id": "booklet-paper-fold", "area": "书刊折手", "item": "8P/16P/20P 骑马钉纸样折叠页码连续", "status": "manual_required", "reason": "纸质折叠是最终页序验收"},
    {"id": "perfect-bind-paper", "area": "书刊折手", "item": "16P/32P 胶装/锁线分帖、爬移、书脊纸样", "status": "manual_required", "reason": "需实际纸张厚度和折页工艺"},
    {"id": "turn-tumble", "area": "正反版", "item": "自翻版/套翻版印刷关系现场核对", "status": "manual_required", "reason": "需印刷机翻纸方式与现场基准"},
    {"id": "3d-fold", "area": "书刊折手", "item": "3D 折页预览", "status": "not_implemented", "reason": "当前版本未实现真正 3D 折页预览"},
    {"id": "marks-measure", "area": "印刷标记", "item": "裁切线/套准/色标/灰梯/帖码/版信息/模切标记位置毫米级测量", "status": "manual_required", "reason": "需 Acrobat/PitStop 测量输出 PDF"},
    {"id": "spot-preserve", "area": "专色工艺", "item": "CMYK+专色/白墨/烫金通道保持及套准", "status": "manual_required", "reason": "需真实含 Separation/DeviceN 的生产 PDF 与分色预览"},
    {"id": "pdfx", "area": "输出", "item": "PDF/X-1a 认证输出", "status": "provider_required", "reason": "内置预检不是认证 PDF/X 引擎"},
    {"id": "separation-ps-tiff", "area": "输出", "item": "分色 PDF / PS / TIFF 输出", "status": "provider_required", "reason": "需要 RIP/Provider 级分色输出"},
    {"id": "rip", "area": "RIP/CTP", "item": "RIP 解析无错误、无错位、无丢内容", "status": "external_required", "reason": "必须连接实际 RIP"},
    {"id": "ctp", "area": "RIP/CTP", "item": "CTP 样版/数码打样套准与裁切线验证", "status": "external_required", "reason": "必须使用实际设备或打样系统"},
]


def run_script(path: Path) -> dict:
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-B", path.name],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        errors="replace",
        env={**os.environ, "QT_QPA_PLATFORM": os.environ.get("QT_QPA_PLATFORM", "offscreen")},
    )
    elapsed = time.perf_counter() - started
    return {
        "name": path.name,
        "status": "pass" if proc.returncode == 0 else "fail",
        "returncode": proc.returncode,
        "seconds": round(elapsed, 3),
        "stdout": proc.stdout[-12000:],
        "stderr": proc.stderr[-12000:],
    }


def main() -> int:
    candidates = sorted(
        p for p in ROOT.glob("test_*.py")
        if p.name not in {"test_full_acceptance.py"}
    )
    # install_smoke_test.py does not follow test_*.py naming but is part of release acceptance.
    install_smoke = ROOT / "install_smoke_test.py"
    if install_smoke.exists():
        candidates.append(install_smoke)

    results = []
    for path in candidates:
        print(f"[ACCEPTANCE] running {path.name}", flush=True)
        result = run_script(path)
        results.append(result)
        print(f"[ACCEPTANCE] {path.name}: {result['status']} ({result['seconds']}s)", flush=True)

    failed = [r for r in results if r["status"] == "fail"]
    passed = [r for r in results if r["status"] == "pass"]
    payload = {
        "schema_version": 1,
        "app": "Desktop Imposer Pro",
        "acceptance_version": "2.3.4",
        "automated": {
            "total": len(results),
            "passed": len(passed),
            "failed": len(failed),
            "results": results,
        },
        "manual_external": MANUAL_CHECKS,
        "policy": "Only automated PASS items are machine-verified. Manual/provider/external items are never promoted to PASS by CI.",
    }
    (REPORT_DIR / "full-acceptance-report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Desktop Imposer Pro V2.3.4 全量功能验收报告",
        "",
        f"- 自动测试：{len(results)}",
        f"- 通过：{len(passed)}",
        f"- 失败：{len(failed)}",
        "",
        "## 自动化测试",
        "",
        "| 测试脚本 | 状态 | 秒 |",
        "|---|---:|---:|",
    ]
    for r in results:
        lines.append(f"| {r['name']} | {'PASS' if r['status']=='pass' else 'FAIL'} | {r['seconds']} |")
    lines += ["", "## 人工 / Provider / 设备验收", "", "| 模块 | 验收项 | 状态 | 原因 |", "|---|---|---|---|"]
    for item in MANUAL_CHECKS:
        lines.append(f"| {item['area']} | {item['item']} | {item['status']} | {item['reason']} |")
    (REPORT_DIR / "full-acceptance-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if failed:
        print("\n[ACCEPTANCE] FAILED scripts:")
        for r in failed:
            print(f"- {r['name']} (exit {r['returncode']})")
            if r["stderr"]:
                print(r["stderr"][-3000:])
        return 1
    print(f"[ACCEPTANCE] PASS: {len(passed)}/{len(results)} automated scripts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
