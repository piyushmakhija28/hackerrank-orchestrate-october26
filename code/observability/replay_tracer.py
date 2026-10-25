"""Deterministic Replay Engine and Diagnostic RCA Report Generator.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Captures full decision graphs per case for reproducible compliance debugging.
"""

from typing import Any, Dict, List, Optional, Set
import json
from pathlib import Path
import threading
from code.security.crypto_vault import CryptoSecurityVault


class ReplayTracer:
    """Thread-safe registry of deterministic decision graphs supporting RCA debugging."""

    _instance: Optional["ReplayTracer"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, max_capacity: int = 2000) -> None:
        """Initializes empty decision graph storage with bounded LRU eviction capacity.

        Args:
            max_capacity: Maximum number of decision graphs to retain before evicting oldest.
        """
        self._traces: Dict[str, Dict[str, Any]] = {}
        self.max_capacity: int = max_capacity
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
            if len(self._traces) >= self.max_capacity and case_id not in self._traces:
                oldest_key = next(iter(self._traces))
                del self._traces[oldest_key]
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

    def export_encrypted_traces(
        self,
        target_path: Path,
        vault: Optional[CryptoSecurityVault] = None,
    ) -> Path:
        """Serializes and encrypts all stored decision traces to disk via AES-256-GCM.

        Args:
            target_path: Destination path for .enc journal file.
            vault: CryptoSecurityVault instance for authenticated encryption.
        Returns:
            Resolved Path of the written encrypted trace file.
        """
        active_vault = vault or CryptoSecurityVault()
        with self._registry_lock:
            serializable_traces = {}
            for cid, trace in self._traces.items():
                copy_tr = dict(trace)
                copy_tr["identity_cluster"] = sorted(list(copy_tr.get("identity_cluster", set())))
                serializable_traces[cid] = copy_tr

        raw_bytes = json.dumps(serializable_traces, ensure_ascii=False, indent=2).encode("utf-8")
        encrypted_bytes = active_vault.encrypt(raw_bytes, associated_data=b"NorthstarShop_ReplayTraces_2026")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_target = target_path.with_suffix(target_path.suffix + ".tmp")
        tmp_target.write_bytes(encrypted_bytes)
        tmp_target.replace(target_path)
        return target_path

    def load_encrypted_traces(
        self,
        source_path: Path,
        vault: Optional[CryptoSecurityVault] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Reads and decrypts stored decision traces from an AES-256-GCM encrypted file.

        Args:
            source_path: Path to encrypted trace journal.
            vault: CryptoSecurityVault instance for decryption.
        Returns:
            Dictionary of case_id to trace objects.
        """
        active_vault = vault or CryptoSecurityVault()
        encrypted_bytes = source_path.read_bytes()
        decrypted_bytes = active_vault.decrypt(encrypted_bytes, associated_data=b"NorthstarShop_ReplayTraces_2026")
        loaded_data = json.loads(decrypted_bytes.decode("utf-8"))

        with self._registry_lock:
            for cid, trace in loaded_data.items():
                trace["identity_cluster"] = set(trace.get("identity_cluster", []))
                self._traces[cid] = trace

        return loaded_data
