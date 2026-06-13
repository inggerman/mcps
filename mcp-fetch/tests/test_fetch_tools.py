"""Tests unitarios para fetch_tools (sin llamadas HTTP reales — mocking con httpx)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from mcp_fetch.tools.fetch_tools import (
    _navigate_path,
    extract_text,
    fetch_json,
    fetch_post,
    fetch_url,
)
from mcp_shared.errors import (
    ApiError,
    NetworkError,
    NetworkTimeoutError,
    ParseError,
    ValidationError,
)

# ---------------------------------------------------------------------------
# Helpers para mock
# ---------------------------------------------------------------------------


def _mock_response(
    status_code: int = 200,
    content: bytes = b"hello world",
    content_type: str = "text/plain",
    url: str = "https://example.com",
    elapsed_ms: float = 50.0,
) -> MagicMock:

    response = MagicMock()
    response.status_code = status_code
    response.content = content
    response.url = url
    response.headers = {"content-type": content_type}
    elapsed = MagicMock()
    elapsed.total_seconds.return_value = elapsed_ms / 1000
    response.elapsed = elapsed
    return response


# ---------------------------------------------------------------------------
# _navigate_path
# ---------------------------------------------------------------------------


class TestNavigatePath:
    def test_simple_key(self) -> None:
        data = {"name": "Alice"}
        assert _navigate_path(data, "name", "http://x") == "Alice"

    def test_nested_key(self) -> None:
        data = {"user": {"city": "CDMX"}}
        assert _navigate_path(data, "user.city", "http://x") == "CDMX"

    def test_array_index(self) -> None:
        data = {"items": ["a", "b", "c"]}
        assert _navigate_path(data, "items[1]", "http://x") == "b"

    def test_nested_array(self) -> None:
        data = {"data": [{"id": 1}, {"id": 2}]}
        assert _navigate_path(data, "data[0].id", "http://x") == 1

    def test_missing_key_raises(self) -> None:
        with pytest.raises(ValidationError):
            _navigate_path({"a": 1}, "b", "http://x")

    def test_index_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            _navigate_path({"items": []}, "items[0]", "http://x")

    def test_key_on_non_dict_raises(self) -> None:
        with pytest.raises(ValidationError):
            _navigate_path({"val": 42}, "val.nested", "http://x")


# ---------------------------------------------------------------------------
# fetch_url
# ---------------------------------------------------------------------------


class TestFetchUrl:
    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            fetch_url("not-a-url")

    def test_ftp_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            fetch_url("ftp://example.com/file")

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_successful_get(self, mock_client_cls: MagicMock) -> None:
        mock_response = _mock_response(content=b"page content", content_type="text/html")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = ctx

        result = fetch_url("https://example.com")
        assert result["status_code"] == 200
        assert result["content"] == "page content"
        assert result["truncated"] is False

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_content_truncated(self, mock_client_cls: MagicMock) -> None:
        big_content = b"x" * 6_000_000
        mock_response = _mock_response(content=big_content)
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = ctx

        result = fetch_url("https://example.com")
        assert result["truncated"] is True
        assert len(result["content"]) < len(big_content)

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_timeout_raises_network_timeout_error(self, mock_client_cls: MagicMock) -> None:
        import httpx as httpx_mod

        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(side_effect=httpx_mod.TimeoutException("timeout"))
        mock_client_cls.return_value = ctx

        with pytest.raises(NetworkTimeoutError):
            fetch_url("https://example.com")

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_network_error_raises_network_error(self, mock_client_cls: MagicMock) -> None:
        import httpx as httpx_mod

        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(side_effect=httpx_mod.ConnectError("refused"))
        mock_client_cls.return_value = ctx

        with pytest.raises(NetworkError):
            fetch_url("https://example.com")


# ---------------------------------------------------------------------------
# fetch_post
# ---------------------------------------------------------------------------


class TestFetchPost:
    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            fetch_post("example.com")

    def test_both_body_types_raises(self) -> None:
        with pytest.raises(ValidationError):
            fetch_post(
                "https://example.com",
                json_body={"key": "val"},
                form_data={"key": "val"},
            )

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_successful_post_json(self, mock_client_cls: MagicMock) -> None:
        mock_response = _mock_response(content=b'{"ok": true}', content_type="application/json")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.post = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = ctx

        result = fetch_post("https://example.com/api", json_body={"x": 1})
        assert result["status_code"] == 200
        assert "ok" in result["content"]


# ---------------------------------------------------------------------------
# extract_text
# ---------------------------------------------------------------------------


class TestExtractText:
    _HTML = b"""<html><head><title>Mi Pagina</title></head>
    <body>
      <nav>Menu nav</nav>
      <h1>Titulo</h1>
      <p>Primer parrafo con texto util.</p>
      <script>alert('js')</script>
      <footer>Footer</footer>
    </body></html>"""

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_extracts_clean_text(self, mock_client_cls: MagicMock) -> None:
        mock_response = _mock_response(content=self._HTML, content_type="text/html")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = ctx

        result = extract_text("https://example.com")
        assert "Titulo" in result["text"]
        assert "Primer parrafo" in result["text"]
        assert "alert" not in result["text"]
        assert "Menu nav" not in result["text"]
        assert result["title"] == "Mi Pagina"
        assert result["word_count"] > 0

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_non_html_raises(self, mock_client_cls: MagicMock) -> None:
        mock_response = _mock_response(content=b'{"key": 1}', content_type="application/json")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = ctx

        with pytest.raises(ApiError):
            extract_text("https://example.com/api.json")

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_include_links(self, mock_client_cls: MagicMock) -> None:
        html = b'<html><body><a href="https://spring.io/docs">Spring Docs</a></body></html>'
        mock_response = _mock_response(content=html, content_type="text/html")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = ctx

        result = extract_text("https://example.com", include_links=True)
        assert result["links"] is not None
        assert any("spring.io" in lnk["href"] for lnk in result["links"])


# ---------------------------------------------------------------------------
# fetch_json
# ---------------------------------------------------------------------------


class TestFetchJson:
    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_returns_parsed_json(self, mock_client_cls: MagicMock) -> None:
        payload = b'{"users": [{"id": 1, "name": "Alice"}]}'
        mock_response = _mock_response(content=payload, content_type="application/json")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = ctx

        result = fetch_json("https://api.example.com/users")
        assert result["data"]["users"][0]["name"] == "Alice"

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_jq_path_navigation(self, mock_client_cls: MagicMock) -> None:
        payload = b'{"data": {"items": [{"label": "K8s"}]}}'
        mock_response = _mock_response(content=payload, content_type="application/json")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = ctx

        result = fetch_json("https://api.example.com", jq_path="data.items[0].label")
        assert result["data"] == "K8s"
        assert result["path_used"] == "data.items[0].label"

    @patch("mcp_fetch.tools.fetch_tools.httpx.Client")
    def test_invalid_json_raises(self, mock_client_cls: MagicMock) -> None:
        mock_response = _mock_response(content=b"<html>Not JSON</html>", content_type="text/html")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = ctx

        with pytest.raises(ParseError):
            fetch_json("https://example.com/page")
