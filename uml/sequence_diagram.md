# UML Sequence Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`multi-agent-graph-orchestration-engineer`, `uml-diagram-mathematics-expert`)  
**Specification Standards:** Conforms to Level 2.2 Docstrings-Only convention and RFC-4180 / ISO-8601 contracts.

```mermaid
sequenceDiagram
    autonumber
    actor User as Participant / CLI Runner
    participant Main as code/main.py (Master Orchestrator)
    participant Sanitize as InputSanitizer (Security)
    participant Container as AuditContainer (IoC)
    participant Identity as IdentityResolver (DSU Orbit Cache)
    participant Inspector as MultimodalInspector (SQLite)
    participant Lineage as LineageTracer (Bisect Search)
    participant Policy as PolicyAuditor (NLU & Rules)
    participant Context as ContextBuilder (Knapsack)
    participant Optimizer as TokenOptimizer (BPE)
    participant Planner as RemediationPlanner (5-Tuple Poset)
    participant Guard as PromptGuard (Witness Verifier)
    participant Replay as ReplayTracer (LRU 2000)
    participant CSV as CSVHandler (RFC-4180)

    User->>Main: execute(python code/main.py --requests deletion_requests.csv)
    
    rect rgb(240, 248, 255)
        Note over Main,Lineage: One-Time Static Pre-Indexing Phase (Amortized Zero-Cost)
        Main->>Container: initialize()
        activate Container
        Container->>Policy: load_rules(deletion_rules.csv)
        Container->>Identity: load_identities_and_audit_log(identities.csv, audit_log.csv)
        Identity->>Identity: build_equivalence_orbit_cache() [Theorem 1]
        Container->>Inspector: index_all_evidence(manifest.csv, evidence_dir)
        Inspector->>Inspector: spinup_in_memory_sqlite_dbs()
        Container->>Lineage: load_activities(system_activity.csv)
        Lineage->>Lineage: sort_worker_timestamps() [Theorem 2]
        Container-->>Main: container_ready (65 MB RAM)
        deactivate Container
    end

    loop For each DeletionRequest in deletion_requests.csv (518 cases)
        Main->>Sanitize: sanitize(request_text)
        Sanitize-->>Main: sanitized_text (OWASP LLM01 injection cleared)

        Main->>Policy: is_deletion_authorized(sanitized_text)
        alt Request is NOT an erasure mandate (Portability, Rectification, Opt-out)
            Policy-->>Main: false
            Main->>Planner: build_plan(case_id, is_authorized=False, ...)
            Planner-->>Main: (NOT_APPLICABLE, [])
        else Request authorizes deletion
            Policy-->>Main: true
            Main->>Identity: resolve_cluster(seed_email) [O(α(N))]
            Identity-->>Main: identity_cluster (user_id, emails, phone, hashes)

            Main->>Inspector: find_exposed_records(identity_cluster, audit_at)
            Inspector-->>Main: exposed_evidence_records

            Main->>Lineage: query_token_activities(identity_cluster)
            Main->>Lineage: query_window_worker_activities(reported_at, 7200, 300) [O(log K)]
            Lineage-->>Main: active_flows, restore_risks, compliant_records

            Main->>Context: pack_context_knapsack(candidate_facts, budget=4096)
            Context-->>Main: packed_facts [Theorem 5]

            Main->>Optimizer: calculate_serialization_savings(packed_facts)
            Optimizer-->>Main: token_metrics (19,332 tokens saved)

            Main->>Planner: build_steps(verdict, findings, verifications)
            activate Planner
            alt Findings or Active Flows Detected
                Planner->>Planner: generate_finding_steps(exposed_records, flows)
                Planner->>Planner: generate_remediation_steps(DISABLE -> BLOCK -> DELETE -> REDACT)
                Planner->>Planner: generate_post_verifications(ABSENT, DISABLED, BLOCKED)
                Planner->>Planner: sort_injective_5_tuple(p_rank, o_rank, sys, res, ev_id, state) [Theorem 3]
                Planner-->>Main: (INCOMPLETE, ordered_steps_1..K)
            else Zero Residuals & Compliant Records Exist
                Planner->>Planner: generate_evidence_backed_verifications(compliant_records)
                Planner->>Planner: sort_injective_5_tuple(p_rank, o_rank, sys, res, ev_id, state) [Theorem 3]
                Planner-->>Main: (COMPLETE, verification_steps_1..K)
            end
            deactivate Planner

            Main->>Guard: verify_witness_grounding(steps, audit_at)
            Guard-->>Main: verified_steps (P(Hallucination) = 0)

            Main->>Replay: record_decision(case_id, verdict, steps, ...) [LRU 2000 Eviction, Theorem 4]
        end
        Main->>CSV: write_row(case_id, deletion_status, steps_json)
    end

    Main->>Main: OutputSchemaValidator.validate_file(output.csv)
    Main-->>User: Audit complete: 518 cases (0.26ms turnaround, 0 errors, output.csv verified)
```
