from pathlib import Path
import json
import tempfile

from production_safety import (
    ProductionSafetyError,
    evaluate_manual_layout_gate,
    require_manual_layout_safe,
    export_diagnostics_json,
)


def main():
    ready_report = {'status': 'READY', 'mapping': {'x':'x_mm','y':'y_mm','page_index':'page_index','job_index':'job_index'}}
    gate = evaluate_manual_layout_gate(ready_report)
    assert gate['ready'] is True and gate['status'] == 'READY'

    blocked_report = {'status': 'BLOCKED', 'reasons': ['layout_override 缺少 job_index']}
    gate = evaluate_manual_layout_gate(blocked_report)
    assert gate['ready'] is False and gate['reasons']

    calls = {'n': 0}
    def provider():
        calls['n'] += 1
        return ready_report
    require_manual_layout_safe(provider)
    require_manual_layout_safe(provider)
    assert calls['n'] == 2, calls

    try:
        require_manual_layout_safe(lambda: blocked_report)
        raise AssertionError('blocked gate did not raise')
    except ProductionSafetyError as exc:
        assert 'job_index' in str(exc)

    with tempfile.TemporaryDirectory() as td:
        out = export_diagnostics_json(Path(td) / '生产诊断', '2.4.16', blocked_report)
        assert out.suffix == '.json' and out.is_file()
        data = json.loads(out.read_text(encoding='utf-8'))
        assert data['schema_version'] == 1
        assert data['app_version'] == '2.4.16'
        assert data['manual_layout_gate']['status'] == 'BLOCKED'
        assert data['generated_at']

    print('V2.4.16 PRODUCTION SAFETY PASS')


if __name__ == '__main__':
    main()
