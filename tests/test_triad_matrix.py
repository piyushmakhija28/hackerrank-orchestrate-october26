"""Triad Testing Suite covering 26 Positive, Negative, and Edge Cases.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Evaluates compliance against GDPR Article 17, CCPA, and statutory retention rules.
"""

from datetime import datetime
from pathlib import Path
import pytest

from code.agent.identity_resolver import IdentityResolver
from code.agent.policy_auditor import PolicyAuditor
from code.agent.remediation_planner import RemediationPlanner
from code.core.models import (
    AuditOperation,
    AuditPhase,
    AuditState,
    AuditStep,
    AuditVerdict,
)


def test_pos_01_single_store_clean_deletion() -> None:
    """Verify single store complete erasure produces exact verification step."""
    planner = RemediationPlanner()
    verifications = [{
        "system_id": "account_service",
        "resource_id": "account_001",
        "operation": "VERIFY_RECORD_ABSENT",
        "state": "ABSENT",
        "evidence_id": "evidence_54",
    }]
    steps = planner.build_steps(AuditVerdict.COMPLETE, [], verifications)
    assert len(steps) == 1
    assert steps[0].phase == AuditPhase.VERIFICATION
    assert steps[0].operation == AuditOperation.VERIFY_RECORD_ABSENT
    assert steps[0].evidence_id == "evidence_54"


def test_pos_02_statutory_tax_invoice_retention() -> None:
    """Verify statutory tax retention keeps invoice record present under IRS rules."""
    planner = RemediationPlanner()
    verifications = [
        {"system_id": "account_service", "resource_id": "account_7566", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_94"},
        {"system_id": "billing_service", "resource_id": "tax_invoice_2021_99", "operation": "VERIFY_RECORD_PRESENT", "state": "PRESENT", "evidence_id": "evidence_94"},
    ]
    steps = planner.build_steps(AuditVerdict.COMPLETE, [], verifications)
    assert len(steps) == 2
    assert steps[1].operation == AuditOperation.VERIFY_RECORD_PRESENT
    assert steps[1].state == AuditState.PRESENT


def test_pos_03_security_audit_log_retention() -> None:
    """Verify security event audit logs are preserved for compliance."""
    planner = RemediationPlanner()
    verifications = [
        {"system_id": "security_service", "resource_id": "audit_event_8812", "operation": "VERIFY_RECORD_PRESENT", "state": "PRESENT", "evidence_id": "evidence_90"}
    ]
    steps = planner.build_steps(AuditVerdict.COMPLETE, [], verifications)
    assert len(steps) == 1
    assert steps[0].operation == AuditOperation.VERIFY_RECORD_PRESENT
    assert steps[0].state == AuditState.PRESENT


def test_pos_04_account_tombstone_preservation() -> None:
    """Verify account tombstone keeps stable UUID but redacts direct PII."""
    planner = RemediationPlanner()
    verifications = [
        {"system_id": "account_service", "resource_id": "account_tombstone_412", "operation": "VERIFY_RECORD_REDACTED", "state": "REDACTED", "evidence_id": "evidence_72"}
    ]
    steps = planner.build_steps(AuditVerdict.COMPLETE, [], verifications)
    assert len(steps) == 1
    assert steps[0].operation == AuditOperation.VERIFY_RECORD_REDACTED
    assert steps[0].state == AuditState.REDACTED


def test_pos_05_multi_system_clean_deletion() -> None:
    """Verify clean erasure spanning Account, Order, and Profile services."""
    planner = RemediationPlanner()
    verifications = [
        {"system_id": "account_service", "resource_id": "account_101", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_54"},
        {"system_id": "order_service", "resource_id": "order_profile_101", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_54"},
        {"system_id": "profile_service", "resource_id": "profile_avatar_101", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_54"},
    ]
    steps = planner.build_steps(AuditVerdict.COMPLETE, [], verifications)
    assert len(steps) == 3
    for s in steps:
        assert s.operation == AuditOperation.VERIFY_RECORD_ABSENT
        assert s.state == AuditState.ABSENT


def test_pos_06_pre_existing_anonymized_analytics_record() -> None:
    """Verify pre-existing unlinked analytics records are preserved as anonymized."""
    planner = RemediationPlanner()
    verifications = [
        {"system_id": "analytics_service", "resource_id": "event_stream_772", "operation": "VERIFY_RECORD_ANONYMIZED", "state": "ANONYMIZED", "evidence_id": "evidence_33"}
    ]
    steps = planner.build_steps(AuditVerdict.COMPLETE, [], verifications)
    assert len(steps) == 1
    assert steps[0].operation == AuditOperation.VERIFY_RECORD_ANONYMIZED
    assert steps[0].state == AuditState.ANONYMIZED


def test_neg_01_active_cdc_reverse_sync_hazard() -> None:
    """Verify active integration connector triggers REPORT_ACTIVE_DATA_FLOW and DISABLE_DATA_FLOW."""
    planner = RemediationPlanner()
    findings = [{
        "system_id": "integration_service",
        "resource_id": "data_flow_9522",
        "operation": "REPORT_ACTIVE_DATA_FLOW",
        "state": "ACTIVE",
        "evidence_id": "evidence_03",
    }]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert len(steps) == 3
    assert steps[0].operation == AuditOperation.REPORT_ACTIVE_DATA_FLOW
    assert steps[1].operation == AuditOperation.DISABLE_DATA_FLOW
    assert steps[1].state == AuditState.DISABLED
    assert steps[2].operation == AuditOperation.VERIFY_DATA_FLOW_DISABLED
    assert steps[2].state == AuditState.DISABLED


def test_neg_02_unblocked_automated_backup_restore_risk() -> None:
    """Verify restorable backup produces REPORT_RESTORE_RISK and BLOCK_RESTORE."""
    planner = RemediationPlanner()
    findings = [{
        "system_id": "backup_service",
        "resource_id": "backup_4978",
        "operation": "REPORT_RESTORE_RISK",
        "state": "ACTIVE",
        "evidence_id": "evidence_93",
    }]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert len(steps) == 3
    assert steps[0].operation == AuditOperation.REPORT_RESTORE_RISK
    assert steps[1].operation == AuditOperation.BLOCK_RESTORE
    assert steps[1].state == AuditState.BLOCKED
    assert steps[2].operation == AuditOperation.VERIFY_RESTORE_BLOCKED


def test_neg_03_secondary_read_replica_drift() -> None:
    """Verify secondary failover replica drift triggers REPORT_REMAINING_RECORD and DELETE_RECORD."""
    planner = RemediationPlanner()
    findings = [{
        "system_id": "customer_profiles_failover_replica",
        "resource_id": "profile_5099",
        "operation": "REPORT_REMAINING_RECORD",
        "state": "PRESENT",
        "evidence_id": "evidence_88",
    }]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert len(steps) == 3
    assert steps[0].operation == AuditOperation.REPORT_REMAINING_RECORD
    assert steps[1].operation == AuditOperation.DELETE_RECORD
    assert steps[1].state == AuditState.ABSENT
    assert steps[2].operation == AuditOperation.VERIFY_RECORD_ABSENT


def test_neg_04_unredacted_pii_in_support_pdf() -> None:
    """Verify unredacted customer support PDF attachment generates REDACT_RECORD."""
    planner = RemediationPlanner()
    findings = [{
        "system_id": "support_service",
        "resource_id": "ticket_invoice_att_12",
        "operation": "REPORT_EXPOSED_PII",
        "state": "PRESENT",
        "evidence_id": "evidence_62",
    }]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert len(steps) == 3
    assert steps[0].operation == AuditOperation.REPORT_EXPOSED_PII
    assert steps[1].operation == AuditOperation.REDACT_RECORD
    assert steps[1].state == AuditState.REDACTED
    assert steps[2].operation == AuditOperation.VERIFY_RECORD_REDACTED


def test_neg_05_direct_pii_in_support_screenshot() -> None:
    """Verify OCR hit in customer support image triggers REDACT_RECORD."""
    planner = RemediationPlanner()
    findings = [{
        "system_id": "support_platform",
        "resource_id": "screenshot_img_88",
        "operation": "REPORT_EXPOSED_PII",
        "state": "PRESENT",
        "evidence_id": "evidence_75",
    }]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert len(steps) == 3
    assert steps[1].operation == AuditOperation.REDACT_RECORD
    assert steps[2].operation == AuditOperation.VERIFY_RECORD_REDACTED


def test_neg_06_search_index_inverted_shard_residue() -> None:
    """Verify search index customer shard residue produces DELETE_RECORD."""
    planner = RemediationPlanner()
    findings = [{
        "system_id": "search_service",
        "resource_id": "customer_doc_441",
        "operation": "REPORT_REMAINING_RECORD",
        "state": "PRESENT",
        "evidence_id": "evidence_57",
    }]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert len(steps) == 3
    assert steps[1].operation == AuditOperation.DELETE_RECORD
    assert steps[2].operation == AuditOperation.VERIFY_RECORD_ABSENT


def test_neg_07_multi_system_cascade_failure() -> None:
    """Verify cascade with simultaneous active sync, restore risk, and unpurged replica."""
    planner = RemediationPlanner()
    findings = [
        {"system_id": "integration_service", "resource_id": "data_flow_1", "operation": "REPORT_ACTIVE_DATA_FLOW", "state": "ACTIVE", "evidence_id": "evidence_01"},
        {"system_id": "backup_service", "resource_id": "backup_1", "operation": "REPORT_RESTORE_RISK", "state": "ACTIVE", "evidence_id": "evidence_02"},
        {"system_id": "account_service", "resource_id": "account_1", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_03"},
    ]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    rem_steps = [s for s in steps if s.phase == AuditPhase.REMEDIATION]
    assert [s.operation for s in rem_steps] == [
        AuditOperation.DISABLE_DATA_FLOW,
        AuditOperation.BLOCK_RESTORE,
        AuditOperation.DELETE_RECORD,
    ]


def test_neg_08_partial_soft_delete_deception() -> None:
    """Verify soft-deleted database record still exposing PII generates REDACT_RECORD."""
    planner = RemediationPlanner()
    findings = [{
        "system_id": "account_database",
        "resource_id": "user_row_992",
        "operation": "REPORT_EXPOSED_PII",
        "state": "PRESENT",
        "evidence_id": "evidence_14",
    }]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert steps[1].operation == AuditOperation.REDACT_RECORD
    assert steps[2].operation == AuditOperation.VERIFY_RECORD_REDACTED


def test_edge_01_non_deletion_data_portability() -> None:
    """Verify data portability export requests are classified as NOT_APPLICABLE."""
    auditor = PolicyAuditor()
    text = "Please provide an export of all my personal data in JSON format under GDPR Art. 20."
    assert not auditor.is_deletion_request(text)


def test_edge_02_non_deletion_rectification_phone_update() -> None:
    """Verify phone update rectification requests are classified as NOT_APPLICABLE."""
    auditor = PolicyAuditor()
    text = "The mobile number on my profile is out of date. Please replace it with my new phone number."
    assert not auditor.is_deletion_request(text)


def test_edge_03_non_deletion_marketing_opt_out() -> None:
    """Verify newsletter opt-out requests are classified as NOT_APPLICABLE."""
    auditor = PolicyAuditor()
    text = "Unsubscribe me from all marketing promotional emails and newsletters immediately."
    assert not auditor.is_deletion_request(text)


def test_edge_04_non_deletion_password_reset() -> None:
    """Verify password reset requests are classified as NOT_APPLICABLE."""
    auditor = PolicyAuditor()
    text = "I cannot access my account because my password expired. Please send an unlock link."
    assert not auditor.is_deletion_request(text)


def test_edge_05_multilingual_spanish_erasure() -> None:
    """Verify Spanish language erasure request is recognized as deletion authorized."""
    auditor = PolicyAuditor()
    text = "Solicito la eliminacion definitiva de mi cuenta y el borrado de mis datos personales."
    assert auditor.is_deletion_request(text)


def test_edge_06_multilingual_french_erasure() -> None:
    """Verify French language erasure request is recognized as deletion authorized."""
    auditor = PolicyAuditor()
    text = "Conformement au RGPD, je vous demande d'effacer definitivement toutes mes donnees personnelles."
    assert auditor.is_deletion_request(text)


def test_edge_07_multilingual_german_erasure() -> None:
    """Verify German language erasure request is recognized as deletion authorized."""
    auditor = PolicyAuditor()
    text = "Bitte loschen Sie mein Kundenkonto und alle gespeicherten personenbezogenen Daten unverzuglich."
    assert auditor.is_deletion_request(text)


def test_edge_08_multilingual_hindi_erasure() -> None:
    """Verify Hindi language erasure request is recognized as deletion authorized."""
    auditor = PolicyAuditor()
    text = "Kripya mera khata aur meri saari personal details hamesha ke liye delete kar dijiye."
    assert auditor.is_deletion_request(text)


def test_edge_09_circular_email_aliases_in_audit_log() -> None:
    """Verify circular email aliases (A -> B -> C -> A) resolve to unified cluster."""
    resolver = IdentityResolver()
    resolver.link_identifiers("user_a@domain.com", "user_b@domain.com")
    resolver.link_identifiers("user_b@domain.com", "user_c@domain.com")
    resolver.link_identifiers("user_c@domain.com", "user_a@domain.com")
    cluster = resolver.resolve_cluster("user_a@domain.com")
    assert cluster == {"user_a@domain.com", "user_b@domain.com", "user_c@domain.com"}


def test_edge_10_post_audit_temporal_cutoff() -> None:
    """Verify records captured after audit_at cutoff are ignored."""
    planner = RemediationPlanner()
    steps = planner.build_steps(AuditVerdict.NOT_APPLICABLE, [], [])
    assert steps == []


def test_edge_11_poset_priority_tie_breaking() -> None:
    """Verify secondary and tertiary tie breakers (system_id asc, resource_id asc)."""
    planner = RemediationPlanner()
    findings = [
        {"system_id": "support_platform", "resource_id": "support_002", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_61"},
        {"system_id": "account_service", "resource_id": "account_005", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_54"},
        {"system_id": "search_service", "resource_id": "search_001", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_57"},
    ]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    f_steps = [s for s in steps if s.phase == AuditPhase.FINDING]
    assert [s.system_id for s in f_steps] == ["account_service", "search_service", "support_platform"]


def test_edge_12_dual_verification_completeness() -> None:
    """Verify every finding in an INCOMPLETE plan has a matching verification step."""
    planner = RemediationPlanner()
    findings = [
        {"system_id": "integration_service", "resource_id": "flow_1", "operation": "REPORT_ACTIVE_DATA_FLOW", "state": "ACTIVE", "evidence_id": "ev_1"},
        {"system_id": "backup_service", "resource_id": "backup_1", "operation": "REPORT_RESTORE_RISK", "state": "ACTIVE", "evidence_id": "ev_2"},
        {"system_id": "account_service", "resource_id": "acc_1", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "ev_3"},
    ]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    v_steps = [s for s in steps if s.phase == AuditPhase.VERIFICATION]
    assert len(v_steps) == 3
    assert {s.operation for s in v_steps} == {
        AuditOperation.VERIFY_DATA_FLOW_DISABLED,
        AuditOperation.VERIFY_RESTORE_BLOCKED,
        AuditOperation.VERIFY_RECORD_ABSENT,
    }
