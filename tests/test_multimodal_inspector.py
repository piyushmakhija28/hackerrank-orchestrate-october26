"""
Unit tests for Multimodal Evidence Inspection Engine.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import pytest
from pathlib import Path
from code.agent.multimodal_inspector import MultimodalInspector, EvidenceFact

def test_multimodal_inspector_initialization() -> None:
    """Verify that MultimodalInspector loads manifest and indexes all evidence facts."""
    inspector = MultimodalInspector(Path("dataset"))
    assert len(inspector.manifest) == 94
    assert len(inspector.facts) > 0

def test_multimodal_inspector_inverted_indices() -> None:
    """Verify that facts_by_res and facts_by_token contain queryable records."""
    inspector = MultimodalInspector(Path("dataset"))
    assert "account_5684" in inspector.facts_by_res
    assert "audit_record_2016" in inspector.facts_by_res

def test_sqlite_sql_dump_parsing(tmp_path: Path) -> None:
    """Verify that parse_sql_dump loads SQLite database and extracts tables."""
    inspector = MultimodalInspector(Path("dataset"))
    sql_path = Path("dataset/evidence/databases/customer_accounts_failover_replica_20260902.sql")
    if sql_path.exists():
        facts = inspector.parse_sql_dump("evidence_54", sql_path, "2026-09-02T23:00:00Z")
        assert len(facts) > 0
        assert any(f.resource_id == "account_005" for f in facts)

def test_txt_handover_parsing() -> None:
    """Verify that pipe-delimited handover records parse into correct operations and states."""
    inspector = MultimodalInspector(Path("dataset"))
    txt_path = Path("dataset/evidence/records/customer_account_handover_20261001.txt")
    if txt_path.exists():
        facts = inspector.parse_txt_handover("evidence_03", txt_path, "2026-10-01T12:00:00Z")
        assert len(facts) > 0
        search_facts = [f for f in facts if f.resource_id == "search_052"]
        assert len(search_facts) == 1
        assert search_facts[0].operation == "REPORT_REMAINING_RECORD"
        assert search_facts[0].state == "PRESENT"
