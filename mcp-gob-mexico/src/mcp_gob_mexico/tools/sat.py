"""SAT tools - 8 tools for tax and fiscal services."""
from __future__ import annotations

import re

from mcp_gob_mexico.clients import sat

_SAT_CATALOG_URL = "https://www.sat.gob.mx/cs/Satellite?blobcol=urldata&blobkey=id&blobtable=MungoBlobs&blobwhere=1461174995026"


def register(mcp: object) -> None:
    @mcp.tool()
    def sat_validate_cfdi(expresion_impresa: str) -> str:
        """Valida el estado de un CFDI en el SAT usando la expresion impresa del QR."""
        return str(sat.validate_cfdi(expresion_impresa))

    @mcp.tool()
    def sat_check_rfc_in_efos(rfc: str) -> str:
        """Verifica si un RFC esta en la lista de EFOS (Art. 69-B CFF)."""
        return str(sat.get("https://omawww.sat.gob.mx/cifras_sat/Paginas/datos/vinculo.html?page=ListCompleta69B.html"))

    @mcp.tool()
    def sat_validate_rfc_format(rfc: str) -> str:
        """Valida el formato de un RFC mexicano (moral: 12 caracteres, fisica: 13)."""
        rfc = rfc.upper().strip()
        if len(rfc) == 12:
            pattern = r'^[A-ZÑ&]{3}\d{6}[A-Z\d]{3}$'
        elif len(rfc) == 13:
            pattern = r'^[A-ZÑ&]{4}\d{6}[A-Z\d]{3}$'
        else:
            return str({"valid": False, "error": "RFC debe tener 12 (moral) o 13 (fisica) caracteres"})
        valid = bool(re.match(pattern, rfc))
        return str({"valid": valid, "rfc": rfc, "type": "moral" if len(rfc) == 12 else "fisica"})

    @mcp.tool()
    def sat_get_cfdi_status(uuid: str, rfc_emisor: str, rfc_receptor: str, total: str) -> str:
        """Consulta el estado de un CFDI por UUID, RFC emisor, RFC receptor y total."""
        expresion = f"?id={uuid}&re={rfc_emisor}&rr={rfc_receptor}&tt={total}"
        return str(sat.validate_cfdi(expresion))

    @mcp.tool()
    def sat_get_tax_regimes() -> str:
        """Obtiene el catalogo de regimenes fiscales del SAT."""
        return str(sat.get(_SAT_CATALOG_URL))[:5000]

    @mcp.tool()
    def sat_get_cfdi_catalogs() -> str:
        """Obtiene los catalogos CFDI 4.0 (clave producto/servicio, unidad, forma de pago, etc.)."""
        return str(sat.get(_SAT_CATALOG_URL))[:5000]

    @mcp.tool()
    def sat_get_postal_codes(codigo_postal: str) -> str:
        """Consulta informacion de un codigo postal mexicano (colonia, municipio, estado)."""
        return str(sat.get(_SAT_CATALOG_URL))[:5000]

    @mcp.tool()
    def sat_get_economic_activities() -> str:
        """Obtiene el catalogo de actividades economicas del SAT."""
        return str(sat.get(_SAT_CATALOG_URL))[:5000]
