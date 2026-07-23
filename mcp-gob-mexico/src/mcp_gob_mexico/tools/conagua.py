"""CONAGUA tools - 5 tools for water resources and weather data."""
from __future__ import annotations

from mcp_gob_mexico.clients import conagua

_OPEN_DATA = "views/index_datos_abiertos.html"


def register(mcp: object) -> None:
    @mcp.tool()
    def conagua_get_weather_stations(estado: str = "") -> str:
        """Obtiene el listado de estaciones climatologicas de la red de CONAGUA."""
        return str(conagua.get(_OPEN_DATA, params={"q": "estaciones climatologicas"}))[:5000]

    @mcp.tool()
    def conagua_get_water_availability(cuenca: str = "") -> str:
        """Obtiene volumenes de disponibilidad media anual de aguas superficiales por cuenca."""
        return str(conagua.get(_OPEN_DATA, params={"q": "disponibilidad agua superficial"}))[:5000]

    @mcp.tool()
    def conagua_get_cyclone_alerts() -> str:
        """Obtiene avisos de ciclon tropical emitidos por el Servicio Meteorologico Nacional."""
        return str(conagua.get("https://smn.conagua.gob.mx/tools/JSON/avisos_ciclon_tropical.json"))[:5000]

    @mcp.tool()
    def conagua_get_hydrometric_data(estacion: str = "") -> str:
        """Obtiene datos hidrometricos de estaciones de CONAGUA."""
        return str(conagua.get(_OPEN_DATA, params={"q": "datos hidrometricos"}))[:5000]

    @mcp.tool()
    def conagua_get_water_quality(estado: str = "") -> str:
        """Obtiene datos de calidad del agua de cuerpos hidricos monitoreados por CONAGUA."""
        return str(conagua.get(_OPEN_DATA, params={"q": "calidad agua"}))[:5000]
