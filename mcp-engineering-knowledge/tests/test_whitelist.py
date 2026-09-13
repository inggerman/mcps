"""Tests for the whitelist module."""

from mcp_engineering_knowledge.whitelist import (
    get_trust_score,
    is_trusted,
    list_by_category,
    list_whitelist,
)


def test_official_docs_trust_1():
    """Official documentation domains have trust score 1.0."""
    assert get_trust_score("https://docs.python.org/3/") == 1.0
    assert get_trust_score("https://kubernetes.io/docs/") == 1.0
    assert get_trust_score("https://fastapi.tiangolo.com/") == 1.0


def test_rfc_domains_trust_1():
    """RFC and standards domains have trust score 1.0."""
    assert get_trust_score("https://datatracker.ietf.org/") == 1.0
    assert get_trust_score("https://www.rfc-editor.org/") == 1.0
    assert get_trust_score("https://openid.net/") == 1.0


def test_industry_leaders_high_trust():
    """Industry leader engineering blogs have trust >= 0.8."""
    assert get_trust_score("https://martinfowler.com/") == 1.0
    assert get_trust_score("https://engineering.fb.com/") == 0.9
    assert get_trust_score("https://netflixtechblog.com/") == 0.9


def test_security_advisories_trust_1():
    """Security advisory domains have trust score 1.0."""
    assert get_trust_score("https://nvd.nist.gov/") == 1.0
    assert get_trust_score("https://cve.mitre.org/") == 1.0


def test_unknown_domain_low_trust():
    """Unknown domains have low trust score."""
    assert get_trust_score("https://random-blog.example.com/") < 0.5


def test_is_trusted_threshold():
    """is_trusted respects the threshold."""
    assert is_trusted("https://docs.python.org/", threshold=0.8) is True
    assert is_trusted("https://random-blog.example.com/", threshold=0.8) is False


def test_list_whitelist_nonempty():
    """list_whitelist returns a non-empty dict."""
    wl = list_whitelist()
    assert len(wl) > 50
    assert "docs.python.org" in wl


def test_list_by_category():
    """list_by_category returns 4 categories."""
    cats = list_by_category()
    assert "official_docs" in cats
    assert "rfcs_standards" in cats
    assert "industry_leaders" in cats
    assert "security_advisories" in cats
    assert len(cats["official_docs"]) > 10
