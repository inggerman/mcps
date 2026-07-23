"""Resources catalog for Gobierno de Mexico MCP Server - 80 resources."""
import json
from typing import Any


RESOURCES: list[dict[str, Any]] = []


def _add(uri: str, name: str, mime_type: str, description: str, category: str, content: str):
    RESOURCES.append({
        "uri": uri,
        "name": name,
        "mimeType": mime_type,
        "description": description,
        "category": category,
        "content": content,
    })


# === INEGI Resources (1-15) ===

_add("inegi://indicadores/catalogo", "Catalogo de Indicadores INEGI", "application/json",
     "Catalogo completo de indicadores economicos, demograficos y sociales del INEGI",
     "INEGI", json.dumps({
         "categorias": ["Economia", "Poblacion", "Educacion", "Salud", "Vivienda", "Empleo"],
         "niveles": ["Nacional", "Estatal", "Municipal"],
         "formatos": ["JSON", "JSONP", "XML", "JSON-stat"],
         "url_base": "https://www.inegi.org.mx/servicios/api_indicadores/v1",
         "autenticacion": "Token gratuito",
     }, ensure_ascii=False, indent=2))

_add("inegi://denue/guia", "Guia DENUE", "application/json",
     "Guia de uso del Directorio Estadistico Nacional de Unidades Economicas",
     "INEGI", json.dumps({
         "total_establecimientos": "5+ millones",
         "filtros": ["nombre", "actividad_economica", "entidad", "municipio"],
         "url_base": "https://www.inegi.org.mx/servicios/api_denue/v1",
         "ejemplo": "busqueda/{nombre}/{entidad}/{pagina}?token={token}",
     }, ensure_ascii=False, indent=2))

_add("inegi://ruteo/guia", "Guia API de Ruteo", "application/json",
     "Documentacion de la API de Ruteo INEGI (Red Nacional de Caminos)",
     "INEGI", json.dumps({
         "metodos": ["buscalinea", "buscadestino", "optima", "cuota", "libre",
                     "detalle_o", "detalle_c", "detalle_l", "combustible"],
         "tipos_ruta": ["optima", "cuota", "libre"],
         "url_base": "https://gaia.inegi.org.mx/sakbe_v3.1",
         "parametros": ["inicio", "fin", "tipo_vehiculo", "ejes_excedentes", "barreras"],
     }, ensure_ascii=False, indent=2))

_add("inegi://geografico/nombres", "Nombres Geograficos", "application/json",
     "Catalogo de nombres geograficos del INEGI (localidades, rios, montanas)",
     "INEGI", json.dumps({
         "tipos": ["Localidades", "Areas naturales", "Formas litorales",
                   "Obras infraestructura", "Rasgos hidrograficos", "Rasgos orograficos"],
         "servicio": "WMS/WFS",
     }, ensure_ascii=False, indent=2))

_add("inegi://mapas/google", "Capas Google Maps", "application/json",
     "Capas del INEGI disponibles para Google Maps",
     "INEGI", json.dumps({
         "url": "https://www.inegi.org.mx/servicios/api_map.html",
         "funcion": "Overlay de capas geograficas INEGI sobre Google Maps",
     }, ensure_ascii=False, indent=2))

_add("inegi://entidades/catalogo", "Catalogo de Entidades Federativas", "application/json",
     "Catalogo de las 32 entidades federativas de Mexico con claves INEGI",
     "INEGI", json.dumps({
         "01": "Aguascalientes", "02": "Baja California", "03": "Baja California Sur",
         "04": "Campeche", "05": "Coahuila", "06": "Colima", "07": "Chiapas",
         "08": "Chihuahua", "09": "Ciudad de Mexico", "10": "Durango", "11": "Guanajuato",
         "12": "Guerrero", "13": "Hidalgo", "14": "Jalisco", "15": "Mexico",
         "16": "Michoacan", "17": "Morelos", "18": "Nayarit", "19": "Nuevo Leon",
         "20": "Oaxaca", "21": "Puebla", "22": "Queretaro", "23": "Quintana Roo",
         "24": "San Luis Potosi", "25": "Sinaloa", "26": "Sonora", "27": "Tabasco",
         "28": "Tamaulipas", "29": "Tlaxcala", "30": "Veracruz", "31": "Yucatan",
         "32": "Zacatecas",
     }, ensure_ascii=False, indent=2))

_add("inegi://actividades/catalogo", "Catalogo de Actividades Economicas", "application/json",
     "Clasificacion de actividades economicas para DENUE (SCIAN)",
     "INEGI", json.dumps({
         "sectores": ["Agricultura", "Mineria", "Manufactura", "Construccion",
                      "Comercio", "Servicios", "Transporte", "Informacion"],
         "sistema": "SCIAN (Sistema de Clasificacion Industrial de America del Norte)",
     }, ensure_ascii=False, indent=2))

_add("inegi://indicadores/economicos", "Indicadores Economicos Principales", "application/json",
     "Lista de indicadores economicos clave disponibles en la API del INEGI",
     "INEGI", json.dumps({
         "PIB": "Producto Interno Bruto",
         "INPC": "Indice Nacional de Precios al Consumidor",
         "Desempleo": "Tasa de Desocupacion",
         "Salarios": "Salarios promedio",
         "Comercio": "Indicadores de comercio",
         "Industria": "Indicadores industriales",
     }, ensure_ascii=False, indent=2))

_add("inegi://indicadores/demograficos", "Indicadores Demograficos", "application/json",
     "Lista de indicadores demograficos del INEGI",
     "INEGI", json.dumps({
         "Poblacion total": "Censo y conteos",
         "Tasa natalidad": "Nacimientos por entidad",
         "Tasa mortalidad": "Defunciones por entidad",
         "Migracion": "Flujos migratorios",
         "Envejecimiento": "Estructura por edad",
     }, ensure_ascii=False, indent=2))

_add("inegi://ruteo/combustibles", "Tipos de Combustible", "application/json",
     "Catalogo de tipos de combustible y precios promedio de la API de Ruteo",
     "INEGI", json.dumps({
         "tipos": ["Regular", "Premium", "Diesel"],
         "metodo": "combustible (GET)",
         "actualizacion": "Periodica",
     }, ensure_ascii=False, indent=2))

_add("inegi://servicios/lista", "Lista de Servicios INEGI", "application/json",
     "Lista completa de servicios y APIs disponibles del INEGI",
     "INEGI", json.dumps({
         "apis": ["Banco de Indicadores", "DENUE", "Ruteo", "Google Maps Layer",
                  "Servicio de Mapas Web (WMS/WFS)", "Nombres Geograficos"],
         "url_documentacion": "https://www.inegi.org.mx/servicios/",
         "autenticacion": "Token gratuito via registro",
     }, ensure_ascii=False, indent=2))

_add("inegi://municipios/catalogo", "Catalogo de Municipios", "application/json",
     "Catalogo de municipios por entidad federativa del INEGI",
     "INEGI", json.dumps({
         "total_municipios": 2469,
         "estructura": "clave_entidad + clave_municipio",
         "ejemplo": "01001 = Aguascalientes, Aguascalientes",
     }, ensure_ascii=False, indent=2))

_add("inegi://denue/tamanos", "Clasificacion de Tamano de Establecimiento", "application/json",
     "Clasificacion de establecimientos por tamano en el DENUE",
     "INEGI", json.dumps({
         "Micro": "0-10 empleados",
         "Pequena": "11-50 empleados",
         "Mediana": "51-250 empleados",
         "Grande": "251+ empleados",
     }, ensure_ascii=False, indent=2))

_add("inegi://ruteo/vehiculos", "Tipos de Vehiculo para Ruteo", "application/json",
     "Catalogo de tipos de vehiculo soportados por la API de Ruteo",
     "INEGI", json.dumps({
         "tipos": ["Automovil", "Camion ligero", "Camion pesado", "Motocicleta"],
         "parametros_adicionales": ["ejes_excedentes", "barreras"],
     }, ensure_ascii=False, indent=2))

_add("inegi://formatos/soportados", "Formatos de Respuesta", "application/json",
     "Formatos de respuesta soportados por las APIs del INEGI",
     "INEGI", json.dumps({
         "json": "JavaScript Object Notation",
         "jsonp": "JSON con Padding",
         "xml": "eXtensible Markup Language",
         "json-stat": "JSON-stat (formato estadistico ligero)",
     }, ensure_ascii=False, indent=2))


# === Banxico Resources (16-23) ===

_add("banxico://series/tipocambio", "Series de Tipo de Cambio", "application/json",
     "Series de tipo de cambio disponibles en el SIE de Banxico",
     "Banxico", json.dumps({
         "SF43718": "Tipo de cambio FIX (USD/MXN)",
         "SF46410": "Tipo de cambio para solventar obligaciones",
         "SF60653": "Tipo de cambio interbancario",
     }, ensure_ascii=False, indent=2))

_add("banxico://series/tasas", "Series de Tasas de Interes", "application/json",
     "Series de tasas de interes del SIE de Banxico",
     "Banxico", json.dumps({
         "SF111516": "Tasa objetivo de politica monetaria",
         "SF43878": "TIIE 28 dias",
         "SF43879": "TIIE 91 dias",
         "SF43936": "CETES 28 dias",
     }, ensure_ascii=False, indent=2))

_add("banxico://series/inflacion", "Series de Inflacion", "application/json",
     "Series de inflacion e indices de precios del SIE de Banxico",
     "Banxico", json.dumps({
         "SP1": "INPC (Indice Nacional de Precios al Consumidor)",
         "SP7": "Inflacion subyacente",
         "SP8": "Inflacion no subyacente",
     }, ensure_ascii=False, indent=2))

_add("banxico://series/monetarios", "Agregados Monetarios", "application/json",
     "Series de agregados monetarios del SIE de Banxico",
     "Banxico", json.dumps({
         "SF118416": "M1 (Efectivo + cuentas corrientes)",
         "SF118417": "M2 (M1 + instrumentos de corto plazo)",
         "SF118418": "M3 (M2 + captacion no bancaria)",
         "SF118419": "M4 (M3 + valores gubernamentales)",
     }, ensure_ascii=False, indent=2))

_add("banxico://series/balanza", "Balanza de Pagos", "application/json",
     "Series de balanza de pagos del SIE de Banxico",
     "Banxico", json.dumps({
         "SR17056": "Cuenta corriente",
         "SR17057": "Cuenta de capital",
         "SR17058": "Balanza comercial",
     }, ensure_ascii=False, indent=2))

_add("banxico://api/documentacion", "Documentacion API SIE", "application/json",
     "Documentacion general de la API REST del SIE de Banxico",
     "Banxico", json.dumps({
         "url_base": "https://www.banxico.org.mx/SieAPIRest/service/v1",
         "autenticacion": "Token (Bmx-Token header)",
         "endpoint_series": "/series/{idSerie}/datos/{fechaInicio}/{fechaFin}",
         "endpoint_metadata": "/series/{idSerie}",
         "formato": "JSON",
         "libreria_python": "pip install sie-banxico",
     }, ensure_ascii=False, indent=2))

_add("banxico://series/externo", "Sector Externo", "application/json",
     "Series del sector externo de la economia mexicana",
     "Banxico", json.dumps({
         "SF43718": "Tipo de cambio USD",
         "SF46410": "Tipo de cambio euros",
         "SR17056": "Cuenta corriente",
         "SF178921": "Reservas internacionales",
     }, ensure_ascii=False, indent=2))

_add("banxico://series/financiero", "Sistema Financiero", "application/json",
     "Series del sistema financiero mexicano",
     "Banxico", json.dumps({
         "SF43783": "Captacion bancaria",
         "SF43784": "Credito bancario",
         "SF43785": "Indicadores de banca",
     }, ensure_ascii=False, indent=2))


# === SAT Resources (24-31) ===

_add("sat://cfdi/guia", "Guia CFDI", "application/json",
     "Guia de servicios CFDI del SAT",
     "SAT", json.dumps({
         "version_actual": "CFDI 4.0",
         "servicios": ["Consulta de CFDI", "Descarga Masiva", "Facturacion gratuita"],
         "url_consulta": "https://consultaqr.facturaelectronica.sat.gob.mx",
         "url_descarga": "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx",
         "protocolo": "SOAP",
         "autenticacion_descarga": "e.Firma (certificado .cer + llave .key)",
     }, ensure_ascii=False, indent=2))

_add("sat://cfdi/estados", "Estados de CFDI", "application/json",
     "Estados posibles de un CFDI al consultar en el SAT",
     "SAT", json.dumps({
         "S": "Comprobante obtenido satisfactoriamente",
         "N601": "Expresion impresa no valida",
         "N602": "Comprobante no encontrado (UUID no en BD)",
         "Codigo_100": "RFC emisor en lista EFOS (Art. 69-B)",
         "Codigo_200": "RFC emisor no en lista EFOS",
     }, ensure_ascii=False, indent=2))

_add("sat://efos/lista", "Lista EFOS (Art. 69-B)", "application/json",
     "Informacion sobre Empresas que Facturan Operaciones Simuladas",
     "SAT", json.dumps({
         "articulo": "Articulo 69-B del Codigo Fiscal de la Federacion",
         "url": "https://omawww.sat.gob.mx/cifras_sat/Paginas/datos/vinculo.html?page=ListCompleta69B.html",
         "implicacion": "Comprobantes de EFOS no tienen efectos fiscales",
     }, ensure_ascii=False, indent=2))

_add("sat://rfc/formato", "Formato de RFC", "application/json",
     "Estructura y validacion de RFC mexicano",
     "SAT", json.dumps({
         "persona_fisica": "4 letras + 6 digitos (fecha) + 3 alfanumerico = 13 caracteres",
         "persona_moral": "3 letras + 6 digitos (fecha) + 3 alfanumerico = 12 caracteres",
         "ejemplo_pf": "GOME850101HDFLRN01",
         "ejemplo_pm": "ABC123456789",
     }, ensure_ascii=False, indent=2))

_add("sat://cfdi/versiones", "Versiones CFDI", "application/json",
     "Versiones del CFDI y su vigencia",
     "SAT", json.dumps({
         "CFDI 4.0": "Vigente desde 2022-01-01",
         "CFDI 3.3": "Vigente hasta 2022-04-01 (transicion)",
         "CFDI 3.2": "Obsoleto",
     }, ensure_ascii=False, indent=2))

_add("sat://catalogos/lista", "Catalogos SAT", "application/json",
     "Lista de catalogos disponibles para CFDI 4.0",
     "SAT", json.dumps({
         "catalogos": ["Clave de producto/servicio", "Clave de unidad",
                       "Forma de pago", "Metodo de pago", "Uso de CFDI",
                       "Regimen fiscal", "Tipo de comprobante", "Pais"],
         "url": "https://www.sat.gob.mx/consultas/27797/catalogos-disponibles-para-cfdi-4.0",
     }, ensure_ascii=False, indent=2))

_add("sat://descarga/tipos", "Tipos de Descarga Masiva", "application/json",
     "Tipos de solicitud de descarga masiva de CFDI",
     "SAT", json.dumps({
         "SolicitaDescargaEmitidos": "CFDIs emitidos",
         "SolicitaDescargaRecibidos": "CFDIs recibidos",
         "SolicitaDescargaFolio": "CFDI por folio especifico",
         "tipos_datos": ["CFDI (XML completo)", "Metadata (solo metadatos)"],
     }, ensure_ascii=False, indent=2))

_add("sat://efirma/requisitos", "Requisitos e.Firma", "application/json",
     "Requisitos para usar e.Firma en servicios del SAT",
     "SAT", json.dumps({
         "archivos": [".cer (certificado)", ".key (llave privada)", "password de llave"],
         "vigencia": "2 anos (e.firma) / 4 anos (e.firma portable)",
         "url_tramite": "https://www.sat.gob.mx/aplicacion/53027/genera-y-descarga-tu-e.firma",
     }, ensure_ascii=False, indent=2))


# === datos.gob.mx Resources (32-39) ===

_add("datosgob://plataforma/info", "Plataforma Nacional de Datos Abiertos", "application/json",
     "Informacion sobre la plataforma datos.gob.mx",
     "datos.gob.mx", json.dumps({
         "url": "https://www.datos.gob.mx",
         "plataforma": "Sistema Ajolote (anteriormente CKAN)",
         "api_compatible": "CKAN API v3",
         "total_datasets": "600+ bases de datos",
         "categorias": ["Salud", "Educacion", "Economia", "Medio ambiente",
                        "Ciencia y tecnologia", "Seguridad", "Transporte"],
     }, ensure_ascii=False, indent=2))

_add("datosgob://api/endpoints", "Endpoints API CKAN", "application/json",
     "Endpoints disponibles de la API CKAN de datos.gob.mx",
     "datos.gob.mx", json.dumps({
         "package_search": "GET /api/3/action/package_search?q={query}",
         "package_show": "GET /api/3/action/package_show?id={id}",
         "organization_list": "GET /api/3/action/organization_list",
         "organization_show": "GET /api/3/action/organization_show?id={id}",
         "group_list": "GET /api/3/action/group_list",
     }, ensure_ascii=False, indent=2))

_add("datosgob://instituciones/lista", "Instituciones Publicadoras", "application/json",
     "Lista de instituciones que publican datos en datos.gob.mx",
     "datos.gob.mx", json.dumps({
         "instituciones": ["INEGI", "SAT", "IMSS", "CFE", "CONAGUA", "SEMARNAT",
                           "SENER", "SE", "PROFECO", "INECC", "IMPI", "INFONAVIT",
                           "Banco de Mexico", "CDMX", "INE", "SSA"],
     }, ensure_ascii=False, indent=2))

_add("datosgob://categorias/lista", "Categorias Tematicas", "application/json",
     "Categorias tematicas disponibles en datos.gob.mx",
     "datos.gob.mx", json.dumps({
         "categorias": ["Salud", "Educacion", "Economia y finanzas",
                        "Medio ambiente", "Ciencia y tecnologia", "Seguridad y justicia",
                        "Transporte y comunicaciones", "Agricultura",
                        "Cultura y deporte", "Turismo", "Gobierno"],
     }, ensure_ascii=False, indent=2))

_add("datosgob://formatos/lista", "Formatos de Datos", "application/json",
     "Formatos de datos disponibles en datos.gob.mx",
     "datos.gob.mx", json.dumps({
         "formatos": ["CSV", "JSON", "XML", "RDF", "XLS", "KML", "GeoJSON", "PDF"],
         "recomendado": "CSV o JSON para procesamiento automatico",
     }, ensure_ascii=False, indent=2))

_add("datosgob://licencias/lista", "Licencias de Uso", "application/json",
     "Licencias aplicables a los datos abiertos del gobierno mexicano",
     "datos.gob.mx", json.dumps({
         "licencia_default": "Datos Abiertos Mexico (libre uso con atribucion)",
         "url_licencia": "https://www.datos.gob.mx/about",
         "restricciones": "Sin restricciones principales (verificar por dataset)",
     }, ensure_ascii=False, indent=2))

_add("datosgob://contrataciones/api", "API de Contrataciones Abiertas", "application/json",
     "API de contrataciones abiertas de la APF",
     "datos.gob.mx", json.dumps({
         "descripcion": "Procedimientos de contratacion de la administracion publica federal",
         "desde": "2017-01-01",
         "url": "https://www.datos.gob.mx/busca/dataset/concentrado-de-contrataciones-abiertas",
     }, ensure_ascii=False, indent=2))

_add("datosgob://plan/apertura", "Planes de Apertura de Datos", "application/json",
     "Informacion sobre planes institucionales de apertura de datos",
     "datos.gob.mx", json.dumps({
         "descripcion": "Cada institucion publica un plan anual de apertura de datos",
         "contenido": "Bases de datos comprometidas, fechas de publicacion, periodicidad",
         "url": "https://www.datos.gob.mx/busca/dataset?q=plan+apertura",
     }, ensure_ascii=False, indent=2))


# === PROFECO Resources (40-45) ===

_add("profeco://qqp/info", "Quien es Quien en los Precios", "application/json",
     "Informacion del programa QQP de PROFECO",
     "PROFECO", json.dumps({
         "url": "https://qqp.profeco.gob.mx",
         "productos": "Alimentos, bebidas, aseo personal, hogar, medicinas, electrodomesticos",
         "funcion": "Comparacion de precios entre tiendas",
     }, ensure_ascii=False, indent=2))

_add("profeco://buenfin/info", "El Buen Fin", "application/json",
     "Informacion sobre ofertas de El Buen Fin verificadas por PROFECO",
     "PROFECO", json.dumps({
         "url": "https://elbuenfin.profeco.gob.mx",
         "periodo": "Noviembre de cada ano",
         "funcion": "Verificacion de precios y ofertas",
     }, ensure_ascii=False, indent=2))

_add("profeco://datos/url", "Portal de Datos Abiertos PROFECO", "application/json",
     "URL y endpoints del portal de datos abiertos de PROFECO",
     "PROFECO", json.dumps({
         "url": "https://datos.profeco.gob.mx",
         "api": "https://datos.profeco.gob.mx/api.php",
     }, ensure_ascii=False, indent=2))

_add("profeco://productos/categorias", "Categorias de Productos QQP", "application/json",
     "Categorias de productos monitoreados por PROFECO",
     "PROFECO", json.dumps({
         "categorias": ["Alimentos basicos", "Bebidas", "Aseo personal",
                        "Aseo del hogar", "Medicinas", "Electrodomesticos",
                        "Articulos de temporada"],
     }, ensure_ascii=False, indent=2))

_add("profeco://tiendas/lista", "Cadenas de Tiendas Monitoreadas", "application/json",
     "Principales cadenas de tiendas monitoreadas por PROFECO",
     "PROFECO", json.dumps({
         "tiendas": ["Walmart", "Soriana", "Chedraui", "Bodega Aurrera",
                     "Superama", "HEB", "Ley", "El Super", "Fresko", "Costco"],
     }, ensure_ascii=False, indent=2))

_add("profeco://denuncias/info", "Portal de Denuncias PROFECO", "application/json",
     "Informacion sobre como presentar denuncias ante PROFECO",
     "PROFECO", json.dumps({
         "telefono": "consumidor.gob.mx",
         "url": "https://www.profeco.gob.mx",
         "tipo_denuncias": "Precios altos, productos caducos, mal servicio",
     }, ensure_ascii=False, indent=2))


# === CDMX Resources (46-51) ===

_add("cdmx://datos/info", "Portal de Datos Abiertos CDMX", "application/json",
     "Informacion del portal de datos abiertos de la Ciudad de Mexico",
     "CDMX", json.dumps({
         "url": "https://datos.cdmx.gob.mx",
         "operador": "Agencia Digital de Innovacion Publica (ADIP)",
         "plataforma": "CKAN",
         "api": "https://datos.cdmx.gob.mx/api/3/action",
     }, ensure_ascii=False, indent=2))

_add("cdmx://seguridad/datasets", "Datasets de Seguridad", "application/json",
     "Datasets de seguridad publica de la CDMX",
     "CDMX", json.dumps({
         "datasets": ["Reportes mensuales de seguridad", "Victimas de delito",
                      "Llamadas de emergencia 911", "Carpetas de investigacion"],
     }, ensure_ascii=False, indent=2))

_add("cdmx://registrocivil/datasets", "Datasets del Registro Civil", "application/json",
     "Datasets del Registro Civil de la CDMX",
     "CDMX", json.dumps({
         "tipos": ["Actas de defuncion", "Actas de nacimiento", "Actas de matrimonio"],
         "formato": "CSV descargable",
     }, ensure_ascii=False, indent=2))

_add("cdmx://presupuesto/datasets", "Datasets de Transparencia Presupuestaria", "application/json",
     "Datasets de presupuesto y gasto de la CDMX",
     "CDMX", json.dumps({
         "contenido": "Presupuesto asignado, ejercicio del gasto, obras publicas",
         "actualizacion": "Mensual / trimestral",
     }, ensure_ascii=False, indent=2))

_add("cdmx://0311/datasets", "Datasets de Solicitudes 0311", "application/json",
     "Datasets del sistema de solicitudes ciudadanas 0311 de la CDMX",
     "CDMX", json.dumps({
         "contenido": "Solicitudes ciudadanas, quejas, reportes de servicios",
         "url_tablero": "https://datos.cdmx.gob.mx",
     }, ensure_ascii=False, indent=2))

_add("cdmx://sig/info", "Sistema de Informacion Geografica CDMX", "application/json",
     "Sistema de informacion geografica de la Ciudad de Mexico",
     "CDMX", json.dumps({
         "contenido": "Mapas, capas geograficas, catastro, servicios publicos",
         "formatos": ["GeoJSON", "KML", "Shapefile"],
     }, ensure_ascii=False, indent=2))


# === IMSS Resources (52-56) ===

_add("imss://datos/info", "Portal de Datos Abiertos IMSS", "application/json",
     "Informacion del portal de datos abiertos del IMSS",
     "IMSS", json.dumps({
         "url": "http://datos.imss.gob.mx",
         "plataforma": "DKAN",
         "api": "http://datos.imss.gob.mx/api/action/datastore/search.json",
     }, ensure_ascii=False, indent=2))

_add("imss://unidades/medicas", "Unidades Medicas en Servicio", "application/json",
     "Informacion sobre unidades medicas del IMSS",
     "IMSS", json.dumps({
         "resource_id": "813b3033-294f-49cc-b242-96932120869e",
         "contenido": "Nombre, delegacion, ubicacion, nivel de atencion",
     }, ensure_ascii=False, indent=2))

_add("imss://salud/datasets", "Datasets de Informacion en Salud", "application/json",
     "Datasets de informacion en salud del IMSS",
     "IMSS", json.dumps({
         "datasets": ["Servicios medicos otorgados", "UMAES",
                      "Planificacion familiar", "Dosis aplicadas",
                      "Deteccion de enfermedades", "Unidades medicas"],
     }, ensure_ascii=False, indent=2))

_add("imss://encuestas/datasets", "Encuestas de Satisfaccion IMSS", "application/json",
     "Encuestas de satisfaccion de usuarios del IMSS",
     "IMSS", json.dumps({
         "encuestas": ["ENSat (servicios medicos)", "Satisfaccion guarderia"],
         "url": "http://datos.imss.gob.mx/groups",
     }, ensure_ascii=False, indent=2))

_add("imss://grupos/lista", "Grupos de Datos IMSS", "application/json",
     "Grupos tematicos de datos disponibles en el IMSS",
     "IMSS", json.dumps({
         "grupos": ["Informacion en Salud", "Servicio de Guarderias",
                    "Encuestas de Satisfaccion", "Salud en el Trabajo",
                    "Leyes y Reglamentos", "Plan Institucional Datos Abiertos"],
     }, ensure_ascii=False, indent=2))


# === CONAGUA Resources (57-61) ===

_add("conagua://datos/info", "Portal de Datos Abiertos CONAGUA", "application/json",
     "Informacion del portal de datos abiertos de CONAGUA",
     "CONAGUA", json.dumps({
         "url": "https://datos.conagua.gob.mx",
         "url_datos": "https://datos.conagua.gob.mx/views/index_datos_abiertos.html",
     }, ensure_ascii=False, indent=2))

_add("conagua://estaciones/tipos", "Tipos de Estaciones CONAGUA", "application/json",
     "Tipos de estaciones de monitoreo de CONAGUA",
     "CONAGUA", json.dumps({
         "tipos": ["Climatologicas convencionales", "Climatologicas automaticas",
                   "Hidrometricas", "Aforos"],
     }, ensure_ascii=False, indent=2))

_add("conagua://disponibilidad/agua", "Disponibilidad de Agua", "application/json",
     "Informacion sobre disponibilidad media anual de agua en Mexico",
     "CONAGUA", json.dumps({
         "norma": "NOM-011-CONAGUA-2015",
         "contenido": "Volumenes de disponibilidad por cuenca hidrologica",
         "variables": "Balance hidrico, recarga, extraccion",
     }, ensure_ascii=False, indent=2))

_add("conagua://smn/avisos", "Avisos del Servicio Meteorologico Nacional", "application/json",
     "Avisos meteorologicos del SMN",
     "CONAGUA", json.dumps({
         "tipos": ["Ciclon tropical", "Lluvias intensas", "Bajas temperaturas",
                   "Ondas calidas", "Sequia"],
         "formato": "RSS / JSON",
         "url": "https://smn.conagua.gob.mx",
     }, ensure_ascii=False, indent=2))

_add("conagua://sinav/info", "Sistema Nacional de Informacion del Agua", "application/json",
     "Informacion del SINAV de CONAGUA",
     "CONAGUA", json.dumps({
         "url": "https://sinav30.conagua.gob.mx:8080",
         "descripcion": "Sistema geoestadistico del sector hidrico",
         "contenido": "Geobases de datos, estadisticas, geografia del agua",
     }, ensure_ascii=False, indent=2))


# === SEMARNAT/INECC Resources (62-66) ===

_add("sinaica://info", "SINAICA - Calidad del Aire", "application/json",
     "Informacion del Sistema Nacional de Informacion de Calidad del Aire",
     "SEMARNAT", json.dumps({
         "url": "https://sinaica.inecc.gob.mx",
         "operador": "INECC (Instituto Nacional de Ecologia y Cambio Climatico)",
         "contaminantes": ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"],
     }, ensure_ascii=False, indent=2))

_add("sinaica://normas", "Normas Oficiales Mexicanas de Calidad del Aire", "application/json",
     "Normas NOM de calidad del aire aplicables",
     "SEMARNAT", json.dumps({
         "NOM_020_SSA_2014": "Ozono (O3)",
         "NOM_023_SSA_1993": "Biouxido de azufre (SO2)",
         "NOM_024_SSA_1993": "Particulas PM10",
         "NOM_025_SSA_2014": "Particulas PM2.5",
         "NOM_021_SSA_1993": "Biouxido de nitrogeno (NO2)",
         "NOM_022_SSA_2010": "Monoxido de carbono (CO)",
     }, ensure_ascii=False, indent=2))

_add("semarnat://mia/info", "Manifestaciones de Impacto Ambiental", "application/json",
     "Informacion sobre Manifestaciones de Impacto Ambiental (MIA)",
     "SEMARNAT", json.dumps({
         "descripcion": "Instrumento de politica ambiental para prevenir, mitigar, restaurar daños",
         "url": "https://www.datos.gob.mx/organization/secretaria_medio_ambiente",
     }, ensure_ascii=False, indent=2))

_add("semarnat://emisiones/info", "Emisiones de Contaminantes", "application/json",
     "Informacion sobre emisiones de contaminantes a la atmosfera",
     "SEMARNAT", json.dumps({
         "fuente": "Chimeneas y conductos de escape industriales, comerciales, residenciales",
         "url": "https://www.datos.gob.mx",
     }, ensure_ascii=False, indent=2))

_add("semarnat://anp/lista", "Areas Naturales Protegidas", "application/json",
     "Areas Naturales Protegidas (ANP) de Mexico",
     "SEMARNAT", json.dumps({
         "total": "182+ ANP federales",
         "categorias": ["Reserva de la Biosfera", "Parque Nacional",
                        "Monumento Natural", "Area de Proteccion de Recursos Naturales",
                        "Area de Proteccion de Flora y Fauna", "Santuario"],
     }, ensure_ascii=False, indent=2))


# === IMPI Resources (67-71) ===

_add("impi://marcanet/info", "MARCANET - Consulta de Marcas", "application/json",
     "Informacion del servicio MARCANET del IMPI",
     "IMPI", json.dumps({
         "url": "https://acervomarcas.impi.gob.mx:8181",
         "busquedas": ["Fonetica", "Por titular", "Por expediente",
                       "Por registro", "Por registro internacional", "Por logotipo"],
         "costo": "Gratuito",
     }, ensure_ascii=False, indent=2))

_add("impi://patentes/libres", "Portal de Tecnologia de Uso Libre", "application/json",
     "Informacion sobre patentes de dominio publico del IMPI",
     "IMPI", json.dumps({
         "url": "https://patenteslibres.impi.gob.mx",
         "descripcion": "Patentes, modelos de utilidad y diseños en dominio publico",
         "uso": "Libre, sin restricciones de patente",
     }, ensure_ascii=False, indent=2))

_add("impi://vidoc/info", "ViDoc - Expedientes Electronicos", "application/json",
     "Portal de visualizacion electronica de documentos de propiedad industrial",
     "IMPI", json.dumps({
         "url": "https://vidoc.impi.gob.mx",
         "funcion": "Consulta y descarga de expedientes publicos",
         "documentos": ["Titulos de marcas", "Titulos de patentes",
                        "Resoluciones", "Escritos"],
     }, ensure_ascii=False, indent=2))

_add("impi://clases/niza", "Clasificacion de Niza", "application/json",
     "Clasificacion Internacional de Niza para marcas (productos y servicios)",
     "IMPI", json.dumps({
         "total_clases": 45,
         "clases_1_34": "Productos",
         "clases_35_45": "Servicios",
         "url": "https://acervomarcas.impi.gob.mx:8181",
     }, ensure_ascii=False, indent=2))

_add("impi://siga/info", "Sistema de Informacion de la Gaceta", "application/json",
     "Portal SIGA - Gaceta de la Propiedad Industrial",
     "IMPI", json.dumps({
         "descripcion": "Publicacion oficial de actos de propiedad industrial",
         "contenido": "Marcas, patentes, modelos de utilidad, diseños industriales",
     }, ensure_ascii=False, indent=2))


# === CFE Resources (72-75) ===

_add("cfe://datos/info", "Datos Abiertos CFE", "application/json",
     "Informacion sobre datos abiertos de la Comision Federal de Electricidad",
     "CFE", json.dumps({
         "url": "https://datos.gob.mx/busca/organization/cfe",
         "total_datasets": "12+ bases de datos",
     }, ensure_ascii=False, indent=2))

_add("cfe://consumo/datasets", "Datasets de Consumo Electrico", "application/json",
     "Datasets de consumo de electricidad de CFE",
     "CFE", json.dumps({
         "datasets": ["Usuarios y consumo por municipio (2018+)",
                      "Usuarios y consumo por municipio (2010-2017)",
                      "Electrificacion por entidad federativa"],
         "formato": "CSV",
     }, ensure_ascii=False, indent=2))

_add("cfe://infraestructura/datasets", "Datasets de Infraestructura Electrica", "application/json",
     "Datasets de infraestructura de transmision y distribucion de CFE",
     "CFE", json.dumps({
         "datasets": ["Lineas instaladas y capacidad de subestaciones",
                      "Generacion bruta por unidad de produccion",
                      "Indice de disponibilidad de transmision"],
     }, ensure_ascii=False, indent=2))

_add("cfe://tarifas/info", "Informacion de Tarifas CFE", "application/json",
     "Informacion sobre tarifas electricas de CFE",
     "CFE", json.dumps({
         "tarifas_residenciales": ["1", "1A", "1B", "1C", "1D", "1E", "1F", "DAC"],
         "tarifas_comerciales": ["GDMTO", "GDMTH", "PDBT"],
         "regulador": "Comision Reguladora de Energia (CRE)",
     }, ensure_ascii=False, indent=2))


# === RPC/SIGER Resources (76-78) ===

_add("rpc://siger/info", "Sistema Integral de Gestion Registral (SIGER 2.0)", "application/json",
     "Informacion del SIGER 2.0 del Registro Publico de Comercio",
     "RPC", json.dumps({
         "url": "https://rpc.economia.gob.mx",
         "descripcion": "Base de datos nacional en tiempo real de sociedades mercantiles",
         "disponibilidad": "24/7",
         "consulta": "Gratuita (consulta publica)",
         "certificacion": "Requiere pago de derechos",
     }, ensure_ascii=False, indent=2))

_add("rpc://consulta/niveles", "Niveles de Consulta RPC", "application/json",
     "Niveles de acceso para consultas del Registro Publico de Comercio",
     "RPC", json.dumps({
         "I": "Consulta general",
         "II": "Consulta por fedatarios publicos",
         "III": "Consulta por instituciones de credito y financieras",
         "IV": "Consulta para usos estadisticos (sin info individualizada)",
         "V": "Otros usos autorizados por la Secretaría de Economia",
     }, ensure_ascii=False, indent=2))

_add("rpc://actos/inscribibles", "Actos Mercantiles Inscribibles", "application/json",
     "Actos que se pueden inscribir en el Registro Publico de Comercio",
     "RPC", json.dumps({
         "actos": ["Constitucion de sociedad", "Transformacion", "Fusion",
                   "Escision", "Disolucion", "Liquidacion",
                   "Nombramiento de administradores", "Poderes",
                   "Emision de obligaciones", "Gravamenes"],
     }, ensure_ascii=False, indent=2))


# === RENAPO/CURP Resources (79-80) ===

_add("renapo://curp/estructura", "Estructura de la CURP", "application/json",
     "Estructura y componentes de la Clave Unica de Registro de Poblacion",
     "RENAPO", json.dumps({
         "estructura": "18 caracteres alfanumericos",
         "componentes": [
             "Pos 1-4: Iniciales de nombre y apellidos",
             "Pos 5-10: Fecha de nacimiento (AAMMDD)",
             "Pos 11: Sexo (H/M)",
             "Pos 12-13: Codigo de entidad federativa",
             "Pos 14-16: Consonantes internas de apellidos y nombre",
             "Pos 17-18: Homoclave y digito verificador",
         ],
         "url_consulta": "https://www.gob.mx/curp",
     }, ensure_ascii=False, indent=2))

_add("renapo://entidades/codigos", "Codigos de Entidad para CURP", "application/json",
     "Catalogo de codigos de entidad federativa usados en la CURP",
     "RENAPO", json.dumps({
         "AS": "Aguascalientes", "BC": "Baja California", "BS": "Baja California Sur",
         "CC": "Campeche", "CL": "Coahuila", "CM": "Colima", "CS": "Chiapas",
         "CH": "Chihuahua", "DF": "Ciudad de Mexico", "DG": "Durango", "GT": "Guanajuato",
         "GR": "Guerrero", "HG": "Hidalgo", "JC": "Jalisco", "MC": "Mexico",
         "MN": "Michoacan", "MS": "Morelos", "NT": "Nayarit", "NL": "Nuevo Leon",
         "OC": "Oaxaca", "PL": "Puebla", "QT": "Queretaro", "QR": "Quintana Roo",
         "SP": "San Luis Potosi", "SL": "Sinaloa", "SR": "Sonora", "TC": "Tabasco",
         "TS": "Tamaulipas", "TL": "Tlaxcala", "VZ": "Veracruz", "YN": "Yucatan",
         "ZS": "Zacatecas", "NE": "Nacido en el Extranjero",
     }, ensure_ascii=False, indent=2))


def get_all_resources() -> list[dict[str, Any]]:
    """Return all registered resources."""
    return RESOURCES


def get_resources_by_category(category: str) -> list[dict[str, Any]]:
    """Filter resources by category."""
    return [r for r in RESOURCES if r["category"] == category]


def get_resource_by_uri(uri: str) -> dict[str, Any] | None:
    """Get a single resource by its URI."""
    for r in RESOURCES:
        if r["uri"] == uri:
            return r
    return None
