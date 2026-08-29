from pathlib import Path
import os, shutil

root=Path(os.environ.get('APP_ROOT','build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root=Path(__file__).resolve().parent
shutil.copy2(patch_root/'batch_queue_v2412.py',root/'batch_queue.py')
shutil.copy2(patch_root/'test_v2412_batch_queue.py',root/'test_v2412_batch_queue.py')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp=root/filename
    text=fp.read_text(encoding='utf-8')
    if '2.4.11' in text: text=text.replace('2.4.11','2.4.12')
    elif '2.4.10' in text: text=text.replace('2.4.10','2.4.12')
    fp.write_text(text,encoding='utf-8')

for filename in ('batch_queue.py','test_v2412_batch_queue.py'):
    compile((root/filename).read_text(encoding='utf-8'),str(root/filename),'exec')

(root/'V2412_BATCH_QUEUE.md').write_text(
    '# V2.4.12 Batch Production Queue Core\n\n'
    '- Persistent versioned batch queue with atomic JSON save.\n'
    '- Per-job pending/running/success/failed/cancelled state machine.\n'
    '- One failed job is isolated and does not block later jobs by default.\n'
    '- Failed jobs can be retried without rerunning completed jobs.\n'
    '- Real preflight + production export is injected through an executor callback; this slice does not claim UI/export wiring yet.\n',
    encoding='utf-8')
print('V2.4.12 batch queue core applied')
