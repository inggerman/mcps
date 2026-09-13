"""Trusted sources whitelist for engineering knowledge curation.

Four categories:
1. Official documentation (trust 1.0)
2. RFCs and standards (trust 1.0)
3. Industry leaders engineering blogs (trust 0.8-0.9)
4. Security advisories (trust 1.0)
"""

from __future__ import annotations

TRUSTED_DOMAINS: dict[str, float] = {
    # --- Official documentation (1.0) ---
    "docs.python.org": 1.0,
    "developer.mozilla.org": 1.0,
    "fastapi.tiangolo.com": 1.0,
    "kubernetes.io": 1.0,
    "docs.docker.com": 1.0,
    "docs.ansible.com": 1.0,
    "registry.terraform.io": 1.0,
    "developer.hashicorp.com": 1.0,
    "docs.github.com": 1.0,
    "docs.gitlab.com": 1.0,
    "platform.openai.com": 1.0,
    "docs.anthropic.com": 1.0,
    "docs.pydantic.dev": 1.0,
    "redis.io": 1.0,
    "www.rabbitmq.com": 1.0,
    "qdrant.tech": 1.0,
    "flask.palletsprojects.com": 1.0,
    "docs.djangoproject.com": 1.0,
    "spring.io": 1.0,
    "docs.spring.io": 1.0,
    "expressjs.com": 1.0,
    "react.dev": 1.0,
    "vuejs.org": 1.0,
    "angular.io": 1.0,
    "nextjs.org": 1.0,
    "go.dev": 1.0,
    "doc.rust-lang.org": 1.0,
    "kotlinlang.org": 1.0,
    "docs.oracle.com": 1.0,
    "www.postgresql.org": 1.0,
    "dev.mysql.com": 1.0,
    "www.mongodb.com": 1.0,
    "docs.aws.amazon.com": 1.0,
    "cloud.google.com": 1.0,
    "learn.microsoft.com": 1.0,
    "docs.microsoft.com": 1.0,
    "argo-cd.readthedocs.io": 1.0,
    "goharbor.io": 1.0,
    "docs.longhorn.io": 1.0,
    "konghq.com": 1.0,
    "docs.n8n.io": 1.0,
    "www.openpolicyagent.org": 1.0,
    "kyverno.io": 1.0,
    "prometheus.io": 1.0,
    "grafana.com": 1.0,
    "opentelemetry.io": 1.0,
    "nginx.org": 1.0,
    "www.envoyproxy.io": 1.0,
    "traefik.io": 1.0,
    "backstage.io": 1.0,

    # --- RFCs and standards (1.0) ---
    "datatracker.ietf.org": 1.0,
    "www.rfc-editor.org": 1.0,
    "openid.net": 1.0,
    "www.w3.org": 1.0,
    "www.iso.org": 1.0,
    "json-schema.org": 1.0,
    "swagger.io": 1.0,
    "www.openapis.org": 1.0,
    "www.owasp.org": 1.0,
    "cheatsheetseries.owasp.org": 1.0,
    "csrc.nist.gov": 1.0,
    "www.cnss.gov": 1.0,

    # --- Industry leaders engineering blogs (0.8-0.9) ---
    "engineering.fb.com": 0.9,
    "engineering.atspotify.com": 0.9,
    "netflixtechblog.com": 0.9,
    "aws.amazon.com": 0.9,
    "aws.amazon.com/blogs": 0.9,
    "cloud.google.com/blog": 0.9,
    "azure.microsoft.com": 0.9,
    "stripe.com": 0.9,
    "stripe.com/blog": 0.9,
    "www.uber.com/blog": 0.9,
    "eng.uber.com": 0.9,
    "engineering.linkedin.com": 0.9,
    "blog.cloudflare.com": 0.9,
    "github.blog": 0.9,
    "blog.gitlab.com": 0.9,
    "martinfowler.com": 1.0,
    "refactoring.com": 0.9,
    "www.thoughtworks.com": 0.9,
    "www.thoughtworks.com/insights": 0.9,
    "engineering.mercadolibre.com": 0.9,
    "medium.com/mercadolibre": 0.8,
    "docs.mercadolibre.com": 0.9,
    "dev.to/github": 0.8,
    "blog.python.org": 0.9,

    # --- Security advisories (1.0) ---
    "nvd.nist.gov": 1.0,
    "cve.mitre.org": 1.0,
    "github.com/advisories": 1.0,
    "security.snyk.io": 0.9,
    "sonarcloud.io": 0.9,
    "snyk.io": 0.9,
    "www.cisa.gov": 1.0,
    "www.cnbv.gob.mx": 1.0,

    # --- Package registries (0.8-0.9) ---
    "pypi.org": 0.9,
    "docs.npmjs.com": 0.9,
    "registry.npmjs.org": 0.8,
    "search.maven.org": 0.8,
    "pkg.go.dev": 0.9,
    "crates.io": 0.8,

    # --- Community (lower trust) ---
    "stackoverflow.com": 0.7,
    "dev.to": 0.7,
    "medium.com": 0.6,
}


def get_trust_score(url: str) -> float:
    """Calculate trust score for a URL based on its domain."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.hostname or ""
    path = parsed.path or ""

    # Exact domain match
    if domain in TRUSTED_DOMAINS:
        return TRUSTED_DOMAINS[domain]

    # Domain + path match (e.g., aws.amazon.com/blogs)
    domain_path = f"{domain}{path}"
    for key, score in TRUSTED_DOMAINS.items():
        if "/" in key and domain_path.startswith(key):
            return score

    # Subdomain match
    parts = domain.split(".")
    for i in range(len(parts)):
        partial = ".".join(parts[i:])
        if partial in TRUSTED_DOMAINS:
            return TRUSTED_DOMAINS[partial]

    # Known TLDs but not whitelisted
    if domain.endswith((".org", ".dev", ".io")):
        return 0.4

    return 0.1


def is_trusted(url: str, threshold: float = 0.8) -> bool:
    """Check if a URL is trusted based on threshold."""
    return get_trust_score(url) >= threshold


def list_whitelist() -> dict[str, float]:
    """Return the complete whitelist with trust scores."""
    return TRUSTED_DOMAINS.copy()


def list_by_category() -> dict[str, list[dict[str, float]]]:
    """Return whitelist organized by category."""
    return {
        "official_docs": [
            {"domain": d, "trust": s}
            for d, s in TRUSTED_DOMAINS.items()
            if s == 1.0 and not _is_rfc(d) and not _is_security(d) and not _is_blog(d)
        ],
        "rfcs_standards": [
            {"domain": d, "trust": s}
            for d, s in TRUSTED_DOMAINS.items()
            if _is_rfc(d)
        ],
        "industry_leaders": [
            {"domain": d, "trust": s}
            for d, s in TRUSTED_DOMAINS.items()
            if _is_blog(d)
        ],
        "security_advisories": [
            {"domain": d, "trust": s}
            for d, s in TRUSTED_DOMAINS.items()
            if _is_security(d)
        ],
    }


def _is_rfc(domain: str) -> bool:
    return domain in {
        "datatracker.ietf.org",
        "www.rfc-editor.org",
        "openid.net",
        "www.w3.org",
        "www.iso.org",
        "json-schema.org",
        "swagger.io",
        "www.openapis.org",
        "www.owasp.org",
        "cheatsheetseries.owasp.org",
        "csrc.nist.gov",
        "www.cnss.gov",
    }


def _is_security(domain: str) -> bool:
    return domain in {
        "nvd.nist.gov",
        "cve.mitre.org",
        "github.com/advisories",
        "security.snyk.io",
        "sonarcloud.io",
        "snyk.io",
        "www.cisa.gov",
        "www.cnbv.gob.mx",
    }


def _is_blog(domain: str) -> bool:
    return domain in {
        "engineering.fb.com",
        "engineering.atspotify.com",
        "netflixtechblog.com",
        "aws.amazon.com",
        "aws.amazon.com/blogs",
        "cloud.google.com/blog",
        "azure.microsoft.com",
        "stripe.com",
        "stripe.com/blog",
        "www.uber.com/blog",
        "eng.uber.com",
        "engineering.linkedin.com",
        "blog.cloudflare.com",
        "github.blog",
        "blog.gitlab.com",
        "martinfowler.com",
        "refactoring.com",
        "www.thoughtworks.com",
        "www.thoughtworks.com/insights",
        "engineering.mercadolibre.com",
        "medium.com/mercadolibre",
        "docs.mercadolibre.com",
        "dev.to/github",
        "blog.python.org",
    }
