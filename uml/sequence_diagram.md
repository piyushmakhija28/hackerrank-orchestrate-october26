# UML Sequence Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-diagram-mathematics-expert`)  
**Specification Standards:** Conforms to Level 2.2 Docstrings-Only convention and RFC-4180 / ISO-8601 contracts.

```mermaid
sequenceDiagram
    autonumber
    actor User as Participant / CLI Runner
    participant Main as code/main.py (Orchestrator)
    participant Container as AuditContainer
    participant Policy as PolicyAuditor
    participant Identity as IdentityResolver (DSU)
    participant Inspector as MultimodalInspector
    participant Lineage as LineageTracer
    participant Planner as RemediationPlanner
    participant CSV as CSVHandler

    User->>Main: execute(python code/main.py --requests deletion_requests.csv)
    Main->>Container: initialize()
    activate Container
    Container->>Policy: load_rules(deletion_rules.csv)
    Container->>Identity: load_identities(identities.csv, audit_log.csv)
    Container->>Inspector: index_all_evidence(manifest.csv, evidence_dir)
    Container->>Lineage: load_activity(system_activity.csv)
    Container-->>Main: container_ready
    deactivate Container

    loop For each DeletionRequest in deletion_requests.csv (518 cases)
        Main->>Policy: is_deletion_authorized(request_text)
        alt Request is NOT an erasure request (Rectification, Portability, Opt-out)
            Policy-->>Main: false
            Main->>Planner: build_plan(case_id, is_authorized=False, ...)
            Planner-->>Main: (NOT_APPLICABLE, [])
        else Request authorizes deletion
            Policy-->>Main: true
            Main->>Identity: resolve_identities(seed_email)
            Identity-->>Main: identity_cluster (emails, user_ids, phones, hashes)
            
            Main->>Inspector: find_exposed_records(identity_cluster, audit_at)
            Inspector-->>Main: exposed_evidence_records
            
            Main->>Lineage: trace_active_flows(identity_cluster, audit_at)
            Lineage-->>Main: active_flows, restore_risks, compliant_records
            
            Main->>Planner: build_plan(case_id, is_authorized=True, findings, flows, verifications)
            activate Planner
            alt Findings or Active Flows Exist
                Planner->>Planner: generate_findings_steps(exposed_records, flows)
                Planner->>Planner: generate_poset_remediation(DISABLE_FLOW -> BLOCK_RESTORE -> DELETE -> REDACT)
                Planner->>Planner: generate_dual_post_verifications(ABSENT, DISABLED, BLOCKED)
                Planner->>Planner: sort_poset_dag(priority_rank, system_id, resource_id)
                Planner-->>Main: (INCOMPLETE, ordered_steps_1..K)
            else Zero Findings and Compliant Records Exist
                Planner->>Planner: generate_evidence_backed_verifications(compliant_records)
                Planner->>Planner: sort_poset_dag(priority_rank, system_id, resource_id)
                Planner-->>Main: (COMPLETE, verification_steps_1..K)
            end
            deactivate Planner
        end
        Main->>CSV: write_row(case_id, deletion_status, steps_json)
    end

    Main->>User: Audit complete -> output.csv (518 rows written & validated)
```
