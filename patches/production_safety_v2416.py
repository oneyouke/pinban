from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from layout_diagnostics import collect_layout_diagnostics


class ProductionSafetyError(RuntimeError):
    pass


def evaluate_manual_layout_gate(diagnostics: dict[str, Any] | None = None) -> dict[str, Any]:
    report = dict(diagnostics or collect_layout_diagnostics())
    status = str(report.get('status') or 'BLOCKED').upper()
    reasons = list(report.get('reasons') or report.get('errors') or [])
    ready = status == 'READY'
    if not ready and not reasons:
        reasons = ['生产引擎未通过手工版位契约安全检查']
    return {
        'ready': ready,
        'status': 'READY' if ready else 'BLOCKED',
        'reasons': reasons,
        'diagnostics': report,
    }


def require_manual_layout_safe(diagnostics_provider: Callable[[], dict[str, Any]] = collect_layout_diagnostics) -> dict[str, Any]:
    """Re-evaluate immediately before production output and fail closed."""
    gate = evaluate_manual_layout_gate(diagnostics_provider())
    if not gate['ready']:
        detail = '; '.join(str(x) for x in gate['reasons'])
        raise ProductionSafetyError('手工版位生产已阻止：' + detail)
    return gate


def build_diagnostics_export(app_version: str, diagnostics: dict[str, Any] | None = None) -> dict[str, Any]:
    gate = evaluate_manual_layout_gate(diagnostics)
    return {
        'schema_version': 1,
        'app_version': str(app_version),
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'manual_layout_gate': gate,
    }


def export_diagnostics_json(path: str | Path, app_version: str, diagnostics: dict[str, Any] | None = None) -> Path:
    target = Path(path).expanduser()
    if target.suffix.lower() != '.json':
        target = target.with_suffix('.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = build_diagnostics_export(app_version, diagnostics)
    fd, tmp_name = tempfile.mkstemp(prefix=target.name + '.', suffix='.tmp', dir=str(target.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return target
