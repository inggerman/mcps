"""Whitelist de fuentes confiables para búsqueda web validada.

Cada dominio tiene un trust_score (0-1) que indica qué tan confiable es.
Solo los resultados con trust_score >= settings.trust_threshold se incluyen.
"""

from __future__ import annotations

# Trust scores por dominio (1.0 = máxima confianza)
TRUSTED_DOMAINS: dict[str, float] = {
    # Official documentation
    "docs.python.org": 1.0,
    "developer.mozilla.org": 1.0,
    "fastapi.tiangolo.com": 1.0,
    "kubernetes.io": 1.0,
    "docs.docker.com": 1.0,
    "docs.ansible.com": 1.0,
    "registry.terraform.io": 1.0,
    "developer.hashicorp.com": 1.0,
    "docs.github.com": 1.0,
    "gitlab.com/docs": 1.0,
    "docs.gitlab.com": 1.0,
    "platform.openai.com/docs": 1.0,
    "docs.anthropic.com": 1.0,
    "langchain-ai.github.io": 1.0,
    "python.langchain.com": 1.0,
    "docs.pydantic.dev": 1.0,
    "docs.celeryq.dev": 1.0,
    "redis.io/docs": 1.0,
    "www.rabbitmq.com/docs": 1.0,
    "qdrant.tech/documentation": 1.0,
    "httpx.com": 1.0,

    # Frameworks & libraries
    "flask.palletsprojects.com": 1.0,
    "docs.djangoproject.com": 1.0,
    "spring.io/projects": 1.0,
    "docs.spring.io": 1.0,
    "expressjs.com": 1.0,
    "react.dev": 1.0,
    "vuejs.org": 1.0,
    "angular.io": 1.0,
    "svelte.dev": 1.0,
    "nextjs.org/docs": 1.0,
    "nuxt.com/docs": 1.0,
    "astro.build": 1.0,

    # Cloud & infra
    "docs.aws.amazon.com": 1.0,
    "cloud.google.com/docs": 1.0,
    "learn.microsoft.com": 1.0,
    "docs.microsoft.com": 1.0,
    "argo-cd.readthedocs.io": 1.0,
    "www.openpolicyagent.org": 1.0,
    "kyverno.io": 1.0,
    "goharbor.io/docs": 1.0,
    "docs.longhorn.io": 1.0,
    "konghq.com/docs": 1.0,
    "docs.n8n.io": 1.0,

    # Code hosting & community
    "github.com": 0.9,
    "stackoverflow.com": 0.8,
    "docs.stackoverflow.com": 0.8,
    "dev.to": 0.7,
    "medium.com": 0.6,
    "blog.python.org": 0.9,

    # Security
    "owasp.org": 1.0,
    "cheatsheetseries.owasp.org": 1.0,
    "nvd.nist.gov": 1.0,
    "cve.mitre.org": 1.0,
    "security.snyk.io": 0.9,
    "sonarcloud.io": 0.9,

    # Databases
    "www.postgresql.org/docs": 1.0,
    "dev.mysql.com/doc": 1.0,
    "docs.mongodb.com": 1.0,
    "redis.io": 1.0,

    # Package registries
    "pypi.org": 0.9,
    "docs.npmjs.com": 0.9,
    "registry.npmjs.org": 0.8,
    "mvnrepository.com": 0.7,
    "search.maven.org": 0.8,

    # Standards
    "datatracker.ietf.org": 1.0,
    "www.rfc-editor.org": 1.0,
    "json-schema.org": 1.0,
    "swagger.io": 1.0,
    "www.openapis.org": 1.0,
}


def get_trust_score(url: str) -> float:
    """Calcula el trust score de una URL basado en su dominio.

    Args:
        url: URL a evaluar.

    Returns:
        Trust score entre 0.0 y 1.0.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.hostname or ""

    # Exact match
    if domain in TRUSTED_DOMAINS:
        return TRUSTED_DOMAINS[domain]

    # Subdomain match (e.g., docs.python.org matches python.org)
    parts = domain.split(".")
    for i in range(len(parts)):
        partial = ".".join(parts[i:])
        if partial in TRUSTED_DOMAINS:
            return TRUSTED_DOMAINS[partial]

    # Known TLDs but not whitelisted
    if domain.endswith((".org", ".dev", ".io")):
        return 0.4

    # Unknown domain
    return 0.1


def is_trusted(url: str, threshold: float = 0.5) -> bool:
    """Verifica si una URL es confiable según el threshold."""
    return get_trust_score(url) >= threshold


def list_whitelist() -> dict[str, float]:
    """Retorna la whitelist completa con trust scores."""
    return TRUSTED_DOMAINS.copy()
