"""
Domain models and DTOs for the Deletion Audit Agent.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
from enum import Enum
from typing import List, Dict, Set, Optional, Literal, Any
from pydantic import BaseModel, Field

class AuditVerdict(str, Enum):
    """Enumeration of overall deletion audit status decisions."""
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class AuditPhase(str, Enum):
    """Enumeration of audit and remediation execution phases."""
    FINDING = "FINDING"
    REMEDIATION = "REMEDIATION"
    VERIFICATION = "VERIFICATION"

class AuditOperation(str, Enum):
    """Enumeration of allowable operations across all phases."""
    REPORT_REMAINING_RECORD = "REPORT_REMAINING_RECORD"
    REPORT_EXPOSED_PII = "REPORT_EXPOSED_PII"
    REPORT_ACTIVE_DATA_FLOW = "REPORT_ACTIVE_DATA_FLOW"
    REPORT_RESTORE_RISK = "REPORT_RESTORE_RISK"
    DISABLE_DATA_FLOW = "DISABLE_DATA_FLOW"
    BLOCK_RESTORE = "BLOCK_RESTORE"
    DELETE_RECORD = "DELETE_RECORD"
    REDACT_RECORD = "REDACT_RECORD"
    ANONYMIZE_RECORD = "ANONYMIZE_RECORD"
    VERIFY_RECORD_ABSENT = "VERIFY_RECORD_ABSENT"
    VERIFY_RECORD_PRESENT = "VERIFY_RECORD_PRESENT"
    VERIFY_RECORD_REDACTED = "VERIFY_RECORD_REDACTED"
    VERIFY_RECORD_ANONYMIZED = "VERIFY_RECORD_ANONYMIZED"
    VERIFY_DATA_FLOW_DISABLED = "VERIFY_DATA_FLOW_DISABLED"
    VERIFY_RESTORE_BLOCKED = "VERIFY_RESTORE_BLOCKED"

    @classmethod
    def priority_rank(cls, op: str) -> int:
        """Return the strict integer priority rank for step ordering.
        
        Args:
            op: Operation name string.
        Returns:
            Integer rank from 1 to 15.
        """
        ranks = {
            cls.REPORT_REMAINING_RECORD.value: 1,
            cls.REPORT_EXPOSED_PII.value: 2,
            cls.REPORT_ACTIVE_DATA_FLOW.value: 3,
            cls.REPORT_RESTORE_RISK.value: 4,
            cls.DISABLE_DATA_FLOW.value: 5,
            cls.BLOCK_RESTORE.value: 6,
            cls.DELETE_RECORD.value: 7,
            cls.REDACT_RECORD.value: 8,
            cls.ANONYMIZE_RECORD.value: 9,
            cls.VERIFY_RECORD_ABSENT.value: 10,
            cls.VERIFY_RECORD_PRESENT.value: 11,
            cls.VERIFY_RECORD_REDACTED.value: 12,
            cls.VERIFY_RECORD_ANONYMIZED.value: 13,
            cls.VERIFY_DATA_FLOW_DISABLED.value: 14,
            cls.VERIFY_RESTORE_BLOCKED.value: 15,
        }
        return ranks.get(op, 99)

class AuditState(str, Enum):
    """Enumeration of allowable resource states."""
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"
    REDACTED = "REDACTED"
    ANONYMIZED = "ANONYMIZED"

class AuditStep(BaseModel):
    """Pydantic model representing a single atomic finding, remediation, or verification step.
    
    Attributes:
        step_no: Consecutive step index starting from 1.
        phase: Execution phase ('FINDING', 'REMEDIATION', 'VERIFICATION').
        system_id: Target system or service identifier.
        resource_id: Identifier of the target record or process.
        operation: Mandatory operation verb from AuditOperation.
        state: Resulting or observed resource state from AuditState.
        evidence_id: Evidence identifier proving the step, or empty string.
    """
    step_no: int
    phase: AuditPhase
    system_id: str
    resource_id: str
    operation: AuditOperation
    state: AuditState
    evidence_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to exact JSON dictionary format.
        
        Returns:
            Dictionary matching problem_statement.md schema.
        """
        return {
            "step_no": self.step_no,
            "phase": self.phase.value,
            "system_id": self.system_id,
            "resource_id": self.resource_id,
            "operation": self.operation.value,
            "state": self.state.value,
            "evidence_id": self.evidence_id
        }

class ProcessType(str, Enum):
    """Enumeration of active replication and synchronization processes."""
    CDC_STREAM = "CDC_STREAM"
    CRON_ETL = "CRON_ETL"
    BACKUP_RESTORE = "BACKUP_RESTORE"
    CACHE_WARMER = "CACHE_WARMER"

class SyncProcess(BaseModel):
    """Represents an active data pipeline or sync process.
    
    Attributes:
        process_id: Unique process identifier.
        source_store: Name of data source.
        target_store: Name of data destination.
        process_type: Category of replication.
        is_active: Whether process is currently enabled.
        is_tombstone_aware: Whether process respects deletion tombstones.
    """
    process_id: str
    source_store: str
    target_store: str
    process_type: ProcessType
    is_active: bool = True
    is_tombstone_aware: bool = False

class ExposedRecord(BaseModel):
    """Represents a residual data record exposing personal identifiers.
    
    Attributes:
        store_name: Datastore where record was discovered.
        record_id: Identifier of the record within the store.
        detected_identifiers: Customer tokens present in the record.
        is_retained_by_law: Whether record falls under statutory retention.
    """
    store_name: str
    record_id: str
    detected_identifiers: List[str]
    is_retained_by_law: bool = False

class PolicyRule(BaseModel):
    """Encapsulates a governance rule from deletion_rules.csv.
    
    Attributes:
        rule_id: Unique rule identifier.
        data_category: Category of data covered.
        required_treatment: Mandatory treatment ('HARD_DELETE', 'ANONYMIZE', 'REDACT', 'RETAIN').
        retention_mandate: Whether record must be kept under statutory regulation.
    """
    rule_id: str
    data_category: str
    required_treatment: str
    retention_mandate: bool = False

class DeletionRequest(BaseModel):
    """Represents a single customer deletion request row from deletion_requests.csv.
    
    Attributes:
        case_id: Unique request case identifier.
        email: Primary or historical email address supplied.
        requested_at: ISO-8601 timestamp when request was submitted.
        reported_status: Workflow status claim ('COMPLETE', 'PARTIALLY_COMPLETE', 'NOT_STARTED').
        reported_at: ISO-8601 timestamp when status was reported.
        audit_at: ISO-8601 audit cutoff timestamp.
        request_text: Free-text request content.
    """
    case_id: str
    email: str
    requested_at: str
    reported_status: str
    reported_at: str
    audit_at: str
    request_text: str

class DeletionAuditOutputRow(BaseModel):
    """Pydantic model representing a single validated row for output.csv.
    
    Attributes:
        case_id: Unique request case identifier.
        deletion_status: Final audit verdict ('COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE').
        steps_json: JSON string representation of ordered AuditStep list.
    """
    case_id: str
    deletion_status: Literal["COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"]
    steps_json: str = "[]"
