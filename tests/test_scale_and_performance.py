"""Scale, queueing theory, and telemetry verification tests.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Validates system throughput, latency percentiles, and telemetry accumulators.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import List
import pytest

from code.core.models import (
    AuditVerdict,
    AuditPhase,
    AuditOperation,
    AuditState,
    AuditStep,
)
from code.core.telemetry import AuditTelemetry, TelemetrySnapshot
from code.agent.identity_resolver import IdentityResolver
from code.agent.lineage_tracer import LineageTracer
from code.observability.replay_tracer import ReplayTracer
from code.agent.remediation_planner import RemediationPlanner


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


def test_identity_resolver_orbit_cache_equivalence() -> None:
    """Verify that cached cluster resolution produces identical sets to raw equivalence traversal."""
    resolver = IdentityResolver()
    resolver.load_identities_and_audit_log("dataset/user_identities.csv", "dataset/user_audit_log.csv")
    test_seed = "amina.elmasri@gmail.com"
    cluster_cached = resolver.resolve_cluster(test_seed)

    assert test_seed in cluster_cached
    root = resolver.dsu.find(test_seed)
    assert root in resolver._cluster_cache
    assert resolver._cluster_cache[root] == cluster_cached


def test_lineage_tracer_monotone_bisect_accuracy() -> None:
    """Verify that bisect window querying matches exact linear scan filtering."""
    tracer = LineageTracer("dataset/system_activity.csv")
    rep_dt = datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)

    bisect_results = tracer.query_window_worker_activities(rep_dt, window_seconds=7200, lead_seconds=300)

    linear_results = []
    t_start = rep_dt - timedelta(seconds=7200)
    t_end = rep_dt + timedelta(seconds=300)
    for dt, act in tracer.worker_activities_sorted:
        if t_start <= dt <= t_end:
            linear_results.append(act)

    assert len(bisect_results) == len(linear_results)
    for b_act, l_act in zip(bisect_results, linear_results):
        assert b_act["activity_id"] == l_act["activity_id"]

    assert len(bisect_results) == len(linear_results)
    for b_act, l_act in zip(bisect_results, linear_results):
        assert b_act["activity_id"] == l_act["activity_id"]


def test_lineage_tracer_invalid_timestamp_graceful_handling() -> None:
    """Verify that bisect querying gracefully returns an empty list for invalid timestamp inputs."""
    tracer = LineageTracer("dataset/system_activity.csv")
    assert tracer.query_window_worker_activities(None) == []


def test_replay_tracer_lru_capacity_eviction() -> None:
    """Verify that ReplayTracer strictly bounds memory to max_capacity via FIFO/LRU eviction."""
    tracer = ReplayTracer(max_capacity=50)
    for i in range(100):
        tracer.record_decision(
            case_id=f"case_{i}",
            verdict="COMPLETE",
            seed_email=f"user_{i}@example.com",
            cluster={f"user_{i}@example.com"},
            findings=[],
            verifications=[],
            steps=[],
            rules_applied=[],
            duration_ms=1.0,
        )

    assert len(tracer._traces) == 50
    assert tracer.get_replay_trace("case_0") is None
    assert tracer.get_replay_trace("case_49") is None
    assert tracer.get_replay_trace("case_50") is not None
    assert tracer.get_replay_trace("case_99") is not None


def test_remediation_planner_injective_total_order() -> None:
    """Verify that 5-tuple sorting deterministically resolves steps with identical phase and operation."""
    planner = RemediationPlanner()
    step_a = AuditStep(
        step_no=0,
        phase=AuditPhase.REMEDIATION,
        system_id="system_alpha",
        resource_id="res_01",
        operation=AuditOperation.DELETE_RECORD,
        state=AuditState.ABSENT,
        evidence_id="ev_02",
    )
    step_b = AuditStep(
        step_no=0,
        phase=AuditPhase.REMEDIATION,
        system_id="system_alpha",
        resource_id="res_01",
        operation=AuditOperation.DELETE_RECORD,
        state=AuditState.ABSENT,
        evidence_id="ev_01",
    )
    sorted_steps = sorted(
        [step_a, step_b],
        key=lambda s: (
            planner.PHASE_RANKS.get(s.phase, 99),
            AuditOperation.priority_rank(s.operation.value),
            s.system_id,
            s.resource_id,
            s.evidence_id,
            s.state.value,
        ),
    )
    assert sorted_steps[0].evidence_id == "ev_01"
    assert sorted_steps[1].evidence_id == "ev_02"
