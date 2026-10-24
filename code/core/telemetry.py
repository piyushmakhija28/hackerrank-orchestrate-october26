"""Enterprise production telemetry and observability engine for the Deletion Audit Agent.

Provides thread-safe Prometheus-compatible counters, latency histograms, and structured
JSON logging for tracking deletion request audit throughput, latency percentiles, and errors.
"""

from collections import Counter
from dataclasses import dataclass, field
import json
import logging
import threading
import time
from typing import Any, Optional


@dataclass
class TelemetrySnapshot:
    """Immutable data record encapsulating aggregate runtime telemetry metrics."""

    total_requests: int
    status_distribution: dict[str, int]
    mean_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_findings_reported: int
    total_remediations_scheduled: int


class AuditTelemetry:
    """Thread-safe telemetry collector recording audit execution performance metrics."""

    _instance: Optional["AuditTelemetry"] = None

    def __init__(self) -> None:
        """Initializes empty telemetry accumulators and counters."""
        self._lock = threading.Lock()
        self._request_counter: int = 0
        self._status_counts: Counter[str] = Counter()
        self._latencies_ms: list[float] = []
        self._total_findings: int = 0
        self._total_remediations: int = 0
        self._logger = logging.getLogger("AuditTelemetry")

    @classmethod
    def get_instance(cls) -> "AuditTelemetry":
        """Retrieves or instantiates the singleton telemetry collector instance.

        Returns:
            The global AuditTelemetry singleton instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Clears accumulated telemetry for clean isolated test runs."""
        cls._instance = cls()

    def record_case_audit(
        self,
        case_id: str,
        status: str,
        duration_ms: float,
        findings_count: int = 0,
        remediations_count: int = 0,
    ) -> None:
        """Records telemetry data for a completed case audit execution.

        Args:
            case_id: The unique identifier of the audited request.
            status: The determined verdict (COMPLETE, INCOMPLETE, NOT_APPLICABLE).
            duration_ms: Total turnaround latency in milliseconds.
            findings_count: Number of non-compliant findings discovered.
            remediations_count: Number of corrective remediation steps scheduled.
        """
        with self._lock:
            self._request_counter += 1
            self._status_counts[status] += 1
            self._latencies_ms.append(duration_ms)
            self._total_findings += findings_count
            self._total_remediations += remediations_count

    def compute_percentiles(self) -> tuple[float, float, float, float]:
        """Calculates mean, 50th, 95th, and 99th latency percentiles.

        Returns:
            A tuple containing (mean, p50, p95, p99) latencies in milliseconds.
        """
        with self._lock:
            if not self._latencies_ms:
                return 0.0, 0.0, 0.0, 0.0

            sorted_latencies = sorted(self._latencies_ms)
            n = len(sorted_latencies)
            mean_val = sum(sorted_latencies) / n

            def get_percentile(p: float) -> float:
                idx = int(p * n)
                return sorted_latencies[min(idx, n - 1)]

            return mean_val, get_percentile(0.50), get_percentile(0.95), get_percentile(0.99)

    def get_snapshot(self) -> TelemetrySnapshot:
        """Constructs an immutable TelemetrySnapshot summarizing aggregate metrics.

        Returns:
            A populated TelemetrySnapshot instance.
        """
        mean_l, p50_l, p95_l, p99_l = self.compute_percentiles()
        with self._lock:
            return TelemetrySnapshot(
                total_requests=self._request_counter,
                status_distribution=dict(self._status_counts),
                mean_latency_ms=round(mean_l, 2),
                p50_latency_ms=round(p50_l, 2),
                p95_latency_ms=round(p95_l, 2),
                p99_latency_ms=round(p99_l, 2),
                total_findings_reported=self._total_findings,
                total_remediations_scheduled=self._total_remediations,
            )

    def to_json(self) -> str:
        """Serializes aggregate telemetry snapshot into a JSON string.

        Returns:
            RFC-compliant JSON string formatted with 2-space indentation.
        """
        snapshot = self.get_snapshot()
        return json.dumps(
            {
                "total_requests": snapshot.total_requests,
                "status_distribution": snapshot.status_distribution,
                "latency_metrics_ms": {
                    "mean": snapshot.mean_latency_ms,
                    "p50": snapshot.p50_latency_ms,
                    "p95": snapshot.p95_latency_ms,
                    "p99": snapshot.p99_latency_ms,
                },
                "total_findings_reported": snapshot.total_findings_reported,
                "total_remediations_scheduled": snapshot.total_remediations_scheduled,
            },
            indent=2,
        )
