"""Herramientas para interactuar con la API REST de ComfyUI.

ComfyUI expone una API REST en el puerto 8188 (default). Esta capa envuelve
los endpoints principales para generación de imágenes y video.

Referencia: https://github.com/comfyanonymous/ComfyUI/blob/master/comfy/cli_serve.py

Todas las operaciones son síncronas (httpx sync client), igual que mcp-fetch.
El polling de resultados es bloqueante con sleep configurable.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from mcp_shared.errors import ApiError, NetworkError, NetworkTimeoutError, ValidationError

from mcp_comfyui.config import settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _client(timeout: float | None = None) -> httpx.Client:
    resolved = timeout or settings.default_timeout
    return httpx.Client(
        base_url=settings.comfyui_url,
        timeout=resolved,
    )


def _check_response(response: httpx.Response) -> None:
    if response.status_code >= 400:
        raise ApiError(
            endpoint=str(response.url),
            status_code=response.status_code,
            detail=response.text[:500],
        )


# ---------------------------------------------------------------------------
# System stats
# ---------------------------------------------------------------------------


def get_system_stats() -> dict[str, Any]:
    """Obtiene estadísticas del sistema ComfyUI (GPU, VRAM, queue, devices).

    Returns:
        Dict con system_stats: { devices: [...], queue_remaining: N },
        y metadata del servidor.
    """
    try:
        with _client(timeout=10.0) as client:
            response = client.get("/system_stats")
            _check_response(response)
            return response.json()
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(
            url=settings.comfyui_url + "/system_stats",
            timeout_seconds=10.0,
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.comfyui_url, reason=str(exc)) from exc


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def list_models() -> dict[str, Any]:
    """Lista los modelos (checkpoints) disponibles en ComfyUI.

    Returns:
        Dict con lista de nombres de checkpoints cargados en la carpeta models/checkpoints.
    """
    try:
        with _client(timeout=15.0) as client:
            response = client.get("/object_info/CheckpointLoaderSimple")
            _check_response(response)
            data = response.json()
            info = data.get("CheckpointLoaderSimple", {})
            return {
                "checkpoints": info.get("input", {}).get("required", {}).get("ckpt_name", [[]])[0],
            }
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(
            url=settings.comfyui_url + "/object_info/CheckpointLoaderSimple",
            timeout_seconds=15.0,
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.comfyui_url, reason=str(exc)) from exc


def list_loras() -> dict[str, Any]:
    """Lista los LoRAs disponibles en ComfyUI.

    Returns:
        Dict con lista de nombres de LoRAs cargados en models/loras.
    """
    try:
        with _client(timeout=15.0) as client:
            response = client.get("/object_info/LoraLoader")
            _check_response(response)
            data = response.json()
            info = data.get("LoraLoader", {})
            return {
                "loras": info.get("input", {}).get("required", {}).get("lora_name", [[]])[0],
            }
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(
            url=settings.comfyui_url + "/object_info/LoraLoader",
            timeout_seconds=15.0,
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.comfyui_url, reason=str(exc)) from exc


def list_embeddings() -> dict[str, Any]:
    """Lista los embeddings (textual inversion) disponibles.

    Returns:
        Dict con lista de nombres de embeddings.
    """
    try:
        with _client(timeout=15.0) as client:
            response = client.get("/embeddings")
            _check_response(response)
            return {"embeddings": response.json()}
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(
            url=settings.comfyui_url + "/embeddings",
            timeout_seconds=15.0,
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.comfyui_url, reason=str(exc)) from exc


# ---------------------------------------------------------------------------
# Queue prompt (ejecutar workflow)
# ---------------------------------------------------------------------------


def queue_prompt(
    workflow: dict[str, Any],
    client_id: str | None = None,
) -> dict[str, Any]:
    """Encola un workflow (prompt) para ejecución en ComfyUI.

    Args:
        workflow: Grafo de nodos de ComfyUI en formato API (no el formato UI).
            Ejemplo: {"3": {"class_type": "KSampler", "inputs": {...}}, ...}
        client_id: ID de cliente opcional para tracking. Si None, se genera uno.

    Returns:
        Dict con:
        - prompt_id (str): UUID del prompt encolado.
        - number (int): Número de posición en la cola.
        - node_errors (dict): Errores de validación de nodos (si los hay).
    """
    if not workflow or not isinstance(workflow, dict):
        raise ValidationError(field="workflow", reason="workflow debe ser un dict no vacío")

    cid = client_id or str(uuid.uuid4())
    payload = {"prompt": workflow, "client_id": cid}

    try:
        with _client(timeout=30.0) as client:
            response = client.post("/prompt", json=payload)
            _check_response(response)
            data = response.json()
            return {
                "prompt_id": data.get("prompt_id"),
                "number": data.get("number"),
                "node_errors": data.get("node_errors", {}),
                "client_id": cid,
            }
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(
            url=settings.comfyui_url + "/prompt",
            timeout_seconds=30.0,
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.comfyui_url, reason=str(exc)) from exc


# ---------------------------------------------------------------------------
# Workflow status / polling
# ---------------------------------------------------------------------------


def get_workflow_status(prompt_id: str) -> dict[str, Any]:
    """Consulta el estado de un prompt encolado.

    Args:
        prompt_id: UUID del prompt devuelto por queue_prompt.

    Returns:
        Dict con:
        - status: "queued" | "executing" | "completed" | "error"
        - queue_position: posición en cola (si queued)
        - node_info: info de nodos (si executing)
    """
    if not prompt_id:
        raise ValidationError(field="prompt_id", reason="prompt_id es requerido")

    try:
        with _client(timeout=10.0) as client:
            response = client.get("/queue")
            _check_response(response)
            queue_data = response.json()

            # Check if running
            running = queue_data.get("queue_running", [])
            for item in running:
                if item and len(item) > 1 and item[1] == prompt_id:
                    return {"status": "executing", "prompt_id": prompt_id}

            # Check if pending
            pending = queue_data.get("queue_pending", [])
            for idx, item in enumerate(pending):
                if item and len(item) > 1 and item[1] == prompt_id:
                    return {
                        "status": "queued",
                        "prompt_id": prompt_id,
                        "queue_position": idx,
                    }

            # Not in queue — check history for completion
            history = get_history(prompt_id=prompt_id)
            if prompt_id in history.get("history", {}):
                return {"status": "completed", "prompt_id": prompt_id}

            return {"status": "unknown", "prompt_id": prompt_id}
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        raise NetworkError(url=settings.comfyui_url, reason=str(exc)) from exc


def get_prompt_result(
    prompt_id: str,
    poll: bool = True,
) -> dict[str, Any]:
    """Obtiene el resultado completo de un prompt (con polling opcional).

    Args:
        prompt_id: UUID del prompt.
        poll: Si True, hace polling hasta que el prompt complete o timeout.

    Returns:
        Dict con:
        - status: "completed" | "error" | "timeout"
        - outputs: dict de outputs por nodo (imágenes, etc.)
        - images: lista de {filename, subfolder, type} para imágenes generadas
        - error: mensaje si hubo error
    """
    if not prompt_id:
        raise ValidationError(field="prompt_id", reason="prompt_id es requerido")

    if poll:
        for _ in range(settings.max_poll_attempts):
            status_info = get_workflow_status(prompt_id)
            if status_info["status"] == "completed":
                break
            if status_info["status"] == "unknown":
                # Could be already done or never existed — check history
                break
            time.sleep(settings.poll_interval)
        else:
            return {
                "status": "timeout",
                "prompt_id": prompt_id,
                "error": f"Timeout tras {settings.max_poll_attempts * settings.poll_interval}s",
            }

    history = get_history(prompt_id=prompt_id)
    hist_entry = history.get("history", {}).get(prompt_id, {})

    if not hist_entry:
        return {
            "status": "unknown",
            "prompt_id": prompt_id,
            "error": "Prompt no encontrado en historial",
        }

    status = hist_entry.get("status", {})
    outputs = hist_entry.get("outputs", {})

    # Extract images from outputs
    images: list[dict[str, str]] = []
    for _node_id, node_output in outputs.items():
        if "images" in node_output:
            images.extend(node_output["images"])
        if "gifs" in node_output:
            for gif in node_output["gifs"]:
                images.append({**gif, "type": "gif"})

    result: dict[str, Any] = {
        "status": "completed" if status.get("completed", False) else "error",
        "prompt_id": prompt_id,
        "outputs": outputs,
        "images": images,
    }

    if status.get("status_str") == "error":
        result["error"] = status.get("messages", "Error desconocido")

    return result


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def get_history(prompt_id: str | None = None, max_items: int = 50) -> dict[str, Any]:
    """Obtiene el historial de ejecuciones de ComfyUI.

    Args:
        prompt_id: Si se pasa, obtiene solo el historial de ese prompt.
        max_items: Número máximo de items a retornar (si no hay prompt_id).

    Returns:
        Dict con history: {prompt_id: {status, outputs, ...}, ...}
    """
    try:
        with _client(timeout=15.0) as client:
            if prompt_id:
                response = client.get("/history", params={"prompt_id": prompt_id})
            else:
                response = client.get("/history")
            _check_response(response)
            data = response.json()
            # Limit if no specific prompt_id
            if not prompt_id and len(data) > max_items:
                # Keep most recent
                items = list(data.items())[-max_items:]
                data = dict(items)
            return {"history": data}
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(
            url=settings.comfyui_url + "/history",
            timeout_seconds=15.0,
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.comfyui_url, reason=str(exc)) from exc


# ---------------------------------------------------------------------------
# Output images
# ---------------------------------------------------------------------------


def get_output_images(
    filename: str,
    subfolder: str = "",
    image_type: str = "output",
) -> dict[str, Any]:
    """Obtiene una imagen generada por ComfyUI (URL para descargar).

    Args:
        filename: Nombre del archivo (devuelto en get_prompt_result.images).
        subfolder: Subcarpeta dentro de output/ (si aplica).
        image_type: "output" | "temp".

    Returns:
        Dict con:
        - url (str): URL completa para descargar la imagen.
        - filename (str): Nombre del archivo.
        - type (str): Tipo de output.
    """
    if not filename:
        raise ValidationError(field="filename", reason="filename es requerido")

    if image_type not in ("output", "temp"):
        raise ValidationError(
            field="image_type",
            reason="image_type debe ser 'output' o 'temp'",
        )

    params = {"filename": filename, "subfolder": subfolder, "type": image_type}
    url = f"{settings.comfyui_url}/view?filename={filename}&subfolder={subfolder}&type={image_type}"

    return {
        "url": url,
        "filename": filename,
        "subfolder": subfolder,
        "type": image_type,
        "params": params,
    }


# ---------------------------------------------------------------------------
# Upload image (para img2img, ControlNet)
# ---------------------------------------------------------------------------


def upload_image(
    image_path: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Sube una imagen a ComfyUI para usar como input (img2img, ControlNet).

    Args:
        image_path: Ruta local al archivo de imagen a subir.
        overwrite: Si True, sobrescribe si ya existe una con el mismo nombre.

    Returns:
        Dict con:
        - name (str): Nombre del archivo subido.
        - subfolder (str): Subcarpeta donde se guardó.
        - type (str): "input"
    """
    if not image_path:
        raise ValidationError(field="image_path", reason="image_path es requerido")

    path = Path(image_path)
    if not path.exists():
        raise ValidationError(field="image_path", reason=f"Archivo no existe: {image_path}")

    if not path.is_file():
        raise ValidationError(field="image_path", reason=f"No es un archivo: {image_path}")

    try:
        with _client(timeout=60.0) as client:
            with path.open("rb") as f:
                files = {"image": (path.name, f, "application/octet-stream")}
                data = {"overwrite": "true" if overwrite else "false"}
                response = client.post("/upload/image", files=files, data=data)
                _check_response(response)
                return response.json()
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(
            url=settings.comfyui_url + "/upload/image",
            timeout_seconds=60.0,
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.comfyui_url, reason=str(exc)) from exc


# ---------------------------------------------------------------------------
# Interrupt
# ---------------------------------------------------------------------------


def interrupt_generation() -> dict[str, Any]:
    """Interrumpe la generación en curso de ComfyUI.

    Returns:
        Dict con status: "interrupted"
    """
    try:
        with _client(timeout=10.0) as client:
            response = client.post("/interrupt")
            _check_response(response)
            return {"status": "interrupted"}
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(
            url=settings.comfyui_url + "/interrupt",
            timeout_seconds=10.0,
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.comfyui_url, reason=str(exc)) from exc
