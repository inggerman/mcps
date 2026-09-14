"""Tools para leer formatos de datos COVAF.

Soporta: PDF, Excel, Word, XML, JSON, JSON-PDF, JSON-Word, XML-Short.
Las tools leen archivos locales o parsean contenido pasado como string.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from defusedxml import ElementTree as DefusedElementTree
from mcp_shared.errors import McpError

# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def read_pdf(file_path: str, max_pages: int = 50) -> dict[str, Any]:
    """Lee un PDF y extrae texto plano por página.

    Usa pdfplumber si está disponible, sino intenta pymupdf, sino lee el binario.
    """
    p = Path(file_path)
    if not p.exists():
        raise McpError(f"Archivo no encontrado: {file_path}")
    if p.suffix.lower() != ".pdf":
        raise McpError(f"El archivo no es PDF: {file_path}")
    pages: list[dict[str, Any]] = []
    # Intentar pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(p) as pdf:
            for i, page in enumerate(pdf.pages[:max_pages]):
                text = page.extract_text() or ""
                pages.append({"page": i + 1, "text": text, "chars": len(text)})
        return {"file": file_path, "pages": pages, "page_count": len(pages), "parser": "pdfplumber"}
    except ImportError:
        pass
    # Intentar pymupdf
    try:
        import fitz  # type: ignore[import-not-found]
        doc = fitz.open(str(p))
        for i in range(min(doc.page_count, max_pages)):
            page = doc[i]
            text = page.get_text()
            pages.append({"page": i + 1, "text": text, "chars": len(text)})
        doc.close()
        return {"file": file_path, "pages": pages, "page_count": len(pages), "parser": "pymupdf"}
    except ImportError:
        pass
    return {
        "file": file_path,
        "pages": [],
        "page_count": 0,
        "parser": "none_available",
        "error": "Instala pdfplumber o pymupdf para leer PDFs",
    }


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------

def read_excel(file_path: str, sheet_name: str | None = None, max_rows: int = 100) -> dict[str, Any]:
    """Lee un archivo Excel (.xlsx) y devuelve filas como diccionarios."""
    p = Path(file_path)
    if not p.exists():
        raise McpError(f"Archivo no encontrado: {file_path}")
    try:
        import openpyxl
    except ImportError as exc:
        raise McpError("openpyxl no instalado — instala para leer Excel") from exc
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    sheets = wb.sheetnames
    target = sheet_name if sheet_name else sheets[0]
    if target not in sheets:
        raise McpError(f"Hoja no encontrada: {target}. Disponibles: {sheets}")
    ws = wb[target]
    rows: list[dict[str, Any]] = []
    headers: list[str] = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i >= max_rows:
            break
        if i == 0:
            headers = [str(c) if c is not None else f"col_{j}" for j, c in enumerate(row)]
            continue
        row_dict = {headers[j]: row[j] for j in range(len(headers)) if j < len(row)}
        rows.append(row_dict)
    wb.close()
    return {
        "file": file_path,
        "sheet": target,
        "sheets_available": sheets,
        "headers": headers,
        "rows": rows,
        "row_count": len(rows),
    }


# ---------------------------------------------------------------------------
# Word (.doc / .docx)
# ---------------------------------------------------------------------------

def read_word(file_path: str) -> dict[str, Any]:
    """Lee un documento Word (.docx) y extrae texto, tablas y propiedades."""
    p = Path(file_path)
    if not p.exists():
        raise McpError(f"Archivo no encontrado: {file_path}")
    if p.suffix.lower() not in (".doc", ".docx"):
        raise McpError(f"El archivo no es Word: {file_path}")
    # .docx es un ZIP
    if p.suffix.lower() == ".docx":
        return _read_docx(p)
    # .doc (binario) — solo metadatos básicos
    return {
        "file": file_path,
        "format": "doc",
        "note": "Formato .doc binario no soportado directamente. Convierte a .docx.",
    }


def _read_docx(p: Path) -> dict[str, Any]:
    """Lee .docx (ZIP con XML interno)."""
    try:
        zf = zipfile.ZipFile(p)
        # Documento principal
        doc_xml = zf.read("word/document.xml")
        root = DefusedElementTree.fromstring(doc_xml)
        paragraphs: list[str] = []
        for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
            texts = [t.text for t in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if t.text]
            if texts:
                paragraphs.append("".join(texts))
        # Propiedades del documento (core.xml)
        props: dict[str, str] = {}
        try:
            core_xml = zf.read("docProps/core.xml")
            core_root = DefusedElementTree.fromstring(core_xml)
            for child in core_root:
                tag = child.tag.split("}")[-1]
                props[tag] = child.text or ""
        except KeyError:
            pass
        # Propiedades custom (custom.xml)
        custom_props: dict[str, str] = {}
        try:
            custom_xml = zf.read("docProps/custom.xml")
            custom_root = DefusedElementTree.fromstring(custom_xml)
            for prop in custom_root:
                name = prop.attrib.get("name", "")
                value_elem = prop.find("{http://schemas.openxmlformats.org/officeDocument/2006/custom-properties}vt")
                if value_elem is not None and value_elem.text:
                    custom_props[name] = value_elem.text
        except KeyError:
            pass
        zf.close()
        return {
            "file": str(p),
            "format": "docx",
            "paragraphs": paragraphs,
            "paragraph_count": len(paragraphs),
            "full_text": "\n".join(paragraphs),
            "core_properties": props,
            "custom_properties": custom_props,
        }
    except (zipfile.BadZipFile, KeyError) as exc:
        raise McpError(f"Error leyendo .docx: {exc}") from exc


# ---------------------------------------------------------------------------
# XML
# ---------------------------------------------------------------------------

def read_xml(file_path: str) -> dict[str, Any]:
    """Lee un archivo XML y lo convierte a diccionario."""
    p = Path(file_path)
    if not p.exists():
        raise McpError(f"Archivo no encontrado: {file_path}")
    try:
        tree = DefusedElementTree.parse(p)
        root = tree.getroot()
        return {
            "file": file_path,
            "root_tag": root.tag,
            "data": _xml_to_dict(root),
        }
    except ElementTree.ParseError as exc:
        raise McpError(f"XML inválido: {exc}") from exc


def _xml_to_dict(elem: ElementTree.Element) -> Any:
    """Convierte un Element XML a diccionario recursivamente."""
    children = list(elem)
    if not children:
        return elem.text or ""
    result: dict[str, Any] = {}
    for child in children:
        tag = child.tag.split("}")[-1]  # quitar namespace
        child_data = _xml_to_dict(child)
        if tag in result:
            if isinstance(result[tag], list):
                result[tag].append(child_data)
            else:
                result[tag] = [result[tag], child_data]
        else:
            result[tag] = child_data
    # Atributos
    for k, v in elem.attrib.items():
        result[f"@{k.split('}')[-1]}"] = v
    return result


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def read_json(file_path: str) -> dict[str, Any]:
    """Lee un archivo JSON."""
    p = Path(file_path)
    if not p.exists():
        raise McpError(f"Archivo no encontrado: {file_path}")
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        return {"file": file_path, "data": json.loads(text)}
    except json.JSONDecodeError as exc:
        raise McpError(f"JSON inválido: {exc}") from exc
    except OSError as exc:
        raise McpError(f"Error leyendo archivo: {exc}") from exc


# ---------------------------------------------------------------------------
# JSON-PDF (OCR output)
# ---------------------------------------------------------------------------

def read_jsonpdf(file_path: str) -> dict[str, Any]:
    """Lee un JSON-PDF (salida de OCR) y lo normaliza al formato COVAF.

    Soporta 4 formatos:
    - Formato 1 (nuevo): array de documentos
    - Formato 2 (viejo): objeto con claves por institución
    - Formato 3 (simple): documento directo
    - Formato 0 (Textract crudo): lista plana de bloques
    """
    p = Path(file_path)
    if not p.exists():
        raise McpError(f"Archivo no encontrado: {file_path}")
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise McpError(f"JSON inválido: {exc}") from exc
    return _normalize_jsonpdf(raw, file_path)


def _normalize_jsonpdf(raw: Any, file_path: str) -> dict[str, Any]:
    """Normaliza cualquier formato de JSON-PDF al formato canónico COVAF."""
    documents: list[dict[str, Any]] = []
    # Formato 1: array de documentos
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict) and "documento" in raw[0]:
            documents = raw
            fmt = "array_documents"
        elif raw and isinstance(raw[0], dict) and "BlockType" in raw[0]:
            # Formato 0: Textract crudo
            documents = _textract_blocks_to_doc(raw)
            fmt = "textract_raw"
        else:
            documents = [{"documento": {"contenido": str(raw)}}]
            fmt = "array_generic"
    # Formato 2: objeto con claves por institución
    elif isinstance(raw, dict):
        if "documento" in raw:
            # Formato 3: documento directo
            documents = [raw]
            fmt = "single_document"
        else:
            # Formato 2: claves por institución
            for key, val in raw.items():
                if isinstance(val, dict):
                    doc = dict(val)
                    doc.setdefault("institution", key)
                    documents.append(doc)
            fmt = "by_institution"
    else:
        documents = [{"documento": {"contenido": str(raw)}}]
        fmt = "unknown"
    # Normalizar cada documento
    normalized: list[dict[str, Any]] = []
    for doc in documents:
        ndoc = _normalize_single_jsonpdf_doc(doc)
        normalized.append(ndoc)
    return {
        "file": file_path,
        "format_detected": fmt,
        "document_count": len(normalized),
        "documents": normalized,
    }


def _normalize_single_jsonpdf_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Normaliza un documento JSON-PDF individual."""
    result: dict[str, Any] = {
        "metadata": {},
        "documento": {"contenido": "", "tablas": [], "formularios": []},
    }
    # Metadata
    for k in ["uuidDocumento", "uuidLayout", "layout", "institution", "formato"]:
        if k in doc:
            result["metadata"][k] = doc[k]
    # Rango de páginas
    if "rangoPaginas" in doc:
        result["metadata"]["rangoPaginas"] = doc["rangoPaginas"]
    # Documento
    doc_data = doc.get("documento", {})
    if isinstance(doc_data, dict):
        result["documento"]["contenido"] = doc_data.get("contenido", "")
        result["documento"]["tablas"] = doc_data.get("tablas", [])
        result["documento"]["formularios"] = doc_data.get("formularios", [])
    elif isinstance(doc_data, str):
        result["documento"]["contenido"] = doc_data
    # Si el contenido está al nivel superior
    if "contenido" in doc and not result["documento"]["contenido"]:
        result["documento"]["contenido"] = doc["contenido"]
    if "tablas" in doc:
        result["documento"]["tablas"] = doc["tablas"]
    if "formularios" in doc:
        result["documento"]["formularios"] = doc["formularios"]
    return result


def _textract_blocks_to_doc(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convierte bloques Textract crudos al formato canónico."""
    lines: list[str] = []
    for block in blocks:
        if block.get("BlockType") == "LINE":
            lines.append(block.get("Text", ""))
    return [{"documento": {"contenido": "\n".join(lines), "tablas": [], "formularios": []}}]


# ---------------------------------------------------------------------------
# JSON-Word (mismo formato que JSON-PDF)
# ---------------------------------------------------------------------------

def read_jsonword(file_path: str) -> dict[str, Any]:
    """Lee un JSON-Word (representación JSON de un Word).

    Usa el mismo parser que JSON-PDF porque el esquema interno es idéntico.
    """
    result = read_jsonpdf(file_path)
    result["format_source"] = "jsonword"
    return result


# ---------------------------------------------------------------------------
# XML-Short (SITIAA)
# ---------------------------------------------------------------------------

def read_xmlshort(file_path: str, folio_id: str | None = None) -> dict[str, Any]:
    """Lee un XML-Short de SITIAA y lo convierte a Map<String,String>.

    Si el XML contiene múltiples <RequerimientoDescargado>, selecciona el
    registro cuyo <IdFolio> coincida con folio_id.
    """
    p = Path(file_path)
    if not p.exists():
        raise McpError(f"Archivo no encontrado: {file_path}")
    try:
        tree = DefusedElementTree.parse(p)
        root = tree.getroot()
    except ElementTree.ParseError as exc:
        raise McpError(f"XML inválido: {exc}") from exc
    # Buscar todos los <RequerimientoDescargado>
    requerimientos = root.findall(".//RequerimientoDescargado")
    if not requerimientos:
        # Si no hay, intentar con el root mismo
        requerimientos = [root]
    records: list[dict[str, str]] = []
    for req in requerimientos:
        record: dict[str, str] = {}
        for child in req:
            tag = child.tag.split("}")[-1]
            record[tag] = child.text or ""
        records.append(record)
    # Seleccionar por folio si se especifica
    selected = records
    if folio_id and len(records) > 1:
        matched = [r for r in records if r.get("IdFolio") == folio_id]
        selected = matched if matched else []
    return {
        "file": file_path,
        "folio_id": folio_id,
        "record_count": len(records),
        "selected_count": len(selected),
        "records": records,
        "selected": selected[0] if selected else {},
    }


# ---------------------------------------------------------------------------
# Parse S3 path
# ---------------------------------------------------------------------------

def parse_s3_path(s3_uri: str) -> dict[str, Any]:
    """Parsea una URI de S3 (s3://bucket/path) en sus componentes."""
    if not s3_uri.startswith("s3://"):
        raise McpError(f"No es una URI S3 válida: {s3_uri}")
    rest = s3_uri[5:]
    parts = rest.split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""
    # Detectar tipo de archivo por extensión
    ext = Path(key).suffix.lower() if key else ""
    file_type = _detect_file_type(key, ext)
    return {
        "uri": s3_uri,
        "bucket": bucket,
        "key": key,
        "extension": ext,
        "file_type": file_type,
    }


def _detect_file_type(key: str, ext: str) -> str:
    """Detecta el tipo de archivo COVAF por nombre/extension."""
    name = key.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in (".xlsx", ".xls"):
        return "excel"
    if ext in (".doc", ".docx"):
        return "word"
    if ext == ".xml":
        if "short" in name:
            return "xml_short"
        if "full" in name or "sitiaa" in name:
            return "xml_full"
        return "xml_full"
    if ext == ".json":
        if "jsonpdf" in name or "json_pdf" in name or "_limpio_salida" in name:
            return "json_pdf"
        if "jsonword" in name or "json_word" in name:
            return "json_word"
        if "jsonpantalla" in name or "json_pantalla" in name:
            return "json_pantalla"
        return "json"
    return "unknown"


# ---------------------------------------------------------------------------
# List extraction sources from folio request
# ---------------------------------------------------------------------------

def list_extraction_sources(folio_json: str) -> dict[str, Any]:
    """Lista las fuentes de extracción disponibles en un folio de request.

    Recibe el JSON de un folio (OficiosFolioDto) y lista qué fuentes tiene.
    """
    try:
        folio = json.loads(folio_json)
    except json.JSONDecodeError as exc:
        raise McpError(f"JSON inválido: {exc}") from exc
    sources: list[dict[str, Any]] = []
    field_map = {
        "xml": ("XML_FULL", "XML completo CNBV"),
        "word": ("WORD", "Documento Word (.doc/.docx)"),
        "jsonPdf": ("JSON_PDF", "JSON-PDF (salida OCR)"),
        "jsonWord": ("JSON_WORD", "JSON-Word (v5.0.0)"),
        "jsonPantalla": ("JSON_PAGE", "JSON pantalla"),
        "xmlShort": ("XML_SHORT", "XML corto SITIAA"),
    }
    for field, (source_type, desc) in field_map.items():
        val = folio.get(field)
        if val:
            parsed = parse_s3_path(val) if val.startswith("s3://") else {"path": val}
            sources.append({
                "field": field,
                "source_type": source_type,
                "description": desc,
                "s3_uri": val,
                "parsed": parsed,
            })
    # Determinar config type
    tiene_xml = folio.get("tengoXml", "false") == "true"
    tiene_jsonword = bool(folio.get("jsonWord"))
    if tiene_xml:
        config_type = "XML_FULL"
    elif tiene_jsonword:
        config_type = "XML_SHORT_JSON_WORD"
    else:
        config_type = "XML_SHORT_WORD"
    return {
        "folio_id": folio.get("folioId", ""),
        "tengo_xml": tiene_xml,
        "config_type": config_type,
        "sources": sources,
        "source_count": len(sources),
    }
