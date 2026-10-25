"""
Remediation and Verification Action Planner.
Builds a strict Partially Ordered Set (Poset) DAG and generates sequentially ordered steps.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
from typing import List, Dict, Set, Any, Tuple
from code.core.interfaces import IRemediationPlanner
from code.core.models import (
    AuditVerdict,
    AuditPhase,
    AuditOperation,
    AuditState,
    AuditStep
)

class RemediationPlanner(IRemediationPlanner):
    """Plans ordered remediation steps or cryptographic proof checks conforming to operation precedence."""

    PHASE_RANKS = {
        AuditPhase.FINDING: 1,
        AuditPhase.REMEDIATION: 2,
        AuditPhase.VERIFICATION: 3
    }

    def build_steps(
        self,
        verdict: AuditVerdict,
        case_findings: List[Dict[str, Any]],
        compliant_verifications: List[Dict[str, Any]]
    ) -> List[AuditStep]:
        """Construct sequentially ordered AuditStep list adhering to precedence and tie-breakers.
        
        Args:
            verdict: Audit decision verdict ('COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE').
            case_findings: List of finding dictionaries with evidence IDs.
            compliant_verifications: List of verification dictionaries.
        Returns:
            Consecutively numbered list of AuditStep instances.
        """
        if verdict == AuditVerdict.NOT_APPLICABLE:
            return []

        raw_steps: List[AuditStep] = []

        if verdict == AuditVerdict.COMPLETE:
            for v in compliant_verifications:
                raw_steps.append(
                    AuditStep(
                        step_no=0,
                        phase=AuditPhase.VERIFICATION,
                        system_id=v["system_id"],
                        resource_id=v["resource_id"],
                        operation=AuditOperation(v["operation"]),
                        state=AuditState(v["state"]),
                        evidence_id=v.get("evidence_id", "")
                    )
                )
        elif verdict == AuditVerdict.INCOMPLETE:
            for f in case_findings:
                raw_steps.append(
                    AuditStep(
                        step_no=0,
                        phase=AuditPhase.FINDING,
                        system_id=f["system_id"],
                        resource_id=f["resource_id"],
                        operation=AuditOperation(f["operation"]),
                        state=AuditState(f["state"]),
                        evidence_id=f.get("evidence_id", "")
                    )
                )

            for f in case_findings:
                op_val = f["operation"]
                sys_id = f["system_id"]
                res_id = f["resource_id"]

                rem_op: AuditOperation
                rem_state: AuditState
                if op_val == AuditOperation.REPORT_ACTIVE_DATA_FLOW.value:
                    rem_op = AuditOperation.DISABLE_DATA_FLOW
                    rem_state = AuditState.DISABLED
                elif op_val == AuditOperation.REPORT_RESTORE_RISK.value:
                    rem_op = AuditOperation.BLOCK_RESTORE
                    rem_state = AuditState.BLOCKED
                elif op_val == AuditOperation.REPORT_REMAINING_RECORD.value:
                    rem_op = AuditOperation.DELETE_RECORD
                    rem_state = AuditState.ABSENT
                elif op_val == AuditOperation.REPORT_EXPOSED_PII.value:
                    if "analytics" in sys_id:
                        rem_op = AuditOperation.ANONYMIZE_RECORD
                        rem_state = AuditState.ANONYMIZED
                    else:
                        rem_op = AuditOperation.REDACT_RECORD
                        rem_state = AuditState.REDACTED
                else:
                    rem_op = AuditOperation.DELETE_RECORD
                    rem_state = AuditState.ABSENT

                raw_steps.append(
                    AuditStep(
                        step_no=0,
                        phase=AuditPhase.REMEDIATION,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=rem_op,
                        state=rem_state,
                        evidence_id=""
                    )
                )

            for v in compliant_verifications:
                raw_steps.append(
                    AuditStep(
                        step_no=0,
                        phase=AuditPhase.VERIFICATION,
                        system_id=v["system_id"],
                        resource_id=v["resource_id"],
                        operation=AuditOperation(v["operation"]),
                        state=AuditState(v["state"]),
                        evidence_id=""
                    )
                )

            for f in case_findings:
                op_val = f["operation"]
                sys_id = f["system_id"]
                res_id = f["resource_id"]

                v_op: AuditOperation
                v_state: AuditState
                if op_val == AuditOperation.REPORT_ACTIVE_DATA_FLOW.value:
                    v_op = AuditOperation.VERIFY_DATA_FLOW_DISABLED
                    v_state = AuditState.DISABLED
                elif op_val == AuditOperation.REPORT_RESTORE_RISK.value:
                    v_op = AuditOperation.VERIFY_RESTORE_BLOCKED
                    v_state = AuditState.BLOCKED
                elif op_val == AuditOperation.REPORT_REMAINING_RECORD.value:
                    v_op = AuditOperation.VERIFY_RECORD_ABSENT
                    v_state = AuditState.ABSENT
                elif op_val == AuditOperation.REPORT_EXPOSED_PII.value:
                    if "analytics" in sys_id:
                        v_op = AuditOperation.VERIFY_RECORD_ANONYMIZED
                        v_state = AuditState.ANONYMIZED
                    else:
                        v_op = AuditOperation.VERIFY_RECORD_REDACTED
                        v_state = AuditState.REDACTED
                else:
                    v_op = AuditOperation.VERIFY_RECORD_ABSENT
                    v_state = AuditState.ABSENT

                raw_steps.append(
                    AuditStep(
                        step_no=0,
                        phase=AuditPhase.VERIFICATION,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=v_op,
                        state=v_state,
                        evidence_id=""
                    )
                )

        def step_sort_key(s: AuditStep) -> Tuple[int, int, str, str, str, str]:
            """Calculates a strictly injective multi-field sort key guaranteeing unique total ordering."""
            p_rank = self.PHASE_RANKS.get(s.phase, 99)
            o_rank = AuditOperation.priority_rank(s.operation.value)
            return (p_rank, o_rank, s.system_id, s.resource_id, s.evidence_id, s.state.value)

        raw_steps.sort(key=step_sort_key)

        ordered_steps: List[AuditStep] = []
        for idx, s in enumerate(raw_steps, start=1):
            s.step_no = idx
            ordered_steps.append(s)

        return ordered_steps
