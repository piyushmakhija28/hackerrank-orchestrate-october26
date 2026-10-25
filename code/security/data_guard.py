"""Transparent Encrypted Storage Vault and Data Shield Manager.

HackerRank Orchestrate — Ghost Data Still Exists.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Provides authenticated AES-256-GCM file persistence for telemetry, journals, and caches.
"""

import json
from pathlib import Path
from typing import Any, Optional, Union
from code.security.anti_tamper_guard import AntiTamperGuard
from code.security.crypto_vault import CryptoSecurityVault, CryptoTamperError


class DataShieldManager:
    """Manages encrypted file storage and data-at-rest protection for agent artifacts."""

    def __init__(
        self,
        vault: Optional[CryptoSecurityVault] = None,
        anti_tamper: Optional[AntiTamperGuard] = None,
    ) -> None:
        """Initializes data shield manager with cryptographic vault and anti-tamper guard.

        Args:
            vault: CryptoSecurityVault instance for AEAD encryption/decryption.
            anti_tamper: AntiTamperGuard for monitoring tripwires during I/O operations.
        """
        self.vault: CryptoSecurityVault = vault or CryptoSecurityVault()
        self.anti_tamper: AntiTamperGuard = anti_tamper or AntiTamperGuard()

    def save_encrypted_json(
        self,
        target_path: Union[str, Path],
        data: Any,
        associated_data: Optional[bytes] = None,
    ) -> Path:
        """Serializes data to JSON and encrypts to disk using authenticated AES-256-GCM.

        Args:
            target_path: Path to write encrypted file (typically with .enc extension).
            data: Arbitrary JSON-serializable Python data structure.
            associated_data: Optional context bytes cryptographically bound to ciphertext.
        Returns:
            Resolved Path of written file.
        """
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw_json = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        encrypted_bytes = self.vault.encrypt(raw_json, associated_data=associated_data)

        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_bytes(encrypted_bytes)
        tmp_path.replace(path)
        return path

    def load_encrypted_json(
        self,
        source_path: Union[str, Path],
        associated_data: Optional[bytes] = None,
    ) -> Any:
        """Reads AES-256-GCM encrypted file from disk, authenticates tag, and parses JSON.

        Args:
            source_path: Path to encrypted file.
            associated_data: Context bytes that must match those used during encryption.
        Returns:
            Deserialized Python data object.
        Raises:
            FileNotFoundError: If source file does not exist.
            CryptoTamperError: If ciphertext has been altered, truncated, or tampered with.
        """
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"Encrypted data file not found: {path}")

        encrypted_bytes = path.read_bytes()
        decrypted_bytes = self.vault.decrypt(encrypted_bytes, associated_data=associated_data)
        return json.loads(decrypted_bytes.decode("utf-8"))

    def secure_write_bytes(
        self,
        target_path: Union[str, Path],
        data: bytes,
        associated_data: Optional[bytes] = None,
    ) -> Path:
        """Encrypts arbitrary binary bytes and writes to disk atomically.

        Args:
            target_path: Destination file path.
            data: Raw payload bytes.
            associated_data: Context bytes for AEAD tag binding.
        Returns:
            Resolved Path of written file.
        """
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        encrypted_bytes = self.vault.encrypt(data, associated_data=associated_data)

        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_bytes(encrypted_bytes)
        tmp_path.replace(path)
        return path

    def secure_read_bytes(
        self,
        source_path: Union[str, Path],
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """Reads and decrypts raw binary file with cryptographic tag verification.

        Args:
            source_path: Source file path.
            associated_data: Expected context bytes.
        Returns:
            Decrypted raw bytes.
        """
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"Encrypted file not found: {path}")

        encrypted_bytes = path.read_bytes()
        return self.vault.decrypt(encrypted_bytes, associated_data=associated_data)
