"""Resources de solo lectura para mcp-documents."""

from __future__ import annotations

import json


def documents_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-documents",
            "version": "1.0.0",
            "root": ".",
            "max_file_size_mb": 50,
            "max_pages": 200,
        },
        indent=2,
        ensure_ascii=False,
    )


def documents_supported_formats() -> str:
    return (
        "# Formatos Soportados\n\n"
        "## PDF (.pdf)\n"
        "- Extraccion de texto por pagina\n"
        "- Metadata: numero de paginas\n"
        "- Busqueda de texto\n"
        "- Deteccion de imagenes\n\n"
        "## DOCX (.docx)\n"
        "- Extraccion de parrafos\n"
        "- Extraccion de tablas\n"
        "- Metadata: parrafos y tablas\n"
        "- Deteccion de imagenes\n\n"
        "## PPTX (.pptx)\n"
        "- Extraccion de texto por slide\n"
        "- Metadata: numero de slides\n"
        "- Deteccion de imagenes\n\n"
        "## Limitaciones\n"
        "- No soporta XLSX\n"
        "- No soporta ODT/ODP\n"
        "- No extrae imagenes binarias\n"
        "- Texto escaneado (OCR) no soportado"
    )


def documents_best_practices() -> str:
    return (
        "# Best Practices - Document Processing\n\n"
        "## Seguridad\n"
        "- Validar path dentro de DOCUMENTS_ROOT\n"
        "- Limitar tamano maximo de archivo\n"
        "- Limitar numero de paginas\n"
        "- No ejecutar macros de Office\n\n"
        "## Performance\n"
        "- Usar batch_extract para multiples archivos\n"
        "- Limitar max_pages para documentos grandes\n"
        "- Cache de resultados cuando sea posible\n"
        "- Procesar async para grandes volumenes\n\n"
        "## Calidad\n"
        "- Validar documentos antes de procesar\n"
        "- Manejar errores por archivo individual\n"
        "- Logging de extracciones\n"
        "- Verificar texto extraido (no vacio)"
    )


def documents_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- documents_extract(path)\n"
        "- documents_metadata(path)\n"
        "- documents_list(directory)\n"
        "- documents_search(path, query)\n"
        "- documents_count_pages(path)\n"
        "- documents_extract_text(path)\n"
        "- documents_summary(path)\n"
        "- documents_to_markdown(path)\n"
        "- documents_batch_extract(directory)\n"
        "- documents_stats(directory)\n"
        "- documents_validate(path)\n"
        "- documents_extract_tables(path)\n"
        "- documents_images_info(path)\n"
        "- documents_compare(path_a, path_b)\n"
        "- documents_export_text(path)\n\n"
        "## Variables .env\n"
        "- DOCUMENTS_ROOT\n"
        "- DOCUMENTS_MAX_FILE_SIZE_MB\n"
        "- DOCUMENTS_MAX_PAGES"
    )


def documents_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "ValidationError: campo invalido"},
                {"code": -32002, "description": "Documento fuera de DOCUMENTS_ROOT"},
                {"code": -32003, "description": "Formato no soportado"},
                {"code": -32004, "description": "Archivo demasiado grande"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def documents_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## No se puede extraer texto\n"
        "- Verificar que el archivo existe\n"
        "- Verificar formato soportado (PDF, DOCX, PPTX)\n"
        "- Verificar tamano del archivo\n"
        "- PDFs escaneados no tienen texto extraible\n\n"
        "## Texto vacio\n"
        "- PDF puede ser escaneado (necesita OCR)\n"
        "- DOCX puede tener solo imagenes\n"
        "- PPTX puede tener texto en notas\n\n"
        "## Error de path\n"
        "- Verificar DOCUMENTS_ROOT\n"
        "- Path debe ser relativo a DOCUMENTS_ROOT\n"
        "- No usar .. para salir del root\n\n"
        "## Archivo muy grande\n"
        "- Aumentar DOCUMENTS_MAX_FILE_SIZE_MB\n"
        "- Reducir DOCUMENTS_MAX_PAGES\n"
        "- Usar batch_extract con directorios especificos"
    )


def documents_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Extraer documento\n"
        'documents_extract(path="reports/quarterly.pdf")\n\n'
        "## Metadata\n"
        'documents_metadata(path="docs/manual.docx")\n\n'
        "## Listar documentos\n"
        'documents_list(directory="reports")\n\n'
        "## Buscar texto\n"
        'documents_search(path="docs/guide.pdf", query="budget")\n\n'
        "## Convertir a Markdown\n"
        'documents_to_markdown(path="slides/presentation.pptx")\n\n'
        "## Comparar documentos\n"
        'documents_compare(path_a="v1.docx", path_b="v2.docx")'
    )


def documents_pdf_guide() -> str:
    return (
        "# PDF Processing Guide\n\n"
        "## Extraccion de texto\n"
        "- pypdf: extraccion basica\n"
        "- pdfplumber: mejor para tablas\n"
        "- PyMuPDF: mas rapido y completo\n"
        "- pdfminer.six: bajo nivel\n\n"
        "## Tipos de PDF\n"
        "- Texto nativo: extraible directamente\n"
        "- PDF escaneado: necesita OCR (tesseract)\n"
        "- PDF con formularios: campos interactivos\n"
        "- PDF protegido: necesita password\n\n"
        "## Metadata PDF\n"
        "- Titulo, autor, asunto\n"
        "- Fecha de creacion\n"
        "- Numero de paginas\n"
        "- Tamano de pagina\n"
        "- Version de PDF\n\n"
        "## Limitaciones\n"
        "- Texto en imagenes no extraible\n"
        "- Layout complejo puede perder formato\n"
        "- Fuentes embebidas pueden causar problemas"
    )


def documents_docx_guide() -> str:
    return (
        "# DOCX Processing Guide\n\n"
        "## Estructura DOCX\n"
        "- Documento XML (word/document.xml)\n"
        "- Parrafos con estilos\n"
        "- Tablas con celdas\n"
        "- Imagenes embebidas\n"
        "- Headers y footers\n\n"
        "## Extraccion\n"
        "- python-docx: parrafos y tablas\n"
        "- Estilos: heading, normal, list\n"
        "- Relaciones: imagenes, hyperlinks\n"
        "- Secciones: page breaks\n\n"
        "## Operaciones\n"
        "- Extraer parrafos con estilo\n"
        "- Extraer tablas como matrices\n"
        "- Contar imagenes\n"
        "- Obtener headers/footers\n\n"
        "## Limitaciones\n"
        "- No extrae imagenes binarias\n"
        "- No soporta comentarios\n"
        "- No soporta control de cambios\n"
        "- Macros no soportadas"
    )


def documents_pptx_guide() -> str:
    return (
        "# PPTX Processing Guide\n\n"
        "## Estructura PPTX\n"
        "- Slides con shapes\n"
        "- Texto en text frames\n"
        "- Imagenes embebidas\n"
        "- Notas del orador\n"
        "- Animaciones (no extraibles)\n\n"
        "## Extraccion\n"
        "- python-pptx: slides y shapes\n"
        "- Texto por slide\n"
        "- Tablas en slides\n"
        "- Contar imagenes\n\n"
        "## Operaciones\n"
        "- Extraer texto por slide\n"
        "- Contar slides\n"
        "- Detectar imagenes\n"
        "- Obtener notas del orador\n\n"
        "## Limitaciones\n"
        "- No extrae imagenes binarias\n"
        "- No soporta animaciones\n"
        "- No soporta transiciones\n"
        "- Graficos no extraibles como datos"
    )


def documents_ocr_guide() -> str:
    return (
        "# OCR Guide (Referencia)\n\n"
        "## Cuando usar OCR\n"
        "- PDFs escaneados\n"
        "- Imagenes con texto\n"
        "- Documentos sin texto nativo\n\n"
        "## Tools de OCR\n"
        "- Tesseract: open source, multi-idioma\n"
        "- AWS Textract: cloud, alto rendimiento\n"
        "- Google Vision: cloud, alta precision\n"
        "- Azure Computer Vision: cloud\n\n"
        "## Configuracion Tesseract\n"
        "```bash\n"
        "pip install pytesseract\n"
        "# Instalar tesseract-ocr del sistema\n"
        "```\n\n"
        "## Flujo recomendado\n"
        "1. Intentar extraccion nativa\n"
        "2. Si texto vacio, usar OCR\n"
        "3. Post-procesar texto OCR\n"
        "4. Validar calidad del texto"
    )


def documents_security() -> str:
    return (
        "# Document Security\n\n"
        "## Path Traversal\n"
        "- Validar path dentro de DOCUMENTS_ROOT\n"
        "- Usar resolve() y is_relative_to()\n"
        "- Rechazar .. en paths\n"
        "- No permitir paths absolutos fuera de root\n\n"
        "## File Validation\n"
        "- Verificar extension soportada\n"
        "- Limitar tamano maximo\n"
        "- Verificar magic bytes\n"
        "- No ejecutar macros\n\n"
        "## Privacy\n"
        "- No loguear contenido de documentos\n"
        "- PII detection en texto extraido\n"
        "- Redaccion de informacion sensible\n"
        "- Acceso basado en roles\n\n"
        "## Malware\n"
        "- Escanear archivos antes de procesar\n"
        "- Usar sandbox para procesamiento\n"
        "- Limitar recursos (CPU, memoria)\n"
        "- Timeout en extraccion"
    )


def documents_batch_processing() -> str:
    return (
        "# Batch Processing\n\n"
        "## Estrategias\n"
        "- Procesar por directorio\n"
        "- Paralelismo con multiprocessing\n"
        "- Queue para grandes volumenes\n"
        "- Progress tracking\n\n"
        "## Configuracion\n"
        "- Limitar archivos por batch\n"
        "- Timeout por archivo\n"
        "- Error handling individual\n"
        "- Resume desde ultimo procesado\n\n"
        "## Output\n"
        "- JSON estructurado por archivo\n"
        "- CSV para reportes\n"
        "- Markdown para documentacion\n"
        "- SQLite para busquedas\n\n"
        "## Optimizacion\n"
        "- Cache de resultados\n"
        "- Lazy loading de documentos\n"
        "- Streaming para archivos grandes\n"
        "- Index de texto extraido"
    )


def documents_text_analysis() -> str:
    return (
        "# Text Analysis\n\n"
        "## Metricas basicas\n"
        "- Conteo de palabras\n"
        "- Conteo de lineas\n"
        "- Conteo de caracteres\n"
        "- Densidad de palabras clave\n\n"
        "## Analisis avanzado\n"
        "- Frecuencia de palabras\n"
        "- Extraccion de entidades (NER)\n"
        "- Sentiment analysis\n"
        "- Topic modeling\n"
        "- Resumen automatico\n\n"
        "## Tools Python\n"
        "- nltk: NLP basico\n"
        "- spaCy: NLP avanzado\n"
        "- transformers: modelos pre-entrenados\n"
        "- sumy: resumen automatico\n\n"
        "## Aplicaciones\n"
        "- Clasificacion de documentos\n"
        "- Busqueda semantica\n"
        "- Deteccion de duplicados\n"
        "- Extraccion de informacion"
    )


def documents_conversion() -> str:
    return (
        "# Document Conversion\n\n"
        "## Formatos de salida\n"
        "- Markdown: texto estructurado\n"
        "- HTML: con formato\n"
        "- JSON: estructurado\n"
        "- CSV: para tablas\n"
        "- TXT: texto plano\n\n"
        "## Conversiones comunes\n"
        "- PDF -> Markdown: paginas como secciones\n"
        "- DOCX -> Markdown: parrafos y tablas\n"
        "- PPTX -> Markdown: slides como secciones\n"
        "- Cualquiera -> TXT: texto plano\n\n"
        "## Tools\n"
        "- pandoc: conversion universal\n"
        "- libreoffice: conversion Office\n"
        "- markitdown: Microsoft, Markdown\n"
        "- Custom: Python + librerias\n\n"
        "## Consideraciones\n"
        "- Formato puede perderse\n"
        "- Imagenes no se convierten\n"
        "- Tablas pueden desalinearse\n"
        "- Headers/footers pueden perderse"
    )
