"""Inversion of Control (IoC) Container for Dependency Injection.

Enforces SOLID Dependency Inversion Principle.
Enforces Level 2.2 Docstrings-Only convention (no inline narration).
"""

from pathlib import Path
from code.agent.identity_resolver import IdentityResolver
from code.agent.lineage_tracer import LineageTracer
from code.agent.multimodal_inspector import MultimodalInspector
from code.agent.policy_auditor import PolicyAuditor
from code.agent.remediation_planner import RemediationPlanner
from code.ai.context_builder import ContextBuilder
from code.ai.prompt_guard import PromptGuard
from code.ai.token_optimizer import TokenOptimizer


class AuditContainer:
    """Dependency injection container assembling all domain audit services.

    Attributes:
        dataset_dir: Path to base dataset directory.
        entity_resolver: Service for customer entity resolution.
        multimodal_inspector: Service for heterogeneous evidence inspection.
        lineage_tracer: Service for tracking active data pipelines.
        policy_auditor: Service for evaluating governance rules.
        remediation_planner: Service for synthesizing ordered actions.
        token_optimizer: Subsystem for token estimation, deduplication, and budgeting.
        context_builder: Subsystem for causal context filtering and knapsack packing.
        prompt_guard: Subsystem for anti-hallucination witness verification.
    """

    def __init__(self, dataset_dir: Path = Path("dataset")) -> None:
        """Initializes container, creating all domain services and AI subsystems.

        Args:
            dataset_dir: Root dataset path.
        """
        self.dataset_dir: Path = dataset_dir
        self.entity_resolver: IdentityResolver = IdentityResolver()
        self.multimodal_inspector: MultimodalInspector = MultimodalInspector(dataset_dir)
        self.lineage_tracer: LineageTracer = LineageTracer(dataset_dir / "system_activity.csv")
        self.policy_auditor: PolicyAuditor = PolicyAuditor(dataset_dir / "deletion_rules.csv")
        self.remediation_planner: RemediationPlanner = RemediationPlanner()
        self.token_optimizer: TokenOptimizer = TokenOptimizer()
        self.context_builder: ContextBuilder = ContextBuilder()
        self.prompt_guard: PromptGuard = PromptGuard(dataset_dir / "evidence_files.csv")
        self.initialize_identities()

    def initialize_identities(self) -> None:
        """Pre-load user identities and historical audit logs into IdentityResolver."""
        identities_csv = self.dataset_dir / "user_identities.csv"
        audit_log_csv = self.dataset_dir / "user_audit_log.csv"
        self.entity_resolver.load_identities_and_audit_log(identities_csv, audit_log_csv)
