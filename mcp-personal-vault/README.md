# mcp-personal-vault

Boveda local cifrada para que clientes MCP consulten contexto personal relevante
sin guardar la informacion en el repositorio.

## Que guardar

- `profile`: nombre preferido, idiomas, zona horaria.
- `preferences`: herramientas, estilos de comunicacion, formatos favoritos.
- `career`: experiencia, habilidades, objetivos profesionales.
- `projects`: intereses, responsabilidades y contexto no secreto.
- `contacts`: relaciones y datos de contacto autorizados.
- `health`: preferencias o contexto necesario, marcado `highly_sensitive`.
- `finance`: objetivos o reglas generales, nunca credenciales ni numeros completos.

No almacenes passwords, tokens, PIN, CVV, frases semilla ni llaves privadas.
Para eso usa un gestor de secretos dedicado.

## Niveles

- `public`: contexto que puede revelarse normalmente.
- `private`: contexto personal cifrado, visible en consultas normales.
- `highly_sensitive`: permanece redactado salvo que la configuracion y la llamada
  autoricen su acceso explicitamente.

## Ejecucion local

```powershell
uv --directory mcp-personal-vault run python -m mcp_personal_vault.server
```

La configuracion incluida para Claude Desktop escribe en:

```text
data/personal-vault/personal.db
data/personal-vault/vault.key
```

Ambos quedan fuera de Git mediante la regla `data/`.

## Docker

```powershell
docker compose --profile personal up -d mcp-personal-vault
```

El puerto HTTP es `127.0.0.1:8035` y el volumen es local.
