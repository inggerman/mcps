"""IMPI tools - 5 tools for industrial property (trademarks, patents)."""
from __future__ import annotations

from mcp_gob_mexico.clients import impi


def register(mcp: object) -> None:
    @mcp.tool()
    def impi_search_trademark(nombre: str, clase: str = "") -> str:
        """Busca marcas registradas o en tramite en MARCANET del IMPI (busqueda fonetica)."""
        return str(impi.get("", params={"busqueda": "fonetica", "nombre": nombre, "clase": clase}))[:5000]

    @mcp.tool()
    def impi_get_trademark_by_expediente(expediente: str) -> str:
        """Obtiene informacion de una marca por numero de expediente del IMPI."""
        return str(impi.get("", params={"busqueda": "expediente", "numero": expediente}))[:5000]

    @mcp.tool()
    def impi_get_trademark_by_registration(registro: str) -> str:
        """Obtiene informacion de una marca por numero de registro del IMPI."""
        return str(impi.get("", params={"busqueda": "registro", "numero": registro}))[:5000]

    @mcp.tool()
    def impi_search_free_patents(query: str = "") -> str:
        """Busca patentes de dominio publico (tecnologia de uso libre) en el portal del IMPI."""
        return str(impi.get("https://patenteslibres.impi.gob.mx/", params={"q": query}))[:5000]

    @mcp.tool()
    def impi_get_patent_document(expediente: str) -> str:
        """Obtiene y descarga documentos de expedientes de propiedad industrial del IMPI (ViDoc)."""
        return str(impi.get("https://vidoc.impi.gob.mx/", params={"expediente": expediente}))[:5000]
