import hashlib
import uuid
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class CredentialManager:
    def __init__(self, vault_path: Path, machine_id: str | None = None):
        self.vault_path = vault_path
        self.machine_id = machine_id or self._derive_machine_id()
        self._fernet = self._make_fernet()

    def _derive_machine_id(self) -> str:
        node = uuid.getnode()
        user = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
        return hashlib.sha256(f"{node}:{user}".encode()).hexdigest()[:16]

    def _make_fernet(self) -> Fernet:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"harness-salt-v1",
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.machine_id.encode()))
        return Fernet(key)

    def store_key(self, key: str):
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        encrypted = self._fernet.encrypt(key.encode("utf-8"))
        self.vault_path.write_bytes(encrypted)

    def get_key(self) -> str | None:
        if not self.vault_path.exists():
            return None
        try:
            decrypted = self._fernet.decrypt(self.vault_path.read_bytes())
            return decrypted.decode("utf-8")
        except Exception:
            return None

    def has_key(self) -> bool:
        return self.get_key() is not None

    def delete_key(self):
        if self.vault_path.exists():
            self.vault_path.unlink()
