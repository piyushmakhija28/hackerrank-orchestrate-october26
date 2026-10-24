# Software Requirements Specification (SRS)
## System: Autonomous AI Deletion Audit Agent (Ghost Data Still Exists)
### Challenge: HackerRank Orchestrate — October 2026

---

## 1. Purpose
This Software Requirements Specification (SRS) defines the functional, non-functional, and verification requirements for the **Autonomous AI Deletion Audit Agent**. The system investigates personal data sprawl across Northstar Shop's enterprise data estate (secondary databases, customer support attachments, search indexes, analytics data lakes, logs, archives, and backups) to audit customer deletion requests, detect zombie synchronization re-creation risks, generate ordered remediation plans, and verify compliance against privacy regulations (GDPR Art. 17 / CCPA) and statutory retention laws (IRS 7-year transaction retention).

---

## 2. Scope
The software encompasses:
- Multi-attribute customer entity resolution via Disjoint-Set Union (DSU) graph transitive closure.
- Two-tier support attachment media inspection (Local OCR pre-filter + Vision LLM verification).
- System replication lineage and zombie synchronization process tracking.
- Policy auditing reconciling `deletion_rules.csv` erasure mandates with statutory retention rules.
- Deadlock-free remediation action planning via Kahn's topological sort and Tarjan's SCC cycle breaking.
- Strict RFC 4180-compliant `output.csv` generation.
- Automated evaluation harness scoring predictions against ground truth labels.
- Real-time AI coding transcript exporter for `log.txt`.
- Submission packaging utility generating a compliant `code.zip`.

---

## 3. Requirements

### 3.1 Functional Requirements
- **FR-1: Request Status Determination:** For every deletion request, the system shall classify the status as `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE` (if the individual never requested deletion).
- **FR-2: Entity & Identifier Resolution:** The system shall link all current and historical customer identifiers (emails, phone numbers, usernames, device IDs, IP addresses) across all datastores using an equivalence relation $\mathcal{R}^*$.
- **FR-3: Unstructured Media Inspection:** The system shall audit customer support attachments, screenshots, and receipts using a two-tier OCR/VLM inspection pipeline to detect unredacted PII.
- **FR-4: Zombie Process Detection:** The system shall trace data lineage across Kafka streams, CDC pipelines, cron ETLs, and backup restore scripts to detect active processes capable of resurrecting deleted data.
- **FR-5: Policy Reconciliation:** The system shall enforce erasure rules from `deletion_rules.csv` while strictly preserving statutory retention records (e.g., tax/financial invoices).
- **FR-6: Ordered Remediation & Proof Synthesis:** 
  - For `INCOMPLETE` requests, synthesize an ordered action DAG preventing race conditions ($T(\text{PauseSync}) \prec T(\text{PurgeSinks}) \prec T(\text{PurgeSource}) \prec T(\text{EmitTombstone}) \prec T(\text{ResumeSync})$).
  - For `COMPLETE` requests, generate verifiable cryptographic or SQL query proof checks.
- **FR-7: Output Schema Adherence:** The system shall produce `output.csv` matching the exact challenge schema with strict escaping.
- **FR-8: AI Transcript Export:** The system shall extract conversation turns and tool executions into `log.txt` for submission.

### 3.2 Non-Functional Requirements
- **NFR-1 (Performance & Latency):** Tabular request audit latency shall not exceed $5\text{ ms}$ per request; average multi-modal audit latency shall not exceed $50\text{ ms}$ per request.
- **NFR-2 (Memory Upper Bound):** Peak memory consumption shall remain strictly $\le 512\text{ MB}$ by streaming data via 64 MB Polars Arrow chunks.
- **NFR-3 (Reliability & Zero Crash Guarantee):** The system shall handle missing fields, malformed CSV rows, corrupted images, and empty attachments gracefully with zero unhandled exceptions.
- **NFR-4 (Security & Privacy):** Zero raw PII shall be emitted to application logs, console stdout, or version-controlled files.
- **NFR-5 (Architecture & Code Quality):** All code shall adhere strictly to SOLID principles, Level 2.2 Docstrings-Only convention, and type-hint annotations throughout.

---

## 4. Acceptance Criteria
1. **Verification Test Suite:** 100% pass rate on all triad unit and integration tests (positive, negative, edge-case).
2. **Schema Integrity:** `output.csv` passes Pydantic v2 validation with zero column mismatches, extra spaces, or malformed rows.
3. **No Hardcoding:** Agent uses generalized heuristics and VLM extraction; zero hardcoded customer IDs or test case labels.
4. **Submission Packaging:** `code.zip` contains strictly `code/` and excludes virtualenvs, caches, datasets, and local media corpus.
5. **Interview Readiness:** AI Judge Voice Interview defense documentation is complete and verified.

---

## 5. Out of Scope
- Direct execution of live database drop commands against external cloud production databases.
- Real-time deployment to external cloud hosting environments (AWS/GCP/Azure) during the hackathon.
- Modification of HackerRank contest platform rules or evaluation harnesses.
