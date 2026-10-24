"""
Unit tests for Policy Compliance Auditor.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import pytest
from pathlib import Path
from code.agent.policy_auditor import PolicyAuditor
from code.core.models import AuditVerdict, DeletionRequest

def test_policy_auditor_not_applicable_phrases() -> None:
    """Verify that all non-erasure user phrases correctly evaluate to non-deletion."""
    auditor = PolicyAuditor(Path("dataset/deletion_rules.csv"))
    
    non_deletion_samples = [
        "Please stop the promotional emails. I still need the account and my order history.",
        "I'd like to download my account information in a portable format. Please keep the profile active.",
        "I can't access my profile and need help resetting the login. Do not close the account.",
        "My surname is misspelled on the account. Can you correct it without removing anything else?",
        "Please remove me from marketing lists only. I still want receipts and service messages.",
        "Can you tell me what personal information you hold about me? This is an information request, not a request to erase.",
        "I need a copy of last year's invoices for my records. Please leave my profile and order history as they are.",
        "Please change the email address used for this account. I want to continue using the service with the new address.",
        "Could you send me a copy of the information held on my account? I still use it, so don't delete my profile.",
        "The mobile number on my profile is out of date. Please replace it with the new one shown below."
    ]
    
    for text in non_deletion_samples:
        assert not auditor.is_deletion_request(text), f"Failed for phrase: {text}"

def test_policy_auditor_valid_deletion_phrases() -> None:
    """Verify that legitimate erasure requests correctly evaluate to deletion requests."""
    auditor = PolicyAuditor(Path("dataset/deletion_rules.csv"))
    
    deletion_samples = [
        "Please permanently delete my account and erase all associated personal data across your systems.",
        "I request the immediate removal of all my personal details under GDPR Article 17 Right to Erasure.",
        "I found an old report saying my account still existed. Please check the latest state and confirm that the profile is gone.",
        "Please close my account and remove my search index documents and support tickets."
    ]
    
    for text in deletion_samples:
        assert auditor.is_deletion_request(text), f"Failed for deletion text: {text}"

def test_policy_auditor_rules_loading() -> None:
    """Verify that deletion_rules.csv is properly loaded with categories and statutory mandates."""
    auditor = PolicyAuditor(Path("dataset/deletion_rules.csv"))
    assert len(auditor.rules) > 0

def test_policy_auditor_evaluate_non_deletion() -> None:
    """Verify evaluate method returns NOT_APPLICABLE for non-deletion request."""
    auditor = PolicyAuditor(Path("dataset/deletion_rules.csv"))
    req = DeletionRequest(
        case_id="case_test_na",
        email="user@shop.com",
        requested_at="2026-09-01T12:00:00Z",
        reported_status="COMPLETE",
        reported_at="2026-09-02T12:00:00Z",
        audit_at="2026-09-15T12:00:00Z",
        request_text="Please stop the promotional emails only."
    )
    verdict, findings = auditor.evaluate(req, {"user@shop.com"}, [])
    assert verdict == AuditVerdict.NOT_APPLICABLE
    assert len(findings) == 0
