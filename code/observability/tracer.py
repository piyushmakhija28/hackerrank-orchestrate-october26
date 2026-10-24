"""Distributed tracing engine tracking subagent execution spans and critical paths.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Adheres to OpenTelemetry-compatible span semantics for subagent DAG orchestration.
"""

from collections import defaultdict
import threading
import time
from typing import Any, Dict, List, Optional
import uuid


class Span:
    """Represents a discrete unit of subagent work with timing and tags."""

    def __init__(
        self,
        name: str,
        subagent: str,
        trace_id: str,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> None:
        """Initializes span attributes and identifiers.

        Args:
            name: Human-readable operation name.
            subagent: Subagent identifier executing the operation.
            trace_id: Root trace identifier.
            span_id: Unique span identifier.
            parent_span_id: Parent span identifier.
        """
        self.name: str = name
        self.subagent: str = subagent
        self.trace_id: str = trace_id
        self.span_id: str = span_id or uuid.uuid4().hex[:12]
        self.parent_span_id: Optional[str] = parent_span_id
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration_ms: float = 0.0
        self.status: str = "OK"
        self.tags: Dict[str, Any] = {}
        self.error_message: Optional[str] = None

    def __enter__(self) -> "Span":
        """Starts timing upon entering context block.

        Returns:
            The active Span instance.
        """
        self.start_time = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Stops timing upon exiting context block and captures exceptions.

        Args:
            exc_type: Exception class if raised.
            exc_val: Exception instance if raised.
            exc_tb: Traceback object if raised.
        """
        self.end_time = time.perf_counter()
        self.duration_ms = round((self.end_time - self.start_time) * 1000.0, 3)
        if exc_val:
            self.status = "ERROR"
            self.error_message = str(exc_val)

    def set_tag(self, key: str, value: Any) -> "Span":
        """Attaches arbitrary metadata key-value pair to span.

        Args:
            key: Tag attribute name.
            value: Tag value.
        Returns:
            Self for method chaining.
        """
        self.tags[key] = value
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serializes span into dictionary.

        Returns:
            Structured span dictionary.
        """
        return {
            "name": self.name,
            "subagent": self.subagent,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "tags": self.tags,
            "error": self.error_message,
        }


class DistributedTracer:
    """Thread-safe distributed tracer managing active trace spans."""

    _instance: Optional["DistributedTracer"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Initializes in-memory span registry."""
        self._traces: Dict[str, List[Span]] = defaultdict(list)
        self._trace_lock: threading.Lock = threading.Lock()

    @classmethod
    def get_tracer(cls) -> "DistributedTracer":
        """Retrieves or creates the global singleton DistributedTracer.

        Returns:
            The global DistributedTracer instance.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Clears all accumulated traces for clean test isolation."""
        with cls._lock:
            cls._instance = cls()

    def start_trace(self, case_id: str) -> str:
        """Initiates a new root trace for a given case.

        Args:
            case_id: The unique deletion request identifier.
        Returns:
            Globally unique trace identifier string.
        """
        suffix = uuid.uuid4().hex[:8]
        return f"trace_{case_id}_{suffix}"

    def create_span(
        self,
        name: str,
        subagent: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
    ) -> Span:
        """Creates and registers a new Span within an active trace.

        Args:
            name: Operation name.
            subagent: Subagent name.
            trace_id: Global trace key.
            parent_span_id: Optional parent span key.
        Returns:
            Constructed Span instance.
        """
        span = Span(
            name=name,
            subagent=subagent,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        with self._trace_lock:
            self._traces[trace_id].append(span)
        return span

    def get_spans_for_trace(self, trace_id: str) -> List[Span]:
        """Retrieves all spans recorded under a given trace.

        Args:
            trace_id: Global trace key.
        Returns:
            List of recorded Span instances.
        """
        with self._trace_lock:
            return list(self._traces.get(trace_id, []))
