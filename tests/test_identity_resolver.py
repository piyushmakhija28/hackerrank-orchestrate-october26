"""
Unit tests for Disjoint-Set Union (DSU) and Identity Resolver.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import pytest
from code.agent.identity_resolver import DisjointSetUnion, IdentityResolver

def test_dsu_basic_union_find() -> None:
    """Verify DSU reflexivity, symmetry, and transitive closure."""
    dsu = DisjointSetUnion()
    dsu.union("a", "b")
    dsu.union("b", "c")
    assert dsu.find("a") == dsu.find("c")
    assert dsu.find("a") != dsu.find("d")

def test_identity_resolver_transitive_linkage() -> None:
    """Verify that indirect links merge into a single identity cluster."""
    resolver = IdentityResolver(max_hub_frequency=10)
    resolver.link_identifiers("user@shop.com", "alt_email@work.com")
    resolver.link_identifiers("alt_email@work.com", "+1-555-0199")
    resolver.link_identifiers("+1-555-0199", "DEV-ID-99")

    cluster = resolver.resolve_cluster("user@shop.com")
    assert "user@shop.com" in cluster
    assert "alt_email@work.com" in cluster
    assert "+1-555-0199" in cluster
    assert "dev-id-99" in cluster

def test_identity_resolver_unrelated_clusters() -> None:
    """Verify that unlinked identifiers remain partitioned into disjoint sets."""
    resolver = IdentityResolver()
    resolver.link_identifiers("alice@shop.com", "dev-alice")
    resolver.link_identifiers("bob@shop.com", "dev-bob")

    alice_cluster = resolver.resolve_cluster("alice@shop.com")
    bob_cluster = resolver.resolve_cluster("bob@shop.com")

    assert "alice@shop.com" in alice_cluster
    assert "dev-alice" in alice_cluster
    assert "bob@shop.com" not in alice_cluster
    assert "alice@shop.com" not in bob_cluster
