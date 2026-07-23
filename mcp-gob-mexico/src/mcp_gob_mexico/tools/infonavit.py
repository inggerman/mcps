"""INFONAVIT tools - 2 tools for housing credit info."""
from __future__ import annotations

from mcp_gob_mexico.clients import BaseClient


def register(mcp: object) -> None:
    client = BaseClient("https://apiweb.infonavit.org.mx")

    @mcp.tool()
    def infonavit_get_credit_info(nss: str) -> str:
        """Consulta informacion crediticia de un derechohabiente del INFONAVIT por NSS."""
        return str(client.get("ApiWeb/inicio.do", params={"nss": nss}))[:5000]

    @mcp.tool()
    def infonavit_get_credit_status(rfc: str) -> str:
        """Consulta el estatus de un credito INFONAVIT por RFC del derechohabiente."""
        return str(client.get("ApiWeb/inicio.do", params={"rfc": rfc}))[:5000]
