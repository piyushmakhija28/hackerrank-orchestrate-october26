"""Triad Unit Tests for Regulatory Compliance Engine and Audit Attestation Subsystem.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Evaluates positive, negative, and edge-case scenarios for GDPR, DPDP Act 2023,
SOC 2 CC6, and PCI DSS Req 3 compliance mappings and tombstone certifications.
"""

from code.security.compliance_guard import (
    ComplianceFrameworkMapper,
    ComplianceStandard,
)


class TestComplianceGuardPositive:
    """Positive test scenarios asserting correct regulatory standards mapping."""

    def test_gdpr_article_17_and_dpdp_sec_12_mapping(self) -> None:
        """Verifies that DELETE_RECORD and REPORT_REMAINING_RECORD map to GDPR Art 17 and DPDP Sec 12."""
        mapper = ComplianceFrameworkMapper()
        stds_del = mapper.map_operation_to_compliance("DELETE_RECORD", "orders_001")
        assert ComplianceStandard.GDPR_ART_17_ERASURE in stds_del
        assert ComplianceStandard.DPDP_ACT_SEC_12_ERASURE in stds_del

        stds_find = mapper.map_operation_to_compliance("REPORT_REMAINING_RECORD", "customer_profile")
        assert ComplianceStandard.GDPR_ART_17_ERASURE in stds_find

    def test_account_tombstone_compliance_validation(self) -> None:
        """Verifies that an account tombstone preserving internal user_id passes compliance."""
        mapper = ComplianceFrameworkMapper()
        cluster_tokens = {"user@example.com", "9876543210"}
        user_id = "user_northstar_007"
        findings = [
            {"resource_id": "account_tombstone_user_northstar_007", "operation": "REPORT_REMAINING_RECORD"}
        ]

        is_compliant = mapper.verify_tombstone_compliance(cluster_tokens, user_id, findings)
        assert is_compliant is True

    def test_statutory_retention_compliance_mapping(self) -> None:
        """Verifies that financial invoice records map to GDPR Art 5(1)(e) storage limitation exemption."""
        mapper = ComplianceFrameworkMapper()
        stds = mapper.map_operation_to_compliance("VERIFY_RECORD_PRESENT", "tax_invoice_2026_09")
        assert ComplianceStandard.GDPR_ART_5_STORAGE_LIMIT in stds
        assert ComplianceStandard.DPDP_ACT_SEC_8_OBLIGATIONS in stds

    def test_case_attestation_synthesis(self) -> None:
        """Verifies that generate_case_attestation() synthesizes a verified compliance certificate."""
        mapper = ComplianceFrameworkMapper()
        steps = [
            {"operation": "DELETE_RECORD", "resource_id": "session_cache_01"},
            {"operation": "REDACT_RECORD", "resource_id": "support_chat_ticket"},
            {"operation": "VERIFY_RECORD_ABSENT", "resource_id": "session_cache_01"},
        ]

        attestation = mapper.generate_case_attestation("case_005", "COMPLETE", steps)
        assert attestation.case_id == "case_005"
        assert attestation.verdict == "COMPLETE"
        assert attestation.risk_level == "LOW"
        assert len(attestation.standards_verified) >= 2


class TestComplianceGuardNegative:
    """Negative test scenarios checking detection of non-compliant configurations."""

    def test_non_compliant_tombstone_with_exposed_pii_detected(self) -> None:
        """Asserts that a tombstone retaining exposed direct PII fails compliance validation."""
        mapper = ComplianceFrameworkMapper()
        cluster_tokens = {"user@example.com"}
        user_id = "user_009"
        findings = [
            {"resource_id": "account_tombstone_user_009", "operation": "REPORT_EXPOSED_PII"}
        ]

        is_compliant = mapper.verify_tombstone_compliance(cluster_tokens, user_id, findings)
        assert is_compliant is False


class TestComplianceGuardEdgeCases:
    """Edge-case test scenarios for unrecognized operations and empty parameter sets."""

    def test_unrecognized_operation_returns_empty_standards(self) -> None:
        """Verifies that an unknown operation returns an empty list without raising an error."""
        mapper = ComplianceFrameworkMapper()
        stds = mapper.map_operation_to_compliance("CUSTOM_UNOFFICIAL_OP", "res_01")
        assert stds == []

    def test_empty_steps_attestation_generation(self) -> None:
        """Verifies that an attestation can be generated for NOT_APPLICABLE cases with zero steps."""
        mapper = ComplianceFrameworkMapper()
        attestation = mapper.generate_case_attestation("case_na_01", "NOT_APPLICABLE", [])
        assert attestation.case_id == "case_na_01"
        assert attestation.verdict == "NOT_APPLICABLE"
        assert attestation.standards_verified == []
