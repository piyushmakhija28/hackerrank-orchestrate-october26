"""Deterministic Replay Engine and Diagnostic RCA Report Generator.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Captures full decision graphs per case for reproducible compliance debugging.
"""

from typing import Any, Dict, List, Optional, Set
import json
import threading


class ReplayTracer:
    """Thread-safe registry of deterministic decision graphs supporting RCA debugging."""

    _instance: Optional["ReplayTracer"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Initializes empty decision graph storage."""
        self._traces: Dict[str, Dict[str, Any]] = {}
        self._registry_lock: threading.Lock = threading.Lock()

    @classmethod
    def get_tracer(cls) -> "ReplayTracer":
        """Retrieves or instantiates the singleton ReplayTracer.

        Returns:
            The global ReplayTracer instance.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Resets stored replay traces for clean test isolation."""
        with cls._lock:
            cls._instance = cls()

    def record_decision(
        self,
        case_id: str,
        verdict: str,
        seed_email: str,
        cluster: Set[str],
        findings: List[Dict[str, Any]],
        verifications: List[Dict[str, Any]],
        steps: List[Dict[str, Any]],
        rules_applied: List[Dict[str, Any]],
        duration_ms: float,
    ) -> None:
        """Records the complete decision graph for an audited case.

        Args:
            case_id: The unique deletion request identifier.
            verdict: Final audit status (COMPLETE, INCOMPLETE, NOT_APPLICABLE).
            seed_email: Input email from request row.
            cluster: Resolved transitive identity tokens.
            findings: Detected evidence findings.
            verifications: Generated compliance verification assertions.
            steps: Final ordered Poset steps array.
            rules_applied: Retention rules evaluated during audit.
            duration_ms: Total turnaround latency in milliseconds.
        """
        trace_record: Dict[str, Any] = {
            "case_id": case_id,
            "verdict": verdict,
            "seed_email": seed_email,
            "identity_cluster": sorted(list(cluster)),
            "findings": findings,
            "verifications": verifications,
            "steps": steps,
            "rules_applied": rules_applied,
            "duration_ms": duration_ms,
        }
        with self._registry_lock:
            self._traces[case_id] = trace_record

    def get_replay_trace(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the raw decision graph dictionary for a given case.

        Args:
            case_id: Case identifier.
        Returns:
            Dictionary containing the case decision trace, or None if not found.
        """
        with self._registry_lock:
            if case_id in self._traces:
                return self._traces[case_id]
            norm = case_id.strip().lower()
            if norm in self._traces:
                return self._traces[norm]
            for k, v in self._traces.items():
                if k.lower() == norm or k.lower().replace("_0", "_") == norm.replace("_0", ""):
                    return v
            return None

    def format_diagnostic_report(self, case_id: str) -> str:
        """Formats a human-readable ASCII diagnostic RCA report for compliance debugging.

        Args:
            case_id: The request identifier to inspect.
        Returns:
            Multi-line diagnostic report string.
        """
        trace = self.get_replay_trace(case_id)
        if not trace:
            return f"[ERROR] No diagnostic replay trace found for case '{case_id}'. Ensure pipeline has run."

        lines: List[str] = [
            "=" * 80,
            f"DELETION AUDIT DIAGNOSTIC RCA REPORT: {case_id}",
            f"Final Verdict : {trace['verdict']}",
            f"Seed Email    : {trace['seed_email']}",
            f"Execution Time: {trace['duration_ms']:.2f} ms",
            "-" * 80,
            f"1. Transitive Identity Cluster (DSU - {len(trace['identity_cluster'])} tokens):",
        ]
        for token in trace["identity_cluster"]:
            lines.append(f"   • {token}")

        lines.append("-" * 80)
        lines.append(f"2. Residual Evidence Findings ({len(trace['findings'])} items):")
        if not trace["findings"]:
            lines.append("   (None - Zero un-scrubbed records or active data flows detected)")
        else:
            for f in trace["findings"]:
                lines.append(
                    f"   [!] {f.get('system_id')}:{f.get('resource_id')} -> {f.get('operation')} ({f.get('state')}) [Evidence: {f.get('evidence_id')}]"
                )

        lines.append("-" * 80)
        lines.append(f"3. Statutory Retention Rules Evaluated ({len(trace['rules_applied'])} rules):")
        if not trace["rules_applied"]:
            lines.append("   (Default hard-purge policy applied)")
        else:
            for r in trace["rules_applied"]:
                lines.append(f"   • Rule {r.get('rule_id')}: {r.get('data_category')} -> {r.get('required_treatment')}")

        lines.append("-" * 80)
        lines.append(f"4. Ordered Poset Execution DAG ({len(trace['steps'])} steps):")
        if not trace["steps"]:
            lines.append("   (Empty step list - Request is NOT_APPLICABLE)")
        else:
            for s in trace["steps"]:
                ev_str = f" [Evidence: {s['evidence_id']}]" if s.get("evidence_id") else ""
                lines.append(
                    f"   Step {s.get('step_no', '?'):2d}: [{s.get('phase')}] {s.get('system_id')}:{s.get('resource_id')} -> {s.get('operation')} ({s.get('state')}){ev_str}"
                )

        lines.append("=" * 80)
        return "\n".join(lines)
