"""Contract tests for the MCP servers added to the engineering workspace."""

from __future__ import annotations

import asyncio
import importlib
import os

import pytest
from fastmcp import FastMCP

os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

SERVERS = [
    ("mcp_project_memory.server", "mcp-project-memory"),
    ("mcp_llm_router.server", "mcp-llm-router"),
    ("mcp_git.server", "mcp-git"),
    ("mcp_github.server", "mcp-github"),
    ("mcp_code_quality.server", "mcp-code-quality"),
    ("mcp_architecture.server", "mcp-architecture"),
    ("mcp_event_driven.server", "mcp-event-driven"),
    ("mcp_orchestrator.server", "mcp-orchestrator"),
    ("mcp_best_practices.server", "mcp-best-practices"),
    ("mcp_ci_cd.server", "mcp-ci-cd"),
    ("mcp_design_patterns.server", "mcp-design-patterns"),
    ("mcp_security_champion.server", "mcp-security-champion"),
    ("mcp_database.server", "mcp-database"),
    ("mcp_filesystem.server", "mcp-filesystem"),
    ("mcp_object_storage.server", "mcp-object-storage"),
    ("mcp_openapi.server", "mcp-openapi"),
    ("mcp_documents.server", "mcp-documents"),
    ("mcp_browser.server", "mcp-browser"),
    ("mcp_kubernetes.server", "mcp-kubernetes"),
    ("mcp_observability.server", "mcp-observability"),
    ("mcp_terraform.server", "mcp-terraform"),
    # Fase 9 — Infra MCPs (core)
    ("mcp_argocd.server", "mcp-argocd"),
    ("mcp_harbor.server", "mcp-harbor"),
    ("mcp_gitea.server", "mcp-gitea"),
    ("mcp_n8n.server", "mcp-n8n"),
    ("mcp_vault_secrets.server", "mcp-vault-secrets"),
    ("mcp_postgres.server", "mcp-postgres"),
    ("mcp_redis.server", "mcp-redis"),
    ("mcp_rabbitmq.server", "mcp-rabbitmq"),
    ("mcp_vector_search.server", "mcp-vector-search"),
    ("mcp_notify.server", "mcp-notify"),
    # Fase 10 — Infra MCPs (script-derived)
    ("mcp_cluster_doctor.server", "mcp-cluster-doctor"),
    ("mcp_image_builder.server", "mcp-image-builder"),
    ("mcp_log_explorer.server", "mcp-log-explorer"),
    ("mcp_config_sync.server", "mcp-config-sync"),
    ("mcp_health_monitor.server", "mcp-health-monitor"),
    ("mcp_network_doctor.server", "mcp-network-doctor"),
    ("mcp_storage_doctor.server", "mcp-storage-doctor"),
    ("mcp_deploy_tracker.server", "mcp-deploy-tracker"),
    ("mcp_node_ops.server", "mcp-node-ops"),
]


@pytest.mark.parametrize(("module_name", "server_name"), SERVERS)
def test_server_contract(module_name: str, server_name: str) -> None:
    module = importlib.import_module(module_name)
    server = module.mcp

    assert isinstance(server, FastMCP)
    assert server.name == server_name
    assert asyncio.run(server.list_tools())
