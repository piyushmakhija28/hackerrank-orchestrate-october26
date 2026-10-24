"""Bayesian threat detection and Shannon entropy analyzer for adversarial text.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Evaluates probability of adversarial manipulation on natural language deletion requests.
"""

from collections import Counter
import math
from typing import Dict


class ThreatDetector:
    """Evaluates request payloads for anomalous information entropy and threat patterns."""

    @classmethod
    def compute_shannon_entropy(cls, text: str) -> float:
        """Calculates Shannon information entropy H(X) over character distribution.

        Args:
            text: Arbitrary string payload.
        Returns:
            Shannon entropy float value in bits per character.
        """
        if not text:
            return 0.0

        n = len(text)
        counts = Counter(text)
        entropy = 0.0
        for count in counts.values():
            p_x = count / n
            entropy -= p_x * math.log2(p_x)
        return entropy

    @classmethod
    def compute_threat_score(cls, text: str) -> float:
        """Evaluates adversarial threat probability using entropy and lexical indicators.

        Args:
            text: Customer request text.
        Returns:
            Normalized threat score between 0.0 (benign) and 1.0 (malicious).
        """
        if not text:
            return 0.0

        score = 0.0
        entropy = cls.compute_shannon_entropy(text)

        if entropy > 4.8:
            score += 0.35
        elif entropy < 2.0 and len(text) > 30:
            score += 0.25

        special_chars = sum(1 for ch in text if not ch.isalnum() and not ch.isspace())
        special_ratio = special_chars / max(1, len(text))
        if special_ratio > 0.30:
            score += 0.30

        suspicious_tokens = ["exec(", "<script>", "union select", "base64", "drop table"]
        low = text.lower()
        for tok in suspicious_tokens:
            if tok in low:
                score += 0.35

        return min(1.0, round(score, 3))
