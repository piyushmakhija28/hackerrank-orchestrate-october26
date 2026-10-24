# UML Deployment Diagram: Autonomous Deletion Audit Agent
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`uml-diagram-mathematics-expert`, `devops-engineer`)  
**Specification Standards:** Conforms to Level 2.2 Docstrings-Only convention and RFC-4180 / ISO-8601 contracts.

```mermaid
flowchart TD
    subgraph HostNode ["Enterprise Linux Host / Cloud Node (Linux / Windows)"]
        subgraph DockerRuntime ["OCI Container Runtime (Docker / Containerd)"]
            subgraph AppContainer ["Pod / Container: deletion-audit-agent:latest"]
                Python["Python 3.13 Runtime"]
                
                subgraph AppCode ["Application Layer"]
                    Entry["CLI Entry: code/main.py"]
                    Core["Container & Agents Engine"]
                    SQLiteMem["In-Memory SQLite C-Engine (:memory:)"]
                    Tele["Telemetry & Health (code/core/telemetry.py)"]
                end
                
                Python --> Entry
                Entry --> Core
                Core --> SQLiteMem
                Core --> Tele
            end
        end

        subgraph HostStorage ["Host File System Mounts"]
            DataMount["dataset/ (Read-Only Mount)\n- deletion_requests.csv\n- user_identities.csv\n- system_activity.csv\n- evidence/"]
            OutputMount["output.csv (Read-Write Mount)\nGenerated Predictions"]
            LogMount["log.txt (Read-Write Mount)\nAudit Chat Transcript"]
        end

        subgraph CICD ["CI/CD & Cloud Orchestration"]
            GHA[".github/workflows/ci.yml\nAutomated Lint, Pytest & Packaging"]
            K8s["deploy/kubernetes/\nDeployment, PDB & HPA"]
        end
    end

    DataMount -.->|Volume Mount :ro| AppContainer
    AppContainer -.->|Writes output| OutputMount
    AppContainer -.->|Writes turns| LogMount
    GHA -->|Builds & Tests| DockerRuntime
    K8s -->|Schedules & Scales| AppContainer
```
