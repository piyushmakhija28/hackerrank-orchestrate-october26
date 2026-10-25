# System Diagrams Master Index: Ghost Data Still Exists
**Challenge:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**System:** Enterprise Deletion Audit Agent & Compliance Verification Platform  
**Authors:** Visual Architecture & Design Squad (`technical-writer-agent`, `uml-structural-diagram-engineer`, `drawio-diagram-architect`)  
**Specification Standards:** Conforms to ISO/IEC/IEEE 42010:2011 Architecture Description, UML 2.5.1 OMG Standards, and Claude Global Rules `45-uml-diagram-lifecycle.md` & `46-architecture-documentation.md`.

---

## 1. Executive Overview

This directory houses the comprehensive architectural, behavioral, and interaction diagram suite for the **Ghost Data Still Exists** autonomous deletion-audit system. Every diagram has been audited and synchronized directly against the production source code under `code/`. All automated MCP stubs (such as `LLM generation unavailable`, `No call graph data`, and generic placeholder templates) have been completely eliminated.

The suite is delivered in two complementary formats:
1. **Mermaid Markdown (`uml/*.md`)**: Standardized diagram-as-code format conforming to UML 2.5.1 that renders natively in GitHub, GitLab, VS Code, and Markdown previewers.
2. **Draw.io XML (`drawio/*.drawio`)**: Full visual vector diagram models with UML shape stencils and orthogonal Bézier edge routing, editable in [draw.io](https://app.diagrams.net), Draw.io Desktop, or VS Code using the Draw.io integration extension.

---

## 2. UML Diagram Suite (`uml/`)

The system implements the complete standard set of 13 diagram types required by Rule 45 plus supplementary deep-dive views across Structural, Behavioral, and Interaction viewpoints:

| # | Diagram Name | Category | Canonical File Link | Primary Purpose & Code Coverage |
|---|---|---|---|---|
| 1 | **Class Diagram** | Structural | [class_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/class_diagram.md) | Full OOP model with abstract interfaces (`IEntityResolver`, `IPolicyAuditor`, `IRemediationPlanner`), concrete agents, DSU internals, and domain DTOs. *(Also: [class_diagram_full.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/class_diagram_full.md))* |
| 2 | **Package Diagram** | Structural | [package_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/package_diagram.md) | Module boundaries across all 8 packages under `code/`, acyclic import dependency DAG, and Robert C. Martin's Package Coupling & Stability metrics ($A, I, D$). |
| 3 | **Component Diagram** | Structural | [component_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/component_diagram.md) | 7-tier modular architecture with provided/required interfaces (lollipops/sockets), boundary ports, and data flow channels. *(Also: [component_diagram_full.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/component_diagram_full.md))* |
| 4 | **Sequence Diagram** | Interaction | [sequence_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/sequence_diagram.md) | End-to-end multi-agent orchestration sequence across all 11 collaborating lifelines, pre-indexing loop, and combined fragments (`alt`, `par`, `loop`). |
| 5 | **State Machine Diagram** | Behavioral | [state_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/state_diagram.md) | 3 state machines: (1) Deletion request lifecycle, (2) Tri-state concurrent circuit breaker, (3) Atomic audit step state transitions. |
| 6 | **Activity Diagram** | Behavioral | [activity_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/activity_diagram.md) | Operational workflow execution flow from request ingestion through decision diamonds, fork/join parallel investigation, to natural sorted CSV row output. |
| 7 | **Deployment Diagram** | Structural | [deployment_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/deployment_diagram.md) | Host workstation nodes, Docker container virtualization, Python 3.13 runtime threads, in-memory SQLite replicas, and disk artifacts. *(Also: [deployment_diagram_full.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/deployment_diagram_full.md))* |
| 8 | **Use Case Diagram** | Behavioral | [usecase_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/usecase_diagram.md) | Actor goals (Participant, HackerRank Grader, Policy Engine), 20 system use cases, and `<<include>>` / `<<extend>>` dependencies. *(Also: [use_case_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/use_case_diagram.md))* |
| 9 | **Object Diagram** | Structural | [object_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/object_diagram.md) | Concrete heap snapshot of objects, slot values, and links during an active audit of `case_005` (residual data + CDC sync hazard). |
| 10 | **Composite Structure** | Structural | [composite_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/composite_diagram.md) | Structured classifier internal decomposition of `AuditContainer` and `DeletionAuditOrchestrator`, boundary ports, and internal connectors. *(Also: [composite_structure.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/composite_structure.md))* |
| 11 | **Interaction Overview** | Interaction | [interaction_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/interaction_diagram.md) | High-level control flow coordinating major sequence interaction fragments (`ref`), decision gates, concurrency forks, and joins. *(Also: [interaction_overview.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/interaction_overview.md))* |
| 12 | **Communication Diagram** | Interaction | [communication_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/communication_diagram.md) | Collaboration graph showing structural links between roles and numbered synchronous/asynchronous message dispatches. |
| 13 | **Call Graph Diagram** | Structural | [call_graph_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/call_graph_diagram.md) | Function call graph across all modules, invocation frequencies, and execution edges. |
| 14 | **Timing Diagram** | Interaction | [timing_diagram.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/timing_diagram.md) | Execution timeline tracks with duration intervals ($T_{\min}, T_{\max}$), latency SLA bounds, and empirical benchmark timings. |
| 15 | **Sequence (Deep-Dive)** | Interaction | [sequence_incomplete_flow.md](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/uml/sequence_incomplete_flow.md) | Granular chronological sequence for complex INCOMPLETE cases with ghost data residuals and active sync replication. |

---

## 3. Draw.io Visual Model Suite (`drawio/`)

Full visual XML models for architectural design, presentations, and interactive exploration in [draw.io](https://app.diagrams.net):

| # | Diagram Name | File Link | Focus Area & Visual Topology |
|---|---|---|---|
| 1 | **Class Architecture** | [class_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/class_diagram.drawio) | Comprehensive class diagram model featuring all 7 tiers, method signatures, attributes, and connectors. |
| 2 | **Package Architecture** | [package_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/package_diagram.drawio) | Multi-package namespace map for all 8 packages under `code/`, internal modules, and dependency flows. |
| 3 | **Component Architecture** | [component_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/component_diagram.drawio) | 7-tier modular component architecture with provided/required interfaces, ports, and inter-tier data streams. |
| 4 | **Sequence Flow** | [sequence_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/sequence_diagram.drawio) | Visual sequence diagram with 11 lifelines, pre-indexing blocks, loop containers, and decision branches. |
| 5 | **State Machine** | [state_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/state_diagram.drawio) | Case lifecycle, tri-state circuit breaker, and atomic audit step state machines with guard labels. *(Also: [state_machine.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/state_machine.drawio))* |
| 6 | **Operational Activity** | [activity_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/activity_diagram.drawio) | Operational activity flow from input sanitization, DSU lookup, parallel SQLite/lineage forks, to CSV row egress. |
| 7 | **Deployment Topology** | [deployment_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/deployment_diagram.drawio) | Local workstation node, Docker container virtualization, CPython VM heap (~65 MB RAM), and NVMe disk storage. |
| 8 | **System Use Cases** | [usecase_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/usecase_diagram.drawio) | 5 external actors, system boundary, 20 deletion-audit use cases, and `<<include>>`/`<<extend>>` associations. |
| 9 | **Object Heap Snapshot** | [object_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/object_diagram.drawio) | Concrete heap snapshot of objects, slot values, and memory relationships during an active audit of `case_005`. |
| 10 | **Composite Structure** | [composite_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/composite_diagram.drawio) | Structured classifier internal decomposition of `AuditContainer` and `DeletionAuditOrchestrator` with boundary ports. |
| 11 | **Interaction Overview** | [interaction_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/interaction_diagram.drawio) | High-level control flow coordinating major sequence interaction fragments (`ref`), decision gates, forks, and joins. |
| 12 | **Communication Messaging** | [communication_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/communication_diagram.drawio) | Multi-agent collaboration graph showing structural links between roles and numbered message dispatches. |
| 13 | **Call Graph Model** | [call_graph_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/call_graph_diagram.drawio) | Function and method invocation call graph across all system modules with complexity highlighting. |
| 14 | **Subsystem Timing** | [timing_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/timing_diagram.drawio) | Execution timeline tracks with duration intervals ($T_{\min}, T_{\max}$) and latency SLA bounds across 8 subsystems. |
| 15 | **System Architecture** | [system_architecture.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/system_architecture.drawio) | 7 swimlanes mapping the full multi-agent estate across the 5 Claude Global Library Engineering Disciplines. |
| 16 | **Entity Relationship (ER)** | [er_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/er_diagram.drawio) | Complete relational schema of all 7 input/output datasets and the embedded `AuditStep` JSON specification. |
| 17 | **Data Flow Diagram (DFD)** | [data_flow_diagram.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/data_flow_diagram.drawio) | Multi-level DFD with external entities, data stores D1–D6, processes 1.0–6.0, and labeled data flows. |
| 18 | **Agent Orchestration DAG** | [agent_interaction_flow.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/agent_interaction_flow.drawio) | Directed Acyclic Graph (DAG) of the 6 specialized squads, branch decisions, and output aggregation paths. |
| 19 | **Security Architecture** | [security_architecture.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/security_architecture.drawio) | 7-layer defense-in-depth model with AES-256-GCM AEAD vault, HMAC blind indexing, anti-reverse-engineering, honeytokens, and GDPR/DPDP regulatory compliance engine. |
| 20 | **Remediation Poset Flow** | [remediation_flow.drawio](file:///C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/hackerrank_orchestration_problem/drawio/remediation_flow.drawio) | Phase ordering (FINDING $\to$ REMEDIATION $\to$ VERIFICATION), 15 operations, and Theorem 3 injective 5-tuple sorting. |

---

## 4. How to Open & Render These Diagrams

### Opening Mermaid Diagrams (`uml/*.md`)
- **In VS Code:** Open any file in `uml/` and press `Ctrl+Shift+V` (or click "Open Preview to the Side").
- **On GitHub / GitLab:** Mermaid diagrams render natively inside markdown code blocks.
- **Online:** Copy any Mermaid code block into the [Mermaid Live Editor](https://mermaid.live).

### Opening Draw.io Diagrams (`drawio/*.drawio`)
- **In Web Browser:** Navigate to [app.diagrams.net](https://app.diagrams.net), select **File $\to$ Open From $\to$ Device**, and upload any `.drawio` file.
- **In VS Code:** Install the official **Draw.io Integration** extension (`hediet.vscode-drawio`). Once installed, clicking any `.drawio` file opens the visual canvas editor directly in the IDE.
- **In Draw.io Desktop:** Install the free [Draw.io Desktop application](https://www.drawio.com/) and open the file directly.
