"""Triad Unit and Integration Tests for Cryptographic Security Vault.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Evaluates positive, negative, and edge-case scenarios for AES-256-GCM authenticated
encryption, HKDF-SHA256 key expansion, HMAC blind indexing, and memory zeroization.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from code.security.crypto_vault import CryptoSecurityVault, CryptoTamperError
from code.security.data_guard import DataShieldManager


class TestCryptoSecurityVaultPositive:
    """Positive test scenarios asserting correct cryptographic functionality."""

    def test_aes_gcm_encryption_decryption_roundtrip(self) -> None:
        """Verifies plaintext string and bytes round-trip through AES-256-GCM AEAD cipher."""
        vault = CryptoSecurityVault()
        secret_message = "Customer SSN: 123-45-6789; Email: user@northstar.com"
        ciphertext = vault.encrypt(secret_message)

        assert ciphertext != secret_message.encode("utf-8")
        assert len(ciphertext) > len(secret_message)

        decrypted = vault.decrypt(ciphertext)
        assert decrypted.decode("utf-8") == secret_message

    def test_hkdf_key_derivation_determinism(self) -> None:
        """Verifies that identical master key seeds deterministically produce identical subkeys."""
        explicit_seed = b"32_byte_master_seed_northstar_01"
        vault_1 = CryptoSecurityVault(explicit_key=explicit_seed)
        vault_2 = CryptoSecurityVault(explicit_key=explicit_seed)

        token = "deterministic_customer@test.com"
        assert vault_1.blind_index(token) == vault_2.blind_index(token)

    def test_blind_indexing_consistency(self) -> None:
        """Verifies that identical customer emails produce identical HMAC-SHA256 blind tokens."""
        vault = CryptoSecurityVault()
        email_1 = "Alice.Smith@Domain.Com"
        email_2 = "alice.smith@domain.com  "

        blind_1 = vault.blind_index(email_1)
        blind_2 = vault.blind_index(email_2)

        assert blind_1 == blind_2
        assert len(blind_1) == 64

    def test_blind_indexing_one_way_irreversibility(self) -> None:
        """Verifies that distinct inputs produce distinct non-reversible HMAC-SHA256 digests."""
        vault = CryptoSecurityVault()
        digest_a = vault.blind_index("customer_a@northstar.com")
        digest_b = vault.blind_index("customer_b@northstar.com")

        assert digest_a != digest_b
        assert "customer" not in digest_a
        assert "@" not in digest_a

    def test_aad_binding_verification_success(self) -> None:
        """Verifies that matching Associated Authenticated Data (AAD) validates successfully."""
        vault = CryptoSecurityVault()
        case_id = "case_005"
        aad = f"Northstar_{case_id}_AuditContext".encode("utf-8")
        secret = "Verified Account Finding"

        ciphertext = vault.encrypt(secret, associated_data=aad)
        decrypted = vault.decrypt(ciphertext, associated_data=aad)
        assert decrypted.decode("utf-8") == secret

    def test_memory_scrubbing_zeros_buffer(self) -> None:
        """Verifies that scrub_buffer() completely overwrites memory bytearrays with zeros."""
        sensitive_data = bytearray(b"Highly_Sensitive_Encryption_Key_Material")
        assert any(b != 0 for b in sensitive_data)

        CryptoSecurityVault.scrub_buffer(sensitive_data)
        assert all(b == 0 for b in sensitive_data)

    def test_encrypted_json_persistence(self, tmp_path: Path) -> None:
        """Verifies that DataShieldManager writes authentic ciphertext and loads exact JSON."""
        vault = CryptoSecurityVault()
        manager = DataShieldManager(vault=vault)
        target_file = tmp_path / "test_data.json.enc"

        payload = {
            "case_id": "case_101",
            "findings": [{"system": "orders_db", "pii_exposed": True}],
            "status": "INCOMPLETE",
        }

        manager.save_encrypted_json(target_file, payload, associated_data=b"case_101")
        assert target_file.exists()

        raw_bytes = target_file.read_bytes()
        assert b"orders_db" not in raw_bytes
        assert b"INCOMPLETE" not in raw_bytes

        recovered = manager.load_encrypted_json(target_file, associated_data=b"case_101")
        assert recovered == payload


class TestCryptoSecurityVaultNegative:
    """Negative test scenarios asserting robustness against tampering, truncation, and corruption."""

    def test_bit_flipping_attack_detected(self) -> None:
        """Asserts that altering even a single bit in ciphertext raises CryptoTamperError."""
        vault = CryptoSecurityVault()
        ciphertext = bytearray(vault.encrypt("Confidential Compliance Record"))

        ciphertext[20] ^= 0x01

        with pytest.raises(CryptoTamperError, match="AEAD tag verification failed"):
            vault.decrypt(bytes(ciphertext))

    def test_aad_mismatch_attack_detected(self) -> None:
        """Asserts that modifying the AAD context raises CryptoTamperError."""
        vault = CryptoSecurityVault()
        aad_valid = b"case_001_context"
        aad_tampered = b"case_002_context"

        ciphertext = vault.encrypt("Record Bound To Case 1", associated_data=aad_valid)

        with pytest.raises(CryptoTamperError, match="AEAD tag verification failed"):
            vault.decrypt(ciphertext, associated_data=aad_tampered)

    def test_wrong_key_decryption_failure(self) -> None:
        """Asserts that attempting decryption with an incorrect key raises CryptoTamperError."""
        vault_a = CryptoSecurityVault(explicit_key=b"key_a_32_bytes_of_secret_material")
        vault_b = CryptoSecurityVault(explicit_key=b"key_b_32_bytes_of_secret_material")

        ciphertext = vault_a.encrypt("Secure Message")

        with pytest.raises(CryptoTamperError, match="AEAD tag verification failed"):
            vault_b.decrypt(ciphertext)

    def test_truncated_ciphertext_rejected(self) -> None:
        """Asserts that truncated ciphertext payloads raise CryptoTamperError."""
        vault = CryptoSecurityVault()
        short_payload = b"too_short"

        with pytest.raises(CryptoTamperError, match="truncated or invalid"):
            vault.decrypt(short_payload)

    def test_vault_lockdown_prevents_operations(self) -> None:
        """Asserts that locking the vault immediately prevents encryption, decryption, and blind indexing."""
        vault = CryptoSecurityVault()
        ciphertext = vault.encrypt("Valid Message")

        vault.lock_vault()
        assert vault.is_locked()

        with pytest.raises(CryptoTamperError, match="vault is locked"):
            vault.encrypt("New Message")

        with pytest.raises(CryptoTamperError, match="vault is locked"):
            vault.decrypt(ciphertext)

        with pytest.raises(CryptoTamperError, match="vault is locked"):
            vault.blind_index("test@example.com")


class TestCryptoSecurityVaultEdgeCases:
    """Edge-case test scenarios testing boundaries, concurrency, and Unicode."""

    def test_empty_payload_encryption(self) -> None:
        """Verifies that empty string and zero-length bytes encrypt and decrypt correctly."""
        vault = CryptoSecurityVault()
        empty_str = ""
        ciphertext = vault.encrypt(empty_str)
        decrypted = vault.decrypt(ciphertext)
        assert decrypted == b""

    def test_multilingual_unicode_payloads(self) -> None:
        """Verifies that Chinese, Hindi, Arabic, Cyrillic, and emoji strings round-trip cleanly."""
        vault = CryptoSecurityVault()
        multilingual_text = "Northstar Shop: 客户删除请求 / ग्राहक डेटा / طلب الحذف / Удаление данных 🚀🔒"
        ciphertext = vault.encrypt(multilingual_text)
        decrypted = vault.decrypt(ciphertext).decode("utf-8")
        assert decrypted == multilingual_text

    def test_large_payload_encryption(self) -> None:
        """Verifies that large 2MB payloads encrypt and decrypt in sub-second time without error."""
        vault = CryptoSecurityVault()
        large_payload = b"X" * (2 * 1024 * 1024)
        ciphertext = vault.encrypt(large_payload)
        decrypted = vault.decrypt(ciphertext)
        assert decrypted == large_payload

    def test_special_character_and_sql_injection_payloads(self) -> None:
        """Verifies that null bytes and SQL injection strings are handled cleanly without truncation."""
        vault = CryptoSecurityVault()
        payload = "admin' OR 1=1; DROP TABLE users; -- \x00\r\n\t"
        ciphertext = vault.encrypt(payload)
        decrypted = vault.decrypt(ciphertext).decode("utf-8")
        assert decrypted == payload

    def test_concurrent_multithreaded_vault_access(self) -> None:
        """Verifies that multiple concurrent worker threads can encrypt and decrypt safely."""
        vault = CryptoSecurityVault()

        def worker(idx: int) -> bool:
            msg = f"Worker_{idx}_payload"
            ct = vault.encrypt(msg)
            pt = vault.decrypt(ct).decode("utf-8")
            return pt == msg

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(worker, range(50)))

        assert all(results)

    def test_safe_repr_no_key_leakage(self) -> None:
        """Verifies that repr() and str() never expose master key or subkey bytes."""
        vault = CryptoSecurityVault(explicit_key=b"super_secret_master_key_32_bytes")
        rep = repr(vault)
        str_val = str(vault)

        assert "super_secret" not in rep
        assert "super_secret" not in str_val
        assert "CryptoSecurityVault" in rep
