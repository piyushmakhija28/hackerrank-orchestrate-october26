"""Concurrency, multi-threaded worker pools, and performance stress test suite.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Evaluates ThreadPoolExecutor parallel execution, lock contention, and output ordering.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
import pytest

from code.container import AuditContainer
from code.engine.concurrent_orchestrator import ConcurrentAuditOrchestrator
from code.security.rate_limiter import TokenBucketRateLimiter
from code.utils.schema_validator import OutputSchemaValidator


def test_concurrent_orchestrator_multi_worker_execution(tmp_path: Path) -> None:
    """Verify concurrent orchestrator processes sample dataset using parallel workers."""
    sample_csv = Path("dataset/sample_deletion_requests.csv")
    output_csv = tmp_path / "concurrent_sample_output.csv"

    container = AuditContainer()
    concurrent_orch = ConcurrentAuditOrchestrator(container=container, max_workers=4)

    start_time = time.perf_counter()
    results = concurrent_orch.run_pipeline_concurrent(
        requests_csv=sample_csv,
        output_csv=output_csv,
        max_workers=4,
    )
    elapsed = time.perf_counter() - start_time

    assert len(results) == 32
    assert output_csv.exists()
    assert elapsed < 5.0, f"Concurrent execution took too long: {elapsed}s"

    is_valid, count, errors = OutputSchemaValidator.validate_file(output_csv)
    assert is_valid, f"Concurrent output schema invalid: {errors}"
    assert count == 32


def test_concurrent_rate_limiter_thread_safety() -> None:
    """Verify TokenBucketRateLimiter sustains 50 concurrent threads without race conditions."""
    limiter = TokenBucketRateLimiter(capacity=200.0, refill_rate=50.0)
    successful_acquires = 0

    def worker_acquire() -> int:
        count = 0
        for _ in range(10):
            if limiter.acquire():
                count += 1
        return count

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker_acquire) for _ in range(50)]
        for f in as_completed(futures):
            successful_acquires += f.result()

    assert successful_acquires <= 250, f"Tokens acquired exceeded maximum burst capacity: {successful_acquires}"
    assert successful_acquires > 0


def test_concurrent_output_natural_numeric_sorting(tmp_path: Path) -> None:
    """Verify that parallel worker execution preserves natural numeric case sorting."""
    sample_csv = Path("dataset/sample_deletion_requests.csv")
    output_csv = tmp_path / "sorted_test_output.csv"

    container = AuditContainer()
    concurrent_orch = ConcurrentAuditOrchestrator(container=container, max_workers=8)
    results = concurrent_orch.run_pipeline_concurrent(
        requests_csv=sample_csv,
        output_csv=output_csv,
        max_workers=8,
    )

    case_numbers = [int(r.case_id.split("_")[1]) for r in results if r.case_id.startswith("case_")]
    assert case_numbers == sorted(case_numbers), "Output cases were not sorted numerically"
