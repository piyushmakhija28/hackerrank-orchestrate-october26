"""
Synthetic Benchmark & Ground-Truth Dataset Generator.
Generates multi-store data estate for local testing and evaluation.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import csv
from pathlib import Path
from typing import Dict, List

class BenchmarkGenerator:
    """Generates synthetic enterprise datasets simulating Northstar Shop data estate."""

    @staticmethod
    def generate_benchmark_suite(base_dir: Path) -> None:
        """Create sample deletion requests, rules, secondary DBs, and replication pipelines.
        
        Args:
            base_dir: Root workspace directory.
        """
        dataset_dir = base_dir / "dataset"
        data_dir = base_dir / "data"
        attachments_dir = data_dir / "support_attachments"

        dataset_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        attachments_dir.mkdir(parents=True, exist_ok=True)

        requests_file = dataset_dir / "deletion_requests.csv"
        with open(requests_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["request_id", "email", "user_id", "requested_deletion"])
            writer.writerow(["REQ-001", "ghost.user@example.com", "USR-101", "true"])
            writer.writerow(["REQ-002", "clean.customer@example.com", "USR-102", "true"])
            writer.writerow(["REQ-003", "active.shopper@example.com", "USR-103", "false"])
            writer.writerow(["REQ-004", "tax.retained@example.com", "USR-104", "true"])

        rules_file = dataset_dir / "deletion_rules.csv"
        with open(rules_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["rule_id", "data_category", "required_treatment", "is_statutory_mandate"])
            writer.writerow(["RUL-01", "user_profile", "HARD_DELETE", "false"])
            writer.writerow(["RUL-02", "analytics_cache", "HARD_DELETE", "false"])
            writer.writerow(["RUL-03", "search_index", "HARD_DELETE", "false"])
            writer.writerow(["RUL-04", "tax_records", "ANONYMIZE", "true"])

        val_labels = dataset_dir / "validation_labels.csv"
        with open(val_labels, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["request_id", "status", "active_zombie_processes"])
            writer.writerow(["REQ-001", "INCOMPLETE", "analytics_reverse_sync"])
            writer.writerow(["REQ-002", "COMPLETE", ""])
            writer.writerow(["REQ-003", "NOT_APPLICABLE", ""])
            writer.writerow(["REQ-004", "COMPLETE", ""])

        primary_db = data_dir / "primary_account_db.csv"
        with open(primary_db, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "user_id", "email", "phone"])
            writer.writerow(["ROW-1", "USR-103", "active.shopper@example.com", "+1-555-0103"])

        analytics_db = data_dir / "analytics_db.csv"
        with open(analytics_db, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "user_id", "email", "alt_email", "device_id"])
            writer.writerow(["ROW-A1", "USR-101", "ghost.user@example.com", "ghost.alt@work.com", "DEV-998"])

        search_db = data_dir / "search_indexes.csv"
        with open(search_db, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["record_id", "user_id", "email", "shipping_address"])
            writer.writerow(["IDX-1", "USR-101", "ghost.alt@work.com", "742 Evergreen Terrace"])

        tax_db = data_dir / "tax_invoices.csv"
        with open(tax_db, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["invoice_id", "user_id", "email", "amount"])
            writer.writerow(["INV-99", "USR-104", "tax.retained@example.com", "2400.00"])

        pipelines = data_dir / "replication_pipelines.csv"
        with open(pipelines, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["process_id", "source_store", "target_store", "process_type", "is_active", "is_tombstone_aware"])
            writer.writerow(["analytics_reverse_sync", "analytics_db", "primary_account_db", "CRON_ETL", "true", "false"])

        sample_media = attachments_dir / "ticket_404_receipt.txt"
        with open(sample_media, mode="w", encoding="utf-8") as f:
            f.write("Support Ticket #404: Customer reported issue.\nCustomer Device: DEV-998\nEmail: ghost.alt@work.com\n")

if __name__ == "__main__":
    BenchmarkGenerator.generate_benchmark_suite(Path("."))
    print("Synthetic benchmark datasets generated in dataset/ and data/")
