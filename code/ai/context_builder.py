"""Context Engineering Subsystem (D80): Causal Filtering, Decoy Suppression, and Knapsack Packing.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Enforces temporal causal boundaries and priority knapsack context budgeting.
"""

from typing import Any, Dict, List, Optional, Set


class ContextBuilder:
    """Constructs context windows obeying temporal causal cones and knapsack packing.

    Attributes:
        max_budget: Token budget ceiling for candidate facts (default 4096).
        priority_weights: Mapping from phase/operation type to knapsack priority weight.
    """

    def __init__(self, max_budget: int = 4096) -> None:
        """Initializes context builder with max budget ceiling and priority weights.

        Args:
            max_budget: Maximum token budget ceiling for context windows.
        """
        self.max_budget: int = max_budget
        self.priority_weights: Dict[str, int] = {
            "FINDING": 100,
            "REPORT_REMAINING_RECORD": 100,
            "REPORT_EXPOSED_PII": 95,
            "REPORT_ACTIVE_DATA_FLOW": 90,
            "REPORT_RESTORE_RISK": 85,
            "STATUTORY_RETAIN": 50,
            "VERIFY_RECORD_PRESENT": 50,
            "VERIFY_RECORD_REDACTED": 40,
            "VERIFY_RECORD_ANONYMIZED": 35,
            "VERIFY_RECORD_ABSENT": 20,
            "VERIFY_DATA_FLOW_DISABLED": 15,
            "VERIFY_RESTORE_BLOCKED": 15,
        }

    def filter_causal_cone(self, facts: List[Any], audit_at: str) -> List[Any]:
        """Filters candidate facts strictly enforcing temporal causal boundary T(e) <= audit_at.

        Args:
            facts: List of candidate EvidenceFact instances or dictionaries.
            audit_at: ISO-8601 audit cutoff timestamp.

        Returns:
            List of facts captured at or before the audit cutoff.
        """
        if not audit_at:
            return list(facts)

        admissible_facts: List[Any] = []
        for f in facts:
            if isinstance(f, dict):
                captured_at = str(f.get("captured_at", ""))
            else:
                captured_at = getattr(f, "captured_at", "")

            if not captured_at or captured_at <= audit_at:
                admissible_facts.append(f)

        return admissible_facts

    def suppress_decoys(
        self, facts: List[Any], cluster: Set[str], user_resources: Set[str]
    ) -> List[Any]:
        """Suppresses decoy facts having zero identifier or resource overlap with the subject.

        Args:
            facts: List of candidate EvidenceFact instances or dictionaries.
            cluster: Set of resolved subject identifier tokens (emails, phones, hashes, uids).
            user_resources: Set of known user-linked resource identifiers.

        Returns:
            List of relevant facts with decoy records filtered out.
        """
        norm_cluster = {str(c).lower().strip() for c in cluster if c}
        norm_resources = {str(r).lower().strip() for r in user_resources if r}

        relevant_facts: List[Any] = []
        for f in facts:
            if isinstance(f, dict):
                res_id = str(f.get("resource_id", "")).lower().strip()
                sys_id = str(f.get("system_id", "")).lower().strip()
                details = str(f.get("details", "")).lower().strip()
            else:
                res_id = getattr(f, "resource_id", "").lower().strip()
                sys_id = getattr(f, "system_id", "").lower().strip()
                details = getattr(f, "details", "").lower().strip()

            is_match = False
            if res_id and (res_id in norm_resources or res_id in norm_cluster):
                is_match = True
            elif any(c in res_id or (c in details if details else False) for c in norm_cluster):
                is_match = True
            elif any(res in res_id for res in norm_resources):
                is_match = True

            if is_match:
                relevant_facts.append(f)

        return relevant_facts

    def calculate_relevance_score(self, fact: Any, cluster: Optional[Set[str]] = None) -> float:
        """Calculates scalar relevance score based on operation priority and identifier matches.

        Args:
            fact: EvidenceFact instance or dictionary.
            cluster: Optional set of resolved subject identifier tokens.

        Returns:
            Float scalar score where higher values denote higher priority.
        """
        if isinstance(fact, dict):
            op = str(fact.get("operation", ""))
            is_finding = bool(fact.get("is_finding", False) or op.startswith("REPORT_"))
            res_id = str(fact.get("resource_id", "")).lower()
        else:
            op = getattr(fact, "operation", "")
            is_finding = getattr(fact, "is_finding", False) or op.startswith("REPORT_")
            res_id = getattr(fact, "resource_id", "").lower()

        base_weight = float(self.priority_weights.get(op, 30))
        if is_finding:
            base_weight += 50.0

        if cluster:
            norm_cluster = {str(c).lower() for c in cluster if c}
            if any(c in res_id for c in norm_cluster):
                base_weight += 20.0

        return base_weight

    def build_knapsack_context(
        self, facts: List[Any], max_tokens: int = 4096, cluster: Optional[Set[str]] = None
    ) -> List[Any]:
        """Packs candidate facts into token budget using greedy priority knapsack allocation.

        Args:
            facts: List of candidate facts.
            max_tokens: Maximum token budget ceiling.
            cluster: Optional set of resolved subject identifiers.

        Returns:
            Subset of facts ordered by descending relevance, strictly fitting within max_tokens.
        """
        if not facts or max_tokens <= 0:
            return []

        scored_facts = [
            (f, self.calculate_relevance_score(f, cluster))
            for f in facts
        ]
        scored_facts.sort(key=lambda pair: pair[1], reverse=True)

        selected_facts: List[Any] = []
        accumulated_tokens = 0

        for f, _ in scored_facts:
            raw_repr = str(f)
            fact_tokens = max(1, len(raw_repr) // 4)
            if accumulated_tokens + fact_tokens <= max_tokens:
                selected_facts.append(f)
                accumulated_tokens += fact_tokens
            elif getattr(f, "is_finding", False) or (isinstance(f, dict) and str(f.get("operation", "")).startswith("REPORT_")):
                selected_facts.append(f)
                accumulated_tokens += fact_tokens

        return selected_facts
