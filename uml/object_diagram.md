# UML Object Diagram: Runtime Instance State
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-structural-diagram-engineer`, `uml-diagram-mathematics-expert`)  
**Specification Standards:** Conforms to UML 2.5.1 Section 9.8 (InstanceSpecifications) and Level 2.2 Docstrings-Only convention.

---

## 1. Concrete Runtime Snapshot: Auditing `case_005` (Ghost Data & CDC Sync Hazard)

This object diagram captures a precise, deterministic runtime snapshot of heap-allocated objects during the audit of an INCOMPLETE deletion case where residual customer data and an active synchronization flow were detected.

```mermaid
classDiagram
    direction TB

    %% ==========================================
    %% RUNTIME INSTANCES (Object : Class)
    %% ==========================================
    class OrchestratorInstance {
        orchestrator : DeletionAuditOrchestrator
        max_workers = 8
        active_threads = 8
    }

    class RequestInstance {
        req : DeletionRequest
        case_id = "case_005"
        email = "alice.smith@example.com"
        requested_at = "2026-09-01T10:00:00Z"
        reported_status = "COMPLETE"
        reported_at = "2026-09-02T14:30:00Z"
        audit_at = "2026-09-05T00:00:00Z"
        request_text = "Please erase all my personal data from your systems."
    }

    class ContainerInstance {
        container : AuditContainer
        dataset_dir = Path("dataset")
    }

    class DSUInstance {
        dsu : DisjointSetUnion
        parent = {"alice.smith@example.com": "usr_9921", "asmith_old@work.com": "usr_9921", "usr_9921": "usr_9921"}
        rank = {"usr_9921": 2, "alice.smith@example.com": 0, "asmith_old@work.com": 0}
    }

    class ResolverInstance {
        resolver : IdentityResolver
        user_id = "usr_9921"
        cluster = {"alice.smith@example.com", "asmith_old@work.com", "usr_9921", "+15550199", "Alice Smith", "d8578edf..."}
        _cache_dirty = false
    }

    class InspectorInstance {
        inspector : MultimodalInspector
        cached_facts = 1420
        open_sqlite_conns = 4
    }

    class FactInstance1 {
        fact_01 : EvidenceFact
        file_id = "evidence_08"
        system_id = "marketing_db_replica"
        resource_id = "user_profile_9921"
        record_type = "SQL_ROW"
        captured_at = "2026-09-03T11:20:00Z"
        tokens_found = {"usr_9921", "alice.smith@example.com"}
    }

    class FactInstance2 {
        fact_02 : EvidenceFact
        file_id = "evidence_23"
        system_id = "order_service"
        resource_id = "order_rec_441"
        record_type = "JSON"
        captured_at = "2026-08-15T09:00:00Z"
        tokens_found = {"usr_9921"}
    }

    class LineageInstance {
        tracer : LineageTracer
        total_activities = 4850
        bisect_lookup_window_sec = 7200
    }

    class SyncProcessInstance {
        cdc_flow : SyncProcess
        process_id = "cdc_user_sync_job"
        process_type = "CDC"
        source_system = "marketing_db_replica"
        target_system = "analytics_warehouse"
        resource_id = "stream_user_profile_9921"
        is_active = true
        last_sync_time = "2026-09-04T08:00:00Z"
    }

    class PolicyAuditorInstance {
        auditor : PolicyAuditor
        total_rules = 18
        is_deletion = true
    }

    class RetainRuleInstance {
        rule_order : PolicyRule
        rule_id = "rule_order_history"
        data_category = "orders"
        required_treatment = "RETAIN"
        retention_mandate = true
    }

    class DeleteRuleInstance {
        rule_marketing : PolicyRule
        rule_id = "rule_marketing_profile"
        data_category = "marketing_profiles"
        required_treatment = "HARD_DELETE"
        retention_mandate = false
    }

    class StepFinding1 {
        step_1 : AuditStep
        step_no = 1
        phase = FINDING
        system_id = "marketing_db_replica"
        resource_id = "stream_user_profile_9921"
        operation = REPORT_ACTIVE_DATA_FLOW
        state = ACTIVE
        evidence_id = "activity_1084"
    }

    class StepFinding2 {
        step_2 : AuditStep
        step_no = 2
        phase = FINDING
        system_id = "marketing_db_replica"
        resource_id = "user_profile_9921"
        operation = REPORT_REMAINING_RECORD
        state = PRESENT
        evidence_id = "evidence_08"
    }

    class StepRemediation1 {
        step_3 : AuditStep
        step_no = 3
        phase = REMEDIATION
        system_id = "marketing_db_replica"
        resource_id = "stream_user_profile_9921"
        operation = DISABLE_DATA_FLOW
        state = DISABLED
        evidence_id = ""
    }

    class StepRemediation2 {
        step_4 : AuditStep
        step_no = 4
        phase = REMEDIATION
        system_id = "marketing_db_replica"
        resource_id = "user_profile_9921"
        operation = DELETE_RECORD
        state = ABSENT
        evidence_id = ""
    }

    class StepVerification1 {
        step_5 : AuditStep
        step_no = 5
        phase = VERIFICATION
        system_id = "marketing_db_replica"
        resource_id = "user_profile_9921"
        operation = VERIFY_RECORD_ABSENT
        state = ABSENT
        evidence_id = ""
    }

    class StepVerification2 {
        step_6 : AuditStep
        step_no = 6
        phase = VERIFICATION
        system_id = "marketing_db_replica"
        resource_id = "stream_user_profile_9921"
        operation = VERIFY_DATA_FLOW_DISABLED
        state = DISABLED
        evidence_id = ""
    }

    class StepVerification3 {
        step_7 : AuditStep
        step_no = 7
        phase = VERIFICATION
        system_id = "order_service"
        resource_id = "order_rec_441"
        operation = VERIFY_RECORD_PRESENT
        state = PRESENT
        evidence_id = ""
    }

    class OutputRowInstance {
        output_row : DeletionAuditOutputRow
        case_id = "case_005"
        deletion_status = "INCOMPLETE"
        step_count = 7
    }

    %% ==========================================
    %% OBJECT LINKS
    %% ==========================================
    OrchestratorInstance ..> RequestInstance : audits
    OrchestratorInstance *-- ContainerInstance : holds
    ContainerInstance *-- ResolverInstance : holds
    ResolverInstance *-- DSUInstance : delegates
    ContainerInstance *-- InspectorInstance : holds
    InspectorInstance o-- FactInstance1 : holds
    InspectorInstance o-- FactInstance2 : holds
    ContainerInstance *-- LineageInstance : holds
    LineageInstance o-- SyncProcessInstance : discovers
    ContainerInstance *-- PolicyAuditorInstance : holds
    PolicyAuditorInstance o-- RetainRuleInstance : evaluates
    PolicyAuditorInstance o-- DeleteRuleInstance : evaluates

    OrchestratorInstance ..> OutputRowInstance : produces
    OutputRowInstance *-- StepFinding1 : step 1
    OutputRowInstance *-- StepFinding2 : step 2
    OutputRowInstance *-- StepRemediation1 : step 3
    OutputRowInstance *-- StepRemediation2 : step 4
    OutputRowInstance *-- StepVerification1 : step 5
    OutputRowInstance *-- StepVerification2 : step 6
    OutputRowInstance *-- StepVerification3 : step 7
```

---

## 2. Invariant Assertions at this Runtime State

1. **Equivalence Orbit Invariant:** Token `"asmith_old@work.com"` correctly resolves to canonical root `"usr_9921"` via DSU path compression: $\text{find}(\text{"asmith\_old@work.com"}) = \text{"usr\_9921"}$.
2. **Temporal Cutoff Invariant:** `FactInstance1` was captured at `"2026-09-03T11:20:00Z"` $\le$ `audit_at` (`"2026-09-05T00:00:00Z"`), proving it is legally admissible.
3. **Statutory Exemption Invariant:** `FactInstance2` (`order_rec_441`) is covered by statutory retention mandate (`rule_order_history`), hence mapped to `VERIFY_RECORD_PRESENT` rather than deletion.
4. **Dependency-First Remediation:** Active CDC flow `stream_user_profile_9921` is ordered for `DISABLE_DATA_FLOW` before `DELETE_RECORD` on `user_profile_9921` to prevent zombie replication.
5. **Poset Total Order:** Steps 1 through 7 satisfy strictly injective 5-tuple sorting: $(r_p, r_o, \text{system\_id}, \text{resource\_id}, \text{evidence\_id}, \text{state})$.
