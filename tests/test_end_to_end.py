"""
End-to-End integration tests for Autonomous Deletion Audit Agent.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import pytest
from pathlib import Path
from code.main import DeletionAuditOrchestrator
from code.utils.schema_validator import OutputSchemaValidator
from code.utils.csv_handler import CsvHandler

def test_pipeline_execution_sample_dataset(tmp_path: Path) -> None:
    """Verify that orchestrator runs cleanly on sample dataset and passes schema validation."""
    requests_csv = Path("dataset/sample_deletion_requests.csv")
    output_csv = tmp_path / "sample_output.csv"
    
    orchestrator = DeletionAuditOrchestrator()
    results = orchestrator.run_pipeline(
        requests_csv=requests_csv,
        output_csv=output_csv
    )
    
    assert len(results) == 32
    assert output_csv.exists()
    
    is_valid, count, errors = OutputSchemaValidator.validate_file(output_csv)
    assert is_valid, f"Validation failed with errors: {errors}"
    assert count == 32
    assert len(errors) == 0

def test_pipeline_execution_full_output_validation() -> None:
    """Verify that existing root output.csv conforms strictly to HackerRank challenge schema."""
    output_csv = Path("output.csv")
    if not output_csv.exists():
        pytest.skip("output.csv not generated yet.")
        
    is_valid, count, errors = OutputSchemaValidator.validate_file(output_csv)
    assert is_valid, f"Full output.csv validation failed: {errors}"
    assert count == 518
    assert len(errors) == 0

def test_csv_handler_roundtrip(tmp_path: Path) -> None:
    """Verify that CsvHandler writes and reads RFC-4180 CSV without data corruption."""
    test_file = tmp_path / "roundtrip.csv"
    from code.core.models import DeletionAuditOutputRow
    
    rows = [
        DeletionAuditOutputRow(case_id="case_01", deletion_status="COMPLETE", steps_json="[]"),
        DeletionAuditOutputRow(case_id="case_02", deletion_status="NOT_APPLICABLE", steps_json="[]")
    ]
    CsvHandler.write_output_csv(test_file, rows)
    assert test_file.exists()
    
    read_rows = CsvHandler.read_csv_safe(test_file)
    assert len(read_rows) == 2
    assert read_rows[0]["case_id"] == "case_01"
    assert read_rows[1]["deletion_status"] == "NOT_APPLICABLE"
