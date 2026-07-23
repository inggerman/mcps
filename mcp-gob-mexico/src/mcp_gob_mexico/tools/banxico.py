"""Banxico tools - 8 tools for economic indicators and financial data."""
from __future__ import annotations

from mcp_gob_mexico.clients import banxico


def register(mcp: object) -> None:
    @mcp.tool()
    def banxico_get_serie(id_serie: str, fecha_inicio: str = "", fecha_fin: str = "") -> str:
        """Obtiene datos de una serie de tiempo del SIE de Banxico. Ej: SF43718=tipo de cambio USD."""
        return str(banxico.get_serie(id_serie, fecha_inicio or None, fecha_fin or None))

    @mcp.tool()
    def banxico_search_series(query: str) -> str:
        """Busca series de tiempo disponibles en el SIE de Banxico por palabra clave."""
        return str(banxico.search_series(query))

    @mcp.tool()
    def banxico_get_tipos_cambio(fecha_inicio: str = "", fecha_fin: str = "") -> str:
        """Obtiene series de tipos de cambio (USD, EUR, etc.) del SIE de Banxico."""
        return str(banxico.get_serie("SF43718", fecha_inicio or None, fecha_fin or None))

    @mcp.tool()
    def banxico_get_tasas_interes(fecha_inicio: str = "", fecha_fin: str = "") -> str:
        """Obtiene tasas de interes (tasa objetivo, TIIE, etc.) del SIE de Banxico."""
        return str(banxico.get_serie("SF111516", fecha_inicio or None, fecha_fin or None))

    @mcp.tool()
    def banxico_get_inflacion(fecha_inicio: str = "", fecha_fin: str = "") -> str:
        """Obtiene el indice nacional de precios al consumidor (INPC) del SIE de Banxico."""
        return str(banxico.get_serie("SP1", fecha_inicio or None, fecha_fin or None))

    @mcp.tool()
    def banxico_get_agregados_monetarios(fecha_inicio: str = "", fecha_fin: str = "") -> str:
        """Obtiene agregados monetarios (M1, M2, M3, M4) del SIE de Banxico."""
        return str(banxico.get_serie("SF118416", fecha_inicio or None, fecha_fin or None))

    @mcp.tool()
    def banxico_get_balanza_pagos(fecha_inicio: str = "", fecha_fin: str = "") -> str:
        """Obtiene datos de balanza de pagos del SIE de Banxico."""
        return str(banxico.get_serie("SR17056", fecha_inicio or None, fecha_fin or None))

    @mcp.tool()
    def banxico_get_serie_metadata(id_serie: str) -> str:
        """Obtiene los metadatos de una serie especifica del SIE de Banxico."""
        return str(banxico.get_series_metadata(id_serie))
