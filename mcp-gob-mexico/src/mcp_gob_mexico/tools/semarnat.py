"""SEMARNAT/INECC tools - 5 tools for environmental data and air quality."""
from __future__ import annotations

from mcp_gob_mexico.clients import semarnat

_DATOS_GOB_SEARCH = "https://www.datos.gob.mx/busca/api/3/action/package_search"


def register(mcp: object) -> None:
    @mcp.tool()
    def sinaica_get_air_quality(estacion: str = "", contaminante: str = "") -> str:
        """Obtiene indicadores de calidad del aire del SINAICA en tiempo real."""
        return str(semarnat.get("scica/", params={"estacion": estacion, "contaminante": contaminante}))[:5000]

    @mcp.tool()
    def sinaica_get_air_quality_station(estacion_id: str) -> str:
        """Obtiene datos de calidad del aire de una estacion especifica del SINAICA."""
        return str(semarnat.get(f"scica/estacion/{estacion_id}"))[:5000]

    @mcp.tool()
    def semarnat_get_environmental_impact(estado: str = "") -> str:
        """Obtiene Manifestaciones de Impacto Ambiental (MIA) de SEMARNAT."""
        return str(semarnat.get(_DATOS_GOB_SEARCH, params={"q": f"impacto ambiental {estado}", "rows": 20}))

    @mcp.tool()
    def semarnat_get_emissions_data(tipo: str = "") -> str:
        """Obtiene datos de emisiones de contaminantes a la atmosfera."""
        query = "emisiones contaminantes atmosfera"
        if tipo:
            query += f" {tipo}"
        return str(semarnat.get(_DATOS_GOB_SEARCH, params={"q": query, "rows": 20}))

    @mcp.tool()
    def semarnat_get_protected_areas() -> str:
        """Obtiene informacion de Areas Naturales Protegidas (ANP) de Mexico."""
        return str(semarnat.get(_DATOS_GOB_SEARCH, params={"q": "areas naturales protegidas", "rows": 20}))
