from pathlib import Path
import os
import shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'production_gate_v245.py', root / 'production_gate.py')
shutil.copy2(patch_root / 'test_v245_production_gate.py', root / 'test_v245_production_gate.py')

# PyMuPDF provides the production PDF drawing backend imported as "fitz".
requirements = root / 'requirements.txt'
requirements_text = requirements.read_text(encoding='utf-8')
if not any(line.strip().lower().startswith(('pymupdf', 'fitz')) for line in requirements_text.splitlines()):
    if requirements_text and not requirements_text.endswith('\n'):
        requirements_text += '\n'
    requirements_text += 'PyMuPDF>=1.24,<2\n'
    requirements.write_text(requirements_text, encoding='utf-8')

p = root / 'production_service.py'
s = p.read_text(encoding='utf-8')

if 'from production_gate import run_enhanced_gate, apply_vector_marks' not in s:
    marker = 'from __future__ import annotations\n'
    imp = 'from production_gate import run_enhanced_gate, apply_vector_marks\n'
    if marker in s:
        s = s.replace(marker, marker + '\n' + imp, 1)
    else:
        s = imp + s

# Enhanced preflight gate: block error-severity issues before production generation.
needle = '    preflight = preflight_report or run_preflight(jobs, settings)\n'
if needle not in s:
    raise SystemExit('production preflight marker missing')
if 'enhanced_gate = run_enhanced_gate(jobs)' not in s:
    insert = needle + '''    enhanced_gate = run_enhanced_gate(jobs)\n    if enhanced_gate.get("blocking"):\n        details = "\\n".join(enhanced_gate["blocking"][:12])\n        extra = len(enhanced_gate["blocking"]) - 12\n        if extra > 0:\n            details += f"\\n... 另有 {extra} 项阻止性错误"\n        raise ValueError("输出前印前检查未通过：\\n" + details)\n'''
    s = s.replace(needle, insert, 1)

# Append vector marks to the temporary imposed PDF before integrity validation.
needle = '        summary = impose_jobs(jobs, tmp, settings, layout_override=layout_override)\n        stage = "PDF 完整性校验"\n'
if needle not in s:
    raise SystemExit('imposition/validation marker missing')
if 'stage = "追加矢量印刷标记"' not in s:
    repl = '''        summary = impose_jobs(jobs, tmp, settings, layout_override=layout_override)\n        stage = "追加矢量印刷标记"\n        mark_result = apply_vector_marks(tmp, settings, jobs, summary)\n        stage = "PDF 完整性校验"\n'''
    s = s.replace(needle, repl, 1)

# Persist gate + mark results in the production manifest and expose warnings.
manifest_marker = '            "preflight": preflight,\n'
if manifest_marker not in s:
    raise SystemExit('manifest preflight marker missing')
if '"enhanced_preflight": enhanced_gate' not in s:
    s = s.replace(manifest_marker, manifest_marker + '            "enhanced_preflight": enhanced_gate,\n            "print_marks": mark_result,\n', 1)

warning_marker = '            "record_warnings": ([commit_warning] if commit_warning else []),\n'
if warning_marker in s:
    repl = '''            "record_warnings": ([commit_warning] if commit_warning else [])\n                + list(enhanced_gate.get("warnings") or [])\n                + ([mark_result.get("warning")] if mark_result.get("warning") else []),\n'''
    s = s.replace(warning_marker, repl, 1)

# Defensive post-commit return must also carry new records if bookkeeping fails later.
post_marker = '                "inputs": inputs, "summary": summary, "preflight": preflight,\n'
if post_marker in s and '"enhanced_preflight": enhanced_gate, "print_marks": mark_result' not in s:
    s = s.replace(post_marker, post_marker + '                "enhanced_preflight": enhanced_gate, "print_marks": mark_result,\n', 1)

p.write_text(s, encoding='utf-8')

for filename in ('product.py', 'pyproject.toml', 'installer_nsis.nsi'):
    fp = root / filename
    text = fp.read_text(encoding='utf-8').replace('2.4.4', '2.4.5')
    fp.write_text(text, encoding='utf-8')

for filename in ('production_gate.py', 'production_service.py', 'test_v245_production_gate.py'):
    compile((root / filename).read_text(encoding='utf-8'), str(root / filename), 'exec')

(root / 'V245_PRODUCTION_GATE.md').write_text(
    '# V2.4.5 Production Export Gate & Vector Marks Integration\n\n'
    '- Enhanced PDF preflight runs before production export.\n'
    '- Error-severity findings (for example unreadable PDF or unembedded fonts) block output.\n'
    '- Warning-severity findings such as RGB, low DPI, bleed and mixed sizes are recorded in the production manifest.\n'
    '- Vector print marks are appended to the temporary imposed PDF before PDF integrity validation and atomic commit.\n'
    '- Crop marks are drawn only when placement trim boxes can be extracted safely; other marks remain available without guessed crop geometry.\n'
    '- Production manifest records enhanced_preflight, print_marks and any warnings.\n',
    encoding='utf-8',
)
print('V2.4.5 production gate and vector marks integrated')
