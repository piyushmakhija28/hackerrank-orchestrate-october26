# UML Component Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-diagram-mathematics-expert`)  
**Specification Standards:** Conforms to Level 2.2 Docstrings-Only convention and RFC-4180 / ISO-8601 contracts.

```mermaid
flowchart TD
    subgraph DataIngestion ["Data Ingestion Layer (Dataset Corpus)"]
        DR["deletion_requests.csv\n(518 Cases)"]
        UI["user_identities.csv\n(Identity Snapshots)"]
        UAL["user_audit_log.csv\n(Historical Aliases)"]
        SA["system_activity.csv\n(Global Event Stream)"]
        DLR["deletion_rules.csv\n(Statutory Retention Rules)"]
        EF["evidence_files.csv\n(94 Evidence Manifest)"]
        EVD["dataset/evidence/\n(SQL, JSON, Logs, Attachments)"]
    end

    subgraph AgentCore ["Autonomous Multi-Agent Processing Core"]
        direction TB
        AC["AuditContainer\n(IoC Dependency Injection)"]
        
        subgraph SubAgents ["Specialized Subagents"]
            IR["IdentityResolver\n(Disjoint-Set Union Graph)"]
            MI["MultimodalInspector\n(In-Memory SQLite & Inverted Index)"]
            LT["LineageTracer\n(CDC & Zombie Process Detector)"]
            PA["PolicyAuditor\n(Retention & Erasure Classifier)"]
            RP["RemediationPlanner\n(Poset DAG Topological Scheduler)"]
        end

        AC --> IR
        AC --> MI
        AC --> LT
        AC --> PA
        AC --> RP
    end

    subgraph OrchestrationLayer ["CLI Orchestration & Validation Pipeline"]
        CLI["code/main.py\n(CLI Orchestrator)"]
        CSVH["code/utils/csv_handler.py\n(RFC-4180 Streaming Engine)"]
        OSV["code/utils/schema_validator.py\n(Strict Grader Schema Validator)"]
        TEL["code/core/telemetry.py\n(Structured Metrics & Logging)"]
    end

    subgraph OutputLayer ["Official Submission Deliverables"]
        OUT["output.csv\n(518 Audited Rows, RFC-4180)"]
        LOG["log.txt\n(Verbatim Audit Transcript)"]
        ZIP["code.zip\n(Submitted Source Package)"]
        EVAL["evaluation/\n(Benchmark & Usage Reports)"]
    end

    DR --> CLI
    UI --> IR
    UAL --> IR
    SA --> LT
    DLR --> PA
    EF --> MI
    EVD --> MI

    CLI --> AC
    CLI --> CSVH
    CSVH --> OUT
    CLI --> OSV
    CLI --> TEL
    CLI --> LOG
    CLI --> EVAL
    CLI --> ZIP
```
