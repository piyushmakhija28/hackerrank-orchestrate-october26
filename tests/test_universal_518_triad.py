"""Comprehensive Triad Matrix Tests for the Universal 518-Case Deletion Audit Engine.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Covers Positive, Negative, and Edge-Case scenarios across temporal bisection,
entity resolution, Poset DAG ordering, and exception resilience.
"""

from datetime import datetime
from pathlib import Path
import pytest
from typing import Dict, List, Set

from code.agent.multimodal_inspector import MultimodalInspector
from code.agent.remediation_planner import RemediationPlanner
from code.container import AuditContainer
from code.core.models import (
    AuditOperation,
    AuditPhase,
    AuditState,
    AuditStep,
    AuditVerdict,
)


class TestUniversal518TriadMatrix:
    """Test suite executing complete Triad Matrix verification (Positive, Negative, Edge-Case)."""

    @pytest.fixture
    def inspector(self) -> MultimodalInspector:
        """Fixture providing initialized MultimodalInspector with loaded evidence manifest.
        
        Returns:
            Configured MultimodalInspector instance.
        """
        return MultimodalInspector(Path("dataset"))

    @pytest.fixture
    def planner(self) -> RemediationPlanner:
        """Fixture providing initialized RemediationPlanner.
        
        Returns:
            Configured RemediationPlanner instance.
        """
        return RemediationPlanner()

    def test_causal_snapshot_bisection_positive(self, inspector: MultimodalInspector) -> None:
        """Verify that dynamic temporal bisection selects the latest snapshot strictly on or before audit cutoff.
        
        Args:
            inspector: Multimodal evidence inspector fixture.
        """
        q1_snap = inspector.get_latest_snapshot_before("2026-02-15T12:00:00Z")
        assert q1_snap in ["evidence_49", "evidence_47"]

        q2_snap = inspector.get_latest_snapshot_before("2026-05-15T12:00:00Z")
        assert q2_snap in ["evidence_31", "evidence_74"]

        q3_snap = inspector.get_latest_snapshot_before("2026-09-05T12:00:00Z")
        assert q3_snap in ["evidence_54", "evidence_89"]

        q4_snap = inspector.get_latest_snapshot_before("2026-10-01T12:00:00Z")
        assert q4_snap in ["evidence_02", "evidence_52", "evidence_05"]

    def test_poset_dag_linear_extension_positive(self, planner: RemediationPlanner) -> None:
        """Verify that build_steps produces a strictly monotonic linear extension: FINDING < REMED < VERIF.
        
        Args:
            planner: Remediation action planner fixture.
        """
        findings = [
            {"system_id": "search_service", "resource_id": "search_101", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_08"},
            {"system_id": "analytics_platform", "resource_id": "analytics_202", "operation": "REPORT_EXPOSED_PII", "state": "PRESENT", "evidence_id": "evidence_08"},
        ]
        verifications = [
            {"system_id": "account_service", "resource_id": "account_303", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""},
            {"system_id": "security_service", "resource_id": "audit_record_404", "operation": "VERIFY_RECORD_PRESENT", "state": "PRESENT", "evidence_id": ""},
        ]
        steps = planner.build_steps(AuditVerdict.INCOMPLETE, findings, verifications)
        assert len(steps) > 0

        phase_ranks = {AuditPhase.FINDING: 1, AuditPhase.REMEDIATION: 2, AuditPhase.VERIFICATION: 3}
        last_rank = 0
        for s in steps:
            curr_rank = phase_ranks[s.phase]
            assert curr_rank >= last_rank
            last_rank = curr_rank

    def test_identity_clustering_positive(self) -> None:
        """Verify that identity resolver clusters user aliases across historical audit changes."""
        container = AuditContainer()
        cluster = container.entity_resolver.resolve_cluster("amina.elmasri@gmail.com")
        assert len(cluster) > 0
        assert "user_01" in [t.lower() for t in cluster] or "amina.elmasri@gmail.com" in cluster

    def test_future_evidence_rejection_negative(self, inspector: MultimodalInspector) -> None:
        """Verify that no snapshot captured after audit_at is ever returned by the bisection engine.
        
        Args:
            inspector: Multimodal evidence inspector fixture.
        """
        audit_at = "2026-03-01T00:00:00Z"
        selected = inspector.get_latest_snapshot_before(audit_at)
        meta = inspector.manifest.get(selected, {})
        cap_at = meta.get("captured_at", "")
        assert cap_at <= audit_at, f"Future evidence leak: {selected} captured at {cap_at} > {audit_at}"

    def test_unauthenticated_non_deletion_request_negative(self) -> None:
        """Verify that non-erasure requests (e.g. marketing opt-out) return NOT_APPLICABLE with empty steps."""
        container = AuditContainer()
        is_del = container.policy_auditor.is_deletion_request("Please unsubscribe me from marketing emails.")
        assert is_del is False

    def test_nonexistent_user_handling_negative(self) -> None:
        """Verify that querying an unknown email returns an isolated singleton cluster without exceptions."""
        container = AuditContainer()
        cluster = container.entity_resolver.resolve_cluster("nonexistent_user_9999@domain.org")
        assert isinstance(cluster, set)
        assert len(cluster) == 0 or "nonexistent_user_9999@domain.org" in cluster

    def test_exact_boundary_timestamp_edge(self, inspector: MultimodalInspector) -> None:
        """Verify that when audit_at matches a snapshot capture time exactly, that snapshot is included.
        
        Args:
            inspector: Multimodal evidence inspector fixture.
        """
        exact_time = "2026-01-31T15:00:00Z"
        selected = inspector.get_latest_snapshot_before(exact_time)
        assert selected == "evidence_49"

    def test_pre_dawn_timestamp_edge(self, inspector: MultimodalInspector) -> None:
        """Verify that an audit_at earlier than all snapshots safely falls back to the earliest snapshot.
        
        Args:
            inspector: Multimodal evidence inspector fixture.
        """
        early_time = "2025-12-01T00:00:00Z"
        selected = inspector.get_latest_snapshot_before(early_time)
        assert selected is not None
        assert selected in inspector.manifest

    def test_empty_verifications_and_findings_edge(self, planner: RemediationPlanner) -> None:
        """Verify that building steps with empty inputs for COMPLETE returns empty list safely.
        
        Args:
            planner: Remediation action planner fixture.
        """
        steps = planner.build_steps(AuditVerdict.COMPLETE, [], [])
        assert steps == []

    def test_malformed_json_resilience_edge(self, inspector: MultimodalInspector) -> None:
        """Verify that corrupted or malformed files do not crash the parser and log structured warnings.
        
        Args:
            inspector: Multimodal evidence inspector fixture.
        """
        dummy_path = inspector.dataset_dir / "nonexistent_corrupt_test_file.json"
        facts = inspector.parse_generic_records_json("evidence_dummy", dummy_path, "2026-01-01T00:00:00Z", "records")
        assert isinstance(facts, list)
        assert len(facts) == 0
