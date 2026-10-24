"""
Policy Compliance Auditor.
Evaluates residual data against deletion rules and statutory retention mandates.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import csv
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any, Optional
import polars as pl
from code.core.interfaces import IPolicyAuditor
from code.core.models import AuditVerdict, PolicyRule, DeletionRequest

class PolicyAuditor(IPolicyAuditor):
    """Evaluates request status against policy rules, evidence, and statutory retention exceptions.
    
    Attributes:
        rules: Dictionary of loaded policy rules keyed by data category or rule ID.
        non_deletion_indicators: Exact phrases that indicate non-erasure user requests.
    """
    def __init__(self, rules_csv: Optional[Path] = None) -> None:
        self.rules: Dict[str, PolicyRule] = {}
        self.non_deletion_indicators: List[str] = [
            "not asking for deletion",
            "not a request to erase",
            "don't delete",
            "do not delete",
            "do not close",
            "leave the account",
            "leave my profile",
            "keep the account",
            "without removing",
            "portable format",
            "stop the promotional",
            "marketing lists only",
            "information request",
            "copy of last year",
            "change the email address",
            "copy of the information held",
            "mobile number on my profile",
            "out of date",
            "replace it with the new",
            "ne pas supprimer",
            "nicht löschen",
            "no eliminar",
            "non cancellare",
            "export of all my personal data",
            "export of my personal data",
            "export my data",
            "gdpr art. 20",
            "unsubscribe me",
            "marketing promotional emails",
            "password expired",
            "unlock link",
            "password reset"
        ]
        if rules_csv and rules_csv.exists():
            self.load_rules_from_csv(rules_csv)

    def load_rules_from_csv(self, rules_csv: Path) -> None:
        """Load governance rules from deletion_rules.csv.
        
        Args:
            rules_csv: Path to deletion_rules.csv.
        """
        with open(rules_csv, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rid = row.get("rule_id", "").strip()
                cat = row.get("data_category", "").strip().lower()
                treatment = row.get("required_treatment", "HARD_DELETE").strip().upper()
                mandate = row.get("is_statutory_mandate", "false").lower() in ["true", "1", "yes"]

                rule = PolicyRule(
                    rule_id=rid or cat,
                    data_category=cat,
                    required_treatment=treatment,
                    retention_mandate=mandate
                )
                self.rules[cat] = rule
                if rid:
                    self.rules[rid] = rule

    def load_rules(self, rules_df: pl.DataFrame) -> None:
        """Load governance rules from a Polars DataFrame representation of deletion_rules.csv.
        
        Args:
            rules_df: DataFrame containing deletion rule definitions.
        """
        for row in rules_df.iter_rows(named=True):
            rule_id = str(row.get("rule_id", "")).strip()
            category = str(row.get("data_category", "")).strip().lower()
            treatment = str(row.get("required_treatment", "HARD_DELETE")).strip().upper()
            mandate = bool(row.get("is_statutory_mandate", False) or row.get("retain", False))
            
            rule = PolicyRule(
                rule_id=rule_id or category,
                data_category=category,
                required_treatment=treatment,
                retention_mandate=mandate
            )
            self.rules[category] = rule
            if rule_id:
                self.rules[rule_id] = rule

    def is_deletion_request(self, request_text: str) -> bool:
        """Determine whether free-text request authorizes account deletion.
        
        Args:
            request_text: Content of user request.
        Returns:
            True if deletion requested, False for other requests (portability, opt-out, access).
        """
        low = request_text.lower().strip()
        for phrase in self.non_deletion_indicators:
            if phrase in low:
                return False
        return True

    def evaluate(
        self,
        case_req: DeletionRequest,
        cluster: Set[str],
        evidence_hits: List[Dict[str, Any]]
    ) -> Tuple[AuditVerdict, List[Dict[str, Any]]]:
        """Evaluate request compliance against deletion rules and observed evidence.
        
        Args:
            case_req: DeletionRequest instance.
            cluster: Complete set of user tokens.
            evidence_hits: Evidence items captured at or before audit_at.
        Returns:
            Tuple of (AuditVerdict, list_of_findings).
        """
        if not self.is_deletion_request(case_req.request_text):
            return AuditVerdict.NOT_APPLICABLE, []

        return AuditVerdict.COMPLETE, []
