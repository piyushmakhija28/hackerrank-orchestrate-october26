# UML Use Case Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-behavioral-diagram-engineer`, `technical-writer-agent`)  
**Specification Standards:** Conforms to UML 2.5.1 Section 18 (Use Cases) and Level 2.2 Docstrings-Only convention.

---

## 1. System Use Case Diagram

This diagram models the functional boundaries of the Deletion-Audit System, illustrating actor interactions, primary audit goals, extension guardrails, and inclusion dependencies.

```mermaid
flowchart LR
    %% ==========================================
    %% ACTORS (External Entities)
    %% ==========================================
    CLI(["Actor: CLI Runner / Participant"])
    GRADER(["Actor: HackerRank Evaluator"])
    EVSTORE(["Actor: Multi-Modal Evidence Store"])
    POLENG(["Actor: Statutory Policy Engine"])
    OBSYS(["Actor: Observability Backend"])

    %% ==========================================
    %% SYSTEM BOUNDARY
    %% ==========================================
    subgraph SYS ["System Boundary: Autonomous Deletion Audit Agent"]
        direction TB

        %% Primary Use Cases
        UC1(["UC-01: Audit Deletion Request"])
        UC2(["UC-02: Sanitize & Validate Input"])
        UC3(["UC-03: Determine Request Intent (NLU)"])
        UC4(["UC-04: Resolve User Identity (DSU)"])
        UC5(["UC-05: Scan Multi-Modal Evidence"])
        UC6(["UC-06: Trace System Lineage & Sync"])
        UC7(["UC-07: Apply Deletion Rules"])
        UC8(["UC-08: Build Causal-Cone Context"])
        UC9(["UC-09: Optimize & Deduplicate Tokens"])
        UC10(["UC-10: Generate Remediation Plan (Poset DAG)"])
        UC11(["UC-11: Verify Deletion Completeness"])
        UC12(["UC-12: Detect Prompt Injection (OWASP LLM01)"])
        UC13(["UC-13: Mask Sensitive PII in Logs"])
        UC14(["UC-14: Export Validated output.csv"])

        %% Secondary / Extension Use Cases
        UC15(["UC-15: Assert Witness Grounding (P(H)=0)"])
        UC16(["UC-16: Record Decision Graph (LRU 2000)"])
        UC17(["UC-17: Collect RED/USE Metrics"])
        UC18(["UC-18: Enforce Rate Limiting & Circuit Breaker"])
        UC19(["UC-19: Fast-Path NOT_APPLICABLE Synthesis"])
        UC20(["UC-20: Generate Evaluation & Usage Reports"])

        %% Inclusions (<<include>>)
        UC1 -->|"<<include>>"| UC2
        UC1 -->|"<<include>>"| UC3
        UC1 -->|"<<include>>"| UC4
        UC1 -->|"<<include>>"| UC5
        UC1 -->|"<<include>>"| UC6
        UC1 -->|"<<include>>"| UC7
        UC1 -->|"<<include>>"| UC8
        UC1 -->|"<<include>>"| UC9
        UC1 -->|"<<include>>"| UC10
        UC1 -->|"<<include>>"| UC11
        UC1 -->|"<<include>>"| UC14

        UC2 -->|"<<include>>"| UC12
        UC8 -->|"<<include>>"| UC9
        UC10 -->|"<<include>>"| UC15
        UC14 -->|"<<include>>"| UC16

        %% Extensions (<<extend>>)
        UC19 -.->|"<<extend>>"| UC3
        UC18 -.->|"<<extend>>"| UC1
        UC13 -.->|"<<extend>>"| UC16
        UC20 -.->|"<<extend>>"| UC14
    end

    %% ==========================================
    %% ACTOR-TO-USE-CASE ASSOCIATIONS
    %% ==========================================
    CLI --> UC1
    CLI --> UC20
    GRADER --> UC14

    EVSTORE --- UC5
    POLENG --- UC7
    OBSYS --- UC17
```

---

## 2. Actor Specification & Goals

| Actor | Classification | Architectural Role & Goals |
|---|---|---|
| **CLI Runner / Participant** | Primary Human Actor | Triggers batch audit pipeline, configures worker threads, and inspects diagnostic logs. |
| **HackerRank Evaluator** | Primary Automated Actor | Ingests `output.csv`, grades prediction accuracy across 518 cases, and validates schema compliance. |
| **Evidence Store** | Secondary System Actor | Supplies multi-modal evidence artifacts (in-memory SQLite, JSON, logs, PDF, images). |
| **Policy Engine** | Secondary System Actor | Dictates required data treatment (`HARD_DELETE`, `RETAIN`, `REDACT`, `ANONYMIZE`, `ACCOUNT_TOMBSTONE`). |
| **Observability Backend** | Secondary System Actor | Ingests OpenTelemetry spans, Prometheus metrics, and structured JSON logs. |
