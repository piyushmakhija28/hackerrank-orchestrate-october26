"""Observability and logging test suite covering structured JSON logs, spans, and replay.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Validates MDC context propagation, span hierarchies, Prometheus exports, and RCA reports.
"""

import json
from pathlib import Path
import pytest

from code.observability.metrics_collector import MetricsCollector
from code.observability.replay_tracer import ReplayTracer
from code.observability.structured_logger import StructuredLogger
from code.observability.tracer import DistributedTracer, Span


def test_structured_logger_json_format_and_mdc(tmp_path: Path) -> None:
    """Verify structured logger formats valid JSON lines with MDC trace and span context."""
    log_file = tmp_path / "test_log.jsonl"
    logger = StructuredLogger(service_name="test-agent", log_file=log_file)

    logger.set_context(trace_id="trace_test_001", case_id="case_99", span_id="span_dsu")
    logger.info("Test event occurred", user_status="active", test_metric=42)
    logger.clear_context()

    assert log_file.exists()
    lines = [json.loads(line) for line in log_file.read_text(encoding="utf-8").strip().split("\n")]
    assert len(lines) >= 1
    last = lines[-1]
    assert last["level"] == "INFO"
    assert last["service"] == "test-agent"
    assert last["trace_id"] == "trace_test_001"
    assert last["case_id"] == "case_99"
    assert last["span_id"] == "span_dsu"
    assert last["event"] == "Test event occurred"
    assert last["metadata"]["user_status"] == "active"


def test_distributed_tracer_span_timing_and_hierarchy() -> None:
    """Verify distributed tracer creates context-managed spans with positive durations."""
    DistributedTracer.reset()
    tracer = DistributedTracer.get_tracer()
    trace_id = tracer.start_trace("case_101")

    with tracer.create_span("parent_op", "ParentAgent", trace_id) as parent_span:
        parent_span.set_tag("layer", "orchestration")
        with tracer.create_span("child_op", "ChildAgent", trace_id, parent_span_id=parent_span.span_id) as child_span:
            child_span.set_tag("layer", "dsu")

    spans = tracer.get_spans_for_trace(trace_id)
    assert len(spans) == 2
    assert spans[0].name == "parent_op"
    assert spans[1].name == "child_op"
    assert spans[1].parent_span_id == spans[0].span_id
    assert spans[0].duration_ms >= 0.0
    assert spans[1].duration_ms >= 0.0


def test_metrics_collector_red_percentiles_and_prometheus() -> None:
    """Verify metrics collector records subagent latencies and formats Prometheus output."""
    MetricsCollector.reset()
    metrics = MetricsCollector.get_collector()

    for d in [5.0, 10.0, 15.0, 20.0, 25.0]:
        metrics.record_subagent_duration("IdentityResolver", d)
    metrics.record_verdict("COMPLETE")
    metrics.record_error("ValidationWarning")

    percentiles = metrics.get_subagent_percentiles()
    assert "IdentityResolver" in percentiles
    assert percentiles["IdentityResolver"]["mean_ms"] == 15.0
    assert percentiles["IdentityResolver"]["p50_ms"] == 15.0

    prom_text = metrics.export_prometheus_text()
    assert 'deletion_audit_requests_total{status="COMPLETE"} 1' in prom_text
    assert 'deletion_audit_errors_total{error_type="ValidationWarning"} 1' in prom_text
    assert 'deletion_audit_subagent_latency_p95_ms{subagent="IdentityResolver"}' in prom_text


def test_replay_tracer_diagnostic_rca_report() -> None:
    """Verify deterministic replay tracer formats detailed ASCII diagnostic report."""
    ReplayTracer.reset()
    tracer = ReplayTracer.get_tracer()

    tracer.record_decision(
        case_id="case_999",
        verdict="INCOMPLETE",
        seed_email="test.user@example.com",
        cluster={"test.user@example.com", "user_999"},
        findings=[{
            "system_id": "account_service",
            "resource_id": "account_999",
            "operation": "REPORT_REMAINING_RECORD",
            "state": "PRESENT",
            "evidence_id": "evidence_54",
        }],
        verifications=[],
        steps=[{
            "step_no": 1,
            "phase": "FINDING",
            "system_id": "account_service",
            "resource_id": "account_999",
            "operation": "REPORT_REMAINING_RECORD",
            "state": "PRESENT",
            "evidence_id": "evidence_54",
        }],
        rules_applied=[{"rule_id": "rule_01", "data_category": "profile", "required_treatment": "HARD_DELETE"}],
        duration_ms=12.34,
    )

    report = tracer.format_diagnostic_report("case_999")
    assert "DELETION AUDIT DIAGNOSTIC RCA REPORT: case_999" in report
    assert "Verdict : INCOMPLETE" in report
    assert "Seed Email    : test.user@example.com" in report
    assert "account_service:account_999" in report
    assert "Step  1: [FINDING]" in report
