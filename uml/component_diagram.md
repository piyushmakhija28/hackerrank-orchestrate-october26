# UML Component Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-structural-diagram-engineer`, `solution-architect`)  
**Specification Standards:** Conforms to UML 2.5.1 Section 11.3 (Components, Provided/Required Interfaces, Ports) and Level 2.2 Docstrings-Only convention.

---

## 1. Multi-Tier Component Architecture

This component diagram models the complete 7-tier modular structure of the Deletion Audit Agent, highlighting strict component boundaries, provided interfaces (lollipops), required interfaces (sockets), and data flows.

```mermaid
flowchart TD
    %% ==========================================
    %% TIER 1: DATA INGESTION & DATASET CORPUS
    %% ==========================================
    subgraph Tier1 ["Tier 1: Data Ingestion & Storage Subsystem"]
        direction TB
        C_DR["component: DeletionRequests<br/>(deletion_requests.csv)"]
        C_ID["component: UserIdentities<br/>(user_identities.csv)"]
        C_UAL["component: UserAuditLog<br/>(user_audit_log.csv)"]
        C_ACT["component: SystemActivity<br/>(system_activity.csv)"]
        C_RUL["component: DeletionRules<br/>(deletion_rules.csv)"]
        C_EVD["component: EvidenceCorpus<br/>(evidence_files.csv + evidence/*)"]
    end

    %% ==========================================
    %% TIER 2: SECURITY & COMPLIANCE SUBSYSTEM
    %% ==========================================
    subgraph Tier2 ["Tier 2: Cryptographic Security & Regulatory Compliance (code/security/)"]
        direction TB
        C_SAN["component: InputSanitizer<br/>(OWASP LLM01 Prompt Injection Filter)"]
        C_PII["component: PiiShield<br/>(ISO/IEC 7812 Luhn Card Masking)"]
        C_RATE["component: RateLimiter<br/>(Token Bucket Burst 1000 / Refill 500s)"]
        C_CB["component: CircuitBreaker<br/>(Tri-State Concurrent Circuit Breaker)"]
        C_VAULT["component: CryptoSecurityVault<br/>(AES-256-GCM AEAD & Blind Indexing)"]
        C_TAMPER["component: AntiTamperGuard<br/>(Anti-Debugging & Honeytoken Traps)"]
        C_COMPL["component: ComplianceFrameworkMapper<br/>(GDPR, DPDP, SOC 2, PCI DSS)"]
        C_DATA["component: DataShieldManager<br/>(Encrypted File Store)"]
    end

    %% ==========================================
    %% TIER 3: MULTI-AGENT DOMAIN CORE
    %% ==========================================
    subgraph Tier3 ["Tier 3: Multi-Agent Audit Core (code/agent/)"]
        direction TB
        C_IOC["component: AuditContainer<br/>(IoC Dependency Injection Assembly)"]
        
        subgraph SpecializedAgents ["Specialized Domain Agents"]
            C_IR["component: IdentityResolver<br/>(DSU Path Compression O(alpha(N)))"]
            C_MI["component: MultimodalInspector<br/>(In-Memory SQLite & Evidence Index)"]
            C_LT["component: LineageTracer<br/>(Monotone Bisect Window Search O(log K))"]
            C_PA["component: PolicyAuditor<br/>(Multilingual NLU & Statutory Retain Rules)"]
            C_RP["component: RemediationPlanner<br/>(Poset DAG Injective 5-Tuple Scheduler)"]
        end

        C_IOC --> C_IR
        C_IOC --> C_MI
        C_IOC --> C_LT
        C_IOC --> C_PA
        C_IOC --> C_RP
    end

    %% ==========================================
    %% TIER 4: AI TOKEN OPTIMIZATION & ANTI-HALLUCINATION
    %% ==========================================
    subgraph Tier4 ["Tier 4: AI Token Optimization & Anti-Hallucination (code/ai/)"]
        direction TB
        C_CTX["component: ContextBuilder<br/>(Causal Cone T(e)<=audit_at Knapsack)"]
        C_TOK["component: TokenOptimizer<br/>(Subword BPE Dedup: 19,332 Tokens Saved)"]
        C_GRD["component: PromptGuard<br/>(Witness Grounding Invariant P(Hallucination)=0)"]
    end

    %% ==========================================
    %% TIER 5: SRE OBSERVABILITY & DIAGNOSTICS
    %% ==========================================
    subgraph Tier5 ["Tier 5: SRE Observability & Telemetry (code/observability/)"]
        direction TB
        C_LOG["component: StructuredLogger<br/>(Thread-Safe JSON MDC Logging)"]
        C_TRC["component: DistributedTracer<br/>(OpenTelemetry Span Context)"]
        C_MET["component: MetricsCollector<br/>(Prometheus RED/USE Percentiles P50/P95)"]
        C_REP["component: ReplayTracer<br/>(Bounded LRU 2000 Registry & ASCII RCA)"]
    end

    %% ==========================================
    %% TIER 6: ORCHESTRATION PIPELINE
    %% ==========================================
    subgraph Tier6 ["Tier 6: Orchestration & Concurrency Engine"]
        direction TB
        C_MAIN["component: DeletionAuditOrchestrator<br/>(code/main.py Master Engine)"]
        C_POOL["component: ThreadPoolExecutor<br/>(8 Concurrent Worker Threads)"]
        C_CSV["component: CsvHandler<br/>(RFC-4180 Streaming File I/O)"]
        C_SCH["component: SchemaValidator<br/>(Strict Output Schema Validator)"]
    end

    %% ==========================================
    %% TIER 7: SUBMISSION OUTPUT DELIVERABLES
    %% ==========================================
    subgraph Tier7 ["Tier 7: Official Submission Deliverables"]
        direction TB
        C_OUT["artifact: output.csv<br/>(518 Sorted Prediction Rows)"]
        C_TRANS["artifact: log.txt<br/>(Verbatim Conversation Audit Log)"]
        C_ZIP["artifact: code.zip<br/>(Production Source Package)"]
        C_REPS["artifact: evaluation/<br/>(evaluation_report.md & usage_report.md)"]
    end

    %% ==========================================
    %% COMPONENT INTERFACE CONNECTIONS (Data Flow)
    %% ==========================================
    C_DR -->|"Raw CSV Stream"| C_SAN
    C_SAN -->|"Sanitized Requests"| C_MAIN
    C_MAIN --> C_POOL
    C_POOL --> C_IOC

    C_ID --> C_IR
    C_UAL --> C_IR
    C_ACT --> C_LT
    C_RUL --> C_PA
    C_EVD --> C_MI

    C_IR -->|"Transitive Identity Cluster"| C_CTX
    C_MI -->|"Admissible Evidence Facts"| C_CTX
    C_LT -->|"Active Flows & Restore Risks"| C_CTX

    C_CTX -->|"Knapsack Packed Facts"| C_TOK
    C_TOK -->|"Deduplicated Facts"| C_PA
    C_PA -->|"Categorized Policy Violations"| C_RP
    C_RP -->|"Poset DAG Steps"| C_GRD

    C_MAIN --> C_LOG
    C_MAIN --> C_TRC
    C_MAIN --> C_MET
    C_MAIN --> C_REP

    C_GRD -->|"Validated Invariant Steps"| C_CSV
    C_CSV --> C_OUT
    C_MAIN --> C_SCH
    C_MAIN --> C_TRANS
    C_MAIN --> C_ZIP
    C_MAIN --> C_REPS
```

---

## 2. Component Interface Specification (Provided & Required)

| Component | Provided Interfaces (Lollipops) | Required Interfaces (Sockets) | Communication Protocol |
|---|---|---|---|
| `InputSanitizer` | `ISanitize` (strip injection, entropy) | `ILogger` | In-memory function call |
| `IdentityResolver` | `IEntityResolver` (`resolve_cluster`) | `IFileSystem` (read CSV) | In-memory hash lookup |
| `MultimodalInspector` | `IEvidenceScanner` (`query_facts`) | `ISQLiteDriver`, `IFileSystem` | SQLite C-API & file reads |
| `LineageTracer` | `ILineageTracker` (`trace_active_flows`) | `IFileSystem` (read CSV) | In-memory binary search |
| `PolicyAuditor` | `IPolicyAuditor` (`is_deletion`, `evaluate`) | `IFileSystem` (read CSV) | In-memory NLU rule evaluation |
| `RemediationPlanner` | `IRemediationPlanner` (`build_steps`) | None (pure algorithm) | In-memory Poset DAG sort |
| `ContextBuilder` | `IContextBuilder` (`causal_cone`, `knapsack`) | `ITokenEstimator` | In-memory priority queue |
| `TokenOptimizer` | `ITokenOptimizer` (`deduplicate`, `serialize`) | None (pure algorithm) | In-memory SHA-256 fingerprinting |
| `PromptGuard` | `IGuardrail` (`verify_grounding`) | None (manifest whitelist) | In-memory set intersection |
| `CsvHandler` | `ICsvStreamer` (`stream`, `write`) | `IFileSystem` | OS file descriptor I/O |
