# UML Deployment Diagram (Full Architecture): Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-structural-diagram-engineer`, `devops-engineer`)  
**Specification Standards:** Conforms to UML 2.5.1 Section 19 (Deployments, Nodes, Artifacts) and Level 2.2 Docstrings-Only convention.

---

## 1. Physical & Containerized Deployment Topology

This deployment diagram models runtime deployment environments across bare-metal workstations, Docker container virtualization, host memory hierarchies, persistent disk storage, and external evaluation harnesses.

```mermaid
flowchart TD
    %% ==========================================
    %% EXECUTION NODES & ENVIRONMENTS
    %% ==========================================
    subgraph HostNode ["Node: Evaluation Host Workstation (Windows 11 / Ubuntu / macOS)"]
        direction TB

        subgraph DockerNode ["Execution Environment: Docker Container (python:3.13-slim)"]
            direction TB

            subgraph RuntimeProc ["Process: Python 3.13 CPython Virtual Machine"]
                direction TB

                subgraph MainThread ["Thread: Main CLI Orchestrator (code/main.py)"]
                    ORCH_EXEC["DeletionAuditOrchestrator<br/>(Process Coordinator)"]
                    IOC_CONT["AuditContainer<br/>(Dependency Injector)"]
                end

                subgraph WorkerPool ["Worker Threads: ThreadPoolExecutor (max_workers=8)"]
                    T1["Worker Thread 1 (Cases 0..64)"]
                    T2["Worker Thread 2 (Cases 65..128)"]
                    T3["Worker Thread 3 (Cases 129..192)"]
                    T4["Worker Thread 4 (Cases 193..256)"]
                    T5["Worker Thread 5 (Cases 257..320)"]
                    T6["Worker Thread 6 (Cases 321..384)"]
                    T7["Worker Thread 7 (Cases 385..448)"]
                    T8["Worker Thread 8 (Cases 449..517)"]
                end

                subgraph InMemStore ["In-Memory Data Structures (~65 MB RAM)"]
                    DSU_MEM["DSU Disjoint-Set Maps<br/>(Parent & Rank Dicts)"]
                    ORBIT_MEM["Equivalence Orbit Cache<br/>(O(alpha(N)) Lookup Index)"]
                    SQLITE_MEM["In-Memory SQLite Connections<br/>(:memory: / sqlite3.connect)"]
                    BISECT_MEM["Monotone Worker Timestamps<br/>(Pre-sorted bisect array)"]
                    LRU_MEM["ReplayTracer Registry<br/>(Bounded LRU 2,000 Graphs)"]
                end
            end
        end

        subgraph DiskStorage ["Node: Local NVMe / SSD Storage Subsystem"]
            direction TB

            subgraph DatasetArtifacts ["Folder: dataset/ (Immutable Corpus)"]
                REQ_CSV["artifact: deletion_requests.csv<br/>(518 Cases)"]
                ID_CSV["artifact: user_identities.csv"]
                LOG_CSV["artifact: user_audit_log.csv"]
                ACT_CSV["artifact: system_activity.csv"]
                RULE_CSV["artifact: deletion_rules.csv"]
                MAN_CSV["artifact: evidence_files.csv"]
                EVD_DIR["folder: dataset/evidence/<br/>(SQL, JSON, PDF, Images, Logs)"]
            end

            subgraph OutputArtifacts ["Folder: Output Deliverables (Workspace Root)"]
                OUT_CSV["artifact: output.csv<br/>(518 Natural Sorted Rows)"]
                CHAT_LOG["artifact: log.txt<br/>(Verbatim Agent Audit Log)"]
                CODE_ZIP["artifact: code.zip<br/>(Runnable Solution Package)"]
                EVAL_DIR["folder: evaluation/<br/>(evaluation_report.md, usage_report.md)"]
            end
        end
    end

    subgraph ExternalHarness ["Node: HackerRank Official Evaluation Infrastructure"]
        GRADER_PROC["HackerRank Automated Grader<br/>(Dockerized Sandbox)"]
    end

    %% ==========================================
    %% COMMUNICATION PATHS & DEPLOYMENT LINKS
    %% ==========================================
    MainThread --> WorkerPool
    WorkerPool --> InMemStore

    DatasetArtifacts -->|"POSIX Read-Only Stream"| MainThread
    DatasetArtifacts -->|"mmap / Read-Only Load"| InMemStore

    WorkerPool -->|"Buffered Thread-Safe Append"| OUT_CSV
    MainThread -->|"Append-Only Audit Stream"| CHAT_LOG
    MainThread -->|"Zip Packaging Engine"| CODE_ZIP

    OutputArtifacts -->|"HTTPS POST / Zip Upload"| ExternalHarness
```

---

## 2. Node Specifications & Hardware Profile

| Node / Device | Runtime Environment | Memory Footprint | Storage Allocation | Concurrency Level |
|---|---|---|---|---|
| **Host Workstation** | Windows / Linux / macOS x86_64 or ARM64 | $\ge 8.0 \text{ GB}$ Recommended | $\ge 1.0 \text{ GB}$ Free Disk Space | Multi-Core CPU |
| **Docker Container** | `python:3.13-slim` Linux Kernel $\ge 5.15$ | $512 \text{ MB}$ Container Limit | Ephemeral Container FS | cgroup restricted |
| **CPython Virtual Machine** | Python 3.13 with native POSIX threads | $\approx 65 \text{ MB}$ RSS Heap | N/A | Global Interpreter Lock (GIL) friendly I/O |
| **In-Memory SQLite** | `sqlite3` in-memory attached databases | $\approx 22 \text{ MB}$ | RAM Buffer Pool | Thread-local connections |
| **Equivalence Orbit Cache** | Python `dict[str, set[str]]` hash index | $\approx 8 \text{ MB}$ | RAM | Shared Read-Only across workers |
| **ReplayTracer LRU Cache** | Bounded deque + dict (Max 2,000 items) | $\approx 14 \text{ MB}$ | RAM | Thread-safe Mutex guarded |
| **Persistent Storage** | NVMe / SSD with NTFS or ext4 filesystem | N/A | Dataset: $45 \text{ MB}$ | Direct asynchronous read |
