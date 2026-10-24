"""Engine package for high-throughput concurrent deletion audits.

Exports the ConcurrentAuditOrchestrator for multi-worker parallel execution.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""

from code.engine.concurrent_orchestrator import ConcurrentAuditOrchestrator

__all__ = ["ConcurrentAuditOrchestrator"]
