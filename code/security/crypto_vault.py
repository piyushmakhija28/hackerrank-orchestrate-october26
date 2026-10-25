"""Cryptographic Security Vault and Zero-Knowledge Memory Plane.

HackerRank Orchestrate — Ghost Data Still Exists.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Provides AES-256-GCM authenticated encryption, HKDF key derivation,
HMAC-SHA256 blind indexing, and zero-knowledge memory scrubbing.
"""

import hashlib
import hmac
import os
import secrets
from typing import Optional, Tuple, Union
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class CryptoTamperError(Exception):
    """Raised when cryptographic authentication fails, indicating tampering or corruption."""
    pass


class CryptoSecurityVault:
    """Enterprise cryptographic vault managing encryption keys, AEAD ciphers, and blind indices."""

    AES_KEY_SIZE: int = 32
    GCM_NONCE_SIZE: int = 12
    DEFAULT_SALT: bytes = b"NorthstarShop_SecuritySalt_2026_Enterprise"
    DEFAULT_INFO: bytes = b"AuditAgent_VaultKey_Derivation_v1"

    def __init__(
        self,
        master_key_env_var: str = "ENCRYPTION_MASTER_KEY",
        explicit_key: Optional[bytes] = None,
    ) -> None:
        """Initializes cryptographic vault, deriving subkeys and configuring AESGCM cipher.

        Args:
            master_key_env_var: Name of environment variable holding master secret.
            explicit_key: Optional explicit raw 32-byte key for testing or injected key stores.
        """
        self._is_locked: bool = False
        raw_master = explicit_key or self._resolve_master_key(master_key_env_var)
        self._master_key: bytearray = bytearray(raw_master)
        aes_sub_key, self._blind_salt = self._derive_subkeys(bytes(self._master_key))
        self._aesgcm: Optional[AESGCM] = AESGCM(aes_sub_key)

    @classmethod
    def _resolve_master_key(cls, env_var_name: str) -> bytes:
        """Resolves 256-bit master key from environment or falls back to CSPRNG in RAM.

        Args:
            env_var_name: Name of environment variable.
        Returns:
            32-byte cryptographic key.
        """
        env_val = os.getenv(env_var_name)
        if env_val:
            try:
                raw_bytes = bytes.fromhex(env_val.strip())
                if len(raw_bytes) == cls.AES_KEY_SIZE:
                    return raw_bytes
            except ValueError:
                pass
            return hashlib.sha256(env_val.encode("utf-8")).digest()
        return secrets.token_bytes(cls.AES_KEY_SIZE)

    @classmethod
    def _derive_subkeys(cls, master_raw: bytes) -> Tuple[bytes, bytes]:
        """Derives independent 32-byte AES key and 32-byte HMAC salt using HKDF-SHA256.

        Args:
            master_raw: 32-byte master key seed.
        Returns:
            Tuple of (32-byte AES encryption key, 32-byte blind indexing salt).
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=64,
            salt=cls.DEFAULT_SALT,
            info=cls.DEFAULT_INFO,
        )
        expanded = hkdf.derive(master_raw)
        return expanded[:32], expanded[32:]

    def encrypt(
        self,
        plaintext: Union[str, bytes],
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """Encrypts plaintext using AES-256-GCM with a fresh 96-bit cryptographic nonce.

        Args:
            plaintext: Raw payload bytes or string.
            associated_data: Optional authenticated data bound to ciphertext (e.g. case ID).
        Returns:
            Serialized payload: 12-byte nonce followed by ciphertext and 16-byte MAC tag.
        Raises:
            CryptoTamperError: If the vault is locked.
        """
        if self._is_locked or self._aesgcm is None:
            raise CryptoTamperError("Cryptographic vault is locked; encryption prohibited.")

        raw_bytes = plaintext.encode("utf-8") if isinstance(plaintext, str) else plaintext
        nonce = secrets.token_bytes(self.GCM_NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(nonce, raw_bytes, associated_data)
        return nonce + ciphertext

    def decrypt(
        self,
        payload: bytes,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """Decrypts and authenticates AES-256-GCM payload, verifying integrity tag.

        Args:
            payload: Serialized payload containing 12-byte nonce and ciphertext+tag.
            associated_data: Optional authenticated data that must match the encryption context.
        Returns:
            Decrypted raw bytes.
        Raises:
            CryptoTamperError: If tag verification fails or vault is locked.
        """
        if self._is_locked or self._aesgcm is None:
            raise CryptoTamperError("Cryptographic vault is locked; decryption prohibited.")

        if len(payload) < self.GCM_NONCE_SIZE + 16:
            raise CryptoTamperError("Ciphertext payload is truncated or invalid.")

        nonce = payload[: self.GCM_NONCE_SIZE]
        ciphertext_and_tag = payload[self.GCM_NONCE_SIZE :]

        try:
            return self._aesgcm.decrypt(nonce, ciphertext_and_tag, associated_data)
        except InvalidTag as exc:
            raise CryptoTamperError("AEAD tag verification failed: ciphertext altered or corrupted.") from exc

    def blind_index(self, token: str) -> str:
        """Computes deterministic one-way HMAC-SHA256 blind index for cluster matching without raw PII.

        Args:
            token: Sensitive identifier (e.g. email, phone, user ID).
        Returns:
            Hex-encoded 64-character blind index token.
        Raises:
            CryptoTamperError: If vault is locked.
        """
        if self._is_locked:
            raise CryptoTamperError("Cryptographic vault is locked; blind indexing prohibited.")

        normalized = token.lower().strip().encode("utf-8")
        return hmac.new(self._blind_salt, normalized, hashlib.sha256).hexdigest()

    @staticmethod
    def scrub_buffer(buf: Union[bytearray, memoryview]) -> None:
        """Securely zeroes out sensitive memory buffer to prevent memory scraping.

        Args:
            buf: Mutable bytearray or memoryview.
        """
        for i in range(len(buf)):
            buf[i] = 0

    def lock_vault(self) -> None:
        """Emergency lockdown: zeroes master key, destroys cipher instance, locks all operations."""
        self._is_locked = True
        self.scrub_buffer(self._master_key)
        self._aesgcm = None

    def is_locked(self) -> bool:
        """Returns True if the vault is currently locked."""
        return self._is_locked

    def __repr__(self) -> str:
        """Returns safe representation concealing internal cryptographic keys."""
        state = "LOCKED" if self._is_locked else "ACTIVE"
        return f"<CryptoSecurityVault state={state}>"

    def __str__(self) -> str:
        """Returns human-readable description concealing internal cryptographic keys."""
        return self.__repr__()
