"""Resources de solo lectura para mcp-docker."""

from __future__ import annotations

import json


def docker_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-docker",
            "docker_host": "default (unix:///var/run/docker.sock)",
            "log_lines": 100,
            "exec_timeout": 30,
        },
        indent=2,
        ensure_ascii=False,
    )


def docker_container_statuses() -> str:
    return (
        "# Estados de contenedores Docker\n\n"
        "| Estado | Descripcion |\n"
        "|--------|-------------|\n"
        "| created | Creado pero no iniciado |\n"
        "| running | En ejecucion |\n"
        "| paused | Pausado |\n"
        "| restarting | Reiniciando |\n"
        "| exited | Detenido |\n"
        "| dead | Muerto (error) |"
    )


def docker_image_reference() -> str:
    return (
        "# Referencia de imagenes Docker\n\n"
        "## Formato\n"
        "`[registry/]repository[:tag]`\n\n"
        "## Ejemplos\n"
        "- `nginx:latest`\n"
        "- `python:3.12-slim`\n"
        "- `ghcr.io/owner/repo:v1.0`\n"
        "- `123456789.dkr.ecr.us-east-1.amazonaws.com/app:prod`\n\n"
        "## Comandos\n"
        "- `images_list` — listar imagenes locales\n"
        "- `image_pull` — descargar desde registry\n"
        "- `image_remove` — eliminar imagen local\n"
        "- `image_inspect` — inspeccionar imagen"
    )


def docker_run_guide() -> str:
    return (
        "# Guia: run_container\n\n"
        "## Parametros principales\n"
        "- `image` (requerido): Imagen a usar\n"
        "- `name`: Nombre del contenedor\n"
        "- `detach`: True = background (default)\n"
        "- `ports`: Mapeo {container: host}\n"
        "- `environment`: Variables de entorno\n"
        "- `volumes`: Montaje de volumenes\n"
        "- `remove_on_exit`: Eliminar al terminar\n\n"
        "## Ejemplo\n"
        "```\n"
        "run_container(\n"
        "    image='nginx:latest',\n"
        "    name='web-server',\n"
        "    ports={'80': '8080'},\n"
        "    environment={'NGINX_HOST': 'localhost'}\n"
        ")\n"
        "```"
    )


def docker_logs_guide() -> str:
    return (
        "# Guia: container_logs\n\n"
        "## Parametros\n"
        "- `container_id` (requerido): ID o nombre\n"
        "- `lines`: Numero de lineas (default 100)\n"
        "- `since`: Desde cuando ('1h', '30m', o timestamp)\n"
        "- `timestamps`: Incluir timestamps\n\n"
        "## Ejemplo\n"
        "```\n"
        "container_logs(\n"
        "    container_id='web-server',\n"
        "    lines=50,\n"
        "    since='1h',\n"
        "    timestamps=True\n"
        ")\n"
        "```"
    )


def docker_exec_guide() -> str:
    return (
        "# Guia: container_exec\n\n"
        "Ejecuta comandos dentro de un contenedor en ejecucion.\n\n"
        "## Parametros\n"
        "- `container_id` (requerido): ID o nombre\n"
        "- `command` (requerido): Comando a ejecutar\n"
        "- `workdir`: Directorio de trabajo\n"
        "- `user`: Usuario (ej: 'root')\n"
        "- `environment`: Variables adicionales\n\n"
        "## Ejemplo\n"
        "```\n"
        "container_exec(\n"
        "    container_id='web-server',\n"
        "    command='ls -la /app',\n"
        "    user='root'\n"
        ")\n"
        "```\n\n"
        "## Notas\n"
        "- El contenedor debe estar en estado 'running'\n"
        "- Timeout por defecto: 30 segundos"
    )


def docker_stats_guide() -> str:
    return (
        "# Guia: containers_stats\n\n"
        "Obtiene metricas de uso de recursos de un contenedor.\n\n"
        "## Metricas retornadas\n"
        "- `cpu_percent`: Uso de CPU (%)\n"
        "- `memory_mb`: Memoria usada (MB)\n"
        "- `memory_limit_mb`: Limite de memoria (MB)\n"
        "- `memory_percent`: % de memoria usada\n"
        "- `net_rx_mb` / `net_tx_mb`: Red (MB)\n"
        "- `block_read_mb` / `block_write_mb`: Disco (MB)"
    )


def docker_best_practices() -> str:
    return (
        "# Mejores practicas Docker\n\n"
        "1. **Usa imagenes oficiales** y tags especificos (no 'latest')\n"
        "2. **Nombra contenedores** para facil identificacion\n"
        "3. **Limita recursos** con --memory y --cpus\n"
        "4. **Usa volumenes** para datos persistentes\n"
        "5. **Minimiza capas** en Dockerfiles\n"
        "6. **Usa .dockerignore** para excluir archivos innecesarios\n"
        "7. **Ejecuta como non-root** cuando sea posible\n"
        "8. **Limpia imagenes dangling** regularmente\n"
        "9. **Usa healthchecks** para monitorear contenedores\n"
        "10. **Usa docker compose** para multi-contenedor"
    )


def docker_network_guide() -> str:
    return (
        "# Redes Docker\n\n"
        "## Tipos de red\n"
        "| Tipo | Descripcion |\n"
        "|------|-------------|\n"
        "| bridge | Red puente por defecto |\n"
        "| host | Usa la red del host |\n"
        "| none | Sin red |\n"
        "| overlay | Multi-host (Swarm) |\n"
        "| macvlan | MAC address asignada |\n\n"
        "## Herramientas disponibles\n"
        "- `network_list` — listar redes\n"
        "- `network_create` — crear red\n"
        "- `network_remove` — eliminar red\n"
        "- `network_inspect` — inspeccionar red"
    )


def docker_volume_guide() -> str:
    return (
        "# Volumenes Docker\n\n"
        "## Tipos de almacenamiento\n"
        "- **Volumes**: Gestionados por Docker, persistentes\n"
        "- **Bind mounts**: Montaje directo del host\n"
        "- **tmpfs**: En memoria, temporal\n\n"
        "## Herramientas disponibles\n"
        "- `volume_list` — listar volumenes\n"
        "- `volume_create` — crear volumen\n"
        "- `volume_remove` — eliminar volumen\n"
        "- `volume_inspect` — inspeccionar volumen"
    )


def docker_compose_guide() -> str:
    return (
        "# Docker Compose\n\n"
        "## Comandos principales\n"
        "- `docker compose up -d` — iniciar servicios\n"
        "- `docker compose down` — detener y limpiar\n"
        "- `docker compose logs -f` — ver logs\n"
        "- `docker compose ps` — listar servicios\n"
        "- `docker compose build` — construir imagenes\n\n"
        "## Herramientas MCP relacionadas\n"
        "- `containers_list` — ver contenedores\n"
        "- `container_logs` — logs de un servicio\n"
        "- `stop_container` — detener un servicio"
    )


def docker_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion (parametros invalidos)"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"common_errors": {
                    "NOT_FOUND": "Contenedor o imagen no encontrada",
                    "CONNECTION_REFUSED": "No se puede conectar al daemon Docker",
                    "PERMISSION_DENIED": "Sin permisos para acceder al socket Docker",
                    "IMAGE_PULL_FAILED": "Error descargando imagen del registry",
                }},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def docker_security_tips() -> str:
    return (
        "# Seguridad Docker\n\n"
        "1. **No expongas el socket Docker** sin TLS\n"
        "2. **Usa imagenes verificadas** (Docker Content Trust)\n"
        "3. **Ejecuta como non-root** (USER mcpuser)\n"
        "4. **Limita capacidades** (--cap-drop=ALL)\n"
        "5. **Usa read-only** (--read-only) cuando sea posible\n"
        "6. **Escanea imagenes** con Trivy/Snyk\n"
        "7. **Usa secrets** para credenciales\n"
        "8. **Aisla contenedores** con redes dedicadas"
    )


def docker_troubleshooting() -> str:
    return (
        "# Troubleshooting Docker\n\n"
        "## Problemas comunes\n\n"
        "### No se puede conectar al daemon\n"
        "- Verifica que Docker este corriendo: `docker info`\n"
        "- Revisa permisos del socket: `ls -la /var/run/docker.sock`\n"
        "- Configura DOCKER_HOST si es remoto\n\n"
        "### Contenedor no inicia\n"
        "- Revisa logs: `container_logs(container_id)`\n"
        "- Verifica la imagen: `images_list()`\n"
        "- Confirma puertos disponibles\n\n"
        "### Espacio en disco agotado\n"
        "- Limpia imagenes: `image_prune()`\n"
        "- Limpia contenedores: `container_prune()`\n"
        "- Limpia volumenes: `volume_prune()`"
    )


def docker_quick_reference() -> str:
    return (
        "# Referencia rapida Docker MCP\n\n"
        "## Tools disponibles\n"
        "| Tool | Descripcion |\n"
        "|------|-------------|\n"
        "| containers_list | Listar contenedores |\n"
        "| containers_stats | Stats de un contenedor |\n"
        "| container_logs | Logs de un contenedor |\n"
        "| container_exec | Ejecutar comando en contenedor |\n"
        "| run_container | Crear y arrancar contenedor |\n"
        "| stop_container | Detener contenedor |\n"
        "| images_list | Listar imagenes |\n"
        "| image_pull | Descargar imagen |\n"
        "| image_remove | Eliminar imagen |\n"
        "| image_inspect | Inspeccionar imagen |\n"
        "| network_list | Listar redes |\n"
        "| volume_list | Listar volumenes |\n"
        "| container_prune | Limpiar contenedores |\n"
        "| image_prune | Limpiar imagenes |\n"
        "| docker_info | Info del daemon |\n"
        "| docker_version | Version de Docker |\n"
        "| container_inspect | Inspeccionar contenedor |\n"
        "| container_restart | Reiniciar contenedor |\n"
        "| container_pause | Pausar contenedor |\n"
        "| container_unpause | Reanudar contenedor |"
    )
