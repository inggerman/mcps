from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_terraform.config import settings
from mcp_terraform.tools import (
    terraform_apply,
    terraform_fmt_check,
    terraform_plan,
    terraform_show,
    terraform_validate,
)

setup_logging(
    log_level=settings.log_level, log_format=settings.log_format, server_name="mcp-terraform"
)
logger = get_logger(__name__)
mcp = FastMCP(name="mcp-terraform", instructions="Terraform validate/plan/show; apply desactivado.")


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="terraform_fmt_check")
def tool_fmt(working_dir: str = ".") -> dict[str, Any]:
    return _handle(
        terraform_fmt_check,
        settings.binary,
        settings.root,
        working_dir,
        settings.timeout_seconds,
    )


@mcp.tool(name="terraform_validate")
def tool_validate(working_dir: str = ".") -> dict[str, Any]:
    return _handle(
        terraform_validate,
        settings.binary,
        settings.root,
        working_dir,
        settings.timeout_seconds,
    )


@mcp.tool(name="terraform_plan")
def tool_plan(
    working_dir: str = ".",
    variables: dict[str, Any] | None = None,
    output_file: str = "tfplan",
) -> dict[str, Any]:
    return _handle(
        terraform_plan,
        settings.binary,
        settings.root,
        working_dir,
        settings.timeout_seconds,
        variables,
        output_file,
    )


@mcp.tool(name="terraform_show")
def tool_show(working_dir: str = ".", plan_file: str = "tfplan") -> dict[str, Any]:
    return _handle(
        terraform_show,
        settings.binary,
        settings.root,
        working_dir,
        settings.timeout_seconds,
        plan_file,
    )


@mcp.tool(name="terraform_apply")
def tool_apply(working_dir: str = ".", plan_file: str = "tfplan") -> dict[str, Any]:
    return _handle(
        terraform_apply,
        settings.binary,
        settings.root,
        working_dir,
        settings.timeout_seconds,
        plan_file,
        settings.allow_apply,
    )


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
