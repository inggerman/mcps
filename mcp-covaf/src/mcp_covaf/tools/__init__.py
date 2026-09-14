"""Exports públicos para tools de mcp-covaf."""

from mcp_covaf.tools.back_tools import (
    back_analyze_cartas_pipeline,
    back_analyze_oficios_pipeline,
    back_get_endpoint_map,
    back_list_extraction_strategies,
    back_list_quality_gates,
    back_list_templates,
    back_search_code,
)
from mcp_covaf.tools.front_tools import (
    front_get_mfe_config,
    front_list_modules,
    front_list_routes,
    front_list_services,
    front_search_code,
)
from mcp_covaf.tools.ia_tools import (
    ia_analyze_extraction_output,
    ia_get_plugin_schema,
    ia_list_eval_tests,
    ia_list_pipeline_tiers,
    ia_list_plugins,
    ia_search_code,
)
from mcp_covaf.tools.lifecycle_tools import (
    lifecycle_get_dependencies,
    lifecycle_get_deploy_manifests,
    lifecycle_get_git_info,
    lifecycle_get_status,
    lifecycle_get_test_command,
    lifecycle_list_components,
)
from mcp_covaf.tools.report_tools import (
    report_format_for_team,
    report_generate_summary,
    report_get_health,
    report_list_findings,
)
from mcp_covaf.tools.template_tools import (
    template_get_schema,
    template_list,
    template_scaffold_new,
    template_validate,
)

__all__ = [
    # back (Java)
    "back_list_extraction_strategies",
    "back_list_templates",
    "back_list_quality_gates",
    "back_search_code",
    "back_get_endpoint_map",
    "back_analyze_oficios_pipeline",
    "back_analyze_cartas_pipeline",
    # front (Vue)
    "front_list_routes",
    "front_list_modules",
    "front_list_services",
    "front_search_code",
    "front_get_mfe_config",
    # ia (Python)
    "ia_list_plugins",
    "ia_list_pipeline_tiers",
    "ia_get_plugin_schema",
    "ia_search_code",
    "ia_analyze_extraction_output",
    "ia_list_eval_tests",
    # lifecycle
    "lifecycle_get_status",
    "lifecycle_list_components",
    "lifecycle_get_git_info",
    "lifecycle_get_dependencies",
    "lifecycle_get_test_command",
    "lifecycle_get_deploy_manifests",
    # report
    "report_generate_summary",
    "report_list_findings",
    "report_get_health",
    "report_format_for_team",
    # template
    "template_list",
    "template_get_schema",
    "template_validate",
    "template_scaffold_new",
]
