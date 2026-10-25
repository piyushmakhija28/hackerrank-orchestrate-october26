# UML Class Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`multi-agent-graph-orchestration-engineer`, `uml-diagram-mathematics-expert`)  
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
        +priority_rank(operation_name) int
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

    class DisjointSetUnion {
        -Dict~string, string~ parent
        -Dict~string, int~ rank
        +find(string item) string
        +union(string item_a, string item_b) void
    }

    class IdentityResolver {
        -DisjointSetUnion dsu
        -Dict~string, string~ email_to_user_id
        -Dict~string, dict~ user_id_to_record
        -Dict~string, Set~string~~ _cluster_cache
        -bool _cache_dirty
        +load_identities_and_audit_log(identities_csv, audit_log_csv) void
        +resolve_cluster(seed) Set~string~
        -rebuild_cluster_index() void
    }

    class MultimodalInspector {
        -Dict~string, dict~ evidence_manifest
        -Dict~string, List~ email_index
        -Dict~string, List~ user_id_index
        -Dict~string, Connection~ sql_connections
        +index_all_evidence(manifest_csv, evidence_dir) void
        +find_exposed_records(identifiers, cutoff) List~dict~
    }

    class LineageTracer {
        -List~dict~ activities
        -Dict~string, List~ resource_to_activities
        -Dict~string, List~ activities_by_token
        -List~Tuple~datetime, dict~~ worker_activities_sorted
        -List~datetime~ worker_timestamps
        +load_activities(activity_csv) void
        +query_window_worker_activities(rep_dt, window_sec, lead_sec) List~dict~
        +query_token_activities(tokens) List~dict~
        +trace_active_flows(identifiers, cutoff) List~dict~
    }

    class PolicyAuditor {
        -List~dict~ rules
        -List~string~ non_deletion_indicators
        +load_rules(rules_csv) void
        +is_deletion_authorized(request_text) bool
        +get_retention_rule(system_id, resource_id) Optional~dict~
    }

    class RemediationPlanner {
        -Dict~AuditPhase, int~ PHASE_RANKS
        +build_steps(verdict, findings, verifications) List~AuditStep~
        -step_sort_key(step) Tuple~int, int, str, str, str, str~
    }

    class TokenOptimizer {
        +int SYSTEM_PROMPT_BASE_TOKENS
        -Lock _lock
        +int total_dedup_saved
        +int total_compression_saved
        +estimate_prompt_tokens(text) int
        +calculate_serialization_savings(facts) int
        +deduplicate_facts(facts) List~dict~
    }

    class ContextBuilder {
        +int context_budget
        +filter_facts_by_temporal_cutoff(facts, cutoff) List~dict~
        +pack_context_knapsack(facts, budget) List~dict~
    }

    class PromptGuard {
        +verify_witness_grounding(steps, audit_at) List~AuditStep~
        +sanitize_step(step) AuditStep
    }

    class InputSanitizer {
        +sanitize(user_text) str
        +compute_shannon_entropy(text) float
    }

    class PiiShield {
        +mask_pii(text) str
        +verify_luhn(card_number) bool
    }

    class ReplayTracer {
        -Dict~string, dict~ _traces
        +int max_capacity
        -Lock _registry_lock
        +record_decision(case_id, verdict, ...) void
        +get_replay_trace(case_id) Optional~dict~
        +format_diagnostic_report(case_id) str
    }

    class AuditContainer {
        +IdentityResolver identity_resolver
        +MultimodalInspector multimodal_inspector
        +LineageTracer lineage_tracer
        +PolicyAuditor policy_auditor
        +RemediationPlanner remediation_planner
        +initialize() void
    }

    class ConcurrentAuditOrchestrator {
        +AuditContainer container
        +int max_workers
        +run_pipeline_concurrent(requests_csv, output_csv, max_workers) List~DeletionAuditOutputRow~
    }

    AuditStep --> AuditPhase
    AuditStep --> AuditOperation
    AuditStep --> AuditState

    IdentityResolver *-- DisjointSetUnion
    AuditContainer o-- IdentityResolver
    AuditContainer o-- MultimodalInspector
    AuditContainer o-- LineageTracer
    AuditContainer o-- PolicyAuditor
    AuditContainer o-- RemediationPlanner

    ConcurrentAuditOrchestrator o-- AuditContainer
    ConcurrentAuditOrchestrator --> ReplayTracer
    ConcurrentAuditOrchestrator --> TokenOptimizer
    ConcurrentAuditOrchestrator --> InputSanitizer
    ConcurrentAuditOrchestrator --> PiiShield
```
