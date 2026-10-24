"""
Lineage and System Activity Tracker.
Identifies active sync, CDC, ETL, and restore paths capable of resurrecting data.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Set, Dict, Any, Optional
from code.core.models import SyncProcess, ProcessType

class LineageTracer:
    """Tracks system activity streams and detects zombie replication or restore risks.
    
    Attributes:
        activities: List of raw activity dictionaries from system_activity.csv.
        resource_to_activities: Inverted index mapping resource_id to activity events.
    """
    def __init__(self, activity_csv: Optional[Path] = None) -> None:
        self.activities: List[Dict[str, str]] = []
        self.resource_to_activities: Dict[str, List[Dict[str, str]]] = {}
        if activity_csv and activity_csv.exists():
            self.load_activities(activity_csv)

    def load_activities(self, activity_csv: Path) -> None:
        """Load and index all records from system_activity.csv.
        
        Args:
            activity_csv: Path to system_activity.csv.
        """
        self.activities = []
        self.resource_to_activities = {}
        with open(activity_csv, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.activities.append(row)
                res_id = row.get("resource_id", "")
                if res_id:
                    if res_id not in self.resource_to_activities:
                        self.resource_to_activities[res_id] = []
                    self.resource_to_activities[res_id].append(row)

    def get_case_activities(
        self,
        reported_at: str,
        requested_at: str,
        user_cluster: Set[str],
        window_seconds: int = 7200
    ) -> List[Dict[str, str]]:
        """Retrieve system activity records associated with a specific deletion request case.
        
        Args:
            reported_at: ISO-8601 reported timestamp.
            requested_at: ISO-8601 requested timestamp.
            user_cluster: Set of user identifier tokens.
            window_seconds: Search window in seconds around reported_at (default 2 hours).
        Returns:
            List of correlated activity dictionaries.
        """
        matched_acts: List[Dict[str, str]] = []
        lower_cluster = {str(c).lower().strip() for c in user_cluster if c}
        rep_dt: Optional[datetime] = None

        if reported_at:
            try:
                rep_dt = datetime.fromisoformat(reported_at.replace("Z", "+00:00"))
            except Exception:
                rep_dt = None

        for act in self.activities:
            event_time = act.get("event_time", "")
            if not event_time:
                continue

            act_dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
            details = act.get("details", "").lower()
            res_id = act.get("resource_id", "").lower()
            source = act.get("source_system", "")

            has_direct_mention = any(c in details for c in lower_cluster) or (res_id in lower_cluster)
            is_in_time_window = False

            if rep_dt and source == "deletion_worker":
                diff = abs((act_dt - rep_dt).total_seconds())
                if diff <= window_seconds:
                    is_in_time_window = True

            if has_direct_mention or is_in_time_window:
                matched_acts.append(act)

        return matched_acts

    def detect_active_data_flows(self, activities: List[Dict[str, str]]) -> List[str]:
        """Detect connectors or dataflows that remain enabled in the activity trace.
        
        Args:
            activities: List of case activities.
        Returns:
            List of active connector resource IDs.
        """
        active_flows: Set[str] = set()
        for a in activities:
            if a.get("target_system") == "integration_service":
                res = a.get("resource_id", "")
                details = a.get("details", "").lower()
                event_type = a.get("event_type", "")
                if "remains enabled" in details or (event_type == "CHECK_DATA_FLOW" and a.get("reported_result") == "SUCCESS"):
                    active_flows.add(res)
                elif event_type == "DISABLE_DATA_FLOW" and a.get("reported_result") == "SUCCESS":
                    active_flows.discard(res)
        return sorted(list(active_flows))

    def detect_restore_risks(self, activities: List[Dict[str, str]]) -> List[str]:
        """Detect backup archives that remain restorable.
        
        Args:
            activities: List of case activities.
        Returns:
            List of restorable backup resource IDs.
        """
        restore_risks: Set[str] = set()
        for a in activities:
            if a.get("target_system") == "backup_service":
                res = a.get("resource_id", "")
                details = a.get("details", "").lower()
                event_type = a.get("event_type", "")
                if "can still be restored" in details or (event_type == "CHECK_RESTORE_ACCESS" and a.get("reported_result") == "SUCCESS"):
                    restore_risks.add(res)
                elif event_type == "BLOCK_RESTORE" and a.get("reported_result") == "SUCCESS":
                    restore_risks.discard(res)
        return sorted(list(restore_risks))
