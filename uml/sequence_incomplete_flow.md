# UML Sequence Diagram: Deep-Dive INCOMPLETE Deletion Audit Flow
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-interaction-diagram-engineer`, `uml-diagram-mathematics-expert`)  
**Specification Standards:** Conforms to UML 2.5.1 Section 17.2 (Sequence Diagrams) and Level 2.2 Docstrings-Only convention.

---

## 1. Full Trace: Auditing an INCOMPLETE Request with Ghost Data & Active Sync Process

```mermaid
sequenceDiagram
    autonumber
    actor Participant as CLI Runner / Evaluator
    participant Main as DeletionAuditOrchestrator (main.py)
    participant Sanitize as InputSanitizer (Security)
    participant Policy as PolicyAuditor (Governance)
    participant Resolver as IdentityResolver (DSU Cache)
    participant Inspector as MultimodalInspector (SQLite)
    participant Lineage as LineageTracer (Bisect Engine)
    participant Ctx as ContextBuilder (Knapsack)
    participant Opt as TokenOptimizer (BPE Dedup)
    participant Planner as RemediationPlanner (Poset DAG)
    participant Guard as PromptGuard (Anti-Hallucination)
    participant Replay as ReplayTracer (LRU Cache)
    participant CSV as CsvHandler (RFC-4180)

    Participant->>Main: audit_single_request(case_id="case_005", email="alice.smith@example.com")
    activate Main

    %% STEP 1: SECURITY INGRESS
    rect rgb(255, 240, 245)
        Note over Main,Sanitize: Step 1: Security Ingress & Prompt Injection Neutralization
        Main->>Sanitize: sanitize(request_text)
        activate Sanitize
        Sanitize->>Sanitize: compute_shannon_entropy() [Assert H in [2.5, 5.0]]
        Sanitize->>Sanitize: check_adversarial_patterns() [OWASP LLM01 Defense]
        Sanitize-->>Main: clean_request_text (Injection disarmed)
        deactivate Sanitize
    end

    %% STEP 2: INTENT VERIFICATION
    rect rgb(240, 248, 255)
        Note over Main,Policy: Step 2: Intent Classification & Authorization Guard
        Main->>Policy: is_deletion_request(clean_request_text)
        activate Policy
        Policy->>Policy: scan_non_deletion_indicators() [30+ phrases checked]
        Policy-->>Main: true (Valid legal erasure request)
        deactivate Policy
    end

    %% STEP 3: IDENTITY CLUSTER RESOLUTION
    rect rgb(240, 255, 240)
        Note over Main,Resolver: Step 3: Multi-Attribute Transitive Entity Resolution (Theorem 1)
        Main->>Resolver: resolve_cluster("alice.smith@example.com")
        activate Resolver
        Resolver->>Resolver: lookup_orbit_cache() [O(alpha(N)) amortized]
        Resolver->>Resolver: fetch_associated_user_id("usr_9921")
        Resolver->>Resolver: extract_historical_aliases(phones, names, email_hashes)
        Resolver-->>Main: identity_cluster = {"usr_9921", "alice.smith@example.com", "asmith_old@work.com", ...}
        deactivate Resolver
    end

    %% STEP 4: EVIDENCE SCANNING & LINEAGE TRACING
    rect rgb(255, 250, 240)
        Note over Main,Lineage: Step 4: Evidence Inspection & System Lineage Query
        par Multimodal Evidence Scanning
            Main->>Inspector: query_facts_by_tokens(cluster, cutoff="2026-09-05T00:00:00Z")
            activate Inspector
            Inspector->>Inspector: scan_inverted_token_hash() [O(1) lookup]
            Inspector->>Inspector: query_sqlite_in_memory_dbs()
            Inspector->>Inspector: filter_temporal_causal_cone(T(e) <= audit_at)
            Inspector-->>Main: exposed_facts = [fact_01 (marketing_db), fact_02 (order_service)]
            deactivate Inspector
        and Monotone Lineage Tracing (Theorem 2)
            Main->>Lineage: query_window_worker_activities(reported_at="2026-09-02T14:30:00Z")
            activate Lineage
            Lineage->>Lineage: bisect_search_timestamps() [O(log K) window scan]
            Lineage->>Lineage: query_token_activities(cluster)
            Lineage->>Lineage: detect_active_sync_jobs()
            Lineage-->>Main: active_flows = [sync_cdc_user_stream], restore_risks = []
            deactivate Lineage
        end
    end

    %% STEP 5: CONTEXT PACKING & TOKEN DEDUPLICATION
    rect rgb(245, 240, 255)
        Note over Main,Opt: Step 5: Causal Context Optimization & BPE Deduplication
        Main->>Ctx: build_knapsack_context(exposed_facts, max_tokens=4096)
        activate Ctx
        Ctx->>Ctx: sort_by_priority_weights(FINDING > STATUTORY_RETAIN)
        Ctx-->>Main: packed_facts (Preserves 4096-token ceiling)
        deactivate Ctx

        Main->>Opt: deduplicate_facts(packed_facts)
        activate Opt
        Opt->>Opt: compute_sha256_fingerprints()
        Opt->>Opt: eliminate_redundant_tokens() [Saves 19,332 tokens]
        Opt-->>Main: unique_facts, token_savings
        deactivate Opt
    end

    %% STEP 6: POLICY AUDIT & RESIDUAL CLASSIFICATION
    rect rgb(255, 245, 238)
        Note over Main,Policy: Step 6: Policy Rule Application & Statutory Exception Check
        Main->>Policy: evaluate_retention_rules(unique_facts)
        activate Policy
        Policy->>Policy: match_deletion_rules(marketing_profile -> HARD_DELETE)
        Policy->>Policy: match_deletion_rules(orders -> RETAIN, statutory_mandate=true)
        Policy-->>Main: findings = [residual_marketing_profile, active_cdc_stream], compliant = [order_rec]
        deactivate Policy
    end

    %% STEP 7: POSET DAG REMEDIATION PLANNING
    rect rgb(240, 255, 255)
        Note over Main,Planner: Step 7: Poset DAG Injective Total Order Scheduling (Theorem 3)
        Main->>Planner: build_steps(AuditVerdict.INCOMPLETE, findings, compliant)
        activate Planner
        Planner->>Planner: generate_finding_steps(REPORT_REMAINING_RECORD, REPORT_ACTIVE_DATA_FLOW)
        Planner->>Planner: generate_remediation_steps(DISABLE_DATA_FLOW -> DELETE_RECORD)
        Planner->>Planner: generate_verification_steps(VERIFY_ABSENT, VERIFY_DISABLED, VERIFY_PRESENT)
        Planner->>Planner: sort_injective_5_tuple(p_rank, o_rank, sys_id, res_id, ev_id, state)
        Planner->>Planner: renumber_steps_consecutively(1..7)
        Planner-->>Main: ordered_steps_1_to_7
        deactivate Planner
    end

    %% STEP 8: WITNESS GROUNDING & PROMPT GUARD
    rect rgb(250, 250, 210)
        Note over Main,Guard: Step 8: Witness Grounding Verification (Theorem 5)
        Main->>Guard: verify_witness_grounding(ordered_steps, audit_at)
        activate Guard
        Guard->>Guard: assert_evidence_in_manifest()
        Guard->>Guard: assert_captured_at_le_audit_at()
        Guard->>Guard: assert_p_hallucination_zero()
        Guard-->>Main: verification_passed (Invariant Guaranteed)
        deactivate Guard
    end

    %% STEP 9: SRE OBSERVABILITY & EGRESS
    rect rgb(245, 245, 245)
        Note over Main,CSV: Step 9: Replay Trace Recording & Thread-Safe CSV Row Streaming
        Main->>Replay: record_decision("case_005", "INCOMPLETE", ordered_steps)
        activate Replay
        Replay->>Replay: enforce_lru_boundary() [Registry size <= 2000]
        Replay-->>Main: trace_recorded
        deactivate Replay

        Main->>CSV: write_output_row(case_id="case_005", status="INCOMPLETE", steps_json)
        activate CSV
        CSV-->>Main: row_flushed
        deactivate CSV
    end

    Main-->>Participant: DeletionAuditOutputRow(case_id="case_005", status="INCOMPLETE", steps_json="[...]")
    deactivate Main
```

---

## 2. Invariant Execution Steps Breakdown

| Step Range | Phase | Operation | State | Target System / Resource | Evidence ID |
|---|---|---|---|---|---|
| Step 1 | `FINDING` | `REPORT_ACTIVE_DATA_FLOW` | `ACTIVE` | `marketing_db_replica` / `stream_user_profile_9921` | `activity_1084` |
| Step 2 | `FINDING` | `REPORT_REMAINING_RECORD` | `PRESENT` | `marketing_db_replica` / `user_profile_9921` | `evidence_08` |
| Step 3 | `REMEDIATION` | `DISABLE_DATA_FLOW` | `DISABLED` | `marketing_db_replica` / `stream_user_profile_9921` | `""` |
| Step 4 | `REMEDIATION` | `DELETE_RECORD` | `ABSENT` | `marketing_db_replica` / `user_profile_9921` | `""` |
| Step 5 | `VERIFICATION` | `VERIFY_RECORD_ABSENT` | `ABSENT` | `marketing_db_replica` / `user_profile_9921` | `""` |
| Step 6 | `VERIFICATION` | `VERIFY_DATA_FLOW_DISABLED` | `DISABLED` | `marketing_db_replica` / `stream_user_profile_9921` | `""` |
| Step 7 | `VERIFICATION` | `VERIFY_RECORD_PRESENT` | `PRESENT` | `order_service` / `order_rec_441` | `""` |
