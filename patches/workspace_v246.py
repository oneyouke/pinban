from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import tempfile

SCHEMA_VERSION = 1


@dataclass
class WorkspaceDocument:
    schema_version: int = SCHEMA_VERSION
    app_version: str = "2.4.6"
    page_canvas: dict | None = None
    print_marks: dict | None = None

    def to_dict(self):
        return asdict(self)


def validate_workspace(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("工作区文件格式错误")
    if int(data.get("schema_version", 0)) != SCHEMA_VERSION:
        raise ValueError(f"不支持的工作区版本：{data.get('schema_version')}")
    for key in ("page_canvas", "print_marks"):
        value = data.get(key)
        if value is not None and not isinstance(value, dict):
            raise ValueError(f"{key} 必须是对象")
    return data


def save_workspace(path: str | Path, data: dict) -> Path:
    dst = Path(path).expanduser()
    if dst.suffix.lower() not in (".json", ".dipw"):
        dst = dst.with_suffix(".dipw")
    dst.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload["schema_version"] = SCHEMA_VERSION
    validate_workspace(payload)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dst.stem}.", suffix=".tmp", dir=str(dst.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        with tmp.open("r+b") as f:
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dst)
    finally:
        if tmp.exists():
            try: tmp.unlink()
            except Exception: pass
    return dst


def load_workspace(path: str | Path) -> dict:
    src = Path(path).expanduser()
    data = json.loads(src.read_text(encoding="utf-8"))
    return validate_workspace(data)
