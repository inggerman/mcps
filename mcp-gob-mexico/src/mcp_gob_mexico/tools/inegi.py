"""INEGI tools - 15 tools for statistics, geography, and economic data."""
from __future__ import annotations

from mcp_gob_mexico.clients import inegi


def register(mcp: object) -> None:
    @mcp.tool()
    def inegi_search_indicador(nombre: str, area: str = "00", idioma: str = "es") -> str:
        """Busca indicadores del INEGI por nombre. area: 00=nacional, 99=entidad, 999=municipio."""
        return str(inegi.get_indicador(nombre, area=area, idioma=idioma))

    @mcp.tool()
    def inegi_get_indicador(clave_indicador: str, area: str = "00", idioma: str = "es",
                            reciente: bool = True, formato: str = "json") -> str:
        """Obtiene datos de un indicador especifico del INEGI por su clave."""
        return str(inegi.get_indicador(clave_indicador, area=area, idioma=idioma,
                                       reciente=reciente, formato=formato))

    @mcp.tool()
    def inegi_get_indicador_metadata(clave_indicador: str, idioma: str = "es") -> str:
        """Obtiene los metadatos de un indicador del INEGI (catalogo de metadatos)."""
        result = inegi.get(
            f"{inegi.base_url}/api/Indicadores/{clave_indicador}/metadata/{idioma}/json",
            params={"token": inegi.token},
        )
        return str(result)

    @mcp.tool()
    def inegi_search_denue(nombre: str, entidad: str = "00", pagina: int = 1) -> str:
        """Busca establecimientos en el DENUE por nombre y entidad federativa."""
        return str(inegi.search_denue(nombre, entidad=entidad, pagina=pagina))

    @mcp.tool()
    def inegi_get_denue_establecimiento(id_establecimiento: str) -> str:
        """Obtiene la ficha completa de un establecimiento del DENUE por su ID."""
        return str(inegi.get_denue_establecimiento(id_establecimiento))

    @mcp.tool()
    def inegi_search_denue_by_actividad(actividad: str, entidad: str = "00") -> str:
        """Busca establecimientos del DENUE por actividad economica."""
        return str(inegi.search_denue(actividad, entidad=entidad))

    @mcp.tool()
    def inegi_calculate_route(inicio: str, fin: str, tipo: str = "optima",
                              formato: str = "json") -> str:
        """Calcula ruta entre dos puntos. tipo: optima, cuota, libre."""
        return str(inegi.calculate_route(inicio, fin, tipo=tipo, formato=formato))

    @mcp.tool()
    def inegi_search_destino(texto: str, formato: str = "json") -> str:
        """Busca un destino en la Red Nacional de Caminos (localidades, sitios de interes)."""
        return str(inegi.search_destino(texto, formato=formato))

    @mcp.tool()
    def inegi_get_combustible_prices(formato: str = "json") -> str:
        """Obtiene tipos de combustible y sus costos promedio actuales."""
        return str(inegi.get_combustible(formato=formato))

    @mcp.tool()
    def inegi_get_route_detail(inicio: str, fin: str, tipo: str = "optima") -> str:
        """Obtiene el itinerario detallado de una ruta (tramos, distancias, tiempos, costos)."""
        return str(inegi.calculate_route(inicio, fin, tipo=tipo))

    @mcp.tool()
    def inegi_find_nearest_line(x: float, y: float, escala: int = 100000,
                                formato: str = "json") -> str:
        """Encuentra la linea mas cercana de la Red Nacional de Caminos a unas coordenadas."""
        data = {"x": x, "y": y, "escala": escala, "tipo": formato}
        result = inegi.post(f"{inegi.base_url}/sakbe_v3.1/buscalinea", data=data)
        return str(result)

    @mcp.tool()
    def inegi_get_google_maps_layer(capa: str = "all") -> str:
        """Obtiene capas del INEGI para visualizar en Google Maps."""
        result = inegi.get(f"{inegi.base_url}/api_map.html", params={"capa": capa})
        return str(result)

    @mcp.tool()
    def inegi_get_wms_layer(servicio: str = "WMS") -> str:
        """Obtiene capas de servicios de mapas web (WMS/WFS) del INEGI."""
        result = inegi.get(f"{inegi.base_url}/wsinfogeo/default.html", params={"servicio": servicio})
        return str(result)

    @mcp.tool()
    def inegi_get_geographic_names(entidad: str = "00") -> str:
        """Obtiene nombres geograficos registrados por el INEGI por entidad federativa."""
        result = inegi.get(
            f"{inegi.base_url}/servicios/wsinfogeo/nombres_geograficos",
            params={"entidad": entidad, "token": inegi.token},
        )
        return str(result)

    @mcp.tool()
    def inegi_get_localidades(entidad: str = "00", municipio: str = "0") -> str:
        """Obtiene el catalogo de localidades por entidad y municipio del INEGI."""
        result = inegi.get(
            f"{inegi.base_url}/servicios/catalogo/localidades",
            params={"entidad": entidad, "municipio": municipio, "token": inegi.token},
        )
        return str(result)
