from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import tempfile

SCHEMA_VERSION = 1


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def default_template_library_path() -> Path:
    base = os.environ.get('APPDATA')
    root = Path(base) if base else (Path.home() / '.desktop_imposer_pro')
    return root / 'DesktopImposerPro' / 'templates.json' if base else root / 'templates.json'


def _empty_library():
    return {'schema_version': SCHEMA_VERSION, 'templates': []}


def load_library(path: str | Path | None = None):
    path = Path(path) if path else default_template_library_path()
    if not path.exists():
        return _empty_library()
    data = json.loads(path.read_text(encoding='utf-8'))
    if int(data.get('schema_version', 0)) != SCHEMA_VERSION:
        raise ValueError('不支持的模板库版本')
    if not isinstance(data.get('templates'), list):
        raise ValueError('模板库结构无效')
    return data


def save_library(data, path: str | Path | None = None):
    path = Path(path) if path else default_template_library_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(data)
    payload['schema_version'] = SCHEMA_VERSION
    fd, tmp_name = tempfile.mkstemp(prefix='templates-', suffix='.partial.json', dir=str(path.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
        with tmp.open('r+b') as f:
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
    return path


def upsert_template(name: str, workspace: dict, *, category: str = '', notes: str = '', path: str | Path | None = None):
    name = str(name or '').strip()
    if not name:
        raise ValueError('模板名称不能为空')
    lib = load_library(path)
    now = utc_now()
    row = None
    for item in lib['templates']:
        if str(item.get('name')) == name:
            row = item
            break
    if row is None:
        row = {'name': name, 'created_at': now}
        lib['templates'].append(row)
    row.update({
        'name': name,
        'category': str(category or ''),
        'notes': str(notes or ''),
        'updated_at': now,
        'workspace': deepcopy(workspace or {}),
    })
    lib['templates'].sort(key=lambda x: (str(x.get('category') or ''), str(x.get('name') or '')))
    save_library(lib, path)
    return deepcopy(row)


def delete_template(name: str, path: str | Path | None = None):
    lib = load_library(path)
    before = len(lib['templates'])
    lib['templates'] = [x for x in lib['templates'] if str(x.get('name')) != str(name)]
    if len(lib['templates']) == before:
        return False
    save_library(lib, path)
    return True


def get_template(name: str, path: str | Path | None = None):
    for row in load_library(path)['templates']:
        if str(row.get('name')) == str(name):
            return deepcopy(row)
    return None


def export_template(name: str, destination: str | Path, path: str | Path | None = None):
    row = get_template(name, path)
    if row is None:
        raise KeyError(name)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({'schema_version': SCHEMA_VERSION, 'template': row}, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    return destination


def import_template(source: str | Path, path: str | Path | None = None, *, overwrite: bool = True):
    data = json.loads(Path(source).read_text(encoding='utf-8'))
    row = data.get('template') or {}
    name = str(row.get('name') or '').strip()
    if not name:
        raise ValueError('模板文件缺少名称')
    if not overwrite and get_template(name, path) is not None:
        raise FileExistsError(name)
    return upsert_template(name, row.get('workspace') or {}, category=row.get('category') or '', notes=row.get('notes') or '', path=path)
