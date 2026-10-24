"""RED and USE Metrics Collector for subagent latency and throughput.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Calculates quantile latencies (p50, p90, p95, p99) and formats Prometheus metrics.
"""

from collections import Counter, defaultdict
import threading
from typing import Dict, List, Optional


class MetricsCollector:
    """Thread-safe Prometheus-compatible metrics aggregator."""

    _instance: Optional["MetricsCollector"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Initializes thread-safe counters and duration accumulators."""
        self._request_counter: Counter[str] = Counter()
        self._subagent_latencies: Dict[str, List[float]] = defaultdict(list)
        self._error_counter: Counter[str] = Counter()
        self._collector_lock: threading.Lock = threading.Lock()

    @classmethod
    def get_collector(cls) -> "MetricsCollector":
        """Retrieves or creates the global singleton MetricsCollector.

        Returns:
            The global MetricsCollector instance.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Resets all metrics counters for clean test isolation."""
        with cls._lock:
            cls._instance = cls()

    def record_verdict(self, verdict: str) -> None:
        """Records an audit case completion verdict.

        Args:
            verdict: Audit status string (COMPLETE, INCOMPLETE, NOT_APPLICABLE).
        """
        with self._collector_lock:
            self._request_counter[verdict] += 1

    def record_subagent_duration(self, subagent: str, duration_ms: float) -> None:
        """Records execution latency for a given subagent.

        Args:
            subagent: Subagent identifier.
            duration_ms: Latency in milliseconds.
        """
        with self._collector_lock:
            self._subagent_latencies[subagent].append(duration_ms)

    def record_error(self, error_type: str) -> None:
        """Increments error counter by category.

        Args:
            error_type: Error class or category name.
        """
        with self._collector_lock:
            self._error_counter[error_type] += 1

    def get_subagent_percentiles(self) -> Dict[str, Dict[str, float]]:
        """Calculates latency distribution percentiles for all monitored subagents.

        Returns:
            Nested dictionary mapping subagent to mean, p50, p90, p95, and p99 latencies.
        """
        results: Dict[str, Dict[str, float]] = {}
        with self._collector_lock:
            for subagent, latencies in self._subagent_latencies.items():
                if not latencies:
                    continue
                sorted_l = sorted(latencies)
                n = len(sorted_l)

                def get_p(p: float) -> float:
                    return sorted_l[min(int(p * n), n - 1)]

                results[subagent] = {
                    "count": float(n),
                    "mean_ms": round(sum(sorted_l) / n, 2),
                    "p50_ms": round(get_p(0.50), 2),
                    "p90_ms": round(get_p(0.90), 2),
                    "p95_ms": round(get_p(0.95), 2),
                    "p99_ms": round(get_p(0.99), 2),
                }
        return results

    def export_prometheus_text(self) -> str:
        """Formats collected metrics into standard Prometheus exposition format.

        Returns:
            Prometheus text format string.
        """
        lines: List[str] = [
            "# HELP deletion_audit_requests_total Total number of deletion audit requests evaluated",
            "# TYPE deletion_audit_requests_total counter",
        ]
        with self._collector_lock:
            for status, count in self._request_counter.items():
                lines.append(f'deletion_audit_requests_total{{status="{status}"}} {count}')

            lines.append("# HELP deletion_audit_errors_total Total audit errors encountered")
            lines.append("# TYPE deletion_audit_errors_total counter")
            for err, count in self._error_counter.items():
                lines.append(f'deletion_audit_errors_total{{error_type="{err}"}} {count}')

        percentiles = self.get_subagent_percentiles()
        lines.append("# HELP deletion_audit_subagent_latency_p95_ms P95 latency per subagent in ms")
        lines.append("# TYPE deletion_audit_subagent_latency_p95_ms gauge")
        for subagent, stats in percentiles.items():
            lines.append(f'deletion_audit_subagent_latency_p95_ms{{subagent="{subagent}"}} {stats["p95_ms"]}')

        return "\n".join(lines) + "\n"
