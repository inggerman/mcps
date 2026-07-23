"""CDMX tools - 6 tools for Mexico City open data."""
from __future__ import annotations

from mcp_gob_mexico.clients import cdmx


def register(mcp: object) -> None:
    @mcp.tool()
    def cdmx_search_datasets(query: str, rows: int = 10) -> str:
        """Busca datasets en el Portal de Datos Abiertos de la CDMX."""
        return str(cdmx.get("package_search", params={"q": query, "rows": rows}))

    @mcp.tool()
    def cdmx_get_dataset(dataset_id: str) -> str:
        """Obtiene los detalles de un dataset especifico de la CDMX."""
        return str(cdmx.get("package_show", params={"id": dataset_id}))

    @mcp.tool()
    def cdmx_get_security_report(entidad: str = "", anio: str = "2026") -> str:
        """Obtiene el reporte mensual de seguridad de la CDMX."""
        return str(cdmx.get("package_search", params={"q": f"seguridad {anio}"}))

    @mcp.tool()
    def cdmx_get_civil_registry(tipo: str = "defuncion", anio: str = "2026") -> str:
        """Obtiene actas del Registro Civil de la CDMX (defuncion, nacimiento, matrimonio)."""
        return str(cdmx.get("package_search", params={"q": f"registro civil {tipo} {anio}"}))

    @mcp.tool()
    def cdmx_get_budget(anio: str = "2026") -> str:
        """Obtiene datos de transparencia presupuestaria de la CDMX."""
        return str(cdmx.get("package_search", params={"q": f"presupuesto {anio}"}))

    @mcp.tool()
    def cdmx_get_0311_requests(fecha: str = "", tipo: str = "") -> str:
        """Obtiene solicitudes del sistema 0311 de la CDMX."""
        query = "0311 solicitudes"
        if fecha:
            query += f" {fecha}"
        if tipo:
            query += f" {tipo}"
        return str(cdmx.get("package_search", params={"q": query}))
