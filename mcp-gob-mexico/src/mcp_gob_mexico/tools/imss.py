"""IMSS tools - 5 tools for Mexican Social Security Institute data."""
from __future__ import annotations

from mcp_gob_mexico.clients import imss

_DATASTORE = "datastore/search.json"


def register(mcp: object) -> None:
    @mcp.tool()
    def imss_search_datasets(query: str, limit: int = 10) -> str:
        """Busca datasets disponibles en el portal de Datos Abiertos del IMSS."""
        return str(imss.get(_DATASTORE, params={"q": query, "limit": limit}))

    @mcp.tool()
    def imss_get_medical_units(delegacion: str = "") -> str:
        """Obtiene el listado de unidades medicas en servicio del IMSS."""
        resource_id = "813b3033-294f-49cc-b242-96932120869e"
        params: dict = {"resource_id": resource_id, "limit": 100}
        if delegacion:
            params["filters"] = f'{{"delegacion":"{delegacion}"}}'
        return str(imss.get(_DATASTORE, params=params))

    @mcp.tool()
    def imss_get_medical_services(anio: str = "2026") -> str:
        """Obtiene servicios medicos otorgados por el IMSS (consultas, especialidades)."""
        return str(imss.get(_DATASTORE, params={"q": f"servicios medicos {anio}", "limit": 50}))

    @mcp.tool()
    def imss_get_health_info(tipo: str = "") -> str:
        """Obtiene informacion en salud del IMSS (UMAES, planificacion familiar, dosis, deteccion)."""
        query = "informacion salud"
        if tipo:
            query += f" {tipo}"
        return str(imss.get(_DATASTORE, params={"q": query, "limit": 50}))

    @mcp.tool()
    def imss_get_satisfaction_survey(anio: str = "2026") -> str:
        """Obtiene resultados de la Encuesta Nacional de Satisfaccion de usuarios del IMSS."""
        return str(imss.get(_DATASTORE, params={"q": f"encuesta satisfaccion {anio}", "limit": 50}))
