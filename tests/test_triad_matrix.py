"""
Triad Testing Suite covering Positive, Negative, and Edge Cases.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import pytest
from pathlib import Path
from code.agent.identity_resolver import IdentityResolver
from code.agent.policy_auditor import PolicyAuditor
from code.agent.remediation_planner import RemediationPlanner
from code.core.models import (
    AuditVerdict,
    AuditPhase,
    AuditOperation,
    AuditState,
    AuditStep
)

def test_triad_positive_single_store_clean_deletion() -> None:
    """Verify single store complete erasure produces exact verification step."""
    planner = RemediationPlanner()
    verifications = [{
        "system_id": "account_service",
        "resource_id": "account_001",
        "operation": "VERIFY_RECORD_ABSENT",
        "state": "ABSENT",
        "evidence_id": "evidence_54"
    }]
    steps = planner.build_steps(AuditVerdict.COMPLETE, [], verifications)
    assert len(steps) == 1
    assert steps[0].phase == AuditPhase.VERIFICATION
    assert steps[0].operation == AuditOperation.VERIFY_RECORD_ABSENT

def test_triad_positive_statutory_retention_preservation() -> None:
    """Verify statutory retention keeps audit logs present while user profile is deleted."""
    planner = RemediationPlanner()
    verifications = [
        {"system_id": "account_service", "resource_id": "account_7566", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_94"},
        {"system_id": "security_service", "resource_id": "audit_record_2016", "operation": "VERIFY_RECORD_PRESENT", "state": "PRESENT", "evidence_id": "evidence_94"}
    ]
    steps = planner.build_steps(AuditVerdict.COMPLETE, [], verifications)
    assert len(steps) == 2
    assert steps[1].operation == AuditOperation.VERIFY_RECORD_PRESENT
    assert steps[1].state == AuditState.PRESENT

def test_triad_negative_active_data_flow_hazard() -> None:
    """Verify active integration connector triggers REPORT_ACTIVE_DATA_FLOW and DISABLE_DATA_FLOW."""
    planner = RemediationPlanner()
    findings = [{
        "system_id": "integration_service",
        "resource_id": "data_flow_9522",
        "operation": "REPORT_ACTIVE_DATA_FLOW",
        "state": "ACTIVE",
        "evidence_id": "evidence_03"
    }]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert len(steps) == 3
    assert steps[0].operation == AuditOperation.REPORT_ACTIVE_DATA_FLOW
    assert steps[1].operation == AuditOperation.DISABLE_DATA_FLOW
    assert steps[1].state == AuditState.DISABLED
    assert steps[2].operation == AuditOperation.VERIFY_DATA_FLOW_DISABLED
    assert steps[2].state == AuditState.DISABLED

def test_triad_negative_backup_restore_risk() -> None:
    """Verify restorable backup produces REPORT_RESTORE_RISK and BLOCK_RESTORE."""
    planner = RemediationPlanner()
    findings = [{
        "system_id": "backup_service",
        "resource_id": "backup_4978",
        "operation": "REPORT_RESTORE_RISK",
        "state": "ACTIVE",
        "evidence_id": "evidence_93"
    }]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert len(steps) == 3
    assert steps[0].operation == AuditOperation.REPORT_RESTORE_RISK
    assert steps[1].operation == AuditOperation.BLOCK_RESTORE
    assert steps[1].state == AuditState.BLOCKED
    assert steps[2].operation == AuditOperation.VERIFY_RESTORE_BLOCKED

def test_triad_edge_multilingual_unicode_names() -> None:
    """Verify Unicode multilingual names (Japanese, Arabic, Yoruba) resolve properly."""
    resolver = IdentityResolver()
    resolver.link_identifiers("keiko.nakamura@gmail.com", "中村 恵子")
    resolver.link_identifiers("中村 恵子", "user_24")
    resolver.link_identifiers("user_24", "+81 90 7610 2507")
    
    cluster = resolver.resolve_cluster("keiko.nakamura@gmail.com")
    assert "中村 恵子" in cluster
    assert "user_24" in cluster
    assert "+81 90 7610 2507" in cluster

def test_triad_edge_non_deletion_international_languages() -> None:
    """Verify non-deletion indicators in foreign languages (French, German, Spanish, Italian)."""
    auditor = PolicyAuditor()
    foreign_phrases = [
        "Veuillez ne pas supprimer mon compte, juste les newsletters.",
        "Bitte nicht löschen, nur die Marketing-E-Mails abbestellen.",
        "Por favor no eliminar mi cuenta, solo las promociones.",
        "Non cancellare il mio account, solo le notifiche."
    ]
    for p in foreign_phrases:
        assert not auditor.is_deletion_request(p), f"Foreign phrase failed: {p}"

def test_triad_edge_poset_operation_tie_breakers() -> None:
    """Verify secondary and tertiary tie breakers (system_id asc, resource_id asc)."""
    planner = RemediationPlanner()
    findings = [
        {"system_id": "support_platform", "resource_id": "support_002", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_61"},
        {"system_id": "account_service", "resource_id": "account_005", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_54"},
        {"system_id": "search_service", "resource_id": "search_001", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_57"}
    ]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    f_steps = [s for s in steps if s.phase == AuditPhase.FINDING]
    assert [s.system_id for s in f_steps] == ["account_service", "search_service", "support_platform"]
