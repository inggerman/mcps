"""API clients for Mexican government APIs."""
from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx

from mcp_gob_mexico.config import settings

_BASE_URLS = {
    "inegi_base": "https://www.inegi.org.mx/servicios",
    "inegi_denue": "https://www.inegi.org.mx/servicios/api_denue/v1",
    "inegi_indicadores": "https://www.inegi.org.mx/servicios/api_indicadores/v1",
    "inegi_ruteo": "https://gaia.inegi.org.mx/sakbe_v3.1",
    "banxico_base": "https://www.banxico.org.mx/SieAPIRest/service/v1",
    "sat_cfdi": "https://consultaqr.facturaelectronica.sat.gob.mx",
    "datos_gob": "https://datos.gob.mx/api/3/action",
    "profeco": "https://datos.profeco.gob.mx/api.php",
    "cdmx": "https://datos.cdmx.gob.mx/api/3/action",
    "imss": "http://datos.imss.gob.mx/api/action",
    "conagua": "https://datos.conagua.gob.mx",
    "sinaica": "https://sinaica.inecc.gob.mx",
    "impi_marcas": "https://acervomarcas.impi.gob.mx:8181",
    "cfe": "https://datos.gob.mx/busca/api/3/action",
    "rpc": "https://rpc.economia.gob.mx/siger2",
}


class BaseClient:
    """Base HTTP client with caching and retry logic."""

    def __init__(self, base_url: str, headers: dict[str, str] | None = None):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self._cache: dict[str, tuple[Any, float]] = {}
        self._client = httpx.Client(timeout=settings.http_timeout, headers=self.headers)

    def _get_cached(self, key: str) -> Any | None:
        if key in self._cache:
            data, ts = self._cache[key]
            if time.time() - ts < settings.cache_ttl:
                return data
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        self._cache[key] = (data, time.time())

    def get(self, path: str, params: dict | None = None, use_cache: bool = True) -> Any:
        cache_key = f"{path}:{json.dumps(params or {}, sort_keys=True)}"
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached
        url = f"{self.base_url}/{path.lstrip('/')}"
        for attempt in range(settings.max_retries):
            try:
                resp = self._client.get(url, params=params)
                resp.raise_for_status()
                ct = resp.headers.get("content-type", "")
                data = resp.json() if "json" in ct else resp.text
                if use_cache:
                    self._set_cache(cache_key, data)
                return data
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                if attempt == settings.max_retries - 1:
                    return {"error": str(e), "status": "failed"}
                time.sleep(2 ** attempt)
        return {"error": "max retries exceeded", "status": "failed"}

    def post(self, path: str, data: dict | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        for attempt in range(settings.max_retries):
            try:
                resp = self._client.post(url, json=data)
                resp.raise_for_status()
                ct = resp.headers.get("content-type", "")
                return resp.json() if "json" in ct else resp.text
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                if attempt == settings.max_retries - 1:
                    return {"error": str(e), "status": "failed"}
                time.sleep(2 ** attempt)
        return {"error": "max retries exceeded", "status": "failed"}


class INEGIClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["inegi_base"], headers={"Accept": "application/json"})
        self.token = settings.inegi_token

    def get_indicador(self, indicador: str, area: str = "00", idioma: str = "es",
                      reciente: bool = True, formato: str = "json") -> Any:
        rec = "true" if reciente else "false"
        url = f"{_BASE_URLS['inegi_indicadores']}/api/Indicadores/{indicador}/{area}/{idioma}/{rec}/{formato}"
        return self.get(url, params={"token": self.token})

    def search_denue(self, nombre: str, entidad: str = "00", pagina: int = 1) -> Any:
        path = f"busqueda/{nombre}/{entidad}/{pagina}"
        return self.get(f"{_BASE_URLS['inegi_denue']}/{path}", params={"token": self.token})

    def get_denue_establecimiento(self, id_establecimiento: str) -> Any:
        path = f"ficha/{id_establecimiento}"
        return self.get(f"{_BASE_URLS['inegi_denue']}/{path}", params={"token": self.token})

    def search_destino(self, texto: str, formato: str = "json") -> Any:
        return self.post(
            f"{_BASE_URLS['inegi_ruteo']}/buscadestino",
            data={"texto": texto, "tipo": formato},
        )

    def calculate_route(self, inicio: str, fin: str, tipo: str = "optima",
                        formato: str = "json", **kwargs: Any) -> Any:
        data = {"inicio": inicio, "fin": fin, "tipo": tipo, "tipo_formato": formato, **kwargs}
        return self.post(f"{_BASE_URLS['inegi_ruteo']}/{tipo}", data=data)

    def get_combustible(self, formato: str = "json") -> Any:
        return self.get(f"{_BASE_URLS['inegi_ruteo']}/combustible", params={"tipo": formato})


class BanxicoClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["banxico_base"], headers={
            "Accept": "application/json",
            "Bmx-Token": settings.banxico_token,
        })

    def get_serie(self, id_serie: str, fecha_inicio: str | None = None,
                  fecha_fin: str | None = None) -> Any:
        path = f"series/{id_serie}/datos/{fecha_inicio or ''}/{fecha_fin or ''}"
        return self.get(path)

    def get_series_metadata(self, id_serie: str) -> Any:
        return self.get(f"series/{id_serie}")

    def search_series(self, query: str) -> Any:
        return self.get("series", params={"q": query})


class SATClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["sat_cfdi"])

    def validate_cfdi(self, expresion_impresa: str) -> Any:
        url = f"{_BASE_URLS['sat_cfdi']}/ConsultaCFDIService.svc"
        soap_body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
            "<soap:Body>"
            '<Consulta xmlns="http://tempuri.org/">'
            f"<expresionImpresa>{expresion_impresa}</expresionImpresa>"
            "</Consulta></soap:Body></soap:Envelope>"
        )
        resp = self._client.post(
            url,
            content=soap_body,
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "http://tempuri.org/IConsultaCFDIService/Consulta",
            },
        )
        return {"status_code": resp.status_code, "response": resp.text[:2000]}


class DatosGobClient(BaseClient):
    """CKAN API client for datos.gob.mx."""

    def __init__(self):
        super().__init__(_BASE_URLS["datos_gob"])

    def search_datasets(self, query: str, rows: int = 10, start: int = 0) -> Any:
        return self.get("package_search", params={"q": query, "rows": rows, "start": start})

    def get_dataset(self, id: str) -> Any:
        return self.get("package_show", params={"id": id})

    def list_organizations(self) -> Any:
        return self.get("organization_list")

    def list_groups(self) -> Any:
        return self.get("group_list")

    def get_organization(self, id: str) -> Any:
        return self.get("organization_show", params={"id": id})

    def search_by_tag(self, tag: str, rows: int = 10) -> Any:
        return self.get("package_search", params={"fq": f"tags:{tag}", "rows": rows})


class ProfecoClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["profeco"])


class CDMXClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["cdmx"])


class IMSSClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["imss"])


class CONAGUAClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["conagua"])


class SEMARNATClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["sinaica"])


class IMPIClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["impi_marcas"])


class CFEClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["cfe"])


class RPCClient(BaseClient):
    def __init__(self):
        super().__init__(_BASE_URLS["rpc"])


class RENAPOClient:
    """RENAPO/CURP utilities (no public API, algorithmic validation)."""

    _CURP_PATTERN = re.compile(
        r'^([A-Z][AEIOUX][A-Z]{2}\d{2}(?:0[1-9]|1[0-2])'
        r'(?:0[1-9]|[12]\d|3[01])[HM]'
        r'(?:AS|B[CS]|C[CLMSH]|D[FG]|G[TR]|HG|JC|M[CNS]|N[ETL]|OC|PL|Q[TR]|S[PLR]|T[CSL]|VZ|YN|ZS)'
        r'[B-DF-HJ-NP-TV-Z]{3}[A-Z\d]\d)$'
    )

    _ENTIDADES = {
        "AGUASCALIENTES": "AS", "BAJA CALIFORNIA": "BC", "BAJA CALIFORNIA SUR": "BS",
        "CAMPECHE": "CC", "COAHUILA": "CL", "COLIMA": "CM", "CHIAPAS": "CS",
        "CHIHUAHUA": "CH", "CIUDAD DE MEXICO": "DF", "DURANGO": "DG", "GUANAJUATO": "GT",
        "GUERRERO": "GR", "HIDALGO": "HG", "JALISCO": "JC", "MEXICO": "MC",
        "MICHOACAN": "MN", "MORELOS": "MS", "NAYARIT": "NT", "NUEVO LEON": "NL",
        "OAXACA": "OC", "PUEBLA": "PL", "QUERETARO": "QT", "QUINTANA ROO": "QR",
        "SAN LUIS POTOSI": "SP", "SINALOA": "SL", "SONORA": "SR", "TABASCO": "TC",
        "TAMAULIPAS": "TS", "TLAXCALA": "TL", "VERACRUZ": "VZ", "YUCATAN": "YN",
        "ZACATECAS": "ZS", "NACIDO EN EL EXTRANJERO": "NE",
    }

    @staticmethod
    def validate_curp_format(curp: str) -> dict:
        if len(curp) != 18:
            return {"valid": False, "error": "CURP debe tener 18 caracteres"}
        if not RENAPOClient._CURP_PATTERN.match(curp.upper()):
            return {"valid": False, "error": "Formato de CURP invalido"}
        return {"valid": True, "curp": curp.upper()}

    @staticmethod
    def generate_curp(nombre: str, apellido_paterno: str, apellido_materno: str,
                      fecha_nacimiento: str, sexo: str, entidad: str) -> dict:
        nombre = nombre.upper().strip()
        ap = apellido_paterno.upper().strip()
        am = apellido_materno.upper().strip()
        sexo = sexo.upper().strip()
        entidad = entidad.upper().strip()

        p1 = ap[0] if ap else "X"
        vocales = [c for c in ap[1:] if c in "AEIOU"]
        p2 = vocales[0] if vocales else "X"
        p3 = am[0] if am else "X"
        p4 = nombre[0] if nombre else "X"

        try:
            yy, mm, dd = fecha_nacimiento.split("-")
            fecha = f"{yy[2:]}{mm}{dd}"
        except Exception:
            fecha = "000000"

        s = "H" if sexo.startswith("H") else "M"
        ent_code = RENAPOClient._ENTIDADES.get(entidad, "NE")

        def _primera_consonante(cadena: str) -> str:
            for c in cadena[1:]:
                if c.isalpha() and c not in "AEIOU":
                    return c
            return "X"

        c1 = _primera_consonante(ap)
        c2 = _primera_consonante(am)
        c3 = _primera_consonante(nombre)

        import random
        homoclave = f"{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789')}{random.randint(0, 9)}"

        curp = f"{p1}{p2}{p3}{p4}{fecha}{s}{ent_code}{c1}{c2}{c3}{homoclave}"
        return {"curp": curp, "valid": True, "nota": "CURP aproximada, verificar en portal oficial"}


inegi = INEGIClient()
banxico = BanxicoClient()
sat = SATClient()
datos_gob = DatosGobClient()
profeco = ProfecoClient()
cdmx = CDMXClient()
imss = IMSSClient()
conagua = CONAGUAClient()
semarnat = SEMARNATClient()
impi = IMPIClient()
cfe = CFEClient()
rpc = RPCClient()
renapo = RENAPOClient()
