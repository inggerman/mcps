"""Tests para mcp-comfyui tools.

Usa httpx.MockTransport para simular respuestas de ComfyUI sin servidor real.
Sigue el patrón de los tests de mcp-fetch y mcp-gitea.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest
from mcp_comfyui.tools import comfyui_tools

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _mock_transport(handler):
    """Crea un MockTransport con el handler dado."""
    return httpx.MockTransport(handler)


@pytest.fixture
def mock_system_stats():
    return {
        "system": {
            "os": "nt",
            "ram_total": 34359738368,
            "ram_total_str": "32 GB",
            "comfyui_version": "0.3.27",
        },
        "devices": [
            {
                "name": "cuda:0",
                "type": "cuda",
                "vram_total": 17179869184,
                "vram_free": 12884901888,
            }
        ],
        "queue_remaining": 0,
    }


@pytest.fixture
def mock_models():
    return {
        "CheckpointLoaderSimple": {
            "input": {
                "required": {
                    "ckpt_name": [
                        ["sd_xl_base_1.0.safetensors", "v1-5-pruned-emaonly.safetensors"],
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_loras():
    return {
        "LoraLoader": {
            "input": {
                "required": {
                    "lora_name": [["detail_tweaker.safetensors", "add_detail.safetensors"]],
                }
            }
        }
    }


@pytest.fixture
def mock_queue_response():
    return {
        "prompt_id": "abc-123-def",
        "number": 1,
        "node_errors": {},
    }


@pytest.fixture
def mock_history_completed():
    return {
        "abc-123-def": {
            "status": {
                "status_str": "success",
                "completed": True,
                "messages": [],
            },
            "outputs": {
                "9": {
                    "images": [
                        {
                            "filename": "ComfyUI_00001_.png",
                            "subfolder": "",
                            "type": "output",
                        }
                    ]
                }
            },
        }
    }


# ---------------------------------------------------------------------------
# get_system_stats
# ---------------------------------------------------------------------------


def test_get_system_stats_success(mock_system_stats):
    def handler(request):
        return httpx.Response(200, json=mock_system_stats)

    with patch("mcp_comfyui.tools.comfyui_tools._client") as mock_client_cls:
        client = httpx.Client(transport=_mock_transport(handler), base_url="http://test")
        mock_client_cls.return_value.__enter__ = lambda self: client
        mock_client_cls.return_value.__exit__ = lambda self, *a: None

        result = comfyui_tools.get_system_stats()
        assert "devices" in result
        assert len(result["devices"]) == 1
        assert result["devices"][0]["name"] == "cuda:0"


def test_get_system_stats_connection_error():
    def handler(request):
        raise httpx.ConnectError("Connection refused")

    with patch("mcp_comfyui.tools.comfyui_tools._client") as mock_client_cls:
        client = httpx.Client(transport=_mock_transport(handler), base_url="http://test")
        mock_client_cls.return_value.__enter__ = lambda self: client
        mock_client_cls.return_value.__exit__ = lambda self, *a: None

        with pytest.raises(Exception, match=r"Connection refused|NetworkError"):
            comfyui_tools.get_system_stats()


# ---------------------------------------------------------------------------
# list_models
# ---------------------------------------------------------------------------


def test_list_models_success(mock_models):
    def handler(request):
        return httpx.Response(200, json=mock_models)

    with patch("mcp_comfyui.tools.comfyui_tools._client") as mock_client_cls:
        client = httpx.Client(transport=_mock_transport(handler), base_url="http://test")
        mock_client_cls.return_value.__enter__ = lambda self: client
        mock_client_cls.return_value.__exit__ = lambda self, *a: None

        result = comfyui_tools.list_models()
        assert "checkpoints" in result
        assert "sd_xl_base_1.0.safetensors" in result["checkpoints"]


# ---------------------------------------------------------------------------
# list_loras
# ---------------------------------------------------------------------------


def test_list_loras_success(mock_loras):
    def handler(request):
        return httpx.Response(200, json=mock_loras)

    with patch("mcp_comfyui.tools.comfyui_tools._client") as mock_client_cls:
        client = httpx.Client(transport=_mock_transport(handler), base_url="http://test")
        mock_client_cls.return_value.__enter__ = lambda self: client
        mock_client_cls.return_value.__exit__ = lambda self, *a: None

        result = comfyui_tools.list_loras()
        assert "loras" in result
        assert "detail_tweaker.safetensors" in result["loras"]


# ---------------------------------------------------------------------------
# queue_prompt
# ---------------------------------------------------------------------------


def test_queue_prompt_success(mock_queue_response):
    def handler(request):
        body = json.loads(request.content)
        assert "prompt" in body
        assert "client_id" in body
        return httpx.Response(200, json=mock_queue_response)

    with patch("mcp_comfyui.tools.comfyui_tools._client") as mock_client_cls:
        client = httpx.Client(transport=_mock_transport(handler), base_url="http://test")
        mock_client_cls.return_value.__enter__ = lambda self: client
        mock_client_cls.return_value.__exit__ = lambda self, *a: None

        workflow = {"3": {"class_type": "KSampler", "inputs": {"seed": 42}}}
        result = comfyui_tools.queue_prompt(workflow=workflow)
        assert result["prompt_id"] == "abc-123-def"
        assert result["number"] == 1


def test_queue_prompt_empty_workflow():
    with pytest.raises(Exception, match=r"ValidationError|workflow"):
        comfyui_tools.queue_prompt(workflow={})


def test_queue_prompt_none_workflow():
    with pytest.raises(Exception, match=r"ValidationError|workflow"):
        comfyui_tools.queue_prompt(workflow=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# get_history
# ---------------------------------------------------------------------------


def test_get_history_success(mock_history_completed):
    def handler(request):
        return httpx.Response(200, json=mock_history_completed)

    with patch("mcp_comfyui.tools.comfyui_tools._client") as mock_client_cls:
        client = httpx.Client(transport=_mock_transport(handler), base_url="http://test")
        mock_client_cls.return_value.__enter__ = lambda self: client
        mock_client_cls.return_value.__exit__ = lambda self, *a: None

        result = comfyui_tools.get_history(prompt_id="abc-123-def")
        assert "abc-123-def" in result["history"]


# ---------------------------------------------------------------------------
# get_output_images
# ---------------------------------------------------------------------------


def test_get_output_images_success():
    result = comfyui_tools.get_output_images(
        filename="ComfyUI_00001_.png",
        subfolder="",
        image_type="output",
    )
    assert "url" in result
    assert "ComfyUI_00001_.png" in result["url"]
    assert result["filename"] == "ComfyUI_00001_.png"
    assert result["type"] == "output"


def test_get_output_images_empty_filename():
    with pytest.raises(Exception, match=r"ValidationError|filename"):
        comfyui_tools.get_output_images(filename="")


def test_get_output_images_invalid_type():
    with pytest.raises(Exception, match=r"ValidationError|image_type"):
        comfyui_tools.get_output_images(filename="test.png", image_type="invalid")


# ---------------------------------------------------------------------------
# interrupt_generation
# ---------------------------------------------------------------------------


def test_interrupt_generation_success():
    def handler(request):
        return httpx.Response(200, json={})

    with patch("mcp_comfyui.tools.comfyui_tools._client") as mock_client_cls:
        client = httpx.Client(transport=_mock_transport(handler), base_url="http://test")
        mock_client_cls.return_value.__enter__ = lambda self: client
        mock_client_cls.return_value.__exit__ = lambda self, *a: None

        result = comfyui_tools.interrupt_generation()
        assert result["status"] == "interrupted"


# ---------------------------------------------------------------------------
# list_embeddings
# ---------------------------------------------------------------------------


def test_list_embeddings_success():
    def handler(request):
        return httpx.Response(200, json=["bad_prompt", "easynegative"])

    with patch("mcp_comfyui.tools.comfyui_tools._client") as mock_client_cls:
        client = httpx.Client(transport=_mock_transport(handler), base_url="http://test")
        mock_client_cls.return_value.__enter__ = lambda self: client
        mock_client_cls.return_value.__exit__ = lambda self, *a: None

        result = comfyui_tools.list_embeddings()
        assert "embeddings" in result
        assert "bad_prompt" in result["embeddings"]
