# UML Sequence Diagram (Master Orchestration): Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-interaction-diagram-engineer`, `orchestration-engineer`)  
**Specification Standards:** Conforms to UML 2.5.1 Section 17.8 (Sequence Diagrams, Combined Fragments, Lifelines) and Level 2.2 Docstrings-Only convention.

---

## 1. End-to-End Multi-Agent Audit Sequence

This sequence diagram models the end-to-end execution flow of auditing a customer deletion request row, capturing lifelines, synchronous and asynchronous message exchanges, parallel investigation forks, and conditional alt fragments.

```mermaid
sequenceDiagram
    autonumber
    actor Participant as Evaluator / Grader
    participant Main as DeletionAuditOrchestrator
    participant Tamper as AntiTamperGuard
    participant Vault as CryptoSecurityVault
    participant Compl as ComplianceFrameworkMapper
    participant San as InputSanitizer
    participant DSU as IdentityResolver (DSU)
    participant Insp as MultimodalInspector (SQLite)
    participant Lin as LineageTracer (Bisect)
    participant Pol as PolicyAuditor (NLU)
    participant Rem as RemediationPlanner (Poset DAG)
    participant Grd as PromptGuard (Witness Assert)
    participant Log as StructuredLogger (MDC)
    participant Csv as CsvHandler (RFC-4180)

    Participant->>Main: execute_pipeline(requests_csv, output_csv)
    activate Main

    Main->>Log: set_context(trace_id, "pipeline_start")
    Main->>Tamper: verify_module_integrity("orchestrator", self.audit_single_request)
    Tamper-->>Main: integrity_verified (SHA-256 SAC match)
    Main->>Tamper: check_debugger_present()
    Tamper-->>Main: debugger_absent (clean execution)
    Main->>DSU: initialize_identities()
    activate DSU
    DSU-->>Main: identities_loaded (O(alpha(N)) cache ready)
    deactivate DSU

    loop For each request row in deletion_requests.csv (518 cases)
        Main->>Tamper: is_honeytoken_probed(request_text)
        Tamper-->>Main: probed=False (safe)
        Main->>San: sanitize(request_text)
        activate San
        San-->>Main: sanitized_text, is_injection=False
        deactivate San

        Main->>Pol: is_deletion_request(sanitized_text)
        activate Pol
        
        alt Request is NOT authorized for deletion (Export, Rectification, Opt-out)
            Pol-->>Main: is_deletion = False
            Main->>Main: assign_verdict(NOT_APPLICABLE, steps=[])
            Main->>Csv: write_row(case_id, "NOT_APPLICABLE", "[]")
        else Request authorizes deletion
            Pol-->>Main: is_deletion = True
            deactivate Pol

            %% Entity Resolution
            Main->>DSU: resolve_cluster(email)
            activate DSU
            DSU-->>Main: identity_cluster (user_id, emails, phone, hashes)
            deactivate DSU

            %% Parallel Investigation Phase
            par Query Evidence Facts
                Main->>Insp: query_facts_for_tokens(identity_cluster, audit_at)
                activate Insp
                Insp-->>Main: candidate_facts (filtered T(e) <= audit_at)
                deactivate Insp
            and Query System Activities & Lineage
                Main->>Lin: trace_active_flows(identity_cluster, audit_at)
                activate Lin
                Lin-->>Main: active_flows, restore_risks (bisect search)
                deactivate Lin
            end

            %% Policy Audit & Decision
            Main->>Pol: evaluate_facts_and_flows(candidate_facts, active_flows)
            activate Pol
            Pol-->>Main: violations_found, required_treatments
            deactivate Pol

            alt Deletion is INCOMPLETE (Residual PII, Active Sync, Restore Hazard)
                Main->>Rem: build_steps(INCOMPLETE, findings, verifications)
                activate Rem
                Rem->>Rem: schedule_poset_dag(Theorem 3 injective 5-tuple)
                Rem-->>Main: ordered_steps (FINDING -> REMEDIATION -> VERIFICATION)
                deactivate Rem
                Main->>Main: set_verdict(INCOMPLETE)
            else Deletion is COMPLETE (No violations, all tombstone/retained compliant)
                Main->>Rem: build_steps(COMPLETE, findings=[], verifications)
                activate Rem
                Rem-->>Main: verification_steps (evidence-backed checks only)
                deactivate Rem
                Main->>Main: set_verdict(COMPLETE)
            end

            %% Witness Grounding & Safety Guardrail
            Main->>Grd: verify_witness_grounding(steps, audit_at)
            activate Grd
            Grd-->>Main: is_valid = True (Invariant asserted)
            deactivate Grd

            Main->>Compl: generate_case_attestation(case_id, verdict, steps)
            activate Compl
            Compl-->>Main: ComplianceAttestation (GDPR, DPDP, SOC2 certified)
            deactivate Compl

            Main->>Csv: write_row(case_id, deletion_status, steps_json)
        end
    end

    Main->>Log: info("Pipeline audit complete", total_cases=518)
    Main-->>Participant: output.csv generated (518 rows sorted)
    deactivate Main
```

---

## 2. Combined Fragments & Architectural Invariants

| Fragment | Operator | Condition / Scope | Invariant Guaranteed |
|---|---|---|---|
| **Fast-Path Ingress** | `alt` | Non-deletion intent (`request_text` lacks deletion mandate) | Emits `NOT_APPLICABLE` with `steps_json='[]'`, skipping database lookups. |
| **Transitive Resolution** | `opt` | Aliases linked across `user_audit_log.csv` | Equivalence orbits queried in $O(\alpha(N))$ amortized via Tarjan's DSU. |
| **Parallel Discovery** | `par` | Evidence file search $\parallel$ Activity log window scan | Causal cone $T(e) \le \text{audit\_at}$ asserted across all candidate facts. |
| **Poset Remediation** | `alt` | Residual records, active CDC flows, or backup restore risks found | Poset DAG guarantees $(r_p, r_o, \text{sys}, \text{res}, \text{ev}, \text{state})$ strict injective order. |
| **Witness Verification** | `seq` | Output step serialization | Every finding cites visible evidence; every remediation step has empty `evidence_id`. |
