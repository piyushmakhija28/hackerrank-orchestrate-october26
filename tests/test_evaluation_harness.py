"""Tests for the deletion audit evaluation harness and benchmark generator.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Validates metric computation, sequence checking, field precision, and benchmark isolation.
"""

import json
from pathlib import Path
import pytest

from code.evaluation.benchmark import BenchmarkGenerator
from code.evaluation.evaluator import AuditEvaluator
from code.utils.csv_handler import CsvHandler


def test_evaluator_perfect_match() -> None:
    """Verify AuditEvaluator computes 100% scores when evaluating identical ground-truth datasets."""
    sample_gt = Path("dataset/sample_output.csv")
    rows = CsvHandler.read_csv_safe(sample_gt)

    metrics = AuditEvaluator.compute_metrics(predictions=rows, ground_truth=rows)

    assert metrics["total_evaluated"] == 32
    assert metrics["status_accuracy"] == 1.0
    assert metrics["step_count_accuracy"] == 1.0
    assert metrics["sequence_order_accuracy"] == 1.0
    assert metrics["field_level_accuracy"] == 1.0
    assert metrics["exact_match_ratio"] == 1.0
    assert metrics["macro_f1"] == 1.0


def test_evaluator_mismatched_status() -> None:
    """Verify AuditEvaluator correctly calculates precision, recall, and penalties on status mismatch."""
    preds = [
        {"case_id": "c1", "deletion_status": "COMPLETE", "steps_json": "[]"},
        {"case_id": "c2", "deletion_status": "INCOMPLETE", "steps_json": "[]"},
    ]
    gt = [
        {"case_id": "c1", "deletion_status": "COMPLETE", "steps_json": "[]"},
        {"case_id": "c2", "deletion_status": "COMPLETE", "steps_json": "[]"},
    ]

    metrics = AuditEvaluator.compute_metrics(predictions=preds, ground_truth=gt)

    assert metrics["total_evaluated"] == 2
    assert metrics["status_accuracy"] == 0.5
    assert metrics["per_class_metrics"]["COMPLETE"]["precision"] == 1.0
    assert metrics["per_class_metrics"]["COMPLETE"]["recall"] == 0.5


def test_evaluator_sequence_order_violation() -> None:
    """Verify AuditEvaluator flags invalid step sequence numbering and out-of-order phases."""
    out_of_order_steps = [
        {
            "step_no": 1,
            "phase": "VERIFICATION",
            "system_id": "s1",
            "resource_id": "r1",
            "operation": "VERIFY_RECORD_ABSENT",
            "state": "ABSENT",
            "evidence_id": "",
        },
        {
            "step_no": 2,
            "phase": "FINDING",
            "system_id": "s2",
            "resource_id": "r2",
            "operation": "REPORT_REMAINING_RECORD",
            "state": "PRESENT",
            "evidence_id": "ev_01",
        },
    ]

    preds = [
        {"case_id": "c1", "deletion_status": "INCOMPLETE", "steps_json": json.dumps(out_of_order_steps)},
    ]
    gt = [
        {"case_id": "c1", "deletion_status": "INCOMPLETE", "steps_json": json.dumps(out_of_order_steps)},
    ]

    metrics = AuditEvaluator.compute_metrics(predictions=preds, ground_truth=gt)

    assert metrics["sequence_order_accuracy"] == 0.0


def test_benchmark_generator_isolation(tmp_path: Path) -> None:
    """Verify BenchmarkGenerator creates synthetic files in data/ without mutating dataset/."""
    bench_dir = BenchmarkGenerator.generate_benchmark_suite(tmp_path)

    assert bench_dir.exists()
    assert (bench_dir / "synthetic_deletion_requests.csv").exists()
    assert (bench_dir / "synthetic_ground_truth.csv").exists()
    assert not (tmp_path / "dataset").exists()
