"""Adversarial input sanitizer and prompt injection disarming engine.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Detects prompt injection attempts (OWASP LLM01) and sanitizes Unicode smuggling.
"""

import re
import unicodedata
from typing import Tuple


class InputSanitizer:
    """Sanitizes incoming customer deletion request text and disarms prompt injections."""

    MAX_PAYLOAD_BYTES: int = 16384

    ZERO_WIDTH_CHARS: set[str] = {
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\ufeff",  # Zero-width no-break space
        "\u202a",  # Left-to-right embedding
        "\u202e",  # Right-to-left override
    }

    ADVERSARIAL_PATTERNS: list[tuple[str, re.Pattern]] = [
        ("system_override", re.compile(r"(?i)(ignore\s+previous\s+instructions|system\s+prompt\s+override|disregard\s+all\s+prior)")),
        ("roleplay_jailbreak", re.compile(r"(?i)(you\s+are\s+now\s+in\s+developer\s+mode|dan\s+mode|unrestricted\s+ai|ignore\s+safety)")),
        ("instruction_leak", re.compile(r"(?i)(repeat\s+the\s+system\s+instructions|print\s+your\s+prompt|show\s+rules|reveal\s+secret)")),
        ("sql_script_injection", re.compile(r"(?i)(drop\s+table|delete\s+from|exec\(|<script>|union\s+select)")),
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Sanitizes text by normalizing Unicode, stripping hidden chars, and bounding length.

        Args:
            text: Raw input text from customer request.
        Returns:
            Sanitized and normalized text string.
        """
        if not text:
            return ""

        normalized = unicodedata.normalize("NFKC", text)

        cleaned_chars = [ch for ch in normalized if ch not in cls.ZERO_WIDTH_CHARS]
        cleaned_text = "".join(cleaned_chars)

        encoded = cleaned_text.encode("utf-8")
        if len(encoded) > cls.MAX_PAYLOAD_BYTES:
            cleaned_text = encoded[: cls.MAX_PAYLOAD_BYTES].decode("utf-8", errors="ignore")

        return cleaned_text.strip()

    @classmethod
    def is_adversarial_injection(cls, text: str) -> Tuple[bool, str, float]:
        """Scans sanitized text for adversarial prompt injection signatures.

        Args:
            text: Sanitized request text.
        Returns:
            Tuple of (is_adversarial, matched_pattern_name, confidence_score).
        """
        if not text:
            return False, "none", 0.0

        for name, pattern in cls.ADVERSARIAL_PATTERNS:
            if pattern.search(text):
                return True, name, 0.95

        return False, "none", 0.0
