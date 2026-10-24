# CLAUDE.md: Coding Assistant Guidelines & Project Context
## Challenge: HackerRank Orchestrate — Ghost Data Still Exists (October 2026)

---

## Project Overview
Autonomous AI Deletion Audit Agent designed for Northstar Shop's $2.4M ghost data incident. The system investigates multi-store data estates, builds transitive customer identity equivalence classes, audits media support attachments, tracks CDC/ETL zombie sync paths, evaluates GDPR vs statutory tax retention policies, and synthesizes ordered remediation DAGs.

---

## Architecture & Structure
The codebase strictly adheres to SOLID principles and Level 2.2 Docstrings-Only standards:

```
code/
├── main.py                     # CLI entrypoint and orchestrator
├── container.py                # IoC container for dependency injection
├── core/                       # Interfaces, domain models, exceptions
│   ├── interfaces.py           # Protocol definitions (SOLID DIP & ISP)
│   ├── models.py               # Immutable domain DTOs & Pydantic models
│   └── exceptions.py           # Centralized domain exception hierarchy
├── agent/                      # Core agent implementations
│   ├── identity_resolver.py    # DSU entity linkage with Ackermann complexity
│   ├── multimodal_inspector.py # Two-tier OCR & Vision LLM inspector
│   ├── lineage_tracer.py       # Sync process lineage & zombie detector
│   ├── policy_auditor.py       # Deletion rules vs retention matrix evaluator
│   └── remediation_planner.py  # Poset DAG & topological action planner
├── evaluation/                 # Evaluation harness & benchmark
│   ├── evaluator.py            # Precision, Recall, F1, Exact Match scorer
│   └── benchmark.py            # Synthetic multi-store benchmark generator
└── utils/                      # Utilities & Submission tooling
    ├── csv_handler.py          # RFC 4180 streaming reader/writer
    ├── schema_validator.py     # Pydantic v2 output validator
    ├── export_transcript.py    # AI pair-programming transcript exporter
    └── package_submission.py   # Clean code.zip packager
```

---

## Development Guidelines

### 1. Code Standards & Docstrings
- **Strict Level 2.2 Docstrings-Only:** Every public and protected class, method, and function must have explicit contract docstrings specifying Purpose, Parameters, Returns, and Raises.
- **BANNED:** Inline comments narrating *what* lines do (e.g. `# loop over records`). Inline comments are permitted ONLY for *why* (non-obvious mathematical or algorithmic decisions).
- **Type Annotations:** 100% strict type hints across all function arguments and returns.

### 2. SOLID Architecture Enforcement
- **Single Responsibility (SRP):** Keep agents focused on single domain tasks.
- **Open/Closed (OCP):** Extend functionality via strategy protocols (`IMediaAuditor`, `IPolicyAuditor`).
- **Liskov Substitution (LSP):** Concrete strategies must be drop-in replaceable.
- **Interface Segregation (ISP):** Use targeted protocols in `code/core/interfaces.py`.
- **Dependency Inversion (DIP):** Depend on protocols, inject via `AuditContainer`.

### 3. Submission Deliverables Guardrails
- `code.zip` must contain strictly `code/` and exclude `data/`, `dataset/`, `venv/`, and `.git/`.
- `output.csv` must strictly adhere to the exact problem statement schema.
- `log.txt` must capture full AI conversation history and timestamps.
