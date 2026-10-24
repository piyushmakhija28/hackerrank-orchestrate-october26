"""High-throughput multi-threaded concurrent orchestrator for deletion audits.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Coordinates parallel execution, thread-safe rate limiting, circuit breaking, and telemetry.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import time
from typing import Dict, List, Optional

from code.container import AuditContainer
from code.core.models import DeletionAuditOutputRow
from code.core.telemetry import AuditTelemetry
from code.observability.structured_logger import StructuredLogger
from code.security.rate_limiter import (
    CircuitBreakerOpenError,
    ConcurrentCircuitBreaker,
    RateLimitExceededError,
    TokenBucketRateLimiter,
)
from code.utils.csv_handler import CsvHandler


class ConcurrentAuditOrchestrator:
    """Thread-safe multi-worker orchestrator processing deletion requests concurrently."""

    def __init__(
        self,
        container: Optional[AuditContainer] = None,
        max_workers: int = 8,
        rate_limit_capacity: float = 1000.0,
        rate_limit_refill: float = 250.0,
    ) -> None:
        """Initializes concurrent orchestrator with dependencies and guardrails.

        Args:
            container: Optional pre-configured AuditContainer instance.
            max_workers: Thread worker pool concurrency limit.
            rate_limit_capacity: Burst capacity for token bucket rate limiter.
            rate_limit_refill: Sustained tokens added per second.
        """
        from code.main import DeletionAuditOrchestrator

        self.container: AuditContainer = container or AuditContainer()
        self.orchestrator: DeletionAuditOrchestrator = DeletionAuditOrchestrator(container=self.container)
        self.max_workers: int = max_workers
        self.rate_limiter: TokenBucketRateLimiter = TokenBucketRateLimiter(
            capacity=rate_limit_capacity,
            refill_rate=rate_limit_refill,
        )
        self.circuit_breaker: ConcurrentCircuitBreaker = ConcurrentCircuitBreaker(
            failure_threshold=10,
            recovery_timeout_sec=15.0,
        )
        self.logger: StructuredLogger = StructuredLogger.get_logger()

    def audit_single_request_safe(self, req: Dict[str, str]) -> DeletionAuditOutputRow:
        """Audits a single deletion request guarded by rate limiting and circuit breakers.

        Args:
            req: Customer request row dictionary.
        Returns:
            Populated DeletionAuditOutputRow instance.
        """
        cid = req.get("case_id") or req.get("id") or "case_unknown"

        if not self.rate_limiter.acquire():
            self.logger.warning("Rate limit exceeded for case", case_id=cid)
            raise RateLimitExceededError(f"Rate limit exceeded processing case {cid}")

        if not self.circuit_breaker.can_execute():
            self.logger.error("Circuit breaker is OPEN", case_id=cid)
            raise CircuitBreakerOpenError(f"Circuit breaker is OPEN for case {cid}")

        start_t = time.perf_counter()
        try:
            result = self.orchestrator.audit_single_request(req)
            dur_ms = (time.perf_counter() - start_t) * 1000.0
            self.circuit_breaker.record_success()
            steps_data = json.loads(result.steps_json)
            findings_count = sum(1 for s in steps_data if s.get("phase") == "FINDING")
            remediations_count = sum(1 for s in steps_data if s.get("phase") == "REMEDIATION")
            AuditTelemetry.get_instance().record_case_audit(
                case_id=result.case_id,
                status=result.deletion_status,
                duration_ms=dur_ms,
                findings_count=findings_count,
                remediations_count=remediations_count,
            )
            return result
        except Exception as exc:
            self.circuit_breaker.record_failure()
            self.logger.error("Error executing case audit in worker", exc=exc, case_id=cid)
            raise

    def run_pipeline_concurrent(
        self,
        requests_csv: Path,
        output_csv: Path,
        max_workers: Optional[int] = None,
    ) -> List[DeletionAuditOutputRow]:
        """Runs the audit pipeline across all cases using parallel worker threads.

        Args:
            requests_csv: Path to input deletion_requests.csv.
            output_csv: Destination path for output.csv.
            max_workers: Optional override for worker count.
        Returns:
            List of generated DeletionAuditOutputRow instances naturally sorted.
        """
        requests = CsvHandler.read_csv_safe(requests_csv)
        workers = max_workers or self.max_workers
        results_by_case: Dict[str, DeletionAuditOutputRow] = {}

        self.logger.info("Starting concurrent deletion audit pipeline", total_cases=len(requests), workers=workers)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_case = {
                executor.submit(self.audit_single_request_safe, req): req.get("case_id", "")
                for req in requests
            }
            for future in as_completed(future_to_case):
                row_result = future.result()
                results_by_case[row_result.case_id] = row_result

        def extract_case_num(row: DeletionAuditOutputRow) -> int:
            parts = row.case_id.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])
            return 999999

        sorted_results = sorted(results_by_case.values(), key=extract_case_num)
        CsvHandler.write_output_csv(output_csv, sorted_results)

        self.logger.info("Concurrent pipeline execution finished", audited_count=len(sorted_results), output_path=str(output_csv))
        return sorted_results
