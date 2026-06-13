"""Herramientas Docker para mcp-docker.

Gestiona contenedores, imágenes, logs y ejecución remota via Docker SDK para Python.
Todas las operaciones son síncronas.
"""

from __future__ import annotations

from typing import Any

from mcp_shared.errors import ApiError, NetworkError, ValidationError

from mcp_docker.config import settings

_DOCKER_MISSING = "docker SDK no está instalado. Ejecuta: pip install docker"


def _get_client() -> Any:
    """Obtiene un cliente Docker conectado al daemon."""
    try:
        import docker
    except ImportError as exc:
        raise NetworkError(url="docker-daemon", reason=_DOCKER_MISSING) from exc

    try:
        kwargs: dict[str, Any] = {}
        if settings.docker_host:
            kwargs["base_url"] = settings.docker_host
        kwargs["timeout"] = settings.exec_timeout
        client = docker.from_env(**kwargs)
        client.ping()
        return client
    except Exception as exc:
        raise NetworkError(
            url=settings.docker_host or "unix:///var/run/docker.sock",
            reason=f"No se puede conectar al daemon Docker: {exc}",
        ) from exc


def _container_to_dict(container: Any) -> dict[str, Any]:
    """Convierte un objeto Container a dict serializable."""
    attrs = container.attrs or {}
    state = attrs.get("State", {})
    config = attrs.get("Config", {})
    net = attrs.get("NetworkSettings", {})
    ports: dict[str, Any] = {}
    for host_port, bindings in (net.get("Ports") or {}).items():
        ports[host_port] = bindings or []
    return {
        "id": container.short_id,
        "name": container.name,
        "image": container.image.tags[0] if container.image.tags else container.image.short_id,
        "status": container.status,
        "created": attrs.get("Created", ""),
        "started": state.get("StartedAt", ""),
        "command": config.get("Cmd") or [],
        "ports": ports,
        "labels": config.get("Labels") or {},
    }


def _image_to_dict(image: Any) -> dict[str, Any]:
    """Convierte un objeto Image a dict serializable."""
    attrs = image.attrs or {}
    size_mb = round(attrs.get("Size", 0) / 1024 / 1024, 1)
    return {
        "id": image.short_id,
        "tags": image.tags,
        "size_mb": size_mb,
        "created": attrs.get("Created", ""),
        "architecture": attrs.get("Architecture", ""),
        "os": attrs.get("Os", ""),
    }


# ---------------------------------------------------------------------------
# containers_list
# ---------------------------------------------------------------------------


def containers_list(
    all_containers: bool = False,
    filters: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Lista contenedores Docker.

    Args:
        all_containers: Si True incluye contenedores detenidos. Default False (solo running).
        filters: Filtros Docker (ej: ``{"name": "web", "status": "running"}``).

    Returns:
        Dict con ``containers`` (list) y ``count`` (int).

    Raises:
        NetworkError: Si no se puede conectar al daemon Docker.
    """
    client = _get_client()
    try:
        container_list = client.containers.list(all=all_containers, filters=filters or {})
        return {
            "containers": [_container_to_dict(c) for c in container_list],
            "count": len(container_list),
            "showing": "all" if all_containers else "running",
        }
    except Exception as exc:
        raise ApiError(
            url="docker-daemon",
            status_code=0,
            response_body=f"Error listando contenedores: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# containers_stats
# ---------------------------------------------------------------------------


def containers_stats(container_id: str) -> dict[str, Any]:
    """Obtiene estadísticas de uso de recursos de un contenedor (CPU, memoria, red, disco).

    Args:
        container_id: ID o nombre del contenedor.

    Returns:
        Dict con ``cpu_percent``, ``memory_mb``, ``memory_limit_mb``,
        ``memory_percent``, ``net_rx_mb``, ``net_tx_mb``, ``block_read_mb``, ``block_write_mb``.

    Raises:
        ValidationError: Si el contenedor no existe.
        NetworkError: Si no se puede conectar al daemon.
    """
    _validate_container_id(container_id)
    client = _get_client()

    try:
        container = client.containers.get(container_id)
    except Exception as exc:
        raise ValidationError(
            field="container_id",
            message=f"Contenedor '{container_id}' no encontrado.",
            value=container_id,
        ) from exc

    try:
        raw = container.stats(stream=False)
    except Exception as exc:
        raise ApiError(
            url="docker-daemon",
            status_code=0,
            response_body=f"Error obteniendo stats de '{container_id}': {exc}",
        ) from exc

    return _parse_stats(raw, container_id)


def _parse_stats(raw: dict[str, Any], container_id: str) -> dict[str, Any]:
    cpu_delta = (
        raw["cpu_stats"]["cpu_usage"]["total_usage"]
        - raw["precpu_stats"]["cpu_usage"]["total_usage"]
    )
    system_delta = raw["cpu_stats"].get("system_cpu_usage", 0) - raw["precpu_stats"].get(
        "system_cpu_usage", 0
    )
    num_cpus = len(raw["cpu_stats"]["cpu_usage"].get("percpu_usage") or []) or 1
    cpu_percent = (cpu_delta / system_delta * num_cpus * 100.0) if system_delta > 0 else 0.0

    mem = raw.get("memory_stats", {})
    mem_usage = mem.get("usage", 0) - mem.get("stats", {}).get("cache", 0)
    mem_limit = mem.get("limit", 1)
    mem_mb = round(mem_usage / 1024 / 1024, 2)
    mem_limit_mb = round(mem_limit / 1024 / 1024, 2)
    mem_percent = round(mem_usage / mem_limit * 100, 1) if mem_limit > 0 else 0.0

    net_rx = net_tx = 0.0
    for net in (raw.get("networks") or {}).values():
        net_rx += net.get("rx_bytes", 0)
        net_tx += net.get("tx_bytes", 0)

    blk_r = blk_w = 0.0
    for blk in raw.get("blkio_stats", {}).get("io_service_bytes_recursive") or []:
        if blk.get("op") == "read":
            blk_r += blk.get("value", 0)
        elif blk.get("op") == "write":
            blk_w += blk.get("value", 0)

    return {
        "container_id": container_id,
        "cpu_percent": round(cpu_percent, 2),
        "memory_mb": mem_mb,
        "memory_limit_mb": mem_limit_mb,
        "memory_percent": mem_percent,
        "net_rx_mb": round(net_rx / 1024 / 1024, 3),
        "net_tx_mb": round(net_tx / 1024 / 1024, 3),
        "block_read_mb": round(blk_r / 1024 / 1024, 3),
        "block_write_mb": round(blk_w / 1024 / 1024, 3),
    }


# ---------------------------------------------------------------------------
# container_logs
# ---------------------------------------------------------------------------


def container_logs(
    container_id: str,
    lines: int | None = None,
    since: str | None = None,
    timestamps: bool = False,
) -> dict[str, Any]:
    """Obtiene los logs de un contenedor.

    Args:
        container_id: ID o nombre del contenedor.
        lines: Número de líneas a retornar (tail). Default: ``settings.log_lines``.
        since: Retornar logs desde esta fecha/hora (formato: "2024-01-01T10:00:00" o "1h", "30m").
        timestamps: Si True incluye timestamp en cada línea.

    Returns:
        Dict con ``logs`` (str), ``container_id``, ``lines_requested``.

    Raises:
        ValidationError: Si el contenedor no existe.
        NetworkError: Si no se puede conectar al daemon.
    """
    _validate_container_id(container_id)
    client = _get_client()
    resolved_lines = lines or settings.log_lines

    try:
        container = client.containers.get(container_id)
    except Exception as exc:
        raise ValidationError(
            field="container_id",
            message=f"Contenedor '{container_id}' no encontrado.",
            value=container_id,
        ) from exc

    try:
        kwargs: dict[str, Any] = {
            "tail": resolved_lines,
            "timestamps": timestamps,
            "stream": False,
        }
        if since:
            kwargs["since"] = since

        raw_logs = container.logs(**kwargs)
        log_text = (
            raw_logs.decode("utf-8", errors="replace")
            if isinstance(raw_logs, bytes)
            else str(raw_logs)
        )

        return {
            "container_id": container.short_id,
            "container_name": container.name,
            "logs": log_text,
            "lines_requested": resolved_lines,
            "status": container.status,
        }
    except Exception as exc:
        raise ApiError(
            url="docker-daemon",
            status_code=0,
            response_body=f"Error obteniendo logs de '{container_id}': {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# container_exec
# ---------------------------------------------------------------------------


def container_exec(
    container_id: str,
    command: str,
    workdir: str | None = None,
    user: str | None = None,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Ejecuta un comando dentro de un contenedor en ejecución.

    Args:
        container_id: ID o nombre del contenedor (debe estar en estado ``running``).
        command: Comando a ejecutar. Se parsea con ``shlex.split`` si es string.
        workdir: Directorio de trabajo dentro del contenedor.
        user: Usuario con el que ejecutar (ej: ``"root"``, ``"1000:1000"``).
        environment: Variables de entorno adicionales.

    Returns:
        Dict con ``exit_code`` (int), ``output`` (str), ``container_id``, ``command``.

    Raises:
        ValidationError: Si el contenedor no existe o no está running.
        ApiError: Si hay error al ejecutar el comando.
    """
    import shlex

    _validate_container_id(container_id)
    if not command or not command.strip():
        raise ValidationError(field="command", message="El comando no puede estar vacío.")

    client = _get_client()

    try:
        container = client.containers.get(container_id)
    except Exception as exc:
        raise ValidationError(
            field="container_id",
            message=f"Contenedor '{container_id}' no encontrado.",
            value=container_id,
        ) from exc

    if container.status != "running":
        raise ValidationError(
            field="container_id",
            message=f"El contenedor '{container_id}' no está running (estado: {container.status}).",
            value=container_id,
        )

    try:
        cmd = shlex.split(command) if isinstance(command, str) else command
        kwargs: dict[str, Any] = {"workdir": workdir, "user": user}
        if environment:
            kwargs["environment"] = environment

        exit_code, output = container.exec_run(cmd, **kwargs)
        output_text = (
            output.decode("utf-8", errors="replace")
            if isinstance(output, bytes)
            else str(output or "")
        )

        return {
            "container_id": container.short_id,
            "container_name": container.name,
            "command": command,
            "exit_code": exit_code,
            "output": output_text,
            "success": exit_code == 0,
        }
    except Exception as exc:
        raise ApiError(
            url="docker-daemon",
            status_code=0,
            response_body=f"Error ejecutando comando en '{container_id}': {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# run_container
# ---------------------------------------------------------------------------


def run_container(
    image: str,
    command: str | None = None,
    name: str | None = None,
    detach: bool = True,
    ports: dict[str, str] | None = None,
    environment: dict[str, str] | None = None,
    volumes: dict[str, str] | None = None,
    remove_on_exit: bool = False,
) -> dict[str, Any]:
    """Crea y arranca un contenedor Docker.

    Args:
        image: Imagen Docker a usar (ej: ``"nginx:latest"``, ``"python:3.12-slim"``).
        command: Comando a ejecutar en el contenedor. None = usa CMD de la imagen.
        name: Nombre del contenedor. None = Docker genera uno automático.
        detach: Si True ejecuta en background (default). False bloquea hasta que termina.
        ports: Mapeo de puertos ``{container_port: host_port}`` (ej: ``{"80/tcp": "8080"}``).
        environment: Variables de entorno (ej: ``{"ENV": "prod", "PORT": "8080"}``).
        volumes: Montaje de volúmenes ``{host_path: container_path}`` (ej: ``{"/data": "/app/data"}``).
        remove_on_exit: Si True elimina el contenedor al terminar. Solo funcional con ``detach=False``.

    Returns:
        Dict con ``id``, ``name``, ``status``, ``image``, ``ports``.

    Raises:
        ValidationError: Si la imagen no tiene nombre válido.
        ApiError: Si hay error al crear/arrancar el contenedor.
    """
    if not image or not image.strip():
        raise ValidationError(field="image", message="El nombre de la imagen no puede estar vacío.")

    client = _get_client()

    port_bindings: dict[str, str] | None = None
    if ports:
        port_bindings = {f"{cp}/tcp" if "/" not in cp else cp: hp for cp, hp in ports.items()}

    volume_bindings: dict[str, dict[str, str]] | None = None
    if volumes:
        volume_bindings = {hp: {"bind": cp, "mode": "rw"} for hp, cp in volumes.items()}

    try:
        container = client.containers.run(
            image=image,
            command=command,
            name=name,
            detach=detach,
            ports=port_bindings,
            environment=environment,
            volumes=volume_bindings,
            remove=remove_on_exit,
        )

        if detach:
            container.reload()
            return _container_to_dict(container)
        else:
            output = container if isinstance(container, bytes) else b""
            return {
                "id": "n/a",
                "name": name or "n/a",
                "image": image,
                "status": "exited",
                "output": output.decode("utf-8", errors="replace"),
            }

    except Exception as exc:
        raise ApiError(
            url="docker-daemon",
            status_code=0,
            response_body=f"Error creando contenedor desde '{image}': {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# stop_container
# ---------------------------------------------------------------------------


def stop_container(
    container_id: str,
    timeout: int = 10,
    remove: bool = False,
) -> dict[str, Any]:
    """Detiene un contenedor en ejecución.

    Args:
        container_id: ID o nombre del contenedor.
        timeout: Segundos a esperar antes de SIGKILL (default 10).
        remove: Si True elimina el contenedor tras detenerlo.

    Returns:
        Dict con ``container_id``, ``name``, ``action``, ``removed``.

    Raises:
        ValidationError: Si el contenedor no existe.
        ApiError: Si hay error al detener.
    """
    _validate_container_id(container_id)
    client = _get_client()

    try:
        container = client.containers.get(container_id)
    except Exception as exc:
        raise ValidationError(
            field="container_id",
            message=f"Contenedor '{container_id}' no encontrado.",
            value=container_id,
        ) from exc

    try:
        name = container.name
        short_id = container.short_id
        container.stop(timeout=timeout)

        if remove:
            container.remove()

        return {
            "container_id": short_id,
            "name": name,
            "action": "stopped_and_removed" if remove else "stopped",
            "removed": remove,
        }
    except Exception as exc:
        raise ApiError(
            url="docker-daemon",
            status_code=0,
            response_body=f"Error deteniendo contenedor '{container_id}': {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# images_list
# ---------------------------------------------------------------------------


def images_list(
    name: str | None = None,
    dangling: bool = False,
) -> dict[str, Any]:
    """Lista imágenes Docker locales.

    Args:
        name: Filtrar por nombre/tag (ej: ``"nginx"``, ``"python:3.12"``).
        dangling: Si True incluye imágenes sin tag (dangling). Default False.

    Returns:
        Dict con ``images`` (list) y ``count`` (int).

    Raises:
        NetworkError: Si no se puede conectar al daemon.
    """
    client = _get_client()
    try:
        filters: dict[str, Any] = {}
        if dangling:
            filters["dangling"] = True

        image_list = client.images.list(name=name, filters=filters)
        return {
            "images": [_image_to_dict(img) for img in image_list],
            "count": len(image_list),
        }
    except Exception as exc:
        raise ApiError(
            url="docker-daemon",
            status_code=0,
            response_body=f"Error listando imágenes: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# image_pull
# ---------------------------------------------------------------------------


def image_pull(
    image: str,
    tag: str = "latest",
) -> dict[str, Any]:
    """Descarga una imagen Docker desde un registry.

    Args:
        image: Nombre de la imagen (ej: ``"nginx"``, ``"python"``, ``"myregistry/myapp"``).
        tag: Tag de la imagen (default ``"latest"``).

    Returns:
        Dict con ``image``, ``tag``, ``id``, ``size_mb``.

    Raises:
        ValidationError: Si el nombre de imagen está vacío.
        ApiError: Si falla el pull (imagen no encontrada, sin permisos, etc.).
    """
    if not image or not image.strip():
        raise ValidationError(field="image", message="El nombre de la imagen no puede estar vacío.")

    client = _get_client()
    try:
        pulled = client.images.pull(image, tag=tag)
        return {
            "image": image,
            "tag": tag,
            "id": pulled.short_id,
            "tags": pulled.tags,
            "size_mb": round((pulled.attrs or {}).get("Size", 0) / 1024 / 1024, 1),
        }
    except Exception as exc:
        raise ApiError(
            url=f"registry/{image}:{tag}",
            status_code=0,
            response_body=f"Error descargando imagen '{image}:{tag}': {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _validate_container_id(container_id: str) -> None:
    if not container_id or not container_id.strip():
        raise ValidationError(
            field="container_id",
            message="El ID o nombre del contenedor no puede estar vacío.",
        )
