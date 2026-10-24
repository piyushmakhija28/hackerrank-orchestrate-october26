# UML Activity Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-diagram-mathematics-expert`)  
**Specification Standards:** Conforms to Level 2.2 Docstrings-Only convention and RFC-4180 / ISO-8601 contracts.

```mermaid
flowchart TD
    Start([Start: Ingest Deletion Request]) --> ParseText[Parse and Normalize request_text]
    ParseText --> DecisionAuth{Does request_text<br/>authorize deletion?}
    
    DecisionAuth -- No (Portability, Rectification, Opt-out) --> SetNA[Set deletion_status = NOT_APPLICABLE<br/>Set steps_json = '[]']
    SetNA --> OutputRow[Emit CSV Row: case_id, status, steps_json]
    
    DecisionAuth -- Yes --> ResolveDSU[Execute DSU Identity Resolver<br/>Extract Transitive Identity Cluster]
    ResolveDSU --> QueryEvidence[Query Inverted Evidence Hash Indexes<br/>Filter records where timestamp <= audit_at]
    QueryEvidence --> QueryLineage[Scan System Activity Stream<br/>Detect Active CDC Flows & Restore Hazards]
    
    QueryLineage --> CheckState{Were exposed records,<br/>active sync flows, or<br/>restore hazards found?}
    
    CheckState -- Yes --> SetIncomplete[Set deletion_status = INCOMPLETE]
    SetIncomplete --> GenFindings[Phase 1: Generate FINDING Steps<br/>Cite participant file_id / activity_id]
    GenFindings --> GenRemediation[Phase 2: Generate Ordered REMEDIATION Steps<br/>1. DISABLE_DATA_FLOW<br/>2. BLOCK_RESTORE<br/>3. DELETE_RECORD<br/>4. REDACT_RECORD<br/>5. ANONYMIZE_RECORD<br/>evidence_id = '']
    GenRemediation --> GenPostVerif[Phase 3: Generate Dual POST-VERIFICATION Steps<br/>VERIFY_RECORD_ABSENT / DISABLED / BLOCKED<br/>evidence_id = '']
    GenPostVerif --> SortPoset[Sort DAG by Poset Priority Ranks 1..15<br/>Tie-break: system_id asc, resource_id asc<br/>Renumber step_no consecutively 1..K]
    SortPoset --> OutputRow
    
    CheckState -- No --> SetComplete[Set deletion_status = COMPLETE]
    SetComplete --> GenVerifOnly[Phase 3: Generate VERIFICATION Steps Only<br/>VERIFY_RECORD_ABSENT / PRESENT / REDACTED<br/>Cite participant evidence_id proving state]
    GenVerifOnly --> SortPoset
    
    OutputRow --> End([End: Proceed to Next Case / Complete])
```
