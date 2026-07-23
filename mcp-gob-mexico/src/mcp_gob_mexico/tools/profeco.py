"""PROFECO tools - 6 tools for consumer protection and price comparison."""
from __future__ import annotations

from mcp_gob_mexico.clients import profeco


def register(mcp: object) -> None:
    @mcp.tool()
    def profeco_search_products(producto: str, pagina: int = 1) -> str:
        """Busca productos en 'Quien es Quien en los Precios' de PROFECO."""
        return str(profeco.get("", params={"q": producto, "page": pagina}))[:5000]

    @mcp.tool()
    def profeco_compare_prices(producto: str, entidad: str = "") -> str:
        """Compara precios de un producto entre diferentes tiendas."""
        return str(profeco.get("", params={"q": producto, "estado": entidad}))[:5000]

    @mcp.tool()
    def profeco_get_product_prices(producto: str, tienda: str = "") -> str:
        """Obtiene precios de un producto especifico, opcionalmente filtrado por tienda."""
        params = {"q": producto}
        if tienda:
            params["tienda"] = tienda
        return str(profeco.get("", params=params))[:5000]

    @mcp.tool()
    def profeco_get_buen_fin_offers() -> str:
        """Obtiene ofertas vigentes de El Buen Fin registradas por PROFECO."""
        return str(profeco.get("https://elbuenfin.profeco.gob.mx/"))[:5000]

    @mcp.tool()
    def profeco_get_product_categories() -> str:
        """Obtiene las categorias de productos disponibles en Quien es Quien en los Precios."""
        return str(profeco.get("https://qqp.profeco.gob.mx/"))[:5000]

    @mcp.tool()
    def profeco_get_price_history(producto: str) -> str:
        """Obtiene el historial de precios de un producto."""
        return str(profeco.get("", params={"q": producto, "history": "true"}))[:5000]
