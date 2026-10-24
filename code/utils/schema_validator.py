"""
Strict Schema and Contract Validator for output.csv.
Validates column names, JSON step schema, operation ordering, and row counts.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import csv
import json
from pathlib import Path
from typing import Tuple, List, Dict, Any, Set
from code.core.models import (
    AuditVerdict,
    AuditPhase,
    AuditOperation,
    AuditState
)

class OutputSchemaValidator:
    """Validates generated output.csv against official HackerRank challenge specifications."""

    EXPECTED_COLUMNS: List[str] = [
        "case_id",
        "deletion_status",
        "steps_json"
    ]

    VALID_STATUSES: Set[str] = {v.value for v in AuditVerdict}
    VALID_PHASES: Set[str] = {p.value for p in AuditPhase}
    VALID_OPERATIONS: Set[str] = {op.value for op in AuditOperation}
    VALID_STATES: Set[str] = {st.value for st in AuditState}

    PHASE_ORDER = {
        AuditPhase.FINDING.value: 1,
        AuditPhase.REMEDIATION.value: 2,
        AuditPhase.VERIFICATION.value: 3
    }

    @classmethod
    def validate_step(cls, step: Dict[str, Any], idx: int, status: str) -> List[str]:
        """Validate a single step dictionary against schema and business constraints.
        
        Args:
            step: Step dictionary parsed from steps_json.
            idx: Row number for error reporting.
            status: Overall case deletion status ('COMPLETE', 'INCOMPLETE').
        Returns:
            List of detected error messages.
        """
        step_errors: List[str] = []
        required_keys = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}
        if not required_keys.issubset(step.keys()):
            missing = required_keys - set(step.keys())
            step_errors.append(f"Row {idx}: Step missing required keys {missing}")
            return step_errors

        phase = step["phase"]
        operation = step["operation"]
        state = step["state"]
        evidence_id = step["evidence_id"]

        if phase not in cls.VALID_PHASES:
            step_errors.append(f"Row {idx}: Invalid phase '{phase}'")
        if operation not in cls.VALID_OPERATIONS:
            step_errors.append(f"Row {idx}: Invalid operation '{operation}'")
        if state not in cls.VALID_STATES:
            step_errors.append(f"Row {idx}: Invalid state '{state}'")

        if status == AuditVerdict.COMPLETE.value:
            if phase != AuditPhase.VERIFICATION.value:
                step_errors.append(f"Row {idx}: COMPLETE case must contain only VERIFICATION steps, got '{phase}'")
            if not evidence_id:
                step_errors.append(f"Row {idx}: COMPLETE case verification must cite non-empty evidence_id")
        elif status == AuditVerdict.INCOMPLETE.value:
            if phase == AuditPhase.FINDING.value and not evidence_id:
                step_errors.append(f"Row {idx}: INCOMPLETE finding must cite non-empty evidence_id")
            elif phase in [AuditPhase.REMEDIATION.value, AuditPhase.VERIFICATION.value] and evidence_id != "":
                step_errors.append(f"Row {idx}: INCOMPLETE remediation/verification must use empty evidence_id, got '{evidence_id}'")

        return step_errors

    @classmethod
    def validate_file(cls, file_path: Path) -> Tuple[bool, int, List[str]]:
        """Validate output.csv against challenge submission schema and sequencing rules.
        
        Args:
            file_path: Path to output.csv file.
        Returns:
            Tuple of (is_valid, total_rows, list_of_error_strings).
        """
        if not file_path.exists():
            return False, 0, [f"File not found: {file_path}"]

        errors: List[str] = []
        row_count = 0

        with open(file_path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            
            if reader.fieldnames != cls.EXPECTED_COLUMNS:
                errors.append(
                    f"Header mismatch. Expected {cls.EXPECTED_COLUMNS}, but got {reader.fieldnames}"
                )
                return False, 0, errors

            prev_case_id = ""
            for idx, row in enumerate(reader, start=1):
                row_count += 1
                case_id = (row.get("case_id") or "").strip()
                status = (row.get("deletion_status") or "").strip()
                steps_json_str = (row.get("steps_json") or "").strip()

                if not case_id:
                    errors.append(f"Row {idx}: Missing or empty case_id")

                def extract_case_num(cid_str: str) -> int:
                    digits = "".join(ch for ch in cid_str if ch.isdigit())
                    return int(digits) if digits else 0

                if case_id and prev_case_id and extract_case_num(case_id) < extract_case_num(prev_case_id):
                    errors.append(f"Row {idx}: Rows out of order. '{case_id}' appears after '{prev_case_id}'")
                prev_case_id = case_id

                if status not in cls.VALID_STATUSES:
                    errors.append(
                        f"Row {idx} (Case: {case_id}): Invalid status '{status}'. Must be one of {cls.VALID_STATUSES}"
                    )

                try:
                    steps = json.loads(steps_json_str)
                    if not isinstance(steps, list):
                        errors.append(f"Row {idx} (Case: {case_id}): steps_json must be a JSON array")
                        continue

                    if status == AuditVerdict.NOT_APPLICABLE.value:
                        if len(steps) != 0:
                            errors.append(f"Row {idx} (Case: {case_id}): NOT_APPLICABLE must have empty steps_json '[]'")
                    else:
                        prev_step_no = 0
                        prev_phase_rank = 0
                        prev_op_rank = 0
                        for step_obj in steps:
                            step_errors = cls.validate_step(step_obj, idx, status)
                            errors.extend(step_errors)

                            s_no = step_obj.get("step_no", 0)
                            if s_no != prev_step_no + 1:
                                errors.append(f"Row {idx} (Case: {case_id}): Non-consecutive step_no {s_no}, expected {prev_step_no + 1}")
                            prev_step_no = s_no

                            phase_rank = cls.PHASE_ORDER.get(step_obj.get("phase"), 99)
                            if phase_rank < prev_phase_rank:
                                errors.append(f"Row {idx} (Case: {case_id}): Inverted phase ordering '{step_obj.get('phase')}'")
                            prev_phase_rank = phase_rank

                except json.JSONDecodeError as jde:
                    errors.append(f"Row {idx} (Case: {case_id}): Malformed JSON in steps_json: {jde}")

        is_valid = len(errors) == 0
        return is_valid, row_count, errors
