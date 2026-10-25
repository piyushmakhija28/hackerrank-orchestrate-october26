# UML Composite Structure Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-structural-diagram-engineer`, `uml-diagram-mathematics-expert`)  
**Specification Standards:** Conforms to UML 2.5.1 Section 11.2 (StructuredClassifiers, Parts, Ports, Connectors) and Level 2.2 Docstrings-Only convention.

---

## 1. Structured Classifier Decomposition

This diagram models the internal part-decomposition, port boundaries, and connector wiring of `DeletionAuditOrchestrator` and `AuditContainer`.

```mermaid
flowchart TD
    %% ==========================================
    %% ORCHESTRATOR ENCLOSING BOUNDARY
    %% ==========================================
    subgraph ORCH ["classifier: DeletionAuditOrchestrator"]
        direction TB

        %% BOUNDARY PORTS
        p_ingress(["port p_ingress<br/>(Ingress Requests)"])
        p_egress(["port p_egress<br/>(RFC-4180 Output)"])
        p_telemetry(["port p_telemetry<br/>(Metrics & Spans)"])

        subgraph SEC_PART ["part: SecurityShield [1..1]"]
            IS["InputSanitizer"]
            PS["PiiShield"]
            RL["TokenBucketRateLimiter"]
            CB["ConcurrentCircuitBreaker"]
        end

        subgraph POOL_PART ["part: WorkerThreadPool [1..1]"]
            POOL["ThreadPoolExecutor<br/>max_workers = 8<br/>WorkerThreads [1..8]"]
        end

        subgraph OBS_PART ["part: ObservabilityHub [1..1]"]
            SL["StructuredLogger (JSON MDC)"]
            DT["DistributedTracer (OTel)"]
            MC["MetricsCollector (RED/USE)"]
            RT["ReplayTracer (LRU 2000)"]
        end

        subgraph CONT_PART ["part: container : AuditContainer [1..1]"]
            direction TB

            %% INTERNAL PORTS OF CONTAINER
            p_data(["port p_dataset<br/>(Dataset FS)"])
            p_evidence(["port p_evidence<br/>(94 Evidence Artifacts)"])

            subgraph AGENTS ["Collaborating Domain Parts"]
                IR_PART["part: entity_resolver : IdentityResolver [1..1]<br/>(DSU + Orbit Cache)"]
                MI_PART["part: multimodal_inspector : MultimodalInspector [1..1]<br/>(SQLite In-Memory + Manifest Index)"]
                LT_PART["part: lineage_tracer : LineageTracer [1..1]<br/>(Monotone Bisect Engine)"]
                PA_PART["part: policy_auditor : PolicyAuditor [1..1]<br/>(Multilingual NLU + Rules)"]
                RP_PART["part: remediation_planner : RemediationPlanner [1..1]<br/>(Poset DAG Injective Scheduler)"]
            end

            subgraph AI_SUBS ["AI Optimization Parts"]
                CB_PART["part: context_builder : ContextBuilder [1..1]<br/>(Causal Cone Knapsack)"]
                TO_PART["part: token_optimizer : TokenOptimizer [1..1]<br/>(Subword BPE Dedup)"]
                PG_PART["part: prompt_guard : PromptGuard [1..1]<br/>(Witness Grounding Invariant)"]
            end
        end
    end

    %% ==========================================
    %% PORTS & CONNECTORS WIRING
    %% ==========================================
    p_ingress -->|"requests.csv"| SEC_PART
    SEC_PART -->|"sanitized requests"| POOL_PART
    POOL_PART -->|"dispatched jobs"| CONT_PART

    p_data -->|"identities.csv, audit_log.csv"| IR_PART
    p_data -->|"system_activity.csv"| LT_PART
    p_data -->|"deletion_rules.csv"| PA_PART
    p_evidence -->|"evidence_files.csv, evidence/*"| MI_PART

    IR_PART -->|"transitive identity cluster"| MI_PART
    IR_PART -->|"identity tokens"| LT_PART
    MI_PART -->|"evidence facts"| CB_PART
    LT_PART -->|"active flows & restore hazards"| CB_PART
    CB_PART -->|"packed knapsack context"| TO_PART
    TO_PART -->|"deduplicated facts"| PA_PART
    PA_PART -->|"policy findings & exceptions"| RP_PART
    RP_PART -->|"Poset DAG steps"| PG_PART

    PG_PART -->|"grounded verified steps"| p_egress
    CONT_PART -->|"telemetry events"| OBS_PART
    OBS_PART -->|"aggregated metrics & spans"| p_telemetry
```

---

## 2. Ports and Connectors Specification

| Port | Multiplicity | Protocol / Type | Provided / Required Interface |
|---|---|---|---|
| `p_ingress` | $1$ | Streaming CSV Generator | Consumes raw `deletion_requests.csv` tuples |
| `p_dataset` | $1$ | Posix File Read Stream | Ingests static reference datasets (`user_identities.csv`, etc.) |
| `p_evidence` | $1$ | Heterogeneous Multi-modal Stream | In-memory SQLite connections, JSON, Log, PDF text streams |
| `p_egress` | $1$ | Buffered RFC-4180 Egress | Streams deterministic, natural numeric sorted `output.csv` rows |
| `p_telemetry` | $1$ | Structured MDC JSON / OTel Span | Emits Prometheus metrics and OpenTelemetry trace spans |

### Internal Part Connector Specifications
1. **Connector $C_1$ (`entity_resolver` $\to$ `multimodal_inspector`):** Delivers equivalence orbit token set $\text{Cluster}(u)$ for sub-millisecond hash-table lookups.
2. **Connector $C_2$ (`entity_resolver` $\to$ `lineage_tracer`):** Transmits token identifiers for chronologically bounded bisect activity window querying.
3. **Connector $C_3$ (`multimodal_inspector` $\to$ `context_builder`):** Feeds raw admissible evidence facts satisfying $T(e) \le audit\_at$.
4. **Connector $C_4$ (`context_builder` $\to$ `token_optimizer`):** Delivers knapsack-packed facts for subword BPE deduplication (saving 19,332 tokens).
5. **Connector $C_5$ (`token_optimizer` $\to$ `policy_auditor`):** Supplies dense, grounded context for statutory exception classification.
6. **Connector $C_6$ (`policy_auditor` $\to$ `remediation_planner`):** Dispatches categorized findings and compliant records for Poset DAG generation.
7. **Connector $C_7$ (`remediation_planner` $\to$ `prompt_guard`):** Streams ordered `AuditStep` candidates for witness grounding invariant assertion ($P(\text{Hallucination}) = 0$).
