"""
Unit tests for Remediation Planner.
Validates Poset DAG ordering, priority ranking, and dual verification synthesis.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import pytest
from code.agent.remediation_planner import RemediationPlanner
from code.core.models import (
    AuditVerdict,
    AuditPhase,
    AuditOperation,
    AuditState,
    AuditStep
)

def test_remediation_planner_not_applicable() -> None:
    """Verify that NOT_APPLICABLE requests produce strictly empty steps list."""
    planner = RemediationPlanner()
    steps = planner.build_steps(AuditVerdict.NOT_APPLICABLE, [], [])
    assert steps == []

def test_remediation_planner_complete_verifications() -> None:
    """Verify that COMPLETE verdicts contain only VERIFICATION steps with consecutive numbers."""
    planner = RemediationPlanner()
    verifications = [
        {
            "system_id": "account_service",
            "resource_id": "account_001",
            "operation": "VERIFY_RECORD_ABSENT",
            "state": "ABSENT",
            "evidence_id": "evidence_54"
        },
        {
            "system_id": "analytics_platform",
            "resource_id": "analytics_901",
            "operation": "VERIFY_RECORD_ANONYMIZED",
            "state": "ANONYMIZED",
            "evidence_id": "evidence_56"
        }
    ]
    steps = planner.build_steps(AuditVerdict.COMPLETE, [], verifications)
    assert len(steps) == 2
    assert [s.step_no for s in steps] == [1, 2]
    assert all(s.phase == AuditPhase.VERIFICATION for s in steps)
    assert steps[0].operation == AuditOperation.VERIFY_RECORD_ABSENT
    assert steps[1].operation == AuditOperation.VERIFY_RECORD_ANONYMIZED

def test_remediation_planner_poset_phase_order() -> None:
    """Verify that FINDING strictly precedes REMEDIATION strictly precedes VERIFICATION."""
    planner = RemediationPlanner()
    findings = [
        {
            "system_id": "search_service",
            "resource_id": "search_052",
            "operation": "REPORT_REMAINING_RECORD",
            "state": "PRESENT",
            "evidence_id": "evidence_03"
        },
        {
            "system_id": "integration_service",
            "resource_id": "data_flow_9522",
            "operation": "REPORT_ACTIVE_DATA_FLOW",
            "state": "ACTIVE",
            "evidence_id": "evidence_03"
        }
    ]
    verifications = [
        {
            "system_id": "account_service",
            "resource_id": "account_4248",
            "operation": "VERIFY_RECORD_ABSENT",
            "state": "ABSENT",
            "evidence_id": ""
        }
    ]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, verifications)
    
    phases = [s.phase for s in steps]
    first_rem = phases.index(AuditPhase.REMEDIATION)
    first_ver = phases.index(AuditPhase.VERIFICATION)
    
    assert all(p == AuditPhase.FINDING for p in phases[:first_rem])
    assert all(p == AuditPhase.REMEDIATION for p in phases[first_rem:first_ver])
    assert all(p == AuditPhase.VERIFICATION for p in phases[first_ver:])

def test_remediation_planner_consecutive_numbering() -> None:
    """Verify that step_no forms a strictly monotonic sequence 1..K."""
    planner = RemediationPlanner()
    findings = [
        {
            "system_id": "support_platform",
            "resource_id": "support_001",
            "operation": "REPORT_EXPOSED_PII",
            "state": "PRESENT",
            "evidence_id": "evidence_58"
        }
    ]
    steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, [])
    assert len(steps) == 3
    assert [s.step_no for s in steps] == [1, 2, 3]
    assert steps[0].phase == AuditPhase.FINDING
    assert steps[1].phase == AuditPhase.REMEDIATION
    assert steps[2].phase == AuditPhase.VERIFICATION
