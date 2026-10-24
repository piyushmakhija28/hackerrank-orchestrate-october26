"""Structured JSON Logger with Mapped Diagnostic Context (MDC) and PII redaction.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Adheres to dual-appender (console + file) pattern and OWASP sensitive data rules.
"""

from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import threading
from typing import Any, Dict, Optional

from code.security.pii_shield import PiiShield


class StructuredLogger:
    """Thread-safe and async-safe structured JSON logger emitting audit-compliant logs."""

    _instance: Optional["StructuredLogger"] = None
    _lock: threading.Lock = threading.Lock()
    _context_var: ContextVar[Dict[str, str]] = ContextVar("mdc_context", default={})

    def __init__(
        self,
        service_name: str = "northstar-deletion-audit-agent",
        log_file: Optional[Path] = None,
        level: int = logging.INFO,
    ) -> None:
        """Initializes structured logger with service identification and log handlers.

        Args:
            service_name: Service name identifier embedded in all JSON records.
            log_file: Optional file destination for rotating JSON lines logs.
            level: Logging verbosity threshold.
        """
        self._service_name: str = service_name
        self._logger: logging.Logger = logging.getLogger(service_name)
        self._logger.setLevel(level)
        self._logger.propagate = False

        if not self._logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            self._logger.addHandler(console_handler)

            if log_file:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
                file_handler.setLevel(level)
                self._logger.addHandler(file_handler)

    @classmethod
    def get_logger(
        cls,
        service_name: str = "northstar-deletion-audit-agent",
        log_file: Optional[Path] = Path("logs/audit_agent.jsonl"),
        level: int = logging.INFO,
    ) -> "StructuredLogger":
        """Retrieves or instantiates the global singleton StructuredLogger.

        Args:
            service_name: Service name identifier.
            log_file: Path to destination JSON lines file.
            level: Minimum log level.
        Returns:
            The singleton StructuredLogger instance.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(service_name=service_name, log_file=log_file, level=level)
            return cls._instance

    @classmethod
    def set_context(cls, trace_id: str, case_id: str, span_id: Optional[str] = None) -> None:
        """Sets thread-local and coroutine-local Mapped Diagnostic Context (MDC).

        Args:
            trace_id: Global distributed trace identifier.
            case_id: Evaluated deletion request case key.
            span_id: Current subagent execution span key.
        """
        ctx: Dict[str, str] = {
            "trace_id": trace_id,
            "case_id": case_id,
            "span_id": span_id or "root",
        }
        cls._context_var.set(ctx)

    @classmethod
    def clear_context(cls) -> None:
        """Clears the active Mapped Diagnostic Context."""
        cls._context_var.set({})

    def _format_record(self, level_name: str, event: str, metadata: Dict[str, Any]) -> str:
        """Formats an RFC-compliant JSON log record with PII masking and MDC context.

        Args:
            level_name: String name of log level (DEBUG, INFO, WARNING, ERROR).
            event: Semantic event description.
            metadata: Arbitrary structured key-value payload.
        Returns:
            Sanitized JSON line string.
        """
        ctx = self._context_var.get()
        sanitized_meta = PiiShield.sanitize_log_record(metadata)

        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level_name,
            "service": self._service_name,
            "trace_id": ctx.get("trace_id", "none"),
            "case_id": ctx.get("case_id", "none"),
            "span_id": ctx.get("span_id", "root"),
            "event": event,
            "metadata": sanitized_meta,
        }
        return json.dumps(record, ensure_ascii=False)

    def debug(self, event: str, **kwargs: Any) -> None:
        """Emits structured DEBUG log message."""
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(self._format_record("DEBUG", event, kwargs))

    def info(self, event: str, **kwargs: Any) -> None:
        """Emits structured INFO log message."""
        if self._logger.isEnabledFor(logging.INFO):
            self._logger.info(self._format_record("INFO", event, kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        """Emits structured WARNING log message."""
        if self._logger.isEnabledFor(logging.WARNING):
            self._logger.warning(self._format_record("WARNING", event, kwargs))

    def error(self, event: str, exc: Optional[Exception] = None, **kwargs: Any) -> None:
        """Emits structured ERROR log message with sanitized exception information."""
        if self._logger.isEnabledFor(logging.ERROR):
            if exc:
                kwargs["exception_type"] = exc.__class__.__name__
                kwargs["exception_message"] = PiiShield.mask_pii_in_text(str(exc))
            self._logger.error(self._format_record("ERROR", event, kwargs))
