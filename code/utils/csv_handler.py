"""
RFC 4180 Streaming CSV Reader and Writer.
Guarantees clean delimiter escaping, chunked streaming, and whitespace trimming.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import csv
from pathlib import Path
from typing import List, Dict, Generator, Any, Optional
import polars as pl
from code.core.models import DeletionAuditOutputRow

class CsvHandler:
    """Handles structured, high-volume CSV I/O with RFC 4180 compliance."""

    @staticmethod
    def read_csv_lazy(file_path: Path) -> pl.LazyFrame:
        """Scan a CSV lazily using Polars Arrow engine.
        
        Args:
            file_path: Path to CSV file.
        Returns:
            Polars LazyFrame.
        """
        return pl.scan_csv(
            file_path,
            ignore_errors=True,
            truncate_ragged_lines=True,
            null_values=["", "NA", "null", "NULL", "None"]
        )

    @staticmethod
    def read_csv_safe(file_path: Path) -> List[Dict[str, str]]:
        """Safely read a CSV file into a list of row dictionaries with trimmed keys.
        
        Args:
            file_path: Path to CSV file.
        Returns:
            List of row dictionaries.
        """
        if not file_path.exists():
            return []

        rows: List[Dict[str, str]] = []
        with open(file_path, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return []
            clean_fieldnames = [fn.strip() for fn in reader.fieldnames]
            for raw_row in reader:
                cleaned_row = {
                    clean_fieldnames[i]: (raw_row[fn] or "").strip()
                    for i, fn in enumerate(reader.fieldnames)
                    if fn is not None
                }
                rows.append(cleaned_row)
        return rows

    @staticmethod
    def write_output_csv(output_path: Path, records: List[DeletionAuditOutputRow]) -> None:
        """Write predictions to output.csv with exact official schema and proper escaping.
        
        Args:
            output_path: Destination path for output.csv.
            records: List of DeletionAuditOutputRow model instances.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "case_id",
            "deletion_status",
            "steps_json"
        ]

        with open(output_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_MINIMAL,
                lineterminator="\n"
            )
            writer.writeheader()
            for r in records:
                writer.writerow({
                    "case_id": r.case_id,
                    "deletion_status": r.deletion_status,
                    "steps_json": r.steps_json
                })
