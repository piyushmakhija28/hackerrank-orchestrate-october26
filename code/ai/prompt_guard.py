"""Prompt Engineering (D47) and Anti-Hallucination Guard Subsystem.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Enforces witness grounding, schema integrity, and negative constraint validation.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class PromptGuard:
    """Verifies evidence witnesses, validates step schemas, and disarms hallucinations.

    Attributes:
        ALLOWED_OPERATIONS: Set of 15 allowed AuditOperation strings.
        ALLOWED_PHASES: Set of 3 allowed AuditPhase strings.
        ALLOWED_STATES: Set of 7 allowed AuditState strings.
        ALLOWED_STEP_KEYS: Set of 7 mandatory and exclusive step keys.
        manifest_evidence_ids: Set of valid participant-visible evidence file IDs.
        manifest_capture_times: Mapping of evidence IDs to their ISO-8601 capture timestamps.
        manifest_path: Path to evidence_files.csv.
        rejected_hallucinations_count: Counter of dropped ungrounded steps.
    """

    ALLOWED_PHASES: Set[str] = {
        "FINDING",
        "REMEDIATION",
        "VERIFICATION",
    }

    ALLOWED_OPERATIONS: Set[str] = {
        "REPORT_REMAINING_RECORD",
        "REPORT_EXPOSED_PII",
        "REPORT_ACTIVE_DATA_FLOW",
        "REPORT_RESTORE_RISK",
        "DISABLE_DATA_FLOW",
        "BLOCK_RESTORE",
        "DELETE_RECORD",
        "REDACT_RECORD",
        "ANONYMIZE_RECORD",
        "VERIFY_RECORD_ABSENT",
        "VERIFY_RECORD_PRESENT",
        "VERIFY_RECORD_REDACTED",
        "VERIFY_RECORD_ANONYMIZED",
        "VERIFY_DATA_FLOW_DISABLED",
        "VERIFY_RESTORE_BLOCKED",
    }

    ALLOWED_STATES: Set[str] = {
        "PRESENT",
        "ABSENT",
        "REDACTED",
        "ANONYMIZED",
        "ACTIVE",
        "DISABLED",
        "BLOCKED",
    }

    ALLOWED_STEP_KEYS: Set[str] = {
        "step_no",
        "phase",
        "system_id",
        "resource_id",
        "operation",
        "state",
        "evidence_id",
    }

    def __init__(self, manifest_path: Path) -> None:
        """Initializes prompt guard, loading manifest evidence and activity IDs.

        Args:
            manifest_path: Path to evidence_files.csv manifest file.
        """
        self.manifest_path: Path = manifest_path
        self.manifest_evidence_ids: Set[str] = set()
        self.manifest_capture_times: Dict[str, str] = {}
        self.rejected_hallucinations_count: int = 0
        self.load_manifest()

    def load_manifest(self) -> None:
        """Loads all participant-visible evidence IDs and timestamps from manifest files."""
        if not self.manifest_path.exists():
            return

        with open(self.manifest_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fid = (row.get("file_id") or "").strip()
                cap_at = (row.get("captured_at") or "").strip()
                if fid:
                    self.manifest_evidence_ids.add(fid)
                    if cap_at:
                        self.manifest_capture_times[fid] = cap_at

        parent_dir = self.manifest_path.parent
        act_csv = parent_dir / "system_activity.csv"
        if act_csv.exists():
            with open(act_csv, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    aid = (row.get("activity_id") or "").strip()
                    ev_time = (row.get("event_time") or "").strip()
                    if aid:
                        self.manifest_evidence_ids.add(aid)
                        if ev_time:
                            self.manifest_capture_times[aid] = ev_time

        audit_csv = parent_dir / "user_audit_log.csv"
        if audit_csv.exists():
            with open(audit_csv, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    auid = (row.get("audit_id") or "").strip()
                    ev_time = (row.get("event_time") or "").strip()
                    if auid:
                        self.manifest_evidence_ids.add(auid)
                        if ev_time:
                            self.manifest_capture_times[auid] = ev_time

    def verify_evidence_witness(
        self,
        evidence_id: str,
        captured_at: Optional[str] = None,
        audit_at: Optional[str] = None,
    ) -> bool:
        """Verifies whether an evidence ID is participant-visible and temporally admissible.

        Args:
            evidence_id: Evidence identifier (e.g., evidence_01, activity_05).
            captured_at: Optional explicit capture timestamp.
            audit_at: Optional audit cutoff timestamp.

        Returns:
            Boolean indicating whether evidence witness is verified and grounded.
        """
        if not evidence_id:
            return False

        if evidence_id not in self.manifest_evidence_ids:
            return False

        if audit_at:
            t_cap = captured_at or self.manifest_capture_times.get(evidence_id, "")
            if t_cap and t_cap > audit_at:
                return False

        return True

    def validate_step_schema(self, step: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates dictionary representation of an audit step against schema contracts.

        Args:
            step: Audit step dictionary.

        Returns:
            Tuple of (is_valid_bool, error_message_or_none).
        """
        step_keys = set(step.keys())
        if step_keys != self.ALLOWED_STEP_KEYS:
            missing = self.ALLOWED_STEP_KEYS - step_keys
            extra = step_keys - self.ALLOWED_STEP_KEYS
            return False, f"Invalid step keys: missing={missing}, extra={extra}"

        step_no = step.get("step_no")
        if not isinstance(step_no, int) or step_no < 1:
            return False, f"step_no must be positive integer, got: {step_no}"

        phase = step.get("phase")
        if phase not in self.ALLOWED_PHASES:
            return False, f"Disallowed phase: {phase}"

        op = step.get("operation")
        if op not in self.ALLOWED_OPERATIONS:
            return False, f"Disallowed operation: {op}"

        st = step.get("state")
        if st not in self.ALLOWED_STATES:
            return False, f"Disallowed state: {st}"

        ev_id = step.get("evidence_id")
        if phase == "REMEDIATION" and ev_id != "":
            return False, "Remediation step must have empty evidence_id"

        return True, None

    def disarm_hallucinations(
        self,
        findings: List[Dict[str, Any]],
        verifications: List[Dict[str, Any]],
        audit_at: str,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Disarms ungrounded candidate findings and sanitizes remediation evidence IDs.

        Args:
            findings: Candidate findings list.
            verifications: Candidate verification steps list.
            audit_at: Audit cutoff timestamp.

        Returns:
            Tuple of (grounded_findings, verified_verifications).
        """
        grounded_findings: List[Dict[str, Any]] = []
        for f in findings:
            ev_id = f.get("evidence_id", "")
            if not self.verify_evidence_witness(ev_id, audit_at=audit_at):
                self.rejected_hallucinations_count += 1
            else:
                grounded_findings.append(f)

        grounded_verifications: List[Dict[str, Any]] = []
        for v in verifications:
            ev_id = v.get("evidence_id", "")
            if ev_id and not self.verify_evidence_witness(ev_id, audit_at=audit_at):
                self.rejected_hallucinations_count += 1
            else:
                grounded_verifications.append(v)

        return grounded_findings, grounded_verifications

    def validate_negative_constraints(
        self, verdict: str, steps: List[Dict[str, Any]]
    ) -> bool:
        """Validates negative constraints: NOT_APPLICABLE produces empty array; COMPLETE has no findings.

        Args:
            verdict: Deletion status verdict (COMPLETE, INCOMPLETE, NOT_APPLICABLE).
            steps: List of step dictionaries.

        Returns:
            Boolean indicating compliance with negative constraints.
        """
        if verdict == "NOT_APPLICABLE":
            return len(steps) == 0

        if verdict == "COMPLETE":
            return not any(s.get("phase") == "FINDING" for s in steps)

        if verdict == "INCOMPLETE":
            has_finding = any(s.get("phase") == "FINDING" for s in steps)
            has_remediation = any(s.get("phase") == "REMEDIATION" for s in steps)
            has_verification = any(s.get("phase") == "VERIFICATION" for s in steps)
            return has_finding and has_remediation and has_verification

        return False
