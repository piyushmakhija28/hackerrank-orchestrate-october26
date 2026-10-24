"""
Centralized domain exception hierarchy.
Enforces Level 2.2 Docstrings-Only convention (no inline narration).
"""

class AuditAgentError(Exception):
    """Base exception for all deletion audit agent errors."""

class EntityResolutionError(AuditAgentError):
    """Raised when customer entity resolution or transitive closure fails."""

class SchemaValidationError(AuditAgentError):
    """Raised when input or output data fails schema validation contract."""

class MediaInspectionError(AuditAgentError):
    """Raised when attachment OCR or multimodal VLM inspection fails."""

class PolicyEvaluationError(AuditAgentError):
    """Raised when policy evaluation or retention conflict resolution fails."""

class RemediationPlanError(AuditAgentError):
    """Raised when remediation DAG construction or topological sorting fails."""
