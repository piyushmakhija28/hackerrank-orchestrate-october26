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

def test_pdf_document_parsing() -> None:
    """Verify that parse_document_pdf extracts support tickets and contact identifiers from PDF files."""
    inspector = MultimodalInspector(Path("dataset"))
    pdf_path = Path("dataset/evidence/documents/delivery_correction_attachment.pdf")
    if pdf_path.exists():
        facts = inspector.parse_document_pdf("evidence_58", pdf_path, "2026-09-12T07:30:00Z", "support_platform")
        assert len(facts) > 0
        assert any(f.resource_id == "support_001" for f in facts)
        assert any("priya.raman@gmail.com" in f.identifiers for f in facts)

def test_generic_records_json_parsing() -> None:
    """Verify that parse_generic_records_json ingests standalone JSON export manifests."""
    inspector = MultimodalInspector(Path("dataset"))
    json_path = Path("dataset/evidence/records/customer_export_jobs_20260914.json")
    if json_path.exists():
        facts = inspector.parse_generic_records_json("evidence_59", json_path, "2026-09-14T15:40:00Z", "export_service")
        assert len(facts) > 0
        assert any(f.resource_id == "export_001" and f.operation == "REPORT_REMAINING_RECORD" for f in facts)

def test_key_value_log_trace_correlation() -> None:
    """Verify that parse_key_value_logs correlates multi-line events sharing identical trace_id."""
    inspector = MultimodalInspector(Path("dataset"))
    log_path = Path("dataset/evidence/logs/service_events_ap_south_20260915.log")
    if log_path.exists():
        facts = inspector.parse_key_value_logs("evidence_01", log_path, "2026-09-15T11:59:39Z")
        assert any(f.resource_id == "data_flow_9846" and "lucia-torres@gmail.com" in f.identifiers for f in facts)
        assert any(f.resource_id == "backup_3245" and "leonie.g9352@outlook.com" in f.identifiers for f in facts)

def test_tombstone_redacted_verification_state() -> None:
    """Verify that identity_service tombstones lacking PII yield VERIFY_RECORD_REDACTED."""
    inspector = MultimodalInspector(Path("dataset"))
    json_path = Path("dataset/evidence/records/customer_data_snapshot_bundle_20260915.json")
    if json_path.exists():
        facts = inspector.parse_snapshot_bundle("evidence_51", json_path, "2026-09-15T12:00:00Z")
        tombstone_facts = [f for f in facts if f.resource_id == "tombstone_440"]
        assert len(tombstone_facts) == 1
        assert tombstone_facts[0].operation == "VERIFY_RECORD_REDACTED"
        assert tombstone_facts[0].state == "REDACTED"
