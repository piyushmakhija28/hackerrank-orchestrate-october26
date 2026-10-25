"""Lineage and System Activity Tracker.

Identifies active sync, CDC, ETL, and restore paths capable of resurrecting data.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Coordinates chronological binary window indexing and inverted token lookups.
"""

import bisect
from collections import defaultdict
import csv
from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from code.core.models import ProcessType, SyncProcess


class LineageTracer:
    """Tracks system activity streams and detects zombie replication or restore risks in O(log A) time.

    Attributes:
        activities: List of raw activity dictionaries from system_activity.csv.
        resource_to_activities: Inverted index mapping lowercase resource_id to activity events.
        activities_by_token: Inverted index mapping lowercase token strings to activity events.
        worker_activities_sorted: Chronologically sorted tuple list of (event_dt, activity) for deletion_worker.
        worker_timestamps: Monotonically increasing list of worker datetimes for binary search.
    """

    def __init__(self, activity_csv: Optional[Union[Path, str]] = None) -> None:
        """Initializes lineage tracer with empty indices and loads activity records if provided.

        Args:
            activity_csv: Optional path or string path to system_activity.csv.
        """
        self.activities: List[Dict[str, str]] = []
        self.resource_to_activities: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        self.activities_by_token: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        self.worker_activities_sorted: List[Tuple[datetime, Dict[str, str]]] = []
        self.worker_timestamps: List[datetime] = []

        if activity_csv:
            path_obj = Path(activity_csv)
            if path_obj.exists():
                self.load_activities(path_obj)

    def load_activities(self, activity_csv: Union[Path, str]) -> None:
        """Load, pre-parse timestamps, and index all records from system_activity.csv.

        Args:
            activity_csv: Path or string path to system_activity.csv.
        """
        path_obj = Path(activity_csv)
        self.activities = []
        self.resource_to_activities = defaultdict(list)
        self.activities_by_token = defaultdict(list)
        self.worker_activities_sorted = []
        self.worker_timestamps = []

        with open(path_obj, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.activities.append(row)
                res_id = (row.get("resource_id") or "").strip().lower()
                details_lower = (row.get("details") or "").lower()

                tokens_in_row = set(re.findall(r"[\w.+-]+@[\w.-]+|\w+", details_lower))
                if res_id:
                    self.resource_to_activities[res_id].append(row)
                    tokens_in_row.add(res_id)

                for tok in tokens_in_row:
                    self.activities_by_token[tok].append(row)

                if row.get("source_system") == "deletion_worker":
                    ev_time = (row.get("event_time") or "").strip()
                    if ev_time:
                        try:
                            dt = datetime.fromisoformat(ev_time.replace("Z", "+00:00"))
                            self.worker_activities_sorted.append((dt, row))
                        except Exception:
                            pass

        self.worker_activities_sorted.sort(key=lambda x: x[0])
        self.worker_timestamps = [x[0] for x in self.worker_activities_sorted]

    def query_token_activities(self, cluster: Set[str]) -> List[Dict[str, str]]:
        """Retrieves activities associated with any token in the subject's identifier cluster in O(|cluster|) time.

        Args:
            cluster: Set of user identifier tokens.
        Returns:
            List of matching activity dictionaries.
        """
        if not cluster:
            return []

        matched: List[Dict[str, str]] = []
        seen_act_ids: Set[int] = set()

        for token in cluster:
            norm = str(token).lower().strip()
            if not norm:
                continue
            for a in self.activities_by_token.get(norm, []):
                aid = id(a)
                if aid not in seen_act_ids:
                    seen_act_ids.add(aid)
                    matched.append(a)

        return matched

    def query_window_worker_activities(
        self,
        rep_dt: Optional[datetime],
        window_seconds: int = 7200,
        lead_seconds: int = 1800,
    ) -> List[Dict[str, str]]:
        """Retrieves deletion_worker batch activities within [-lead_seconds, +window_seconds] via binary search.

        Args:
            rep_dt: Base report datetime.
            window_seconds: Trailing window boundary in seconds.
            lead_seconds: Leading window boundary in seconds.
        Returns:
            List of matching activity dictionaries.
        """
        if not rep_dt or not self.worker_timestamps:
            return []

        t_min = rep_dt - timedelta(seconds=window_seconds)
        t_max = rep_dt + timedelta(seconds=lead_seconds)

        i_left = bisect.bisect_left(self.worker_timestamps, t_min)
        i_right = bisect.bisect_right(self.worker_timestamps, t_max)

        return [self.worker_activities_sorted[i][1] for i in range(i_left, i_right)]

    def get_case_activities(
        self,
        reported_at: str,
        requested_at: str,
        user_cluster: Set[str],
        window_seconds: int = 7200,
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
        token_acts = self.query_token_activities(user_cluster)
        rep_dt: Optional[datetime] = None
        if reported_at:
            try:
                rep_dt = datetime.fromisoformat(reported_at.replace("Z", "+00:00"))
            except Exception:
                rep_dt = None

        batch_acts = self.query_window_worker_activities(rep_dt, window_seconds=window_seconds, lead_seconds=300)
        seen_ids = set(id(a) for a in token_acts)
        for b in batch_acts:
            if id(b) not in seen_ids:
                seen_ids.add(id(b))
                token_acts.append(b)

        return token_acts

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
                if "remains enabled" in details or (
                    event_type == "CHECK_DATA_FLOW" and a.get("reported_result") == "SUCCESS"
                ):
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
                if "can still be restored" in details or (
                    event_type == "CHECK_RESTORE_ACCESS" and a.get("reported_result") == "SUCCESS"
                ):
                    restore_risks.add(res)
                elif event_type == "BLOCK_RESTORE" and a.get("reported_result") == "SUCCESS":
                    restore_risks.discard(res)
        return sorted(list(restore_risks))
