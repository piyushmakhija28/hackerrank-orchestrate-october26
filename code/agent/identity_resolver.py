"""Disjoint-Set Union (DSU) and Multi-Attribute Entity Resolution Engine.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Evaluates transitivity-linked current and historical identity clusters in O(alpha(N)) amortized time.
"""

from collections import defaultdict
import csv
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import polars as pl

from code.core.interfaces import IEntityResolver


class DisjointSetUnion:
    """Disjoint Set Union (DSU) with Path Compression and Union by Rank.

    Attributes:
        parent: Mapping of each token to its immediate parent.
        rank: Depth ranking used to balance union tree merges.
    """

    def __init__(self) -> None:
        """Initializes empty parent and rank dictionaries."""
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}

    def find(self, item: str) -> str:
        """Find the canonical root representative with recursive path compression.

        Args:
            item: Identifier token string.
        Returns:
            Canonical root token string.
        """
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0
            return item
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, item_a: str, item_b: str) -> None:
        """Merge the sets containing item_a and item_b using rank balancing.

        Args:
            item_a: First identifier token string.
            item_b: Second identifier token string.
        """
        root_a = self.find(item_a)
        root_b = self.find(item_b)
        if root_a == root_b:
            return

        if self.rank[root_a] < self.rank[root_b]:
            self.parent[root_a] = root_b
        elif self.rank[root_a] > self.rank[root_b]:
            self.parent[root_b] = root_a
        else:
            self.parent[root_b] = root_a
            self.rank[root_a] += 1


class IdentityResolver(IEntityResolver):
    """Resolves multi-attribute customer entity clusters and historical aliases in O(alpha(N)) time.

    Attributes:
        dsu: Underlying DisjointSetUnion data structure.
        token_occurrences: Global frequency counts of identifier tokens for hub pruning.
        max_hub_frequency: Threshold above which a generic token is pruned from linking.
        email_to_user_id: Direct mapping from any email (current or historical) to user_id.
        user_id_to_record: Mapping from user_id to identity record dict.
        _all_tokens: Universe of all observed identity tokens.
        _cluster_cache: Inverted equivalence orbit cache mapping canonical roots to token sets.
        _cache_dirty: Flag indicating whether merges require rebuilding the cluster index.
    """

    def __init__(self, max_hub_frequency: int = 500) -> None:
        """Initializes identity resolver with DSU, lookup tables, and empty orbit cache.

        Args:
            max_hub_frequency: Upper limit frequency for generic hub token pruning.
        """
        self.dsu: DisjointSetUnion = DisjointSetUnion()
        self.token_occurrences: Dict[str, int] = defaultdict(int)
        self.max_hub_frequency: int = max_hub_frequency
        self._all_tokens: Set[str] = set()
        self.email_to_user_id: Dict[str, str] = {}
        self.user_id_to_record: Dict[str, Dict[str, str]] = {}
        self._cluster_cache: Dict[str, Set[str]] = {}
        self._cache_dirty: bool = True

    def _rebuild_cluster_index(self) -> None:
        """Rebuilds the inverted root-to-cluster cache across all registered tokens.

        Complexity: O(N * alpha(N)) where N is total tokens in the universe.
        """
        if not self._cache_dirty and self._cluster_cache:
            return

        new_cache: Dict[str, Set[str]] = defaultdict(set)
        for token in self._all_tokens:
            root = self.dsu.find(token)
            new_cache[root].add(token)

        self._cluster_cache = dict(new_cache)
        self._cache_dirty = False

    def load_identities_and_audit_log(
        self, identities_csv: Union[Path, str], audit_log_csv: Union[Path, str]
    ) -> None:
        """Load customer identities and historical audit logs, establishing equivalence links.

        Args:
            identities_csv: Path or str path to user_identities.csv.
            audit_log_csv: Path or str path to user_audit_log.csv.
        """
        identities_path = Path(identities_csv)
        audit_log_path = Path(audit_log_csv)
        if identities_path.exists():
            with open(identities_path, mode="r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    uid = row.get("user_id", "").strip()
                    email = row.get("email", "").strip().lower()
                    phone = row.get("phone", "").strip()
                    name = row.get("name", "").strip()
                    ehash = row.get("email_hash", "").strip()

                    if uid:
                        self.user_id_to_record[uid] = row
                        self._all_tokens.add(uid)
                    if email and uid:
                        self.email_to_user_id[email] = uid
                        self.link_identifiers(email, uid)
                    if phone and uid:
                        self.link_identifiers(phone, uid)
                    if ehash and uid:
                        self.link_identifiers(ehash, uid)

        if audit_log_path.exists():
            with open(audit_log_path, mode="r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    field = row.get("field_name", "").strip()
                    uid = row.get("user_id", "").strip()
                    old_val = row.get("old_value", "").strip()
                    new_val = row.get("new_value", "").strip()

                    if field == "email":
                        if old_val and uid:
                            self.email_to_user_id[old_val.lower()] = uid
                            self.link_identifiers(old_val.lower(), uid)
                        if new_val and uid:
                            self.email_to_user_id[new_val.lower()] = uid
                            self.link_identifiers(new_val.lower(), uid)
                    elif field in ["phone", "email_hash"]:
                        if old_val and uid:
                            self.link_identifiers(old_val, uid)
                        if new_val and uid:
                            self.link_identifiers(new_val, uid)

        self._cache_dirty = True

    def ingest_records(self, dataframe: pl.LazyFrame, id_columns: List[str]) -> None:
        """Ingest tabular records and establish co-occurrence equivalence edges.

        Args:
            dataframe: Lazy Polars frame of records.
            id_columns: Column names containing identifier tokens.
        """
        available_cols = [col for col in id_columns if col in dataframe.collect_schema().names()]
        if not available_cols:
            return

        df_collected = dataframe.select(available_cols).collect()
        for row in df_collected.iter_rows(named=True):
            tokens: List[str] = []
            for col in available_cols:
                val = row[col]
                if val is not None:
                    str_val = str(val).strip().lower()
                    if str_val and str_val not in ["none", "null", ""]:
                        tokens.append(str_val)
                        self.token_occurrences[str_val] += 1
                        self._all_tokens.add(str_val)

            valid_tokens = [t for t in tokens if self.token_occurrences[t] <= self.max_hub_frequency]
            if len(valid_tokens) > 1:
                first = valid_tokens[0]
                for next_token in valid_tokens[1:]:
                    self.dsu.union(first, next_token)

        self._cache_dirty = True

    def link_identifiers(self, token_a: str, token_b: str) -> None:
        """Directly establish an equivalence edge between two tokens.

        Args:
            token_a: First identifier token string.
            token_b: Second identifier token string.
        """
        norm_a = token_a.strip().lower()
        norm_b = token_b.strip().lower()
        if not norm_a or not norm_b:
            return
        self._all_tokens.add(norm_a)
        self._all_tokens.add(norm_b)
        self.dsu.union(norm_a, norm_b)
        self._cache_dirty = True

    def resolve_cluster(self, seed_identifier: str) -> Set[str]:
        """Retrieve all transitivity-linked current and historical identifiers in O(alpha(N)) amortized time.

        Args:
            seed_identifier: Starting identifier token (e.g. email, user ID).
        Returns:
            Complete set of linked identifier tokens.
        """
        norm_seed = seed_identifier.strip().lower()
        self._rebuild_cluster_index()
        seed_root = self.dsu.find(norm_seed)
        cached = self._cluster_cache.get(seed_root)
        if cached:
            return set(cached) | {norm_seed}
        return {norm_seed}

    def get_user_id(self, email: str) -> Optional[str]:
        """Retrieve canonical user_id for a given email address.

        Args:
            email: Email address string.
        Returns:
            Matching user_id or None.
        """
        return self.email_to_user_id.get(email.strip().lower())
