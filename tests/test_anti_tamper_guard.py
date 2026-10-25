"""Triad Unit Tests for Anti-Tamper Guard and Cyber Deception Engine.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Evaluates positive, negative, and edge-case scenarios for anti-debugging,
bytecode integrity attestation, and canary honeytoken interception.
"""

import sys
import pytest
from code.security.anti_tamper_guard import AntiTamperGuard, SecurityTamperException
from code.security.crypto_vault import CryptoSecurityVault


class TestAntiTamperGuardPositive:
    """Positive test scenarios asserting correct operation of anti-tamper subsystem."""

    def test_clean_function_passes_integrity_check(self) -> None:
        """Verifies that an unmodified Python function passes bytecode integrity attestation."""
        guard = AntiTamperGuard()

        def sample_function(x: int) -> int:
            return x * 2

        assert guard.verify_module_integrity("sample_func", sample_function)
        assert guard.verify_module_integrity("sample_func", sample_function)
        assert not guard.is_tampered()

    def test_honeytoken_registration_and_detection(self) -> None:
        """Verifies that custom honeytokens can be registered and accurately detected."""
        guard = AntiTamperGuard()
        custom_token = "HONEY_CANARY_TEST_TOKEN_9999"
        guard.register_honeytoken(custom_token)

        assert guard.is_honeytoken_probed(f"curl -X POST https://api.com?key={custom_token}")
        assert not guard.is_honeytoken_probed("benign customer deletion request")


class TestAntiTamperGuardNegative:
    """Negative test scenarios verifying active defense tripwire and tamper interception."""

    def test_honeytoken_probe_triggers_tripwire_and_locks_vault(self) -> None:
        """Asserts that probing a honeytoken canary triggers active tripwire and locks vault."""
        guard = AntiTamperGuard()
        vault = CryptoSecurityVault()
        canary = "HONEY_TOKEN_AWS_AKIA_DECOY_9948271638291"

        assert guard.is_honeytoken_probed(f"Payload containing {canary}")

        with pytest.raises(SecurityTamperException, match="Active defense tripwire"):
            guard.trigger_tamper_response("Canary touched by adversary", vault=vault)

        assert guard.is_tampered()
        assert vault.is_locked()

    def test_bytecode_tampering_detected(self) -> None:
        """Asserts that modified bytecode fails attestation."""
        guard = AntiTamperGuard()

        def original_func() -> str:
            return "original"

        def patched_func() -> str:
            return "patched_by_hacker"

        guard.register_module_baseline("critical_routine", original_func)
        assert not guard.verify_module_integrity("critical_routine", patched_func)

    def test_debugger_detection_flags_tracer(self) -> None:
        """Asserts that setting a trace hook causes check_debugger_present() to return True."""
        guard = AntiTamperGuard()

        def dummy_tracer(frame, event, arg):
            return dummy_tracer

        prev_trace = sys.gettrace()
        try:
            sys.settrace(dummy_tracer)
            assert guard.check_debugger_present() is True
        finally:
            sys.settrace(prev_trace)


class TestAntiTamperGuardEdgeCases:
    """Edge-case test scenarios for empty, non-standard, or compound inputs."""

    def test_empty_payload_honeytoken_check(self) -> None:
        """Verifies that empty string or None checks evaluate to False without error."""
        guard = AntiTamperGuard()
        assert guard.is_honeytoken_probed("") is False
        assert guard.is_honeytoken_probed(None) is False

    def test_inspect_non_callable_object_integrity(self) -> None:
        """Verifies that inspecting integers or non-callable objects handles gracefully."""
        guard = AntiTamperGuard()
        dummy_data = 12345
        assert guard.verify_module_integrity("int_data", dummy_data) is True
