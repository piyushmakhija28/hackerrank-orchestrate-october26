"""Thread-safe rate limiter and concurrency circuit breaker.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Protects against unbounded resource consumption and denial of service (OWASP LLM10).
"""

import threading
import time
from typing import Optional


class RateLimitExceededError(Exception):
    """Raised when a request exceeds token bucket rate limit capacity."""
    pass


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN due to repeated system failures."""
    pass


class TokenBucketRateLimiter:
    """Thread-safe Token Bucket rate limiter controlling burst request concurrency."""

    def __init__(self, capacity: float = 500.0, refill_rate: float = 100.0) -> None:
        """Initializes token bucket with maximum burst capacity and refill rate.

        Args:
            capacity: Maximum burst capacity tokens.
            refill_rate: Tokens added per second.
        """
        self._capacity: float = capacity
        self._refill_rate: float = refill_rate
        self._tokens: float = capacity
        self._last_refill: float = time.monotonic()
        self._lock: threading.Lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> bool:
        """Attempts to acquire specified number of tokens atomically.

        Args:
            tokens: Number of tokens requested.
        Returns:
            True if tokens were acquired, False if capacity is exhausted.
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
            self._last_refill = now

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def get_available_tokens(self) -> float:
        """Returns the current available token balance.

        Returns:
            Current floating-point token balance.
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            return min(self._capacity, self._tokens + elapsed * self._refill_rate)


class ConcurrentCircuitBreaker:
    """Thread-safe Circuit Breaker preventing cascading failure propagation."""

    STATE_CLOSED: str = "CLOSED"
    STATE_OPEN: str = "OPEN"
    STATE_HALF_OPEN: str = "HALF_OPEN"

    def __init__(self, failure_threshold: int = 5, recovery_timeout_sec: float = 30.0) -> None:
        """Initializes circuit breaker with failure threshold and recovery timeout.

        Args:
            failure_threshold: Consecutive failures needed to trip the circuit breaker.
            recovery_timeout_sec: Cooldown seconds before transitioning from OPEN to HALF_OPEN.
        """
        self._failure_threshold: int = failure_threshold
        self._recovery_timeout_sec: float = recovery_timeout_sec
        self._state: str = self.STATE_CLOSED
        self._failure_count: int = 0
        self._last_state_change: float = time.monotonic()
        self._lock: threading.Lock = threading.Lock()

    @property
    def state(self) -> str:
        """Returns the current operational state of the circuit breaker."""
        with self._lock:
            self._evaluate_state_transition()
            return self._state

    def _evaluate_state_transition(self) -> None:
        """Evaluates whether an OPEN circuit breaker should transition to HALF_OPEN."""
        if self._state == self.STATE_OPEN:
            now = time.monotonic()
            if now - self._last_state_change >= self._recovery_timeout_sec:
                self._state = self.STATE_HALF_OPEN
                self._last_state_change = now

    def can_execute(self) -> bool:
        """Determines whether a protected operation is permitted to execute.

        Returns:
            True if state is CLOSED or HALF_OPEN; False if OPEN.
        """
        with self._lock:
            self._evaluate_state_transition()
            return self._state != self.STATE_OPEN

    def record_success(self) -> None:
        """Records a successful operation, resetting failure counter and closing circuit."""
        with self._lock:
            self._failure_count = 0
            if self._state != self.STATE_CLOSED:
                self._state = self.STATE_CLOSED
                self._last_state_change = time.monotonic()

    def record_failure(self) -> None:
        """Records a failed operation, tripping the circuit if failure threshold is reached."""
        with self._lock:
            self._failure_count += 1
            if self._failure_count >= self._failure_threshold:
                self._state = self.STATE_OPEN
                self._last_state_change = time.monotonic()
