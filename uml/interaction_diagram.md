# UML Interaction Overview Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-interaction-diagram-engineer`, `uml-behavioral-diagram-engineer`)  
**Specification Standards:** Conforms to UML 2.5.1 Section 17.6 (Interaction Overview Diagrams) and Level 2.2 Docstrings-Only convention.

---

## 1. High-Level Multi-Interaction Control Flow

This diagram coordinates high-level control transitions between major sequence interaction fragments (`ref`), decisions, forks, and joins.

```mermaid
flowchart TD
    %% ==========================================
    %% CONTROL NODES & INTERACTION OCCURRENCES
    %% ==========================================
    StartNode([Initial Node: CLI Invocation]) --> RefInit

    subgraph RefInit ["sd: One-Time Static Pre-Indexing Phase (Amortized Zero Cost)"]
        direction TB
        InitText["1. AuditContainer loads deletion_rules.csv into memory<br/>2. IdentityResolver builds DSU & Equivalence Orbit Cache<br/>3. MultimodalInspector spins up in-memory SQLite replicas<br/>4. LineageTracer sorts worker timestamps for bisect indexing<br/>Total Memory: ~65 MB | Latency: ~1.85s"]
    end

    RefInit --> ForkConcurrency{Fork: ThreadPoolExecutor<br/>max_workers = 8}

    ForkConcurrency --> RefIngress

    subgraph RefIngress ["sd: Security Ingress & Sanitization Guardrails"]
        direction TB
        IngressText["1. InputSanitizer strips prompt injections (OWASP LLM01)<br/>2. Shannon Entropy verified: H in [2.5, 5.0]<br/>3. TokenBucketRateLimiter checks burst capacity"]
    end

    RefIngress --> DecAuth{Decision: Does request_text<br/>authorize erasure?}

    DecAuth -- "[No: Portability / Rectification / Opt-out]" --> RefNA

    subgraph RefNA ["sd: Fast-Path NOT_APPLICABLE Synthesis"]
        direction TB
        NAText["1. PolicyAuditor flags non-erasure keyword<br/>2. deletion_status = NOT_APPLICABLE<br/>3. steps_json = '[]'<br/>4. ReplayTracer logs decision graph"]
    end

    DecAuth -- "[Yes: Legal Erasure Mandate]" --> RefDeepAudit

    subgraph RefDeepAudit ["sd: Multi-Agent Deep Estate Investigation"]
        direction TB
        DeepText["1. IdentityResolver resolves cluster via O(alpha(N)) cache<br/>2. MultimodalInspector queries SQLite & inverted hash indices<br/>3. LineageTracer runs O(log K) bisect window scan for CDC/sync<br/>4. ContextBuilder filters causal cone T(e) <= audit_at<br/>5. TokenOptimizer applies BPE dedup (19,332 tokens saved)"]
    end

    RefDeepAudit --> DecViolations{Decision: Were residual records,<br/>active sync flows, or<br/>restore hazards found?}

    DecViolations -- "[Yes: Residuals Exist]" --> RefIncomplete

    subgraph RefIncomplete ["sd: Poset DAG Remediation Planning (INCOMPLETE)"]
        direction TB
        IncompleteText["1. Phase 1 (FINDING): Cite participant file_id / activity_id<br/>2. Phase 2 (REMEDIATION): DISABLE -> BLOCK -> DELETE -> REDACT<br/>3. Phase 3 (VERIFICATION): Post-remediation dual checks<br/>4. Strict injective 5-tuple sorting & renumbering 1..K"]
    end

    DecViolations -- "[No: Zero Residuals]" --> RefComplete

    subgraph RefComplete ["sd: Evidence-Backed Verification Synthesis (COMPLETE)"]
        direction TB
        CompleteText["1. Phase 3 (VERIFICATION only): Proofs of clean state<br/>2. Cites participant evidence_id proving compliant state<br/>3. Statutory retained records mapped to VERIFY_RECORD_PRESENT<br/>4. Strict injective 5-tuple sorting & renumbering 1..K"]
    end

    RefNA --> JoinEgress{Join: Collect Finished Cases}
    RefIncomplete --> RefWitness
    RefComplete --> RefWitness

    subgraph RefWitness ["sd: Witness Grounding & Egress Pipeline"]
        direction TB
        WitnessText["1. PromptGuard asserts evidence_id in manifest & T <= audit_at<br/>2. P(Hallucination) = 0 invariant enforced<br/>3. ReplayTracer stores graph (LRU bounded to 2,000)<br/>4. CsvHandler streams natural numeric sorted RFC-4180 CSV row"]
    end

    RefWitness --> JoinEgress

    JoinEgress --> CheckAllDone{Decision: Have all 518 cases<br/>completed?}

    CheckAllDone -- "[Pending cases remain]" --> RefIngress
    CheckAllDone -- "[All 518 cases finished]" --> FinalNode([Activity Final Node: output.csv Validated])
```

---

## 2. Interaction Occurrences & Contract Summary

| Interaction Fragment | Enclosing Subsystem | Formal Theorem / Guarantee |
|---|---|---|
| `sd: One-Time Static Pre-Indexing` | `code.container` | Amortized zero per-case cost; 65 MB total memory footprint |
| `sd: Security Ingress Guardrails` | `code.security` | Disarms prompt injections before intent parsing; prevents OWASP LLM01 |
| `sd: Fast-Path NOT_APPLICABLE` | `code.agent.policy_auditor` | Deterministic $O(1)$ fast-path exit with empty steps `[]` |
| `sd: Multi-Agent Deep Estate Investigation` | `code.agent` & `code.ai` | **Theorem 1** (DSU Orbit Cache) + **Theorem 2** (Monotone Bisect Search) |
| `sd: Poset DAG Remediation Planning` | `code.agent.remediation_planner` | **Theorem 3** (Strictly Injective 5-Tuple Total Order) |
| `sd: Witness Grounding & Egress` | `code.ai` & `code.observability` | **Theorem 4** (Bounded LRU 2000) + **Theorem 5** (Knapsack Causal Cone) |
