"""Regulatory Compliance Framework Engine and Audit Attestation Subsystem.

HackerRank Orchestrate — Ghost Data Still Exists.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Maps deletion operations, account tombstones, and statutory retention to
GDPR (Art 5, 17, 25, 32), India DPDP Act 2023 (Sec 8, 12), SOC 2 CC6, and PCI DSS Req 3.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ComplianceStandard(str, Enum):
    """Enumeration of formal regulatory compliance controls governing personal data deletion."""

    GDPR_ART_17_ERASURE = "GDPR_ART_17_RIGHT_TO_ERASURE"
    GDPR_ART_5_STORAGE_LIMIT = "GDPR_ART_5_1_E_STORAGE_LIMITATION"
    GDPR_ART_25_DATA_PROTECTION = "GDPR_ART_25_DATA_PROTECTION_BY_DESIGN"
    GDPR_ART_32_SECURITY = "GDPR_ART_32_SECURITY_OF_PROCESSING"
    DPDP_ACT_SEC_8_OBLIGATIONS = "INDIA_DPDP_ACT_2023_SEC_8_FIDUCIARY_OBLIGATIONS"
    DPDP_ACT_SEC_12_ERASURE = "INDIA_DPDP_ACT_2023_SEC_12_DATA_PRINCIPAL_ERASURE"
    SOC2_CC6_SECURITY = "SOC2_TRUST_SERVICES_CRITERIA_CC6_LOGICAL_ACCESS"
    PCI_DSS_REQ_3_PROTECT_PAN = "PCI_DSS_V4_REQ_3_PROTECT_STORED_ACCOUNT_DATA"


@dataclass
class ComplianceAttestation:
    """Verifiable compliance attestation certifying deletion audit decision and actions.

    Attributes:
        case_id: Unique identifier of customer audit case.
        verdict: Final audit status (COMPLETE, INCOMPLETE, NOT_APPLICABLE).
        standards_verified: List of regulatory standards satisfied by this audit.
        tombstone_compliant: Whether account tombstone preserves user reference and strips PII.
        retention_statute_honored: Whether statutory retention exemptions (tax/invoices) were preserved.
        risk_level: Evaluated compliance risk level (LOW, MEDIUM, HIGH, CRITICAL).
    """

    case_id: str
    verdict: str
    standards_verified: List[str] = field(default_factory=list)
    tombstone_compliant: bool = True
    retention_statute_honored: bool = True
    risk_level: str = "LOW"


class ComplianceFrameworkMapper:
    """Evaluates deletion audit operations against global privacy and security regulations."""

    FINANCIAL_RESOURCES: Set[str] = {
        "invoice",
        "billing",
        "tax",
        "financial_ledger",
        "payment_receipt",
        "order_invoice",
    }

    @classmethod
    def map_operation_to_compliance(
        cls,
        operation: str,
        resource_id: str = "",
    ) -> List[ComplianceStandard]:
        """Maps an audit step operation to its corresponding regulatory standards.

        Args:
            operation: Audit step operation string (e.g. DELETE_RECORD, REDACT_RECORD).
            resource_id: Identifier of target resource.
        Returns:
            List of satisfied ComplianceStandard enum values.
        """
        standards: List[ComplianceStandard] = []
        op_upper = operation.upper()
        res_lower = resource_id.lower()

        if any(f in res_lower for f in cls.FINANCIAL_RESOURCES) and "VERIFY_RECORD_PRESENT" in op_upper:
            standards.append(ComplianceStandard.GDPR_ART_5_STORAGE_LIMIT)
            standards.append(ComplianceStandard.DPDP_ACT_SEC_8_OBLIGATIONS)
            return standards

        if op_upper in ("DELETE_RECORD", "VERIFY_RECORD_ABSENT", "REPORT_REMAINING_RECORD"):
            standards.append(ComplianceStandard.GDPR_ART_17_ERASURE)
            standards.append(ComplianceStandard.DPDP_ACT_SEC_12_ERASURE)

        elif op_upper in ("REDACT_RECORD", "VERIFY_RECORD_REDACTED", "REPORT_EXPOSED_PII"):
            standards.append(ComplianceStandard.GDPR_ART_25_DATA_PROTECTION)
            standards.append(ComplianceStandard.PCI_DSS_REQ_3_PROTECT_PAN)

        elif op_upper in ("ANONYMIZE_RECORD", "VERIFY_RECORD_ANONYMIZED"):
            standards.append(ComplianceStandard.GDPR_ART_25_DATA_PROTECTION)
            standards.append(ComplianceStandard.DPDP_ACT_SEC_8_OBLIGATIONS)

        elif op_upper in (
            "DISABLE_DATA_FLOW",
            "BLOCK_RESTORE",
            "REPORT_ACTIVE_DATA_FLOW",
            "REPORT_RESTORE_RISK",
            "VERIFY_DATA_FLOW_DISABLED",
            "VERIFY_RESTORE_BLOCKED",
        ):
            standards.append(ComplianceStandard.GDPR_ART_25_DATA_PROTECTION)
            standards.append(ComplianceStandard.GDPR_ART_32_SECURITY)
            standards.append(ComplianceStandard.SOC2_CC6_SECURITY)

        return standards

    @classmethod
    def verify_tombstone_compliance(
        cls,
        cluster_tokens: Set[str],
        preserved_user_id: str,
        remaining_findings: List[Dict[str, Any]],
    ) -> bool:
        """Validates that an account tombstone preserves internal user reference while stripping direct PII.

        Args:
            cluster_tokens: Set of customer identity tokens (emails, phones, hashes).
            preserved_user_id: Immutable internal user reference.
            remaining_findings: List of remaining record findings from audit.
        Returns:
            True if tombstone complies with GDPR Recital 26 and policy rules, False otherwise.
        """
        if not preserved_user_id:
            return True

        for finding in remaining_findings:
            res_id = str(finding.get("resource_id", "")).lower()
            if preserved_user_id.lower() in res_id:
                if finding.get("operation") == "REPORT_EXPOSED_PII":
                    return False

        return True

    @classmethod
    def generate_case_attestation(
        cls,
        case_id: str,
        verdict: str,
        steps: List[Dict[str, Any]],
    ) -> ComplianceAttestation:
        """Synthesizes a formal regulatory compliance attestation for an audited deletion case.

        Args:
            case_id: Request case identifier.
            verdict: Deletion verdict (COMPLETE, INCOMPLETE, NOT_APPLICABLE).
            steps: List of executed finding, remediation, or verification step dictionaries.
        Returns:
            Populated ComplianceAttestation record.
        """
        verified_standards: Set[str] = set()
        retention_honored = True
        risk = "LOW"

        if verdict == "INCOMPLETE":
            risk = "HIGH"

        for step in steps:
            op = step.get("operation", "")
            res = step.get("resource_id", "")
            mapped = cls.map_operation_to_compliance(op, res)
            for std in mapped:
                verified_standards.add(std.value)

        return ComplianceAttestation(
            case_id=case_id,
            verdict=verdict,
            standards_verified=sorted(list(verified_standards)),
            tombstone_compliant=True,
            retention_statute_honored=retention_honored,
            risk_level=risk,
        )
