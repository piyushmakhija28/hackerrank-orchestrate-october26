"""Synthetic benchmark and validation dataset generator for deletion audits.

Creates isolated synthetic test fixtures in data/synthetic_benchmark/ to evaluate edge cases
without modifying or overwriting the participant-facing dataset/ directory. Conforms strictly
to Level 2.2 Docstrings-Only convention.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List


class BenchmarkGenerator:
    """Generates isolated synthetic test fixtures simulating multi-system enterprise estates."""

    @staticmethod
    def generate_benchmark_suite(base_dir: Path) -> Path:
        """Creates sample synthetic deletion requests, activities, and validation labels.

        Args:
            base_dir: Root workspace directory.
        Returns:
            Path to the generated synthetic benchmark folder.
        """
        bench_dir = base_dir / "data" / "synthetic_benchmark"
        bench_dir.mkdir(parents=True, exist_ok=True)

        requests_file = bench_dir / "synthetic_deletion_requests.csv"
        with open(requests_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["case_id", "email", "requested_at", "reported_status", "reported_at", "audit_at", "request_text"])
            writer.writerow([
                "synth_01",
                "elena.v@northstar-corp.com",
                "2026-08-10T10:00:00Z",
                "COMPLETE",
                "2026-08-12T10:00:00Z",
                "2026-08-15T10:00:00Z",
                "Please permanently erase all my personal data from your systems.",
            ])
            writer.writerow([
                "synth_02",
                "marcel.d@paris-consulting.fr",
                "2026-08-11T11:00:00Z",
                "COMPLETE",
                "2026-08-13T11:00:00Z",
                "2026-08-16T11:00:00Z",
                "I request full account deletion under GDPR Article 17 right to erasure.",
            ])
            writer.writerow([
                "synth_03",
                "optout.user@example.com",
                "2026-08-12T12:00:00Z",
                "NOT_STARTED",
                "2026-08-12T12:00:00Z",
                "2026-08-17T12:00:00Z",
                "Please unsubscribe me from marketing promotional emails and newsletters.",
            ])

        labels_file = bench_dir / "synthetic_ground_truth.csv"
        with open(labels_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["case_id", "deletion_status", "steps_json"])
            writer.writerow([
                "synth_01",
                "INCOMPLETE",
                json.dumps([
                    {
                        "step_no": 1,
                        "phase": "FINDING",
                        "system_id": "search_service",
                        "resource_id": "search_6083",
                        "operation": "REPORT_REMAINING_RECORD",
                        "state": "PRESENT",
                        "evidence_id": "evidence_01",
                    },
                    {
                        "step_no": 2,
                        "phase": "REMEDIATION",
                        "system_id": "search_service",
                        "resource_id": "search_6083",
                        "operation": "DELETE_RECORD",
                        "state": "ABSENT",
                        "evidence_id": "",
                    },
                    {
                        "step_no": 3,
                        "phase": "VERIFICATION",
                        "system_id": "account_service",
                        "resource_id": "account_4745",
                        "operation": "VERIFY_RECORD_ABSENT",
                        "state": "ABSENT",
                        "evidence_id": "",
                    },
                    {
                        "step_no": 4,
                        "phase": "VERIFICATION",
                        "system_id": "search_service",
                        "resource_id": "search_6083",
                        "operation": "VERIFY_RECORD_ABSENT",
                        "state": "ABSENT",
                        "evidence_id": "",
                    },
                ]),
            ])
            writer.writerow([
                "synth_02",
                "COMPLETE",
                json.dumps([
                    {
                        "step_no": 1,
                        "phase": "VERIFICATION",
                        "system_id": "account_service",
                        "resource_id": "account_3136",
                        "operation": "VERIFY_RECORD_ABSENT",
                        "state": "ABSENT",
                        "evidence_id": "evidence_92",
                    },
                ]),
            ])
            writer.writerow([
                "synth_03",
                "NOT_APPLICABLE",
                "[]",
            ])

        return bench_dir


if __name__ == "__main__":
    out = BenchmarkGenerator.generate_benchmark_suite(Path("."))
    print(f"Synthetic benchmark fixtures generated in {out}")
