"""PII Redaction Shield and Data Leakage Prevention Engine.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Prevents sensitive information disclosure (OWASP LLM02) in logs and traces.
"""

import re
from typing import Any, Dict


class PiiShield:
    """Detects and masks sensitive personal and financial identifiers."""

    CARD_PATTERN: re.Pattern = re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b")
    SSN_PATTERN: re.Pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    PHONE_PATTERN: re.Pattern = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    EMAIL_PATTERN: re.Pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")

    @classmethod
    def is_valid_luhn(cls, card_number: str) -> bool:
        """Validates Luhn algorithm checksum for candidate credit card numbers.

        Args:
            card_number: Raw digit string of credit card.
        Returns:
            True if card number satisfies Luhn check, False otherwise.
        """
        digits = [int(d) for d in re.sub(r"\D", "", card_number)]
        if len(digits) < 13 or len(digits) > 19:
            return False

        checksum = 0
        reverse_digits = digits[::-1]
        for i, digit in enumerate(reverse_digits):
            if i % 2 == 1:
                doubled = digit * 2
                checksum += doubled - 9 if doubled > 9 else doubled
            else:
                checksum += digit
        return checksum % 10 == 0

    @classmethod
    def mask_pii_in_text(cls, text: str) -> str:
        """Masks credit cards, SSNs, and phone numbers in raw text with redaction tokens.

        Args:
            text: Arbitrary string payload.
        Returns:
            Sanitized text with identifiers replaced by redaction placeholders.
        """
        if not text:
            return ""

        def mask_card(match: re.Match) -> str:
            val = match.group(0)
            return "[REDACTED_CARD]" if cls.is_valid_luhn(val) else val

        res = cls.CARD_PATTERN.sub(mask_card, text)
        res = cls.SSN_PATTERN.sub("[REDACTED_SSN]", res)
        res = cls.PHONE_PATTERN.sub("[REDACTED_PHONE]", res)
        return res

    @classmethod
    def sanitize_log_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitizes dictionary keys and string values prior to log emission.

        Args:
            record: Arbitrary dictionary containing telemetry or debug metadata.
        Returns:
            A sanitized deep-copy dictionary with PII masked.
        """
        sanitized: Dict[str, Any] = {}
        for key, value in record.items():
            if isinstance(value, str):
                sanitized[key] = cls.mask_pii_in_text(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_log_record(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.mask_pii_in_text(v) if isinstance(v, str) else v for v in value
                ]
            else:
                sanitized[key] = value
        return sanitized
