"""RPC/SIGER tools - 3 tools for commercial registry."""
from __future__ import annotations

from mcp_gob_mexico.clients import rpc

_RPC_PATH = "xhtml/consulta/consultaPublica/detalleConsultaPublica.xhtml"


def register(mcp: object) -> None:
    @mcp.tool()
    def rpc_search_company(nombre: str) -> str:
        """Busca una empresa en el Registro Publico de Comercio (SIGER 2.0) por nombre o razon social."""
        return str(rpc.get(_RPC_PATH, params={"nombre": nombre}))[:5000]

    @mcp.tool()
    def rpc_get_company_by_folio(folio_mercantil: str) -> str:
        """Obtiene informacion de una sociedad por su folio mercantil electronico del RPC."""
        return str(rpc.get(_RPC_PATH, params={"folio": folio_mercantil}))[:5000]

    @mcp.tool()
    def rpc_get_registry_offices(estado: str = "") -> str:
        """Obtiene el listado de oficinas registrales del Registro Publico de Comercio."""
        return str(rpc.get(_RPC_PATH, params={"estado": estado}))[:5000]
