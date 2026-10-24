"""
Interface protocols defining abstract contracts for the Deletion Audit Agent.
Conforms strictly to SOLID Interface Segregation and Dependency Inversion Principles.
Enforces Level 2.2 Docstrings-Only convention (no inline narration).
"""
from typing import Protocol, Set, Dict, List, Tuple, Any
from pathlib import Path
import polars as pl
from code.core.models import (
    AuditVerdict,
    AuditStep,
    SyncProcess,
    ExposedRecord,
    DeletionRequest
)

class IEntityResolver(Protocol):
    """Protocol for customer entity resolution and alias linkage."""
    def ingest_records(self, dataframe: pl.LazyFrame, id_columns: List[str]) -> None:
        """Ingest tabular records and populate internal equivalence classes.
        
        Args:
            dataframe: Lazy Polars frame of records.
            id_columns: Column names containing identifier tokens.
        """
        ...

    def resolve_cluster(self, seed_identifier: str) -> Set[str]:
        """Retrieve all transitivity-linked current and historical identifiers.
        
        Args:
            seed_identifier: Starting identifier token (e.g. email or user ID).
        Returns:
            Complete set of linked identifier tokens.
        """
        ...

class IMultimodalInspector(Protocol):
    """Protocol for inspecting heterogeneous evidence across files, databases, and media."""
    def parse_pdf(self, file_path: Path) -> str:
        """Extract text from a PDF document.
        
        Args:
            file_path: Absolute path to PDF file.
        Returns:
            Extracted text content.
        """
        ...

    def parse_image(self, file_path: Path) -> str:
        """Extract text from an image file using OCR.
        
        Args:
            file_path: Absolute path to image file.
        Returns:
            Extracted text content.
        """
        ...

    def query_evidence(self, user_cluster: Set[str], audit_at: str) -> List[Dict[str, Any]]:
        """Retrieve all evidence hits captured at or before audit_at mentioning target cluster.
        
        Args:
            user_cluster: Set of user identifier tokens.
            audit_at: ISO-8601 audit cutoff timestamp.
        Returns:
            List of evidence hit dictionaries.
        """
        ...

class ILineageTracer(Protocol):
    """Protocol for detecting zombie sync and replication paths."""
    def register_process(self, process: SyncProcess) -> None:
        """Register an active data movement pipeline.
        
        Args:
            process: SyncProcess model instance.
        """
        ...

    def detect_zombie_paths(self, exposed_stores: Set[str], primary_store: str) -> List[str]:
        """Detect active processes capable of resurrecting data from exposed stores.
        
        Args:
            exposed_stores: Set of store names containing residual customer data.
            primary_store: Name of primary user-account store.
        Returns:
            List of process IDs that can recreate deleted records.
        """
        ...

class IPolicyAuditor(Protocol):
    """Protocol for evaluating policy compliance and retention exceptions."""
    def load_rules(self, rules_df: pl.DataFrame) -> None:
        """Load governance rules from deletion_rules.csv.
        
        Args:
            rules_df: Dataframe of policy rules.
        """
        ...

    def is_deletion_request(self, request_text: str) -> bool:
        """Determine whether free-text request authorizes account deletion.
        
        Args:
            request_text: Content of user request.
        Returns:
            True if deletion requested, False for other requests (portability, opt-out, access).
        """
        ...

    def evaluate(
        self,
        case_req: DeletionRequest,
        cluster: Set[str],
        evidence_hits: List[Dict[str, Any]]
    ) -> Tuple[AuditVerdict, List[Dict[str, Any]]]:
        """Evaluate request compliance against deletion rules and observed evidence.
        
        Args:
            case_req: DeletionRequest instance.
            cluster: Complete set of user tokens.
            evidence_hits: Evidence items captured at or before audit_at.
        Returns:
            Tuple of (AuditVerdict, list_of_findings_or_violations).
        """
        ...

class IRemediationPlanner(Protocol):
    """Protocol for building ordered remediation and verification steps."""
    def build_steps(
        self,
        verdict: AuditVerdict,
        case_findings: List[Dict[str, Any]],
        compliant_verifications: List[Dict[str, Any]]
    ) -> List[AuditStep]:
        """Construct ordered remediation steps or verification proofs.
        
        Args:
            verdict: Audit status verdict.
            case_findings: Observed non-compliant findings.
            compliant_verifications: Verified compliant states.
        Returns:
            Ordered list of AuditStep instances.
        """
        ...
