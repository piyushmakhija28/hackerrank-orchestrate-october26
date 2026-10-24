# UML Class Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-diagram-mathematics-expert`)  
**Specification Standards:** Conforms to Level 2.2 Docstrings-Only convention and RFC-4180 / ISO-8601 contracts.

```mermaid
classDiagram
    direction TB

    class AuditVerdict {
        <<enumeration>>
        +COMPLETE : string
        +INCOMPLETE : string
        +NOT_APPLICABLE : string
    }

    class AuditPhase {
        <<enumeration>>
        +FINDING : string
        +REMEDIATION : string
        +VERIFICATION : string
    }

    class AuditOperation {
        <<enumeration>>
        +REPORT_REMAINING_RECORD : string
        +REPORT_EXPOSED_PII : string
        +REPORT_ACTIVE_DATA_FLOW : string
        +REPORT_RESTORE_RISK : string
        +DISABLE_DATA_FLOW : string
        +BLOCK_RESTORE : string
        +DELETE_RECORD : string
        +REDACT_RECORD : string
        +ANONYMIZE_RECORD : string
        +VERIFY_RECORD_ABSENT : string
        +VERIFY_RECORD_PRESENT : string
        +VERIFY_RECORD_REDACTED : string
        +VERIFY_RECORD_ANONYMIZED : string
        +VERIFY_DATA_FLOW_DISABLED : string
        +VERIFY_RESTORE_BLOCKED : string
        +priority_rank() int
    }

    class AuditState {
        <<enumeration>>
        +PRESENT : string
        +ACTIVE : string
        +ABSENT : string
        +DISABLED : string
        +BLOCKED : string
        +REDACTED : string
        +ANONYMIZED : string
    }

    class AuditStep {
        +int step_no
        +AuditPhase phase
        +string system_id
        +string resource_id
        +AuditOperation operation
        +AuditState state
        +string evidence_id
        +to_dict() dict
    }

    class DeletionRequest {
        +string case_id
        +string email
        +datetime requested_at
        +string reported_status
        +datetime reported_at
        +datetime audit_at
        +string request_text
    }

    class DeletionAuditOutputRow {
        +string case_id
        +AuditVerdict deletion_status
        +List~AuditStep~ steps
        +to_csv_row() dict
    }

    class IIdentityResolver {
        <<interface>>
        +resolve_identities(string seed_email) Set~string~
    }

    class IMultimodalInspector {
        <<interface>>
        +find_exposed_records(Set~string~ identifiers, datetime cutoff) List~dict~
    }

    class ILineageTracer {
        <<interface>>
        +trace_active_flows(Set~string~ identifiers, datetime cutoff) List~dict~
    }

    class IPolicyAuditor {
        <<interface>>
        +is_deletion_authorized(string request_text) bool
        +get_retention_rule(string system_id, string resource_type) Optional~dict~
    }

    class IRemediationPlanner {
        <<interface>>
        +build_plan(string case_id, bool is_authorized, List findings, List active_flows, List verifications) Tuple
    }

    class DisjointSetUnion {
        -Dict~string, string~ parent
        -Dict~string, int~ rank
        +find(string item) string
        +union(string item1, string item2) void
        +get_cluster(string item) Set~string~
    }

    class IdentityResolver {
        -DisjointSetUnion dsu
        -Dict~string, string~ email_to_user_id
        -Dict~string, Set~ user_id_to_emails
        +load_identities(Path identities_csv, Path audit_log_csv) void
        +resolve_identities(string seed_email) Set~string~
    }

    class MultimodalInspector {
        -Dict~string, dict~ evidence_manifest
        -Dict~string, List~ email_index
        -Dict~string, List~ user_id_index
        -Dict~string, sqlite3.Connection~ sql_connections
        +index_all_evidence(Path manifest_csv, Path evidence_dir) void
        +find_exposed_records(Set~string~ identifiers, datetime cutoff) List~dict~
    }

    class LineageTracer {
        -List~dict~ activity_stream
        -Dict~string, List~ resource_activity_index
        +load_activity(Path activity_csv) void
        +trace_active_flows(Set~string~ identifiers, datetime cutoff) List~dict~
    }

    class PolicyAuditor {
        -Dict retention_rules
        -List~string~ non_deletion_indicators
        +load_rules(Path rules_csv) void
        +is_deletion_authorized(string request_text) bool
        +get_retention_rule(string system_id, string resource_type) Optional~dict~
    }

    class RemediationPlanner {
        -Dict~AuditPhase, int~ phase_precedence
        -Dict~AuditOperation, int~ operation_ranks
        +build_plan(string case_id, bool is_authorized, List findings, List active_flows, List verifications) Tuple
    }

    class AuditContainer {
        +Path dataset_dir
        +IdentityResolver identity_resolver
        +MultimodalInspector multimodal_inspector
        +LineageTracer lineage_tracer
        +PolicyAuditor policy_auditor
        +RemediationPlanner remediation_planner
        +initialize() void
    }

    AuditStep --> AuditPhase
    AuditStep --> AuditOperation
    AuditStep --> AuditState
    DeletionAuditOutputRow --> AuditVerdict
    DeletionAuditOutputRow --> AuditStep

    IdentityResolver ..|> IIdentityResolver
    MultimodalInspector ..|> IMultimodalInspector
    LineageTracer ..|> ILineageTracer
    PolicyAuditor ..|> IPolicyAuditor
    RemediationPlanner ..|> IRemediationPlanner

    IdentityResolver *-- DisjointSetUnion
    AuditContainer o-- IdentityResolver
    AuditContainer o-- MultimodalInspector
    AuditContainer o-- LineageTracer
    AuditContainer o-- PolicyAuditor
    AuditContainer o-- RemediationPlanner
```
