"""RENAPO/CURP tools - 3 tools for identity validation."""
from __future__ import annotations

from mcp_gob_mexico.clients import renapo


def register(mcp: object) -> None:
    @mcp.tool()
    def renapo_validate_curp(curp: str) -> str:
        """Valida el formato de una CURP mexicana (18 caracteres, estructura oficial)."""
        return str(renapo.validate_curp_format(curp))

    @mcp.tool()
    def renapo_generate_curp(nombre: str, apellido_paterno: str, apellido_materno: str,
                             fecha_nacimiento: str, sexo: str, entidad: str) -> str:
        """Genera una CURP aproximada usando el algoritmo oficial. fecha_nacimiento=YYYY-MM-DD."""
        return str(renapo.generate_curp(nombre, apellido_paterno, apellido_materno,
                                        fecha_nacimiento, sexo, entidad))

    @mcp.tool()
    def renapo_get_entity_codes() -> str:
        """Obtiene el catalogo de codigos de entidad federativa usados en la CURP."""
        codes = {
            "AS": "Aguascalientes", "BC": "Baja California", "BS": "Baja California Sur",
            "CC": "Campeche", "CL": "Coahuila", "CM": "Colima", "CS": "Chiapas",
            "CH": "Chihuahua", "DF": "Ciudad de Mexico", "DG": "Durango", "GT": "Guanajuato",
            "GR": "Guerrero", "HG": "Hidalgo", "JC": "Jalisco", "MC": "Mexico",
            "MN": "Michoacan", "MS": "Morelos", "NT": "Nayarit", "NL": "Nuevo Leon",
            "OC": "Oaxaca", "PL": "Puebla", "QT": "Queretaro", "QR": "Quintana Roo",
            "SP": "San Luis Potosi", "SL": "Sinaloa", "SR": "Sonora", "TC": "Tabasco",
            "TS": "Tamaulipas", "TL": "Tlaxcala", "VZ": "Veracruz", "YN": "Yucatan",
            "ZS": "Zacatecas", "NE": "Nacido en el Extranjero",
        }
        return str(codes)
