from pathlib import Path
import os
import shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
repo_root = Path(__file__).resolve().parent.parent

# Replace the client-side license verification key. The matching private key is
# deliberately NOT stored in the repository or distributed with the client.
public_src = repo_root / "patches" / "vendor_public_key_v237.pem"
if not public_src.exists():
    raise SystemExit("V2.3.7 public key file missing")
shutil.copy2(public_src, root / "vendor_public_key.pem")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    p = root / filename
    text = p.read_text(encoding="utf-8").replace("2.3.6", "2.3.7")
    p.write_text(text, encoding="utf-8")

# Validate that the public key is an Ed25519 key and that the app remains importable.
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
key = serialization.load_pem_public_key((root / "vendor_public_key.pem").read_bytes())
if not isinstance(key, Ed25519PublicKey):
    raise SystemExit("V2.3.7 vendor_public_key.pem is not Ed25519")

compile((root / "product.py").read_text(encoding="utf-8"), str(root / "product.py"), "exec")
(root / "V237_LICENSE_TRUST.md").write_text(
    "# V2.3.7 License trust update\n\n"
    "- Replaces the embedded Ed25519 verification public key.\n"
    "- The corresponding private key is never included in the client or repository.\n"
    "- Licenses remain payload+signature JSON and may use .lic or .json.\n",
    encoding="utf-8",
)
print("V2.3.7 license public key applied")
