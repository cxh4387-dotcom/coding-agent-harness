import pytest
from pathlib import Path
import tempfile
from harness.credentials import CredentialManager

def test_store_and_get_key():
    with tempfile.TemporaryDirectory() as td:
        cm = CredentialManager(vault_path=Path(td) / "vault.enc", machine_id="test-machine-001")
        cm.store_key("sk-test-key-12345")
        assert cm.has_key() is True
        assert cm.get_key() == "sk-test-key-12345"

def test_no_key_initially():
    with tempfile.TemporaryDirectory() as td:
        cm = CredentialManager(vault_path=Path(td) / "vault.enc", machine_id="test-machine-001")
        assert cm.has_key() is False
        assert cm.get_key() is None

def test_delete_key():
    with tempfile.TemporaryDirectory() as td:
        cm = CredentialManager(vault_path=Path(td) / "vault.enc", machine_id="test-machine-001")
        cm.store_key("sk-test-key-12345")
        cm.delete_key()
        assert cm.has_key() is False
        assert cm.get_key() is None

def test_vault_is_encrypted():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td) / "vault.enc"
        cm = CredentialManager(vault_path=vault, machine_id="test-machine-001")
        cm.store_key("sk-secret-key-99999")
        raw = vault.read_bytes()
        assert b"sk-secret-key-99999" not in raw

def test_different_machine_cannot_decrypt():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td) / "vault.enc"
        cm1 = CredentialManager(vault_path=vault, machine_id="machine-A")
        cm1.store_key("sk-test-key-12345")
        cm2 = CredentialManager(vault_path=vault, machine_id="machine-B")
        assert cm2.get_key() is None or cm2.get_key() != "sk-test-key-12345"
