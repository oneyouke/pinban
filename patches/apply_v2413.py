from pathlib import Path
import os, shutil

root=Path(os.environ.get('APP_ROOT','build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root=Path(__file__).resolve().parent
for src,dst in [('batch_executor_v2413.py','batch_executor.py'),('test_v2413_batch_executor.py','test_v2413_batch_executor.py')]:
    shutil.copy2(patch_root/src,root/dst)

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp=root/filename
    fp.write_text(fp.read_text(encoding='utf-8').replace('2.4.12','2.4.13'),encoding='utf-8')

for filename in ('batch_executor.py','test_v2413_batch_executor.py'):
    compile((root/filename).read_text(encoding='utf-8'),str(root/filename),'exec')

(root/'V2413_BATCH_PRODUCTION_EXECUTOR.md').write_text(
    '# V2.4.13 Batch Production Executor\n\n'
    '- Loads V2.4 workspace source PDF/page references and sheet size.\n'
    '- Builds real InputJob and ImpositionSettings objects and calls atomic_production_export.\n'
    '- Each successful task returns production output path, SHA-256, page count, warnings and manifest.\n'
    '- Missing source files fail per-task without stopping the batch queue.\n'
    '- Manual canvas placements fail closed until exact legacy layout_override bridging is implemented, preventing silent layout mismatch.\n',
    encoding='utf-8')
print('V2.4.13 batch production executor integrated')
