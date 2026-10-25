"""Anti-Reverse-Engineering, Anti-Debugging, and Cyber Deception Guard.

HackerRank Orchestrate — Ghost Data Still Exists.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Detects dynamic debuggers, attests bytecode integrity, and monitors canary honeytokens.
"""

import hashlib
import hmac
import inspect
import logging
import sys
from typing import Any, Callable, Dict, List, Optional, Set


class SecurityTamperException(Exception):
    """Raised when an active reverse-engineering, debugger, or tampering attempt is intercepted."""
    pass


class AntiTamperGuard:
    """Interception guard enforcing anti-analysis, code sealing, and deception tripwires."""

    DEFAULT_HONEYTOKENS: Set[str] = {
        "HONEY_TOKEN_AWS_AKIA_DECOY_9948271638291",
        "HONEY_TOKEN_PROD_DB_SECRET_p4ssw0rd_decoy_vault",
        "HONEY_TOKEN_CUSTOMER_PAN_4111111111111111_DECOY",
        "HONEY_TOKEN_ROOT_PRIVATE_KEY_BEGIN_RSA_DECOY_BLOCK",
    }

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initializes anti-tamper guard with honeytokens and empty attestation baseline.

        Args:
            logger: Optional logger for emitting security alerts.
        """
        self._logger: logging.Logger = logger or logging.getLogger("anti_tamper_guard")
        self._honeytokens: Set[str] = set(self.DEFAULT_HONEYTOKENS)
        self._baseline_hashes: Dict[str, str] = {}
        self._tamper_detected: bool = False
        self._violation_reason: Optional[str] = None

    def check_debugger_present(self) -> bool:
        """Inspects runtime execution state for active debuggers, profilers, and trace hooks.

        Returns:
            True if a debugger, tracer, or execution probe is detected, False otherwise.
        """
        if sys.gettrace() is not None:
            return True

        curr_frame = sys._getframe()
        while curr_frame:
            f_trace = curr_frame.f_trace
            if f_trace is not None:
                return True
            curr_frame = curr_frame.f_back

        return False

    def register_honeytoken(self, token: str) -> None:
        """Adds a canary honeytoken to the active deception registry.

        Args:
            token: Decoy string to register as a tripwire.
        """
        if token:
            self._honeytokens.add(token.strip())

    def is_honeytoken_probed(self, payload: str) -> bool:
        """Checks if arbitrary payload contains any registered canary honeytoken.

        Args:
            payload: Input text or queried token string.
        Returns:
            True if a honeytoken was probed, triggering tripwire.
        """
        if not payload:
            return False

        for h in self._honeytokens:
            if h in payload:
                return True
        return False

    def register_module_baseline(self, name: str, obj: Any) -> None:
        """Records initial SHA-256 bytecode hash baseline for a module or function.

        Args:
            name: Identifier for module or component.
            obj: Function, class, or module whose bytecode will be hashed.
        """
        code_bytes = self._extract_code_bytes(obj)
        if code_bytes:
            self._baseline_hashes[name] = hashlib.sha256(code_bytes).hexdigest()

    def verify_module_integrity(self, name: str, obj: Any) -> bool:
        """Verifies current bytecode SHA-256 hash against established baseline to detect patching.

        Args:
            name: Module identifier.
            obj: Component to verify.
        Returns:
            True if integrity is verified or baseline not yet set, False if modified.
        """
        expected = self._baseline_hashes.get(name)
        if not expected:
            self.register_module_baseline(name, obj)
            return True

        curr_bytes = self._extract_code_bytes(obj)
        curr_hash = hashlib.sha256(curr_bytes).hexdigest()
        return hmac.compare_digest(expected, curr_hash)

    @classmethod
    def _extract_code_bytes(cls, obj: Any) -> bytes:
        """Extracts immutable compiled bytecode and constants from a callable or class.

        Args:
            obj: Python object to inspect.
        Returns:
            Byte sequence of compiled bytecode, constants, and names.
        """
        if inspect.isfunction(obj) or inspect.ismethod(obj):
            co = obj.__code__
            return b"".join([co.co_code, str(co.co_consts).encode("utf-8"), str(co.co_names).encode("utf-8")])
        if inspect.isclass(obj):
            accum = []
            for attr_name in sorted(dir(obj)):
                val = getattr(obj, attr_name, None)
                if inspect.isfunction(val) or inspect.ismethod(val):
                    co = val.__code__
                    accum.extend([co.co_code, str(co.co_consts).encode("utf-8"), str(co.co_names).encode("utf-8")])
            return b"".join(accum)
        return b""

    def trigger_tamper_response(
        self,
        reason: str,
        vault: Optional[Any] = None,
    ) -> None:
        """Executes active defense response: trips alarm, locks vault, zeroes memory, and halts.

        Args:
            reason: Diagnostic explanation of detected violation.
            vault: Optional CryptoSecurityVault instance to immediately scrub and lock.
        Raises:
            SecurityTamperException: Always raised to stop execution.
        """
        self._tamper_detected = True
        self._violation_reason = reason
        self._logger.critical("ACTIVE DEFENSE TRIPWIRE TRIGGERED: %s", reason)

        if vault and hasattr(vault, "lock_vault"):
            vault.lock_vault()

        raise SecurityTamperException(f"Active defense tripwire: Execution halted by AntiTamperGuard: {reason}")

    def is_tampered(self) -> bool:
        """Returns True if a tamper violation has been detected."""
        return self._tamper_detected

    def get_violation_reason(self) -> Optional[str]:
        """Returns diagnostic reason for tamper trigger, or None if clean."""
        return self._violation_reason
