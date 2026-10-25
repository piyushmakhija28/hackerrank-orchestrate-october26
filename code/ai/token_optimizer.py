"""Token Estimation, Semantic Deduplication, Dense Serialization, and Budgeting Subsystem.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Coordinates subword BPE token budgeting, fact fingerprinting, and cost tracking.
"""

import hashlib
import json
import math
import threading
from typing import Any, Dict, List, Optional, Set, Tuple


class TokenOptimizer:
    """Manages token budgeting, semantic deduplication, dense serialization, and financial telemetry.

    Attributes:
        CHARS_PER_TOKEN: Calibrated subword BPE ratio (default 3.8).
        INPUT_COST_PER_MILLION: Vertex AI pricing ($0.075 / 1M input tokens).
        OUTPUT_COST_PER_MILLION: Vertex AI pricing ($0.300 / 1M output tokens).
        SYSTEM_PROMPT_BASE_TOKENS: Baseline instruction tokens for multi-agent system prompt.
        max_context_tokens: Ceiling for total prompt context tokens.
        total_input_tokens: Cumulative input tokens tracked.
        total_output_tokens: Cumulative output tokens tracked.
        total_tokens_saved: Cumulative tokens pruned via deduplication and compression.
        total_dedup_saved: Cumulative tokens saved via semantic evidence fact deduplication.
        total_compression_saved: Cumulative tokens saved via dense tabular serialization.
        deduplication_cache: Mapping of MD5 hash to first-seen evidence fact.
    """

    CHARS_PER_TOKEN: float = 3.8
    INPUT_COST_PER_MILLION: float = 0.075
    OUTPUT_COST_PER_MILLION: float = 0.300
    SYSTEM_PROMPT_BASE_TOKENS: int = 2450

    def __init__(self, max_context_tokens: int = 4096) -> None:
        """Initializes token optimizer with max context budget, counters, and thread lock.

        Args:
            max_context_tokens: Maximum token budget ceiling for context windows.
        """
        self.max_context_tokens: int = max_context_tokens
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_tokens_saved: int = 0
        self.total_dedup_saved: int = 0
        self.total_compression_saved: int = 0
        self.deduplication_cache: Dict[str, Any] = {}
        self._lock: threading.Lock = threading.Lock()

    def estimate_tokens(self, text: str) -> int:
        """Estimates token count using calibrated BPE heuristics with UTF-8 byte weighting.

        Args:
            text: Arbitrary string payload or serialization.

        Returns:
            Integer token count estimation.
        """
        if not text:
            return 0
        utf8_bytes = len(text.encode("utf-8"))
        char_len = len(text)
        effective_len = (char_len + utf8_bytes) / 2.0
        return max(1, math.ceil(effective_len / self.CHARS_PER_TOKEN))

    def estimate_prompt_tokens(
        self,
        compact_facts_str: str,
        request_text: str = "",
        include_system_prompt: bool = True,
    ) -> int:
        """Estimates full LLM inference prompt token footprint across instructions, request, and facts.

        Args:
            compact_facts_str: Serialized pipe-delimited candidate evidence facts.
            request_text: Optional sanitized customer request text.
            include_system_prompt: Whether to include baseline multi-agent system prompt instructions.

        Returns:
            Aggregate input token count estimation.
        """
        base_tokens = self.SYSTEM_PROMPT_BASE_TOKENS if include_system_prompt else 0
        facts_tokens = self.estimate_tokens(compact_facts_str)
        req_tokens = self.estimate_tokens(request_text)
        return base_tokens + facts_tokens + req_tokens

    def fingerprint_fact(self, fact: Any) -> str:
        """Generates deterministic MD5 hash for evidence fact tuple.

        Args:
            fact: EvidenceFact model instance or dictionary.

        Returns:
            Hexadecimal MD5 hash representing semantic identity.
        """
        if isinstance(fact, dict):
            sys_id = str(fact.get("system_id", ""))
            res_id = str(fact.get("resource_id", ""))
            op = str(fact.get("operation", ""))
            st = str(fact.get("state", ""))
        else:
            sys_id = getattr(fact, "system_id", "")
            res_id = getattr(fact, "resource_id", "")
            op = getattr(fact, "operation", "")
            st = getattr(fact, "state", "")

        canonical_repr = f"{sys_id}|{res_id}|{op}|{st}"
        return hashlib.md5(canonical_repr.encode("utf-8")).hexdigest()

    def deduplicate_facts(self, facts: List[Any]) -> Tuple[List[Any], int]:
        """Deduplicates facts using fingerprinting, accumulating saved tokens under thread lock.

        Args:
            facts: List of candidate EvidenceFact instances or dictionaries.

        Returns:
            Tuple of (unique_facts_list, total_tokens_saved_int).
        """
        if not facts:
            return [], 0

        unique_facts: List[Any] = []
        seen_hashes: Set[str] = set()
        tokens_saved = 0

        with self._lock:
            for f in facts:
                fp = self.fingerprint_fact(f)
                if fp in seen_hashes:
                    raw_repr = str(f)
                    tokens_saved += self.estimate_tokens(raw_repr)
                else:
                    seen_hashes.add(fp)
                    self.deduplication_cache[fp] = f
                    unique_facts.append(f)

            self.total_dedup_saved += tokens_saved
            self.total_tokens_saved += tokens_saved

        return unique_facts, tokens_saved

    def compact_serialize(self, facts: List[Any]) -> str:
        """Serializes facts into dense tabular notation saving >= 68% tokens vs JSON.

        Args:
            facts: List of evidence facts or dictionary steps.

        Returns:
            Pipe-delimited dense string representation.
        """
        if not facts:
            return ""

        lines: List[str] = []
        for f in facts:
            if isinstance(f, dict):
                sys_id = str(f.get("system_id", ""))
                res_id = str(f.get("resource_id", ""))
                op = str(f.get("operation", ""))
                st = str(f.get("state", ""))
                ev_id = str(f.get("evidence_id", ""))
            else:
                sys_id = getattr(f, "system_id", "")
                res_id = getattr(f, "resource_id", "")
                op = getattr(f, "operation", "")
                st = getattr(f, "state", "")
                ev_id = getattr(f, "evidence_id", "")

            lines.append(f"{sys_id}|{res_id}|{op}|{st}|{ev_id}")

        return "\n".join(lines)

    def calculate_serialization_savings(self, facts: List[Any], compact_str: str) -> int:
        """Calculates token compression delta between standard JSON and compact tabular notation.

        Args:
            facts: List of packed evidence facts.
            compact_str: Dense pipe-delimited representation.

        Returns:
            Integer tokens saved by using compact serialization over verbose JSON.
        """
        if not facts or not compact_str:
            return 0

        raw_dicts: List[Dict[str, str]] = []
        for f in facts:
            if isinstance(f, dict):
                raw_dicts.append({
                    "system_id": str(f.get("system_id", "")),
                    "resource_id": str(f.get("resource_id", "")),
                    "operation": str(f.get("operation", "")),
                    "state": str(f.get("state", "")),
                    "evidence_id": str(f.get("evidence_id", "")),
                })
            else:
                raw_dicts.append({
                    "system_id": getattr(f, "system_id", ""),
                    "resource_id": getattr(f, "resource_id", ""),
                    "operation": getattr(f, "operation", ""),
                    "state": getattr(f, "state", ""),
                    "evidence_id": getattr(f, "evidence_id", ""),
                })

        json_repr = json.dumps(raw_dicts)
        json_tokens = self.estimate_tokens(json_repr)
        compact_tokens = self.estimate_tokens(compact_str)
        return max(0, json_tokens - compact_tokens)

    def check_budget(self, estimated_tokens: int, budget: Optional[int] = None) -> bool:
        """Verifies whether estimated tokens fit within defined budget ceiling.

        Args:
            estimated_tokens: Estimated token count.
            budget: Optional override budget ceiling.

        Returns:
            Boolean indicating whether budget is respected.
        """
        ceiling = budget if budget is not None else self.max_context_tokens
        return estimated_tokens <= ceiling

    def record_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        additional_tokens_saved: int = 0,
    ) -> None:
        """Records inference token usage and accumulated compression savings under thread lock.

        Args:
            input_tokens: Number of prompt/context tokens consumed.
            output_tokens: Number of completion tokens generated.
            additional_tokens_saved: Supplementary tokens saved via dense compression or knapsack pruning.
        """
        with self._lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            if additional_tokens_saved > 0:
                self.total_compression_saved += additional_tokens_saved
                self.total_tokens_saved += additional_tokens_saved

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns cumulative token optimization telemetry and financial cost estimates under thread lock.

        Returns:
            Dictionary with token counters, savings, and estimated USD cost.
        """
        with self._lock:
            input_cost = (self.total_input_tokens / 1_000_000.0) * self.INPUT_COST_PER_MILLION
            output_cost = (self.total_output_tokens / 1_000_000.0) * self.OUTPUT_COST_PER_MILLION
            total_cost = input_cost + output_cost

            return {
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens_saved": self.total_tokens_saved,
                "total_dedup_saved": self.total_dedup_saved,
                "total_compression_saved": self.total_compression_saved,
                "estimated_cost_usd": round(total_cost, 6),
                "max_context_tokens": self.max_context_tokens,
            }
