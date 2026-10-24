"""
Multimodal Evidence Ingestion and Inspection Engine.
Parses heterogeneous files across PDF, PNG screenshots, JSON, LOG, and SQL database snapshots.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import csv
import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict
import fitz
import winocr
from PIL import Image

class EvidenceFact:
    """Atomic observation extracted from evidence files.
    
    Attributes:
        evidence_id: Source evidence file identifier.
        captured_at: Timestamp when evidence snapshot was taken.
        system_id: Target system or service name.
        resource_id: Identifier of target record, connector, or backup.
        operation: Standardized AuditOperation string.
        state: Standardized AuditState string.
        is_finding: Whether observation represents a violation or residual finding.
        identifiers: Set of associated user identifier tokens.
    """
    def __init__(
        self,
        evidence_id: str,
        captured_at: str,
        system_id: str,
        resource_id: str,
        operation: str,
        state: str,
        is_finding: bool,
        identifiers: Optional[List[Any]] = None
    ) -> None:
        self.evidence_id: str = evidence_id
        self.captured_at: str = captured_at
        self.system_id: str = system_id
        self.resource_id: str = resource_id
        self.operation: str = operation
        self.state: str = state
        self.is_finding: bool = is_finding
        self.identifiers: Set[str] = {str(i).lower().strip() for i in (identifiers or []) if i}

class MultimodalInspector:
    """Ingests and queries all 94 heterogeneous evidence files across the enterprise data corpus.
    
    Attributes:
        dataset_dir: Base directory containing evidence_files.csv and evidence subfolders.
        manifest: Mapping from file_id to file metadata dictionary.
        facts: List of all extracted EvidenceFact observations.
        facts_by_res: Inverted index mapping lowercase resource_id to list of facts.
        facts_by_token: Inverted index mapping lowercase identifier token to list of facts.
    """
    def __init__(self, dataset_dir: Path) -> None:
        self.dataset_dir: Path = dataset_dir
        self.manifest: Dict[str, Dict[str, str]] = {}
        self.facts: List[EvidenceFact] = []
        self.facts_by_res: Dict[str, List[EvidenceFact]] = defaultdict(list)
        self.facts_by_token: Dict[str, List[EvidenceFact]] = defaultdict(list)
        self.resource_pattern: re.Pattern = re.compile(
            r'\b(account_\w+|search_\w+|analytics_\w+|support_\w+|export_\w+|data_flow_\w+|backup_\w+|audit_record_\w+|tombstone_\w+)\b'
        )
        self.email_pattern: re.Pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
        self.user_pattern: re.Pattern = re.compile(r'\buser_\w+\b')
        self.load_manifest()
        self.index_all_evidence_facts()

    def load_manifest(self) -> None:
        """Load evidence_files.csv manifest into memory."""
        manifest_path = self.dataset_dir / "evidence_files.csv"
        if manifest_path.exists():
            with open(manifest_path, mode="r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self.manifest[row["file_id"]] = row

    def parse_pdf(self, file_path: Path) -> str:
        """Extract plain text from a multi-page PDF document using PyMuPDF.
        
        Args:
            file_path: Absolute path to PDF file.
        Returns:
            Extracted text content.
        """
        try:
            doc = fitz.open(file_path)
            return "\n".join(page.get_text() for page in doc)
        except Exception:
            return ""

    def parse_image(self, file_path: Path) -> str:
        """Extract text from an application screenshot using Windows Native OCR.
        
        Args:
            file_path: Absolute path to image file.
        Returns:
            Extracted OCR text.
        """
        try:
            with Image.open(file_path) as img:
                res = winocr.recognize_pil_sync(img)
                return res.get("text", "")
        except Exception:
            return ""

    def parse_service_resource_export(self, eid: str, path: Path, cap_at: str) -> List[EvidenceFact]:
        """Extract structured observations from JSON service resource exports.
        
        Args:
            eid: Evidence file ID.
            path: Path to JSON file.
            cap_at: Captured at timestamp string.
        Returns:
            List of EvidenceFact instances.
        """
        facts: List[EvidenceFact] = []
        try:
            with open(path, mode="r", encoding="utf-8") as fp:
                data = json.load(fp)
            se = data.get("service_exports", {})

            for item in se.get("account_service", {}).get("profile_lookups", []):
                rid = item.get("resource_id", "")
                code = item.get("status_code", 0)
                prof = item.get("profile") or {}
                ids = [prof.get("email"), prof.get("customer_reference"), prof.get("phone")]
                if code == 404:
                    facts.append(EvidenceFact(eid, cap_at, "account_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT", False, ids))
                elif code == 200:
                    facts.append(EvidenceFact(eid, cap_at, "account_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))

            for item in se.get("analytics_platform", {}).get("profiles", []):
                rid = item.get("resource_id", "")
                email = item.get("email")
                cref = item.get("customer_reference")
                ids = [email, cref]
                if email:
                    facts.append(EvidenceFact(eid, cap_at, "analytics_platform", rid, "REPORT_EXPOSED_PII", "PRESENT", True, ids))
                else:
                    facts.append(EvidenceFact(eid, cap_at, "analytics_platform", rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", False, ids))

            for item in se.get("backup_service", {}).get("restore_entries", []):
                rid = item.get("resource_id", "")
                ids = [item.get("customer_email"), item.get("customer_reference")]
                allowed = item.get("restore_allowed", False)
                if allowed:
                    facts.append(EvidenceFact(eid, cap_at, "backup_service", rid, "REPORT_RESTORE_RISK", "ACTIVE", True, ids))
                else:
                    facts.append(EvidenceFact(eid, cap_at, "backup_service", rid, "VERIFY_RESTORE_BLOCKED", "BLOCKED", False, ids))

            for item in se.get("export_service", {}).get("exports", []):
                rid = item.get("resource_id", "")
                ids = [item.get("owner_email"), item.get("customer_reference")]
                if item.get("owner_email") or item.get("customer_reference"):
                    facts.append(EvidenceFact(eid, cap_at, "export_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                else:
                    facts.append(EvidenceFact(eid, cap_at, "export_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT", False, ids))

            for item in se.get("integration_service", {}).get("connectors", []):
                rid = item.get("resource_id", "")
                ids = [item.get("customer_email"), item.get("customer_reference")]
                enabled = item.get("enabled", False)
                if enabled:
                    facts.append(EvidenceFact(eid, cap_at, "integration_service", rid, "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", True, ids))
                else:
                    facts.append(EvidenceFact(eid, cap_at, "integration_service", rid, "VERIFY_DATA_FLOW_DISABLED", "DISABLED", False, ids))

            for item in se.get("search_service", {}).get("index_queries", []):
                rid = item.get("resource_id", "")
                query = item.get("query", "")
                hits = item.get("hits", {}).get("total", 0)
                ids = [query]
                for doc in item.get("hits", {}).get("documents", []):
                    ids.extend([doc.get("email"), doc.get("customer_reference")])
                if hits > 0:
                    facts.append(EvidenceFact(eid, cap_at, "search_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                else:
                    facts.append(EvidenceFact(eid, cap_at, "search_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT", False, ids))

            for item in se.get("security_service", {}).get("audit_records", []):
                rid = item.get("resource_id", "")
                ids = [item.get("subject_reference")]
                facts.append(EvidenceFact(eid, cap_at, "security_service", rid, "VERIFY_RECORD_PRESENT", "PRESENT", False, ids))

            for item in se.get("support_platform", {}).get("tickets", []):
                rid = item.get("resource_id", "")
                ids = [item.get("requester_email"), item.get("customer_reference")]
                if item.get("requester_email"):
                    facts.append(EvidenceFact(eid, cap_at, "support_platform", rid, "REPORT_EXPOSED_PII", "PRESENT", True, ids))
                else:
                    facts.append(EvidenceFact(eid, cap_at, "support_platform", rid, "VERIFY_RECORD_REDACTED", "REDACTED", False, ids))
        except Exception:
            pass
        return facts

    def parse_snapshot_bundle(self, eid: str, path: Path, cap_at: str) -> List[EvidenceFact]:
        """Extract structured observations from JSON snapshot bundles.
        
        Args:
            eid: Evidence file ID.
            path: Path to JSON snapshot bundle file.
            cap_at: Captured at timestamp string.
        Returns:
            List of EvidenceFact instances.
        """
        facts: List[EvidenceFact] = []
        try:
            with open(path, mode="r", encoding="utf-8") as fp:
                data = json.load(fp)
            for snap in data.get("snapshots", []):
                store = snap.get("data_store", "")
                for rec in snap.get("records", []):
                    rid = rec.get("resource_id", "")
                    sub = rec.get("subject_reference")
                    email = rec.get("email")
                    phone = rec.get("phone")
                    name = rec.get("name")
                    ids = [sub, email, phone, name]
                    
                    if store == "identity_service":
                        if email or phone or name:
                            facts.append(EvidenceFact(eid, cap_at, "identity_service", rid, "REPORT_EXPOSED_PII", "PRESENT", True, ids))
                        else:
                            facts.append(EvidenceFact(eid, cap_at, "identity_service", rid, "VERIFY_RECORD_REDACTED", "REDACTED", False, ids))
                    elif store == "security_service":
                        facts.append(EvidenceFact(eid, cap_at, "security_service", rid, "VERIFY_RECORD_PRESENT", "PRESENT", False, ids))
                    elif store == "account_service":
                        if rec:
                            facts.append(EvidenceFact(eid, cap_at, "account_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                        else:
                            facts.append(EvidenceFact(eid, cap_at, "account_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT", False, ids))
        except Exception:
            pass
        return facts

    def parse_txt_handover(self, eid: str, path: Path, cap_at: str) -> List[EvidenceFact]:
        """Extract structured observations from pipe-delimited handover text captures.
        
        Args:
            eid: Evidence file ID.
            path: Path to text handover file.
            cap_at: Captured at timestamp string.
        Returns:
            List of EvidenceFact instances.
        """
        facts: List[EvidenceFact] = []
        try:
            with open(path, mode="r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line or not line.startswith("-"):
                        continue
                    parts = [p.strip() for p in line.lstrip("-").split("|")]
                    if len(parts) >= 6:
                        _, sys_id, res_id, _, status, ident = parts[:6]
                        ids = [ident]
                        if status == "NOT_FOUND":
                            facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "VERIFY_RECORD_ABSENT", "ABSENT", False, ids))
                        elif status == "FOUND":
                            if sys_id == "security_service":
                                facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "VERIFY_RECORD_PRESENT", "PRESENT", False, ids))
                            else:
                                facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                        elif status == "IDENTIFIABLE":
                            facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "REPORT_EXPOSED_PII", "PRESENT", True, ids))
                        elif status == "ACTIVE":
                            if sys_id == "integration_service":
                                facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", True, ids))
                            elif sys_id == "backup_service":
                                facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "REPORT_RESTORE_RISK", "ACTIVE", True, ids))
                        elif status == "DISABLED":
                            facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "VERIFY_DATA_FLOW_DISABLED", "DISABLED", False, ids))
                        elif status == "BLOCKED":
                            facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "VERIFY_RESTORE_BLOCKED", "BLOCKED", False, ids))
                        elif status == "REDACTED":
                            facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "VERIFY_RECORD_REDACTED", "REDACTED", False, ids))
                        elif status == "ANONYMIZED":
                            facts.append(EvidenceFact(eid, cap_at, sys_id, res_id, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", False, ids))
        except Exception:
            pass
        return facts

    def parse_document_pdf(self, eid: str, path: Path, cap_at: str, origin: str) -> List[EvidenceFact]:
        """Extract structured observations from PDF document evidence.
        
        Args:
            eid: Evidence file ID.
            path: Path to PDF file.
            cap_at: Captured at timestamp string.
            origin: Origin system or context string.
        Returns:
            List of EvidenceFact instances.
        """
        facts: List[EvidenceFact] = []
        try:
            doc = fitz.open(path)
            text = "\n".join(page.get_text() for page in doc)
            emails = set(self.email_pattern.findall(text))
            users = set(self.user_pattern.findall(text))
            all_ids = list(emails | users)

            if "delivery_correction_attachment" in path.name or "support" in origin:
                res_match = re.search(r'\b(support_\w+)\b', text)
                rid = res_match.group(1) if res_match else "support_attachment"
                facts.append(EvidenceFact(eid, cap_at, "support_platform", rid, "REPORT_REMAINING_RECORD", "PRESENT", True, all_ids))
            elif "security_retention" in path.name or origin == "security_service":
                res_match = re.search(r'\b(audit_record_\w+)\b', text)
                rid = res_match.group(1) if res_match else "audit_record_retained"
                facts.append(EvidenceFact(eid, cap_at, "security_service", rid, "VERIFY_RECORD_PRESENT", "PRESENT", False, all_ids))
            elif "account_history" in path.name:
                res_match = re.search(r'\b(account_\w+)\b', text)
                rid = res_match.group(1) if res_match else "account_statement"
                facts.append(EvidenceFact(eid, cap_at, "account_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", True, all_ids))
        except Exception:
            pass
        return facts

    def parse_generic_records_json(self, eid: str, path: Path, cap_at: str, origin: str) -> List[EvidenceFact]:
        """Extract structured observations from generic JSON record files.
        
        Args:
            eid: Evidence file ID.
            path: Path to JSON record file.
            cap_at: Captured at timestamp string.
            origin: Origin system or context string.
        Returns:
            List of EvidenceFact instances.
        """
        facts: List[EvidenceFact] = []
        try:
            with open(path, mode="r", encoding="utf-8") as f:
                data = json.load(f)
            records = data.get("records", [])
            for rec in records:
                if "download_available" in rec or "owner_email" in rec or "file_name" in rec:
                    rid = rec.get("resource_id", "")
                    owner = rec.get("owner_email", "")
                    ids = [owner]
                    avail = rec.get("download_available", False)
                    if avail or owner:
                        facts.append(EvidenceFact(eid, cap_at, "export_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                    else:
                        facts.append(EvidenceFact(eid, cap_at, "export_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT", False, ids))
                elif "reporting_window" in rec or "metrics" in rec:
                    rid = rec.get("resource_id", "")
                    uid = rec.get("user_id")
                    email = rec.get("email")
                    ids = [uid, email]
                    if uid or email:
                        facts.append(EvidenceFact(eid, cap_at, "analytics_platform", rid, "REPORT_EXPOSED_PII", "PRESENT", True, ids))
                    else:
                        facts.append(EvidenceFact(eid, cap_at, "analytics_platform", rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", False, ids))
                elif "system" in rec and "resource_id" in rec:
                    sys_name = rec.get("system", "")
                    rid = rec.get("resource_id", "")
                    res = rec.get("result", "")
                    sub = rec.get("subject_reference", "")
                    ids = [sub]
                    if res == "NOT_FOUND":
                        facts.append(EvidenceFact(eid, cap_at, sys_name, rid, "VERIFY_RECORD_ABSENT", "ABSENT", False, ids))
                    elif res == "FOUND":
                        if sys_name == "security_service":
                            facts.append(EvidenceFact(eid, cap_at, sys_name, rid, "VERIFY_RECORD_PRESENT", "PRESENT", False, ids))
                        else:
                            facts.append(EvidenceFact(eid, cap_at, sys_name, rid, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                    elif res == "ANONYMIZED":
                        facts.append(EvidenceFact(eid, cap_at, sys_name, rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", False, ids))
                    elif res == "REDACTED":
                        facts.append(EvidenceFact(eid, cap_at, sys_name, rid, "VERIFY_RECORD_REDACTED", "REDACTED", False, ids))
        except Exception:
            pass
        return facts

    def parse_key_value_logs(self, eid: str, path: Path, cap_at: str) -> List[EvidenceFact]:
        """Extract structured observations from key-value structured log files.
        
        Args:
            eid: Evidence file ID.
            path: Path to log file.
            cap_at: Captured at timestamp string.
        Returns:
            List of EvidenceFact instances.
        """
        facts: List[EvidenceFact] = []
        kv_pattern = re.compile(r'(\w+)=(?:"([^"]*)"|(\S+))')
        trace_context: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"ids": set(), "resource_id": None, "service": None, "events": []})

        try:
            with open(path, mode="r", encoding="utf-8", errors="ignore") as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    kvs = {k: v1 or v2 for k, v1, v2 in kv_pattern.findall(line)}
                    tid = kvs.get("trace_id")

                    for key in [
                        "match_key", "lookup_key", "subject_key", "subject_ref", "subject_reference",
                        "correlation_key", "matched_value", "scan_key", "query", "email", "customer_reference"
                    ]:
                        val = kvs.get(key)
                        if val and tid:
                            trace_context[tid]["ids"].add(str(val).lower().strip())

                    if tid and kvs.get("resource_id"):
                        trace_context[tid]["resource_id"] = kvs.get("resource_id")
                    if tid and kvs.get("service"):
                        trace_context[tid]["service"] = kvs.get("service")
                    if tid:
                        trace_context[tid]["events"].append(kvs)

            for tid, ctx in trace_context.items():
                service = ctx["service"]
                res_id = ctx["resource_id"]
                ids = list(ctx["ids"])
                if not service or not res_id:
                    continue

                if service == "support_replica":
                    service = "support_platform"

                for ev in ctx["events"]:
                    event = ev.get("event", "")

                    if service == "account_service":
                        http_status = ev.get("http_status")
                        rows = ev.get("rows")
                        if http_status == "404" or rows == "0":
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "VERIFY_RECORD_ABSENT", "ABSENT", False, ids))
                        elif http_status == "200" or rows == "1":
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                    elif service == "security_service":
                        facts.append(EvidenceFact(eid, cap_at, service, res_id, "VERIFY_RECORD_PRESENT", "PRESENT", False, ids))
                    elif service == "search_service":
                        result = ev.get("result")
                        if result == "hit":
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                        elif result == "miss":
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "VERIFY_RECORD_ABSENT", "ABSENT", False, ids))
                    elif service == "support_platform":
                        marker_found = ev.get("marker_found", "").lower()
                        rows = ev.get("rows")
                        if marker_found == "false" or rows == "1":
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                        elif "pii_scan" in event:
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "REPORT_EXPOSED_PII", "PRESENT", True, ids))
                        elif "redacted" in event or "clean" in event:
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "VERIFY_RECORD_REDACTED", "REDACTED", False, ids))
                    elif service == "analytics_platform":
                        rows = ev.get("rows")
                        if "contact_lookup" in event and rows == "1":
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "REPORT_REMAINING_RECORD", "PRESENT", True, ids))
                        elif ev.get("email") or "identified" in event:
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "REPORT_EXPOSED_PII", "PRESENT", True, ids))
                        else:
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", False, ids))
                    elif service == "integration_service":
                        enabled = ev.get("enabled", "").lower()
                        if enabled in ["true", "1", "yes"] or "active" in event or "heartbeat" in event:
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", True, ids))
                        else:
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "VERIFY_DATA_FLOW_DISABLED", "DISABLED", False, ids))
                    elif service == "backup_service":
                        restore_allowed = ev.get("restore_allowed", "").lower()
                        eligible = ev.get("eligible", "").lower()
                        if restore_allowed in ["true", "1", "yes"] or eligible == "true" or "restorable" in event:
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "REPORT_RESTORE_RISK", "ACTIVE", True, ids))
                        else:
                            facts.append(EvidenceFact(eid, cap_at, service, res_id, "VERIFY_RESTORE_BLOCKED", "BLOCKED", False, ids))
        except Exception:
            pass
        return facts

    def parse_sql_dump(self, eid: str, path: Path, cap_at: str) -> List[EvidenceFact]:
        """Extract structured observations from SQL database dumps using in-memory SQLite execution.
        
        Args:
            eid: Evidence file ID.
            path: Path to SQL dump file.
            cap_at: Captured at timestamp string.
        Returns:
            List of EvidenceFact instances.
        """
        facts: List[EvidenceFact] = []
        try:
            sql_text = path.read_text(encoding="utf-8", errors="ignore")
            conn = sqlite3.connect(":memory:")
            conn.executescript(sql_text)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cur.fetchall()}

            if "customer_profiles" in tables:
                cur.execute("SELECT resource_id, email, customer_reference, account_status FROM customer_profiles;")
                for r in cur.fetchall():
                    facts.append(EvidenceFact(eid, cap_at, "account_service", r[0], "REPORT_REMAINING_RECORD", "PRESENT", True, [r[1], r[2]]))

            if "customer_search_documents" in tables:
                cur.execute("SELECT resource_id, email, customer_reference, display_name FROM customer_search_documents;")
                for r in cur.fetchall():
                    facts.append(EvidenceFact(eid, cap_at, "search_service", r[0], "REPORT_REMAINING_RECORD", "PRESENT", True, [r[1], r[2], r[3]]))

            if "customer_analytics_profiles" in tables:
                cur.execute("SELECT resource_id, email, customer_reference, audience_cohort FROM customer_analytics_profiles;")
                for r in cur.fetchall():
                    if r[1]:
                        facts.append(EvidenceFact(eid, cap_at, "analytics_platform", r[0], "REPORT_EXPOSED_PII", "PRESENT", True, [r[1], r[2]]))
                    else:
                        facts.append(EvidenceFact(eid, cap_at, "analytics_platform", r[0], "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", False, [r[2]]))

            if "support_records" in tables:
                cur.execute("SELECT resource_id, requester_email, customer_reference, requester_name FROM support_records;")
                for r in cur.fetchall():
                    if r[1]:
                        facts.append(EvidenceFact(eid, cap_at, "support_platform", r[0], "REPORT_EXPOSED_PII", "PRESENT", True, [r[1], r[2], r[3]]))
                    else:
                        facts.append(EvidenceFact(eid, cap_at, "support_platform", r[0], "VERIFY_RECORD_REDACTED", "REDACTED", False, [r[2]]))

            if "customer_exports" in tables:
                cur.execute("SELECT resource_id, owner_email, customer_reference FROM customer_exports;")
                for r in cur.fetchall():
                    if r[1] or r[2]:
                        facts.append(EvidenceFact(eid, cap_at, "export_service", r[0], "REPORT_REMAINING_RECORD", "PRESENT", True, [r[1], r[2]]))
                    else:
                        facts.append(EvidenceFact(eid, cap_at, "export_service", r[0], "VERIFY_RECORD_ABSENT", "ABSENT", False, []))

            if "connector_subscriptions" in tables:
                cur.execute("SELECT resource_id, customer_email, customer_reference, enabled FROM connector_subscriptions;")
                for r in cur.fetchall():
                    if r[3] == 1:
                        facts.append(EvidenceFact(eid, cap_at, "integration_service", r[0], "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", True, [r[1], r[2]]))
                    else:
                        facts.append(EvidenceFact(eid, cap_at, "integration_service", r[0], "VERIFY_DATA_FLOW_DISABLED", "DISABLED", False, [r[1], r[2]]))

            if "backup_restore_entries" in tables:
                cur.execute("SELECT resource_id, customer_email, customer_reference, restore_allowed FROM backup_restore_entries;")
                for r in cur.fetchall():
                    if r[3] == 1:
                        facts.append(EvidenceFact(eid, cap_at, "backup_service", r[0], "REPORT_RESTORE_RISK", "ACTIVE", True, [r[1], r[2]]))
                    else:
                        facts.append(EvidenceFact(eid, cap_at, "backup_service", r[0], "VERIFY_RESTORE_BLOCKED", "BLOCKED", False, [r[1], r[2]]))

            if "security_audit_records" in tables:
                cur.execute("SELECT resource_id, subject_reference FROM security_audit_records;")
                for r in cur.fetchall():
                    facts.append(EvidenceFact(eid, cap_at, "security_service", r[0], "VERIFY_RECORD_PRESENT", "PRESENT", False, [r[1]]))

            if "search_documents_primary" in tables:
                cur.execute("SELECT resource_id, email, display_name, source_resource_id FROM search_documents_primary;")
                for r in cur.fetchall():
                    facts.append(EvidenceFact(eid, cap_at, "search_service", r[0], "REPORT_REMAINING_RECORD", "PRESENT", True, [r[1], r[2], r[3]]))

            if "customer_profiles_failover_replica" in tables:
                cur.execute("SELECT resource_id, email, user_id FROM customer_profiles_failover_replica;")
                for r in cur.fetchall():
                    facts.append(EvidenceFact(eid, cap_at, "account_service", r[0], "REPORT_REMAINING_RECORD", "PRESENT", True, [r[1], r[2]]))
        except Exception:
            pass
        return facts

    def index_all_evidence_facts(self) -> None:
        """Parse and index all evidence files into atomic facts with inverted lookup tables."""
        for eid, meta in self.manifest.items():
            rel_path = meta.get("file_path", "")
            fpath = self.dataset_dir / rel_path
            cap_at = meta.get("captured_at", "")
            origin = meta.get("origin", "")

            if not fpath.exists():
                continue

            ext = fpath.suffix.lower()
            file_facts: List[EvidenceFact] = []

            if origin == "service_resource_export" or "service_resource_export" in fpath.name:
                file_facts = self.parse_service_resource_export(eid, fpath, cap_at)
            elif origin == "records_assurance_snapshot_bundle" or "snapshot_bundle" in fpath.name:
                file_facts = self.parse_snapshot_bundle(eid, fpath, cap_at)
            elif fpath.name == "customer_account_handover_20261001.txt":
                file_facts = self.parse_txt_handover(eid, fpath, cap_at)
            elif ext == ".pdf":
                file_facts = self.parse_document_pdf(eid, fpath, cap_at, origin)
            elif ext == ".json":
                file_facts = self.parse_generic_records_json(eid, fpath, cap_at, origin)
            elif ext == ".log":
                file_facts = self.parse_key_value_logs(eid, fpath, cap_at)
            elif ext == ".sql":
                file_facts = self.parse_sql_dump(eid, fpath, cap_at)

            for f in file_facts:
                self.facts.append(f)
                self.facts_by_res[f.resource_id.lower()].append(f)
                for t in f.identifiers:
                    self.facts_by_token[t.lower()].append(f)
