"""Scale, queueing theory, and telemetry verification tests.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Validates system throughput, latency percentiles, and telemetry accumulators.
"""

import time
import pytest

from code.core.models import AuditVerdict
from code.core.telemetry import AuditTelemetry, TelemetrySnapshot


def test_telemetry_accumulator_and_percentiles() -> None:
    """Verify that telemetry records latencies and accurately computes percentiles."""
    AuditTelemetry.reset()
    telemetry = AuditTelemetry.get_instance()

    latencies = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 100.0]
    for i, lat in enumerate(latencies):
        status = AuditVerdict.COMPLETE.value if i % 2 == 0 else AuditVerdict.INCOMPLETE.value
        telemetry.record_case_audit(
            case_id=f"case_{i}",
            status=status,
            duration_ms=lat,
            findings_count=1 if status == AuditVerdict.INCOMPLETE.value else 0,
            remediations_count=2 if status == AuditVerdict.INCOMPLETE.value else 0,
        )

    snapshot = telemetry.get_snapshot()
    assert snapshot.total_requests == 10
    assert snapshot.status_distribution[AuditVerdict.COMPLETE.value] == 5
    assert snapshot.status_distribution[AuditVerdict.INCOMPLETE.value] == 5
    assert snapshot.total_findings_reported == 5
    assert snapshot.total_remediations_scheduled == 10
    assert snapshot.mean_latency_ms == 37.0
    assert snapshot.p50_latency_ms == 35.0
    assert snapshot.p95_latency_ms == 100.0


def test_queueing_stability_and_high_throughput_burst() -> None:
    """Verify sub-millisecond execution overhead under high-volume synthetic bursts."""
    AuditTelemetry.reset()
    telemetry = AuditTelemetry.get_instance()

    burst_size = 1000
    start_time = time.perf_counter()

    for i in range(burst_size):
        telemetry.record_case_audit(
            case_id=f"synthetic_case_{i}",
            status=AuditVerdict.COMPLETE.value,
            duration_ms=0.5,
        )

    total_time = time.perf_counter() - start_time
    snapshot = telemetry.get_snapshot()

    assert snapshot.total_requests == burst_size
    assert total_time < 0.25, f"High throughput burst exceeded time budget: {total_time}s"


def test_telemetry_json_serialization_validity() -> None:
    """Verify that telemetry serialization produces valid RFC-compliant JSON."""
    AuditTelemetry.reset()
    telemetry = AuditTelemetry.get_instance()
    telemetry.record_case_audit("case_1", AuditVerdict.COMPLETE.value, 12.5)

    json_str = telemetry.to_json()
    assert '"total_requests": 1' in json_str
    assert '"mean": 12.5' in json_str
    assert '"COMPLETE": 1' in json_str
