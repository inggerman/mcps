# Estado del proyecto

Actualizado: 13 de junio de 2026.

## Estado general

El workspace contiene ocho servidores FastMCP operativos:

| Servidor | Puerto HTTP | Tools |
|---|---:|---:|
| `mcp-tabular` | 8001 | 8 |
| `mcp-calendar` | 8002 | 15 |
| `mcp-markdown` | 8003 | 12 |
| `mcp-prompt-engineer` | 8004 | 8 |
| `mcp-structured-output` | 8005 | 4 |
| `mcp-fetch` | 8006 | 4 |
| `mcp-docker` | 8007 | 8 |
| `mcp-kafka` | 8008 | 6 |

Todos soportan `stdio` y `streamable-http`. El workspace, los Dockerfiles,
Compose y la configuración de Claude Desktop solo referencian paquetes
existentes.

## Verificación

- `uv run pytest -q`: 217 pruebas aprobadas.
- Cobertura total: 62.59%; umbral exigido: 55%.
- Ruff format y lint: aprobados.
- mypy: aprobado en 46 archivos fuente.
- Compose normal y con perfil `privileged-tools`: configuración válida.
- El build de imágenes requiere que Docker Desktop esté iniciado.

## Seguridad operativa

- Compose publica los puertos únicamente en `127.0.0.1`.
- `mcp-docker` requiere el perfil `privileged-tools`; el socket Docker concede
  control efectivo sobre el daemon incluso montado como `ro`.
- `mcp-fetch` bloquea destinos no públicos y credenciales embebidas por defecto.
- Las redirecciones de Fetch están desactivadas por defecto.
- En Docker, Tabular y Markdown restringen acceso al volumen `/data`.
- Los errores inesperados no devuelven detalles de excepciones al cliente.
- Structured Output valida el JSON recibido contra el schema solicitado.

## Decisiones vigentes

1. FastMCP standalone `>=2.3` es el framework común.
2. `MCP_TRANSPORT` selecciona `stdio` o `streamable-http`.
3. La lógica de negocio vive en `tools/`; `server.py` registra tools y traduce
   errores al protocolo MCP.
4. `mcp_shared` centraliza configuración base, errores, logging y modelos.
5. Los healthchecks de Compose son TCP porque FastMCP no expone `/health`.
6. Frankfurter es el único proveedor de divisas implementado.

## Comandos de trabajo

```bash
uv sync --all-packages
uv run pytest -q
uv run ruff format --check .
uv run ruff check .
make lint
docker compose up -d
docker compose --profile privileged-tools up -d mcp-docker
```

## Pendientes reales

- Ejecutar `docker compose build` con Docker Desktop activo.
- Añadir autenticación delante de `streamable-http` antes de publicar cualquier
  servidor fuera de localhost.
- Incrementar cobertura en los adaptadores externos de Calendar y Structured
  Output.
