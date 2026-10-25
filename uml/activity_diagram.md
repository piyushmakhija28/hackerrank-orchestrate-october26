# UML Activity Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`multi-agent-graph-orchestration-engineer`, `uml-diagram-mathematics-expert`)  
**Specification Standards:** Conforms to Level 2.2 Docstrings-Only convention and RFC-4180 / ISO-8601 contracts.

```mermaid
flowchart TD
    Start([Start: Ingest Deletion Request Row]) --> SanitizeInput[InputSanitizer: Disarm Prompt Injection<br/>Validate Shannon Entropy H in [2.5, 5.0]]
    SanitizeInput --> ParseText[Normalize request_text & Parse Intent]
    ParseText --> DecisionAuth{Does request_text<br/>authorize deletion?}
    
    DecisionAuth -- No (Portability, Rectification, Opt-out) --> SetNA[Set deletion_status = NOT_APPLICABLE<br/>Set steps_json = '[]']
    SetNA --> OutputRow[Emit CSV Row: case_id, status, steps_json]
    
    DecisionAuth -- Yes --> ResolveDSU[Execute DSU Identity Resolver<br/>Lookup Equivalence Orbit Cache in O(α(N))<br/>Extract Transitive Identity Cluster]
    ResolveDSU --> QueryEvidence[Query Inverted Evidence Hash Indexes & SQLite<br/>Filter records where timestamp <= audit_at]
    QueryEvidence --> QueryLineage[Query LineageTracer<br/>1. activities_by_token[cluster] in O(|K|)<br/>2. Monotone Bisect Window Search in O(log K)<br/>Detect Active CDC Flows & Restore Hazards]
    
    QueryLineage --> PackContext[ContextBuilder: Knapsack Context Allocation<br/>TokenOptimizer: Fact Fingerprinting & Dense Serialization]
    
    PackContext --> CheckState{Were exposed records,<br/>active sync flows, or<br/>restore hazards found?}
    
    CheckState -- Yes --> SetIncomplete[Set deletion_status = INCOMPLETE]
    SetIncomplete --> GenFindings[Phase 1: Generate FINDING Steps<br/>Cite participant file_id / activity_id]
    GenFindings --> GenRemediation[Phase 2: Generate Ordered REMEDIATION Steps<br/>1. DISABLE_DATA_FLOW<br/>2. BLOCK_RESTORE<br/>3. DELETE_RECORD<br/>4. REDACT_RECORD<br/>5. ANONYMIZE_RECORD<br/>evidence_id = '']
    GenRemediation --> GenPostVerif[Phase 3: Generate Dual POST-VERIFICATION Steps<br/>VERIFY_RECORD_ABSENT / DISABLED / BLOCKED<br/>evidence_id = '']
    GenPostVerif --> SortPoset[Sort DAG by Strictly Injective 5-Tuple:<br/>(phase_rank, op_rank, system_id, resource_id, evidence_id, state)<br/>Renumber step_no consecutively 1..K]
    
    CheckState -- No --> SetComplete[Set deletion_status = COMPLETE]
    SetComplete --> GenVerifOnly[Phase 3: Generate VERIFICATION Steps Only<br/>VERIFY_RECORD_ABSENT / PRESENT / REDACTED<br/>Cite participant evidence_id proving compliant state]
    GenVerifOnly --> SortPoset
    
    SortPoset --> VerifyWitness[PromptGuard: Verify Witness Grounding Invariant<br/>Assert P(Hallucination) = 0]
    VerifyWitness --> RecordTrace[ReplayTracer: Record Decision Graph<br/>Evict oldest if registry >= 2000 items]
    RecordTrace --> OutputRow
    
    OutputRow --> End([End: Natural Numeric Sorted Output Row])
```
