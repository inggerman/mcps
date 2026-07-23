"""CFE tools - 4 tools for electricity data."""
from __future__ import annotations

from mcp_gob_mexico.clients import cfe


def register(mcp: object) -> None:
    @mcp.tool()
    def cfe_get_electricity_consumption(entidad: str = "", anio: str = "") -> str:
        """Obtiene usuarios y consumo de electricidad por municipio (a partir de 2018)."""
        params = {"q": "usuarios consumo electricidad municipio"}
        if entidad:
            params["q"] += f" {entidad}"
        if anio:
            params["q"] += f" {anio}"
        return str(cfe.get("package_search", params=params))

    @mcp.tool()
    def cfe_get_electrification_data() -> str:
        """Obtiene el nivel de electrificacion desglosado por entidad federativa."""
        return str(cfe.get("package_search", params={"q": "electrificacion entidad federativa"}))

    @mcp.tool()
    def cfe_get_capacity() -> str:
        """Obtiene lineas instaladas y capacidad de subestaciones de transmision."""
        return str(cfe.get("package_search", params={"q": "lineas capacidad subestaciones"}))

    @mcp.tool()
    def cfe_get_generation() -> str:
        """Obtiene datos de generacion bruta de energia electrica de CFE."""
        return str(cfe.get("package_search", params={"q": "generacion bruta energia"}))
