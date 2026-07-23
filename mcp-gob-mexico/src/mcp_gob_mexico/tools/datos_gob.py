"""datos.gob.mx tools - 8 tools for CKAN open data platform."""
from __future__ import annotations

from mcp_gob_mexico.clients import datos_gob


def register(mcp: object) -> None:
    @mcp.tool()
    def datos_gob_search_datasets(query: str, rows: int = 10, start: int = 0) -> str:
        """Busca datasets en la Plataforma Nacional de Datos Abiertos de Mexico."""
        return str(datos_gob.search_datasets(query, rows=rows, start=start))

    @mcp.tool()
    def datos_gob_get_dataset(dataset_id: str) -> str:
        """Obtiene los detalles completos de un dataset por su ID en datos.gob.mx."""
        return str(datos_gob.get_dataset(dataset_id))

    @mcp.tool()
    def datos_gob_get_dataset_resources(dataset_id: str) -> str:
        """Obtiene los recursos (archivos descargables) de un dataset especifico."""
        return str(datos_gob.get_dataset(dataset_id))

    @mcp.tool()
    def datos_gob_list_organizations() -> str:
        """Lista todas las instituciones que publican datos en datos.gob.mx."""
        return str(datos_gob.list_organizations())

    @mcp.tool()
    def datos_gob_list_groups() -> str:
        """Lista todas las categorias/grupos tematicos disponibles en datos.gob.mx."""
        return str(datos_gob.list_groups())

    @mcp.tool()
    def datos_gob_get_organization_datasets(organization_id: str) -> str:
        """Obtiene los datasets publicados por una institucion especifica."""
        return str(datos_gob.get_organization(organization_id))

    @mcp.tool()
    def datos_gob_search_by_tag(tag: str, rows: int = 10) -> str:
        """Busca datasets por etiqueta (tag) en datos.gob.mx."""
        return str(datos_gob.search_by_tag(tag, rows=rows))

    @mcp.tool()
    def datos_gob_get_dataset_metadata(dataset_id: str) -> str:
        """Obtiene los metadatos (frecuencia, cobertura, licencia, etc.) de un dataset."""
        return str(datos_gob.get_dataset(dataset_id))
