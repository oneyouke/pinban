from pathlib import Path
import os, shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'layout_contract_v2414.py', root / 'layout_contract.py')
shutil.copy2(patch_root / 'test_v2414_layout_contract.py', root / 'test_v2414_layout_contract.py')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    p = root / filename
    text = p.read_text(encoding='utf-8').replace('2.4.13','2.4.14')
    p.write_text(text, encoding='utf-8')

compile((root/'layout_contract.py').read_text(encoding='utf-8'), str(root/'layout_contract.py'), 'exec')
compile((root/'test_v2414_layout_contract.py').read_text(encoding='utf-8'), str(root/'test_v2414_layout_contract.py'), 'exec')

(root/'V2414_LAYOUT_CONTRACT.md').write_text(
    '# V2.4.14 Manual Layout Contract Bridge\n\n'
    '- Adds runtime detection of the production engine layout_override type contract.\n'
    '- Maps placement semantics only when typed dataclass fields are explicit.\n'
    '- Fails closed when required fields are missing or ambiguous.\n'
    '- Does not guess an undocumented layout_override schema.\n'
    '- Manual-layout production activation remains gated until the source/job semantics are confirmed.\n',
    encoding='utf-8'
)
print('V2.4.14 layout contract bridge applied')
